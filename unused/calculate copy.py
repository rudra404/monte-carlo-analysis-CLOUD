'''
#!/usr/bin/env python3

import math
import random
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from pandas_datareader import data as pdr
# override yfinance with pandas – seems to be a common step
yf.pdr_override()

def fetch_stock_data():
    # Get stock data from Yahoo Finance – here, asking for about 3 years
    today = date.today()
    ThreeYearsAgo = today - timedelta(days=1095)

    # Get stock data from Yahoo Finance – here, Gamestop which had an interesting
    #time in 2021: https://en.wikipedia.org/wiki/GameStop_short_squeeze

    data = pdr.get_data_yahoo('NFLX', start=ThreeYearsAgo, end=today) # get data for NETFLIX
    print(data.index[0])
    # Add two columns to this to allow for Buy and Sell signals
    # fill with zero
    data['Buy']=0
    data['Sell']=0

    return data

def find_signals(data, signaltype):
# Find the signals – uncomment print statements if you want to
# look at the data these pick out in some another way
# e.g. check that the date given is the end of the pattern claimed

    for i in range(2, len(data)):

        body = 0.01
        if signaltype == "Buy":
            # Three Soldiers
            if (data.Close[i] - data.Open[i]) >= body  \
        and data.Close[i] > data.Close[i-1]  \
        and (data.Close[i-1] - data.Open[i-1]) >= body  \
        and data.Close[i-1] > data.Close[i-2]  \
        and (data.Close[i-2] - data.Open[i-2]) >= body:
                data.at[data.index[i], 'Buy'] = 1
                #print("Buy at ", data.index[i])
        elif signaltype == "Sell":
            # Three Crows
            if (data.Open[i] - data.Close[i]) >= body  \
        and data.Close[i] < data.Close[i-1] \
        and (data.Open[i-1] - data.Close[i-1]) >= body  \
        and data.Close[i-1] < data.Close[i-2]  \
        and (data.Open[i-2] - data.Close[i-2]) >= body:
                data.at[data.index[i], 'Sell'] = 1
                #print("Sell at ", data.index[i])

    # Data now contains signals, so we can pick signals with a minimum amount
    # of historic data, and use shots for the amount of simulated values
    # to be generated based on the mean and standard deviation of the recent history
    return data

def calculate(data, minhistory, shots, signaltype, P):

    # create empty lists to store the results
    signal_dates = []
    risk95_values = []
    risk99_values = []
    pnl_values = []

    for i in range(minhistory, len(data)):
        if (i+P) < len(data):
            if signaltype=="Buy" and data.Buy[i]==1: # if we’re interested in Buy or Sell signals
                # calculate the mean and standard deviation of the price changes over the past minhistory days
                mean = data.Close[i-minhistory:i].pct_change(1).mean()
                std = data.Close[i-minhistory:i].pct_change(1).std()
                
                # generate much larger random number series with same broad characteristics
                simulated = [random.gauss(mean,std) for x in range(shots)]
                
                # sort and pick 95% and 99%  - not distinguishing long/short risks here
                simulated.sort(reverse=True)
                var95 = simulated[int(len(simulated)*0.95)]
                var99 = simulated[int(len(simulated)*0.99)]
                
                # record the signal date and risk values
                signal_dates.append(data.index[i])
                risk95_values.append(var95)
                risk99_values.append(var99)
                
                # calculate the profit/loss per share based on the difference between the price at the signal and the price P days forward
                price_at_signal = data.Close[i]
                price_P_days_forward = data.Close[i+P]

                pnl_per_share = price_P_days_forward - price_at_signal
                
                # record the profit/loss per share
                pnl_values.append(pnl_per_share)
            
            elif signaltype=="Sell" and data.Sell[i]==1:
                # calculate the mean and standard deviation of the price changes over the past minhistory days
                mean = data.Close[i-minhistory:i].pct_change(1).mean()
                std = data.Close[i-minhistory:i].pct_change(1).std()
                
                # generate much larger random number series with same broad characteristics
                simulated = [random.gauss(mean,std) for x in range(shots)]
                
                # sort and pick 95% and 99%  - not distinguishing long/short risks here
                simulated.sort(reverse=True)
                var95 = simulated[int(len(simulated)*0.95)]
                var99 = simulated[int(len(simulated)*0.99)]
                
                # record the signal date and risk values
                signal_dates.append(data.index[i])
                risk95_values.append(var95)
                risk99_values.append(var99)
                
                # calculate the profit/loss per share based on the difference between the price at the signal and the price P days forward
                price_at_signal = data.Close[i]
                price_P_days_forward = data.Close[i+P]
                pnl_per_share =  price_at_signal - price_P_days_forward
                
                # record the profit/loss per share
                pnl_values.append(pnl_per_share)

    # create a pandas DataFrame to store the results
    result_df = pd.DataFrame({'Signal Date': signal_dates, 
                            'Risk 95%': risk95_values, 
                            'Risk 99%': risk99_values, 
                            'Profit/Loss per Share': pnl_values})

    # calculate the total profit (or loss)
    total_pnl = result_df['Profit/Loss per Share'].sum()
    avg_var95 = result_df['Risk 95%'].mean()
    avg_var99 = result_df['Risk 99%'].mean()

    return(result_df, total_pnl, avg_var95, avg_var99)
# print the results
# print(result_df)
# print('Total Profit/Loss : {:.2f}'.format(total_pnl))
# print('Average Risk 95% : {:.2f}'.format(avg_var95))
# print('Average Risk 99% : {:.2f}'.format(avg_var99))
'''