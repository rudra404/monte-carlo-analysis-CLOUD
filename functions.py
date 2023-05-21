#!/usr/bin/env python3
# import required libraries
import math
import random
import yfinance as yf
from datetime import date, timedelta
from pandas_datareader import data as pdr
# Lambda imports
import http.client
import json
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
# EC2 imports
import os
from flask import session

import requests
os.environ['AWS_SHARED_CREDENTIALS_FILE']='./cred' 

import boto3

# Override yfinance with pandas – seems to be a common step
yf.pdr_override()

###### FUNCTIONS FOR GENERAL USE ######

# Define a function to fetch stock data from yfinance and convert to list format
def fetch_stock_data():
    # Get NFLX stock data from Yahoo Finance – here, asking for 3 years
    today = date.today()
    ThreeYearsAgo = today - timedelta(days=1095)

    data = pdr.get_data_yahoo('NFLX', start=ThreeYearsAgo, end=today) # get data for NETFLIX
    
    # Convert the dataframe to a list of lists - avoiding pandas for consistency with EC2 and lambda scripts
    # Add columns for BUY and SELL signals
    data_list = []
    for index, row in data.iterrows():
        data_list.append([index.date(), row['Open'], row['High'], row['Low'], row['Close'], row['Adj Close'], row['Volume'], 0, 0])

    return data_list

# Define function to identify buy and sell signals in the data
def find_signals(data):
    # Find signals
    for i in range(2, len(data)):
        body = 0.01
        # Three Soldiers
        if (data[i][4] - data[i][1]) >= body \
                and data[i][4] > data[i-1][4] \
                and (data[i-1][4] - data[i-1][1]) >= body \
                and data[i-1][4] > data[i-2][4] \
                and (data[i-2][4] - data[i-2][1]) >= body:
            data[i][7] = 1

        # Three Crows
        if (data[i][1] - data[i][4]) >= body \
                and data[i][4] < data[i-1][4] \
                and (data[i-1][1] - data[i-1][4]) >= body \
                and data[i-1][4] < data[i-2][4] \
                and (data[i-2][1] - data[i-2][4]) >= body:
            data[i][8] = 1

    return data

# Define a function to generate the url for plotting results graph
def make_img_url(result_list, avg_var95, avg_var99):
    signal_dates = [row[0] for row in result_list[1:]]  # Extract signal dates
    risk95_values = [row[1] for row in result_list[1:]]  # Extract Risk 95% values
    risk99_values = [row[2] for row in result_list[1:]]  # Extract Risk 99% values
    avg_var95_values = [avg_var95]*len(signal_dates)  # Create list of average 95 values
    avg_var99_values = [avg_var99]*len(signal_dates)  # Create list of average 99 values
    # Format as strings
    signal_dates_str = ','.join([date.strftime('%Y-%m-%d') for date in signal_dates])
    risk95_values_str = ','.join([str(val) for val in risk95_values])
    risk99_values_str = ','.join([str(val) for val in risk99_values])
    avg_var95_values_str = ','.join(str(v) for v in avg_var95_values)
    avg_var99_values_str = ','.join(str(v) for v in avg_var99_values)

    # Using quickchart.io here which is a better option and more visually pleasing than google charts and image charts
    img_url = f"https://quickchart.io/chart/render/zm-f285fd40-0b04-481b-a408-84fb4b705c8c?labels={signal_dates_str}&data1={risk95_values_str}&data2={risk99_values_str}&data3={avg_var95_values_str}&data4={avg_var99_values_str}"

    return img_url

# Define a function to calculate average values from all runs
def averaging_results(results):
    # Create empty lists to store results
    signal_dates = []
    risk95_values = []
    risk99_values = []
    pnl_values = []

    for i in range(len(results[0][0])):
        signal_dates.append(results[0][0][i][0]) # Copying signal dates from first set of results

    for i in range(len(results[0][0])):
        avg = 0
        for result in results:
            avg = avg + result[0][i][1]
        avg = avg / len(results)

        risk95_values.append(avg) # Average risk 95 values of all runs

    for i in range(len(results[0][0])):
        avg = 0
        for result in results:
            avg = avg + result[0][i][2]
        avg = avg / len(results)

        risk99_values.append(avg) # Average risk 95 values of all runs

    for i in range(len(results[0][0])):
        avg = 0
        for result in results:
            avg = avg + result[0][i][3]
        avg = avg / len(results)

        pnl_values.append(avg) # Average profit & loss values of all runs

    # Create a results list to return values
    result_list = [['Signal Date', 'Risk 95%', 'Risk 99%', 'Profit/Loss per Share']]
    for i in range(len(signal_dates)):
        result_list.append([signal_dates[i], risk95_values[i], risk99_values[i], pnl_values[i]])

    # Calculate the total profit/loss and average risk values and return with the results list
    total_pnl = sum(pnl_values)
    avg_var95 = sum(risk95_values) / len(risk95_values)
    avg_var99 = sum(risk99_values) / len(risk99_values)

    return (result_list, total_pnl, avg_var95, avg_var99)


