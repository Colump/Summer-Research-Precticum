# -*- coding: utf-8 -*-
import functools
from datetime import date, datetime, timedelta
from sqlite3 import Date
from flask import Flask, g, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import json
from jinja2 import Template
#from models import db, Station, StationState, StationStateResampled, weatherHistory
# Imports for Model/Pickle Libs
import pickle
import pandas as pd
import os, sys

import requests

def loadCredentials():
    """Load the credentials required for accessing the Weather API, Google Maps, etc.

    Returns a JSON object with the required credentials.
    Implemented in a method as Credential storage will be subject to change.
    """
    # Our credentials are just stored in a JSON file (for now)
    # This file is not saved to GitHub and is placed on each EC2 instance
    # by a team member.
    # Load the JSON file
    file = open(os.path.join(jtParentDir, 'journeytime.json'), 'r')
    credentials = json.load(file)
    file.close  # Can close the file now we have the data loaded...
    return credentials

# According to the article here:
#    -> https://towardsdatascience.com/simple-trick-to-work-with-relative-paths-in-python-c072cdc9acb9
# ... Python, if needing to use relative paths in order to make it easier to 
# relocate an application, one can determine the directory that a specific code
# module is located in using os.path.dirname(__file__). A full path name can then
# be constructed by using os.path.join()...
# Application Startup...
jtParentDir = os.path.dirname(os.path.dirname(__file__))
print("===================================================================")
print("JourneyTime: Application Start-up.")
print("             Parent Dir. is ->")
print("             " + str(jtParentDir) + "\n")


# Load our private credentials from a JSON file.  Nothing runs without these...
credentials = loadCredentials()

# Create our flask app.
# Static files are server from the 'static' directory
journeyTime = Flask(__name__, static_url_path='')

# In Flask, regardless of how you load your config, there is a 'config' object
# available which holds the loaded configuration values: The 'config' attribute
# of the Flask object
# The config is actually a subclass of a dictionary and can be modified just like
# any dictionary.  E.g. to update multiple keys at once you can use the dict.update()
# method:
#     journeyTime.config.update(
#         TESTING=True,
#         SECRET_KEY='192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'
#     )
#
# NOTE: Configuration Keys *** MUST BE ALL IN CAPITALS ***
#       (Ask me how I know...)
#
# This first line loads config from a Python object:
#journeyTime.config.from_object('config')
# This next one loads up our good old json object!!!
journeyTime.config.from_file(os.path.join(jtParentDir, 'journeyTime.json'), json.load)
# Following line disables some older stuff we don't use that is deprecated (and
# suppresses a warning about using it). Please just leave it hard-coded here.
journeyTime.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# As recommended here:
#     https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/#installation
# ... we used the "flask_sqlachemy" extension for Flask that adds support for
# SQLAlchemy to our application. It simplifies using SQLAlchemy with Flask by
#  providing useful defaults and extra helpers that make it easier to accomplish
# common tasks.
#
# Road to Enlightenment:
# Some of the things you need to know for Flask-SQLAlchemy compared to plain SQLAlchemy are:
# SQLAlchemy gives you access to the following things:
#   -> all the functions and classes from sqlalchemy and sqlalchemy.orm
#   -> a preconfigured scoped session called session
#   -> the metadata
#   -> the engine
#   -> a SQLAlchemy.create_all() and SQLAlchemy.drop_all() methods to create and drop tables according to the models.
#   -> a Model baseclass that is a configured declarative base.
# The Model declarative base class behaves like a regular Python class but has a
# query attribute attached that can be used to query the model. (Model and BaseQuery)
# We have to commit the session, but we don’t have to remove it at the end of the
# request, Flask-SQLAlchemy does that for us.
journeyTime.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://" \
            + journeyTime.config['DB_USER'] + ":" + journeyTime.config['DB_PASS'] \
            + "@" \
            + journeyTime.config['DB_SRVR'] + ":" + journeyTime.config['DB_PORT']\
            + "/" + journeyTime.config['DB_NAME'] + "?charset=utf8mb4"
#db.init_app(journeyTime)

# @app.route('/user/<id>')
# def get_user(id):
#     user = load_user(id) if not user:
#     abort(404)
#     return '<h1>Hello, %s</h1>' % user.name

# Example of setting status code:
# @app.route('/')
# def index():
#     return '<h1>Bad Request</h1>', 400

@journeyTime.route('/')
@journeyTime.route('/index.html')
def root():
    print(journeyTime.config)

    # This route simply serves 'static/index.html'
    return journeyTime.send_static_file('index.html')
    # This route renders a template from the template folder
    #return render_template('index.html', MAPS_API_KEY=journeyTime.config["MAPS_API_KEY"])

    ########################################################################
    #      vvvvv SqlAlchemy ORM DB Access reference notes BELOW vvvvv
    ########################################################################

    # If you want to access the 'session' using SQL Alchemy - you can do so as
    # follows:
    #   db.session. ...
    # Lots of the SQLAlchemy documentation seem to use the session object whereas
    # documentation on using models appears to be lighter.
    #
    # Station.query gives you a "BaseQuery"
    # To get actual data from a "BaseQuery" you just use .all(), .first(), etc.
    # db.session.query(Station) gives you a "BaseQuery" too (same??)
    # Station.query.all() gives you a result set
    # Station.query.join(StationState).all() seems to give me a result set
    #                                        ... but it's huge and takes forever
    #                                        and eventually just times out.
    # Following are examples of filter_by (gives a BaseQuery)
    # StationState.query.filter_by(stationId=1, weatherTime='2022-02-21 12:35:27')
    # Station.query.filter_by(stationName='SomeRandomStationName').first()
    # StationState.query.filter_by(stationId=1, weatherTime='2022-02-21 12:35:27').all()

    #-----------------------------------------------------------------------
    # Tested, working above this line, in progress below
    #-----------------------------------------------------------------------

    # We can filter results using filter_by
    # db.users.filter_by(name='Joe')
    # The same can be accomplished with filter, not using kwargs, but instead using
    # the '==' equality operator, which has been overloaded on the db.users.name object:
    # db.users.filter(db.users.name=='Joe')
    # db.users.filter(or_(db.users.name=='Ryan', db.users.country=='England'))

    ########################################################################
    #      ^^^^^ SqlAlchemy ORM DB Access reference notes ABOVE ^^^^^
    ########################################################################

##########################################################################################
##########################################################################################

# Flask will automatically remove database sessions at the end of the request or
# when the application shuts down:
@journeyTime.teardown_appcontext
def shutdown_session(exception=None):
    #db.session.remove()
    # sys.stdout.close()  # Close the file handle we have open
    # sys.stdout = sys.__stdout__ # Reset to the standard output
    pass

if __name__ == "__main__":
    # Reassign stdout so any debugs etc. generated by flask won't be lost when
    # running as a service on EC2
    # sys.stdout = open('dwmb_Flask_.logs', 'a')

    # print("DWMB Flask Application is starting: " + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    journeyTime.run(debug=False, host=journeyTime.config["FLASK_HOST"], port=journeyTime.config["FLASK_PORT"])