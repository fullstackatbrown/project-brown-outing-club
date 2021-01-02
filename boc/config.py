import os

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'CHANGE THIS SECRET KEY'
    #correctly: comment 9 and leave 10 uncommented
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
   SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.gmail.com' # need to change based on server
    MAIL_PORT = 465 # need to change based on port
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEBUG = False # based on app debug setting
    MAIL_USERNAME = "brownuoutingclub"
    MAIL_PASSWORD = "Brownoutingclub2020"
    MAIL_DEFAULT_SENDER = ('Brown Outing Club' 'brownuoutingclub@gmail.com')
    MAIL_MAX_EMAILS = 400 # large limit for now 
    MAIL_SUPPRESS_SEND = False # same as testing value
    MAIL_ASCII_ATTACHMENTS = False

class TestConfig(Config):
    TESTING = False
    #jury rigged fix: comment 27, uncomment 26
    #SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admin:EOKg9ICKKiC98wyW4Rmx@dev-mariadb.catkywuq5bap.us-east-1.rds.amazonaws.com:3306/test'
    SQLALCHEMY_DATABASE_URI = os.environ['TEST_DATABASE_URL']

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class authConfig():
    client_id='J28X7Tck3Wh7xrch1Z3OQYN379zanO6Z'
    client_secret='S1PAZdX5lAm3eGIv5tnmJfycfIW9W4Msv8Bi5_5N3uhjVmOVONCUbjaI0Ht6fp_k'
    api_base_url='https://dev-h395rto6.us.auth0.com'
    access_token_url='https://dev-h395rto6.us.auth0.com/oauth/token'
    authorize_url='https://dev-h395rto6.us.auth0.com/authorize'
    client_kwargs={
        'scope': 'openid profile email'
    }
