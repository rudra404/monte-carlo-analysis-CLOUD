import os
import logging

from flask import Flask, request, render_template

app = Flask(__name__)

# various Flask explanations available at:  https://flask.palletsprojects.com/en/1.1.x/quickstart/

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
		h = request.form.get('num_h')
		d = request.form.get('num_d')
		t = request.form.get('select_signal')
		p = request.form.get('num_p')

		# Check if inputs are correct
		note1 = ''
		note2 = ''
		note3 = ''
		if int(h) < 1 or int(h) > 1095:
			note1 = 'Please enter a value between 1 and 1095'
		if int(d) < 0:
			note2 = 'Please enter a positive value'
		if int(p) < 0:
			note3 = 'Please enter a positive value'
			
		if note1 or note2 or note3:
			return doRender('index.htm', {'note1': note1, 'note2': note2, 'note3': note3})
		else:
			return 'Calculation stuff here'
			
	return 'Should not ever get here'
	
# Defines a POST supporting initialize route
@app.route('/initialize', methods=['POST'])
def initializeHandler():
	if request.method == 'POST':
		s = request.form.get('select_service')
		r = request.form.get('num_r')
		# Check if input for R is within 3-20
		if int(r) < 3 or int(r) > 20:
			return doRender('index.htm', {'note': 'Please enter a value between 3 and 20'})
		else:
			return 'EC2 stuff here'

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

