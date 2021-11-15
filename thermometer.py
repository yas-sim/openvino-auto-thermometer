import sys, time
import glob
import datetime
import json
import logging

import numpy as np
import cv2
import simpleaudio
import serial

from submodules.openvino_model import *
from submodules.excel_operation import *
from submodules.common_face_utils import *
from submodules.mlx90614 import *

#---------------------------------------------------------------------

def scan_and_register_faces(directory:str, FD_net, FR_net, LM_net):
    face_db = []
    json_files = glob.glob(os.path.join(config['system']['database_dir'], '*.json'))
    for json_file in json_files:
        with open(json_file, 'rt') as f:
            json_data = json.load(f)
        face_db.append(json_data)
        logging.info('Registered: {}'.format(json_file))
    logging.info('Total {} faces are registered.'.format(len(face_db)))
    return face_db

#---------------------------------------------------------------------

def draw_ROI(ROI, image, threshold=0.7, distance=-1):
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

def draw_label(ROI, image, text):
    _, _, x0, y0, x1, y1 = ROI
    height, width = image.shape[:1+1]
    x = int(x0 * width)
    y = int(y0 * height)
    (w, h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_PLAIN, 2, 2)
    cv2.putText(image, text, (x,y-baseline), cv2.FONT_HERSHEY_PLAIN, 2, (  0,  0,  0), 5)
    cv2.putText(image, text, (x,y-baseline), cv2.FONT_HERSHEY_PLAIN, 2, (  0,255,255), 2)

def draw_temps(comp_temp, obj_temp, amb_temp, image):
    msg = 'Temp:{:4.1f}C, Obj:{:4.1f}C, Amb:{:4.1f}C'.format(comp_temp, obj_temp, amb_temp)
    (w, h), baseline = cv2.getTextSize(msg, cv2.FONT_HERSHEY_PLAIN, 2, 2)
    cv2.putText(image, msg, (0,h+baseline), cv2.FONT_HERSHEY_PLAIN, 2, (  0,  0,  0), 5)
    cv2.putText(image, msg, (0,h+baseline), cv2.FONT_HERSHEY_PLAIN, 2, (255,255, 64), 2)


# Consolidates records
#  - Data for the same person ID will be averaged.
def consolidate_result(temp_record:list, config):
    if len(temp_record) == 0:
        return []
    dt = datetime.datetime.now()
    date = '{:04}/{}/{}'.format(dt.year, dt.month, dt.day)
    consolidate = []
    unique_id = set(np.array(temp_record)[:, 0])    # get unique IDs
    for pid in unique_id:
        cmp_tmp = []
        obj_tmp = []
        amb_tmp = []
        for row in temp_record:
            if row[0] == pid:
                cmp_tmp.append(row[2])
                obj_tmp.append(row[3])
                amb_tmp.append(row[4])
                tmp_id   = row[0]
                tmp_name = row[1]
        cmp_avg = sum(cmp_tmp) / len(cmp_tmp)
        obj_avg = sum(obj_tmp) / len(obj_tmp)
        amb_avg = sum(amb_tmp) / len(amb_tmp)
        if config['system']['school_flag'] == 'True':
            fever_status =  '37度以上' if cmp_avg >= 37.0 else '37度以下'             # check if the person has fever
            record = [tmp_id, tmp_name, date, fever_status, cmp_avg, obj_avg, amb_avg]
        else:
            record = [tmp_id, tmp_name, date,               cmp_avg, obj_avg, amb_avg]
        consolidate.append(record)
    sorted_record = sorted(consolidate, key=lambda record : record[0])
    return sorted_record

#---------------------------------------------------------------------

