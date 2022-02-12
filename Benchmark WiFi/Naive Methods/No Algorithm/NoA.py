from SI7006A20 import SI7006A20
import time
import machine
from pysense import Pysense
from network import WLAN
import urequests as requests


py = Pysense()
si = SI7006A20(py)

TOKEN = "Put here your TOKEN" #Put here your TOKEN
DELAY = 0.1  # Delay in seconds

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

####################################Application Settings##################################################################

temp=(si.temperature() + 273.15)*100 #convert to kelvins to avoid negative values
post_var("pycom", temp)
time.sleep(DELAY)
py.setup_sleep(60)
py.go_to_sleep()


			

