#!/usr/bin/env python3
# import required libraries
import math
import random
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from pandas_datareader import data as pdr
#lambda imports
import http.client
import json
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
#ec2 imports
import os

# override yfinance with pandas – seems to be a common step
yf.pdr_override()

###### FUNCTIONS FOR GENERAL USE ######

# define a function to fetch stock data from yfinance and convert to list format
def fetch_stock_data():
    # Get stock data from Yahoo Finance – here, asking for about 3 years
    today = date.today()
    ThreeYearsAgo = today - timedelta(days=1095)

    # Get stock data from Yahoo Finance – here, Gamestop which had an interesting
    #time in 2021: https://en.wikipedia.org/wiki/GameStop_short_squeeze

    data = pdr.get_data_yahoo('NFLX', start=ThreeYearsAgo, end=today) # get data for NETFLIX
    
    # Convert the dataframe to a list of lists
    data_list = []
    for index, row in data.iterrows():
        data_list.append([index.date(), row['Open'], row['High'], row['Low'], row['Close'], row['Adj Close'], row['Volume'], 0, 0])
        # add columns for BUY and SELL signals

    return data_list

# define function to identify buy and sell signals in the data
def find_signals(data):
    # Find the signals
    for i in range(2, len(data)):
        body = 0.01
        # if signaltype == "Buy":
        # Three Soldiers
        if (data[i][4] - data[i][1]) >= body \
                and data[i][4] > data[i-1][4] \
                and (data[i-1][4] - data[i-1][1]) >= body \
                and data[i-1][4] > data[i-2][4] \
                and (data[i-2][4] - data[i-2][1]) >= body:
            data[i][7] = 1
                #print("Buy at ", data[i][0])
        # elif signaltype == "Sell":
        # Three Crows
        if (data[i][1] - data[i][4]) >= body \
                and data[i][4] < data[i-1][4] \
                and (data[i-1][1] - data[i-1][4]) >= body \
                and data[i-1][4] < data[i-2][4] \
                and (data[i-2][1] - data[i-2][4]) >= body:
            data[i][8] = 1
                #print("Sell at ", data[i][0])
    return data

# define a function to generate the url for plotting a graph
def make_img_url(result_list, avg_var95, avg_var99):
    signal_dates = [row[0] for row in result_list[1:]]  # Extract signal dates
    risk95_values = [row[1] for row in result_list[1:]]  # Extract Risk 95% values
    risk99_values = [row[2] for row in result_list[1:]]  # Extract Risk 99% values
    avg_var95_values = [avg_var95]*len(signal_dates)  # Create list of average 95 values
    avg_var99_values = [avg_var99]*len(signal_dates)  # Create list of average 99 values
    # selected_dates = [date for date in signal_dates if date.day == 1] # Only show the first date of every month
    # selected_dates_str = ','.join([date.strftime('%Y-%m-%d') for date in selected_dates]) # Format dates as strings
    signal_dates_str = ','.join([date.strftime('%Y-%m-%d') for date in signal_dates]) # Format dates as strings
    risk95_values_str = ','.join([str(val) for val in risk95_values])
    risk99_values_str = ','.join([str(val) for val in risk99_values])
    avg_var95_values_str = ','.join(str(v) for v in avg_var95_values)
    avg_var99_values_str = ','.join(str(v) for v in avg_var99_values)

    img_url = f"https://quickchart.io/chart/render/zm-f285fd40-0b04-481b-a408-84fb4b705c8c?labels={signal_dates_str}&data1={risk95_values_str}&data2={risk99_values_str}&data3={avg_var95_values_str}&data4={avg_var99_values_str}"

    return img_url

# define a function for all calculations 
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

###### FUNCTIONS FOR LAMBDA ######
# define a function to use lambda for simulation and calculation of risk values
# this function also handles further calculation and returns a result_list
def uselambda(data, h, d, t, p):
	# collecting only required columns
	closing_prices = [data[i][4] for i in range(len(data))]
	buy_signals = [data[i][7] for i in range(len(data))]
	sell_signals = [data[i][8] for i in range(len(data))]
	# establish a connection using invoke URL of lambda_calc function
	connection = http.client.HTTPSConnection("wie41at3mc.execute-api.us-east-1.amazonaws.com")
	# creating a json to send input data to the function
	json_keys = {
    "history": h,
    "shots": d,
    "signal_type": t,
    "time_horizon": p,
    "closing_prices": closing_prices,
    "buy_signals": buy_signals,
    "sell_signals": sell_signals
	}

	input_json = json.dumps(json_keys)
	connection.request("POST", "/default/lambda_calc", input_json)
	response = connection.getresponse()
	lambda_out_data = response.read().decode('utf-8')
	lambda_out_data = json.loads(lambda_out_data)

	signal_dates = []
	risk95_values = []
	risk99_values = []
	pnl_values = []

	risk95_values = lambda_out_data[0]
	risk99_values = lambda_out_data[1]

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
			
			elif t=="Sell" and data[i][8]==1:
				signal_dates.append(data[i][0]) # record the signal date
				# calculate the profit/loss per share based on the difference between the price at the signal and the price P days forward
				price_at_signal = data[i][4]
				price_p_days_forward = data[i+p][4]
				pnl_per_share =  price_at_signal - price_p_days_forward
				# record the profit/loss per share
				pnl_values.append(pnl_per_share)
	
	# create a list of lists to store the results - avoiding pandas dataframes
	# result_list = [['Signal Date', 'Risk 95%', 'Risk 99%', 'Profit/Loss per Share']]
	result_list = []

	for i in range(len(signal_dates)):
		result_list.append([signal_dates[i], risk95_values[i], risk99_values[i], pnl_values[i]])

	# calculate the total profit/loss and average risk values
	total_pnl = sum(pnl_values)
	avg_var95 = sum(risk95_values) / len(risk95_values)
	avg_var99 = sum(risk99_values) / len(risk99_values)

	# print("USE LAMBDAAAAAAA")
	# print([result_list, total_pnl, avg_var95, avg_var99])
	return [result_list, total_pnl, avg_var95, avg_var99]
	# return [result_list]

