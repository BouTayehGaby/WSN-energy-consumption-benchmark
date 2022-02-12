from pysense import Pysense
from SI7006A20 import SI7006A20
import time

py = Pysense()
si = SI7006A20(py)

nbIteration = pycom.nvs_get('nbIteration')

if nbIteration is None:
	nbIteration = 0
	pycom.nvs_set('nbIteration',0)
else:
	nbIteration=nbIteration+1
	pycom.nvs_set('nbIteration',int(nbIteration))

temp=si.temperature()
print(temp)
time.sleep(0.1)
py.setup_sleep(60)
py.go_to_sleep()


			

