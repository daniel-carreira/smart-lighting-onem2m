import utils.discovery as discovery
import utils.onem2m as onem2m
from flask import Flask, render_template, request, jsonify, abort
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import paho.mqtt.client as mqtt
from threading import Thread
import json
import time

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
        "mni": 50,
        "rn": "state"
    }
}
onem2m.create_resource(SWITCH_AE, request_body)

request_body = {
     "m2m:cnt": {
        "mni": 50,
        "rn": "lightbulbs"
    }
}
onem2m.create_resource(SWITCH_AE, request_body)

# ==================== 4. DISCOVER SMART LIGHTBULBS ====================

print("[NMAP]: Searching for smart lightbulbs...")

smart_device_ips = discovery.discover_ips_on_port(local_ip, 8000)
smart_lightbulb_ips = [ smart_device_ip for smart_device_ip in smart_device_ips if onem2m.get_resource(f"http://{smart_device_ip}:8000/onem2m/lightbulb") is not None ]

print("[NMAP]:", smart_lightbulb_ips)

# ==================== 5. CREATE CIN ====================

if len(smart_lightbulb_ips) > 0:
    request_body = {
        "m2m:cin": {
            "cnf": "text/plain:0",
            "con": smart_lightbulb_ips[0],
            "rn": f"target-lightbulb_{int(time.time()*1000)}"
        }
    }
    onem2m.create_resource(SWITCH_CNT, request_body)

    for smart_lightbulb_ip in smart_lightbulb_ips:
        request_body = {
            "m2m:cin": {
                "cnf": "text/plain:0",
                "con": smart_lightbulb_ip,
                "rn": smart_lightbulb_ip
            }
        }
        onem2m.create_resource(f"{SWITCH_AE}/lightbulbs", request_body)

# ==================== 6. SUBSCRIBE TO ALL SMART LIGHTBULBS ====================

local_ip_no_points = local_ip.replace('.', '')

def subscribe_lightbulb(ip):
    REQUEST_BODY = {
        "m2m:sub": {
            "nu": ["mqtt://" + local_ip + ":1883"],
            "rn": "sub-" + local_ip_no_points
        }
    }
    LIGHTBULB_CNT = f"http://{ip}:8000/onem2m/lightbulb/state"
    onem2m.create_resource(LIGHTBULB_CNT, REQUEST_BODY)

for smart_lightbulb_ip in smart_lightbulb_ips:
    subscribe_lightbulb(smart_lightbulb_ip)


# ==================== SELF SUBSCRIBE ====================

REQUEST_BODY = {
    "m2m:sub": {
        "nu": ["mqtt://" + local_ip + ":1883"],
        "rn": "sub"
    }
}
onem2m.create_resource(f"{SWITCH_AE}/lightbulbs", REQUEST_BODY)

REQUEST_BODY = {
    "m2m:sub": {
        "nu": ["mqtt://" + local_ip + ":1883"],
        "rn": "sub"
    }
}
onem2m.create_resource(f"{SWITCH_AE}/state", REQUEST_BODY)


# ==================== WEB SMART SWITCH CONTROL ====================

@app.route('/')
def home():
    return render_template('switch/index.html')

# Discovered bulbs
@app.route('/bulbs')
def bulbs():
    # Get target lightbulb
    switch_state = onem2m.get_resource(f"{SWITCH_CNT}/la")
    if (switch_state != {'m2m:dbg': 'no instance for <latest> or <oldest>'}):
        switch_state_ip = switch_state["m2m:cin"]["con"] if switch_state else None

        # Get all lightbulb IPs
        switch_lightbulbs_path = onem2m.get_resource(f"{SWITCH_AE}/lightbulbs?fu=1&ty=4")
        switch_lightbulbs = switch_lightbulbs_path["m2m:uril"]
        lightbulb_ips = [path.split('/')[-1] for path in switch_lightbulbs]

        # Respond with lightbulb states
        response = []
        for lightbulb_ip in lightbulb_ips:
            lightbulb_state = onem2m.get_resource(f"http://{lightbulb_ip}:8000/onem2m/lightbulb/state/la")
            is_current = lightbulb_ip == switch_state_ip

            lightbulb = {
                "ip": lightbulb_ip,
                "state": lightbulb_state["m2m:cin"]["con"],
                "current": is_current
            }
            response.append(lightbulb)

        return jsonify(response)
    else:
        return ""

# Toggle route
@app.route('/toggle', methods=['POST'])
def toggle():
    # Get target lightbulb
    switch_state = onem2m.get_resource(f"{SWITCH_CNT}/la")
    switch_state_ip = switch_state["m2m:cin"]["con"] if switch_state else None

    if switch_state_ip is None:
        abort(400)

    # Get target lightbulb state
    BULB_CNT = f"http://{switch_state_ip}:8000/onem2m/lightbulb/state"
    last_bulb_state = onem2m.get_resource(f"{BULB_CNT}/la")

    # Toggle State of Lightbulb
    last_bulb_state["m2m:cin"]["con"] = "on" if last_bulb_state["m2m:cin"]["con"] == "off" else "off"
    request_body = {
        "m2m:cin": {
            "cnf": "text/plain:0",
            "con": last_bulb_state["m2m:cin"]["con"],
            "rn": f"lightbulb_{switch_state_ip}_{int(time.time()*1000)}"
        }
    }
    state = onem2m.create_resource(BULB_CNT, request_body)
    if state is None:
        abort(400)

    socketio.emit("state", {"ip": switch_state_ip, "state": state["m2m:cin"]["con"]})
    return jsonify({"state": state["m2m:cin"]["con"]})

