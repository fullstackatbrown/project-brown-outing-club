import os
import tempfile
import pytest
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from boc import *

@pytest.fixture
def client():
    # test_app = Flask(__name__)
    # test_app.config.from_object(os.environ.get('APP_SETTINGS'))
    # test_app.config['TESTING'] = True
    test_app = create_app(config.TestConfig())

    # Create a test client using the Flask application configured for testing
    with test_app.test_client() as client:
        # Establish an application context
        with test_app.app_context():
            yield client 


def test_landing(client):
    response = client.get('/')
    assert b'Log In' in response.data

# def test_dashboard(client):
#     response = client.get('/dashboard', follow_redirects=True)
#     assert b'Admin' in response.data


# def login(client, username, password):
#     return client.post('/login', data=dict(
#         username=username,
#         password=password
#     ), follow_redirects=True)


# def logout(client):
#     return client.get('/logout', follow_redirects=True)

# def test_login_logout(client):
#     """Make sure login and logout works."""

#     rv = login(client, 'test@brown.edu', '#xzAeGCrTenjR9jt')
#     print(rv.data)
#     assert b'You were logged in' in rv.data

#     rv = logout(client)
#     assert b'You were logged out' in rv.data

#     rv = login(client, 'test@brown.edu' + 'x', '#xzAeGCrTenjR9jt')
#     assert b'Invalid username' in rv.data

#     rv = login(client, 'test@brown.edu', '#xzAeGCrTenjR9jt' + 'x')
#     assert b'Invalid password' in rv.data