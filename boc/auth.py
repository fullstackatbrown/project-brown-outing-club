import os
import random

from flask import Blueprint, Flask, render_template, request, jsonify, redirect, session, url_for, flash
from sqlalchemy.sql import select, func, text, delete

from .models import *

# for OAuth
from functools import wraps
import json
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv, find_dotenv
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode
from flask import current_app

bp = Blueprint('auth', __name__, url_prefix='/auth')

# instantiate 0auth authentication
oauth = OAuth()

auth0 = oauth.register(
	'auth0',
	client_id=os.environ['AUTH_CLIENTID'],
	client_secret=os.environ['AUTH_CLIENTSECRET'],
	api_base_url='https://fsab.us.auth0.com',
	access_token_url='https://fsab.us.auth0.com/oauth/token',
	authorize_url='https://fsab.us.auth0.com/authorize',
	client_kwargs={
		'scope': 'openid profile email',
	},
)

def authenticated():
	# checks if current user email is in adminclearance table
	is_admin, logged_in = False, False
	if session.get('profile') is not None:
		current_user_email = session.get('profile').get('email')
		is_admin = db.session.query(AdminClearance).filter_by(email=current_user_email).first() is not None
		logged_in = True
	return is_admin, logged_in


@bp.route('/login')
def login():
	return auth0.authorize_redirect(redirect_uri=os.environ['BASE_URL']+'/auth/callback')


# called after authentication
# stores new users in database if email is not in User Table already
@bp.route('/callback')
def callback_handling():
	print("callback")
	auth0.authorize_access_token()
	resp = auth0.get('userinfo')
	userinfo = resp.json()

	session['jwt_payload'] = userinfo
	session['profile'] = {
		'user_id': userinfo['sub'],
		'email': userinfo['email']
	}

	check_new_user = select([User]).where(User.email == userinfo['email'])
	if db.session.execute(check_new_user).fetchone() is None:
		# Assign random weight between 1 and 0 initially so that lottery can be run gracefully
		new_user = User(auth_id=userinfo['sub'], email=userinfo['email'])
		db.session.add(new_user)
		add_default_admin = select([User]).where(User.email == "test@brown.edu")
		# if db.session.execute(add_default_admin).fetchone() is None:
		#     db.session.add(AdminClearance(email = "test@brown.edu", can_create=True, can_edit=True, can_delete=True))
		db.session.commit()

	return redirect('/')


# tag that restricts access to only those logged in
def login_required(f):
	@wraps(f)
	def check_login(*args, **kwargs):
		if 'profile' not in session:
			return redirect(url_for('auth.login'))
		return f(*args, **kwargs)

	return check_login


# logout function
@bp.route('/logout')
def logout():
	session.clear()
	params = {'returnTo': url_for('trips.dashboard', _scheme='https', _external=True), 'client_id': os.environ['AUTH_CLIENTID']}
	return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))
