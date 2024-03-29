import random
import uuid

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class AdminClearance(db.Model):
    __tablename__ = 'adminclearance'
    # Table columns
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), db.ForeignKey('user.email', ondelete="CASCADE"), nullable=False)
    user = db.relationship('User', backref=db.backref('adminclearance'))

    # dictates what each admin is able to do with the data
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
    weight = db.Column(db.Float, nullable=False, default=round(random.uniform(0.0001, -0.0001), 5))

    # String representation of this object (for logging)
    def __repr__(self):
        return '<User %r>' % self.email


class Trip(db.Model):
    __tablename__ = 'trips'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text())
    # primary email
    contact = db.Column(db.String(120))
    # trip leaders' names
    boc_leaders = db.Column(db.String(120))
    destination = db.Column(db.String(80))
    # for src filepath
    image = db.Column(db.Text())

    departure_date = db.Column(db.Date(), nullable=False)
    departure_location = db.Column(db.String(120), nullable=False)
    departure_time = db.Column(db.Time(), nullable=False)
    return_date = db.Column(db.Date(), nullable=True)
    return_time = db.Column(db.Time(), nullable=True)

    signup_deadline = db.Column(db.Date(), nullable=False)
    price = db.Column(db.Numeric(5, 2), nullable=False)
    car_cap = db.Column(db.Integer)
    non_car_cap = db.Column(db.Integer, nullable=False)

    # boolean indicating if lottery has been for the trip run or not
    lottery_completed = db.Column(db.Boolean, default=False, nullable=False)

    # String representation of this object (for logging)
    def __repr__(self):
        return '<Trip %r - %s>' % (self.name, self.departure_date.strftime('%m/%d/%Y'))


class Response(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id', ondelete="CASCADE"), nullable=False)
    trip = db.relationship('Trip', backref=db.backref('responses'))
    user_email = db.Column(db.String(120), db.ForeignKey('user.email', ondelete="CASCADE"), nullable=False)
    user = db.relationship('User', backref=db.backref('responses'))
    financial_aid = db.Column(db.Boolean, default=False)
    car = db.Column(db.Boolean, default=False)

    # update when lottery is ran, true means they received a lottery spot
    lottery_slot = db.Column(db.Boolean, default=False)

    # update when user responds to their trip spot offer
    user_behavior = db.Column(db.String(20), default="NoResponse", nullable=False)

    def __repr__(self):
        trip = Trip.query.filter_by(id=self.trip_id).first()
        return '<Response to %r by %r>' % (
        trip.name + ' - ' + trip.departure_date.strftime('%m/%d/%Y'), self.user_email)


# class Waitlist(db.Model):
#     __tablename__ = 'waitlist'
#     id = db.Column(db.Integer, primary_key=True)
#     trip_id = db.Column(db.Integer, db.ForeignKey('trips.id', ondelete="CASCADE"), nullable=False)
#     trip = db.relationship('Trip', backref=db.backref('waitlist'))
#     # Yes, as relationship is an ORM concept that helps map the SQL table relationships to the object world,
#     # but it does not define them.
#     response_id = db.Column(db.String(36), db.ForeignKey('responses.id', ondelete="CASCADE"), nullable=False)
#     response = db.relationship('Response', backref=db.backref('waitlist'))
#     waitlist_rank = db.Column(db.Integer, nullable=False)
#
#     # indicates if moved off the waitlist
#     off = db.Column(db.Boolean, default=False)

    # want it to appear only for those where you can select a trip where lottery_completed is true but
    # some responses lottery_slot is false
