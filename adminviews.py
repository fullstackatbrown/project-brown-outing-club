from flask_admin.contrib.sqla import ModelView, filters
from flask import session
from sqlalchemy import create_engine
import os
from sqlalchemy.sql import select
from models import AdminClearance

engine = create_engine(os.environ['DATABASE_URL'])
conn = engine.connect()

class ReqClearance(ModelView):
    def is_accessible(self):
        if (session.get('profile') is not None):
            if (session.get('profile').get('email') is not None):
                check_clearance = select([AdminClearance]).where(AdminClearance.email == session.get('profile').get('email'))
                admin = conn.execute(check_clearance).fetchone()
                if admin is not None:
                    can_create = admin['can_create']
                    can_edit = admin['can_edit']
                    can_delete = admin['can_delete']
                    return True
        return False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('app.login', next=request.url))

class UserView(ReqClearance):
    # Show only weight and email columns in list view
    column_list = ('email', 'weight')

    # Enable search functionality - it will search for emails
    column_searchable_list = ['email']

    # # Add filters for weight column
    column_filters = ['weight']

class TripView(ReqClearance):
    # renames image column to clarify input should be a filepath
    column_labels = dict(image='Image Source Filepath')

    # excludes image column from list view
    column_exclude_list = ['image']

    # Enable search functionality - it will search for trips
    column_searchable_list = ['name', 'contact']

    column_sortable_list = ['price', 'departure_date', 'signup_deadline']

class ResponseView(ReqClearance):
    # renames financial_aid and car columns
    column_labels = dict(financial_aid='Needs Financial Aid', car='Has a Car')