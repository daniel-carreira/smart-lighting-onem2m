import utils.discovery as discovery
import utils.onem2m as onem2m
import paho.mqtt.client as mqtt

# ------- Procedure List -------
# 1. Find Local IP
# 2. Create AE (delete if exists)
# 3. Create CNT
# 4. Create CIN
# 5. Discover Smart Lightbulbs
# 6. Subscribe to all Smart Lightbulbs
# 7. Smart Lightbulb listener
# 8. Smart Switch controls


# ==================== FIND LOCAL IP ====================

local_ip = discovery.get_local_ip()


# ==================== CREATE AE ====================

# Constants
CSE_BASE = f"http://{local_ip}:8000/onem2m"
SWITCH_AE = f"{CSE_BASE}/switch"
SWITCH_CNT = f"{SWITCH_AE}/state"

# Delete AE if exists
onem2m.delete_resource(SWITCH_AE)

# Create AE
request_body = {
    "m2m:ae": {
        "api": "N.switch",
        "rn": "switch",
        "rr": "true"
    }
}
onem2m.create_resource(CSE_BASE, request_body)


# ==================== CREATE CNT ====================

request_body = {
     "m2m:cnt": {
        "mni": 1,
        "rn": "state"
    }
}
onem2m.create_resource(SWITCH_AE, request_body)


# ==================== CREATE CIN ====================

request_body = {
    "m2m:cin": {
        "cnf": "text/plain:0",
        "con": "{\"controlledLight\": \"10.79.12.150\"}"
    }
}
onem2m.create_resource(SWITCH_CNT, request_body)


# ==================== DISCOVER SMART LIGHTBULBS ====================

print("[NMAP]: Searching for smart lightbulbs...")

smart_device_ips = discovery.discover_ips_on_port(local_ip, 8000)
smart_lightbulb_ips = [ smart_device_ip for smart_device_ip in smart_device_ips if onem2m.get_resource(f"http://{smart_device_ip}:8000/onem2m/lightbulb") is not None ]

print("[NMAP]:", smart_lightbulb_ips)


# ==================== SUBSCRIBE TO ALL SMART LIGHTBULBS ====================

def subscribe_lightbulb(ip):
    REQUEST_BODY = {
        "m2m:sub": {
            "nu": f"[\"mqtt://{local_ip}:1883\"]",
            "rn": "switch"
        }
    }
    LIGHTBULB_CNT = f"http://{ip}:8000/onem2m/lightbulb/state"
    onem2m.create_resource(LIGHTBULB_CNT, REQUEST_BODY)

for smart_lightbulb_ip in smart_lightbulb_ips:
    subscribe_lightbulb(smart_lightbulb_ip)


# ==================== SMART LIGHTBULB LISTENER ====================

client = mqtt.Client()

topic = "discovery"
smart_lightbulb_ips = set(smart_lightbulb_ips)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        # Publish a message after successful connection
        client.subscribe(topic)
    else:
        print(f"[MQTT]: Listening for new smart lightbulbs...")

def on_message(client, userdata, message):
    if topic != message.topic:
        return
    
    global smart_lightbulb_ips
    ip = message.payload.decode('utf-8')
    smart_lightbulb_ips.add(ip)

    print(f"[MQTT]: {ip} found")

client.on_connect = on_connect
client.on_message = on_message

client.connect(local_ip)

client.loop_start()


# ==================== SMART SWITCH CONTROLS ====================

try:
    while True:
        if len(smart_lightbulb_ips) == 0:
            exit()
        
        last_switch_state = onem2m.get_resource(f"{SWITCH_CNT}/la")
        bulb_ip = last_switch_state["m2m:cin"]["con"]["controlledLight"]

        # Menu
        print(f"Smart Switch controlling Smart Lightbulb {bulb_ip}:")
        print("[1] - Toggle State")
        print("[2] - Next")
        print("[Ctrl + C] - Quit")

        value = input("Option: ")
        if value == 1:
            # Get Last State of Lightbulb
            BULB_CNT = f"http://{bulb_ip}:8000/onem2m/lightbulb/state"
            last_bulb_state = onem2m.get_resource(f"{BULB_CNT}/la")
            
            # Toggle State of Lightbulb
            last_bulb_state["m2m:cin"]["con"]["state"] = "on" if last_bulb_state["m2m:cin"]["con"]["state"] == "off" else "off"
            onem2m.create_resource(BULB_CNT, last_bulb_state)

        if value == 2:
            # Find IP in List
            index = smart_lightbulb_ips.find(bulb_ip)

            # Find next IP
            next = index + 1
            next = 0 if next == len(smart_lightbulb_ips) else next
            next_bulb_ip = smart_lightbulb_ips[next]

            # Change to the next Lightbulb
            last_switch_state["m2m:cin"]["con"]["controlledLight"] = next_bulb_ip
            onem2m.create_resource(SWITCH_CNT, last_switch_state)

except KeyboardInterrupt:
    pass

client.loop_stop()