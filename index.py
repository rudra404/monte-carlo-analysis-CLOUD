# import required libraries and functions from other python files

import os
import logging
from flask import Flask, request, render_template
import http.client
import json
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from functions import fetch_stock_data, find_signals, calculate, make_img_url, averaging_lambda_results
from globals import s,r

app = Flask(__name__)

# various Flask explanations available at:  https://flask.palletsprojects.com/en/1.1.x/quickstart/

# define a function to render pages while taking in parameters
def doRender(tname, values={}):
	if not os.path.isfile( os.path.join(os.getcwd(), 'templates/'+tname) ): #No such file
		return render_template('index.htm')
	return render_template(tname, **values) 

@app.route('/hello')
# Keep a Hello World message to show that at least something is working
def hello():
    return 'Hello World!'

################
# @app.route('/random', methods=['POST'])
# def RandomHandler():
#         import http.client
#         if request.method == 'POST':
#                 v = request.form.get('key1')
#                 c = http.client.HTTPSConnection("ium4xzu2u0.execute-api.us-east-1.amazonaws.com")
#                 json= '{ "key1": "'+v+'"}'
#                 c.request("POST", "/default/function_one", json)
#                 response = c.getresponse()
#                 data = response.read().decode('utf-8')
#                 return doRender( 'index.htm',
#                         {'note': data} )
###############

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

def uselambda_parallel(data, h, d, t, p):
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


# Defines a POST supporting calculate route
@app.route('/calculate', methods=['POST'])
def calculateHandler():
	if request.method == 'POST':

		# s = request.form.get('select_service')
		# r = request.form.get('num_r')
		h = int(request.form.get('num_h')) # history
		d = int(request.form.get('num_d')) # shots
		t = request.form.get('select_signal') # signal type
		p = int(request.form.get('num_p')) # time horizon

		# Check if inputs are correct
		# note = ''
		note1 = ''
		note2 = ''
		note3 = ''

		# if int(r) < 0 or int(r) > 19: 	# Check if input for R is within 0-19 to avoid AWS academy account deactivation
		# 	note = 'Please enter a value between 0 and 19'
		if int(h) < 1 or int(h) > 1095: # max data fetched from yfinance
			note1 = 'Please enter a value between 1 and 1095'
		if int(d) < 0:
			note2 = 'Please enter a positive value'
		if int(p) < 0:
			note3 = 'Please enter a positive value'
			
		if note1 or note2 or note3:
			return doRender('index.htm', {'note1': note1, 'note2': note2, 'note3': note3})
		else:
			# functions from calculate.py
			data = fetch_stock_data()
			find_signals(data, t)
			if s == 'lambda':
				results = uselambda_parallel(data, h, d, t, p)
				# print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
				# print(results)
				# print(len(results))
				# print(results[3])
				# print(results[1][2])
				# skip first value from each resutl bec those are labels

				# runs=[value for value in range(int(r))]
				# with ThreadPoolExecutor() as executor:
				# 	result_list, total_pnl, avg_var95, avg_var99 = executor.map(uselambda, data, h, d, t, p, runs)
				# 	print(result_list)
				result_list, total_pnl, avg_var95, avg_var99 = averaging_lambda_results(results)
				if result_list:
					img_url = make_img_url(result_list, avg_var95, avg_var99)
				
				# uselambda(data, h, d, t, p)
			elif s == 'ec2':
				result_list, total_pnl, avg_var95, avg_var99 = calculate(data, h, d, t, p)
				if result_list:
					img_url = make_img_url(result_list, avg_var95, avg_var99)
					
			# display results using a new template results.htm
			return doRender('results.htm', {'result_list': result_list, 'total_pnl': total_pnl, 'avg_var95': avg_var95, 'avg_var99': avg_var99, 'img_url': img_url})
			
	return 'Should not ever get here'
	
# Defines a POST supporting initialize route
@app.route('/initialize', methods=['POST'])
def initializeHandler():
	if request.method == 'POST':
		global s, r
		s = request.form.get('select_service')
		r = request.form.get('num_r')
		# Check if input for R is within 0-19 to avoid AWS academy account deactivation
		if int(r) < 0 or int(r) > 19:
			return doRender('index.htm', {'note': 'Please enter a value between 0 and 19'})
		else:
			return '', 204

	return 'Should not ever get here'

# catch all other page requests - doRender checks if a page is available (shows it) or not (index)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def mainPage(path):
	return doRender(path)

@app.errorhandler(500)
# A small bit of error handling
def server_error(e):
    logging.exception('ERROR!')
    return """
    An  error occurred: <pre>{}</pre>
    """.format(e), 500

if __name__ == '__main__':
    # Entry point for running on the local machine
    # On GAE, endpoints (e.g. /) would be called.
    # Called as: gunicorn -b :$PORT index:app,
    # host is localhost; port is 8080; this file is index (.py)
    app.run(host='127.0.0.1', port=8080, debug=True)

