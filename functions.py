#!/usr/bin/env python3
# import required libraries
import math
import random
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from pandas_datareader import data as pdr
# override yfinance with pandas – seems to be a common step
yf.pdr_override()

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
def find_signals(data, signaltype):
    # Find the signals
    for i in range(2, len(data)):
        body = 0.01
        if signaltype == "Buy":
            # Three Soldiers
            if (data[i][4] - data[i][1]) >= body \
                    and data[i][4] > data[i-1][4] \
                    and (data[i-1][4] - data[i-1][1]) >= body \
                    and data[i-1][4] > data[i-2][4] \
                    and (data[i-2][4] - data[i-2][1]) >= body:
                data[i][7] = 1
                #print("Buy at ", data[i][0])
        elif signaltype == "Sell":
            # Three Crows
            if (data[i][1] - data[i][4]) >= body \
                    and data[i][4] < data[i-1][4] \
                    and (data[i-1][1] - data[i-1][4]) >= body \
                    and data[i-1][4] < data[i-2][4] \
                    and (data[i-2][1] - data[i-2][4]) >= body:
                data[i][8] = 1
                #print("Sell at ", data[i][0])
    return data

# define a function for all calculation
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

