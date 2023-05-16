'''
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

import json
import os

os.environ['AWS_SHARED_CREDENTIALS_FILE']='./cred' 

import boto3
s3 = boto3.client('s3')
# Create an empty list with table headers
table_headers = ['Service (S)', 'Resources (R)', 'Price Hsitory (H)', 'Data Points (D)', 'Signal Type (T)', 'Profitability Horizon (P)', 'Avg 95 Risk', 'Avg 99 Risk', 'Total PnL ($)', 'Runtime (sec)', 'Cost ($)']
data_list = [table_headers]

# Convert the list to JSON format
json_data = json.dumps(data_list)

# Store the JSON data in a variable
object_key = 'audit.json'
bucket_name = 'audit-page-bucket'

# Upload the JSON data to an S3 bucket using the `put_object` method
s3.put_object(Body=json_data, Bucket=bucket_name, Key=object_key)

print('Empty list with table headers created and stored in S3.')

def read_list_from_s3(bucket_name, file_name):
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_name)
        content = response['Body'].read().decode('utf-8')
        data = json.loads(content)
        return data
    except Exception as e:
        print('Error reading list from S3:', str(e))
        return []

def write_list_to_s3(bucket_name, file_name, data):
    try:
        content = json.dumps(data)
        s3.put_object(Body=content, Bucket=bucket_name, Key=file_name)
        print('List successfully written to S3.')
    except Exception as e:
        print('Error writing list to S3:', str(e))

@app.route('/update_list')
def update_list():
    # Read the existing list from S3
    bucket_name = 'audit-page-bucket'
    file_name = 'audit.json'
    existing_list = read_list_from_s3(bucket_name, file_name)

    # Append new values to the list
    new_values = ['lambda', 4, 20, 100, 'Buy', 25, -0.00432, -0.023434, 128, 3, 3]
    existing_list.append(new_values)
    print(existing_list)
    # Write the updated list back to S3
    write_list_to_s3(bucket_name, file_name, existing_list)

    return 'List updated and stored in S3.'
'''