import pycom
pycom.wifi_on_boot(False) # turn off BE and  WIFI (replace with True to reverse)
pycom.nvc_erase_all() # erase nvram stored values


#### write to memory

sd = machine.SD()
try:
	os.mount(sd, '/sd')
except OSError:
    print('SD already mounted')
	
f = open('/sd/test.txt', 'a+')
f.write(str(temp)+'\n')
f.close()