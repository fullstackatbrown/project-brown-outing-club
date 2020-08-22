from app import db
from sqlalchemy import CheckConstraint

class AdminClearance(db.Model):
    __tablename__ = 'adminclearance'
    # Table columns
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    #dictates what each admin is able to do with the data
    can_create = db.Column(db.Boolean, nullable=False)
    can_edit = db.Column(db.Boolean, nullable=False)
    can_delete = db.Column(db.Boolean, nullable=False)

    # String representation of this object (for logging)
    def __repr__(self):
        return '<Admin %r>' % self.email

class User(db.Model):
    __tablename__ = 'user'
    # Table columns
    id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    #lottery determinants
    # first_time = db.Column(db.Boolean, nullable=True, default=True)
    # got_last_trip = db.Column(db.Boolean, nullable=True, default=True)
    # total_trips = db.Column(db.Integer, nullable=False, default = 0)

    #float with 1 digit before decimal, 10 after
    weight = db.Column(db.Float(1, 10), nullable=False, default=1.0)

    # String representation of this object (for logging)
    def __repr__(self):
        return '<User %r>' % self.email

class Trip(db.Model):
    __tablename__ = 'trips'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text())
    contact = db.Column(db.String(120))
    destination = db.Column(db.String(80))
    #for src filepath
    image = db.Column(db.Text())

    departure_date = db.Column(db.Date(), nullable=False)
    departure_location = db.Column(db.String(120), nullable=False)
    departure_time = db.Column(db.Time(), nullable=False)
    return_date = db.Column(db.Date(), nullable=True)
    return_time = db.Column(db.Time(), nullable=True)
    
    signup_deadline = db.Column(db.Date(), nullable=False)
    price = db.Column(db.Numeric(5, 2), nullable=False)
    car_cap = db.Column(db.Integer)
    noncar_cap = db.Column(db.Integer, nullable=False)

    # String representation of this object (for logging)
    def __repr__(self):
        return '<Trip %r>' % self.name

class Response(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    trip = db.relationship('Trip', backref = db.backref('responses'))
    user_email = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)
    user = db.relationship('User', backref = db.backref('responses'))
    financial_aid= db.Column(db.Boolean, default=False)
    car = db.Column(db.Boolean, default=False)

    #update when lottery is ran, true means they received a lottery spot
    lottery_slot = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Response to %r by %r>' % (self.trip_id, self.user_id)
