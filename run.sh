#!/bin/bash

# Check the argument and run the corresponding Python script
if [ "$1" == "switch" ]; then
  # Check if port 1883 is open and not occupied
  if ! sudo lsof -i :1883 > /dev/null; then
    ./mqtt-server &
  else
    echo "Port 1883 is either open or occupied. Cannot start the MQTT server for switch."
  fi

  # Run smart-switch.py
  python smart-switch.py
elif [ "$1" == "bulb" ]; then
  # Run smart-bulb.py
  python smart-bulb.py
else
  echo "Invalid argument. Please provide 'switch' or 'bulb'."
fi
