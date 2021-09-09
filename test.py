import sys
import glob
import datetime
import json

import serial
import numpy as np
import cv2
from scipy import spatial

from config import *
from amg8833 import *
from openvino_model import *
from excel_operation import *
from common_face_utils import *

#---------------------------------------------------------------------

def scan_and_register_faces(directory:str, FD_net, FR_net, LM_net):
    face_db = []
    json_files = glob.glob(os.path.join(database_dir, '*.json'))
    for json_file in json_files:
        with open(json_file, 'rt') as f:
            json_data = json.load(f)
        face_db.append(json_data)
        print('[INFO] Registered:', json_file)
    print('[INFO] Total', len(face_db), 'faces are registered.')
    return face_db

#---------------------------------------------------------------------

def draw_ROI(ROI, image, threshold=0.7):
    height, width = image.shape[:1+1]
    confidence = ROI[0]
    x0 = int(ROI[2] * width)
    y0 = int(ROI[3] * height)
    x1 = int(ROI[4] * width)
    y1 = int(ROI[5] * height)
    if confidence > threshold:
        color = (  0,255,  0)       # Green
    else:
        #color = (  0,  0,255)       # Red
        color = (255,  0,  0)       # Blue
    cv2.rectangle(image, (x0, y0), (x1, y1), color, 2)

def draw_ROIs(ROIs, image):
    for ROI in ROIs:
        draw_ROI(ROI, image)

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

def draw_label(ROI, image, text):
    _, _, x0, y0, x1, y1 = ROI
    height, width = image.shape[:1+1]
    x = int(x0 * width)
    y = int(y0 * height)
    (w, h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_PLAIN, 2, 2)
    cv2.putText(image, text, (x,y-baseline), cv2.FONT_HERSHEY_PLAIN, 2, (  0,  0,  0), 5)
    cv2.putText(image, text, (x,y-baseline), cv2.FONT_HERSHEY_PLAIN, 2, (  0,255,255), 2)

def draw_ambient_temp(temp, image):
    msg = 'Ambient temp : {:4.1f}C'.format(temp)
    (w, h), baseline = cv2.getTextSize(msg, cv2.FONT_HERSHEY_PLAIN, 2, 2)
    cv2.putText(image, msg, (0,h+baseline), cv2.FONT_HERSHEY_PLAIN, 2, (  0,  0,  0), 5)
    cv2.putText(image, msg, (0,h+baseline), cv2.FONT_HERSHEY_PLAIN, 2, (255,255,255), 2)

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
        if len(face_db)>0:
            idx, dist = search_face_db(feat_vec, face_db)                               # feature vector matching (face recognition)
            person_id, person_name, _ = face_db[idx]
        else:
            idx, dist, person_id, person_name = 0, 1.0, -1, 'none'
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
    draw_ambient_temp(ambient_temp, img_disp)
    if not ROI is None:
        px, py = calc_measure_point(ROI, LM_res)
        temp = measure_temp(ROI, (px, py), temp_map, img_disp)
        msg = '{} {:4.1f}C {:4.1f}%'.format(person_name, temp, (1-dist)*100)
        ROI[0] = 1-dist             # replace confidence value with similarity value
        draw_ROI(ROI, img_disp)
        draw_label(ROI, img_disp, msg)
        draw_landmarks(ROI, LM_res, img_disp)
    cv2.imshow('Automatic Body Temperature Measuring System', img_disp)
    key = cv2.waitKey(1)

dt = datetime.datetime.now()
filename = 'body_temp_record_{:04}{:02}{:02}-{:02}{:02}{:02}.xlsx'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
export_to_excel(filename, temp_record)

cam.release()
com.close()
