import os
import json

import cv2

with open('thermometer_cfg.json', 'rt') as f:    # read configurations from the configuration file
    config = json.load(f)

cam_w = config["camera"]["width"]
cam_h = config["camera"]["height"]

cap=cv2.VideoCapture(config["camera"]["port"])
cap.set(cv2.CAP_PROP_FRAME_WIDTH , cam_w)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_h)

print('Input ID number:', end='')
id_number=input()
print('Input name:', end='')
name=input()

print('Hit \'(SPACE)\' key to capture an image.')
print('Hit \'(ESC)\' key to exit.')
print('Note: \'cam\' window must be active (selected)')
key=0
num=0
while key!=27:  #ESC key to exit
    _, img = cap.read()
    cv2.imshow('cam', img)
    key = cv2.waitKey(1)
    if key==ord(' '):
        fn = os.path.join(config["system"]["image_dir"], '{}-{}-{}.jpg'.format(id_number, name, num))
        cv2.imwrite(fn, img)
        print('captured:', fn)
        num+=1
