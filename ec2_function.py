#!/usr/bin/python3
# import boto3
import json
import random
import math
# import requests
import sys

# s3 = boto3.client('s3')

# def main():
request_body = sys.stdin.read()

input_json = json.loads(request_body)
# resp = requests.get('http://169.254.169.254/latest/meta-data/public-hostname')
# public_dns_name = resp.content.decode('utf-8')
# input_json = json.loads(requests.get('http://' + public_dns_name + '/ec2_function.py').content)
# obj = request.json
# input_json = json.loads(obj['Body'].read().decode('utf-8'))
# Extract the required parameters from the input data
minhistory = int(input_json['history'])
shots = int(input_json['shots'])
signaltype = str(input_json['signal_type'])
P = int(input_json['time_horizon'])
closing_prices = input_json['closing_prices']
buy_signals = input_json['buy_signals']
sell_signals = input_json['sell_signals']
# input_key = str(input_json['input_key'])
# output_key = str(input_json['output_key'])
# Read the input JSON data from the S3 bucket
# input_bucket = 'ec2-function-input'
# output_bucket = 'instance-results'
# input_key = event['key']
# obj = s3.get_object(Bucket=input_bucket, Key=input_key)

# create empty lists to store the results
risk95_values = []
risk99_values = []

for i in range(minhistory, len(closing_prices)):
    if (i+P) < len(closing_prices): # this ignores signals where we don't have price_p_days_forward
        if signaltype=="Buy" and buy_signals[i]==1: # for buy signals
            # calculate the mean and standard deviation of the price changes over the past minhistory days
            pct_changes = [closing_prices[j]/closing_prices[j-1] - 1 for j in range(i-minhistory, i)] # percent changes with previous closing price
            mean = sum(pct_changes)/len(pct_changes)
            std = math.sqrt(sum([(x-mean)**2 for x in pct_changes])/len(pct_changes))
            
            # generate much larger random number series with same broad characteristics
            simulated = [random.gauss(mean,std) for x in range(shots)]
            
            # sort and pick 95% and 99%  - not distinguishing long/short risks here
            simulated.sort(reverse=True)
            var95 = simulated[int(len(simulated)*0.95)]
            var99 = simulated[int(len(simulated)*0.99)]
            
            # record the risk values
            risk95_values.append(var95)
            risk99_values.append(var99)

        
        elif signaltype=="Sell" and sell_signals[i]==1:
            # calculate the mean and standard deviation of the price changes over the past minhistory days
            pct_changes = [closing_prices[j]/closing_prices[j-1] - 1 for j in range(i-minhistory, i)] # percent changes with previous closing price
            mean = sum(pct_changes)/len(pct_changes)
            std = math.sqrt(sum([(x-mean)**2 for x in pct_changes])/len(pct_changes))
            
            # generate much larger random number series with same broad characteristics
            simulated = [random.gauss(mean,std) for x in range(shots)]
            
            # sort and pick 95% and 99%  - not distinguishing long/short risks here
            simulated.sort(reverse=True)
            var95 = simulated[int(len(simulated)*0.95)]
            var99 = simulated[int(len(simulated)*0.99)]
            
            # record the risk values
            risk95_values.append(var95)
            risk99_values.append(var99)
            
# Create a dictionary to store the simulation results
simulation_results = {
    'risk95_values': risk95_values,
    'risk99_values': risk99_values
}

# Convert the dictionary to a JSON string
output_json = json.dumps(simulation_results)
print('Content-Type: application/json')
print()
print(output_json)
    # Return the JSON string as the response
    # return output_json

    # # Write the simulation results to a JSON file
    # with open('simulation_results.json', 'w') as f:
    #     json.dump(simulation_results, f)

    # # Upload the output to S3 bucket
    # s3.upload_file('simulation_results.json', bucket_name, output_key)
    # output_data_json = json.dumps(simulation_results)
    # s3.put_object(Bucket=output_bucket,Key=output_key, Body=output_data_json)

    # # Write the output to a new file in the S3 bucket
    # output_bucket = event['output_bucket']
    # output_key = key
    # output_data = {
    #     'risk95_values': risk95_values,
    #     'risk99_values': risk99_values
    # }
    # s3.put_object(Bucket=output_bucket, Key=output_key, Body=json.dumps(output_data))

    # # Return a success response
    # response = {
    #     'statusCode': 200,
    #     'body': json.dumps('Simulation completed successfully!')
    # }
    # return response
    # return (risk95_values, risk99_values)

# if __name__ == "__main__":
#     main()