import os
import sys
import pytest
from dotenv import load_dotenv
from pathlib import Path
from tests.testing_utils import *

# Connect this directory to outer scope
this_path = os.path.dirname(os.path.relpath(__file__))
sys.path.insert(0, this_path + '/../')

from boc import *


@pytest.fixture
def client():
	dotenv_path = Path('../.env')
	load_dotenv(dotenv_path=dotenv_path)
	test_app = create_app(config.TestConfig())
	db.drop_all()
	db.create_all()
	# Create a test client using the Flask application configured for testing
	with test_app.test_client() as client:
		# Establish an application context
		with test_app.app_context():
			yield client


def test_landing(client):
	response = client.get('/')
	assert b'Login' in response.data
	login(client)
	response = client.get('/')
	assert b'Logout' in response.data


def test_sample_trip(client):
	login(client)
	new_trip = Trip(
		id=1, name="Adirondack Hiking", description="people literally are going hiking",
		departure_date=func.current_date(), boc_leaders="Anna, Clara, Ethan, & Lucas",
		departure_location="Adirondacks", departure_time=func.current_time(),
		return_date=func.current_date(), return_time=func.current_time(),
		car_cap=10,
		signup_deadline=func.current_date(), price=9.99, non_car_cap=10)
	db.session.add(new_trip)
	db.session.commit()
	trip_page = client.get('/trip/1').data
	assert b"Adirondack Hiking" in trip_page
	assert b"people literally are going hiking" in trip_page


def test_confirm_attendance(client):
	trip_id = create_trip(4, 8)
	auth_token, email = create_users(1)[0]
	response_id = create_response(client, trip_id, auth_token, email)
	trip_page = client.get('/trip/' + str(trip_id)).data
	assert b'<h6 class="content">1</h6>' in trip_page
	assert b'12' in trip_page
	initial_weight = User.query.filter_by(email=email).one().weight
	assert Response.query.filter_by(user_behavior='NoResponse').count() == 1
	run_lottery(trip_id)
	assert initial_weight - 5 == User.query.filter_by(email=email).one().weight
	client.post('/confirm_attendance/' + response_id)
	assert Response.query.filter_by(user_behavior='Confirmed').count() == 1
	assert initial_weight == User.query.filter_by(email=email).one().weight
	assert Response.query.filter_by(user_behavior='NoResponse').count() == 0


def test_decline_attendance(client):
	login_admin(client)
	trip_id = create_trip(8, 5)
	(auth_token1, email1), (auth_token2, email2) = create_users(2)
	response_id1 = create_response(client, trip_id, auth_token1, email1)
	response_id2 = create_response(client, trip_id, auth_token2, email2)
	trip_page = client.get('/trip/' + str(trip_id)).data
	assert b'<h6 class="content">2</h6>' in trip_page
	assert b'13' in trip_page
	assert Response.query.filter_by(user_behavior='NoResponse').count() == 2
	initial_weight_confirm = User.query.filter_by(email=email1).one().weight
	initial_weight_decline = User.query.filter_by(email=email2).one().weight
	run_lottery(trip_id)
	assert initial_weight_confirm - 5 == User.query.filter_by(email=email1).one().weight
	assert initial_weight_decline - 5 == User.query.filter_by(email=email2).one().weight
	client.post('/confirm_attendance/' + response_id1)
	client.post('/decline_attendance/' + response_id2)
	assert Response.query.filter_by(user_behavior='Confirmed').count() == 1
	assert Response.query.filter_by(user_behavior='Declined').count() == 1
	assert Response.query.filter_by(user_behavior='NoResponse').count() == 0
	assert initial_weight_confirm == User.query.filter_by(email=email1).one().weight
	assert initial_weight_decline - 2 == User.query.filter_by(email=email2).one().weight


def test_reset_weights(client):
	trip_id = create_trip(4, 8)
	users = create_users(4)
	for auth_token, email in users:
		create_response(client, trip_id, auth_token, email)
		assert abs(User.query.filter_by(email=email).one().weight) < 1
	run_lottery(trip_id)
	for auth_token, email in users:
		assert abs(User.query.filter_by(email=email).one().weight) > 1
	login_admin(client)
	client.post('/admin/user/reset')
	for auth_token, email in users:
		assert abs(User.query.filter_by(email=email).one().weight) < 1


