import os
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.sql import select, func, text
from sqlalchemy import create_engine, Date, cast

#for OAuth
from functools import wraps
import json
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv, find_dotenv
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

engine = create_engine(os.environ['DATABASE_URL'], echo=True)
conn = engine.connect()

oauth = OAuth(app)

# auth0 = oauth.register(os.environ['AUTH_SETTINGS'])
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

# Check out /admin/user/
admin = Admin(app)
admin.add_view(ModelView(User, db.session))

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

@app.route('/callback')
def callback_handling():
    print("callback")
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    session['jwt_payload'] = userinfo
    session['profile'] = {
        'user_id': userinfo['sub'],
        # 'first_name': userinfo['given_name'],
        # 'last_name': userinfo['family_name'],
        'name': userinfo['name'],
        'email': userinfo['email'],
        'picture': userinfo['picture']
    }

    check_new_user = select([User]).where(User.email == userinfo['email'])
    if conn.execute(check_new_user).fetchone() is None:
        new_user = User(username = userinfo['sub'], email = userinfo['email'], first_name = userinfo['name'], last_name = "last")             
        db.session.add(new_user)
        db.session.commit()

    return redirect('/dashboard')

@app.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri='http://127.0.0.1:5000/callback')

def login_required(f):
    @wraps(f)
    def check_login(*args, **kwargs):
        if 'profile' not in session:
            return redirect(url_for('test'))
        return f(*args, **kwargs)
    return check_login

@app.route('/dashboard')
@login_required
def dashboard():
    # print(func.currentdate())
    #selects rows where the current date matches or is earlier than the sign up deadline
    upcoming_text = select([Trip]).where(Trip.signup_deadline >= func.current_date())
    past_text = select([Trip]).where(Trip.signup_deadline < func.current_date())

    # print(conn.execute(upcoming_trips).fetchone())
    # print(conn.execute(past_trips).fetchone())
    #name of the user if available
    # if session.get('first_name') is not None:
    #     name = session.get('first_name')
    # elif session.get('full_name') is not None:
    #     name = session.get('full_name')
    # else:
    #     name = ""
    upcoming_trips = conn.execute(upcoming_text).fetchall()
    past_trips = conn.execute(past_text).fetchall()
    return render_template('upcoming.html',
    upcoming_trips = upcoming_trips, past_trips = past_trips, name = name)

@app.route('/logout')
def logout():
    session.clear()
    params = {'returnTo': url_for('index', _external=True), 'client_id': 'J28X7Tck3Wh7xrch1Z3OQYN379zanO6Z'}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))

if __name__ == '__main__':
    app.run()
