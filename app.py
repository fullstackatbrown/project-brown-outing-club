import os
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from sqlalchemy.sql import select, func, text
from sqlalchemy import create_engine, Date, cast

#for OAuth
from functools import wraps
import json
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv, find_dotenv
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode

#instantiate Flask app
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

#create connection to database
engine = create_engine(os.environ['DATABASE_URL'], echo=True)
conn = engine.connect()

#instantiate 0auth authentication
oauth = OAuth(app)

# auth0 = oauth.register('auth0', os.environ['AUTH_SETTINGS'])
auth0 = oauth.register(
    'auth0',
    client_id='J28X7Tck3Wh7xrch1Z3OQYN379zanO6Z',
    client_secret='S1PAZdX5lAm3eGIv5tnmJfycfIW9W4Msv8Bi5_5N3uhjVmOVONCUbjaI0Ht6fp_k',
    api_base_url='https://dev-h395rto6.us.auth0.com',
    access_token_url='https://dev-h395rto6.us.auth0.com/oauth/token',
    authorize_url='https://dev-h395rto6.us.auth0.com/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    },
)

# Sync SQLAlchemy with database
db = SQLAlchemy(app)

from models import *
from adminviews import *

#instantiate flask-admin
# Check out /admin/{table name}/
admin = Admin(app)
admin.add_view(ReqClearance(AdminClearance, db.session, name = 'Admin'))
admin.add_view(UserView(User, db.session))
admin.add_view(TripView(Trip, db.session))
admin.add_view(ResponseView(Response, db.session))

# db.drop_all()
# db.create_all()
# db.session.add(AdminClearance(email = 'test@brown.edu', can_create=True, can_edit = True, can_delete=True))
# db.session.commit()
# Serve a template from index
@app.route('/')
def index():
    #create a landing page w welcome, explanation of purpose, login button
    return render_template('test.html', name="name")

# Serve an API endpoint from test
@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        return 'POST request received'
    else:
        return 'GET request received'

#called after authentication
#stores new users in database if email is not in User Table already
@app.route('/callback')
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
    if conn.execute(check_new_user).fetchone() is None:
        new_user = User(auth_id = userinfo['sub'], email = userinfo['email'])             
        db.session.add(new_user)
        db.session.commit()

    return redirect('/dashboard')

#redirects user to auth0 login
@app.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri='http://127.0.0.1:5000/callback')

#tag that restricts access to only those logged in
def login_required(f):
    @wraps(f)
    def check_login(*args, **kwargs):
        if 'profile' not in session:
            return redirect(url_for('test'))
        return f(*args, **kwargs)
    return check_login

#dashboard that is the target of redirect from login page
@app.route('/dashboard')
@login_required
def dashboard():
    #selects rows where the current date matches or is earlier than the sign up deadline
    #NOTE: current date uses the server clock to fetch the date, so make sure the app is deployed on an Eastern Time Server
    upcoming_text = select([Trip]).where(Trip.signup_deadline >= func.current_date()).order_by(Trip.signup_deadline)
    upcoming_trips = conn.execute(upcoming_text).fetchall()

    #list of trips that have lotteries the user has signed up for
    signed_text = select([Response.trip_id]).where(Response.user_email == session.get('profile').get('email'))
    signed_up = conn.execute(signed_text).fetchall()

    return render_template('upcoming.html', upcoming_trips = upcoming_trips, signed_up = signed_up)

#displays past trips
@app.route('/pasttrips')
def pasttrips():
    #selects rows where the current date is after the sign up deadline
    #NOTE: current date uses the server clock to fetch the date, so make sure the app is deployed on an Eastern Time Server
    past_text = select([Trip]).where(Trip.signup_deadline < func.current_date()).order_by(Trip.signup_deadline.desc())
    past_trips = conn.execute(past_text).fetchall()

    return render_template('past.html', past_trips = past_trips)

#gets trip object from its id
def get_trip(id):
    trip_text = select([Trip]).where(Trip.id == id)
    trip = conn.execute(trip_text).fetchone()

    if trip is None:
        abort(404, "Trip doesn't exist.")

    return trip

#page linked with "Enter Lottery" from dashboard, should collect information necessary to create Response row in db using a form
@app.route('/lotterysignup/<int:id>', methods=('GET', 'POST'))
@login_required
def lotterysignup(id):
    trip = get_trip(id)

    if request.method == 'POST':
        car = request.form['car']
        financial_aid = request.form['financial_aid']

        new_response = Response(trip_id = id, user_email = session.get('profile').get('email'), financial_aid = financial_aid, car = car)
        db.session.add(new_response)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('lottery.html', id = id)

#logout function
@app.route('/logout')
def logout():
    session.clear()
    params = {'returnTo': url_for('index', _external=True), 'client_id': 'J28X7Tck3Wh7xrch1Z3OQYN379zanO6Z'}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))

if __name__ == '__main__':
    app.run()
