import cv2, math
import numpy as np
from matplotlib import pyplot as plt
# from PIL import Image
# from colorthief import ColorThief
import fast_colorthief

# from task_executor import TaskExecutor
# from p_hash import pHash
# from config import Config

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, always_init=True, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        elif always_init:
            cls._instances[cls].__init__(*args, **kwargs)
        return cls._instances[cls]

def cnt_to_pts(cnt):
    pts = np.float32([p[0] for p in cnt])
    return pts

def split_dataframe(df, chunk_size=10000):
    chunks = []
    num_chunks = math.ceil(len(df) / chunk_size)
    # num_chunks = len(df) // chunk_size + 1
    for i in range(num_chunks):
        chunks.append(df[i*chunk_size:(i+1)*chunk_size])
    return chunks

def resize_with_aspect_ratio(image, width=None, height=None, inter=cv2.INTER_AREA):
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

def get_image_color(img, method='dominant', colorspace_output='BGR', quality=1, normalize_hsv=True):
    if isinstance(img, str):
        img = plt.imread(img) # reads as RGB

    if method == 'mean':
        a,b,c = cv2.split(img)
        res = [int(a.mean()), int(b.mean()), int(c.mean())]
    elif method == 'dominant':
        # color_thief = ColorThief(img)
        # res = color_thief.get_color(quality)
        if isinstance(img, np.ndarray) and img.shape[2] == 3:
            if normalize_hsv:
                # normalize brightness value
                img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                img_hsv[:,:,2] = cv2.equalizeHist(img_hsv[:,:,2])
                img = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)
            
            # add alpha channel to the image array
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)

        res = fast_colorthief.get_dominant_color(img, quality)
    else:
        raise ValueError(f'Unknown method `{method}`')
    
    res = np.uint8([[res]])
    if colorspace_output is None \
            or colorspace_output.upper() == 'RGB':
        pass
    elif colorspace_output.upper() == 'LAB':
        res = cv2.cvtColor(res, cv2.COLOR_RGB2LAB)
    elif colorspace_output.upper() == 'HSV':
        res = cv2.cvtColor(res, cv2.COLOR_RGB2HSV)
    elif colorspace_output.upper() == 'BGR':
        res = cv2.cvtColor(res, cv2.COLOR_RGB2BGR)
    else:
        raise ValueError(f'Unknown color space `{colorspace_output.upper()}`')
    
    res = list(res[0][0])
    return res

def get_color_class(img=None, color:tuple=None, num_of_classes=4, eps=0.2, **kwargs): #method='dominant', colorspace_output='BGR', normalize_hsv):
    '''
    Converts rgb-color code to a specific color class.
    Each channel is split into `num_of_classes`, effectively creating `num_of_classes**3` classes.

    The user should pass only one of `img` or `color`.
    
    :param img: Can be either a path to the image or an image array.
    :param color: Should be tuple of the three rgb channels.
    :param num_of_classes: Number of classes each channel will be divided into.
    :param eps: Value between 0 to 1, ±epsilon to consider when choosing classes.
    :return: a 3-tuple of list of classes, each channel can have multiple classes. `([b_classes],[g_classes],[r_classes])`
    '''
    # input checks
    if color is None and img is None :
        raise ValueError('Both `color` and `img` are None type.')
    elif color is not None and img is not None:
        raise ValueError('You must choose only one of `color` and `img`.')
    if img is not None:
        color = get_image_color(img, **kwargs) #method=method, colorspace_output=colorspace_output)
    if eps < 0 or eps > 1:
        raise ValueError('`eps` not in range[0,1]')

    # per channel classes creation
    step_size = (256//num_of_classes)
    steps = [ i for i in range(0, 256, step_size) ]
    ranges = []
    if steps[-1] < 255:
        steps += [255]
    for i in range(1, len(steps)):
        ranges += [ range(steps[i-1],steps[i]) ]

    eps = int((step_size+1) * eps)
    cats = [[],[],[]]
    for channel,val in enumerate(color):
        for cat,_range in enumerate(ranges):
            if val in _range:
                cats[channel] += [ cat ]
            elif val+eps in _range:
                cats[channel] += [ cat ]
            elif val-eps in _range:
                cats[channel] += [ cat ]

    return cats