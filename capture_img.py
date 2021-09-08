import cv2

cam_w = 640
cam_h = 480

cap=cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH , cam_w)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_h)

print('input number:', end='')
number=input()
print('input name:', end='')
name=input()

print('Hit \'(SPACE)\' key to capture an image.')
print('Hit \'(ESC)\' key to exit.')
key=0
num=0
while key!=27:  #ESC key to exit
    _, img = cap.read()
    cv2.imshow('cam', img)
    key = cv2.waitKey(1)
    if key==ord(' '):
        fn = './face_db/{}-{}-{}.jpg'.format(number, name, num)
        cv2.imwrite(fn, img)
        print('captured:', fn)
        num+=1
