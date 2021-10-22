import sys, os
import logging
import serial
import time

from submodules.mlx90614 import *

logging.basicConfig(level=[logging.INFO, logging.DEBUG, logging.WARN, logging.ERROR][0])

sensor = mlx90614()
sensor.open()

if sensor.com_port is None:
    logging.critical("Sensor is not attached.")
    sys.exit(1)

while True:
    try:
        distance, object_temp, ambient_temp = sensor.receive_temp_data()
    except serial.serialutil.SerialException:
        while True:
            logging.info("Trying to re-open temp sensor")
            time.sleep(1)
            try:
                del sensor
                sensor = mlx90614()
                sensor.open()
                break
            except:
                pass


    logging.info('{:4.2f}cm {:4.2f}C {:4.2f}C'.format(distance, object_temp, ambient_temp))
