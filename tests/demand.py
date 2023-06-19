import requests
import json
import time
import matplotlib.pyplot as plt
import csv

def create_resource(url, data):
    try:
        headers = { "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200 or response.status_code == 201:
            return response.json()
        else:
            print(f"[ONEM2M]: Could't create the resource '{url}'")
            return None
    except:
        print(f"[ONEM2M]: Could't create the resource '{url}'")
        return None
    

request_body = {
    "m2m:ae": {
        "api": "lightbulb",
        "rn": "lightbulb",
        "rr": "true"
    }
}
res = create_resource(f"http://localhost:8000/onem2m", request_body)

request_body = {
     "m2m:cnt": {
        "rn": "state"
    }
}
res = create_resource(f"http://localhost:8000/onem2m/lightbulb", request_body)

batch_size = 100
average_times = []
total_time = 0

failed_num = 0
    
for i in range(10000):
    start_time = time.time()

    # Make POST request
    request_body = {
        "m2m:cin": {
            "cnf": "text/plain:0",
            "con": "off"
        }
    }
    res = create_resource(f"http://localhost:8000/onem2m/lightbulb/state", request_body)
    succeded = res is not None

    failed_num = failed_num + (1 if not succeded else 0)

    end_time = time.time()
    elapsed_time = end_time - start_time

    total_time = total_time + elapsed_time

    if (i + 1) % batch_size == 0:
        avg_time = total_time / batch_size
        average_times.append(avg_time)
        total_time = 0
        print(f"[Progress]: {i / 100}%")

print("Success: ", 10000 - failed_num)
print("Failed: ", failed_num)

print("Success Rate: ", ((10000 - failed_num) / 10000) )

x = [i * 100 for i in range(len(average_times))]
data = [[i * 100, time] for i, time in enumerate(average_times, start=1)]

plt.plot(x, average_times)
plt.xlabel("Number of CIN Objects")
plt.ylabel("Average Time (ms)")

plt.savefig("average_times_graph.png")

# Write the data to the CSV file
with open("output.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Number of Requests", "Average Time (ms)"])  # Write header row
    writer.writerows(data)  # Write data rows