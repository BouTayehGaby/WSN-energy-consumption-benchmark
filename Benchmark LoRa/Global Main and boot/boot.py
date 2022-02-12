from machine import UART
import machine
import pycom
import os

# disable the heartbeat LED
pycom.heartbeat(False)

uart = UART(0, baudrate=115200)
os.dupterm(uart)

machine.main('main.py')