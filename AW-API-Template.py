#!/usr/bin/env python

import logging
import os 
import requests
import smtplib
import sys
from email.mime.text import MIMEText

# Get Script Name
scriptName =  os.path.basename(sys.argv[0])

# Variables
consoleURL = ''
b64EncodedAuth = ''
tenantCode = ''
lookupLimit = '10000'
apiFolder = ''
logFileFullPath = os.path.join(apiFolder, os.path.basename(sys.argv[0]) + '.log')
mailServer = ''
mailFrom = ''
mailTo = ''

# Configure Logging
logging.basicConfig(filename=logFileFullPath,level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s',filemode='w')

# Send email		
def sendEmail(statusMessage):
	# Open the logFile as email contents
	logFile = open(logFileFullPath, 'rb')
	# Create a text/plain message
	msg = MIMEText(logFile.read())
	logFile.close()
	# Email From, To & Subject
	msg['From'] = mailFrom
	msg['To'] = mailTo
	msg['Subject'] = scriptName + ": " + statusMessage
	# Send the email
	s = smtplib.SMTP(mailServer)
	s.sendmail(mailFrom, mailTo, msg.as_string())
	s.quit()
	# Quit the script once sent
	sys.exit(0)

# Try to make the API call
try:
	# Log we're starting
	logging.info('-------- Getting All Device Information --------')
	# API call, pulling in all Employee Owned devices from the OG "All Peoples Devices"
	awTest = requests.get(consoleURL + "/API/v1/mdm/devices/search?pagesize=" + lookupLimit, headers={"Authorization": "Basic " + b64EncodedAuth, "aw-tenant-code": tenantCode,"Accept": "application/json"}, timeout=30)
	# If the above gives a 4XX or 5XX error
	awTest.raise_for_status()
	# Get the JSON from the above
	deviceDetails = awTest.json()
	# Pull in the "Devices' dict only
	deviceDetails = deviceDetails['Devices']
	# For each device in deviceDetails
	for device in deviceDetails:
		# Log each devices one by one
		logging.info(device)
# If the API call fails, report error as e
except requests.exceptions.RequestException, e:
	# Status message to use as subject for sendMail funtion
	statusMessage = 'Get request failed with %s' % e
	# Advise that no devices are to be deleted
	logging.error('-------- ' + statusMessage + ' --------')
	sendEmail(statusMessage)

# Status message to use as subject for sendMail funtion
statusMessage = 'Retrieved information for %s devices' % len(deviceDetails)
# Advise that no devices are to be deleted
logging.info('-------- ' + statusMessage + ' --------')
sendEmail(statusMessage)
