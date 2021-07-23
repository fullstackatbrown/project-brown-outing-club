import random

from flask import abort, Blueprint, render_template, request, redirect, session, url_for, flash, \
	current_app
from sqlalchemy import and_, desc, false, true, asc
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
	upcoming_trips = Trip.query.filter(Trip.signup_deadline >= func.current_date()). \
		order_by(asc(Trip.signup_deadline)).all()
	past_trips = Trip.query.filter(Trip.signup_deadline < func.current_date()).order_by(asc(Trip.signup_deadline)).all()

	# checks if current user email is in adminclearance table
	is_admin, logged_in = authenticated()
	return render_template('index.html', upcoming_trips=upcoming_trips, past_trips=past_trips, is_admin=is_admin,
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


@bp.route('/respond/<response_id>')
def respond(response_id):
	response = get_response(response_id)
	is_admin, logged_in = authenticated()
	if response["user_behavior"] != "NoResponse":
		return redirect(url_for('trips.dashboard'))
	return render_template('respond.html', id=response_id, trip=get_trip(response["trip_id"]), is_admin=is_admin,
	                       logged_in=logged_in)


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
	current_email = session.get('profile').get('email')
	response = db.session.query(Response).filter(Response.trip_id == id).filter(
		Response.user_email == current_email).first()
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
# called within respond.html
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
	db.session.execute(update(Response).where(Response.id == id).values(user_behavior="Declined"))
	db.session.commit()

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
		Response.car == true(),
		Response.trip_id == trip_id
	))
	car_winners = db.session.execute(get_cars).fetchall()
	get_wait_list = db.session.query(Response.user_email, Response.id, Response.lottery_slot). \
		join(User, User.email == Response.user_email). \
		filter(Response.lottery_slot == false(), Response.trip_id == trip_id)
	if (car_cap or 0) > len(car_winners):
		get_wait_list = get_wait_list.order_by(desc(Response.car))
	get_wait_list = get_wait_list.order_by(desc(User.weight))

	# Check that there was a user on the wait list, return immediately if not
	wait_list_winner = db.session.execute(get_wait_list).fetchone()
	if wait_list_winner is None:
		return redirect(url_for('trips.dashboard'))
	winner_email, response_id, _ = wait_list_winner

	# update response from user to reflect getting a lottery slot
	wait_update = update(Response).where(Response.id == response_id).values(lottery_slot=True)
	db.session.execute(wait_update)
	db.session.commit()

	# email new winner
	emails.mail_individual(winner_email, trip_name, response_id)
	return redirect(url_for('trips.dashboard'))

# if __name__ == '__main__':
#     app.run()
