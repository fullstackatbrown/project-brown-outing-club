import os
import sys

from flask import url_for, current_app

from boc import config

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def mail_individual(receiver_address, trip_name, response_id):
	if current_app.config['TESTING']:
		return
	mail_content = ('Hey! You have been selected for ' + trip_name +
	                '! Please confirm or decline your attendance by clicking on the link below:\n' +
	                os.environ['BASE_URL'] + url_for('trips.respond', response_id=response_id))
	# The mail addresses and password
	sender_address = current_app.config['MAIL_ADDRESS']
	# Setup the MIME
	message = MIMEMultipart()
	message['From'] = sender_address
	message['To'] = receiver_address
	message['Subject'] = 'BOC Lottery Selection'
	# The body and the attachments for the mail
	message.attach(MIMEText(mail_content, 'plain'))
	# Create SMTP session for sending the mail
	session = smtplib.SMTP(current_app.config['MAIL_SERVER'], 587)  # use gmail with port
	session.starttls()
	print(current_app.config['MAIL_USERNAME'] + " " + current_app.config['MAIL_PASSWORD'] + " " + current_app.config['MAIL_SERVER'], flush=True)
	session.login(current_app.config['MAIL_USERNAME'],
	              current_app.config['MAIL_PASSWORD'])  # login with mail_id and password
	session.sendmail(sender_address, receiver_address, message.as_string())
	session.quit()


def mail_group(app, recipients):
	if app.config['TESTING']:
		return
	for response in recipients:
		mail_individual(response.user_email, response.trip.name, response.id)
