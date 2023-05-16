# import required libraries and functions from other python files

import os
import logging
from flask import Flask, request, render_template
import time

from functions import fetch_stock_data, find_signals, calculate, make_img_url, averaging_lambda_results, uselambda, launchec2, uselambda_parallel, useec2_parallel, useec2, read_list_from_s3, write_list_to_s3
# from globals import s,r
os.environ['AWS_SHARED_CREDENTIALS_FILE']='./cred' 

import boto3

app = Flask(__name__)

# define a function to render pages while taking in parameters
def doRender(tname, values={}):
	if not os.path.isfile( os.path.join(os.getcwd(), 'templates/'+tname) ): #No such file
		return render_template('index.htm')
	return render_template(tname, **values) 

@app.route('/hello')
# Keep a Hello World message to show that at least something is working
def hello():
    return 'Hello World!'


# Defines a POST supporting calculate route
@app.route('/calculate', methods=['POST'])
def calculateHandler():
	if request.method == 'POST':

		h = int(request.form.get('num_h')) # history
		d = int(request.form.get('num_d')) # shots
		t = request.form.get('select_signal') # signal type
		p = int(request.form.get('num_p')) # time horizon

		# Check if inputs are correct
		# note = ''
		note1 = ''
		note2 = ''
		note3 = ''

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
			# data = fetch_stock_data()
			# find_signals(data)
			if s == 'lambda':
				starttime = time.time()
				results = uselambda_parallel(data, h, d, t, p, r)
				runtime = time.time() - starttime
				cost = runtime * float(r) * 0.0000000021 * 100
				result_list, total_pnl, avg_var95, avg_var99 = averaging_lambda_results(results)
				# if result_list:
				# 	img_url = make_img_url(result_list, avg_var95, avg_var99)

			elif s == 'ec2':
				starttime = time.time()
				results = useec2_parallel(data, h, d, t, p, public_dns_names)
				runtime = time.time() - starttime
				cost = runtime * float(r) * 0.0000000021 * 100
				result_list, total_pnl, avg_var95, avg_var99 = averaging_lambda_results(results)
				# if result_list:
				# 	img_url = make_img_url(result_list, avg_var95, avg_var99)
			
			# Update the audit list
			s3 = boto3.client('s3')
			# Read the existing list from S3
			bucket_name = 'audit-page-bucket'
			file_name = 'audit.json'
			existing_list = read_list_from_s3(bucket_name, file_name)
			# Append new values to the list
			new_values = [s, r, h, d, t, p, avg_var95, avg_var99, total_pnl, runtime, cost]
			existing_list.append(new_values)
			# print(existing_list)
			# Write the updated list back to S3
			write_list_to_s3(bucket_name, file_name, existing_list)


			# display results using a new template results.htm
			img_url = make_img_url(result_list, avg_var95, avg_var99)
			return doRender('results.htm', {'result_list': result_list, 'total_pnl': total_pnl, 'avg_var95': avg_var95, 'avg_var99': avg_var99, 'img_url': img_url})
			
	return 'Should not ever get here'
	
# Defines a POST supporting initialize route
@app.route('/initialize', methods=['POST'])
def initializeHandler():
	if request.method == 'POST':
		global s, r
		global data
		s = request.form.get('select_service')
		r = request.form.get('num_r')
		# Check if input for R is within 0-19 to avoid AWS academy account deactivation
		if int(r) < 0 or int(r) > 19:
			return doRender('index.htm', {'note': 'Please enter a value between 0 and 19'})
		else:
			data = fetch_stock_data()
			find_signals(data)
			if s == 'lambda':
				dummyresults = uselambda_parallel(data, 30, 100, 'Buy', 20, r)
			if s == 'ec2':
				global public_dns_names
				public_dns_names = launchec2(r)
				time.sleep(150)
			return doRender('index.htm', {'initnote': f"Initialized {r} {s} resources successfully. Please proceed."})

			return '', 204

# Defines a POST supporting audit route
@app.route('/audit', methods=['POST'])
def auditHandler():
	if request.method == 'POST':
		s3 = boto3.client('s3')
		# Read the existing list from S3
		bucket_name = 'audit-page-bucket'
		file_name = 'audit.json'
		audit_list = read_list_from_s3(bucket_name, file_name)
		return doRender('audit.htm', {'audit_list': audit_list})
	
# Defines a POST supporting terminate route
@app.route('/terminate1', methods=['POST'])
def terminate1():
	# Initialize the EC2 client
	ec2 = boto3.client('ec2', region_name='us-east-1')
	# Get the IDs of running EC2 instances
	# filters = [{'Name': 'instance-state-name', 'Values': ['running']}]
	running_instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
	instance_ids = [i['InstanceId'] for r in running_instances['Reservations'] for i in r['Instances']]
	# Check if running instance_ids exist and terminate if they do
	if instance_ids:
		ec2.terminate_instances(InstanceIds=instance_ids)
		terminote = 'Instances have been terminated'
	else:
		terminote = 'No instances to terminate'
	
	return doRender('results.htm', {'terminote': terminote})

@app.route('/terminate2', methods=['POST'])
def terminate2():
	# Initialize the EC2 client
	ec2 = boto3.client('ec2', region_name='us-east-1')
	# Get the IDs of running EC2 instances
	# filters = [{'Name': 'instance-state-name', 'Values': ['running']}]
	running_instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
	instance_ids = [i['InstanceId'] for r in running_instances['Reservations'] for i in r['Instances']]
	# Check if running instance_ids exist and terminate if they do
	if instance_ids:
		ec2.terminate_instances(InstanceIds=instance_ids)
		terminote = 'Instances have been terminated'
	else:
		terminote = 'No instances to terminate'
	
	return doRender('index.htm', {'terminote': terminote})

	# return 'Should not ever get here'

# Defines a route to fetch static setup file while avoiding cache
# @app.route('/cacheavoid/<name>')
# def cacheavoid(name):
#     # file exists?
#     if not os.path.isfile( os.path.join(os.getcwd(), 'static/'+name) ): 
#         return ( 'No such file ' + os.path.join(os.getcwd(), 'static/'+name) )
#     f = open ( os.path.join(os.getcwd(), 'static/'+name) )
#     contents = f.read()
#     f.close()
#     return contents # far from the best HTTP way to do this

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

