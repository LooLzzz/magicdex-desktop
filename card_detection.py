import cv2, time, re, subprocess, os
import numpy as np
import pandas as pd
import imagehash as ih
from PIL import Image as PILImage

from p_hash import pHash
from config import Config

def ResizeWithAspectRatio(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    return cv2.resize(image, dim, interpolation=inter)

# www.pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/
def order_points(pts):
    """
    initialzie a list of coordinates that will be ordered such that the first entry in the list is the top-left,
    the second entry is the top-right, the third is the bottom-right, and the fourth is the bottom-left
    :param pts: array containing 4 points
    :return: ordered list of 4 points
    """
    rect = np.zeros((4, 2), dtype="float32")

    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    # return the ordered coordinates
    return rect


def four_point_transform(image, pts):
    """
    Transform a quadrilateral section of an image into a rectangular area
    From: www.pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/
    :param image: source image
    :param pts: 4 corners of the quadrilateral
    :return: rectangular image of the specified area
    """
    # obtain a consistent order of the points and unpack them
    # individually
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # compute the width of the new image, which will be the
    # maximum distance between bottom-right and bottom-left
    # x-coordiates or the top-right and top-left x-coordinates
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_a), int(width_b))

    # compute the height of the new image, which will be the
    # maximum distance between the top-right and bottom-right
    # y-coordinates or the top-left and bottom-left y-coordinates
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_a), int(height_b))

    # now that we have the dimensions of the new image, construct
    # the set of destination points to obtain a "birds eye view",
    # (i.e. top-down view) of the image, again specifying points
    # in the top-left, top-right, bottom-right, and bottom-left
    # order
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]], dtype="float32")

    # compute the perspective transform matrix and then apply it
    mat = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, mat, (max_width, max_height))

    # If the image is horizontally long, rotate it by 90
    if max_width > max_height:
        center = (max_height / 2, max_height / 2)
        mat_rot = cv2.getRotationMatrix2D(center, 270, 1.0)
        warped = cv2.warpAffine(warped, mat_rot, (max_height, max_width))

    # return the warped image
    return warped

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
    stack = [(0, hier[0][0])]
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

def detect_image(img, hash_size=32, size_thresh=10000, display=True, debug=False):
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

    phash_df = pHash.get_pHash_df()
    img_result = img.copy() # For displaying and saving
    det_cards = []
    # Detect contours of all cards in the image
    cnts = find_rects_in_image(img_result, size_thresh=size_thresh)
    for i in range(len(cnts)):
        cnt = cnts[i]
        # For the region of the image covered by the contour, transform them into a rectangular image
        pts = np.float32([p[0] for p in cnt])
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
        # the stored values of hashes in the dataframe is pre-emptively flattened already to minimize computation time
        card_hash = pHash.img_to_phash(img_warp).hash.flatten()
        phash_df['hash_diff'] = phash_df['phash'].apply(lambda x: np.count_nonzero(x != card_hash))
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
        cv2.imshow('Result', ResizeWithAspectRatio(img_result, height=800))
        cv2.waitKey(0)

    return (
        det_cards,
        img_result
    )

################################################################
################################################################

def detect_images(imgs, **kwargs):
    for img in imgs:
        # detect_image(img)
        detect_image(img, **kwargs)

def detect_video(capture, display, debug):
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
            
            (det_cards, img_result) = detect_image(frame, display=False, debug=debug)
            if display:
                cv2.imshow('result', img_result)
                key = cv2.waitKey(1) & 0xFF
            
            if debug:
                max_num_obj = max(max_num_obj, len(det_cards))
                for i in range(len(det_cards), max_num_obj):
                    cv2.imshow(f'Card {i}', np.zeros((1, 1), dtype=np.uint8))
            
            elapsed_ms = (time.time() - start_time) * 1000
            print('Elapsed time: %.2f ms' % elapsed_ms)
    finally:
        cv2.destroyAllWindows()

if __name__ == '__main__':
    # imgs = []
    # for i in range(1,6): #range=[1,...,5]
    #     imgs += [ cv2.imread(f'{Config.cards_path}/test/{i}.jpg') ]
    # detect_images(imgs, debug=True)

    capture = cv2.VideoCapture(0)
    detect_video(capture, display=True, debug=True)
    capture.release()