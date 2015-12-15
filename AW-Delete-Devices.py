#!/usr/bin/env python
####################################################################################################
#
# More information: https://macmule.com/2015/12/15/deleting-unenrolled-devices-via-the-airwatch-api
#
# GitRepo: https://github.com/macmule/AW-API-Scripts/
#
# License: http://macmule.com/license/
#
####################################################################################################

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
ownershipLevel = ''
locationGroupID = ''
deleteDeviceList = []

# Configure Logging
logging.basicConfig(filename=logFileFullPath,level=logging.DEBUG,format='%(asctime)s %(message)s',filemode='w')

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
	logging.info('-------- Started Checking for Employee Owned Devices to Delete --------')
	# API call, pulling in device information
	awTest = requests.get("https://" + consoleURL + "/API/v1/mdm/devices/search?ownership=" + ownershipLevel + "&lgid=" + locationGroupID + "&pagesize=" + lookupLimit, headers={"Authorization": "Basic " + b64EncodedAuth, "aw-tenant-code": tenantCode,"Accept": "application/json"}, timeout=30)
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
	logging.error('-------- ' + statusMessage + ' --------')
	sendEmail(statusMessage)

# For each device in the deviceDetails list
for device in deviceDetails:
	# If the EnrollmentStatus is not Enrolled (so: DeviceWipePending, EnrollmentInProgress, EnterpriseWipePending or Unenrolled).
	 if 'Enrolled' not in device['EnrollmentStatus']:
		# Grab the devices SerialNumber, EnrollmentStatus, DeviceFriendlyname, UserName & LastSeen date
		toDelete = [ device['Id']['Value'], device['SerialNumber'], device['EnrollmentStatus'], device['DeviceFriendlyName'], device['UserName'], device['LastSeen']]
		# For each device, log the above
		logging.info(toDelete)
		# Append to list
		deleteDeviceList.append(toDelete)

# Comment out this when live
deleteDeviceList=[]

# If nothing found to delete
if not len(deleteDeviceList):
	# Status message to use as subject for sendMail function
	statusMessage = 'No Devices to be deleted'
	# Advise that no devices are to be deleted
	logging.info('-------- ' + statusMessage + ' --------')
	sendEmail(statusMessage)
# If deleteDeviceList has entries
else:
	# Advise how many Devices to be deleted
	logging.info('-------- Devices to be deleted: %s --------' % len(deleteDeviceList))
	# For each device in deleteDeviceList
	for device in deleteDeviceList:
		# Get the devices ID as a string for concatenation
		deviceID = str(device[0])
		# Try to make the API call
		try:
			# Delete device, using SerialNumber as the identifier, this will log so no need for a logging action
			deleteDevice = requests.delete("https://" + consoleURL + "/API/v1/mdm/devices/" + deviceID, headers={"Authorization": "Basic " + b64EncodedAuth, "aw-tenant-code": tenantCode,"Accept": "application/json"})
			# If the above gives a 4XX or 5XX error
			deleteDevice.raise_for_status()
		# If the API call fails
		except requests.exceptions.RequestException, e:
			# Status message to use as subject for sendMail funtion
			statusMessage = 'Failed Deletion Attempt: %s' % e
			# Advise that no devices are to be deleted
			logging.error('-------- ' + statusMessage + ' --------')
			sendEmail(statusMessage)

# Status message to use as subject for sendMail function
statusMessage = 'Devices Deleted = %s ' % len(deleteDeviceList)
# Advise that no devices are to be deleted
logging.info('-------- ' + statusMessage + ' --------')
sendEmail(statusMessage)
