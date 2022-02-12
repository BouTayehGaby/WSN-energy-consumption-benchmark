from SI7006A20 import SI7006A20
import time
import config
import machine
import pycom
from pysense import Pysense
		
py = Pysense()
si = SI7006A20(py)


####################################Application Settings##################################################################
maxerr=0.5

flag = pycom.nvs_get('flag')
alpha = pycom.nvs_get('alpha')
trh = pycom.nvs_get('trh')
counter = pycom.nvs_get('counter')
tCounter = pycom.nvs_get('tCounter')
sleeptime = 60

if flag is None:
	flag = 0
if alpha is None:
	alpha=1
if trh is None:
	trh=1
if counter is None:
	counter=0
if tCounter is None:
	tCounter=0	
pkt=b'5D4A1517FA5B7B25617635F783EE1C81E732233F9D8116B5EDA49E189F60B3CCF79F589BB02B5FA2673379E3C7C5C695C46F805EE2137605EB'

#########################################################################################################################

### if there is no transmission there is no need to conenct Lora at every wake up
def connectLora(pkt):
	from network import LoRa
	import socket
	import binascii
	import struct
	lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
	lora.bandwidth(LoRa.BW_125KHZ)
	lora.sf(12)


	# create an ABP authentication params
	dev_addr = struct.unpack(">l", binascii.unhexlify('0860018D'))[0]
	nwk_swkey = binascii.unhexlify('d0fafdb372116b6cad25e0fb4d0be328')
	app_swkey = binascii.unhexlify('f2f2537e1bb4ca410b6d29e9c55b7dbe')

	# remove all the non-default channels
	for i in range(3, 16):
		lora.remove_channel(i)

	# set the 3 default channels to the same frequency
	lora.add_channel(0, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
	lora.add_channel(1, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
	lora.add_channel(2, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)

	# join a network using ABP (Activation By Personalization)
	lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))

	# create a LoRa socket
	s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

	# set the LoRaWAN data rate
	s.setsockopt(socket.SOL_LORA, socket.SO_DR, config.LORA_NODE_DR)

	# make the socket non-blocking
	s.setblocking(False)
	s.send(pkt)
	time.sleep(0.1)


def truncate(n, decimals=0):
	multiplier = 10 ** decimals
	return int(n * multiplier) / multiplier
	
	
nbIteration = pycom.nvs_get('nbIteration')

if nbIteration is None:
	nbIteration = 0
	pycom.nvs_set('nbIteration',0)
else:
	nbIteration=nbIteration+1
	pycom.nvs_set('nbIteration',int(nbIteration))
	
#Collect firt measurement
if flag==0:
	oldTemp=truncate(si.temperature(),1)
	flag=1
	pycom.nvs_set('flag',flag)
	pycom.nvs_set('oldTemp',int(oldTemp*10))
	py.setup_sleep(sleeptime)
	py.go_to_sleep()
	
#Collect second measurement and calculate slope	
if flag==1:
	from network import LoRa
	import socket
	import binascii
	import struct
	oldTemp = pycom.nvs_get('oldTemp')/10
	newTemp=truncate(si.temperature(),1)
	CR= newTemp - oldTemp
	lastTemp=newTemp
	flag=2
	
	#######Save values in memory######
	pycom.nvs_set('lastTemp',int(lastTemp*10))
	pycom.nvs_set('flag',flag)
	pycom.nvs_set('CR',int(CR*10))
	pycom.nvs_set('oldTemp',int(oldTemp*10))
	pycom.nvs_set('counter',0)
	pycom.nvs_set('tCounter',0)
	pycom.nvs_set('alpha',1)
	##################################
	
	pkt=b'5D4A1517FA5B7B25617635F783EE1C81E732233F9D8116B5EDA49E189F60B3CCF79F589BB02B5FA2673379E3C7C5C695C46F805EE2137605EB'
	pkt+=int(newTemp).to_bytes(2,'little')
	connectLora(pkt)
	py.setup_sleep(sleeptime)
	py.go_to_sleep()
	
#From now on predict and correct slope	
elif flag==2:

	oldTemp = pycom.nvs_get('oldTemp')/10
	CR = pycom.nvs_get('CR')/10
	lastTemp = pycom.nvs_get('lastTemp')/10
	alpha = pycom.nvs_get('alpha')/10
	
	prediction = truncate(oldTemp+CR*alpha,1)
	newTemp=truncate(si.temperature(),1)
	err= abs(newTemp-prediction)
	
	print("Prediction: "+str(prediction)+", Real: "+str(newTemp))
	
	if err>maxerr:
		print("counter:"+str(counter)+", err"+str(err)+"-->"+str(newTemp))
		currTemp=(newTemp + 273.1)*100 		#convert to kelvins to avoid negative values
		pkt=b'5D4A1517FA5B7B25617635F783EE1C81E732233F9D8116B5EDA49E189F60B3CCF79F589BB02B5FA2673379E3C7C5C695C46F805EE2137605EB'
		pkt+=int(currTemp).to_bytes(2,'little') #Multiplying by 100 to store temperature integers while keeping the resolution of 2 fraction digits.
		CR= (newTemp-lastTemp)/trh
		pycom.nvs_set('CR',int(CR*10))
	
		if trh==1:
			AF=(newTemp-prediction)
		else:
			AF=(newTemp-prediction)/(trh-1)
			
		if abs(AF)<maxerr and AF<maxerr and abs(AF)>10**(-4):
			bool=1
		else:
			bool=0
			alpha=0.5
		
		if bool==1:
			P=AF*100/maxerr
			alpha=alpha-(P*alpha/100)
			if alpha>1:
				alpha=1
					
		pycom.nvs_set('alpha',int(truncate(alpha,1)*10))
		
		oldTemp=newTemp	
		pycom.nvs_set('oldTemp',int(oldTemp*10))
		
		lastTemp=newTemp
		pycom.nvs_set('lastTemp',int(lastTemp*10))

		trh=1
		counter=counter+1
		pycom.nvs_set('trh',trh)
		pycom.nvs_set('counter',counter)
		
		connectLora(pkt)
		print('Sending: ', pkt)	
		
		tCounter=tCounter+1;
		print('################## TCounter is: '+str(tCounter)+' #####################')
		pycom.nvs_set('tCounter',tCounter)
		
		py.setup_sleep(sleeptime)
		py.go_to_sleep()
	else:
		print("err: "+str(err)+" -x-> "+str(newTemp))
		counter=counter+1
		trh=trh+1
		oldTemp=prediction
		pycom.nvs_set('oldTemp',int(oldTemp*10))
		pycom.nvs_set('counter',counter)
		pycom.nvs_set('trh',trh)
		
		py.setup_sleep(sleeptime)
		py.go_to_sleep()