# Next route
@app.route('/next', methods=['POST'])
def next():
    # Get target lightbulb
    switch_state = onem2m.get_resource(f"{SWITCH_CNT}/la")
    switch_state_ip = switch_state["m2m:cin"]["con"] if switch_state else None

    if switch_state_ip is None:
        abort(400)

    # Get all lightbulb IPs
    switch_lightbulbs_path = onem2m.get_resource(f"{SWITCH_AE}/lightbulbs?fu=1&ty=4")
    switch_lightbulbs = switch_lightbulbs_path["m2m:uril"]
    lightbulb_ips = [path.split('/')[-1] for path in switch_lightbulbs]

    if len(lightbulb_ips) == 0:
        abort(400)

    index = -1
    try:
        index = lightbulb_ips.index(switch_state_ip)
    except ValueError:
        pass
    finally:
        index = (index + 1) % len(lightbulb_ips)

    next_bulb_ip = lightbulb_ips[index]
    
    # Change to the next Lightbulb
    request_body = {
        "m2m:cin": {
            "cnf": "text/plain:0",
            "con": next_bulb_ip,
            "rn": f"lightbulb_{next_bulb_ip}_{int(time.time()*1000)}"
        }
    }
    created = onem2m.create_resource(SWITCH_CNT, request_body)
    if created is None:
        abort(400)

    return jsonify({"state": created["m2m:cin"]["con"]})

# MQTT
client = mqtt.Client()

# Function to run MQTT client loop
def run_mqtt_client():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            sub_topic = f"/onem2m/lightbulb/state/sub-{local_ip_no_points}"
            client.subscribe(sub_topic)
            client.subscribe("/onem2m/switch/state/sub")
            client.subscribe("/onem2m/switch/lightbulbs/sub")
            print(f"[MQTT]: Listening for changes...")

    def on_message(client, userdata, message):
        msg = json.loads(message.payload.decode('utf-8').replace('\x00', ''))

        # Topic: /onem2m/lightbulb/state/sub
        if message.topic == "/onem2m/lightbulb/state/sub":
            # On POST event
            if msg["m2m:sgn"]["nev"]["net"] != "POST" or "m2m:cin" not in msg["m2m:sgn"]["nev"]["rep"]:
                return
            
            bulb_cin = msg["m2m:sgn"]["nev"]["rep"]["m2m:cin"]

            state = bulb_cin["con"]
            ip = bulb_cin["rn"].split("_")[1]

            if state == "null":
                onem2m.delete_resource(f"{SWITCH_AE}/lightbulbs/{ip}")

            else:
                body = {
                    "ip": ip,
                    "state": state
                }
                socketio.emit("state", body)

            print(f"[MQTT]: Lightbulb changed state")

        # Topic: /onem2m/switch/state/sub
        if message.topic == "/onem2m/switch/state/sub":
            # On POST event
            if msg["m2m:sgn"]["nev"]["net"] != "POST" or "m2m:cin" not in msg["m2m:sgn"]["nev"]["rep"]:
                return

            switch_cin = msg["m2m:sgn"]["nev"]["rep"]["m2m:cin"]

            ip = switch_cin["con"]
            body = {
                "ip": ip
            }

            socketio.emit("target", body)
            print(f"[MQTT]: Switch changed state (target)")

        # Topic: /onem2m/switch/lightbulbs/sub
        if message.topic == "/onem2m/switch/lightbulbs/sub":
            switch_cin = msg["m2m:sgn"]["nev"]["rep"]["m2m:cin"]
            ip = switch_cin["con"]

            body = {
                "ip": ip,
                "state": ""
            }

            mqtt_url = "mqtt://" + local_ip + ":1883"
            # On POST event
            if msg["m2m:sgn"]["nev"]["net"] == "POST":
                REQUEST_BODY = {
                    "m2m:sub": {
                        "nu": [mqtt_url],
                        "rn": "sub-" + local_ip_no_points
                    }
                }
                onem2m.create_resource(f"http://{ip}:8000/onem2m/lightbulb/state", REQUEST_BODY)

                switch_state = onem2m.get_resource(f"{SWITCH_CNT}/la")
                if "no instance" in str(switch_state):
                    request_body = {
                        "m2m:cin": {
                            "cnf": "text/plain:0",
                            "con": ip,
                            "rn": f"lightbulb_{ip}_{int(time.time()*1000)}"
                        }
                    }
                    onem2m.create_resource(SWITCH_CNT, request_body)

                lightbulb_state = onem2m.get_resource(f"http://{ip}:8000/onem2m/lightbulb/state/la")
                body["state"] = lightbulb_state["m2m:cin"]["con"]
                socketio.emit("add", body)

            # On DELETE event
            if msg["m2m:sgn"]["nev"]["net"] == "DELETE":
                socketio.emit("remove", body)

            print(f"[MQTT]: Switch changed state (add)")

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