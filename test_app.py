import os
import tempfile
import pytest
from flask import session
from flask_sqlalchemy import SQLAlchemy
from boc import *


@pytest.fixture
def client():
    test_app = create_app(config.TestConfig())

    # Create a test client using the Flask application configured for testing
    with test_app.test_client() as client:
        # Establish an application context
        with test_app.app_context():
            yield client 


def test_landing(client):
    print(load_dotenv)
    print(find_dotenv)
    response = client.get('/dashboard')
    
    print(response.data)

    assert b'Log In' in response.data


def login(client):
    with client.session_transaction() as session:
        session['profile'] = {
            'user_id': 'auth0|5f3489a68f18aa00689d5333',
            'email': 'test@brown.edu'
        }
    # return client.get('/dashboard')

def logout(client):
    return client.get('/auth/logout')

def test_login_logout(client):
    """Make sure login and logout works."""

    rv = login(client)
    # assert b'Brown Outing Club' in rv.data

    # rv = logout(client)
    # assert b'Log In' in rv.data

    # rv = login(client, 'test@brown.edu' + 'x', '#xzAeGCrTenjR9jt')
    # assert b'Invalid username' in rv.data

    # rv = login(client, 'test@brown.edu', '#xzAeGCrTenjR9jt' + 'x')
    # assert b'Invalid password' in rv.data

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
# def test_resetweights(client):
    # modify weights of users
    # query the count of all users and query the count of all users with weight 1 and check if matching

# def test_runlottery(client):

# def test_updatebehavior(client):

# def test_awardspot(client):