#!/usr/bin/env python
####################################################################################################
#
# More information: https://macmule.com/2015/12/16/retaining-enrolment-user-information-on-airwatch-via-the-api
#
# GitRepo: https://github.com/macmule/AW-API-Scripts/
#
# License: http://macmule.com/license/
#
####################################################################################################

import json
import logging
import os 
import requests
import smtplib
import sys
from email.mime.text import MIMEText

# Get Script Name
scriptName =  os.path.basename(sys.argv[0])

# Variables
consoleURL = 'cn32.airwatchportals.com'
locationGroupID = '6214'
b64EncodedAuth = 'YWlyd2F0Y2hBUEk6bWVkOSxTbGF5ZXI='
tenantCode = '1KADIYMAAAG6A4GACQAA'
lookupLimit = '10000'
apiFolder = '/private/var/log/Airwatch API Logs/'
logFileFullPath = os.path.join(apiFolder, os.path.basename(sys.argv[0]) + '.log')
mailServer = 'mail.pentland.com'
mailFrom = 'airwatch@LS-MAC-API-01.pentland.com'
mailTo = 'ben.toms@pentland.com'

# Configure Logging
logging.basicConfig(filename=logFileFullPath,level=logging.WARNING,format='%(asctime)s %(levelname)s %(message)s',filemode='w')

# Send email on errors		
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

# Try to make the API call
try:
	# Log we're starting
	logging.warning('-------- Getting A List of Devices --------')
	# API call, pulling in details for all devices from the OG specified via locationGroupID
	awTest = requests.get("https://" + consoleURL + "/API/v1/mdm/devices/search?&lgid=" + locationGroupID + "&pagesize=" + lookupLimit, headers={"Authorization": "Basic " + b64EncodedAuth, "aw-tenant-code": tenantCode,"Accept": "application/json"}, timeout=30)
	# If the above gives a 4XX or 5XX error
	awTest.raise_for_status()
	# Get the JSON from the above
	deviceDetails = awTest.json()
	# Pull in the "Devices' dict only
	deviceDetails = deviceDetails['Devices']
# If the API call fails, report error as e
except requests.exceptions.RequestException, e:
	# Status message to use as subject for sendMail funtion
	statusMessage = 'Get request failed with %s' % e
	# Advise that no devices are to be deleted
	logging.error('--------' + statusMessage + '--------')
	sendEmail(statusMessage)

# Log we're starting
logging.warning('-------- Adding Notes to %s Devices --------' % len(deviceDetails))

# For each device in the deviceDetails list
for device in deviceDetails:
	# Get the devices ID as a string for concatenation
	deviceID = str(device['Id']['Value'])
	# Try to get the users ID, this fails if the device is unenrolled.. So we continue
	try:
		# Get the User ID as a string for concatenation
		userID = str(device['UserId']['Id']['Value'])
	# If we fail, then the device is probably not enrolled
	except:
		# Continue with the next iteration of the loop
		continue
	# Try to make the API call
	try:
		# API call, get details of devices enrollmentUser
		awTest = requests.get("https://" + consoleURL + "/API/v1/system/users/" + userID, headers={"Authorization": "Basic " + b64EncodedAuth, "aw-tenant-code": tenantCode, "Accept": "application/json" }, timeout=30)
		# If the above gives a 4XX or 5XX error
		awTest.raise_for_status()
		# Get the JSON from the above
		employeeDetails = awTest.json()
		# Grab the enrollmentUsers UserName, Email, ContactNumber, Mobile Number & CustomAttribute1
		employeeNote = """Username: %s\nEmail: %s\nPhone Number: %s\nMobile Number: %s\nManager: %s""" % (employeeDetails['UserName'], employeeDetails['Email'], employeeDetails['ContactNumber'], employeeDetails['MobileNumber'], employeeDetails['CustomAttribute1'])
		# Create payload for POST
		payload = {"DeviceId": deviceID, "Note": employeeNote}
		# Try to make the API call
		try:
			# API call, post the users information to the devices notes
			#awTest = requests.post("https://" + consoleURL + "/API/v1/mdm/devices/" + deviceID + "/addnote", headers={"Authorization": "Basic " + b64EncodedAuth, "aw-tenant-code": tenantCode, "Content-type": "application/json" }, data=json.dumps(payload))
			# Comment out the below & uncomment above when live
			logging.warning(payload)
			# If the above gives a 4XX or 5XX error
			awTest.raise_for_status()
		# If the API call fails, report error as e
		except requests.exceptions.RequestException, e:
			# Status message to use as subject for sendMail funtion
			statusMessage = 'Post request failed with %s' % e
			# Advise that no devices are to be deleted
			logging.error('-------- ' + statusMessage + ' --------')
			sendEmail(statusMessage)
			# Quit if we error, to stop a loop			
			sys.exit(1)
	# If the API call fails, report error as e
	except requests.exceptions.RequestException, e:
		# Status message to use as subject for sendMail funtion
		statusMessage = 'Get request failed with %s' % e
		# Advise that no devices are to be deleted
		logging.error('-------- ' + statusMessage + ' --------')
		sendEmail(statusMessage)
		
# Advise how many Devices had notes added
logging.warning('-------- Added Notes to %s Devices --------' % len(deviceDetails))
