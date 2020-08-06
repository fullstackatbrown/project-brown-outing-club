import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

# Sync SQLAlchemy with database
db = SQLAlchemy(app)
from models import *
# The segment below will recreate database on runtime (comment out if data is valuable)
try:
    db.drop_all()
    db.create_all()
except:
    print("issue encountered regenerating database")

#trying out adding a user
user_test = User(username = "username", email = "test@email.com", first_name = "first", last_name = "last")
db.session.add(user_test)
db.session.commit()
# Check out /admin/user/
admin = Admin(app)
admin.add_view(ModelView(User, db.session))

# Serve a template from index
@app.route('/')
def index():
    return render_template('test.html', name="name")

# Serve an API endpoint from test
@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        return 'POST request received'
    else:
        return 'GET request received'

if __name__ == '__main__':
    app.run()
