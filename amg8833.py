import serial

from color_table import *

def capture_thermo_frame(com_port):
    global ambient_temp
    thermo_txt_buf = ''
    read_thermo_frame = False
    thermo_frame_start = False
    while True:
        line = com_port.readline().decode('utf-8').replace('\n', '').replace('\r', '')
        if line[0] == '@':
            ambient_temp = float(line[1:])      # ambient temperature
            read_thermo_frame = True
            continue
        if read_thermo_frame == False:
            continue
        if line[0] == '[':
            tmermo_txt_buf = ''
            thermo_frame_start = True
            continue
        if line[0] == ']' and thermo_frame_start:
            break
        if thermo_frame_start:
            thermo_txt_buf += line

    thermo = [ float(dt) for dt in thermo_txt_buf.split(',') ]

    return thermo, ambient_temp

def color_interpolate(dt):
    global color_table
    col = (0,0,255)
    for idx in range(1, len(color_table)):
        if dt < color_table[idx][0]:
            t1, c1 = color_table[idx-1]
            t2, c2 = color_table[idx  ]
            mix = (dt-t1) / (t2-t1)
            col = [ (c2[0]-c1[0])*mix+c1[0],    # B
                    (c2[1]-c1[1])*mix+c1[1],    # G
                    (c2[2]-c1[2])*mix+c1[2]]    # R
            break
    return col

def color_map(img, ofst=0):
    return [ color_interpolate(dt+ofst) for dt in img ]

def temp_compensation(thermo, t_amb, ofst=0):
    offset = -0.323333 * t_amb + 13.9 + ofst    # original (intercept=13.9)
    #offset = -0.323333 * t_amb + 11.6 + ofst
    #print(t_amb, offset)
    return [ t+offset for t in thermo ]
