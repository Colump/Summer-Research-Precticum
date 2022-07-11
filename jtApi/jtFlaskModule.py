# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from pickle import NONE
# jsonify serializes data to JavaScript Object Notation (JSON) format, wraps it
# in a Response object with the application/json mimetype.
from flask import flash, Flask, g, jsonify, make_response, redirect, request, render_template, url_for
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from forms import UserForm
from sqlalchemy import text, func
import json
from jinja2 import Template
from models import Agency, Calendar, CalendarDates, Routes, Shapes, Stop, StopTime, Trips, Transfers, JT_User
from jtUtils import query_results_as_compressed_csv
# Imports for Model/Pickle Libs
#import pickle
#import pandas as pd
import os, os.path, sys
import requests

# According to the article here:
#    -> https://towardsdatascience.com/simple-trick-to-work-with-relative-paths-in-python-c072cdc9acb9
# ... Python, if needing to use relative paths in order to make it easier to 
# relocate an application, one can determine the directory that a specific code
# module is located in using os.path.dirname(__file__). A full path name can then
# be constructed by using os.path.join()...
# Application Startup...
jtFlaskModParentDir = os.path.dirname(os.path.dirname(__file__))
print("===================================================================")
print("jtFlaskApp: Application Start-up.")
print("            Parent Dir. is ->")
print("            " + str(jtFlaskModParentDir) + "\n")

# Create our flask app.
# Static files are server from the 'static' directory
jtFlaskApp = Flask(__name__, static_url_path='')

# In Flask, regardless of how you load your config, there is a 'config' object
# available which holds the loaded configuration values: The 'config' attribute
# of the Flask object
# The config is actually a subclass of a dictionary and can be modified just like
# any dictionary.  E.g. to update multiple keys at once you can use the dict.update()
# method:
#     jtFlaskApp.config.update(
#         TESTING=True,
#         SECRET_KEY='192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'
#     )
#
# NOTE: Configuration Keys *** MUST BE ALL IN CAPITALS ***
#       (Ask me how I know...)
#
# This first line loads config from a Python object:
#jtFlaskApp.config.from_object('config')
# This next one loads up our good old json object!!!
jtFlaskApp.config.from_file(os.path.join(jtFlaskModParentDir, 'journeytime.json'), json.load)
# Following line disables some older stuff we don't use that is deprecated (and
# suppresses a warning about using it). Please just leave it hard-coded here.
jtFlaskApp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# As recommended here:
#     https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/#installation
# ... we used the "flask_sqlachemy" extension for Flask that adds support for
# SQLAlchemy to our application. It simplifies using SQLAlchemy with Flask by
# providing useful defaults and extra helpers that make it easier to accomplish
# common tasks.
#
# Road to Enlightenment:
# Some of the things you need to know for Flask-SQLAlchemy compared to plain SQLAlchemy are:
# SQLAlchemy gives you access to the following things:
#   -> all the functions and classes from sqlalchemy and sqlalchemy.orm
#   -> *** a preconfigured scoped session called session ***
#   -> the metadata
#   -> the engine
#   -> a SQLAlchemy.create_all() and SQLAlchemy.drop_all() methods to create and drop tables according to the models.
#   -> a Model baseclass that is a configured declarative base.
# The Model declarative base class behaves like a regular Python class but has a
# query attribute attached that can be used to query the model. (Model and BaseQuery)
# We have to commit the session, but we don’t have to remove it at the end of the
# request, Flask-SQLAlchemy does that for us.
jtFlaskApp.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://" \
            + jtFlaskApp.config['DB_USER'] + ":" + jtFlaskApp.config['DB_PASS'] \
            + "@" \
            + jtFlaskApp.config['DB_SRVR'] + ":" + jtFlaskApp.config['DB_PORT']\
            + "/" + jtFlaskApp.config['DB_NAME'] + "?charset=utf8mb4"

# 'csrf' gives us a mechanism for controlling csrf behaviour on forms (enabled by default)
csrf = CSRFProtect(jtFlaskApp)

db = SQLAlchemy(jtFlaskApp)

