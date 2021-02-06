import os
import tempfile
import pytest
from flask import session
from flask_sqlalchemy import SQLAlchemy
from boc import *
from boc import trips

@pytest.fixture
def client():
    test_app = create_app(config.TestConfig())

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
    new_user = User(auth_id = 'auth0|5f3489a68f18aa00689d5333', email = 'test@brown.edu')             
    db.session.add(new_user)
    db.session.add(AdminClearance(email = "test@brown.edu", can_create=True, can_edit=True, can_delete=True))
    db.session.commit()

def logout(client):
    return client.get('/auth/logout')

def test_landing(client):
    response = client.get('/dashboard')

    assert b'Login' in response.data

    login(client)
    response = client.get('/dashboard')

    assert b'Logout' in response.data


### TRIP.PY TESTING OUTLINE ###

# def test_confirmattendance(client):
    # first check: 
    #   response w client's response id = "NoResponse"
    #   client user row

    # post w data from client's response id, check if response user behavior = "Confirmed" and user weight is lowered

# def test_declineattendance(client):
    # first check: 
    #   response w client's response id is "NoResponse"
    #   client user row
    #   get waitlist and response row of 1st and 2nd in line for waitlist

    # post w data from client's response id, check if response user behavior = "Declined" and user weight is lowered
    # check waitlist row of 1st in line now has off = True & response now has lottery_slot = True
    # check waitlist row of 2nd in line now has waitlist_rank = 1

### ADMINVIEWS.PY TESTING OUTLINE ###

# (/admin/user/)
def test_resetweights(client):
    # modify weights of users
    # query the count of all users and query the count of all users with weight 1 and check if matching
    trips.dummy_users()
    assert db.session.query(User).filter_by(weight = 1.0).count() < 51

    login_admin(client)

    response = client.post('/admin/user/reset')
    
    assert db.session.query(User).filter_by(weight = 1.0).count() == 51
    logout(client)

# def test_runlottery(client):

# def test_updatebehavior(client):
#     trips.dummy_users()
#     login_admin(client)
#     response = client.post('/admin/response/updatebehavior', {'user_email': 'test@brown.edu'})

# def test_awardspot(client):