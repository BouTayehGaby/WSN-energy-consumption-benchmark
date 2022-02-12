from pysense import Pysense
from SI7006A20 import SI7006A20
import time
import machine
import pycom
import os
from array import array
import math
from network import WLAN
import urequests as requests


######################################Adaptive sampling settings########################################################
pSize=5; #period size (how many values are sensed during each period)
R = 0.4 # application criticality.
Ht=5.991
St =pSize # number of measurement sensed each period.
sMax=pSize
sMin=1
round=2 #each round consits of two periods
#used in the formula of Kruskal Wallis
sum=0;
DELAY = 0.1  # Delay in seconds
fixedSleepTime=60

####################################TR Settings##########################################################################
maxerr=0.5
###########Reading stored values in NVRAM (protected against deepsleep wake up reset)
flag = pycom.nvs_get('flag')
alpha = pycom.nvs_get('alpha')
trh = pycom.nvs_get('trh')
counter = pycom.nvs_get('counter')
tCounter = pycom.nvs_get('tCounter')
send = pycom.nvs_get('send') #flag to see if we need to transmit after reboot (wifi on again)

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
if send is None:
	send = 0
#####################################global intialisation#################################################################
sleeptime = pycom.nvs_get('sleeptime')
countPeriod = pycom.nvs_get('countPeriod')
countRound = pycom.nvs_get('countRound')

if sleeptime is None:
	sleeptime=60
else:
	sleeptime=sleeptime/10
if countPeriod is None:	
	countPeriod=0
if countRound is None:
	countRound=0
	
#############################Retrieve array values from memory################

l1 = pycom.nvs_get('lenp1')
if l1 is None:
	p1=array('i',[]) # Fill values collected in period 1
else:
	p1=array('i',[]) # Fill values collected in period 1
	for i in range(l1):
		index='p1'+str(i)
		p1.append(int(pycom.nvs_get(index)/10))
		
l2 = pycom.nvs_get('lenp2')
if l2 is None:
	p2=array('i',[]) # Fill values collected in period 2
else:
	p2=array('i',[]) # Fill values collected in period 1
	for i in range(l2):
		index='p2'+str(i)
		p2.append(int(pycom.nvs_get(index)/10))
	
###########################################################################

py = Pysense()
si = SI7006A20(py)

#################################### Functions Definition#################################################################

###################################This function combines two array and return the one array containing the rank of each value in both arrays
def rank(p1,p2): 
	A=p1+p2
	# Rank Vector 
	R = [0 for x in range(len(A))] 

	for i in range(len(A)): 
		(r, s) = (1, 1) 
		for j in range(len(A)): 
			if j != i and A[j] < A[i]: 
				r += 1
			if j != i and A[j] == A[i]: 
				s += 1	
		
		# Use formula to obtain rank 
		R[i] = r + (s - 1) / 2

	# Return Rank Vector 
	return R 

####################################This function returns the new sampling inerval #####################################################
def behavior(H,Ht,R,sMax):

	b0=array('f',[0,0])
	b1=array('f',[0,0])
	b2=array('f',[0,0])

	b2[0]=Ht
	b2[1]=sMax

	#calcul b1
	b1[0]= -b2[0]*R+b2[0]
	b1[1]= b2[1]*R

	#calcul b0 (Carol)
	b0[0]=0
	b0[1]=sMin

	print('Pre Alfaf1: ',b1[0]*b1[0])
	print('Pre Alfaf2: ',-2*b1[0]*H)
	print('Pre Alfaf3: ',b2[0]*H)
	print('Pre Alfaf: ',(b1[0]*b1[0])-(2*b1[0]*H)+(b2[0]*H))
	AlfaF= (-b1[0]+math.sqrt(b1[0]*b1[0]-2*b1[0]*H+b2[0]*H))/(b2[0]-2*b1[0])
	print('Alfaf is: ',AlfaF)

	if((b2[0]-2*b1[0]) == 0):
		BV=(((b2[1]-2*b1[1])*H*H)/(4*b1[0]*b1[0]))+((b2[1]/b1[0])*Ht)

	else:
		BV=((b2[1]-2*b1[1])*(AlfaF*AlfaF))+(2*b1[1]*AlfaF)

	if (BV<1):
		BV=sMin
	
	return math.ceil(BV)
	
def connectWiFi():
	TOKEN = "Put here your TOKEN" #Put here your TOKEN

	wlan = WLAN(mode=WLAN.STA)
	wlan.antenna(WLAN.INT_ANT)

	# Assign your Wi-Fi credentials
	wlan.connect("Wi-Fi name", auth=(WLAN.WPA2, "password"), timeout=5000)

	while not wlan.isconnected ():
		machine.idle()
	print("Connected to Wifi\n")

# Builds the json to send the request
def build_json(variable1, value1):
    try:
        data = {variable1: {"value": value1}}
        return data
    except:
        return None

