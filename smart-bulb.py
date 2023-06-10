import utils.discovery as discovery
import utils.onem2m as onem2m
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import paho.mqtt.client as mqtt
import uuid
import json
from threading import Thread
import signal

app = Flask(__name__)
CORS(app, origins='*', methods=['GET', 'POST'], allow_headers='Content-Type')
socketio = SocketIO(app, cors_allowed_origins='*')

# Define Cleanup method
def cleanup():
    global local_ip
    request_body = {
        "m2m:cin": {
            "cnf": "text/plain:0",
            "con": "null",
            "rn": f"lightbulb_{local_ip}_{uuid.uuid4().hex[:8]}"
        }
    }
    onem2m.create_resource(LIGHTBULB_CNT, request_body)

signal.signal(signal.SIGINT, cleanup)

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
        "con": "off",
        "rn": f"lightbulb_{local_ip}_{uuid.uuid4().hex[:8]}"
    }
}
onem2m.create_resource(LIGHTBULB_CNT, request_body)


# ==================== CREATE SUB ====================

request_body = {
    "m2m:sub": {
        "nu": ["mqtt://" + local_ip + ":1883"],
        "rn": "self-sub"
    }
}
onem2m.create_resource(LIGHTBULB_CNT, request_body)


# ==================== DISCOVER SMART SWITCHES ====================

print("[NMAP]: Searching for smart switches...")

smart_device_ips = discovery.discover_ips_on_port(local_ip, 8000)
smart_switch_ips = [ smart_device_ip for smart_device_ip in smart_device_ips if onem2m.get_resource(f"http://{smart_device_ip}:8000/onem2m/switch") is not None ]

print("[NMAP]:", smart_switch_ips)


# ==================== NOTIFY PRESENCE TO ALL SMART SWITCHES VIA WEBSOCKETS ====================

@app.route('/')
def home():
    return render_template('bulb/index.html')

@app.route('/state')
def state():
    last_bulb_state = onem2m.get_resource(f"{LIGHTBULB_CNT}/la")
    return jsonify({"state": last_bulb_state["m2m:cin"]["con"]})

@socketio.on('connect')
def on_connect():
    print(f"[WebSocket]: Connection established")

# Create CIN to Add Bulb to Every Discovered Switch
for smart_switch_ip in smart_switch_ips:
    request_body = {
        "m2m:cin": {
            "cnf": "text/plain:0",
            "con": local_ip,
            "rn": local_ip
        }
    }
    onem2m.create_resource(f"http://{smart_switch_ip}:8000/onem2m/switch/lightbulbs", request_body)
    

client = mqtt.Client()

# Function to run MQTT client loop
def run_mqtt_client():
    topic = "/onem2m/lightbulb/state/self-sub"

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(topic)
            print(f"[MQTT]: Listening for changes...")

    def on_message(client, userdata, message):
        if message.topic != topic:
            return

        state = json.loads(message.payload.decode('utf-8'))
        if ("m2m:cin" in str(state["m2m:sgn"]["nev"]["rep"])):
            socketio.emit('state', state["m2m:sgn"]["nev"]["rep"]["m2m:cin"]["con"])
            print(f"[MQTT]: State {state}")   

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(local_ip)
    client.loop_start()

# Function to run SocketIO server
def run_socketio_server():
    socketio.run(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':

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