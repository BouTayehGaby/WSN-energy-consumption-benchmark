from pysense import Pysense
from SI7006A20 import SI7006A20
import time
import config
import machine
import pycom
		
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
DELAY=0.1

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
		
def truncate(n, decimals=0):
	multiplier = 10 ** decimals
	return int(n * multiplier) / multiplier
	
	
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
	
	time.sleep(DELAY)
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
	
	print("Prediction:"+str(prediction)+", Real:"+str(newTemp))
	
	if err>maxerr:
		print("counter:"+str(counter)+", err"+str(err)+"-->"+str(newTemp))
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
		
		print('Sending Next round')	

		tCounter=tCounter+1;
		print('################## TCounter is: '+str(tCounter)+' #####################')
		pycom.nvs_set('tCounter',tCounter)
		
		pycom.nvs_set('send',1)
		
		time.sleep(DELAY)
		py.setup_sleep(sleeptime)
		py.go_to_sleep()
		
	else:
		print("err"+str(err)+"-x->"+str(newTemp))
		counter=counter+1
		trh=trh+1
		oldTemp=prediction
		pycom.nvs_set('oldTemp',int(oldTemp*10))
		pycom.nvs_set('counter',counter)
		pycom.nvs_set('trh',trh)
		
		pycom.nvs_set('send',0)
		time.sleep(DELAY)
		py.setup_sleep(sleeptime)
		py.go_to_sleep()
		

