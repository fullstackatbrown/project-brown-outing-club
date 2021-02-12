import trips

def dummy_users(): # put into a test file 
    for i in range(50):
        db.session.add(User(email = str(uuid.uuid4())+"@brown.edu", auth_id = int(uuid.uuid4()), weight = random.randint(-2,2)))

    db.session.commit()

def dummy_responses():
    for i in range(50):
        if i < 25: 
            db.session.add(Response(email = str(uuid.uuid4())+"@brown.edu", auth_id = int(uuid.uuid4())))
        else: 
            db.session.add(Response(email = str(uuid.uuid4())+"@brown.edu", auth_id = int(uuid.uuid4()), financial_aid = True))

def dummy_waitlist()
    for i in range(50):
        db.session.add(Waitlist(waitlist_rank = i))