##########################################################################################
#  GROUP 1: BASIC HTML PAGES
##########################################################################################

# @app.route('/user/<id>')
# def get_user(id):
#     user = load_user(id) if not user:
#     abort(404)
#     return '<h1>Hello, %s</h1>' % user.name

# Example of setting status code:
# @app.route('/')
# def index():
#     return '<h1>Bad Request</h1>', 400

@jtFlaskApp.route('/')
@jtFlaskApp.route('/index.html')
def root():
#    print(jtFlaskApp.config)

    # This route simply serves 'static/index.html'
    #return jtFlaskApp.send_static_file('index.html')
    # This route renders a template from the template folder
    return render_template('index.html')
    # This route renders a template from the template folder
    #return render_template('index.html', MAPS_API_KEY=jtFlaskApp.config["MAPS_API_KEY"])

@jtFlaskApp.route('/documentation.html')
def documentation():
    # This route renders a template from the template folder
    return render_template('documentation.html')

@jtFlaskApp.route('/about.html')
def about():
    # This route renders a template from the template folder
    return render_template('about.html')

@jtFlaskApp.route('/TKTESTING.do', methods=['GET'])
def TKTESTING():
    # This route renders a template from the template folder
    return render_template('test_forms.html', form=UserForm())

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
#  GROUP 3: STRAIGHTFORWARD DATASET EXTRACTS
##########################################################################################

# endpoint for Agency model
@jtFlaskApp.route("/agency", defaults={'agency_name':None})
@jtFlaskApp.route("/agency/<agency_name>")
def get_agency(agency_name):
    agencyQuery = db.session.query(Agency)
    if agency_name != None:
        agencyQuery = agencyQuery.filter(Agency.agency_name ==  agency_name)
    agencyQuery = agencyQuery.order_by(text('agency_name asc'))

    # use serialize function to make a new list from the results
    # just one serialize function so no if statement
    json_list=[i.serialize() for i in agencyQuery.all()]
    return jsonify(json_list)

# endpoint for Calendar model
@jtFlaskApp.route("/calendar", defaults={'service_id':None})
@jtFlaskApp.route("/calendar/<service_id>")
def get_calendar(service_id):
    calendarQuery = db.session.query(Calendar)
    if service_id != None:
        calendarQuery = calendarQuery.filter(Calendar.service_id == service_id)
    calendarQuery = calendarQuery.order_by(text('service_id asc'))

    # use serialize to make a new list from the results
    # just one serialize functiomn so no if statement
    json_list=[i.serialize() for i in calendarQuery.all()]
    return jsonify(json_list)

# endpoint for CalendarDates
@jtFlaskApp.route("/calendardates", defaults={'date':None})
@jtFlaskApp.route("/calendardates/<date>")
def get_calendar_dates(date):
    calendardatesQuery = db.session.query(CalendarDates)
    if date != None:
        calendardatesQuery = calendardatesQuery.filter(CalendarDates.date == date)
    calendardatesQuery = calendardatesQuery.order_by(text('date asc'))

    # use serialize to make a new list from the results
    # just one serialize functiomn so no if statement
    json_list=[i.serialize() for i in calendardatesQuery.all()]
    return jsonify(json_list)

@jtFlaskApp.route("/routes", defaults={'route_id': None})
@jtFlaskApp.route("/routes/<route_id>")
def get_routes(route_id):
    routeQuery = db.session.query(Routes)
    if route_id != None:
        routeQuery = routeQuery.filter(Routes.route_id == route_id)
    routeQuery = routeQuery.order_by(text('route_id asc'))

    # haven't done the serialization for routes in models.py so this won't work yet
    # just copying the structure of the code above for get_stops function
    json_list=[i.serialize() for i in routeQuery.all()]
    return jsonify(json_list)

# # endpoint for Shapes
# @jtFlaskApp.route("/shapes", defaults={'shape_id':None})
# @jtFlaskApp.route("/shapes/<shape_id>")
# def get_shape(shape_id):
#     shapeQuery = db.session.query(Shapes)
#     if shape_id != None:
#         shapeQuery = shapeQuery.filter(Shapes.shape_id == shape_id)
#     shapeQuery = shape_id.order_by(text('shape_id asc'))

