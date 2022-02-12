from machine import UART
import machine
import pycom
import os
from network import Bluetooth

# disable the heartbeat LED
pycom.heartbeat(False)

# Disable bluetooth
bluetooth = Bluetooth()
bluetooth.deinit()

uart = UART(0, baudrate=115200)
os.dupterm(uart)

machine.main('main.py')