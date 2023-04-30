#!/usr/bin/env python3

import math
import random
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from pandas_datareader import data as pdr
# override yfinance with pandas – seems to be a common step
yf.pdr_override()

# Get stock data from Yahoo Finance – here, asking for about 3 years
today = date.today()
decadeAgo = today - timedelta(days=1095)

# Get stock data from Yahoo Finance – here, Gamestop which had an interesting
#time in 2021: https://en.wikipedia.org/wiki/GameStop_short_squeeze

data = pdr.get_data_yahoo('NFLX', start=decadeAgo, end=today) # get data for NETFLIX
print(data.index[0])
# Add two columns to this to allow for Buy and Sell signals
# fill with zero
data['Buy']=0
data['Sell']=0


# Find the signals – uncomment print statements if you want to
# look at the data these pick out in some another way
# e.g. check that the date given is the end of the pattern claimed

for i in range(2, len(data)):

    body = 0.01

       # Three Soldiers
    if (data.Close[i] - data.Open[i]) >= body  \
and data.Close[i] > data.Close[i-1]  \
and (data.Close[i-1] - data.Open[i-1]) >= body  \
and data.Close[i-1] > data.Close[i-2]  \
and (data.Close[i-2] - data.Open[i-2]) >= body:
        data.at[data.index[i], 'Buy'] = 1
        print("Buy at ", data.index[i])

       # Three Crows
    if (data.Open[i] - data.Close[i]) >= body  \
and data.Close[i] < data.Close[i-1] \
and (data.Open[i-1] - data.Close[i-1]) >= body  \
and data.Close[i-1] < data.Close[i-2]  \
and (data.Open[i-2] - data.Close[i-2]) >= body:
        data.at[data.index[i], 'Sell'] = 1
        print("Sell at ", data.index[i])

# Data now contains signals, so we can pick signals with a minimum amount
# of historic data, and use shots for the amount of simulated values
# to be generated based on the mean and standard deviation of the recent history

minhistory = 101
shots = 10000
for i in range(minhistory, len(data)):
    if data.Buy[i]==1: # if we’re interested in Buy signals
               mean=data.Close[i-minhistory:i].pct_change(1).mean()
               std=data.Close[i-minhistory:i].pct_change(1).std()
               # generate much larger random number series with same broad characteristics
               simulated = [random.gauss(mean,std) for x in range(shots)]
               # sort and pick 95% and 99%  - not distinguishing long/short risks here
               simulated.sort(reverse=True)
               var95 = simulated[int(len(simulated)*0.95)]
               var99 = simulated[int(len(simulated)*0.99)]

               print(var95, var99) # so you can see what is being produced
