'''
from flask import Flask, request, jsonify
import json
import random
import math

app = Flask(__name__)

@app.route('/work', methods=['POST'])
def run_simulation():
    # Parse the JSON input data
    input_json = request.json

    # Extract the required parameters from the input data
    minhistory = int(input_json['history'])
    shots = int(input_json['shots'])
    signaltype = str(input_json['signal_type'])
    P = int(input_json['time_horizon'])
    closing_prices = input_json['closing_prices']
    buy_signals = input_json['buy_signals']
    sell_signals = input_json['sell_signals']


    # print(minhistory, shots, signaltype, P)
    # print(buy_signals)
    # print(sell_signals)

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
                

    return (risk95_values, risk99_values)


    # # Return the results as a JSON response
    # response_json = {
    #     'result': result
    # }
    # return jsonify(response_json)

###### FUNCTIONS FROM functions.py TO WORK WITH EC2 USING FLASK ######
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
                apt install python3-flask -y
                # apt install python3-pandas -y
                # Restart Apache
                apache2ctl restart
                # Copy files from public domain to instance - hosting these on GAE makes it very slow
                wget https://gitlab.surrey.ac.uk/rs01922/montecarlo_cw_files/-/raw/main/apache2.conf -O /etc/apache2/apache2.conf
                wget https://gitlab.surrey.ac.uk/rs01922/montecarlo_cw_files/-/raw/main/ec2_function.py -P /var/www/html
                # Set permissions
                chmod 755 /var/www/html/ec2_function.py
                # Enable CGI module and restart Apache
                a2enmod cgi
                service apache2 restart
                FLASK_APP=/var/www/html/ec2_function.py flask run --host=0.0.0.0 &"""
    

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
    public_dns_names = []
    # Wait for AWS to report instance(s) ready. 
    for i in instances:
        i.wait_until_running()
        # Reload the instance attributes
        i.load()
        public_dns_names.append(i.public_dns_name)
        print(i.public_dns_name) # ec2 com address
    print(public_dns_names)
    return public_dns_names

# Function to run the simulation on an EC2 instance
def useec2(public_dns_name, data, h, d, t, p):
    # Collect only required columns
    closing_prices = [data[i][4] for i in range(len(data))]
    buy_signals = [data[i][7] for i in range(len(data))]
    sell_signals = [data[i][8] for i in range(len(data))]

    # Establish a connection to the EC2 instance
    connection = http.client.HTTPConnection(str(public_dns_name))
    print("EC222222222222222222")
    print(public_dns_name)
    print(type(public_dns_name))
    # Create a JSON to send input data to the function
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

    time.sleep(10)
    # Send a POST request to the instance to run the simulation
    connection.request("POST", "/work", input_json)
    response = connection.getresponse()
    ec2_out_data = response.read().decode('utf-8')
    ec2_out_data = json.loads(ec2_out_data)

    # Close the connection
    # connection.close()

    signal_dates = []
    risk95_values = []
    risk99_values = []
    pnl_values = []

    risk95_values = ec2_out_data[0]
    risk99_values = ec2_out_data[1]

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

# define a function to use multiple instances of ec2
def useec2_parallel(data, h, d, t, p, r):
    # Launch EC2 instances
    public_dns_names = launchec2(r)
    print("EC2 PARALLELLLLLLLLLLLLLLLLLLLLL")
    print(public_dns_names)
    print(type(public_dns_names[0]))
    # Collect public DNS names of all instances
    # public_dns_names = [i.public_dns_name for i in instances]

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

    # Combine the results from all instances
    # combined_results = combine_results(results)

    # Terminate all instances
    # terminateec2(ec2_client, instances)

    # Return the combined results
    return results
'''
