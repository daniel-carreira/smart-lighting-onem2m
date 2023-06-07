import utils.discovery as discovery
import utils.onem2m as onem2m
import paho.mqtt.client as mqtt

# ------- Procedure List -------
# 1. Find Local IP
# 2. Create AE (delete if exists)
# 3. Create CNT
# 4. Create CIN
# 5. Discover Smart Switches
# 6. Notify presence to All Smart Switches via WebSockets


# ==================== FIND LOCAL IP ====================

local_ip = discovery.get_local_ip()

# ==================== CREATE AE ====================

# Constants
CSE_BASE = f"http://{local_ip}:8000/onem2m"
LIGHTBULB_AE = f"{CSE_BASE}/lightbulb"
LIGHTBULB_CNT = f"{LIGHTBULB_AE}/state"

# Delete AE if exists
onem2m.delete_resource(LIGHTBULB_AE)

# Create AE
request_body = {
    "m2m:ae": {
        "api": "lightbulb",
        "rn": "lightbulb",
        "rr": "true"
    }
}
onem2m.create_resource(CSE_BASE, request_body)


# ==================== CREATE CNT ====================

request_body = {
     "m2m:cnt": {
        "mbs": 10000,
        "mni": 50,
        "rn": "state"
    }
}
onem2m.create_resource(LIGHTBULB_AE, request_body)


# ==================== CREATE CIN ====================

request_body = {
    "m2m:cin": {
        "cnf": "text/plain:0",
        "con": "{\"state\": \"off\"}"
    }
}
onem2m.create_resource(LIGHTBULB_CNT, request_body)


# ==================== DISCOVER SMART SWITCHES ====================

print("[NMAP]: Searching for smart switches...")

smart_device_ips = discovery.discover_ips_on_port(local_ip, 8000)
smart_switch_ips = [ smart_device_ip for smart_device_ip in smart_device_ips if onem2m.get_resource(f"http://{smart_device_ip}:8000/onem2m/smartswitch") is not None ]

print("[NMAP]:", smart_switch_ips)


# ==================== NOTIFY PRESENCE TO ALL SMART SWITCHES VIA WEBSOCKETS ====================

client = mqtt.Client()

topic = "discovery"
num_published = 0
total_publishes = len(smart_switch_ips)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        # Publish a message after successful connection
        client.publish(topic, local_ip)
    else:
        print(f"[MQTT]: Device '{client._host}' doesn't have MQTT Broker running on port 1883")

def on_publish(client, userdata, mid):
    global num_published
    num_published += 1

    if num_published == total_publishes:
        print("[MQTT]: All smart switches were notified")
        client.disconnect()

client.on_connect = on_connect
client.on_publish = on_publish

for smart_switch_ip in smart_switch_ips:
    client.connect(smart_switch_ip)

client.loop_forever()