def test_not_enough_spots(client):
	trip_id = create_trip(2, 1)
	users = create_users(6)
	for auth_token, email in users:
		create_response(client, trip_id, auth_token, email)
	assert Response.query.filter_by(lottery_slot=True).count() == 0
	run_lottery(trip_id)
	assert Response.query.filter_by(lottery_slot=True).count() == 1


def test_too_many_spots(client):
	trip_id = create_trip(200, 100)
	users = create_users(20)
	for auth_token, email in users:
		create_response(client, trip_id, auth_token, email)
	assert Response.query.filter_by(lottery_slot=True).count() == 0
	run_lottery(trip_id)
	assert Response.query.filter_by(lottery_slot=True).count() == 20


def test_car_spots(client):
	trip_id = create_trip(2, 1)
	users = create_users(5)
	for i, (auth_token, email) in enumerate(users):
		create_response(client, trip_id, auth_token, email, True if i < 2 else False)
	assert Response.query.filter_by(lottery_slot=True).count() == 0
	run_lottery(trip_id)
	assert Response.query.filter_by(lottery_slot=True).count() == 3
	assert Response.query.filter(Response.lottery_slot == True, Response.car == True).count() == 2


def test_car_spots_only(client):
	trip_id = create_trip(2, 0)
	users = create_users(4)
	for auth_token, email in users:
		create_response(client, trip_id, auth_token, email, False)
	assert Response.query.filter_by(lottery_slot=True).count() == 0
	run_lottery(trip_id)
	assert Response.query.filter_by(lottery_slot=True).count() == 0


def test_cars_only(client):
	trip_id = create_trip(0, 3)
	users = create_users(3)
	for auth_token, email in users:
		create_response(client, trip_id, auth_token, email, True)
	assert Response.query.filter_by(lottery_slot=True).count() == 0
	run_lottery(trip_id)
	assert Response.query.filter_by(lottery_slot=True).count() == 3


def test_lottery_withdraw(client):
	trip_id = create_trip(3, 3)
	users = create_users(3)
	for auth_token, email in users:
		create_response(client, trip_id, auth_token, email)
	assert Response.query.filter_by(lottery_slot=True).count() == 0
	with client.session_transaction() as transaction:
		transaction['profile'] = {'user_id': users[0][0], 'email': users[0][1]}
	client.post("/lottery_withdraw/" + str(trip_id))
	run_lottery(trip_id)
	assert Response.query.filter_by(lottery_slot=True).count() == 2

# def test_integration_1(client):
#     # create trip with normal cap 10 and car cap 10, id = 1
#     create_trip(10, 10)
#     # create 25 new accounts without cars
#     trips.dummy_users(25)
# 	# create 25 new accounts with cars
# 	trips.dummy_users(25, True)

#     # sign up all 50 for the trip w id 1
#     users = db.session.query(User)
#     for user in users:
#         db.session.add(Response(trip_id=1, user_email = user.email))
#     db.session.commit()
#     assert db.session.query(Response).count() == 50

# 	# run lottery, only 20 should be awarded spot
#     lottery.runlottery(1)
# 	assert db.session.query(Response).filter_by(trip_id = 1).filter_by(lottery_slot = True).filter_by(car = True).count() == 10

# 	first_no_car_winners = db.session.query(Response).filter_by(trip_id = 1).filter_by(lottery_slot = True).filter_by(car = False)
# 	assert first_no_car_winners.count() == 10

# 	# track all the unique emails of the first no car winners
# 	first_no_car_emails = {}
# 	for winners in first_no_car_winners:
# 		first_no_car_emails.add(winners.email)

# 	# create trip with normal cap 20 and car cap 10, id = 2
# 	# total cap is equal to the number of people not rewarded spot in trip 1
# 	# car cap is greater than the number of people with cars who did not get first trip (20 > 15)
# 	create_trip(10, 20)

# 	# sign up all 50 for the trip w id 2
#     users = db.session.query(User)
#     for user in users:
#         db.session.add(Response(trip_id=2, user_email = user.email))
#     db.session.commit()
#     assert db.session.query(Response).count() == 50

# 	lottery.runlottery(2)
# 	assert db.session.query(Response).filter_by(trip_id = 2).filter_by(lottery_slot = True).filter_by(car = True).count() == 20

# 	second_no_car_winners = db.session.query(Response).filter_by(trip_id = 2).filter_by(lottery_slot = True).filter_by(car = False)
# 	assert second_no_car_winners.count() == 10

# 	# check to see no second_no_car_winners are got the first trip also
# 	for winner in second_no_car_winners:
# 		assert winner.email not in first_no_car_emails
