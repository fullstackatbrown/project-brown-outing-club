import random

from sqlalchemy import desc, and_, false, true
from sqlalchemy.sql import select, update, insert
from decimal import Decimal
from .models import *

userweight_floor = Decimal(0.5)
userweight_roof = Decimal(5.0)


def gotspot(user):
	if user.weight - Decimal(0.05) < userweight_floor:
		user.weight = userweight_floor
	else:
		user.weight = user.weight - Decimal(0.05)


# ACTION REQUIRED:
# def send_email(user):
# fill in with code to send an email given a user as input (to be used in run_lottery and WaitlistView's award_spot method)

# returns a list of the user emails that won the lottery for the trip associated w input id
def run_lottery(id):
	# get responses to the trip id inputted
	get_trip = select([Trip.car_cap, Trip.noncar_cap]).where(Trip.id == id)
	car_cap, noncar_cap = db.session.execute(get_trip).fetchone()
	print(car_cap, noncar_cap)

	# Get winners from car cap
	user_fields = [Response.user_email, Response.id]
	get_cars = select(user_fields).where(and_(Response.trip_id == id, Response.car is true()))
	get_cars.order_by(desc(User.weight)).limit(car_cap)
	car_winners = db.session.execute(get_cars).fetchall()
	for user in car_winners:
		db.session.query(Response).filter(Response.id == user.id).update({Response.lottery_slot: True})

	# Get remaining winners
	get_others = select(user_fields).where(and_(Response.trip_id == id, Response.lottery_slot == false()))
	get_others.order_by(desc(User.weight)).limit(noncar_cap)
	other_winners = db.session.execute(get_others).fetchall()

	for user in other_winners:
		db.session.query(Response).filter(Response.id == user.id).update({Response.lottery_slot: true()})

	# return winners
	print("Winners: ", car_winners + other_winners)
	return car_winners + other_winners,


# updates user weights based on if they declined or did not show
def update_user_weights(behavior, user_email):
	# Johnny note: commented out for now, lets just do random to be safe and fair

	# get user weight from user email
	# get_user_text = select([User.weight]).where(User.email == user_email)
	# current_weight = db.session.execute(get_user_text).fetchone()
	# user_weight = current_weight[0]

	# adjust weight according to behavior
	# if behavior == "Declined":
	# 	user_weight *= Decimal(0.9)
	# elif behavior == "No Response":
	# 	user_weight *= Decimal(0.8)
	# elif behavior == "Confirmed":
	# 	user_weight *= Decimal(0.95)
	# add did not get result

	# ensure weight doesn't drop to below 0.25
	# if user_weight < userweight_floor:
	# 	user_weight = userweight_floor
	# if user_weight > userweight_roof:
	# 	user_weight = userweight_roof

	db.session.query(User).update({User.weight: random.uniform(0, 1)})
