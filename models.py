from app import db
from sqlalchemy import CheckConstraint

class User(db.Model):
    __tablename__ = 'user'
    # Table columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    fullname = column_property(first_name+" "+last_name)
    weight = dbColumn(db.Float(1, 10), nullable=False, default=1.0)

    # String representation of this object (for logging)
    def __repr__(self):
        return '<User %r>' % self.username

# Define an arbitrary amount of these classes below...

class Trips(db.Model):
    __tablename__ = 'trips'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    description = db.Column(db.String(500))
    signup_deadline = db.Column(db.DateTime(timezone=False), nullable=False)
    price = db.Column(db.Float(3, 2), nullable=False)
    car_cap = db.Column(db.Integer)
    noncar_cap = db.Column(db.Integer, nullable=False)

    # String representation of this object (for logging)
    def __repr__(self):
        return '<Trip %r>' % self.name

class Responses(db.Model):
    __tablename__ = 'reponses'
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    trips = db.relationship('Trips', backref = db.backref('responses'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trips = db.relationship('User', backref = db.backref('responses'))
    financial_aid= db.Column(db.Boolean)
    car = db.Column(db.Boolean)
