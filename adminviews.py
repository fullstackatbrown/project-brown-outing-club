from flask_admin.contrib.sqla import ModelView, filters
from flask import session, url_for, Markup, flash, redirect, abort
import os, sqlalchemy
from sqlalchemy import or_
from sqlalchemy.sql import select, update, insert, func
from models import AdminClearance
from flask_admin import expose, BaseView
from flask_admin.helpers import get_form_data
from flask_mail import Mail, Message
from decimal import Decimal
import datetime
from lottery import *
from app import mail

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

# class AdminView(ReqClearance):
#     list_template = 'admin/guide.html'

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
    column_labels = dict(image='Image Source Filepath', boc_leaders="Trip Leaders")

    # excludes image column from list view
    column_list = (
        'name', 'contact', 'boc_leaders', 'destination', 'departure_date', 'departure_location', 
        'departure_time', 'return_date', 'return_time','signup_deadline', 
        'price', 'car_cap', 'noncar_cap', 'Run Lottery', 'Email Winners'
        )

    # Enable search functionality - it will search for trips
    column_searchable_list = ['name', 'contact']

    column_sortable_list = ('name', 'departure_date')

    #exlude admin from being able to input responses or lottery_completed values when creating a trip
    form_excluded_columns = ('lottery_completed')

    #creates the html form with a button that will call lottery_view method to run for a specific trip
    def format_runlottery(view, context, model, name):
        #if model.signup_deadline > datetime.date.today():
         #   return "Signup Deadline Hasn't Passed"

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
    # column_formatters = {
    #     'Run Lottery': format_runlottery
    # }

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
        runlottery(self, trip_id)
        try:
            self.session.commit()
        except Exception:
            flash('Failed to run lottery on the trip', 'error')

        return redirect(trip_index)

    def format_emailWinners(view, context, model, name):
        #if model.signup_deadline > datetime.date.today():
         #   return "Signup Deadline Hasn't Passed"
        
        emailWinners_button = '''
            <form action = "{emailWinners_view}" method="POST">
                <input id="trip_id" name = "trip_id" type="hidden" value="{trip_id}>
                <button type='submit'>Run</button>
            </form>
        '''.format(emailWinners_view=url_for('.emailWinners_view'), trip_id=model.id)

        return Markup(emailWinners_button)
    
    column_formatters = {
        'Email Winners': format_emailWinners
    }

    @expose('emailWinners', methods=['POST'])
    def emailWinners_view(self):
        trip_index = self.get_url('.index_view')
        form = get_form_data()

        trip_id = form['trip_id']

        # to change to pull from the database
        winners = self.session.query(Response).filter_by(id = trip_id, lottery_slot = True)
    
        with mail.connect() as conn:
            for response in winners:
                msg = Message('Lottery Selection', recipients = [response['email']])
                # to add specific lottery trip based on database pull
                msg.body = 'Hey! You have been selected for ' + response['trip']['name'] + '! Please confirm your attendance below.'
                conn.send(msg)
        return redirect(trip_index)
        

