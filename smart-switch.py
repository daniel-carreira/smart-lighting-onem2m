import utils.discovery as discovery
import utils.onem2m as onem2m
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import paho.mqtt.client as mqtt
from threading import Thread
import json
import uuid

app = Flask(__name__)
CORS(app, origins='*', methods=['GET', 'POST'], allow_headers='Content-Type')
socketio = SocketIO(app, cors_allowed_origins='*')

# ------- Procedure List -------
# 1. Find Local IP
# 2. Create AE (delete if exists)
# 3. Create CNT
# 4. Discover Smart Lightbulbs
# 5. Create CIN
# 6. Subscribe to all Smart Lightbulbs
# 7. Smart Lightbulb listener
# 8. Smart Switch controls


# ==================== 1. FIND LOCAL IP ====================

local_ip = discovery.get_local_ip()


# ==================== 2. CREATE AE ====================

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


# ==================== 3. CREATE CNT ====================

request_body = {
     "m2m:cnt": {
        "mni": 1,
        "rn": "state"
    }
}
onem2m.create_resource(SWITCH_AE, request_body)


# ==================== 4. DISCOVER SMART LIGHTBULBS ====================

print("[NMAP]: Searching for smart lightbulbs...")

smart_device_ips = discovery.discover_ips_on_port(local_ip, 8000)
smart_lightbulb_ips = [ smart_device_ip for smart_device_ip in smart_device_ips if onem2m.get_resource(f"http://{smart_device_ip}:8000/onem2m/lightbulb") is not None ]

print("[NMAP]:", smart_lightbulb_ips)

# ==================== 5. CREATE CIN ====================
request_body = {
    "m2m:cin": {
        "cnf": "text/plain:0",
        "con": "X.X.X.X",
        "rn": f"switch_{local_ip}_{uuid.uuid4().hex[:8]}"
    }
}

if not smart_device_ips:
    request_body["m2m:cin"]["con"] = smart_lightbulb_ips[0]
onem2m.create_resource(SWITCH_CNT, request_body)

# ==================== 6. SUBSCRIBE TO ALL SMART LIGHTBULBS ====================

def subscribe_lightbulb(ip):
    REQUEST_BODY = {
        "m2m:sub": {
            "nu": f"[\"mqtt://{local_ip}:1883\"]",
            "rn": "sub"
        }
    }
    LIGHTBULB_CNT = f"http://{ip}:8000/onem2m/lightbulb/state"
    onem2m.create_resource(LIGHTBULB_CNT, REQUEST_BODY)

for smart_lightbulb_ip in smart_lightbulb_ips:
    subscribe_lightbulb(smart_lightbulb_ip)


smart_lightbulbs = []

def find_bulb(param, value):
    for index, obj in enumerate(smart_lightbulbs):
        if obj[param] == value:
            return index
    return -1

def add_bulb(ip, socket):
    for obj in smart_lightbulbs:
        if obj["ip"] == ip:
           return False
    
    smart_lightbulbs.append({
        "ip": ip,
        "socket": socket
    })
    return True
    
def remove_bulb(index):
    del smart_lightbulbs[index]


# ==================== WEB SMART SWITCH CONTROL ====================

@app.route('/')
def home():
    return render_template('switch/index.html')

# Discovered bulbs
@app.route('/bulbs')
def bulbs():
    switch_state = onem2m.get_resource(f"{SWITCH_CNT}/la")
    switch_state_ip = switch_state["m2m:cin"]["con"]

    response = []
    for smart_lightbulb_ip in smart_lightbulb_ips:
        is_current = switch_state_ip == smart_lightbulb_ip
        data = onem2m.get_resource(f"http://{smart_lightbulb_ip}:8000/onem2m/lightbulb/state/la")
        obj = {
            "ip": smart_lightbulb_ip,
            "state": data["m2m:cin"]["con"],
            "current": is_current
        }
        response.append(obj)
    
    return jsonify(response)