#     # use serialize to make a new list from the results
#     # just one serialize functiomn so no if statement
#     json_list=[i.serialize() for i in shapeQuery.all()]
#     return jsonify(json_list)

@jtFlaskApp.route("/stops", defaults={'stop_id': None})
@jtFlaskApp.route("/stops/<stop_id>")
def get_stops(stop_id):

    # .filter() and .filter_by:
    # Both are used differently;
    # .filters can write > < and other conditions like where conditions for sql,
    # but when referring to column names, you need to use class names and attribute
    # names.
    # .filter_by can pass conditions using python’s normal parameter passing method,
    # and no additional class names need to be specified when specifying column names.
    # The parameter name corresponds to the attribute name in the name class, but does
    # not seem to be able to use conditions such as > < etc..
    # Each has its own strengths.http://docs.sqlalchemy.org/en/rel_0_7&#8230;

    stopQuery = db.session.query(Stop)
    if stop_id != None:
        stopQuery = stopQuery.filter(Stop.stop_id == stop_id)
    stopQuery = stopQuery.order_by(text('stop_id asc'))

    # Use list comprehension (on the query results)... to build a new list.
    if stop_id != None:
        # Single stop selected, include stop_times detail
        json_list=[i.serialize() for i in stopQuery.all()]
    else:
        # All stops selected, omit stop_times detail
        json_list=[i.serialize_norels() for i in stopQuery.all()]

    return jsonify(json_list)

# # endpoint for StopTime model, should work because TK has written serialize function
# # within StopTime
# @jtFlaskApp.route("/stoptimes", defaults={'trip_id':None})
# @jtFlaskApp.route("/stoptimes/<trip_id>")
# def get_stop_times(trip_id):
#     stoptimeQuery = db.session.query(StopTime)
#     if trip_id != None:
#         stoptimeQuery = stoptimeQuery.filter(StopTime.trip_id == trip_id)
#     stoptimeQuery = stoptimeQuery.order_by(text('trip_id asc'))

#     # Use list comprehension (on the query results)... to build a new list.
#     # serialize is the only function within Routes so just return new serialized list
#     json_list=[i.serialize() for i in stoptimeQuery.all()]
#     return jsonify(json_list)
    
# endpoint for Transfers
@jtFlaskApp.route("/transfers", defaults={'from_stop_id':None})
@jtFlaskApp.route("/transfers/<from_stop_id>")
def get_transfers(from_stop_id):
    transferQuery = db.session.query(Transfers)
    if from_stop_id != None:
        transferQuery = transferQuery.filter(Transfers.from_stop_id == from_stop_id)
    transferQuery = transferQuery.order_by(text('from_stop_id asc'))

    # use serialize to make a new list from the results
    # just one serialize functiomn so no if statement
    json_list=[i.serialize() for i in transferQuery.all()]
    return jsonify(json_list)

# endpoint for Trips
# Trips is a large table - so we don't return the json directly to user in the
# resonse, instead we stream them a file with the json inside!
@jtFlaskApp.route("/trips", defaults={'route_id':None})
@jtFlaskApp.route("/trips/<route_id>")
def get_trips(route_id):
    tripsQuery = db.session.query(Trips)
    if route_id != None:
        tripsQuery = tripsQuery.filter(Trips.route_id == route_id)
    tripsQuery = tripsQuery.order_by(text('route_id asc'))

    # Trips is a large data set.  For small datasets we return the json directly
    # to the browser.  For larger datasets we return them as files.  Seeems
    # arbitrary - should we use a parameter to control? Discuss with team.
    return query_results_as_compressed_csv(tripsQuery, 'trips')

##########################################################################################
#  GROUP 3: COMPLEX QUERIES
##########################################################################################

