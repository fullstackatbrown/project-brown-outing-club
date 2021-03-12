# Very Simple Flask Webapp

Disclaimer: this starter project is not modular and does not use best practices for scalability. This should be used for
speedy, simple dev, or learning.

This template uses the SQLAlchemy ORM configured to use mariaDB, however, this connection can be easily interchanged
with another.

## Setting Up
#### Starting venv
Mac: 
`. venv/bin/activate`

Windows: 
`> venv\Scripts\activate`

#### Installing dependencies
Inside your virtual env, run: 
`pip install -r requirements.txt`

#### Loading .env File
Find the demo .env file [here](https://drive.google.com/file/d/1k8gmwnB7f437M31O55UKAT-5e8AefVvZ/view) and put it in 
your toplevel project directory

#### Running the app
`export FLASK_APP=boc/__init__.py`
`flask run`

## Additional Resources
https://flask.palletsprojects.com/en/1.1.x/quickstart/

https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/

TODO: If creating and destroying the database is not a suitable substitution for true migration, implement [alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html) 
([alternative resource](https://www.compose.com/articles/schema-migrations-with-alembic-python-and-postgresql/)).

## TODO

* Fetch RSVP list in .csv
* Repair run_lottery
* 