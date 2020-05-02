#x16126602
#my_iot_application.py
#IoT Application Development
#National College of Ireland
#08th March 2020

from datetime import datetime
import time
import math
import grovepi
import threading
from grovepi import *
import json
from threading import Thread
import paho.mqtt.client as mqtt #Imports MQTT client structure from the packeage that have been downloaded

temp_humidity_sensor = 7 #Port Number D7
light_sensor = 1 #Port Number A1
sound_sensor = 0 #Port Number A0

led = 5 #D5

#Temp humidity sensor type.  You can use the blue or the white version.
#Note the GrovePi Starter Kit comes with the blue sensor
blue=0
white=1
therm_version = blue            # If you change the thermometer, this is where you redefine.

#Below we define our variables' state
publishing = True
listening = True
publishing_thread = None
listen_thread = None
terminate = False

ADDRESS_BROKER = 'broker.mqttdashboard.com'
CLIENT_ID_LISTENER = 'clientId-TkWjA2GMp'
CLIENT_ID_PUBLISHER = 'clientId-wr3GO0UfLF'
MY_TOPIC = 'myIoT/publisher'
MY_SUBSCRIBER = 'myIoT/listener'

client = None

#Below we asign the I/O type for each sensor
pinMode(light_sensor, "INPUT")
pinMode(sound_sensor, "INPUT")

pinMode(led, "OUTPUT")

#The function below is used to deal with the sound sensor
def my_sound_readings():
    sound_intensity = grovepi.analogRead(sound_sensor)
    return(sound_intensity,'db')

#The function below is used to deal with the light sensor
def my_light_readings():
    light_intensity = grovepi.analogRead(light_sensor)
    return(light_intensity)
    
#The function below is used to deal with the temperature and humidity sensors
def my_tem_hum_readings():
    [temp,humidity] = grovepi.dht(temp_humidity_sensor, therm_version)
        
    #Return -1 in case of bad temp/humidity sensor reading
    if math.isnan(temp) or math.isnan(humidity):        #temp/humidity sensor sometimes gives nan
        return [-1,-1,-1,-1]
           
    return [temp,humidity]		

#The client sends a CONNECT message and the MQTT Broker sends a CONNACK message back
def on_connect(client, userdata, flags, reasonCode, properties):
    print('Connected to MQTT Broker')
    print('Connection flags=%s' % flags)
    print('Reason Code=%s' % reasonCode)
    print('Properties=%s' % properties)
   
#The function below is used for when a PUBLISH message is received from the server
def on_publish(client, userdata, mid):
    print('Published to=%s' % mid)
    
def on_subscribe(client, userdata, mid, reasonCode, properties):
    print('Subscribed to=%s' % mid)
    print('Reason Code=%s' % reasonCode)
    print('Properties=%s' % properties)
    
def on_message(client, userdata, message):
    str_message = str(message.payload.decode('utf-8'))
    print('Message received=%s' % str_message)
    print('Message topic=%s' % (message.topic))
	
    #try
	#Below we convert our message into json format
    message = json.loads(str_message)
    global publishing
    global publishing_thread
    
    if message.get('terminate'):
        global terminate
        global listening
        listening = False
        publishing = False
        client.disconnect()
        client.loop_stop()
        terminate = True

    if message.get('publishing'):
        publishing = True
        print('publish')
        if not  publishing_thread.is_alive():
            print('thread not alive')
            publishing_thread = Thread(target=publish)
            publishing_thread.daemon = True
            publishing_thread.start()
        else:
            publishing = False
            print("Not Publishing")
               
#The function below publishes the readings from my sensors to the MQTT Broker after reading them
def publish():
    client = start_client(CLIENT_ID_PUBLISHER)########
    
    while publishing:
        sensor_sound = my_sound_readings()
        sensor_light = my_light_readings()
        temp_hum_level = my_tem_hum_readings()    
        
        readings = {
            'timestamp': datetime.now().isoformat(),
            'Sound Level': sensor_sound,
            'Light Level': sensor_light,
            'Temperature and Humidity Levels': temp_hum_level
        }
        
        client.publish(MY_TOPIC, json.dumps(readings))
        print('Published readings: ', readings)
        client.loop(.1)
        time.sleep(2.5)
    print('Stop publishing')
    
#The function below listens to all the messages from my pre-defined topic
def listen(publisher):	
    client = start_client(CLIENT_ID_LISTENER)
    client.subscribe(MY_SUBSCRIBER)
    print('We are subscribed to the topic!!!')
    while listening:
        client.loop(.1)
    
#The function below starts my MQTT client and connects to the Broker then we loop through
def start_client(client_id):
	
	#Below we create an MQTT client and attach our routines to it
    client = mqtt.Client(client_id)
    client.connect(ADDRESS_BROKER)
    client.on_connect=on_connect
    client.on_publish=on_publish
    client.on_subscribe=on_subscribe
    client.on_message=on_message
    return client

#The function below is the main one regarding my program
def main():
    global publishing_thread
    global listen_thread
    publishing_thread = Thread(target=publish)
    publishing_thread.daemon = True
    listen_thread = Thread(target=listen, args=(publishing_thread,))
    listen_thread.daemon = True
    listen_thread.start()
    
    while terminate == False:
        pass
    
if __name__ == '__main__':
    try:
        main()
        
    except KeyboardInterrupt:
        sys.exit(0)
        
