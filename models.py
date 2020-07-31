from app import db

class User(db.Model):
    # Table columns
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    weight = db.Column(db.Float, nullable=False)

    # String representation of this object (for logging)
    def __repr__(self):
        return '<User %r>' % self.username

# Define an arbitrary amount of these classes below...

class Trip(db.Model):
    # Table columns
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.Date(), nullable=False)
    time = db.Column(db.Time(), nullable=False)
    description = db.Column(db.Text())
    signup_deadline = db.Column(db.DateTime(), nullable=False)
    price = db.Column(db.Float(), nullable=False)
    car_cap = db.Column(db.Integer(), nullable = False)
    noncar_cap = db.Column(db.Integer(), nullable=False)

    def__repr__(self):
        return '<Trip %r>' % self.name

class Response(db.Model):
    # Table columns
    id = db.Column(db.Integer, primary_key=True)
    # user_id
    financial_aid = db.Column(db.Boolean, default=False)
    car = db.Column(db.Boolean, default=False)