import sys
import glob
import datetime

import serial
import numpy as np
import cv2

from config import *
from amg8833 import *
from openvino_model import *
from excel_operation import *

#---------------------------------------------------------------------

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

def draw_ROI(ROI, image):
    height, width = image.shape[:1+1]
    x0 = int(ROI[2] * width)
    y0 = int(ROI[3] * height)
    x1 = int(ROI[4] * width)
    y1 = int(ROI[5] * height)
    cv2.rectangle(image, (x0, y0), (x1, y1), (0,255,0), 2)

def draw_ROIs(ROIs, image):
    for ROI in ROIs:
        draw_ROI(ROI, image)

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

def scan_and_register_faces(directory:str, FD_net, FR_net, LM_net):
    face_db = []
    pictures = glob.glob(os.path.join(directory, '*.jpg'))
    for pic in pictures:
        in_img = cv2.imread(pic)
        FD_res = FD_net.image_sync_infer(in_img)[FD_net.outblob_names[0]]
        ROIs = get_ROIs(FD_res[0][0])
        if len(ROIs)<1:
            continue
        ROI = find_largest_ROI(ROIs)
        ROI[2:2+4+1] = rescale_ROI(ROI[2:2+4+1], scale_factor=1.2)
        cropped_face = crop_ROI(ROI, in_img)

        LM_res = LM_net.image_sync_infer(cropped_face)[LM_net.outblob_names[0]]
        aligned_face = align_face(cropped_face, LM_res.reshape((5,2)))

        FR_res = FR_net.image_sync_infer(aligned_face)[FR_net.outblob_names[0]]
        feat_vec = FR_res.ravel()

        path, filename = os.path.split(pic)
        base_name, ext = os.path.splitext(filename)
        person_id, person_name = base_name.split('-')[:1+1]

        face_db.append([person_id, person_name, feat_vec])
        print('[INFO] Registered:', pic)
    print('[INFO] Total', len(face_db), 'faces are registered.')
    return face_db

from scipy import spatial

def search_face_db(feat_vec, face_db):
    distances = []
    for person_id, person_name, vect in face_db:
        dist = spatial.distance.cosine(feat_vec, vect)
        distances.append(dist)
    min_idx = distances.index(min(distances))
    return min_idx, distances[min_idx]


def draw_landmarks(ROI, LM, image):
    height, width = image.shape[:1+1]
    _, _, x0, y0, x1, y1 = ROI
    for x,y in LM:
        xx = int(((x1-x0)*x+x0)*width)
        yy = int(((y1-y0)*y+y0)*height)
        cv2.drawMarker(image, (xx, yy), 
                        (0,255,255), cv2.MARKER_CROSS, 5, 5)
    # LM  0: right eye, 1: left eye, 2: nose, 3: right mouth, 4: left mouth

def calc_measure_point(ROI, LM):
    erx, ery = LM[0]
    elx, ely = LM[1]
    nx, ny = LM[2]
    ecx, ecy = (elx+erx)/2.0, (ely+ery)/2.0     # eye center
    dx, dy = ecx-nx, ecy-ny
    ratio = 1.8
    px, py = nx+dx*ratio, ny+dy*ratio           # extend line segment of nose to eye-center
    return px, py

def measure_temp(ROI, pt, temp_map, image, draw_marker_flag=True):
    height, width = image.shape[:1+1]
    _, _, x0, y0, x1, y1 = ROI
    xx = int(((x1-x0)*pt[0]+x0)*width)
    yy = int(((y1-y0)*pt[1]+y0)*height)
    temp = temp_map[yy, xx]
    if draw_marker_flag:
        cv2.drawMarker(image, (xx, yy), 
                        (255,0,255), cv2.MARKER_CROSS, 10, 5)
    return temp

def draw_label(ROI, image, person_name):
    _, _, x0, y0, x1, y1 = ROI
    height, width = image.shape[:1+1]
    x = int(x0 * width)
    y = int(y0 * height)
    cv2.putText(image, person_name, (x,y), cv2.FONT_HERSHEY_PLAIN, 2, (0,255,255), 2)

#---------------------------------------------------------------------

# Open serial port (COM port) for AMG8833 temperature area sensor
try:
    com = serial.Serial(com_port, com_speed, timeout=None)
except serial.serialutil.SerialException:
    print('Failed to open serial port \'{}\''.format(com_port))
    sys.exit()

