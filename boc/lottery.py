import random
from decimal import Decimal

from sqlalchemy import desc, and_, false, true
from sqlalchemy.sql import select

from .models import *


# ACTION REQUIRED:
# def send_email(user):
# fill in with code to send an email given a user as input (to be used in run_lottery and WaitlistView's award_spot method)

# returns a list of the user emails that won the lottery for the trip associated w input id
def run_lottery(id):
	# get responses to the trip id inputted
	get_trip = select([Trip.car_cap, Trip.noncar_cap]).where(Trip.id == id)
	car_cap, noncar_cap = db.session.execute(get_trip).fetchone()
	print(car_cap, noncar_cap)

	# increase all weights before (so that everyone who doesn't get chosen will have higher weights)
	for row in User.query.join(Response, User.email == Response.user_email).filter(Response.trip_id == id):
		row.weight = row.weight + 5.0
	db.session.commit()

	# Get winners from car cap
	user_fields = [Response.user_email, Response.id]
	get_cars = select(user_fields).where(and_(Response.trip_id == id, Response.car is true()))
	get_cars.order_by(desc(User.weight)).limit(car_cap)
	car_winners = db.session.execute(get_cars).fetchall()

	# Get remaining winners
	get_others = select(user_fields).where(and_(Response.trip_id == id, Response.lottery_slot == false()))
	get_others.order_by(desc(User.weight)).limit(noncar_cap)
	other_winners = db.session.execute(get_others).fetchall()

	# Grant spots and return winners to their original weights (these are treated like no response until responded to)
	for user in other_winners + car_winners:
		row = User.query.join(Response, User.email == Response.user_email).filter(Response.id == user.id).first()
		row.weight = row.weight - 10.0
		db.session.query(Response).filter(Response.id == user.id).update({Response.lottery_slot: True})

	# return winners
	print("Winners: ", car_winners + other_winners)
	return car_winners + other_winners,


# updates user weights based on if they declined or did not show
def update_user_weights(behavior, user_email):
	# get user weight from user email
	# TODO: this weight update seems broken (it is broken, fix)
	row = User.query.filter(User.email == user_email).first()
	print("BOOM " + str(User.email) + " " + str(row.weight) + " " + behavior)
	# get_user_text = select([User.weight]).where(User.email == user_email)
	# user_weight = db.session.execute(get_user_text).fetchone()[0]
	# print("Found initial weight of " + str(user_weight) + " " + str(user_email))
	# adjust weight according to behavior
	if behavior == "Declined":
		# print("DECLINING" + str(user_weight + 3.0))
		row.weight += 3.0
	elif behavior == "No Response":
		row.weight -= 0.0
	elif behavior == "Confirmed":
		# print("CONFIRMING" + str(user_weight + 5.0))
		row.weight += 5.0
	# add did not get result

	# ensure weight doesn't drop to below 0.25
	# if user_weight < userweight_floor:
	# 	user_weight = userweight_floor
	# if user_weight > userweight_roof:
	# 	user_weight = userweight_roof
	# db.session.query(User).filterupdate({User.weight: user_weight})
	# db.session.commit()