@jtFlaskApp.route("/getStopsByRoute", methods=['GET'])
def get_stops_by_route():
    # /getStopsByRoute?rsn=<route_short_name>&jrny_dt=<yyyymmddhhmmss>&depstoplat=<departure_stop_lat>&depstoplont=<departure_stop_lon>
    # e.g.: https://journeyti.me/getStopsByRoute?rsn=17&jrny_dt=20220703165400&depstoplat=53.3351498&depstoplon=-6.2943145
    # Returns a list of stops on a particular route with lat/lon coordinates

    # We have three pieces of information from Google Directions:
    #   -> the date of the desired trip
    #   -> the route shortname
    #   -> the departure stop id

    # There are many routes with the same short name
    # There are many trips for each route
    # Trips only run on certain days, based on the service id

    # In 'traditional' SQL the query to find the trip id (which will then give
    # us our sequence of stops) is as follows:

    # SELECT stop_times.trip_id
    # FROM stop_times
    # INNER JOIN stops ON stop_times.stop_id=stops.stop_id
    # WHERE stop_times.trip_id IN (
    #     SELECT trips.trip_id FROM trips WHERE trips.route_id IN (
    #         SELECT routes.route_id FROM routes WHERE routes.route_short_name = '17'
    #     )
    # )
    # AND ABS(stops.stop_lat - 53.3351498) < 0.0000005
    # AND ABS(stops.stop_lon - -6.2943145) < 0.0000005
    # AND arrival_time < CAST('16:54:00' AS TIME)
    # ORDER BY arrival_time DESC
    # LIMIT 1;

    # We ASSUME google directions is hot enough to only suggest routes that are
    # running on the requested travel date (i.e. we don't cross check the calendar
    # or calendar_dates tables)

    args = request.args
    route_short_name = args.get('rsn')
    jrny_dt = args.get('jrny_dt')
    departure_stop_lat = args.get('depstoplat')
    departure_stop_lon = args.get('depstoplon')

    #jrny_date = datetime.strptime(jrny_dt[0:8], "%Y%m%d").date()
    jrny_time = datetime.strptime(jrny_dt[8:], "%H%M%S").time()

    if (route_short_name is None) or (jrny_dt is None) \
        or (departure_stop_lat) is None or (departure_stop_lon) is None:
        # required parameters missing
        # ALERT the LERTS!!!!!
        pass
    else:
        print ("OK - We're testing the route query!!")
        route_query = db.session.query(Routes.route_id)
        route_query = route_query.filter(Routes.route_short_name == route_short_name)
        route_query = route_query.order_by(text('route_id asc'))

        routes_for_shortname = []
        for r in route_query.all():
            routes_for_shortname.append(r.route_id)
        print('We found ' + str(len(routes_for_shortname)) + ' routes for this shortname')
        
        # We now how a list of route_ids, we can use that list to get a list of trips
        # for those routes...
        trips_query = db.session.query(Trips).filter(Trips.route_id.in_(routes_for_shortname))

        trips_for_routes = []
        for t in trips_query.all():
            trips_for_routes.append(t.trip_id)
        
        print('We found ' + str(len(trips_for_routes)) + ' trips for these routes')

        stop_times_query = db.session.query(StopTime.trip_id)
        stop_times_query = stop_times_query.join(Stop, Stop.stop_id == StopTime.stop_id)
        stop_times_query = stop_times_query.filter(StopTime.trip_id.in_(trips_for_routes))
        # Google directions are 7 decimal places (cm accurate), but the GTFSR stop
        # locations are 13 decimal places (nm accurate).  Use tolerance for comparison...
        stop_times_query = stop_times_query.filter(func.abs(Stop.stop_lat - departure_stop_lat) < 0.0000005)
        stop_times_query = stop_times_query.filter(func.abs(Stop.stop_lon - departure_stop_lon) < 0.0000005)
        stop_times_query = stop_times_query.filter(StopTime.arrival_time < jrny_time)
        stop_times_query = stop_times_query.order_by(text('arrival_time desc'))
        trip_id = stop_times_query.limit(1).all()

        # Following just useful for debugging...
        # stop_times_for_selected_stop_before_arrival_time = []
        # for i in stop_times_query.all():
        #     stop_times_for_selected_stop_before_arrival_time.append(i.trip_id)
        # print('We found ' + str(len(stop_times_for_selected_stop_before_arrival_time)) + ' stops before the arrival time.')

        # At this point we've identified the * most likely * trip_id for the
        # requested journey! Sweet - now we just return the list of stops for this
        # trip_id!

        stops_for_trip_query = db.session.query(StopTime)
        stops_for_trip_query = stops_for_trip_query.filter(StopTime.trip_id == trip_id[0][0])

        # All stops selected, omit stop_times detail
        json_list=[st.serialize() for st in stops_for_trip_query.all()]

    return jsonify(json_list)

