import subprocess
import json

def get_resource(url):
    try:
        command = ['curl', '-X', 'GET', url]
        output = subprocess.check_output(command)
        response = json.loads(output)
        if response.get('status_code') is not None:
            return None
        print(f"[ONEM2M]: Found resource '{url}'")
        return response
    except subprocess.CalledProcessError:
        print(f"[ONEM2M]: Internal error")
        return None
    except json.JSONDecodeError:
        print(f"[ONEM2M]: Invalid JSON response from '{url}'")
        return None

def delete_resource(url):
    try:
        command = ['curl', '-X', 'DELETE', url]
        output = subprocess.check_output(command)
        response = json.loads(output)
        if response.get('status_code') not in [200, 201]:
            print(f"[ONEM2M]: Couldn't delete the resource '{url}'")
        print(f"[ONEM2M]: Resource '{url}' deleted successfully")
    except subprocess.CalledProcessError:
        print(f"[ONEM2M]: Couldn't delete the resource '{url}'")
    except json.JSONDecodeError:
        print(f"[ONEM2M]: Invalid JSON response from '{url}'")
        return None

def create_resource(url, data):
    try:
        headers = "-H 'Content-Type: application/json'"
        command = ['curl', '-X', 'POST', url, headers, '-d', json.dumps(data)]
        output = subprocess.check_output(command)
        response = json.loads(output)
        if response.get('status_code') is not None:
            print(f"[ONEM2M]: Couldn't create the resource '{url}'")
            return None

        print(f"[ONEM2M]: Resource '{url}' created successfully")
        return response

    except subprocess.CalledProcessError:
        print(f"[ONEM2M]: Couldn't create the resource '{url}'")
        return None
    except json.JSONDecodeError:
        print(f"[ONEM2M]: Invalid JSON response from '{url}'")
        return None
