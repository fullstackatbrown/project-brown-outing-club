import random

from flask import abort, Blueprint, render_template, request, redirect, session, url_for, flash, \
	current_app
from sqlalchemy import and_, desc, false, true
from sqlalchemy.sql import select, func, update

from . import emails
from .auth import login_required, authenticated
from .lottery import update_user_weights
from .models import *

bp = Blueprint('trips', __name__)

# dashboard that is the target of redirect from login page
@bp.route('/')
# @login_required
def dashboard():
	# selects rows where the current date matches or is earlier than the sign up deadline
	# NOTE: current date uses the server clock to fetch the date, so make sure the app is deployed on an Eastern Time Server
	upcoming_text = select([Trip]).where(Trip.signup_deadline >= func.current_date()).order_by(Trip.signup_deadline)
	upcoming_trips = db.session.execute(upcoming_text).fetchall()

	# number of responses to each trip, in the same order as the upcoming trips list
	taken_text = select([Response.trip_id, func.count(Response.user_email)]).group_by(Response.trip_id)
	taken_spots = db.session.execute(taken_text).fetchall()

	taken = {}
	for trip_id, spot in taken_spots:
		taken[trip_id] = spot

	# checks if current user email is in adminclearance table
	is_admin, logged_in = authenticated()
	return render_template('index.html', upcoming_trips=upcoming_trips, taken_spots=taken, is_admin=is_admin,
						   logged_in=logged_in)


@bp.route('/trip/<int:id>')
@login_required
def individual_trip(id):
	trip = get_trip(id)
	signed_up = False
	# list of trips that have lotteries the user has signed up for
	current_user_email = session.get('profile').get('email')
	query = select([Response.user_email]).where(Response.trip_id == id)
	registrations = db.session.execute(query).fetchall()
	if (current_user_email,) in registrations:
		signed_up = True
	# checks if current user email is in adminclearance table
	is_admin, logged_in = authenticated()
	return render_template('trip.html', trip=trip, taken_spots=0, registrations=registrations, signed_up=signed_up,
						   is_admin=is_admin, logged_in=logged_in)


@bp.route('/confirm/<id>')
def trip_confirm(id):
	response = get_response(id)
	if (response["user_behavior"] != "NoResponse"):
		return redirect(url_for('trips.dashboard'))
	return render_template('confirm.html', id=id, trip=get_trip(response["trip_id"]))


# gets trip object from its id
def get_trip(id):
	trip_text = select([Trip]).where(Trip.id == id)
	trip = db.session.execute(trip_text).fetchone()

	if trip is None:
		abort(404, "Trip doesn't exist.")

	return trip


# page linked with "Enter Lottery" from dashboard, should collect information necessary to create Response row in db using a form
@bp.route('/api/lottery_signup/<int:id>', methods=['POST'])
@bp.route('/lottery_signup/<int:id>', methods=['POST'])
@login_required
def lottery_signup(id):
	new_response = Response(
		trip_id=id, user_email=session.get('profile').get('email'),
		financial_aid=(request.form.get("financial_aid") is not None), car=(request.form.get("car") is not None)
	)
	db.session.add(new_response)
	db.session.commit()
	if request.path.split("/")[1] == "api":
		return new_response.id
	return redirect(url_for('trips.dashboard'))


@bp.route('/lottery_withdraw/<id>', methods=['POST'])
@login_required
def lottery_withdraw(id):
	response = db.session.query(Response).filter(Response.trip_id == id).filter(
		Response.user_email == session.get('profile').get('email')).first()
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
		return render_template('index.html')


def get_response(id):
	response_text = select([Response]).where(Response.id == id)
	response = db.session.execute(response_text).fetchone()

	if response is None:
		abort(404, "Response doesn't exist.")

	return response


# confirms user attendance for given trip
# called within confirm.html
@bp.route('/confirm_attendance/<id>', methods=['POST'])
def confirm_attendance(id):
	to_update = update(Response).where(Response.id == id).values(user_behavior="Confirmed")
	db.session.execute(to_update)
	# update user weight for declining
	get_confirmed_email = select([Response.user_email]).where(Response.id == id)
	confirmed_email = db.session.execute(get_confirmed_email).fetchone()[0]
	update_user_weights("Confirmed", confirmed_email)

	db.session.commit()
	return redirect(url_for('trips.dashboard'))


@bp.route('/decline_attendance/<id>', methods=['POST'])
def decline_attendance(id):
	# update response to declined
	to_update = update(Response).where(Response.id == id).values(user_behavior="Declined")
	db.session.execute(to_update)

	# update user weight for declining
	get_response_info = select([Response.user_email, Response.trip_id]).where(Response.id == id)
	declined_email, trip_id = db.session.execute(get_response_info).fetchone()
	update_user_weights("Declined", declined_email)

	# pick a user, if we dont have enough cars, prioritize a car
	trip_name, car_cap = db.session.execute(select([Trip.name, Trip.car_cap]).where(Trip.id == trip_id)).fetchone()
	# In order to count a car, user must be granted lottery slot and not decline
	get_cars = select([Response.user_email, Response.id]).where(and_(
		Response.lottery_slot == true(),
		Response.user_behavior != 'Declined',
		Response.car == true()))
	car_winners = db.session.execute(get_cars).fetchall()
	get_waitlist = select([Response.user_email, Response.id]).where(Response.lottery_slot == false())
	if car_cap > len(car_winners):
		get_waitlist.order_by(desc(Response.car))
	get_waitlist.order_by(desc(User.weight))

	# Check that there was a user on the waitlist, return immediately if not
	waitlist_winner = db.session.execute(get_waitlist).fetchone()
	if waitlist_winner is None:
		return redirect(url_for('trips.dashboard'))
	winner_email, response_id = waitlist_winner

	# update response from user to reflect getting a lottery slot
	wait_update = update(Response).where(Response.id == response_id).values(lottery_slot=True)
	db.session.execute(wait_update)

	# email new winner
	emails.mail_individual(winner_email, trip_name, response_id)
	return redirect(url_for('trips.dashboard'))

# if __name__ == '__main__':
#     app.run()
