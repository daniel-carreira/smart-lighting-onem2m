import requests
import json

def get_resource(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ONEM2M]: Could't find the resource '{url}'")
            return None
    except:
        print(f"[ONEM2M]: Could't find the resource '{url}'")
        return None
    
def delete_resource(url):
    try:
        response = requests.delete(url)
        if response.status_code == 200 or response.status_code == 204:
            print(f"[ONEM2M]: Resource '{url}' deleted successfully")
        else:
            print(f"[ONEM2M]: Could't delete the resource '{url}'")
    except:
        print(f"[ONEM2M]: Could't delete the resource '{url}'")

def create_resource(url, data):
    try:
        headers = { "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200 or response.status_code == 201:
            print(f"[ONEM2M]: Resource '{url}' created successfully")
            return json.loads(response.text)
        else:
            print(f"[ONEM2M]: Could't create the resource '{url}'")
            return None
    except:
        print(f"[ONEM2M]: Could't create the resource '{url}'")
        return None