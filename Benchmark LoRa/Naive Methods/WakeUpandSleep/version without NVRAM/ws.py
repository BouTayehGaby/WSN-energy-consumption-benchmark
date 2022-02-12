import time
import config
import machine
from pysense import Pysense

py = Pysense()

print('woke')
time.sleep(0.1)
py.setup_sleep(60)
py.go_to_sleep()


			