def main(config):

    # Load OpenVINO Deep-learning models
    inference_device = config['system']['inference_device']
    FD_net = openvino_model(config['dl_models']['FD_model'], inference_device)
    FR_net = openvino_model(config['dl_models']['FR_model'], inference_device)
    LM_net = openvino_model(config['dl_models']['LM_model'], inference_device)

    # Open USB webCam
    img_width  = config["camera"]["width"]
    img_height = config['camera']['height']
    cam_port   = config['camera']['port']
    cam = cv2.VideoCapture(cam_port)
    if cam.isOpened() == False:
        logging.critical('Failed to open a USB webCam ({})'.format(cam_port))
        sys.exit(1)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH,  config['camera']['width'])
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, config['camera']['height'])

    temp_sensor = mlx90614()
    temp_sensor.open()

    # Read and register face database
    face_db = scan_and_register_faces(config['system']['database_dir'], FD_net, FR_net, LM_net)

    temp_record = []        # record of measured temerature data (to be exported to Excel)

    beep_obj = simpleaudio.WaveObject.from_wave_file(config['sound']['sound_file'])

    last_recognition_id, last_recognition_name = -1, 'none'
    current_person_id, current_person_name = -1, 'none'
    ma = []    # Moving agerage for temperature
    key = -1
    while key != 27:
        sts, img = cam.read()       # Capture an image from a USB webCam

        # Face detection - Face landmark detection - Face recognition
        res = FD_net.image_sync_infer(img)[FD_net.outblob_names[0]]                     # detect face
        ROIs = get_ROIs(res[0][0])
        ROI = None
        if len(ROIs)>0:
            ROI = find_largest_ROI(ROIs)                                                # find the largest face in a picture
            face_size = calc_ROI_area(ROI)
            logging.debug('Face size {}'.format(face_size))
            if face_size < ((1/3)*(1/3)):                                               # Check face size and ignore it if it's too small
                ROI = None
            else:
                cropped_face = crop_ROI(ROI, img)
                LM_res = LM_net.image_sync_infer(cropped_face)[LM_net.outblob_names[0]]     # detect landmarks
                LM_res = LM_res.reshape((5,2))
                aligned_face = align_face(cropped_face, LM_res)
                FR_res = FR_net.image_sync_infer(aligned_face)[FR_net.outblob_names[0]]     # extract feature vector from a face
                feat_vec = FR_res.ravel()
                if len(face_db)>0:
                    idx, dist = search_face_db(feat_vec, face_db)                           # feature vector matching (face recognition)
                    person_id, person_name, _ = face_db[idx]
                    last_recognition_id, last_recognition_name = person_id, person_name
                else:
                    idx, dist, person_id, person_name = 0, 1.0, -1, 'none'

        # Display image processing
        if config['system']['convert_to_line_art'] == 'True':
            # Convert the picture into line drawing (edge detection)
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)        # color -> gray
            img_gray = cv2.split(img_gray)[0]                       # 3ch -> 1ch
            img_edge = cv2.Canny(img_gray, 96, 128)                 # edge detection
            img_disp = cv2.merge([img_edge, img_edge, img_edge])    # 1ch -> 3ch
        else:
            img_disp = img

        # Read temp and distance from the sensors
        try:
            face_distance, object_temp, ambient_temp = temp_sensor.receive_temp_data()
        except serial.serialutil.SerialException:
            while True:
                logging.info('Trying to re-open temp sensor')
                time.sleep(1)
                try:
                    del temp_sensor
                    temp_sensor = mlx90614()
                    temp_sensor.open()
                    break
                except:
                    pass
        # Compensate measured temp
        ofst = 0.0
        comp_temp = temp_sensor.temp_compensation(object_temp, ambient_temp, ofst)
        logging.debug('Distance {:4.1f}cm Ambient {:4.1f}C, Object {:4.1f}C, Compensated {:4.1f}C'.format(face_distance, ambient_temp, object_temp, comp_temp))

        # Check distance and face validity, and record the measured temp
        target_distance    = config['distance_sensor']['distance']       # unit = cm
        distance_torelance = config['distance_sensor']['tolerance']      # unit = cm
        distance_valid = True if face_distance>= (target_distance-distance_torelance) and face_distance<=(target_distance+distance_torelance) else False
        face_valid     = True if last_recognition_id != -1 else False
        if distance_valid and face_valid:
            temp_record.append([last_recognition_id, last_recognition_name, comp_temp, object_temp, ambient_temp])
            beep_obj.play()
            if current_person_id != last_recognition_id:         # measure temp
                ma = [ comp_temp ]          # reset moving average buffer
                current_person_id, current_person_name = last_recognition_id, last_recognition_name
            else:
                ma.append(comp_temp)        # add temp to moving average buffer
                if len(ma)>10:
                    ma = ma[-10:]           # keep the latest 10 data
            avg_temp = sum(ma) / len(ma)
        else:
            if face_valid:
                if current_person_id == last_recognition_id:
                    avg_temp = sum(ma) / len(ma)
                else:
                    avg_temp = -1
            else:
                avg_temp = -1

        # Draw results
        draw_ROIs(ROIs, img_disp)
        draw_temps(avg_temp, object_temp, ambient_temp, img_disp)
        if not ROI is None:
            msg = '{} {:4.1f}%'.format(last_recognition_name, (1-dist)*100)
            ROI[0] = 1-dist             # replace confidence value with similarity value
            #draw_ROI(ROI, img_disp)
            draw_ROI(ROI, img_disp, distance=face_distance)
            draw_label(ROI, img_disp, msg)
            draw_landmarks(ROI, LM_res, img_disp)
        cv2.imshow('Automatic Body Temperature Measuring System', img_disp)
        key = cv2.waitKey(1)

    dt = datetime.datetime.now()
    filename = 'body_temp_record_{:04}{:02}{:02}-{:02}{:02}{:02}.xlsx'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    logging.debug(temp_record)
    consolidated_record = consolidate_result(temp_record, config)   # Consolidates records (同じIDのデータは平均を取ってまとめる)
    logging.debug(consolidated_record)
    if len(consolidated_record) > 0:
        export_to_excel(filename, consolidated_record)              # Export to Excel (Excelファイルに書き出し)
        logging.info('"{}" is generated.'.format(filename))
    else:
        logging.warning('No record is captured - No Excel file is generated.')

    cam.release()
    return 0

if __name__ == '__main__':
    with open('thermometer_cfg.json', 'rt') as f:    # read configurations from the configuration file
        config = json.load(f)
    logging.basicConfig(level=[logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG][config['system']['log_level']])

    sys.exit(main(config))
