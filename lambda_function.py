# import required libraries
import json
import random
import math

def lambda_handler(event, context):
    # Extract input values
    minhistory = int(event['history'])
    shots = int(event['shots'])
    signaltype = str(event['signal_type'])
    P = int(event['time_horizon'])
    closing_prices = event['closing_prices']
    buy_signals = event['buy_signals']
    sell_signals = event['sell_signals']

    # Create empty lists to store the results
    risk95_values = []
    risk99_values = []
    # Run simulations
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
                

    return (risk95_values, risk99_values) # Return simulation results


###### TEST EVENT ######
# {
#   "history": "2",
#   "shots": "200",
#   "signal_type": "Buy",
#   "time_horizon": "1",
#   "closing_prices": "[10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]",
#   "buy_signals": "[1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1]",
#   "sell_signals": "[0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0]"
# }