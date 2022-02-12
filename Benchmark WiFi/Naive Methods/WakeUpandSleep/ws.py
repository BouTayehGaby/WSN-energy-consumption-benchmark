import time
import config
from pysense import Pysense

print('woke')

py = Pysense()
time.sleep(0.1)
py.setup_sleep(60)
py.go_to_sleep()


			

