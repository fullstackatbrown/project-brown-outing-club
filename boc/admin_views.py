from flask import session, url_for, Markup, flash, redirect
from flask_admin import expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.helpers import get_form_data
from sqlalchemy.sql import func

from . import emails, trips
from .lottery import *


class ReqClearance(ModelView):
    def is_accessible(self):
        if (session.get('profile') is not None):
            if (session.get('profile').get('email') is not None):
                check_clearance = select([AdminClearance]).where(
                    AdminClearance.email == session.get('profile').get('email'))
                admin = db.session.execute(check_clearance).fetchone()
                if admin is not None:
                    can_create = admin['can_create']
                    can_edit = admin['can_edit']
                    can_delete = admin['can_delete']
                    return True
        return False


class UserView(ReqClearance):
    # Show only weight and email columns in list view
    column_list = ('email', 'weight')

    # Enable search functionality - it will search for emails
    column_searchable_list = ['email']

    # # Add filters for weight column
    column_filters = ['weight']

    list_template = 'admin/resetweights.html'

    # resets all user weights to default value of 1
    @expose('reset', methods=['POST'])
    def reset_weights(self):
        reset_weights = db.session.query(User).update({User.weight: 1})
        db.session.commit(reset_weights)

        return redirect(db.get_url('.index_view'))


class TripView(ReqClearance):
    # renames image column to clarify input should be a filepath
    column_labels = dict(image='Image Source Filepath', boc_leaders="Trip Leaders")

    # excludes image column from list view
    column_list = (
        'name', 'contact', 'boc_leaders', 'destination', 'departure_date', 'departure_location',
        'departure_time', 'return_date', 'return_time', 'signup_deadline',
        'price', 'car_cap', 'noncar_cap', 'Run Lottery', 'Email Winners'
    )

    # Enable search functionality - it will search for trips
    column_searchable_list = ['name', 'contact']

    column_sortable_list = ('name', 'departure_date')

    # exlude admin from being able to input responses or lottery_completed values when creating a trip
    form_excluded_columns = ('lottery_completed')

    # creates the html form with a button that will call lottery_view method to run for a specific trip
    def format_run_lottery(view, context, model, name):
        # if model.signup_deadline > datetime.date.today():
        #   return "Signup Deadline Hasn't Passed"

        if model.lottery_completed:
            return 'Completed'

        run_lottery_button = '''
            <form action="{lottery_view}" method="POST">
                <input id="trip_id" name="trip_id"  type="hidden" value="{trip_id}">
                <button type='submit'>Run</button>
            </form>
        '''.format(lottery_view=url_for('.lottery_view'), trip_id=model.id)

        return Markup(run_lottery_button)

    # creates a /trip/run_lottery endpoint that runs the run_lottery method on the trip id from the form
    @expose('run_lottery', methods=['POST'])
    def lottery_view(self):
        trip_index = self.get_url('.index_view')
        form = get_form_data()

        if not form:
            flash("Could not process lottery request", 'error')
            return redirect(trip_index)

        # get trip id and trip from the form submission
        trip_id = form['trip_id']
        trip = self.get_one(trip_id)

        # set lottery_complete field to true
        trip.lottery_completed = True

        # updates the values in the db
        run_lottery(trip_id)
        try:
            db.session.commit()
        except Exception:
            flash('Failed to run lottery on the trip', 'error')

        return redirect(trip_index)

    def format_emailWinners(view, context, model, name):
        # if model.signup_deadline > datetime.date.today():
        #   return "Signup Deadline Hasn't Passed"

        emailWinners_button = '''
            <form action="{emailwinners}" method="POST">
                <input id="trip_id" name="trip_id"  type="hidden" value="{trip_id}">
                <button type='submit'>Run</button>
            </form>
        '''.format(emailwinners=url_for('.emailWinners_view'), trip_id=model.id)

        return Markup(emailWinners_button)

    # sets the format of the column Run Lottery
    # displays a button to run the lottery or message saying lottery is complete depending on Trips column lottery_completed
    column_formatters = {
        'Run Lottery': format_run_lottery,
        'Email Winners': format_emailWinners
    }

    @expose('emailWinners', methods=['POST'])
    def emailWinners_view(self):
        trip_index = self.get_url('.index_view')
        form = get_form_data()

        trip_id = form['trip_id']

        # to change to pull from the database
        winners = db.session.query(Response).filter_by(trip_id=trip_id, lottery_slot=True).join(Trip,
                                                                                                  Response.trip_id == Trip.id).all()
        if winners is not None:
            emails.mail_group(winners, trips.get_trip(trip_id))
        return redirect(trip_index)


