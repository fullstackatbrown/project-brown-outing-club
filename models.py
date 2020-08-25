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

    #boolean indicating if lottery has been for the trip run or not
    lottery_completed = db.Column(db.Boolean, default=False)

    # String representation of this object (for logging)
    def __repr__(self):
        return '<Trip %r - %s>' % (self.name, self.departure_date.strftime('%m/%d/%Y'))

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

    #update when user responds to their trip spot offer
    user_behavior = db.Column(db.String(10))

    def __repr__(self):
        return '<Response to %r by %r>' % (self.trip_id, self.user_email)

# class Waitlist(db.Model):
#     __tablename__ = 'waitlist'
#     id = db.Column(db.Integer, primary_key=True)
#     trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
#     trip = db.relationship('Trip', backref = db.backref('waitlist'))
#     user_email = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)
#     user = db.relationship('User', backref = db.backref('waitlist'))
#     waitlist_rank = db.Column(db.Integer, nullable=False)
#     #Yes, as relationship is an ORM concept that helps map the SQL table relationships to the object world, 
#     # but it does not define them.
#     responses = db.relationship('Response', backref = db.backref('waitlist'))

#     #want it to appear only for those where you can select a trip where lottery_completed is true but
#     #some responses lottery_slot is false