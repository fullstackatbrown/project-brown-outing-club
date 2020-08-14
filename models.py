from app import db
from sqlalchemy import CheckConstraint

class User(db.Model):
    __tablename__ = 'user'
    # Table columns
    id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    #float with 1 digit before decimal, 10 after
    weight = db.Column(db.Float(1, 10), nullable=False, default=1.0)

    # String representation of this object (for logging)
    def __repr__(self):
        return '<User %r>' % self.username

# Define an arbitrary amount of these classes below...

class Trip(db.Model):
    __tablename__ = 'trips'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text())
    contact = db.Column(db.String(120))
    #for src filepath
    image = db.Column(db.Text())

    departure_date = db.Column(db.Date(), nullable=False)
    return_date = db.Column(db.Date(), nullable=False)
    departure_location = db.Column(db.String(120), nullable=False)
    departure_time = db.Column(db.Time(), nullable=False)
    signup_deadline = db.Column(db.Date(), nullable=False)
    
    price = db.Column(db.Float(3, 2), nullable=False)
    car_cap = db.Column(db.Integer)
    noncar_cap = db.Column(db.Integer, nullable=False)

    # String representation of this object (for logging)
    def __repr__(self):
        return '<Trip %r>' % self.name

class Response(db.Model):
    __tablename__ = 'reponses'
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    trips = db.relationship('Trip', backref = db.backref('responses'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    users = db.relationship('User', backref = db.backref('responses'))
    financial_aid= db.Column(db.Boolean, default=False)
    car = db.Column(db.Boolean, default=False)