##########################################################################################
#  GROUP 4: JT_UI SUPPORT FUNCTIONS
##########################################################################################

@jtFlaskApp.route("/login.do", methods=['POST'])
def login():
    """For the supplier username and hashed password, attempt login

    Returns
    """
    resp = jsonify(success=True)
    resp.status_code = 200  # Success
    #resp.status_code = 401  # Unauthorized
    return resp

@jtFlaskApp.route("/get_profile_picture.do", methods=['GET'])
def get_profile_picture():
    args = request.args
    gpp_username = args.get('username')
    user = db.session.query(JT_User).filter_by(username=gpp_username).one()

    response = make_response(user.profile_picture)
    extension = os.path.splitext(user.profile_picture_filename)[1][1:].strip() 
    response.headers.set('Content-Type', 'image/' + extension)
    return response

@jtFlaskApp.route("/register.do", methods=['POST'])
@csrf.exempt
def register():
    #form = UserForm(CombinedMultiDict((request.files, request.form)))  # see forms.py
    #   -> 'request.form' only contains form input data.
    #   -> 'request.files' contains file upload data.
    # You need to pass the combination of both to the form. Since a form inherits
    # from Flask-WTF's Form (now called FlaskForm), it will handle this automatically
    # if you don't pass anything to the form!!
    user_form = UserForm(meta={'csrf': False})  # see forms.py

    # 'validate_on_submit' ensures BOTH post AND form checks passed!
    valid = user_form.validate_on_submit()
    if valid:
        print("username ->", user_form.username.data, "-", type(user_form.username.data))
        print("password_hash ->", user_form.password_hash.data, "-", type(user_form.password_hash.data))
        print("nickname ->", user_form.nickname.data, "-", type(user_form.nickname.data))
        print("colour ->", user_form.colour.data, "-", type(user_form.colour.data))
        print("profile_picture ->", user_form.profile_picture.data, "-", type(user_form.profile_picture.data))
        new_user = JT_User()
        user_form.populate_obj(new_user)
        # It appears the 'populate_obj' doesn't handle files well - so pos
        # populate_obj we do file fields manually...
        if user_form.profile_picture.data.filename:
            new_user.profile_picture_filename = user_form.profile_picture.data.filename
            new_user.profile_picture = user_form.profile_picture.data.read()
        else:
            new_user.profile_picture_filename = None
            new_user.profile_picture = None

        db.session.add(new_user)
        db.session.flush()
        db.session.commit()

        # filename = secure_filename(f.filename)
        flash('SUCCESS')
        return render_template('test_forms.html', form=user_form)
    else:
        # 'form.errors' is only populated when you call either validate() or
        # validate_on_submit.  So you can't check this in advance!
        # Log any errors in the server log (while devloping at least...)
        print("ERRORS Detected on form:")
        for key in user_form.errors:
            for message in user_form.errors[key]:
                print("\t" + str(key)+ " : " + message)

    response = make_response(render_template('test_forms.html', form=user_form))
    response.headers.set('Access-Control-Allow-Origin', '*')
    return response

##########################################################################################
#  END: CLOSE APPLICATION
##########################################################################################

# Flask will automatically remove database sessions at the end of the request or
# when the application shuts down:
@jtFlaskApp.teardown_appcontext
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
    jtFlaskApp.run(debug=False, host=jtFlaskApp.config["FLASK_HOST"], port=jtFlaskApp.config["FLASK_PORT"])
