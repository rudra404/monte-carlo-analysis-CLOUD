# import required libraries
import os
import logging
from flask import Flask, request, render_template, session
import time
import datetime
# import functions from functions.py for improved readability
from functions import fetch_stock_data, find_signals, make_img_url, averaging_results, launchec2, uselambda_parallel, useec2_parallel, read_list_from_s3, write_list_to_s3
# Ensuring correct credentials are picked up by boto3 by pointing before importing
os.environ['AWS_SHARED_CREDENTIALS_FILE']='./cred' 
import boto3

# Start a flask app with secret_key for session variables storage
app = Flask(__name__)
app.secret_key = 'cloudcomputingisthebest!!1!'

# Define a function to render pages while taking in parameters
def doRender(tname, values={}):
	if not os.path.isfile( os.path.join(os.getcwd(), 'templates/'+tname) ): # No such file
		return render_template('index.htm') # Render homepage
	return render_template(tname, **values) 

@app.route('/hello')
# Keep a Hello World message to show that at least something is working
def hello():
    return 'Hello World!'


# Define a POST supporting calculate app route
@app.route('/calculate', methods=['POST'])
def calculateHandler():
	if request.method == 'POST':
		s = session['s'] # Get from session variable
		r = session['r'] # Get from session variable

		h = int(request.form.get('num_h')) # History
		d = int(request.form.get('num_d')) # Shots
		t = request.form.get('select_signal') # Signal type
		p = int(request.form.get('num_p')) # Time horizon

		# Check if inputs are correct - some sort of error handling
		note1 = ''
		note2 = ''
		note3 = ''

		if int(h) < 1 or int(h) > 1095: # Max data fetched from yfinance
			note1 = 'Please enter a value between 1 and 1095'
		if int(d) < 0:
			note2 = 'Please enter a positive value'
		if int(p) < 0:
			note3 = 'Please enter a positive value'
			
		if note1 or note2 or note3:
			return doRender('index.htm', {'note1': note1, 'note2': note2, 'note3': note3})
		else:
			# For lambda as chosen service
			if s == 'lambda':
				starttime = time.time()
				results = uselambda_parallel(data, h, d, t, p, r) # Call function to use lambda in parallel
				runtime = time.time() - starttime
				cost = runtime * float(r) * 0.0000000021 * 100 # Calculate costs based on runtime and number of resources
				result_list, total_pnl, avg_var95, avg_var99 = averaging_results(results) # Get the average results from all runs

			# For EC2 as chosen service
			elif s == 'ec2':
				starttime = session['ec2starttime']
				results = useec2_parallel(data, h, d, t, p, public_dns_names) # Call function to use EC2 in parallel
				runtime = time.time() - starttime
				cost = runtime * float(r) * 0.0116 * (1/3600) # Calculate costs based on runtime and number of resources
				result_list, total_pnl, avg_var95, avg_var99 = averaging_results(results) # Get the average results from all runs
			
			# Update the audit list after simulations are finished and results are obtained
			s3 = boto3.client('s3')
			# Read the existing list from S3
			bucket_name = 'audit-page-bucket'
			file_name = 'audit.json'
			existing_list = read_list_from_s3(bucket_name, file_name)
			# Append new values to the list
			timestampnow = datetime.datetime.now().strftime("%d/%m/%y %H:%M")
			new_values = [timestampnow, s, r, h, d, t, p, avg_var95, avg_var99, total_pnl, runtime, cost]
			existing_list.append(new_values)
			# Write the updated list back to S3
			write_list_to_s3(bucket_name, file_name, existing_list)

			# Display results using the template 'results.htm' and send it an image url generated
			img_url = make_img_url(result_list, avg_var95, avg_var99)
			return doRender('results.htm', {'result_list': result_list, 'total_pnl': total_pnl, 'avg_var95': avg_var95, 'avg_var99': avg_var99, 'img_url': img_url})
			
	return 'Should not ever get here'
	
# Define a POST supporting initialize app route
@app.route('/initialize', methods=['POST'])
def initializeHandler():
	if request.method == 'POST':
		global data # to be used again upon pre-processing
		# Store input values as session variables - to be used again too
		s = request.form.get('select_service')
		session['s'] = s
		r = request.form.get('num_r')
		session['r'] = r
		# Check if input for R is within 0-19 to avoid AWS academy account deactivation
		if int(r) < 0 or int(r) > 19:
			return doRender('index.htm', {'note': 'Please enter a value between 0 and 19'})
		else:
			# Get NFLX data from yfinance and add trading signals based on chosen strategy
			data = fetch_stock_data()
			find_signals(data)
			# Initialization steps for lambda - just send it some dummy values to 'r' threads to avoid a cold-start
			if s == 'lambda':
				dummyresults = uselambda_parallel(data, 30, 100, 'Buy', 20, r)
			# Initialization steps for EC2
			if s == 'ec2':
				# First check for intialized instances already running
				ec2 = boto3.client('ec2', region_name='us-east-1')
				running_instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
				instance_ids = [i['InstanceId'] for instance in running_instances['Reservations'] for i in instance['Instances']]
				global public_dns_names
				public_dns_names = []
				# If exact number of requested running instance_ids exist, use them to avoid re-initialization
				if instance_ids and (len(instance_ids) == int(r)):
					public_dns_names_list = session['public_dns_names']
					public_dns_names = public_dns_names_list[0]
				else:
					public_dns_names = launchec2(r) # Otherwise launch 'r' new instances
					time.sleep(150) # Wait for the instances to be launched and configured with apache, running our python script
			return doRender('index.htm', {'initnote': f"Initialized {r} {s} resources successfully. Please proceed."}) # Confirmation message pop-up

			return '', 204 # Success code

# Define a POST supporting audit app route
@app.route('/audit', methods=['POST'])
def auditHandler():
	if request.method == 'POST':
		s3 = boto3.client('s3')
		# Read the existing list from S3
		bucket_name = 'audit-page-bucket'
		file_name = 'audit.json'
		audit_list = read_list_from_s3(bucket_name, file_name)
		return doRender('audit.htm', {'audit_list': audit_list}) # Render the audit log page with updated values from bucket
	
# Define POST supporting terminate app routes - twice because we have this button on 2 different pages and need to render separately
@app.route('/terminate1', methods=['POST'])
def terminate1():
	# Initialize the EC2 client
	ec2 = boto3.client('ec2', region_name='us-east-1')
	# Get the IDs of running EC2 instances
	running_instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
	instance_ids = [i['InstanceId'] for instance in running_instances['Reservations'] for i in instance['Instances']]
	# Check if running instance_ids exist and terminate if they do with a confirmation message
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
	running_instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
	instance_ids = [i['InstanceId'] for instance in running_instances['Reservations'] for i in instance['Instances']]
	# Check if running instance_ids exist and terminate if they do with a confirmation message
	if instance_ids:
		ec2.terminate_instances(InstanceIds=instance_ids)
		terminote = 'Instances have been terminated'
	else:
		terminote = 'No instances to terminate'
	
	return doRender('index.htm', {'terminote': terminote})

# Catch all other page requests - doRender checks if a page is available (shows it) or not (index)
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
    # On GAE, endpoints (e.g. /) would be called as 'gunicorn -b :$PORT index:app' - host is localhost; port is 8080; this file is index (.py)
    app.run(host='127.0.0.1', port=8080, debug=True)

