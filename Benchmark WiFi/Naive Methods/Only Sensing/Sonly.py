from pysense import Pysense
from SI7006A20 import SI7006A20
import time
import config
import machine

py = Pysense()
si = SI7006A20(py)

temp=si.temperature()
print(temp)
time.sleep(0.1)
py.setup_sleep(60)
py.go_to_sleep()


			

