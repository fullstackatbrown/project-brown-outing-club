import os
import sys
import pytest
from dotenv import load_dotenv
from pathlib import Path

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


def login(client):
	with client.session_transaction() as session:
		session['profile'] = {
			'user_id': 'auth0|5f3489a68f18aa00689d5333',
			'email': 'test@brown.edu'
		}


def login_admin(client):
	with client.session_transaction() as session:
		session['profile'] = {
			'user_id': 'auth0|5f3489a68f18aa00689d5333',
			'email': 'test@brown.edu'
		}
	new_user = User(auth_id='auth0|5f3489a68f18aa00689d5333', email='test@brown.edu')
	db.session.add(new_user)
	db.session.add(AdminClearance(email="test@brown.edu", can_create=True, can_edit=True, can_delete=True))
	db.session.commit()


def logout(client):
	return client.get('/auth/logout')


def create_trip(car_cap = 0, noncar_cap = 10):
	new_trip = Trip(
		name="test name", departure_date=func.current_date(),
		departure_location="test location", departure_time=func.current_time(),
		signup_deadline=func.current_date(), price=9.99, noncar_cap=noncar_cap, car_cap=car_cap)
	db.session.add(new_trip)
	db.session.commit()


def create_response():
	create_trip()
	new_response = Response(
		trip_id=1, user_email='test@brown.edu', lottery_slot=True
	)
	db.session.add(new_response)
	db.session.commit()

	response_text = select([Response.id])
	response_id = db.session.execute(response_text).fetchone()
	# returns reponse id
	return response_id[0]


def create_waitlist():
	response1_id = create_response()
	new_user = User(auth_id='auth0|5f3489a68f18aa00689d5334', email='test2@brown.edu')

	new_response = Response(
		trip_id=1, user_email='test2@brown.edu'
	)
	db.session.add(new_user)
	db.session.add(new_response)
	db.session.commit()

	new_user = User(auth_id='auth0|5f3489a68f18aa00689d5335', email='test3@brown.edu')

	new_response = Response(
		trip_id=1, user_email='test3@brown.edu'
	)
	db.session.add(new_user)
	db.session.add(new_response)
	db.session.commit()

	response_text = select([Response.id]).where(Response.user_email == 'test2@brown.edu')
	response2_id = db.session.execute(response_text).fetchone()[0]

	response_text = select([Response.id]).where(Response.user_email == 'test3@brown.edu')
	response3_id = db.session.execute(response_text).fetchone()[0]

	new_waitlist1 = Waitlist(
		trip_id=1, response_id=response2_id, waitlist_rank=1
	)

	new_waitlist2 = Waitlist(
		trip_id=1, response_id=response3_id, waitlist_rank=2
	)

	db.session.add(new_waitlist1)
	db.session.add(new_waitlist2)
	db.session.commit()

	return response1_id, response2_id, response3_id


def test_landing(client):
	response = client.get('/')

	assert b'Login' in response.data

	login(client)
	response = client.get('/')

	assert b'Logout' in response.data


### TEMPLATE TESTING OUTLINE ###

def test_sampletrip(client):
	login(client)
	new_trip = Trip(
		id=1, name="Adirondack Hiking", description="people literally are going hiking",
		departure_date=func.current_date(), boc_leaders="Anna, Clara, Ethan, & Lucas",
		departure_location="Adirondacks", departure_time=func.current_time(),
		return_date=func.current_date(), return_time=func.current_time(),
		car_cap=10,
		signup_deadline=func.current_date(), price=9.99, noncar_cap=10)
	db.session.add(new_trip)
	db.session.commit()

	# https://stackoverflow.com/questions/22559720/flask-response-object-is-not-iterable-with-response-producing-exceptions

	trip_page = client.get('/trip/1').data
	assert b"Adirondack Hiking" in trip_page
	assert b"people literally are going hiking" in trip_page


### TRIP.PY TESTING OUTLINE ###

def test_confirm_attendance(client):
	login_admin(client)
	response_id = create_response()
	assert db.session.query(Response).filter_by(user_behavior='NoResponse').count() == 1

	response_text = select([Response.user_email])
	email = db.session.execute(response_text).fetchone()[0]
	assert Decimal.compare(db.session.query(User).filter_by(email=email).one().weight, Decimal('1.0')) == 0

	response = client.post('/confirm_attendance/' + response_id)

	# check that user behavior changed from NoResponse to Confirmed, and that the weight has lowered
	assert db.session.query(Response).filter_by(user_behavior='Confirmed').count() == 1
	assert Decimal.compare(db.session.query(User).filter_by(email=email).one().weight, Decimal('0.95')) == 0


