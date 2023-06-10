#!/bin/bash

# Check if port 1883 is open and not occupied
if ! lsof -i :1883 > /dev/null; then
  echo "[1883] - Running MQTT server"
  ./mqtt-server &
else
  echo "[1883] - occupied. Cannot start MQTT server"
fi

if ! lsof -i :8000 > /dev/null; then
  echo "[8000] - Running TinyOneM2M instance"
  cd TinyOneM2M
  ./server.o &
  sleep 1
  cd ..
else
  echo "[8000] - occupied. Cannot start TinyOneM2M instance."
fi

# Check the argument and run the corresponding Python script
if [ "$1" == "switch" ]; then
  # Run smart-switch.py
  python smart-switch.py
elif [ "$1" == "bulb" ]; then
  # Run smart-bulb.py
  python smart-bulb.py
else
  echo "Invalid argument. Please provide 'switch' or 'bulb'."
fi
