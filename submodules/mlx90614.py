import sys
import logging
import json
import serial
import serial.tools.list_ports

from color_table import *

class mlx90614:
    def __init__(self):
        with open('thermometer_cfg.json', 'rt') as f:    # read configurations from the configuration file
            self.com_port = None
            self.com_port_device = None
            self.config = json.load(f)

    def __del__(self):
        if not self.com_port is None:
            self.com_port.close()

    def receive_temp_data(self):
        while True:
            line = self.com_port.readline().decode('utf-8').replace('\n', '').replace('\r', '')
            if len(line)==0:
                logging.warning('COM port ({}) timed out. A wrong port is specified possibly.'.format(self.com_port))
                continue
            if line[0] == '%':
                line_data = line[1:].split(',')
                if len(line_data)!=3:
                    continue            # irregular data is captured
                dist     = float(line_data[0])
                temp_obj = float(line_data[1])
                temp_amb = float(line_data[2])
                return dist, temp_obj, temp_amb

    def temp_compensation(self, t_obj, t_amb, ofst=0):
        coefficient = self.config['temp_compensation']['coefficient']
        intercept = self.config['temp_compensation']['intercept']
        offset = coefficient * t_amb + intercept + ofst
        return t_obj + offset

    def find_thermo_sensor(self):
        self.com_port_device = None
        available_com_devices = serial.tools.list_ports.comports()
        for device in available_com_devices:
            if device.vid is None:
                pid, vid = 0, 0
            else:
                pid, vid = device.pid, device.vid
            logging.debug('COM port {}, PID, {:04x}, VID {:04x}'.format(device.device, pid, vid))
            if pid == 0x9206 and vid == 0x1b4f:     # PID(0x9206 == Pro micro Arduino, VID(0x1b4f) == SparkFun)
                self.com_port_device = device.device

    def open(self):
        self.find_thermo_sensor()
        if self.com_port_device is None:
            logging.critical('Thermal sensor is not attached.')
            sys.exit(1)
        logging.info('{} will be used to communicate with the thermo sensor'.format(self.com_port_device))

        # Open serial port (COM port) for Arduino (Adafruit Qwiic Pro Micro USB-C)
        try:
            com_speed = self.config['com_port']['speed']
            self.com_port = serial.Serial(self.com_port_device, com_speed, timeout=3)
        except serial.serialutil.SerialException:
            logging.critical('Failed to open serial port \'{}\''.format(self.com_port_device))
            sys.exit(1)
        self.com_port.reset_input_buffer();