def test_decline_attendance(client):
	login_admin(client)
	response1_id, waitlist_rank1, waitlist_rank2 = create_waitlist()
	assert db.session.query(Response).filter_by(user_behavior='NoResponse').count() == 3

	# check that both users start with full weight of 1.0 and that the waitlisted user is not off the waitlist
	assert Decimal.compare(db.session.query(User).filter_by(email='test@brown.edu').one().weight, Decimal('1.0')) == 0
	assert Decimal.compare(db.session.query(User).filter_by(email='test2@brown.edu').one().weight, Decimal('1.0')) == 0
	assert Decimal.compare(db.session.query(User).filter_by(email='test3@brown.edu').one().weight, Decimal('1.0')) == 0
	assert db.session.query(Waitlist).filter_by(response_id=waitlist_rank1).one().off == False
	assert db.session.query(Waitlist).filter_by(response_id=waitlist_rank2).one().off == False

	# have user test@brown.edu decline their spot
	response = client.post('/decline_attendance/' + response1_id)
	# check that user behavior changed from NoResponse to Declined, and that the weight has lowered accordingly
	assert db.session.query(Response).filter_by(user_behavior='Declined').filter_by(
		user_email='test@brown.edu').count() == 1
	assert db.session.query(Response).filter_by(user_behavior='NoResponse').count() == 2
	assert Decimal.compare(db.session.query(User).filter_by(email='test@brown.edu').one().weight, Decimal('0.9')) == 0
	# check that the waitlisted user is now awarded a spot and is off the list
	assert db.session.query(Response).filter_by(lottery_slot=True).count() == 2
	assert db.session.query(Waitlist).filter_by(response_id=waitlist_rank1).one().off == True
	# check that second in line becomes first in line
	new_first = db.session.query(Waitlist).filter_by(response_id=waitlist_rank2).one()
	assert new_first.off == False
	assert new_first.waitlist_rank == 1


### ADMINVIEWS.PY TESTING OUTLINE ###

# (/admin/user/)
def test_resetweights(client):
	# modify weights of users
	# query the count of all users and query the count of all users with weight 1 and check if matching
	trips.dummy_users()
	assert db.session.query(User).filter_by(weight=1.0).count() < 51

	login_admin(client)

	response = client.post('/admin/user/reset')

	assert db.session.query(User).filter_by(weight=1.0).count() == 51


# def test_run_lottery(client):

def test_updatebehavior(client):
	login_admin(client)
	response_id = create_response()

	assert db.session.query(Response).filter_by(user_behavior='NoResponse').count() == 1
	response = client.post('/admin/response/updatebehavior',
						   data={'user_email': 'test@brown.edu', 'response_id': response_id, 'behavior': 'No Response'})
	assert db.session.query(Response).filter_by(user_behavior='No Response').count() == 1
	assert db.session.query(Response).filter_by(user_behavior='NoResponse').count() == 0


def test_awardspot(client):
	login_admin(client)
	response_id = create_response()
	new_waitlist = Waitlist(
		trip_id=1, response_id=response_id, waitlist_rank=1
	)
	db.session.add(new_waitlist)
	db.session.commit()

	assert db.session.query(Waitlist).filter_by(off=False).count() == 1
	response = client.post('/admin/waitlist/awardspot',
						   data={'trip_id': 1, 'waitlist_id': 1, 'response_id': response_id})
	assert db.session.query(Waitlist).filter_by(off=True).count() == 1
	assert db.session.query(Waitlist).filter_by(off=False).count() == 0


def test_lottery_signup(client):
	login_admin(client)
	create_trip()
	trips.dummy_users()

	assert db.session.query(Response).filter_by(user_email='test@brown.edu').count() == 0
	assert db.session.query(Trip).filter_by(id=1).count() == 1
	response = client.post("/lottery_signup/1", data={'financial_aid': 'True'})
	assert db.session.query(Response).filter_by(user_email='test@brown.edu').count() == 1


def test_lottery_withdraw(client):
	login_admin(client)
	create_trip()
	trips.dummy_users()

	assert db.session.query(Response).filter_by(user_email='test@brown.edu').count() == 0
	assert db.session.query(Trip).filter_by(id=1).count() == 1
	response = client.post("/lottery_signup/1", data={'financial_aid': 'True'})
	assert db.session.query(Response).filter_by(user_email='test@brown.edu').count() == 1

	response = client.post("/lottery_withdraw/1")
	print(response)
	assert db.session.query(Response).filter_by(user_email='test@brown.edu').count() == 0

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