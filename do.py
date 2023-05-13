import http.client
import json
import time

public_dns_names = ['ec2-52-87-184-36.compute-1.amazonaws.com', 'ec2-54-152-211-118.compute-1.amazonaws.com']
for public_dns_name in public_dns_names:
    connection = http.client.HTTPConnection(public_dns_name)



json_keys = {
    "history": "2",
    "shots": "100",
    "signal_type": "Buy",
    "time_horizon": "5",
    "closing_prices": "[1,11,12,13,14,69,420,666, 333, 3141, 161]",
    "buy_signals": "[0,1,0,0,1,1,1,0,0,1,1]",
    "sell_signals": "[1,0,1,1,0,0,0,1,1,0,0]"
    }

input_json = json.dumps(json_keys)

time.sleep(5)
# Send a POST request to the instance to run the simulation
connection.request("POST", "/", input_json)
response = connection.getresponse()
print(response)
ec2_out_data = response.read().decode('utf-8')
print(ec2_out_data)
ec2_out_data = json.loads(ec2_out_data)