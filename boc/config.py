import os


class Config(object):
	DEBUG = False
	TESTING = False
	CSRF_ENABLED = True
	SECRET_KEY = os.environ['SECRET_KEY']
	# correctly: comment 9 and leave 10 uncommented
	SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	MAIL_SERVER = 'email-smtp.us-east-1.amazonaws.com' # need to change based on server
	MAIL_USERNAME = os.environ['EMAIL_USERNAME']
	MAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
	MAIL_ADDRESS = "fsabbearbot@gmail.com"


class TestConfig(Config):
	TESTING = True
	SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL')


class ProductionConfig(Config):
	DEBUG = False


class DevelopmentConfig(Config):
	DEVELOPMENT = True
	DEBUG = True