# define a function to run multiple uselambda() functions in parallel
def uselambda_parallel(data, h, d, t, p, r):
	with ThreadPoolExecutor(max_workers=19) as executor:
		futures = []
		for i in range(int(r)):
			future = executor.submit(uselambda, data, h, d, t, p)
			futures.append(future)

		results = []
		for future in concurrent.futures.as_completed(futures):
		# for future in futures:
			result = future.result()
			results.append(result)
	# print("USELAMBDA PARALLELLLLLLLLLLL")
	# print(results)
	return results

# define a function to calculate average values from all lambda runs
def averaging_lambda_results(results):
    signal_dates = []
    risk95_values = []
    risk99_values = []
    pnl_values = []

    for i in range(len(results[0][0])):
        signal_dates.append(results[0][0][i][0])

    for i in range(len(results[0][0])):
        avg = 0
        for result in results:
            # print(result[0][i][1])
            avg = avg + result[0][i][1]
        avg = avg / len(results)

        risk95_values.append(avg)

    for i in range(len(results[0][0])):
        avg = 0
        for result in results:
            # print(result[0][i][2])
            avg = avg + result[0][i][2]
        avg = avg / len(results)

        risk99_values.append(avg)

    for i in range(len(results[0][0])):
        avg = 0
        for result in results:
            # print(result[0][i][3])
            avg = avg + result[0][i][3]
        avg = avg / len(results)

        pnl_values.append(avg)

    # print(signal_dates)
    result_list = [['Signal Date', 'Risk 95%', 'Risk 99%', 'Profit/Loss per Share']]
    for i in range(len(signal_dates)):
        result_list.append([signal_dates[i], risk95_values[i], risk99_values[i], pnl_values[i]])
        # print(result_list)
        # calculate the total profit/loss and average risk values
    total_pnl = sum(pnl_values)
    avg_var95 = sum(risk95_values) / len(risk95_values)
    avg_var99 = sum(risk99_values) / len(risk99_values)

    return (result_list, total_pnl, avg_var95, avg_var99)

###### FUNCTIONS FOR EC2 ######
# define a function to run ec2
def launchec2(r):
    os.environ['AWS_SHARED_CREDENTIALS_FILE']='./cred' 
    # Above line needs to be here before boto3 to ensure cred file is read from the right place
    import boto3

    # Set the user-data we need – use your endpoint
    # user_data = """#!/bin/bash
    #             wget https://monte-carlo-analysis.nw.r.appspot.com/cacheavoid/setup.bash
    #             bash setup.bash"""
    user_data = """#!/bin/bash
                # Update packages
                apt update -y
                # Install required packages
                apt install python3 apache2 -y
                # apt install python3-pandas -y
                # Restart Apache
                apache2ctl restart
                # Copy files from public domain to instance - hosting these on GAE makes it very slow
                wget https://gitlab.surrey.ac.uk/rs01922/montecarlo_cw_files/-/raw/main/apache2.conf -O /etc/apache2/apache2.conf
                wget https://gitlab.surrey.ac.uk/rs01922/montecarlo_cw_files/-/raw/main/postform.py -P /var/www/html
                # Set permissions
                chmod 755 /var/www/html/postform.py
                # Enable CGI module and restart Apache
                a2enmod cgi
                service apache2 restart"""
    

    ec2 = boto3.resource('ec2', region_name='us-east-1')

    instances = ec2.create_instances(
        ImageId = 'ami-007855ac798b5175e', # Ubuntu AMI
        MinCount = int(r), 
        MaxCount = int(r), 
        InstanceType = 't2.micro', 
        KeyName = 'us-east-1kp', # Make sure you have the named us-east-1kp
        SecurityGroups=['ssh'], # Make sure you have the named SSH
        UserData=user_data # and user-data
        )

    # Wait for AWS to report instance(s) ready. 
    for i in instances:
        print(i)
        i.wait_until_running()
        # Reload the instance attributes
        i.load()
        print(i.public_dns_name) # ec2 com address

    return '', 204

    # Should add checks here that e.g. hello.py or index.html is responding
