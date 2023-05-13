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
