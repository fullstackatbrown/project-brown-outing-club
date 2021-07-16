import random
from decimal import Decimal

from sqlalchemy import desc, and_, false, true
from sqlalchemy.sql import select

from .models import *


# ACTION REQUIRED:
# def send_email(user): Fill in with code to send an email given a user as input (to be used in run_lottery and
# WaitlistView's award_spot method)
# returns a list of the user emails that won the lottery for the trip associated w input id
def run_lottery(id):
	# get responses to the trip id inputted
	car_cap, non_car_cap = db.session.query(Trip.car_cap, Trip.non_car_cap).filter(Trip.id == id).first()

	# increase all weights before (so that everyone who doesn't get chosen will have higher weights)
	for row in User.query.join(Response, User.email == Response.user_email).filter(Response.trip_id == id):
		row.weight = row.weight + 5.0
	db.session.commit()

	# Get winners from car cap
	car_winners = Response.query.join(User, User.email == Response.user_email).filter(
		Response.trip_id == id, Response.lottery_slot == false(), Response.car == true()).order_by(
		desc(User.weight)).limit(car_cap).all()
	print("GOT CAR WINNERS")
	print(len(car_winners))
	for response in car_winners:
		response.lottery_slot = True

	# Get remaining winners
	other_winners = Response.query.join(User, User.email == Response.user_email).filter(
		Response.trip_id == id, Response.lottery_slot == false()).order_by(desc(User.weight)).limit(
		(car_cap or 0) + non_car_cap - len(car_winners)).all()
	for response in other_winners:
		response.lottery_slot = True

	# Grant spots and return winners to their original weights (these are treated like no response until responded to)
	for response in other_winners + car_winners:
		row = User.query.join(Response, User.email == Response.user_email).filter(Response.id == response.id).first()
		row.weight = row.weight - 10.0

	# return winners
	return car_winners + other_winners,


# updates user weights based on if they declined or did not show
def update_user_weights(behavior, user_email):
	row = User.query.filter(User.email == user_email).first()
	if behavior == "Declined":
		row.weight += 3.0
	elif behavior == "No Response":
		row.weight -= 0.0
	elif behavior == "Confirmed":
		row.weight += 5.0
