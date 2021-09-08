import cv2

face_w = 300
face_h = 300

cam_w = 640
cam_h = 480

cap=cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH , cam_w)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_h)

x1=(cam_w-face_w)>>1
y1=(cam_h-face_h)>>1
x2=(cam_w+face_w)>>1
y2=(cam_h+face_h)>>1

print('input name:', end='')
name=input()

key=0
num=0
while key!=27:  #ESC key to exit
    _, img = cap.read()
    cv2.rectangle(img, (x1,y1), (x2,y2), (255,255,0), 4 )
    cv2.imshow('cam', img)
    key = cv2.waitKey(1)
    if key==ord(' '):
        face=img[y1:y2,x1:x2]
        cv2.imshow('captured', face)
        cv2.imwrite('./face_gallery/{}-{}.jpg'.format(name, num), face)
        num+=1
