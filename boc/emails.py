import os

from flask import url_for, current_app
from flask_mail import Mail, Message

from boc import config

mail = None


def init_mail(app):
	global mail
	mail = Mail(app)


def mail_individual(app, email, trip_name, response_id):
	if app.config['TESTING']:
		return
	msg = Message('Lottery Selection', recipients=[email])
	msg.body = (
			'Hey! You have been selected for ' + trip_name +
			'! Please confirm or decline your attendance by clicking on the link below:\n' +
			os.environ['BASE_URL'] + url_for('trips.respond', response_id=response_id))
	mail.send(msg)


def mail_group(app, recipients):
	if app.config['TESTING']:
		return
	with mail.connect() as conn:
		for response in recipients:
			msg = Message('Lottery Selection', recipients=[response.user_email])
			msg.body = (
					'Hey! You have been selected for ' + response.trip.name +
					'! Please confirm or decline your attendance by clicking on the link below:\n' +
					os.environ['BASE_URL'] + url_for('trips.respond', response_id=response.id))
			conn.send(msg)
