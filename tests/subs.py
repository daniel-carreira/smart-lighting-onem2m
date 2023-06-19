import requests
import json
import time
import matplotlib.pyplot as plt
import csv
import paho.mqtt.client as mqtt

deliveries = 0

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe("#")

def on_message(client, userdata, message):
    global deliveries
    deliveries = deliveries + 1

# Set the on_message callback
client.on_message = on_message

# Connect to the MQTT broker
client.on_connect = on_connect
client.connect("localhost", 1883, 60)

# Start the MQTT loop to listen for messages
client.loop_start()

def create_resource(url, data):
    try:
        headers = { "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200 or response.status_code == 201:
            return response.json()
        else:
            print(f"[ONEM2M]: Could't create the resource '{url}'")
            return None
    except:
        print(f"[ONEM2M]: Could't create the resource '{url}'")
        return None
    

request_body = {
    "m2m:ae": {
        "api": "lightbulb",
        "rn": "lightbulb",
        "rr": "true"
    }
}
create_resource(f"http://localhost:8000/onem2m", request_body)

request_body = {
     "m2m:cnt": {
        "rn": "state"
    }
}
create_resource(f"http://localhost:8000/onem2m/lightbulb", request_body)

num_subs = 50
for i in range(num_subs):
    REQUEST_BODY = {
        "m2m:sub": {
            "nu": f"[\"mqtt://localhost:1883\"]"
        }
    }
    create_resource(f"http://localhost:8000/onem2m/lightbulb/state", request_body)

batch_size = 100
average_times = []
total_time = 0

expected_deliveries = num_subs * 1000
failed_num = 0
    
for i in range(1000):
    start_time = time.time()

    # Make POST request
    request_body = {
        "m2m:cin": {
            "cnf": "text/plain:0",
            "con": "off"
        }
    }
    res = create_resource(f"http://localhost:8000/onem2m/lightbulb/state", request_body)
    succeded = res is not None

    failed_num = failed_num + (1 if not succeded else 0)

    end_time = time.time()
    elapsed_time = end_time - start_time

    total_time = total_time + elapsed_time

    if (i + 1) % batch_size == 0:
        avg_time = total_time / batch_size
        average_times.append(avg_time)
        total_time = 0

time.sleep(10)
client.loop_stop()

print("Expected: ", expected_deliveries)
print("Delivered: ", deliveries)