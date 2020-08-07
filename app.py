import os
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

#for OAuth
from functools import wraps
import json
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv, find_dotenv
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

oauth = OAuth(app)

# auth0 = oauth.register('auth0', os.environ['AUTH_SETTINGS'],)
auth0 = oauth.register(
    'auth0',
    client_id='J28X7Tck3Wh7xrch1Z3OQYN379zanO6Z',
    client_secret='YOUR_CLIENT_SECRET',
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
# The segment below will recreate database on runtime (comment out if data is valuable)
# db.drop_all()
# db.create_all()

#trying out adding a user
user_test = User(username = "username", email = "test@email.com", first_name = "first", last_name = "last")
db.session.add(user_test)
db.session.commit()
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
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    session['jwt_payload'] = userinfo
    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name']
    }

    return redirect('/dashboard')

@app.route('/login')
def login():
    #change redirect_uri after development passes
    return auth0.authorize_redirect(redirect_uri='http://127.0.0.1:5000/')

# @app.route('/dashboard')
# @login_required
# def dashboard():
#     upcoming_trips = db.session.execute(
#         'SELECT '
#     )
#     past_trips = db.session.execute()
#     return render_template('upcoming.html', upcoming_trips = upcoming_trips, past_trips=past_trips)

def login_required(f):
    @wraps(f)
    def check_login(*args, **kwargs):
        if 'profile' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return check_login

if __name__ == '__main__':
    app.run()