class ResponseView(ReqClearance):
    # renames columns for legibility
    column_labels = {
        'financial_aid': 'Needs Financial Aid',
        'car': 'Has a Car',
        'user_behavior': 'User Behavior (Declined Offer, No Show)',
        'trip.name': 'trip name',
        'user_email' : 'user email',
        'trip.departure_date': 'Departure Date',
        'trip.signup_deadline': 'Signup Deadline',
        'trip.contact': 'Trip Contact',
        'trip.price': 'Price',
        'trip.noncar_cap': 'Max Trip Spots',
        'trip.car_cap': 'Number of Cars Needed'
    }
    
    column_searchable_list = ['user_email', 'trip.name']

    column_filters = [
        'trip.departure_date', 'trip.signup_deadline', 'trip.contact', 'trip.price', 
        'trip.noncar_cap', 'trip.car_cap', 'financial_aid'
    ]

    column_list = ['trip', 'user', 'financial_aid', 'car', 'lottery_slot', 'user_behavior']

    #sets options for user_behavior (null, declined, or no show)
    form_choices = {
        'user_behavior': [
            ("Confirmed", "Confirmed"),
            ("Declined", "Declined"),
            ("No Show", "No Show")
        ]
    }

    #creates the html form with a button that will call lottery_view method to run for a specific trip
    def format_userbehavior(view, context, model, name):
        if not model.lottery_slot:
            return 'Not Given a Spot'

        if model.user_behavior is not None:
            return model.user_behavior

        select_behavior = '''
            <form action="{update_behavior}" method="POST" onsubmit="return confirm('Are you sure you want to update user behavior?');">
                <input id="user_email" name="user_email"  type="hidden" value="{user_email}">
                <input id="response_id" name="response_id"  type="hidden" value="{response_id}">
                <select id="behavior" name="behavior">
                    <option value="Confirmed">Confirmed</option>
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

class WaitlistView(ReqClearance):
    column_list = ['trip', 'response', 'waitlist_rank', 'Award Trip Spot']

    column_filters = [
        'trip.departure_date', 'trip.signup_deadline', 'trip.contact', 
        'trip.noncar_cap'
    ]

    column_searchable_list = ['response.user_email', 'trip.name']

    column_labels = {
        'trip.name': 'Trip Name',
        'trip.departure_date': 'Departure Date',
        'trip.signup_deadline': 'Signup Deadline',
        'trip.contact': 'Trip Contact',
        'trip.noncar_cap': 'Max Trip Spots',
        'response.user_email': 'User Email'
    }

    #displays only waitlist rows that are not off the waitlist yet by default
    def get_query(self):
      return self.session.query(self.model).filter(self.model.off==False)

    def get_count_query(self):
      return self.session.query(func.count('*')).filter(self.model.off==False)

    #creates the html form with a button that will call move user off waitlist (updating their response)
    def format_awardspot(view, context, model, name):
        #if the waitlist row isn't the top of the waitlist, display a message saying so
        if model.waitlist_rank != 1:
            return "Not Next In Line"

        award_button = '''
            <form action="{award_spot}" method="POST" onsubmit="return confirm('Are you sure you want to move the user off the waitlist?');">
            <input id="trip_id" name="trip_id"  type="hidden" value="{trip_id}">
                <input id="waitlist_id" name="waitlist_id"  type="hidden" value="{waitlist_id}">
                <input id="response_id" name="response_id"  type="hidden" value="{response_id}">
                <button type='submit'>Move Off Waitlist</button>
            </form>
        '''.format(award_spot=url_for('.award_spot'), trip_id=model.trip_id, waitlist_id=model.id, response_id=model.response_id)

        return Markup(award_button)
    
    #sets the format of the column Award Trip Spot
    #displays a button to move the response off the waitlist
    column_formatters = {
        'Award Trip Spot': format_awardspot
    }

    #creates a /waitlist/awardspot endpoint that runs the award_spot method
    @expose('awardspot', methods=['POST'])
    def award_spot(self):
        waitlist_index = self.get_url('.index_view')
        form = get_form_data()

        if not form:
            flash("Could not process waitlist edit request", 'error')
            return redirect(waitlist_index)

        #get waitlist id, response id, response, and waitlist from the form submission
        waitlist_id = form['waitlist_id']
        response_id = form['response_id']
        trip_id = form['trip_id']

        response = self.session.query(Response).filter_by(id=response_id).first()
        waitlist = self.get_one(waitlist_id)
        trip = self.session.query(Trip).filter_by(id=trip_id).first()

        #counts the number of responses to the trip in question that have been awarded a lottery spot and have either accepted, or have not declined
        # taken_spots = self.session.query(Response).filter(Response.id == trip_id, Response.lottery_slot == True, or_(Response.user_behavior == None, Response.user_behavior == "Confirmed")).count()
        taken_spots = self.session.query(Response).filter_by(id = trip_id, lottery_slot = True).count()
        #calculate total spots taken for the trip
        total_spots = trip.noncar_cap
        if trip.car_cap is not None:
            total_spots += trip.car_cap

        if (total_spots - taken_spots > 0):
            #set lottery_slot and off fields to true
            response.lottery_slot=True
            waitlist.off=True

            #supdate ranking for remaining waitlist rows on waitlist
            self.session.query(Waitlist).filter_by(trip_id=trip_id).filter_by(off=False).update({Waitlist.waitlist_rank: Waitlist.waitlist_rank-1})
            user = self.session.query(User).filter(User.email == response.user_email).first()
            gotspot(user)

            #ACTION REQUIRED: 
            #send email updating user about their spot in the trip
            #send_email(user)
        else :
            flash('Not enough spots available to move someone off the waitlist', 'error')

        try:
            self.session.commit()
        except Exception:
            flash('Failed to move response off waitlist', 'error')

        return redirect(waitlist_index)

class BackToDashboard(BaseView):
    @expose('/')
    def back_to_dashboard(self):
        return redirect(url_for('dashboard'))

class UserGuide(BaseView):
    @expose('/')
    def user_guide(self):
        return redirect(url_for('guide'))