###### FUNCTIONS FOR LAMBDA ######

# Define a function to use lambda for simulation and calculation of risk values
# This function also handles further calculation and returns a list of results
def uselambda(data, h, d, t, p):
	# Collecting only columns required for simulations to be sent
	closing_prices = [data[i][4] for i in range(len(data))]
	buy_signals = [data[i][7] for i in range(len(data))]
	sell_signals = [data[i][8] for i in range(len(data))]
	# Establish a connection using invoke URL of lambda_calc function
	connection = http.client.HTTPSConnection("wie41at3mc.execute-api.us-east-1.amazonaws.com")
	# Creating a dictionary to send input data to the function
	json_keys = {
    "history": h,
    "shots": d,
    "signal_type": t,
    "time_horizon": p,
    "closing_prices": closing_prices,
    "buy_signals": buy_signals,
    "sell_signals": sell_signals
	}

	input_json = json.dumps(json_keys) # Converting dictionary to json
	connection.request("POST", "/default/lambda_calc", input_json) # Sending a POST request to lambda function
    # Get the response and convert to json and further to a list of lists
	response = connection.getresponse()
	lambda_out_data = response.read().decode('utf-8')
	lambda_out_data = json.loads(lambda_out_data)

	signal_dates = []
	risk95_values = []
	risk99_values = []
	pnl_values = []

    # Extract output from lambda function
	risk95_values = lambda_out_data[0]
	risk99_values = lambda_out_data[1]

    # Calculation steps after completing simulation
	for i in range(h, len(data)):
		if (i+p) < len(data): # this ignores signals where we don't have price_p_days_forward
			if t=="Buy" and data[i][7]==1: # for buy signals
				signal_dates.append(data[i][0]) # record the signal date
				# calculate the profit/loss per share based on the difference between the price at the signal and the price P days forward
				price_at_signal = data[i][4]
				price_p_days_forward = data[i+p][4]
				pnl_per_share = price_p_days_forward - price_at_signal
				# record the profit/loss per share
				pnl_values.append(pnl_per_share)
			
			elif t=="Sell" and data[i][8]==1: # for sell signals
				signal_dates.append(data[i][0]) # record the signal date
				# calculate the profit/loss per share based on the difference between the price at the signal and the price P days forward
				price_at_signal = data[i][4]
				price_p_days_forward = data[i+p][4]
				pnl_per_share =  price_at_signal - price_p_days_forward
				# record the profit/loss per share
				pnl_values.append(pnl_per_share)
	
	# Create a list of lists to store the results - avoiding pandas dataframes
	result_list = []

	for i in range(len(signal_dates)):
		result_list.append([signal_dates[i], risk95_values[i], risk99_values[i], pnl_values[i]])

	# Calculate the total profit/loss and average risk values
	total_pnl = sum(pnl_values)
	avg_var95 = sum(risk95_values) / len(risk95_values)
	avg_var99 = sum(risk99_values) / len(risk99_values)

	return [result_list, total_pnl, avg_var95, avg_var99]

# Define a function to run multiple uselambda() functions in parallel using ThreadPoolExecutor
def uselambda_parallel(data, h, d, t, p, r):
	with ThreadPoolExecutor(max_workers=19) as executor:
		futures = []
        # We want to parallelize within 'r' functions
		for i in range(int(r)):
			future = executor.submit(uselambda, data, h, d, t, p)
			futures.append(future)

		results = []
		for future in concurrent.futures.as_completed(futures):
			result = future.result()
			results.append(result)

	return results

###### FUNCTIONS FOR EC2 ######

# Define a function to initialize EC2 instances
def launchec2(r):
    os.environ['AWS_SHARED_CREDENTIALS_FILE']='./cred' 
    # Above line needs to be here before boto3 to ensure cred file is read from the right place
    import boto3

    # Set the user data that will be run as a bash script when EC2 instances are initialized
    # It is not being imported from another file hosting service to increase speed and reduce errors
    user_data = """#!/bin/bash
                # Update packages
                apt update -y
                # Install required packages
                apt install python3 apache2 -y
                # Restart Apache
                apache2ctl restart
                # Copy files from gitlab public domain to the new instance
                # Hosting on GAE increases the time taken by a lot
                wget https://gitlab.surrey.ac.uk/rs01922/montecarlo_cw_files/-/raw/main/apache2.conf -O /etc/apache2/apache2.conf
                wget https://gitlab.surrey.ac.uk/rs01922/montecarlo_cw_files/-/raw/main/ec2_function.py -P /var/www/html
                # Set permissions
                chmod 755 /var/www/html/ec2_function.py
                # Enable CGI module and restart Apache
                a2enmod cgi
                # Restart Apache to use new config file and ensure everything is fine
                service apache2 restart"""
    

    ec2 = boto3.resource('ec2', region_name='us-east-1')

    session['ec2starttime'] = time.time() # Store the start time in a session variable. This will be overwritten each time instances are initialized

    instances = ec2.create_instances(
        ImageId = 'ami-007855ac798b5175e', # Ubuntu AMI
        MinCount = int(r), # initialize 'r' instances
        MaxCount = int(r), 
        InstanceType = 't2.micro', 
        KeyName = 'us-east-1kp', # Security key
        SecurityGroups=['ssh'], # Security group
        UserData=user_data
        )
    public_dns_names = []
    # Wait for AWS to report instance(s) ready
    for i in instances:
        i.wait_until_running()
        # Reload the instance attributes
        i.load()
        public_dns_names.append(i.public_dns_name)
    print(public_dns_names)
    session['public_dns_names'] = [public_dns_names] # Store list of DNS names in session variable
    return public_dns_names

