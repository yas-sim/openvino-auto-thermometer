import cv2
import numpy as np
from scipy import spatial

def rescale_ROI(ROI, scale_factor=1.0):
    x0, y0, x1, y1 = ROI
    center_x = (x0+x1) / 2.0
    center_y = (y0+y1) / 2.0
    x0 = (x0-center_x) * scale_factor + center_x
    y0 = (y0-center_y) * scale_factor + center_y
    x1 = (x1-center_x) * scale_factor + center_x
    y1 = (y1-center_y) * scale_factor + center_y
    x0 = min(1.0, max(0.0, x0))
    y0 = min(1.0, max(0.0, y0))
    x1 = min(1.0, max(0.0, x1))
    y1 = min(1.0, max(0.0, y1))
    return [x0, y0, x1, y1]

def get_ROIs(infer_results, threshold=0.7):
    ROIs = []
    for result in infer_results:
        conf = result[2]
        if conf >= threshold:
            label = result[1]
            ROI = result[3:6+1]
            x0, y0, x1, y1 = rescale_ROI(ROI, scale_factor=1.2)
            ROIs.append([conf, label, x0, y0, x1, y1])
    return ROIs

def crop_ROI(ROI, image):
    height, width = image.shape[:1+1]
    x0 = int(ROI[2] * width)
    y0 = int(ROI[3] * height)
    x1 = int(ROI[4] * width)
    y1 = int(ROI[5] * height)
    return image[y0:y1, x0:x1]

def crop_ROIs(ROIs, image):
    for ROI in ROIs:
        ROI.append(crop_ROI(ROI, image))

def normalize(array, axis):
    mean = array.mean(axis=axis)
    array -= mean
    std = array.std()
    array /= std
    return mean, std

def get_transform(src, dst):
    src_col_mean, src_col_std = normalize(src, axis=0)
    dst_col_mean, dst_col_std = normalize(dst, axis=0)

    u, _, vt = np.linalg.svd(np.matmul(src.T, dst))
    r = np.matmul(u, vt).T

    transform = np.empty((2, 3))
    transform[:, 0:2] = r * (dst_col_std / src_col_std)
    transform[:, 2] = dst_col_mean.T - np.matmul(transform[:, 0:2], src_col_mean.T)
    return transform

def align_face(image, face_landmark):
    REFERENCE_LANDMARKS = [
        (30.2946 / 96, 51.6963 / 112), # left eye
        (65.5318 / 96, 51.5014 / 112), # right eye
        (48.0252 / 96, 71.7366 / 112), # nose tip
        (33.5493 / 96, 92.3655 / 112), # left lip corner
        (62.7299 / 96, 92.2041 / 112)] # right lip corner
    scale = np.array((image.shape[1], image.shape[0]))
    desired_landmarks = np.array(REFERENCE_LANDMARKS, dtype=np.float64) * scale
    landmarks = face_landmark * scale
    transform = get_transform(desired_landmarks, landmarks)
    tmpimg = image.copy()
    cv2.warpAffine(tmpimg, transform, tuple(scale), tmpimg, flags=cv2.WARP_INVERSE_MAP)
    return tmpimg

def find_largest_ROI(ROIs):
    areas = [ (x1-x0)*(y1-y0) for _,_,x0,y0,x1,y1 in ROIs ]
    idx = areas.index(max(areas))
    return ROIs[idx]

def search_face_db(feat_vec, face_db):
    distances = []
    for person_id, person_name, vect in face_db:
        dist = spatial.distance.cosine(feat_vec, vect)
        distances.append(dist)
    min_idx = distances.index(min(distances))
    return min_idx, distances[min_idx]
