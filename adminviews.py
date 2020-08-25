from flask_admin.contrib.sqla import ModelView, filters
from flask import session, url_for, Markup, flash, redirect
import os, sqlalchemy
from sqlalchemy.sql import select, update, insert
from models import AdminClearance
from flask_admin import expose
from flask_admin.helpers import get_form_data
from decimal import Decimal

#evenutally needs to be moved into lottery.py
#---------------------------------------------------------------------------------------
from models import *
#returns a list of the users that won the lottery for the trip associated w input id
def runlottery(self, id):
    #get user emails that joined the lottery for the trip associated w input id
    get_users_text = select([Response.user_email]).where(Response.trip_id == id)
    users = self.session.execute(get_users_text).fetchall()

    #replace witht the actual lottery mechanism to produce list of users that won a spot
    winners = users

    for user in winners:
        user.lottery_slot = True
    
    return winners

#updates user weights based on if they declined or did not show
def update_userweights(self, behavior, user_email):
    #get user weight from user email
    get_user_text = select([User.weight]).where(User.email == user_email)
    current_weight = self.session.execute(get_user_text).fetchone()
    user_weight = current_weight[0]

    #adjust weight according to behavior
    if behavior == "Declined":
        user_weight -= Decimal(0.05)
    elif behavior == "No Show":
        user_weight -= Decimal(0.15)
    #ensure weight doesn't drop to below 0.25
    if user_weight < 0.25:
        user_weight = Decimal(0.25)

    self.session.query(User).update({User.weight: user_weight})

#---------------------------------------------------------------------------------------

class ReqClearance(ModelView):
    def is_accessible(self):
        if (session.get('profile') is not None):
            if (session.get('profile').get('email') is not None):
                check_clearance = select([AdminClearance]).where(AdminClearance.email == session.get('profile').get('email'))
                admin = self.session.execute(check_clearance).fetchone()
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

    list_template = 'admin/resetweights.html'

    #resets all user weights to default value of 1
    @expose('reset', methods=['POST'])
    def reset_weights(self):
        reset_text = self.session.query(User).update({User.weight: 1})
        self.session.commit()
        
        return redirect(self.get_url('.index_view'))

class TripView(ReqClearance):
    # renames image column to clarify input should be a filepath
    column_labels = dict(image='Image Source Filepath')

    # excludes image column from list view
    column_list = (
        'name', 'contact', 'destination', 'departure_date', 'departure_location', 
        'departure_time', 'return_date', 'return_time','signup_deadline', 
        'price', 'car_cap', 'noncar_cap', 'Run Lottery'
        )

    # Enable search functionality - it will search for trips
    column_searchable_list = ['name', 'contact']

    column_sortable_list = ('name', 'departure_date')

    #exlude admin from being able to input responses or lottery_completed values when creating a trip
    form_excluded_columns = ('lottery_completed')

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
            runlottery(self, trip_id)
            self.session.commit()
        except Exception:
            flash('Failed to run lottery on the trip', 'error')

        return redirect(trip_index)

class ResponseView(ReqClearance):
    # renames financial_aid and car columns
    column_labels = dict(
        financial_aid='Needs Financial Aid', car='Has a Car', user_email = "User Email", 
        trip_id = 'Trip Id', user_behavior="User Behavior"
        )

    column_searchable_list = ['user_email', 'trip_id']

    column_filters = ['trip', 'financial_aid']

    column_list = ['trip', 'trip_id', 'user', 'financial_aid', 'car', 'lottery_slot', 'user_behavior']

    form_choices = {
        'user_behavior': [
            ("Declined", "Declined"),
            ("No Show", "No Show")
        ]
    }

    #creates the html form with a button that will call lottery_view method to run for a specific trip
    def format_userbehavior(view, context, model, name):
        if model.user_behavior is not None:
            return model.user_behavior

        select_behavior = '''
            <form action="{update_behavior}" method="POST" onsubmit="return confirm('Are you sure you want to update user behavior?');">
                <input id="user_email" name="user_email"  type="hidden" value="{user_email}">
                <input id="response_id" name="response_id"  type="hidden" value="{response_id}">
                <select id="behavior" name="behavior">
                    <option value="Declined">Declined</option>
                    <option value="No Show">No Show</option>
                </select>
                <button type='submit'>Submit</button>
            </form>
        '''.format(update_behavior=url_for('.update_behavior'), response_id=model.id, user_email=model.user_email)

        return Markup(select_behavior)
    
    #sets the format of the column User Behavior
    #displays a selection of options to update user behavior to if necessary (i.e. decline, no show)
    column_formatters = {
        'user_behavior': format_userbehavior
    }

    #creates a /response/updatebehavior endpoint that lowers user weights according to their behavior
    @expose('updatebehavior', methods=['POST'])
    def update_behavior(self):
        response_index = self.get_url('.index_view')
        form = get_form_data()

        if not form:
            flash("Could not process update request", 'error')
            return redirect(response_index)

        #get user email, response id and response from the form submission
        user_email = form['user_email']
        response_id = form['response_id']
        response = self.get_one(response_id)

        #update user_behavior according to form submission
        behavior = form['behavior']
        response.user_behavior = behavior

        #updates the values in the db
        update_userweights(self, behavior, user_email)
        try:
            self.session.commit()
        except Exception:
            flash('Failed to update user weights', 'error')

        return redirect(response_index)

#eventually display the lottery table to be created
# class LotteryView(ReqClearance):
#     column_list = ('name', 'contact', 'destination', 'lottery_completed')

#     column_labels = dict(image='Image Source Filepath')

#     list_template = 'admin/runlottery.html'