# Define a function to run the simulation on an EC2 instance
def useec2(public_dns_name, data, h, d, t, p):
    # Collect only required columns
    closing_prices = [data[i][4] for i in range(len(data))]
    buy_signals = [data[i][7] for i in range(len(data))]
    sell_signals = [data[i][8] for i in range(len(data))]


    # Create a dictionary to send input data to the function
    json_keys = {
        "history": h,
        "shots": d,
        "signal_type": t,
        "time_horizon": p,
        "closing_prices": closing_prices,
        "buy_signals": buy_signals,
        "sell_signals": sell_signals
    }

    # Create empty lists to store the results
    signal_dates = []
    risk95_values = []
    risk99_values = []
    pnl_values = []

    url = 'http://' + public_dns_name + '/ec2_function.py' # Connect to the initialized and configured EC2 instance using this url
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(json_keys)) # Send a POST request to the EC2 instance

    # Some error handling for the response recieved from EC2
    if response.status_code != 200:
        print('Error:', response.status_code)
        return None

    if not response.text:
        print('Error: Response is empty')
        return None

    # Collect the response from EC2
    response_data = json.loads(response.text)

    # Extract simulation result values from EC2 output
    risk95_values = response_data['risk95_values']
    risk99_values = response_data['risk99_values']


    # Remaining calculation steps repeated as before
    for i in range(h, len(data)):
        if (i+p) < len(data): # This ignores signals where we don't have price_p_days_forward
            if t=="Buy" and data[i][7]==1: # For buy signals
                signal_dates.append(data[i][0]) # Record the signal date
                # Calculate the profit/loss per share based on the difference between the price at the signal and the price P days forward
                price_at_signal = data[i][4]
                price_p_days_forward = data[i+p][4]
                pnl_per_share = price_p_days_forward - price_at_signal
                # Record the profit/loss per share
                pnl_values.append(pnl_per_share)
            
            elif t=="Sell" and data[i][8]==1: # For sell signals
                signal_dates.append(data[i][0]) # Record the signal date
                # Calculate the profit/loss per share based on the difference between the price at the signal and the price P days forward
                price_at_signal = data[i][4]
                price_p_days_forward = data[i+p][4]
                pnl_per_share =  price_at_signal - price_p_days_forward
                # Record the profit/loss per share
                pnl_values.append(pnl_per_share)

    # Create a list of lists to store the results - avoiding pandas dataframes
    result_list = []

    for i in range(len(signal_dates)):
        result_list.append([signal_dates[i], risk95_values[i], risk99_values[i], pnl_values[i]])

    # Calculate the total profit/loss and average risk values
    total_pnl = sum(pnl_values)
    avg_var95 = sum(risk95_values) / len(risk95_values)
    avg_var99 = sum(risk99_values) / len(risk99_values)

    return [result_list, total_pnl, avg_var95, avg_var99] # Return a list of results and required values

# define a function to use multiple instances of ec2
def useec2_parallel(data, h, d, t, p, public_dns_names):    
    # Create a list to store the results from all instances
    results = []

    # Launch one thread for each instance to calculate the results
    with ThreadPoolExecutor(max_workers=len(public_dns_names)) as executor:
        futures = []
        for public_dns_name in public_dns_names:
            futures.append(executor.submit(useec2, public_dns_name, data, h, d, t, p))

        # Wait for all threads to finish and collect the results
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)

    return results # Return the combined results


###### FUNCTIONS FOR AUDIT ######
# Define function to read the existing audit list from S3 bucket using boto3 with error handling
def read_list_from_s3(bucket_name, file_name):
    try:
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=bucket_name, Key=file_name)
        content = response['Body'].read().decode('utf-8')
        data = json.loads(content)
        return data
    except Exception as e:
        print('Error reading list from S3:', str(e))
        return []

# Define function to write the updated audit list to S3 bucket using boto3 with error handling
def write_list_to_s3(bucket_name, file_name, data):
    try:
        s3 = boto3.client('s3')
        content = json.dumps(data)
        s3.put_object(Body=content, Bucket=bucket_name, Key=file_name)
    except Exception as e:
        print('Error writing list to S3:', str(e))