# Load OpenVINO Deep-learning models
config = {'CACHE_DIR' : './cache'}
FD_net = openvino_model(FD_model, 'GPU', config=config)
FR_net = openvino_model(FR_model, 'GPU', config=config)
LM_net = openvino_model(LM_model, 'GPU', config=config)

# Open USB webCam
img_width  = 640
img_height = 480
cam = cv2.VideoCapture(0)
if cam.isOpened() == False:
    print('Failed to open a USB webCam (0)')
    sys.exit()
cam.set(cv2.CAP_PROP_FRAME_WIDTH,  img_width)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, img_height)

# Read and register face database
face_db = scan_and_register_faces('./face_db', FD_net, FR_net, LM_net)

overlay  = np.zeros((img_height, img_width, 3), dtype=np.uint8)
temp_map = np.zeros((img_height, img_width   ), dtype=np.float32)

temp_record = []        # record of measured temerature data (to be exported to Excel)

key = -1
while key != 27:
    sts, img = cam.read()

    # Face detection - Face landmark detection - Face recognition
    res = FD_net.image_sync_infer(img)[FD_net.outblob_names[0]]     # detect face
    ROIs = get_ROIs(res[0][0])
    if len(ROIs)>0:
        ROI = find_largest_ROI(ROIs)                                                # find the largest face in a picture
        cropped_face = crop_ROI(ROI, img)
        LM_res = LM_net.image_sync_infer(cropped_face)[LM_net.outblob_names[0]]     # detect landmarks
        LM_res = LM_res.reshape((5,2))
        aligned_face = align_face(cropped_face, LM_res)
        FR_res = FR_net.image_sync_infer(aligned_face)[FR_net.outblob_names[0]]     # extract feature vector from a face
        feat_vec = FR_res.ravel()
        idx, dist = search_face_db(feat_vec, face_db)                               # feature vector matching (face recognition)
        person_id, person_name, _ = face_db[idx]
    else:
        ROI = None

    # Convert the picture into line drawing (edge detection)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)        # color -> gray
    img_gray = cv2.split(img_gray)[0]                       # 3ch -> 1ch
    img_edge = cv2.Canny(img_gray, 64, 128)                 # edge detection
    img_disp = cv2.merge([img_edge, img_edge, img_edge])    # 1ch -> 3ch

    thermo, ambient_temp = capture_thermo_frame(com)

    ofst = 7.0    # 30cm
    thermo = temp_compensation(thermo, ambient_temp, ofst)
    max_tmp, min_tmp = max(thermo), min(thermo)
    #print(ambient_temp, max_tmp, min_tmp)
    thermo_img = np.array(color_map(thermo)).astype(np.uint8)
    thermo_img = thermo_img.reshape((8,8,3))

    # Overlay thermo image onto the input image
    height, width = overlay.shape[:1+1]
    center_x = width / 2.0
    center_y = height / 2.0
    mag = height / thermo_img.shape[0]
    interpolation = cv2.INTER_LANCZOS4
    thermo_img = cv2.resize(thermo_img, dsize=(0,0), fx=mag, fy=mag, interpolation=interpolation)
    overlay[:, int(center_x-height/2):int(center_x+height/2), :] = thermo_img
    img_disp = img_disp | overlay

    # scale thermo map to the same size as the display image
    thermo_map = np.array(thermo, dtype=np.float32).reshape((8,8))
    thermo_map = cv2.resize(thermo_map, dsize=(0,0), fx=mag, fy=mag, interpolation=interpolation)
    temp_map[:, int(center_x-height/2):int(center_x+height/2)] = thermo_map

    # draw results
    draw_ROIs(ROIs, img_disp)
    if not ROI is None:
        px, py = calc_measure_point(ROI, LM_res)
        temp = measure_temp(ROI, (px, py), temp_map, img_disp)
        msg = '{} {:4.1f}C {:4.1f}%'.format(person_name, temp, (1-dist)*100)
        draw_label(ROI, img_disp, msg)
        draw_landmarks(ROI, LM_res, img_disp)
    cv2.imshow('Automatic Body Temperature Measuring System', img_disp)
    key = cv2.waitKey(1)

dt = datetime.datetime.now()
filename = 'body_temp_record_{:04}{:02}{:02}-{:02}{:02}{:02}.xlsx'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
export_to_excel(filename, temp_record)

cam.release()
com.close()
