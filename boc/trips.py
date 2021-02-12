import os
from flask import Blueprint, Flask, render_template, request, jsonify, redirect, session, url_for, flash, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from sqlalchemy.sql import select, func, text, update
from sqlalchemy import create_engine, Date, cast, and_
from datetime import date
import pymysql
import random
from guid import GUID
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .models import *
from .auth import login_required
from .lottery import update_userweights

bp = Blueprint('trips', __name__)

# dummy_users()

# Serve a template from index
@bp.route('/')
def index():
    #create a landing page w welcome, explanation of purpose, login button
    return render_template('test.html', name="name")


#redirects user to auth0 login
#User: test@brown.edu
#Password: #xzAeGCrTenjR9jt


#dashboard that is the target of redirect from login page
@bp.route('/dashboard')
# @login_required
def dashboard():
    #selects rows where the current date matches or is earlier than the sign up deadline
    #NOTE: current date uses the server clock to fetch the date, so make sure the app is deployed on an Eastern Time Server
    print(current_app.config)
    upcoming_text = select([Trip]).where(Trip.signup_deadline >= func.current_date()).order_by(Trip.signup_deadline)
    print(upcoming_text)
    upcoming_trips = db.session.execute(upcoming_text).fetchall()
    print(upcoming_trips)

    #number of responses to each trip, in the same order as the upcoming trips list
    taken_text = select([Response.trip_id, func.count(Response.user_email)]).group_by(Response.trip_id)
    print(taken_text)
    taken_spots = db.session.execute(taken_text).fetchall()
    print(taken_spots)

    taken = {}
    for trip_id, spot in taken_spots:
        taken[trip_id] = spot

    #checks if current user email is in adminclearance table
    is_admin = False
    logged_in = False
    if session.get('profile') is not None:
        currentuser_email = session.get('profile').get('email')
        is_admin = db.session.query(AdminClearance).filter_by(email = currentuser_email).first() is not None
        logged_in = True
    return render_template('upcoming.html', upcoming_trips = upcoming_trips, taken_spots = taken, is_admin = is_admin, logged_in = logged_in)

@bp.route('/trip/<int:id>')
@login_required
def individual_trip(id, taken_spots = None):
    trip = get_trip(id)
    if (taken_spots is None):
        taken_spots = 0
    signed = False
    #list of trips that have lotteries the user has signed up for
    currentuser_email = session.get('profile').get('email')
    signed_text = select([Response.trip_id]).where(Response.user_email == currentuser_email)
    signed_up = db.session.execute(signed_text).fetchall()
    if ((id,) in signed_up):
        signed = True
    return render_template('trip.html', trip = trip, taken_spots = taken_spots, signed_up = signed)


@bp.route('/confirm/<int:id>')
@login_required
def trip_confirm(id):
    trip = get_trip(id)
    #list of trips that have lotteries the user has signed up for
    return render_template('confirm.html', trip = trip)

#displays past trips
@bp.route('/pasttrips')
def pasttrips():
    #selects rows where the current date is after the sign up deadline
    #NOTE: current date uses the server clock to fetch the date, so make sure the app is deployed on an Eastern Time Server
    past_text = select([Trip]).where(Trip.signup_deadline < func.current_date()).order_by(Trip.signup_deadline.desc())
    past_trips = db.session.execute(past_text).fetchall()

    return render_template('past.html', past_trips = past_trips)

#gets trip object from its id
def get_trip(id):
    trip_text = select([Trip]).where(Trip.id == id)
    trip = db.session.execute(trip_text).fetchone()

    if trip is None:
        abort(404, "Trip doesn't exist.")

    return trip

#page linked with "Enter Lottery" from dashboard, should collect information necessary to create Response row in db using a form
@bp.route('/lotterysignup/<int:id>', methods=['POST'])
@login_required
def lotterysignup(id):
    trip = get_trip(id)

@bp.route('/lotterywithdraw/<id>', methods=['POST'])
@login_required
def lotterywithdraw(id):
    response = db.session.query(Response).filter(Response.trip_id == id).first()
    db.session.delete(response)
    db.session.commit()
    return redirect(url_for('trips.dashboard'))

@bp.route('/adminviewguide')
@login_required
def guide(): 
    # flash("Could not process lottery request", 'error')
    check_clearance = select([AdminClearance]).where(AdminClearance.email == session.get('profile').get('email'))
    if check_clearance is not None:
        return render_template('admin/guide.html')
    else:
        flash("Only authorized users can view", 'error')
        return render_template('upcoming.html')

def get_response(id):
    response_text = select([Response]).where(Response.id == id)
    response = db.session.execute(response_text).fetchone()

    if response is None:
        abort(404, "Response doesn't exist.")
    
    return response

# confirms user attendance for given trip
@bp.route('/confirmattendance/<id>', methods=['POST'])
@login_required
def confirmattendance(id):
    to_update = update(Response).where(Response.id == id).values(user_behavior = "Confirmed")
    db.session.execute(to_update)
    # update user weight for declining
    get_confirmed_email = select([Response.user_email]).where(Response.id == id)
    confirmed_email = db.session.execute(get_confirmed_email).fetchone()[0]
    update_userweights(db, "Confirmed", confirmed_email)

    db.session.commit()
    return redirect(url_for('trips.dashboard'))

@bp.route('/declineattendance/<id>', methods=['POST'])
@login_required
def declineattendance(id):
    # update response to declined
    to_update = update(Response).where(Response.id == id).values(user_behavior = "Declined")
    db.session.execute(to_update)

    declined_response = get_response(id)
    # get row of waitlist to update since there is an open spot for trip w/ same trip id as declined response
    get_waitlist = select([Waitlist]).where(and_(Waitlist.trip_id == declined_response["trip_id"], Waitlist.waitlist_rank == 1, Waitlist.off == False))
    waitlist = db.session.execute(get_waitlist).fetchone()

    # update user weight for declining
    get_declined_email = select([Response.user_email]).where(Response.id == id)
    declined_email = db.session.execute(get_declined_email).fetchone()[0]
    update_userweights(db, "Declined", declined_email)

    # if there are still people waiting for the trip in the waitlist
    if waitlist is not None:
        #remove user from waitlist
        wait_text = update(Waitlist).where(and_(Waitlist.trip_id == declined_response["trip_id"], Waitlist.waitlist_rank == 1, Waitlist.off == False)).values(off = True)
        db.session.execute(wait_text)
        #update response from user to reflect getting a lottery slot
        wait_update = update(Response).where(Response.id == waitlist["response_id"]).values(lottery_slot = True)
        db.session.execute(wait_update)
        #update rest of the waitlist to move their positions up on the waitlist
        db.session.query(Waitlist).filter_by(trip_id=declined_response["trip_id"]).filter_by(off=False).update({Waitlist.waitlist_rank: Waitlist.waitlist_rank-1})
    db.session.commit()
    
    trip = get_trip(declined_response["trip_id"])
    msg = Message('Lottery Selection', recipients = [declined_response["user_email"]])
    msg.body = 'Hey! You have been selected for ' + trip["name"] + '! Please confirm your attendance by clicking on the link below. \n\n' + "http://127.0.0.1:5000" + url_for('confirmattendance', id = declined_response["id"])
    mail.send(msg)
    return redirect(url_for('trips.dashboard'))


# if __name__ == '__main__':
#     app.run()
