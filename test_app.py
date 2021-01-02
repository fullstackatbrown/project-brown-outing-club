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