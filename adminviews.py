from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView, filters

class UserView(ModelView):
    # Show only weight and email columns in list view
    column_list = ('email', 'weight')

    # Enable search functionality - it will search for emails
    column_searchable_list = ['email']

    # # Add filters for weight column
    column_filters = ['weight']

class TripView(ModelView):
    # renames image column to clarify input should be a filepath
    column_labels = dict(image='Image Source Filepath')

    # excludes image column from list view
    column_exclude_list = ['image']

    # Enable search functionality - it will search for trips
    column_searchable_list = ['name', 'contact']

    column_sortable_list = ['price', 'departure_date', 'signup_deadline']

class ResponseView(ModelView):
    # renames financial_aid and car columns
    column_labels = dict(financial_aid='Needs Financial Aid', car='Has a Car')