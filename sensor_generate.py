""""this file is used to generate the sensor data for the homeassistant"""
import paho.mqtt.client as mqtt
import random
import time
import json
# define the MQTT broker and topic
broker = "192.168.137.1"
def sensor_init(client):
    topic = "homeassistant/sensor/DemoTemperature/config"
    message = '''{
        "device_class": "temperature",
        "name": "DemoTemperature",
        "state_topic": "homeassistant/sensor/DemoTemperature/state",
        "unit_of_measurement": "°C",
        "value_template": "{{ value_json.temperature}}", 
        "uniq_id": "DemoTemperature-temp"
    }'''
    client.publish(topic, message)
    # ----------------------------------------------
    topic = "homeassistant/sensor/DemoHumidity/config"
    message = '''{
        "device_class": "humidity",
        "name": "DemoHumidity",
        "state_topic": "homeassistant/sensor/DemoHumidity/state",
        "unit_of_measurement": "%",
        "value_template": "{{ value_json.humidity}}",
        "uniq_id": "DemoHumidity-hum"
    }'''
    client.publish(topic, message)
    # ----------------------------------------------
    topic = "homeassistant/sensor/DemoGas/config"
    message = '''{
        "device_class": "gas",
        "name": "DemoGas",
        "state_topic": "homeassistant/sensor/DemoGas/state",
        "unit_of_measurement": "m³",
        "value_template": "{{ value_json.gas}}",
        "uniq_id": "DemoGas-gas"
    }'''
    client.publish(topic, message)
    # ---------------------------------------------
    topic = "homeassistant/sensor/DemoNone/config"
    '''sensor with no device_class'''
    message = '''{
        "name": "DemoNone",
        "state_topic": "homeassistant/sensor/DemoNone/state",
        "unit_of_measurement": "ppm",
        "value_template": "{{ value_json.smoke}}",
        "uniq_id": "DemoNone-smoke"
    }'''
    client.publish(topic, message)
    # ---------------------------------------------
    topic = "homeassistant/sensor/DemoLight/config"
    message = '''{
        "device_class": "illuminance",
        "name": "DemoLight",
        "state_topic": "homeassistant/sensor/DemoLight/state",
        "unit_of_measurement": "lx",
        "value_template": "{{ value_json.light}}",
        "uniq_id": "DemoLight-illuminance"
    }'''
    client.publish(topic, message)
    
    
def sensor_temperature(client):
    topic = "homeassistant/sensor/DemoTemperature/state"
    message = {"temperature":+ round(random.random() * 100,2)}
    client.publish(topic, json.dumps(message))
    print("publishing message: " + str(message))
    time.sleep(0.5)
def sensor_humidity(client):
    topic = "homeassistant/sensor/DemoHumidity/state"
    message = {"humidity":+ round(random.random() * 100,2)}
    client.publish(topic, json.dumps(message))
    print("publishing message: " + str(message))
    time.sleep(0.5)
def sensor_gas(client):
    topic = "homeassistant/sensor/DemoGas/state"
    message = {"gas":round(random.random() * 100,2)}
    client.publish(topic, json.dumps(message))
    print("publishing message: " + str(message))
    time.sleep(0.5)
def sensor_None(client):
    topic = "homeassistant/sensor/DemoNone/state"
    message = {'smoke':+round(random.random() * 100,2)}
    client.publish(topic, json.dumps(message))
    print("publishing message: " + str(message))
    time.sleep(0.5)
def sensor_illu(client):
    topic = "homeassistant/sensor/DemoLight/state"
    message = {'light':+round(random.random() * 100,2)}
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
    sensor_humidity(client)
    sensor_illu(client)

    time.sleep(10)



