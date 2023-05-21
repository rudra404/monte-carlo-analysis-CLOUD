'''
# Script for testing responses i/o from EC2 instances

import requests
import json

json_keys = {
    'history': '2',
    'shots': '200',
    'signal_type': 'Buy',
    'time_horizon': '1',
    'closing_prices': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    'buy_signals': [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],
    'sell_signals': [0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0]
}

url = "http://{ec2_public_ip}/riskvalues"

url = 'http://' + 'ec2-18-205-191-113.compute-1.amazonaws.com' + '/ec2_function.py'
headers = {"Content-Type": "application/json"}
response = requests.post(url, headers=headers, data=json.dumps(json_keys))
print(response.text)

response_data = json.loads(response.text)

risk95_values = response_data['risk95_values']
risk99_values = response_data['risk99_values']

print(risk95_values)
print(risk99_values)

#################################

# Script for creating an object in S3 bucket - empty list for audit log

import json
import os

os.environ['AWS_SHARED_CREDENTIALS_FILE']='./cred' 

import boto3
s3 = boto3.client('s3')
# Create an empty list with table headers
table_headers = ['Time', 'Service (S)', 'Resources (R)', 'Price Hsitory (H)', 'Data Points (D)', 'Signal Type (T)', 'Profitability Horizon (P)', 'Avg 95 Risk', 'Avg 99 Risk', 'Total PnL ($)', 'Runtime (sec)', 'Cost ($)']
data_list = [table_headers]

# Convert list to JSON format
json_data = json.dumps(data_list)

# Specify file name and bucket name
object_key = 'audit.json'
bucket_name = 'audit-page-bucket'

# Upload the JSON data to bucket using the `put_object` method
s3.put_object(Body=json_data, Bucket=bucket_name, Key=object_key)

print('Empty list with table headers created and stored in S3.') # Confirmation

#################################

## Effort in ec2_function.py to read input by fetching the dns name and send results as json file ##

# resp = requests.get('http://169.254.169.254/latest/meta-data/public-hostname')
# public_dns_name = resp.content.decode('utf-8')
# input_json = json.loads(requests.get('http://' + public_dns_name + '/ec2_function.py').content)
# obj = request.json
# input_json = json.loads(obj['Body'].read().decode('utf-8'))

    # return the JSON string as the response
    # return output_json

    # write the simulation results to a JSON file
    # with open('simulation_results.json', 'w') as f:
    #     json.dump(simulation_results, f)

## Effort in ec2_function.py to read input and send results using s3 buckets ##

# input_key = str(input_json['input_key'])
# output_key = str(input_json['output_key'])
# Read input JSON data from the S3 bucket
# input_bucket = 'ec2-function-input'
# output_bucket = 'instance-results'
# input_key = event['key']
# obj = s3.get_object(Bucket=input_bucket, Key=input_key)

    # upload output to S3 bucket
    # s3.upload_file('simulation_results.json', bucket_name, output_key)
    # output_data_json = json.dumps(simulation_results)
    # s3.put_object(Bucket=output_bucket,Key=output_key, Body=output_data_json)

    # write the output to a new file in the S3 bucket
    # output_bucket = event['output_bucket']
    # output_key = key
    # output_data = {
    #     'risk95_values': risk95_values,
    #     'risk99_values': risk99_values
    # }
    # s3.put_object(Bucket=output_bucket, Key=output_key, Body=json.dumps(output_data))

## Effort in useec2() using various methods to try and connect before eventually succeeding using apache requests##

    # input_key = public_dns_name+h+d+t+p+'inputparameters'+'.json'
    # output_key = public_dns_name+h+d+t+p+'simulationresults'+'.json'

        # "input_key": input_key,
        # "output_key": output_key

    # Using s3 buckets to transfer information
    s3 = boto3.client('s3')
    input_json = json.dumps(json_keys)
    s3.put_object(Bucket='ec2-function-input',Key=input_key, Body=input_json)
    # Write input JSON to a file
    # with open('input.json', 'w') as f:
    #     json.dump(json_keys, f)

    # Upload the input file to S3 bucket
    # s3.upload_file('input.json', bucket_name, input_key)

    # Establish a connection to the EC2 instance using SSH with paramiko
    pemkey = paramiko.RSAKey.from_private_key_file('us-east-1kp.pem')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh.connect(hostname=public_dns_name, username='ubuntu', key_filename='us-east-1kp.pem')
    ssh.connect(hostname=public_dns_name, username='ubuntu', pkey=pemkey)

    command = 'cd /var/www/html && python3 ec2_function.py ' + input_key + ' ' + output_key
    # Run the simulation script on the instance
    stdin, stdout, stderr = ssh.exec_command(command)

    # Wait for the simulation to complete
    while not stdout.channel.exit_status_ready():
        time.sleep(1)

    # Close the SSH connection
    ssh.close()

    # Download the output file from S3 bucket
    newobj = s3.get_object(Bucket='instance-results',Key=output_key)
    output_json = json.loads(newobj['Body'].read().decode('utf-8'))

    # Download the output file from S3 bucket
    # s3.download_file(bucket_name, output_key, 'output.json')

    # Extract the required lists from the output data
    risk95_values = output_json['risk95_values']
    risk99_values = output_json['risk99_values']

    # Read the output file
    # with open('output.json') as f:
    #     ec2_out_data = json.load(f)

    # risk95_values = ec2_out_data[0]
    # risk99_values = ec2_out_data[1]

#################################

# Function for testing all calculations locally

def calculate(data, minhistory, shots, signaltype, P):

    # create empty lists to store the results
    signal_dates = []
    risk95_values = []
    risk99_values = []
    pnl_values = []

    for i in range(minhistory, len(data)):
        if (i+P) < len(data): # this ignores signals where we don't have price_p_days_forward
            if signaltype=="Buy" and data[i][7]==1: # for buy signals
                # calculate the mean and standard deviation of the price changes over the past minhistory days
                pct_changes = [data[j][4]/data[j-1][4] - 1 for j in range(i-minhistory, i)] # percent changes with previous closing price
                mean = sum(pct_changes)/len(pct_changes)
                std = math.sqrt(sum([(x-mean)**2 for x in pct_changes])/len(pct_changes))
                
                # generate much larger random number series with same broad characteristics
                simulated = [random.gauss(mean,std) for x in range(shots)]
                
                # sort and pick 95% and 99%  - not distinguishing long/short risks here
                simulated.sort(reverse=True)
                var95 = simulated[int(len(simulated)*0.95)]
                var99 = simulated[int(len(simulated)*0.99)]
                
                # record the signal date and risk values
                signal_dates.append(data[i][0])
                risk95_values.append(var95)
                risk99_values.append(var99)
                
                # calculate the profit/loss per share based on the difference between the price at the signal and the price P days forward
                price_at_signal = data[i][4]
                price_p_days_forward = data[i+P][4]

                pnl_per_share = price_p_days_forward - price_at_signal
                
                # record the profit/loss per share
                pnl_values.append(pnl_per_share)
            
            elif signaltype=="Sell" and data[i][8]==1:
                # calculate the mean and standard deviation of the price changes over the past minhistory days
                pct_changes = [data[j][4]/data[j-1][4] - 1 for j in range(i-minhistory, i)] # percent changes with previous closing price
                mean = sum(pct_changes)/len(pct_changes)
                std = math.sqrt(sum([(x-mean)**2 for x in pct_changes])/len(pct_changes))
                
                # generate much larger random number series with same broad characteristics
                simulated = [random.gauss(mean,std) for x in range(shots)]
                
                # sort and pick 95% and 99%  - not distinguishing long/short risks here
                simulated.sort(reverse=True)
                var95 = simulated[int(len(simulated)*0.95)]
                var99 = simulated[int(len(simulated)*0.99)]
                
                # record the signal date and risk values
                signal_dates.append(data[i][0])
                risk95_values.append(var95)
                risk99_values.append(var99)
                
                # calculate the profit/loss per share based on the difference between the price at the signal and the price P days forward
                price_at_signal = data[i][4]
                price_p_days_forward = data[i+P][4]
                pnl_per_share =  price_at_signal - price_p_days_forward
                
                # record the profit/loss per share
                pnl_values.append(pnl_per_share)

    # create a list of lists to store the results - avoiding pandas dataframes
    result_list = [['Signal Date', 'Risk 95%', 'Risk 99%', 'Profit/Loss per Share']]
    for i in range(len(signal_dates)):
        result_list.append([signal_dates[i], risk95_values[i], risk99_values[i], pnl_values[i]])

        # calculate the total profit/loss and average risk values
    total_pnl = sum(pnl_values)
    avg_var95 = sum(risk95_values) / len(risk95_values)
    avg_var99 = sum(risk99_values) / len(risk99_values)

    return (result_list, total_pnl, avg_var95, avg_var99)

#################################
#################################
'''