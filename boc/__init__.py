from flask import Flask, render_template
from flask_admin import Admin

from . import config, emails
from .admin_views import *
from .auth import authenticated


def create_app(test_config=None):
	app = Flask(__name__)

	if test_config is None:
		app.config.from_object(config.Config())
	else:
		app.config.from_object(test_config)

	from .models import db
	db.app = app
	db.init_app(app)
	# refresh database
	# with app.app_context():
	#     db.drop_all()
	#     db.create_all()

	from .auth import oauth
	oauth.init_app(app)

	emails.init_mail(app)

	# instantiate flask-admin
	# Check out /admin/{table name}/
	admin = Admin(app, template_mode='bootstrap4')
	admin.add_view(ReqClearance(AdminClearance, db.session, name='Admin'))
	admin.add_view(UserView(User, db.session))
	admin.add_view(TripView(Trip, db.session))
	admin.add_view(ResponseView(Response, db.session))
	admin.add_view(WaitlistView(Waitlist, db.session))
	admin.add_view(BackToDashboard(name="Back to Main Site"))

	from . import auth, trips
	app.register_blueprint(auth.bp)
	app.register_blueprint(trips.bp)

	@app.route('/help')
	def root():
		is_admin, logged_in = authenticated()
		return render_template('help.html', is_admin=is_admin, logged_in=logged_in)

	return app
