import cv2, time #, os
import numpy as np
import pandas as pd
# from modin import pandas as modin_pd
# import imagehash as ih
# from PIL import Image as PILImage

from utils import four_point_transform, resize_with_aspect_ratio, cnt_to_pts
from task_executor import TaskExecutor
from p_hash import pHash
# from config import Config

# os.environ['MODIN_ENGINE'] = 'dask'  # Modin will use Dask

def find_rects_in_image(img, thresh_c=5, kernel_size=(3, 3), size_thresh=10000):
    """
    Find contours of all cards in the image
    :param img: source image
    :param thresh_c: value of the constant C for adaptive thresholding
    :param kernel_size: dimension of the kernel used for dilation and erosion
    :param size_thresh: threshold for size (in pixel) of the contour to be a candidate
    :return: list of candidate contours
    """
    # Typical pre-processing - grayscale, blurring, thresholding
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.medianBlur(img_gray, 5)
    img_thresh = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 5, thresh_c)

    # Dilute the image, then erode them to remove minor noises
    kernel = np.ones(kernel_size, np.uint8)
    img_dilate = cv2.dilate(img_thresh, kernel, iterations=1)
    img_erode = cv2.erode(img_dilate, kernel, iterations=1)

    # Find the contour
    cnts, hier = cv2.findContours(img_erode, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(cnts) == 0:
        #print('no contours')
        return []

    # The hierarchy from cv2.findContours() is similar to a tree: each node has an access to the parent, the first child
    # their previous and next node
    # Using recursive search, find the uppermost contour in the hierarchy that satisfies the condition
    # The candidate contour must be rectangle (has 4 points) and should be larger than a threshold
    cnts_rect = []
    stack = [ (0, hier[0][0]) ]
    while len(stack) > 0:
        i_cnt, h = stack.pop()
        i_next, i_prev, i_child, i_parent = h
        if i_next != -1:
            stack.append((i_next, hier[0][i_next]))
        cnt = cnts[i_cnt]
        size = cv2.contourArea(cnt)
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
        if size >= size_thresh and len(approx) == 4:
            cnts_rect.append(approx)
        else:
            if i_child != -1:
                stack.append((i_child, hier[0][i_child]))
    return cnts_rect

def detect_image(img, phash_df, hash_size=32, size_thresh=10000, display=True, debug=False):
    """
    Identify all cards in the input frame, display or save the frame if needed\n
    ---
    :param img: cv2 input image
    :param card_pool: pandas dataframe of all card's information
    :param hash_size: param for pHash algorithm
    :param size_thresh: threshold for size (in pixel) of the contour to be a candidate
    :param out_path: path to save the result
    :param display: flag for displaying the result
    :param debug: flag for debug mode
    :return: list of detected card's name/set and resulting image
    """

    # phash_df = pHash.get_pHash_df()
    img_result = img.copy() # For displaying and saving
    det_cards = []
    # Detect contours of all cards in the image
    cnts = find_rects_in_image(img_result, size_thresh=size_thresh)
    for (i,cnt) in enumerate(cnts):
        # For the region of the image covered by the contour, transform them into a rectangular image
        pts = cnt_to_pts(cnt)
        img_warp = four_point_transform(img, pts)

        # To identify the card from the card image, perceptual hashing (pHash) algorithm is used
        # Perceptual hash is a hash string built from features of the input medium. If two media are similar
        # (ie. has similar features), their resulting pHash value will be very close.
        # Using this property, the matching card for the given card image can be found by comparing pHash of
        # all cards in the database, then finding the card that results in the minimal difference in pHash value.
        '''
        img_art = img_warp[47:249, 22:294]
        img_art = Image.fromarray(img_art.astype('uint8'), 'RGB')
        art_hash = ih.phash(img_art, hash_size=hash_size).hash.flatten()
        phash_df['hash_diff'] = phash_df['art_hash'].apply(lambda x: np.count_nonzero(x != art_hash))
        '''
        # the stored values of hashes in the dataframe are pre-emptively flattened to minimize computation time
        phash_value = pHash.img_to_phash(img_warp, hash_size=hash_size).hash.flatten()

        phash_df['hash_diff'] = phash_df['phash'].apply(lambda x: np.count_nonzero(x != phash_value))
        # card_hash = pHash.img_to_phash(img_warp)
        # phash_df['hash_diff'] = phash_df['phash'] - card_hash
        
        min_card = phash_df[phash_df['hash_diff'] == min(phash_df['hash_diff'])].iloc[0]
        card_name = min_card['name']
        card_set = min_card['set']
        det_cards += [ (card_name, card_set) ]
        hash_diff = min_card['hash_diff']

        # Render the result, and display them if needed
        cv2.drawContours(img_result, [cnt], -1, (255, 0, 0), 7)
        cv2.putText(img_result, card_name, (min(pts[0][0], pts[1][0]), min(pts[0][1], pts[1][1])),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        if debug:
            # cv2.rectangle(img_warp, (22, 47), (294, 249), (0, 255, 0), 2)
            cv2.putText(img_warp, card_name + ', ' + str(hash_diff), (0, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            cv2.imshow(f'Card {i}', img_warp)
    if display:
        cv2.imshow('Result', resize_with_aspect_ratio(img_result, height=800))
        cv2.waitKey(0)

    return (
        det_cards,
        img_result
    )

################################################################
################################################################

def detect_images(imgs, **kwargs):
    phash_df = pd.DataFrame(pHash.get_pHash_df(update=False))
    for img in imgs:
        # detect_image(img)
        detect_image(img, phash_df, **kwargs)
        cv2.destroyAllWindows()

def detect_video(capture, display, debug):
    def _task(img, df):
        det_cards = []
        cnts = find_rects_in_image(img)
        for cnt in cnts:
            pts = cnt_to_pts(cnt)
            img_warp = four_point_transform(img, pts)
            
            phash_value = pHash.img_to_phash(img_warp).hash.flatten()
            df['hash_diff'] = df['phash'].apply(lambda x: np.count_nonzero(x != phash_value))

            min_diff = min(df['hash_diff'])
            min_card = df[df['hash_diff'] == min_diff].iloc[0]
            card_name = min_card['name']
            # card_set = min_card['set']
            det_cards += [ (cnt, card_name, img_warp, min_diff) ]
        return det_cards

    task_master = TaskExecutor(max_workers=1)
    phash_df = pHash.get_pHash_df(update=False)
    det_cards = [] # each item in `det_cards` conatins `(cnt, card_name, img_warp, hash_diff)`
    max_num_obj = 0

    try:
        while True:
            (ret, frame) = capture.read()
            start_time = time.time()
            if not ret:
                # End of video
                print("End of video. Press any key to exit")
                cv2.waitKey(0)
                break
            
            # (det_cards, img_result) = detect_image(frame, phash_df=phash_df, display=False, debug=debug)
            # (det_cards, img_result) = detect_image(frame, phash_df=phash_df_split, display=False, debug=debug)

            img_result = frame.copy()
            if len(task_master.futures) == 0:
                task_master.submit(_task, img=frame, df=phash_df)
            elif task_master.futures[0].done():
                det_cards = task_master.futures.pop().result()
            
            for (cnt, card_name, _img_warp, _hash_diff) in det_cards:
                pts = cnt_to_pts(cnt)
                cv2.drawContours(img_result, [cnt], -1, (255, 0, 0), 7)
                cv2.putText(img_result, card_name, (min(pts[0][0], pts[1][0]), min(pts[0][1], pts[1][1])),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            if display:
                cv2.imshow('result', img_result)
                key = cv2.waitKey(1) & 0xFF
            
            if debug:
                max_num_obj = max(max_num_obj, len(det_cards))
                for (i, (cnt, card_name, img_warp, hash_diff)) in enumerate(det_cards):
                    # img_warp = four_point_transform(frame, pts)
                    cv2.putText(img_warp, card_name + ', ' + str(hash_diff), (0, 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                    cv2.imshow(f'Card {i}', img_warp)
            
            elapsed_ms = (time.time() - start_time) * 1000
            print('Elapsed time: %.2f ms' % elapsed_ms)
    finally:
        cv2.destroyAllWindows()

if __name__ == '__main__':
    # imgs = []
    # for i in range(1,6): #range=[1,...,5]
    #     imgs += [ cv2.imread(f'{Config.cards_path}/test/{i}.jpg') ]
    # phash_df = pHash.get_pHash_df(update=False)
    # detect_images(imgs, debug=True)

    capture = cv2.VideoCapture(0)
    detect_video(capture, display=True, debug=True)
    capture.release()