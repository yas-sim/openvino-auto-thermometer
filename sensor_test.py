import sys, os
import logging
import serial

from submodules.mlx90614 import *

logging.basicConfig(level=[logging.INFO, logging.DEBUG, logging.WARN, logging.ERROR][0])

com_port = find_thermo_sensor()
if com_port is None:
    logging.critical('Thermal sensor is not attached.')
    sys.exit(1)
logging.info('{} will be used to communicate with the thermo image sensor'.format(com_port))

# Open serial port (COM port) for Arduino (Adafruit Qwiic Pro Micro USB-C)
try:
    com_speed = 115200
    com = serial.Serial(com_port, com_speed, timeout=3)
except serial.serialutil.SerialException:
    logging.critical('Failed to open serial port \'{}\''.format(com_port))
    sys.exit(1)
com.reset_input_buffer();

while True:
    distance, object_temp, ambient_temp = receive_temp_data(com)
    logging.info('{:4.2f}cm {:4.2f}C {:4.2f}C'.format(distance, object_temp, ambient_temp))
