#x16126602
#my_iot_application.py
#IoT Application Development
#National College of Ireland
#April 2020

from datetime import datetime
import time
import math
import grovepi
import threading
from grovepi import *
import json
from threading import Thread
import paho.mqtt.client as mqtt #Imports MQTT client structure from the packeage that have been downloaded

#Below we define our variables' state
publishing = True
listening = True
publishing_thread = None
listen_thread = None
terminate = False
buttonPressed = False

ADDRESS_BROKER = 'broker.mqttdashboard.com'
MY_TOPIC = 'myIoT/publisher'
client = None     

#Simple Sensor class that definies a template and sets port number and mode (input - output) for all the sensors in the program
class Sensor():
    def __init__(self, port, mode):
        self.port = port
        self.mode = mode

#Lights class responsible for controlling all the LEDs in the program, definiyng commmun proprerties in the constructor
class Lights():
    def __init__(self):  #Inicialization - constructor      
        self.sensorRedLed = Sensor(8, "OUTPUT")
        grovepi.pinMode(self.sensorRedLed.port, self.sensorRedLed.mode)    #Assign port and mode for red LED as output

        self.sensorGreenLed = Sensor(6, "OUTPUT")
        grovepi.pinMode(self.sensorGreenLed.port, self.sensorGreenLed.mode)  #Assign port and mode for green LED as output

        self.sensorBlueLed = Sensor(5, "OUTPUT")
        grovepi.pinMode(self.sensorBlueLed.port, self.sensorBlueLed.mode)   #Assign port and mode for blue LED as output
        
        potentiometer = Sensor(2, "OUTPUT")
        # Read resistance from Potentiometer
        self.i = grovepi.analogRead(potentiometer.port)
        
    #Method that turns LED Red On and the others OFF
    def setRedLedON(self):
        grovepi.analogWrite(self.sensorRedLed.port, self.i//4)
        grovepi.analogWrite(self.sensorBlueLed.port,0)
        grovepi.analogWrite(self.sensorGreenLed.port,0)

    ##Method that turns LED Blue On and the others OFF
    def setBlueLedON(self):
        grovepi.analogWrite(self.sensorRedLed.port,0)
        grovepi.analogWrite(self.sensorBlueLed.port, self.i//4)
        grovepi.analogWrite(self.sensorGreenLed.port,0)
        
    #Method that turns LED Green On and the others OFF
    def setGreenLedON(self):
        grovepi.analogWrite(self.sensorRedLed.port,0)
        grovepi.analogWrite(self.sensorBlueLed.port,0) 
        grovepi.analogWrite(self.sensorGreenLed.port, self.i//4)

#ReadingsReceiver responsible for the readings of the sensors INPUT mode
class ReadingsReceiver():
    
    #Method responsible for reading the temperature and humidity sensors
    def my_tem_hum_readings(self):
        
        sensorTemperatureHumidity = Sensor(7, "INPUT")
        pinMode(sensorTemperatureHumidity.port, sensorTemperatureHumidity.mode)
        
        [temp,humidity] = grovepi.dht(sensorTemperatureHumidity.port, 0) #0 Means sensorHumidity.version = StartKit
            
        #Return -1 in case of bad temp/humidity sensor reading
        if math.isnan(temp) or math.isnan(humidity):        #temp/humidity sensor sometimes gives nan
            return [-1,-1,-1,-1]
               
        return [temp,humidity]		

    #Method responsible for reading the light sensor
    def my_light_readings(self):
        
        sensorLight = Sensor(1, "INPUT")
        pinMode(sensorLight.port,sensorLight.mode)
        light_intensity = grovepi.analogRead(sensorLight.port)
        
        return(light_intensity)

    #Method responsible for reading the sound sensor
    def my_sound_readings(self):
        
        sensorSound = Sensor(0, "INPUT")
        pinMode(sensorSound.port, sensorSound.mode)
        sound_intensity = grovepi.analogRead(sensorSound.port)
        
        return(sound_intensity,'db')

#Buzzer class responsible for the Buzzer sensor
class Buzzer():
    
    #Set the button to false
    pressed = False
    
    def __init__(self): #Inicialization - constructor  
        
        #Below we set the buzzer port and mode type
        self.sensorBuzzer = Sensor(3, "OUTPUT")
        
    #Below we set the buzzer port and set it ON
    def buzzerON(self):
        digitalWrite(self.sensorBuzzer.port,3)
        
    #Below we set the buzzer port and set it ON
    def buzzerOFF(self):
        digitalWrite(self.sensorBuzzer.port,0)

    #Below we check if the ultrasonic ranger sensor is blocked by <= 10cm and trigger the buzzer, if what is blocking it is removed then the buzzer stops
    def buzzerBlock(self):    
        
        sensorUltrasonicRanger = Sensor(2, "INPUT")        
        pinMode(sensorUltrasonicRanger.port, sensorUltrasonicRanger.mode)   
             
        pinMode(self.sensorBuzzer.port, self.sensorBuzzer.mode)
        
        distant = ultrasonicRead(sensorUltrasonicRanger.port)
        
        #Prints the distance from the ultrasonic ranger
        print(distant,'cm')
        
        #If the distance is <=10cm the buzzer gets triggered
        if distant <= 10:
            digitalWrite(self.sensorBuzzer.port,3)  
            
        #If the distance is >10cm the buzzer gets turned OFF
        else:
            digitalWrite(self.sensorBuzzer.port, 0)
                   
    #If the button is pressed the buzzer stops
    def buttonPress(self):

        global buttonPressed
        
        sensorButton = Sensor(4, "INPUT")
        
        #Sets the button mode
        pinMode(sensorButton.port, sensorButton.mode)
        
        #Sets the button port
        button_status= digitalRead(sensorButton.port)

        #Check if the buzzer is triggered, if it is then stops it
        if button_status:            
            digitalWrite(self.sensorBuzzer.port,0)
            buttonPressed = True

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
    
    if message.get('SwitchOn'):
        grovepi.analogWrite(sensorBlueLed.port,1)
        grovepi.analogWrite(sensorRedLed.port,1)
        digitalWrite(sensorBuzzer.port,1)    
        
    if message.get('SwitchOff'):
        
        from subprocess import call
        call("sudo nohup shutdown -h now", shell=True)       

    if message.get('terminate'):    
        
        from subprocess import call
        #call("sudo nohup shutdown -h now", shell=True)
        call("ps -ef | grep python", shell=True)
        
        global terminate
        global listening
        listening = False
        publishing = False
        client.disconnect()
        client.loop_stop()
        
        grovepi.analogWrite(sensorBlueLed.port,0)
        grovepi.analogWrite(sensorRedLed.port,0)
        #digitalWrite(sensorBuzzer.port,0) 
        digitalWrite(self.sensorBuzzer.port, 0)         

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

# Returns all readings as follows
# readings, temp, hum, sound, light
def readings():

        reading = ReadingsReceiver()
            
        sensor_sound = reading.my_sound_readings()
        sensor_light = reading.my_light_readings()
        temp_hum_level = reading.my_tem_hum_readings()

        readings = {
            'timestamp': datetime.now().isoformat(),
            'Sound Level': sensor_sound,
            'Light Level': sensor_light,
            'Temperature': temp_hum_level[0],
            'Humidity Levels': temp_hum_level[1]
        }
        return readings, temp_hum_level[0], temp_hum_level[1], sensor_sound, sensor_light

#The function below publishes the readings from my sensors to the MQTT Broker after reading them
#Method responsible for managing all business rules (constrains - structure or to control or influence the behavior of the business)
def publish():

    global buttonPressed
    
    CLIENT_ID_PUBLISHER = 'clientId-wr3GO0UfLF'
    client = start_client(CLIENT_ID_PUBLISHER)
    read = None
    temp = None
    hum = None
    sound = None
    light = None
    bpressed = None    
    
    #Loop to keep the below running while publishing = true
    while publishing:
            buzzerOn = False
            startTime = None
            endTime = None

            #Get all readings, and all readings separated aswell
            read, temp, hum, sound, light = readings()
            
            #Instancing the classes Lights() and Buzzer()            
            lightObj = Lights()
            buzzerObj = Buzzer()
            
            #if the temperature is too hot turns the red LED ON
            if temp >= 21.0:
                lightObj.setRedLedON()
                #Current time once temp reaches >= 21
                startTime = time.time()                
                         
            #if the temperature is too cold turns the blue LED ON
            elif temp <= 15.0:
                lightObj.setBlueLedON()
                #Current time once temp reaches <= 15
                startTime = time.time()
            #If temperature is ideal set LED Green ON
            else:
                lightObj.setGreenLedON()         

            #Calling methods buzzerBlock() and buttonPres() 
            buzzerObj.buzzerBlock()
            buzzerObj.buttonPress()            
            
            #While temp less than 16 or higher than 20
            while temp <= 15.0 or temp >= 21.0:

                #Get all readings, and all readings separated aswell
                read, temp, hum, sound, light = readings()
         
                #If the temperature is not ideal for >= 15min triggers the buzzer 
                # if seconds > 900:
                if time.time() - startTime > 900:

                    if buzzerOn == False:
                        buzzerObj.buzzerON()
                        buzzerOn = True
                    
                buzzerObj.buttonPress()
                seconds = time.time() - startTime
                
                print(seconds)

                #Button pressed leave this loop
                if buttonPressed:
                    buttonPressed = False
                    break                        

                client.publish(MY_TOPIC, json.dumps(read))
                print('Published readings: ', read)
                            
                #Sleep for 0.3 seconds to drag down the unnessesary iterations.
                client.loop(0.3)
                time.sleep(0.3)       
                
            client.publish(MY_TOPIC, json.dumps(read))
            
            print('Published readings: ', read)
            
            client.loop(.3)
            time.sleep(.3)  
        
    print('Stop publishing')

#4
#The function below listens to all the messages from my pre-defined topic
def listen(publisher):
    
    CLIENT_ID_LISTENER = 'clientId-TkWjA2GMp'	
    client = start_client(CLIENT_ID_LISTENER)
    MY_SUBSCRIBER = 'myIoT/listener'
    client.subscribe(MY_SUBSCRIBER)    
    print('We are subscribed to the topic!!!')
    
    while listening:
        client.loop(.3)

#3
#The function below starts my MQTT client and connects to the Broker then we loop through
def start_client(client_id):
	
	#Below we create an MQTT client and attach our routines to it
    client = mqtt.Client(client_id)
    client.connect(ADDRESS_BROKER)
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    
    return client

#2
#Method below manages threads' cycles - start and terminate
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
    
#1
if __name__ == '__main__':
    try:
        main()
        
    except KeyboardInterrupt:
        sys.exit(0)
        
