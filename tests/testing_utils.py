import json

from boc import *


def login(client):
	auth_token = str(uuid.uuid4())
	email = str(uuid.uuid4()) + '@brown.edu'
	new_user = User(auth_id=auth_token, email=email)
	db.session.add(new_user)
	db.session.commit()
	with client.session_transaction() as transaction:
		transaction['profile'] = {'user_id': auth_token, 'email': email}
	return auth_token, email


def login_admin(client):
	auth_token = str(uuid.uuid4())
	email = str(uuid.uuid4()) + '@brown.edu'
	new_user = User(auth_id=auth_token, email=email)
	db.session.add(new_user)
	db.session.add(AdminClearance(email=email, can_create=True, can_edit=True, can_delete=True))
	db.session.commit()
	with client.session_transaction() as transaction:
		transaction['profile'] = {'user_id': auth_token, 'email': email}
	return auth_token, email


def create_users(n):
	users = []
	for i in range(n):
		auth_token = str(uuid.uuid4())
		email = str(uuid.uuid4()) + '@brown.edu'
		new_user = User(auth_id=auth_token, email=email)
		db.session.add(new_user)
		db.session.commit()
		users.append((auth_token, email))
	return users


def logout(client):
	return client.get('/auth/logout')


def create_trip(car_cap, non_car_cap):
	new_trip = Trip(name=str(uuid.uuid4()), departure_date=func.current_date(), departure_location="test location",
					departure_time=func.current_time(), signup_deadline=func.current_date(), price=9.99,
					non_car_cap=non_car_cap, car_cap=car_cap)
	db.session.add(new_trip)
	db.session.commit()
	return new_trip.id


def create_response(client, trip_id, auth_token, email, car=False):
	with client.session_transaction() as transaction:
		transaction['profile'] = {'user_id': auth_token, 'email': email}
	response = client.post('/api/lottery_signup/' + str(trip_id), content_type='multipart/form-data',
						data={"car": "true"} if car else None)
	return response.data.decode('UTF-8')


def create_waitlist():
	response1_id = create_response()
	new_user = User(auth_id='auth0|5f3489a68f18aa00689d5334', email='test2@brown.edu')
	new_response = Response(trip_id=1, user_email='test2@brown.edu')
	db.session.add(new_user)
	db.session.add(new_response)
	db.session.commit()

	new_user = User(auth_id='auth0|5f3489a68f18aa00689d5335', email='test3@brown.edu')
	new_response = Response(trip_id=1, user_email='test3@brown.edu')
	db.session.add(new_user)
	db.session.add(new_response)
	db.session.commit()

	response_text = select([Response.id]).where(Response.user_email == 'test2@brown.edu')
	response2_id = db.session.execute(response_text).fetchone()[0]

	response_text = select([Response.id]).where(Response.user_email == 'test3@brown.edu')
	response3_id = db.session.execute(response_text).fetchone()[0]

	return response1_id, response2_id, response3_id