# Toggle route
@app.route('/toggle', methods=['POST'])
def toggle():
    # Get Last State of Lightbulb
    bulb_ip = request.json.get('state')
    BULB_CNT = f"http://{bulb_ip}:8000/onem2m/lightbulb/state"
    last_bulb_state = onem2m.get_resource(f"{BULB_CNT}/la")

    request_body = {
        "m2m:cin": {
            "cnf": "text/plain:0",
            "con": "X.X.X.X",
            "rn": f"switch_{local_ip}_{uuid.uuid4().hex[:8]}"
        }
    }

    # Toggle State of Lightbulb
    last_bulb_state["m2m:cin"]["con"] = "on" if last_bulb_state["m2m:cin"]["con"] == "off" else "off"
    request_body["m2m:cin"]["con"] = last_bulb_state["m2m:cin"]["con"]
    request_body["m2m:cin"]["rn"] = f"lightbulb_{bulb_ip}_{uuid.uuid4().hex[:8]}"
    state = onem2m.create_resource(BULB_CNT, request_body)
    print(state)
    if (state is None):
        return ""
    else:
        return jsonify({"state": state["m2m:cin"]["con"]})

# Next route
@app.route('/next', methods=['POST'])
def next():
    # Find IP in List
    bulb_ip = request.json.get('state')
    print(smart_lightbulb_ips)
    smart_lightbulb_ips_array = list(smart_lightbulb_ips)
    index = smart_lightbulb_ips_array.index(bulb_ip)

    # Find next IP
    next = index + 1
    next = 0 if next == len(smart_lightbulb_ips) else next
    next_bulb_ip = smart_lightbulb_ips_array[next]
    print("-----------------------")
    print(next_bulb_ip)

    # Change to the next Lightbulb
    switch_state = {
        "m2m:cin": {
            "cnf": "text/plain:0",
            "con": next_bulb_ip
        }
    }

    switch_state["m2m:cin"]["rn"] = f"switch_{local_ip}_{uuid.uuid4().hex[:8]}"
    created = onem2m.create_resource(SWITCH_CNT, switch_state)
    return jsonify({"state": created["m2m:cin"]["con"]})

# MQTT
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe("discover")
        print(f"[MQTT]: Listening for changes...")

def on_message(client, userdata, message):
    msg = message.payload.decode('utf-8')

    print("olaaafwefewfewfewf")
    # Topic: discover
    if message.topic == "discover":
        add_bulb(ip, client)
        socketio.emit("discover", msg)
        print(f"[MQTT]: Lightbulb discovered")
        return

    # Topic: /onem2m/lightbulb/state/sub
    if message.topic == "/onem2m/lightbulb/state/sub":
        cin = json.loads(msg)
        cin_obj = cin["m2m:sgn"]["nev"]["rep"]["m2m:cin"]

        state = cin_obj["con"]
        ip = cin_obj["rn"].split("_")[0]

        body = {
            "ip": ip,
            "state": state
        }

        socketio.emit("state", body)
        print(f"[MQTT]: Lightbulb changed state")

client.on_connect = on_connect
client.on_message = on_message

# Function to run MQTT client loop
def run_mqtt_client():
    client.connect(local_ip)
    client.loop_start()

# Function to run SocketIO server
def run_socketio_server():
    socketio.run(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':

    smart_lightbulb_ips = set(smart_lightbulb_ips)

    # Create separate threads for MQTT client and SocketIO server
    mqtt_thread = Thread(target=run_mqtt_client)
    socketio_thread = Thread(target=run_socketio_server)

    # Start the threads
    mqtt_thread.start()
    socketio_thread.start()

    # Wait for both threads to complete
    mqtt_thread.join()
    socketio_thread.join()

    # Stop MQTT client loop
    client.loop_stop()


"""
# ==================== CLI SMART SWITCH CONTROLS ====================
try:
    while True:
        while len(smart_lightbulb_ips) == 0:
            pass
        
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
"""