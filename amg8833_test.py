# AMG8833 test

import sys
import logging

import cv2
import numpy as np
import serial
from submodules.amg8833 import *

com_port = find_thermo_sensor()
if com_port is None:
    logging.critical('Thermal image sensor is not attached.')
    sys.exit(1)

# Open serial port (COM port) for AMG8833 temperature area sensor
try:
    com_speed = 115200
    com = serial.Serial(com_port, com_speed, timeout=3)
except serial.serialutil.SerialException:
    logging.critical('Failed to open serial port \'{}\''.format(com_port))
    sys.exit(1)
com.reset_input_buffer();

cell_size = 48
img_cells = np.zeros((cell_size * 8, cell_size * 8, 3), dtype=np.uint8)
img_range = np.zeros((cell_size * 2, cell_size * 8, 3), dtype=np.uint8)

def disp_temp(image, x, y, temp, temp_min=-999, temp_max=999, cell_size = 48):
    def disp_text(image, text, x, y, cy, color=(255,255,255)):
        font = cv2.FONT_HERSHEY_PLAIN
        (w, h), baseline = cv2.getTextSize(text, font, 1, 1)
        xx = int(x)
        yy = int(y + (cy+1) * (h+baseline))
        cv2.putText(image, text, (xx, yy), font, 1, (0,0,0), 3)
        cv2.putText(image, text, (xx, yy), font, 1, color, 1)
    cell_x = x * cell_size
    cell_y = y * cell_size
    if temp_min != -999:
        disp_text(image, '{:4.1f}'.format(temp_min), cell_x, cell_y, 0, (255,128,0))
    disp_text(image, '{:4.1f}'.format(temp), cell_x, cell_y, 1)
    if temp_max != 999:
        disp_text(image, '{:4.1f}'.format(temp_max), cell_x, cell_y, 2, (0,0,255))

thermo_min = np.full((8*8,),  999, dtype=np.float32)
thermo_max = np.full((8*8,), -999, dtype=np.float32)

key = -1
ambient_temp = 0
while key != 27:
    img_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    thermo, ambient_temp, face_distance = capture_thermo_frame(com)
    #thermo = temp_compensation(thermo, ambient_temp, ofst=0.0)
    thermo = np.array(thermo, dtype=np.float32)
    thermo_max = np.where(thermo>thermo_max, thermo, thermo_max)
    thermo_min = np.where(thermo<thermo_min, thermo, thermo_min)
    max_tmp, min_tmp = thermo.max(), thermo.min()
    logging.debug('Ambient {:4.1f}, max {:4.1f}, min {:4.1f}'.format(ambient_temp, max_tmp, min_tmp))
    clip_h, clip_l = max_tmp, min_tmp
    thermo_norm = (thermo - clip_l) / (clip_h - clip_l)      # normalize (0.0-1.0)
    thermo_img = thermo_norm.reshape((8,8))
    thermo_img = cv2.resize(thermo_img, (cell_size*8, cell_size*8), interpolation=cv2.INTER_AREA)
    thermo_img *= 255
    thermo_img = cv2.merge([thermo_img, thermo_img, thermo_img])
    for y in range(8):
        for x in range(8):
            temp = thermo[y*8+x]
            max_t = thermo_max[y*8+x]
            min_t = thermo_min[y*8+x]
            disp_temp(thermo_img, x, y, temp, min_t, max_t, cell_size)
    fx = int(640-cell_size*9)
    fy = int((480 - cell_size * 8)/2)
    img_frame[fy:fy+cell_size*8, fx:fx+cell_size*8,:] = thermo_img

    cv2.putText(img_frame, 'Thermister Temp={:4.1f}C'.format(ambient_temp), (0, 40), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
    cv2.imshow('AMG8833 Test Program', img_frame)
    key = cv2.waitKey(50)

    if key == ord('r'):
        thermo_min = np.full((8*8,),  999, dtype=np.float32)
        thermo_max = np.full((8*8,), -999, dtype=np.float32)


cv2.destroyAllWindows()
com.close()
