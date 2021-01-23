from sqlalchemy.sql import select, update, insert
from decimal import Decimal
from .models import *

userweight_floor = Decimal(0.5)
userweight_roof = Decimal(5.0)

def gotspot(user):
    if user.weight - Decimal(0.05) < userweight_floor:
            user.weight = userweight_floor
    else:
        user.weight = user.weight - Decimal(0.05)

#ACTION REQUIRED:
# def send_email(user):
    #fill in with code to send an email given a user as input (to be used in runlottery and WaitlistView's award_spot method)

#returns a list of the user emails that won the lottery for the trip associated w input id
def runlottery(self, id):
    print('Start')
    #get responses to the trip id inputted
    get_responses = select([Response.id, Response.user_email]).where(Response.trip_id == id)
    responses = self.session.execute(get_responses).fetchall()

    #get response ids and user emails from the list of tuples fetchall() returns
    response_ids = []
    user_emails = []
    #list of actual user rows to allow access to fields, (e.g. user.weight)
    users = []
    for r_id, email in responses:
        response_ids.append(r_id)
        user_emails.append(email)
        users.append(self.session.query(User).filter(User.email == email).first())

    #ACTION REQUIRED:
    #replace with the actual lottery mechanism to produce list of users that won a spot
    finalResults = {}
    for i in users:
        if not Response.car:
            currRank = 0
            currPerson = users[i]
            currWeight = users[i].weight
            currRank = random.randint(0,100) + currWeight #maybe make it out of total number of slots?
            nonCarFinalResults[currPerson] = currRank
        else: 
            currRank = 0
            currPerson = users[i]
            currWeight = users[i].weight
            currRank = random.randint(0,100) + currWeight #maybe make it out of total number of slots?
            carFinalResults[currPerson] = currRank
    nonCarSortedResults = sorted(nonCarFinalResults.items(), key=lambda x: x[1], reverse=True)
    CarSortedResults = sorted(carFinalResults.items(), key=lambda x: x[1], reverse=True)
    winner_ids =[]
    winner_emails = []
    noncar_winner_ids = []
    winner_emails = []
    car_winner_emails = []
    noncar_winner_emails = []
    waitlist_ids = []
    car_waitlist_ids = []
    noncar_waitlist_ids =[]
    waitlist_emails = []
    car_waitlist_emails = []
    noncar_waitlist_emails = []
    nc = Trip.noncar_cap
    n = Trip.car_cap
    for i in range(len(nonCarSortedResults)):
        if i < nc:
            winner_ids.append(i.id)
            winner_emails.append(i.email)
            noncar_winner_ids.append(i.id)
            noncar_winner_emails.append(i.email)
        else:
            waitlist_ids.append(i.id)
            noncar_waitlist_ids.append(i.id)
            waitlist_emails.append(i.email)
            noncar_waitlist_emails.append(i.email)
    for i in range(len(CarSortedResults)):
        if i < n:
            winner_ids.append(i.id)
            car_winner_ids.append(i.id)
            winner_emails.append(i.email)
            car_winner_emails.append(i.email)
        else:
            waitlist_ids.append(i.id)
            car_waitlist_ids.append(i.id)
            waitlist_emails.append(i.email)
            car_waitlist_emails.append(i.email)

    #update lottery_slot field in responses that won a spot
    for index in range(len(winner_ids)):
        self.session.query(Response).filter(Response.id == winner_ids[index]).update({Response.lottery_slot: True})
        user = self.session.query(User).filter(User.email == winner_emails[index]).first()
        gotspot(user)
    return winner_emails

    for i in range(len(car_winner_ids)):
        self.session.query(Response).filter(Response.id == car_waitlist_ids[index]).update({Response.lottery_slot: True})
        user = self.session.query(User).filter(User.email == winner_emails[index]).first()
        gotspot(user)
    return car_winner_emails
    



#updates user weights based on if they declined or did not show
def update_userweights(self, behavior, user_email):
    #get user weight from user email
    get_user_text = select([User.weight]).where(User.email == user_email)
    current_weight = self.session.execute(get_user_text).fetchone()
    user_weight = current_weight[0]

    #adjust weight according to behavior
    if behavior == "Declined":
        user_weight *= Decimal(0.9)
    elif behavior == "No Show":
        user_weight *= Decimal(0.8)
    elif behavior == "Confirmed":
        user_weight *= Decimal (0.95)
    #add did not get result

    #ensure weight doesn't drop to below 0.25
    if user_weight < userweight_floor:
        user_weight = userweight_floor
    if user_weight > userweight_roof:
        user_weight = userweight_roof

    self.session.query(User).update({User.weight: user_weight})
