import utils.discovery as discovery
import utils.onem2m as onem2m
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import websocket

app = Flask(__name__)
CORS(app, origins='*', methods=['GET', 'POST'], allow_headers='Content-Type')

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
smart_switch_ips = [ smart_device_ip for smart_device_ip in smart_device_ips if onem2m.get_resource(f"http://{smart_device_ip}:8000/onem2m/switch") is not None ]

print("[NMAP]:", smart_switch_ips)


# ==================== NOTIFY PRESENCE TO ALL SMART SWITCHES VIA WEBSOCKETS ====================

@app.route('/')
def home():
    return render_template('bulb/index.html')

@app.route('/state')
def state():
    last_bulb_state = onem2m.get_resource(f"{LIGHTBULB_CNT}/la")
    return jsonify(last_bulb_state)

if __name__ == '__main__':
    for smart_switch_ip in smart_switch_ips:
        ws = websocket.WebSocketApp(f"ws://{smart_switch_ip}:8081")
        def on_open(ws):
            print(f"[WebSocket]: {smart_switch_ip} - Connection established")
            ws.send(smart_switch_ip)
            print(f"[WebSocket]: {smart_switch_ip} - Message sent \"{smart_switch_ip}\"")

        # Set the callback function
        ws.on_open = on_open

        # Start the WebSocket connection
        ws.run_forever()

    app.run(host='0.0.0.0', port=8080)