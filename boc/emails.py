from flask import url_for
from flask_mail import Mail, Message
from . import trips

mail = None

def init_mail(app):
    global mail
    mail = Mail(app)

def mail_individual(email, trip_name, response_id, trip):
    msg = Message('Lottery Selection', recipients = [email])
    msg.body = ('Hey! You have been selected for ' + trip_name + '! Please confirm your attendance by clicking on the link below. \n\n' + 
    "http://127.0.0.1:5000" + url_for('trips.trip_confirm', id = response_id))
    mail.send(msg)

def mail_group(winners, trip):
    with mail.connect() as conn:
        for response in winners:
            msg = Message('Lottery Selection', recipients = [response.user_email])
            msg.body = ('Hey! You have been selected for ' + response.trip.name + '! Please confirm your attendance by clicking on the link below. \n\n' + 
            "http://127.0.0.1:5000" + url_for('trips.trip_confirm', id = response.id))
            conn.send(msg)