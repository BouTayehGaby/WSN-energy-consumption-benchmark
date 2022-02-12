import time
import config
import machine
from pysense import Pysense

py = Pysense()

nbIteration = pycom.nvs_get('nbIteration')

if nbIteration is None:
	nbIteration = 0
	pycom.nvs_set('nbIteration',0)
else:
	nbIteration=nbIteration+1
	pycom.nvs_set('nbIteration',int(nbIteration))

print('woke')
time.sleep(0.1)
py.setup_sleep(60)
py.go_to_sleep()


			

