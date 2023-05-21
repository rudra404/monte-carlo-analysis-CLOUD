#!/usr/bin/python3
# import required libraries
import json
import random
import math
import sys

# Use system standard input to read the recieved request input data
request_body = sys.stdin.read()
input_json = json.loads(request_body)

# Extract the required parameters from the input data
minhistory = int(input_json['history'])
shots = int(input_json['shots'])
signaltype = str(input_json['signal_type'])
P = int(input_json['time_horizon'])
closing_prices = input_json['closing_prices']
buy_signals = input_json['buy_signals']
sell_signals = input_json['sell_signals']

# create empty lists to store the results
risk95_values = []
risk99_values = []

# start simulations
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

        
        elif signaltype=="Sell" and sell_signals[i]==1: # for sell signals
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
            
# create a dictionary to store simulation results
simulation_results = {
    'risk95_values': risk95_values,
    'risk99_values': risk99_values
}

# convert the dictionary to a JSON string and print it using headers in required format
output_json = json.dumps(simulation_results)
print('Content-Type: application/json')
print()
print(output_json)
