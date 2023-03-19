import paho.mqtt.client as mqtt
import random
import time
import json
# define the MQTT broker and topic
broker = "localhost"
def sensor_init(client):
    topic = "homeassistant/sensor/DemoT/config"
    message = '''{
        "device_class": "temperature",
        "name": "DemoTemperature",
        "state_topic": "homeassistant/sensor/DemoT/state",
        "unit_of_measurement": "°C",
        "value_template": "{{ value_json.temperature}}", 
        "uniq_id": "DemoT-temp"
    }'''
    client.publish(topic, message)
    # ----------------------------------------------
    topic = "homeassistant/sensor/DemoH/config"
    message = '''{
        "device_class": "humidity",
        "name": "DemoHumidity",
        "state_topic": "homeassistant/sensor/DemoH/state",
        "unit_of_measurement": "%",
        "value_template": "{{ value_json.humidity}}",
        "uniq_id": "DemoH-hum"
    }'''
    client.publish(topic, message)
    # ----------------------------------------------
    topic = "homeassistant/sensor/DemoG/config"
    message = '''{
        "device_class": "gas",
        "name": "DemoGas",
        "state_topic": "homeassistant/sensor/DemoG/state",
        "unit_of_measurement": "m³",
        "value_template": "{{ value_json.gas}}",
        "uniq_id": "DemoG-gas"
    }'''
    client.publish(topic, message)
    topic = "homeassistant/sensor/DemoN/config"
    message = '''{
        "name": "DemoNone",
        "state_topic": "homeassistant/sensor/DemoN/state",
        "unit_of_measurement": "ppm",
        "value_template": "{{ value_json.smoke}}",
        "uniq_id": "DemoN-smoke"
    }'''
    client.publish(topic, message)
    
    
def sensor_temperature(client):
    topic = "homeassistant/sensor/DemoT/state"
    message = {"temperature":+ round(random.random() * 100,2)}
    client.publish(topic, json.dumps(message))
    print("publishing message: " + str(message))
    time.sleep(0.5)
def sensor_humidity(client):
    topic = "homeassistant/sensor/DemoH/state"
    message = {"humidity":+ round(random.random() * 100,2)}
    client.publish(topic, json.dumps(message))
    print("publishing message: " + str(message))
    time.sleep(0.5)
def sensor_gas(client):
    topic = "homeassistant/sensor/DemoG/state"
    message = {"gas":round(random.random() * 100,2)}
    client.publish(topic, json.dumps(message))
    print("publishing message: " + str(message))
    time.sleep(0.5)
def sensor_None(client):
    topic = "homeassistant/sensor/DemoN/state"
    message = {'smoke':+round(random.random() * 100,2)}
    client.publish(topic, json.dumps(message))
    print("publishing message: " + str(message))
    time.sleep(0.5)


client = mqtt.Client()
client.connect(broker)
time.sleep(5)
sensor_init(client)

while 1:
    sensor_temperature(client)
    sensor_humidity(client)
    sensor_gas(client)
    sensor_None(client)
    time.sleep(10)




