# Monte Carlo Analysis on the Cloud
The aim of this project is to demonstrate my understanding of how to critically explain, and construct, a Cloud application using multiple services across Cloud providers (AWS lambda, EC2, S3, and Google App Engine), involving user-specifiable scaling.

The flask web app analyses trade signals on the financial time series data of NFLX obtained from yahoo finance.
The trade signals are given by 'Three White Soldiers' and 'Three Black Crows' strategies.
95% and 99% risk values are determined for each trade signal using a monte carlo simulation.
The audit page stores results from all previous runs to estimate costs for resources used.

## Brief example user scenario
The user asks the system to ‘warm up’ 4 resources (R) of the type selected (S). Resources, either Lambda, or EC2, are brought to a point where they are ready for running analysis.

The user specifies 80,000 shots (D) per R, with a history of 200 days per signal (H) and for Buy signals (T) and a Profitability time horizon P of 10 days.

In doing so, the user expects that, for each signal, 320,000 shots are being produced in total, and there will be the averaging of 4 values for each of 95% and 99% - i.e. two values per R – that results in one value per signal for each of 95% and 99% - and only these two values result from analysis per signal. In addition, the value of profit (or loss) for each signal is calculated using the difference between the price at the signal and, when available, the price P days forward of the signal – for a Buy signal, there is profit if the price has moved higher but loss if lower; for Sell, there is profit if the price has moved lower but loss if it has moved higher.

Following this analysis, the user will be presented with a chart showing all risk values – the two risk values for each signal, and two lines of averages over these – one over the 95% signal values and one over the 99% signal values. The total value of profit/loss, and the table, will also be presented to the user.

All the result values and estimated costs (based on resource type chosen) will be stored on an AWS S3 bucket and displayed on the Audit page. The user could run further analysis, but for this scenario has done enough so wants (non-Lambda) resources to be terminated. This does not, however, delete the Audit, which needs to be stored across uses/sessions.

## Quick look

Registration, authentication, login functionality. <br /><br />
![](screencaps/login.gif) <br /><br />
What the app looks like after logging in. <br /><br />
![](screencaps/appfunctions.gif) <br /><br />

## Pre-requisites

Install packages from the 'requirements.txt' file. This also installs packages required for the app to run on the cloud services.

## Note
The deployed app will not work on the cloud services at this time, however you may clone and test it locally using the instructions below. The code can be referenced for creating similar applications to be deployed using the chosen services.

## Start the app
Within the root directory, use the following command to start the application:
'''
python index.py
'''

## Test the app
1. Once you start the flask app, it will run on localhost. The terminal confirms 'Running on http://127.0.0.1:8080/ '. Enter this in the browser to access the application.
2. Enter the following example values to do a trial run:<br />
    a. S: Run Locally
    b. R: 4
3. Click on 'Initialize' before entering other values and wait for the green confirmation button.
4. Enter the remaining values:<br />
    c. H: 30
    d. D: 200
    e. T: Buy
    f. P: 30
5. Click on the 'Calculate' button to view the results page with relevant graph and results tables.
6. You may now click the 'Reset' button to start new calculations with your own values. 

Note: the audit page will also not display anything as this S3 bucket will not be functional after trial has ended.


## Acknowledgements
Project supervisor: [Dr. Lee Gilliam](https://sites.google.com/site/drleegillam/)
