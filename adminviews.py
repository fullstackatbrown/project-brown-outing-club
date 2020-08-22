from flask_admin.contrib.sqla import ModelView, filters
from flask import session, url_for, Markup, flash, redirect
from sqlalchemy import create_engine
import os
from sqlalchemy.sql import select
from models import AdminClearance
from flask_admin import expose
from flask_admin.helpers import get_form_data

engine = create_engine(os.environ['DATABASE_URL'])
conn = engine.connect()

#evenutally needs to be moved into lottery.py
#---------------------------------------------------------------------------------------
from models import *
#returns a list of the users that won the lottery for the trip associated w input id
def runlottery(id):
    #get user emails that joined the lottery for the trip associated w input id
    get_users_text = select([Response.user_email]).where(Response.trip_id == id)
    users = conn.execute(get_users_text).fetchall()

    #replace witht the actual lottery mechanism to produce list of users that won a spot
    winners = users

    for user in winners:
        user.lottery_slot = True
    
    return winners

#---------------------------------------------------------------------------------------

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
    column_list = (
        'name', 'contact', 'destination', 'departure_date', 'departure_location', 'departure_time', 'return_date', 'return_time',
        'signup_deadline', 'price', 'car_cap', 'noncar_cap', 'Run Lottery'
        )

    # Enable search functionality - it will search for trips
    column_searchable_list = ['name', 'contact']

    column_sortable_list = ('name', 'departure_date')

    #creates the html form with a button that will call lottery_view method to run for a specific trip
    def format_runlottery(view, context, model, name):
        if model.lottery_completed:
            return 'Completed'

        runlottery_button = '''
            <form action="{lottery_view}" method="POST">
                <input id="trip_id" name="trip_id"  type="hidden" value="{trip_id}">
                <button type='submit'>Run</button>
            </form>
        '''.format(lottery_view=url_for('.lottery_view'), trip_id=model.id)

        return Markup(runlottery_button)
    
    #sets the format of the column Run Lottery
    #displays a button to run the lottery or message saying lottery is complete depending on Trips column lottery_completed
    column_formatters = {
        'Run Lottery': format_runlottery
    }

    #creates a /trip/runlottery endpoint that runs the runlottery method on the trip id from the form 
    @expose('runlottery', methods=['POST'])
    def lottery_view(self):
        trip_index = self.get_url('.index_view')
        form = get_form_data()

        if not form:
            flash("Could not process lottery request", 'error')
            return redirect(trip_index)

        #get trip id and trip from the form submission
        trip_id = form['trip_id']
        trip = self.get_one(trip_id)

        #set lottery_complete field to true
        trip.lottery_completed=True

        #updates the values in the db
        try:
            runlottery(trip_id)
            self.session.commit()
        except Exception:
            flash('Failed to run lottery on the trip', 'error')

        return redirect(trip_index)

class ResponseView(ReqClearance):
    # renames financial_aid and car columns
    column_labels = dict(financial_aid='Needs Financial Aid', car='Has a Car')

#eventually display the lottery table to be created
# class LotteryView(ReqClearance):
#     column_list = ('name', 'contact', 'destination', 'lottery_completed')

#     column_labels = dict(image='Image Source Filepath')

#     list_template = 'admin/runlottery.html'