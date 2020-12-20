from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

app.config['DEBUG'] = True
app.config['TESTING'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com' # need to change based on server
app.config['MAIL_PORT'] = 465 # need to change based on port
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEBUG'] = True # based on app debug setting
app.config['MAIL_USERNAME'] = "brownuoutingclub" # to add boc email
app.config['MAIL_PASSWORD'] = "" # to add boc email
app.config['MAIL_DEFAULT_SENDER'] = ('Brown Outing Club' 'brownuoutingclub@gmail.com') # to add boc email between ''
app.config['MAIL_MAX_EMAILS'] = 200 # large limit for now 
app.config['MAIL_SUPPRESS_SEND'] = False # same as testing value
app.config['MAIL_ASCII_ATTACHMENTS'] = False

mail = Mail(app)
@app.route('/')
def index():
    # to change to pull from the database
    winners = [{'name' : 'name', 'email' : 'email'}]
    
    with mail.connect() as conn:
        for user in winners:
            msg = Message('Lottery Selection', recipients = [user['email']])
            # to add specific lottery trip based on database pull
            msg.body = 'Hey ' + user['name'] + '! You have been selected for this lottery trip'
            conn.send(msg)
    return 'message sent'

if __name__ == '__main__':
    app.run()