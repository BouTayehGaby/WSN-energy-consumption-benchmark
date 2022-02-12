from SI7006A20 import SI7006A20
from pysense import Pysense
from network import LoRa
import socket
import binascii
import struct
import time
import config
import struct
from pysense import Pysense

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
	
py = Pysense()
si = SI7006A20(py)


nbIteration = pycom.nvs_get('nbIteration')

if nbIteration is None:
	nbIteration = 0
	pycom.nvs_set('nbIteration',0)
else:
	nbIteration=nbIteration+1
	pycom.nvs_set('nbIteration',int(nbIteration))
	
####################################Application Settings##################################################################

temp=(si.temperature() + 273.15)*100 #convert to kelvins to avoid negative values
pkt=b'5D4A1517FA5B7B25617635F783EE1C81E732233F9D8116B5EDA49E189F60B3CCF79F589BB02B5FA2673379E3C7C5C695C46F805EE2137605EB'
pkt+=int(temp).to_bytes(2,'little')
print('Sending:', pkt)
s.send(pkt)
time.sleep(0.1)
py.setup_sleep(60)
py.go_to_sleep()


			

