import logging
import serial
import serial.tools.list_ports

from color_table import *
from config import *

def receive_temp_data(com):
    while True:
        line = com.readline().decode('utf-8').replace('\n', '').replace('\r', '')
        if len(line)==0:
            logging.warning('COM port ({}) timed out. A wrong port is specified possibly.'.format(com_port))
            continue
        if line[0] == '%':
            line_data = line[1:].split(',')
            if len(line_data)!=3:
                continue            # irregular data is captured
            dist     = float(line_data[0])
            temp_obj = float(line_data[1])
            temp_amb = float(line_data[2])
            return dist, temp_obj, temp_amb

def temp_compensation(t_obj, t_amb, ofst=0):
    #offset = -0.323333 * t_amb + 13.9 + ofst    # original (intercept=13.9)
    #offset = -0.323333 * t_amb + 11.6 + ofst
    offset = -0.2 * t_amb + 7.3 + ofst
    return t_obj + offset

def find_thermo_sensor():
    com_port = None
    available_com_ports = serial.tools.list_ports.comports()
    for com in available_com_ports:
        if com.vid is None:
            pid, vid = 0, 0
        else:
            pid, vid = com.pid, com.vid
        logging.debug('COM port {}, PID, {:04x}, VID {:04x}'.format(com.device, pid, vid))
        if pid == 0x9206 and vid == 0x1b4f:     # PID(0x9206 == Pro micro Arduino, VID(0x1b4f) == SparkFun)
            com_port = com.device
    return com_port