class ResponseView(ReqClearance):
    # renames columns for legibility
    column_labels = {
        'financial_aid': 'Needs Financial Aid',
        'car': 'Has a Car',
        'user_behavior': 'User Behavior (Declined Offer, No Response)',
        'trip.name': 'trip name',
        'user_email': 'user email',
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

    column_list = ['trip', 'user', 'financial_aid', 'car', 'lottery_slot', 'user_behavior', 'resend_email']

    # sets options for user_behavior (null, declined, or No Response)
    form_choices = {
        'user_behavior': [
            ("NoResponse", "No Response"),
            ("Confirmed", "Confirmed"),
            ("Declined", "Declined"),
        ]
    }

    # creates the html form with a button that will call lottery_view method to run for a specific trip
    def format_userbehavior(view, context, model, name):
        if not model.lottery_slot:
            return 'Not Given a Spot'

        if (model.user_behavior != "NoResponse"):
            return model.user_behavior

        select_behavior = '''
            <form action="{update_behavior}" method="POST" onsubmit="return confirm('Are you sure you want to update user behavior?');">
                <input id="user_email" name="user_email"  type="hidden" value="{user_email}">
                <input id="response_id" name="response_id"  type="hidden" value="{response_id}">
                <select id="behavior" name="behavior">
                    <option value="No Response">No Response</option>
                    <option value="Confirmed">Confirmed</option>
                    <option value="Declined">Declined</option>
                </select>
                <button type='submit'>Submit</button>
            </form>
        '''.format(update_behavior=url_for('.update_behavior'), response_id=model.id, user_email=model.user_email)

        return Markup(select_behavior)

    # creates a /response/updatebehavior endpoint that lowers user weights according to their behavior
    @expose('updatebehavior', methods=['POST'])
    def update_behavior(self):
        response_index = self.get_url('.index_view')
        form = get_form_data()

        if not form:
            flash("Could not process update request", 'error')
            return redirect(response_index)

        # get user email, response id and response from the form submission
        user_email = form['user_email']
        response_id = form['response_id']
        response = self.get_one(response_id)

        # update user_behavior according to form submission
        behavior = form['behavior']
        response.user_behavior = behavior

        # updates the values in the db
        update_user_weights(behavior, user_email)
        try:
            db.session.commit()
        except Exception:
            flash('Failed to update user weights', 'error')

        return redirect(response_index)

    def format_resendEmail(view, context, model, name):
        # if model.signup_deadline > datetime.date.today():
        #   return "Signup Deadline Hasn't Passed"

        resendEmail_button = '''
            <form action="{resendemail}" method="POST">
                <input id="response_id" name="response_id"  type="hidden" value="{response_id}">
                <button type='submit'>Resend Email</button>
            </form>
        '''.format(resendemail=url_for('.resend_email'), response_id=model.id)

        return Markup(resendEmail_button)

    # sets the format of the column User Behavior
    # displays a selection of options to update user behavior to if necessary (i.e. decline, No Response)
    column_formatters = {
        'user_behavior': format_userbehavior,
        'resend_email': format_resendEmail
    }

    @expose('resendemail', methods=['POST'])
    def resend_email(self):
        response_index = self.get_url('.index_view')
        form = get_form_data()

        response_id = form['response_id']
        response = self.get_one(response_id)
        trip = db.session.query(Trip).filter_by(id=response.trip_id).first()

        emails.mail_individual(response.user_email, trip.name, response.id)
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

    # displays only waitlist rows that are not off the waitlist yet by default
    def get_query(self):
        return db.session.query(self.model).filter(self.model.off == False)

    def get_count_query(self):
        return db.session.query(func.count('*')).filter(self.model.off == False)

    # creates the html form with a button that will call move user off waitlist (updating their response)
    def format_awardspot(view, context, model, name):
        # if the waitlist row isn't the top of the waitlist, display a message saying so
        if model.waitlist_rank != 1:
            return "Not Next In Line"

        award_button = '''
            <form action="{award_spot}" method="POST" onsubmit="return confirm('Are you sure you want to move the user off the waitlist?');">
            <input id="trip_id" name="trip_id"  type="hidden" value="{trip_id}">
                <input id="waitlist_id" name="waitlist_id"  type="hidden" value="{waitlist_id}">
                <input id="response_id" name="response_id"  type="hidden" value="{response_id}">
                <button type='submit'>Move Off Waitlist</button>
            </form>
        '''.format(award_spot=url_for('.award_spot'), trip_id=model.trip_id, waitlist_id=model.id,
                   response_id=model.response_id)

        return Markup(award_button)

    # sets the format of the column Award Trip Spot
    # displays a button to move the response off the waitlist
    column_formatters = {
        'Award Trip Spot': format_awardspot
    }

    # creates a /waitlist/awardspot endpoint that runs the award_spot method
    @expose('awardspot', methods=['POST'])
    def award_spot(self):
        waitlist_index = self.get_url('.index_view')
        form = get_form_data()

        if not form:
            flash("Could not process waitlist edit request", 'error')
            return redirect(waitlist_index)

        # get waitlist id, response id, response, and waitlist from the form submission
        waitlist_id = form['waitlist_id']
        response_id = form['response_id']
        trip_id = form['trip_id']

        response = db.session.query(Response).filter_by(id=response_id).first()
        waitlist = self.get_one(waitlist_id)
        trip = db.session.query(Trip).filter_by(id=trip_id).first()

        # counts the number of responses to the trip in question that have been awarded a lottery spot and have either accepted, or have not declined
        # taken_spots = db.session.query(Response).filter(Response.id == trip_id, Response.lottery_slot == True, or_(Response.user_behavior == None, Response.user_behavior == "Confirmed")).count()
        taken_spots = db.session.query(Response).filter_by(trip_id=trip_id, lottery_slot=True).count()
        # calculate total spots taken for the trip
        total_spots = trip.noncar_cap
        if trip.car_cap is not None:
            total_spots += trip.car_cap

        if (total_spots - taken_spots > 0):
            # set lottery_slot and off fields to true
            response.lottery_slot = True
            waitlist.off = True

            # supdate ranking for remaining waitlist rows on waitlist
            db.session.query(Waitlist).filter_by(trip_id=trip_id).filter_by(off=False).update(
                {Waitlist.waitlist_rank: Waitlist.waitlist_rank - 1})
            user = db.session.query(User).filter(User.email == response.user_email).first()
            gotspot(user)

            # emails person moved off of the waitlist
            emails.mail_individual(response.user_email, trip.name, response.id)
        else:
            flash('Not enough spots available to move someone off the waitlist', 'error')

        try:
            db.session.commit()
        except Exception:
            flash('Failed to move response off waitlist', 'error')

        return redirect(waitlist_index)


class BackToDashboard(BaseView):
    @expose('/')
    def back_to_dashboard(self):
        return redirect(url_for('trips.dashboard'))


class UserGuide(BaseView):
    @expose('/')
    def user_guide(self):
        return redirect(url_for('trips.guide'))
