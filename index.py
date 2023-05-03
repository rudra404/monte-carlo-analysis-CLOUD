# import required libraries and functions from other python files

import os
import logging
from flask import Flask, request, render_template

from calculate import fetch_stock_data, find_signals, calculate


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
	import http.client
	import json
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
	print(lambda_out_data)


# Defines a POST supporting calculate route
@app.route('/calculate', methods=['POST'])
def calculateHandler():
	if request.method == 'POST':

		s = request.form.get('select_service')
		r = request.form.get('num_r')
		h = int(request.form.get('num_h')) # history
		d = int(request.form.get('num_d')) # shots
		t = request.form.get('select_signal') # signal type
		p = int(request.form.get('num_p')) # time horizon

		# Check if inputs are correct
		note = ''
		note1 = ''
		note2 = ''
		note3 = ''

		if int(r) < 0 or int(r) > 19: 	# Check if input for R is within 0-19 to avoid AWS academy account deactivation
			note = 'Please enter a value between 0 and 19'
		if int(h) < 1 or int(h) > 1095: # max data fetched from yfinance
			note1 = 'Please enter a value between 1 and 1095'
		if int(d) < 0:
			note2 = 'Please enter a positive value'
		if int(p) < 0:
			note3 = 'Please enter a positive value'
			
		if note or note1 or note2 or note3:
			return doRender('index.htm', {'note': note, 'note1': note1, 'note2': note2, 'note3': note3})
		else:
			# functions from calculate.py
			data = fetch_stock_data()
			find_signals(data, t)
			if s == 'lambda':
				# result_list, total_pnl, avg_var95, avg_var99 = uselambda(data, h, d, t, p)
				uselambda(data, h, d, t, p)
			elif s == 'ec2':
				result_list, total_pnl, avg_var95, avg_var99 = calculate(data, h, d, t, p)
				if result_list:
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
					# img_url = f"https://quickchart.io/chart/render/zm-0fa28e6d-70c1-4be9-b4db-47aebbdb8b4c?labels={signal_dates}&data1={risk95_values_str}&data2={risk99_values_str}"
					# img_url = f"https://image-charts.com/chart?cht=lc&chd=t:{risk95_values_str}|{risk99_values_str}|{str(avg_var95)}|{str(avg_var99)}&chm=o,0066FF,0,-1,2|o,FF6600,1,-1,2&chds=a&chs=600x300&chxt=x,y&chxl=0:|{selected_dates_str}&chxs=0,000000,11.5,90&chdl=Risk+95%|Risk+99%|Avg+95%|Avg+99%&chco=FF0000,0000FF"
					# H,FF6600,0,{avg_var99},600|H,FF6600,0,{avg_var95},600
					# img_url = f"https://chart.googleapis.com/chart?cht=lc&chd=t:{risk95_values_str}|{risk99_values_str}|&chm=o,0066FF,0,-1,2|o,FF6600,1,-1,2&chs=600x300&chxt=x,y&chxl=0:|{selected_dates_str}&chxs=0,000000,11.5,90&chdl=Risk+95%|Risk+99%|Avg+95%|Avg+99%&chco=FF0000,0000FF"
					# img_url = f"https://chart.googleapis.com/chart?cht=lc&chs=600x300&chd=t:{risk95_values_str}|{risk99_values_str}|{str(avg_var95)}|{str(avg_var99)}&chm=o,0066FF,0,-1,2|o,FF6600,1,-1,2&chxt=x,y&chxl=0:|{selected_dates_str}&chxs=0,000000,11.5,90&chdl=Risk+95%|Risk+99%&chco=FF0000,0000FF"
					# img_url = f"https://quickchart.io/chart?c={type:'line',data:{labels:[{selected_dates}],datasets:[{label:'Risk 95%',data:[{risk95_values}],fill:false,borderColor:'red'},{label:'Risk 99%',data:[{risk99_values}],fill:false,borderColor:'blue'},{label:'Average 95%',data:[{avg_var95}],fill:false,borderColor:'orange',borderDash:[10,5]},{label:'Average 99%',data:[{avg_var99}],fill:false,borderColor:'green',borderDash:[10,5]}]},options:{scales:{yAxes:[{ticks:{beginAtZero:true}}]},title:{display:true,text:'Risk Analysis'},elements:{line:{tension:0}}}}&width=600&height=300"
					# https://quickchart.io/chart-maker/edit/zm-c3786dd9-00d3-4328-a5ac-7eefe38ac123
			# display results using a new template results.htm
			return doRender('results.htm', {'result_list': result_list, 'total_pnl': total_pnl, 'avg_var95': avg_var95, 'avg_var99': avg_var99, 'img_url': img_url})
			
	return 'Should not ever get here'
	
# # Defines a POST supporting initialize route
# @app.route('/initialize', methods=['POST'])
# def initializeHandler():
# 	if request.method == 'POST':
# 		s = request.form.get('select_service')
# 		r = request.form.get('num_r')
# 		# Check if input for R is within 0-19 to avoid AWS academy account deactivation
# 		if int(r) < 0 or int(r) > 19:
# 			return doRender('index.htm', {'note': 'Please enter a value between 0 and 19'})
# 		else:
# 			return 'initialize and pass values to other functions'

# 	return 'Should not ever get here'

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

