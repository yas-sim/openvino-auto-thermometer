import os

import cv2

from config import *

cam_w = 640
cam_h = 480

cap=cv2.VideoCapture(0)
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
        fn = os.path.join(image_dir, '{}-{}-{}.jpg'.format(id_number, name, num))
        cv2.imwrite(fn, img)
        print('captured:', fn)
        num+=1
