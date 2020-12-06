import os
from flask import Flask, render_template, request, jsonify, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_mail import Mail, Message
from sqlalchemy.sql import select, func, text, delete
from sqlalchemy import and_, create_engine, Date, cast, update
from .adminviews import *
from . import config

def create_app(test_config=None):
    
    app = Flask(__name__)
    
    if test_config is None:
        app.config.from_object(config.Config())
    else:
        app.config.from_object(test_config)

    from .models import db
    db.init_app(app)

    from .auth import oauth
    oauth.init_app(app)

    mail = Mail(app)

    # from .adminviews import ReqClearance

    #instantiate flask-admin
    # Check out /admin/{table name}/
    admin = Admin(app)
    admin.add_view(ReqClearance(AdminClearance, db.session, name = 'Admin'))
    admin.add_view(UserView(User, db.session))
    admin.add_view(TripView(Trip, db.session))
    admin.add_view(ResponseView(Response, db.session))
    admin.add_view(WaitlistView(Waitlist, db.session))
    admin.add_view(UserGuide(name="Admin User Guide"))
    admin.add_view(BackToDashboard(name="Back to Main Site"))

    from . import auth, trips
    app.register_blueprint(auth.bp)
    app.register_blueprint(trips.bp)

    # app.add_url_rule('/', endpoint = 'index')

    return app