# Sends the request. Please reference the REST API reference https://ubidots.com/docs/api/
def post_var(device, value1):
    try:
        url = "https://industrial.api.ubidots.com/"
        url = url + "api/v1.6/devices/" + device
        headers = {"X-Auth-Token": TOKEN, "Content-Type": "application/json"}
        data = build_json("temp", value1)
        if data is not None:
            print(data)
            req = requests.post(url=url, headers=headers, json=data)
            return req.json()
        else:
            pass
    except:
        pass

###############################This fucntion is to simply reduce the accuracy of the collected measurement to one value after the break point (ex: 11.2 instead of 11.2325)######################	
def truncate(n, decimals=0):
	multiplier = 10 ** decimals
	return int(n * multiplier) / multiplier


if send==1:
	oldTemp = pycom.nvs_get('oldTemp')/10
	#Connect to WiFi And Send Packet if previously a packet needed to be sent (couldn't be sent previously because wifi was off)
	connectWiFi()
	post_var("pycom", oldTemp)
	time.sleep(DELAY)
	
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
		
	connectWiFi()
	post_var("pycom", newTemp)
	time.sleep(DELAY)
	pycom.wifi_on_boot(False)
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
	
	############################################################################################################
								
	if countPeriod>=pSize:
		countRound=countRound+1
		pycom.nvs_set('countRound',countRound)
		countPeriod=0
		pycom.nvs_set('countPeriod',countPeriod)
	if countRound==round:
		#call the rank function to rank the arrays
		rankedArray=rank(p1,p2)
		H=0
		lenp1=len(p1)
		lenp2=len(p2)
		N=lenp1+lenp2
		r1=0
		r2=0
		
		for i in range(lenp1):
			r1=r1+(rankedArray[i])
		for j in range(lenp2,N):
			r2=r2+(rankedArray[j])
			
		print(r1)
		print(r2)
		sum=((r1**2)/lenp1)+((r2**2)/lenp2)
		H=((12.0/(N*(N+1)))*sum)-3*(N+1)
		
		print('H is: ',H)
		
		if(H<0):
			st=sMin
		elif(H<=Ht):
			st=behavior(H,Ht,R,sMax)
			if st==0:
				st=sMax
		else:	
			st=sMax
		
		print('New St: ',st)			
		
		sleeptime=(fixedSleepTime/st)*sMax
		pycom.nvs_set('sleeptime',int(truncate(sleeptime,1)*10))
		
		print('New sleep time: ',sleeptime)
		print('\n')
		
		countRound=0
		pycom.nvs_set('countRound',countRound)
		countPeriod=0
		pycom.nvs_set('countPeriod',countPeriod)
		p1=array('i',[]) # Clear values of period 1 array
		p2=array('i',[]) # Clear values of period 2 aray
				
	if countRound==0:
		p1.append(int(newTemp))
	if countRound==1:
		p2.append(int(newTemp))
	countPeriod=countPeriod+1
	pycom.nvs_set('countPeriod',countPeriod)
	
	############################################################################################################

	if err>maxerr:
		print("counter:"+str(counter)+", err"+str(err)+"---Send--->"+str(newTemp))

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
		
		pycom.nvs_set('send',1)
		
		pycom.wifi_on_boot(True)
		
		######################store values of P1 and P2 before going to sleep################
		
		if countRound==0:
			l1=len(p1)
			pycom.nvs_set('lenp1',l1)
			for i in range(l1):
				index='p1'+str(i)
				pycom.nvs_set(index,int(p1[i]*10))
		elif countRound==1:
			l2=len(p2)
			pycom.nvs_set('lenp2',l2)
			for i in range(l2):
				index='p2'+str(i)
				pycom.nvs_set(index,int(p2[i]*10))
		
		###################################################################
		tCounter=tCounter+1;
		print('################## TCounter is: '+str(tCounter)+' #####################')
		pycom.nvs_set('tCounter',tCounter)
		py.setup_sleep(sleeptime)
		py.go_to_sleep()
	else:
		print("err"+str(err)+"---not sent x--->"+str(newTemp))				
		counter=counter+1
		trh=trh+1
		oldTemp=prediction
		pycom.nvs_set('oldTemp',int(oldTemp*10))
		pycom.nvs_set('counter',counter)
		pycom.nvs_set('trh',trh)
		
		if countRound==0:
			l1=len(p1)
			pycom.nvs_set('lenp1',l1)
			for i in range(l1):
				index='p1'+str(i)
				pycom.nvs_set(index,int(p1[i]*10))
		elif countRound==1:
			l2=len(p2)
			pycom.nvs_set('lenp2',l2)
			for i in range(l2):
				index='p2'+str(i)
				pycom.nvs_set(index,int(p2[i]*10))
			
		# Nothing to send next iteratin, so we turn the wifi off
		pycom.nvs_set('send',0)
		
		pycom.wifi_on_boot(False)
		
		py.setup_sleep(sleeptime)
		py.go_to_sleep()
		

