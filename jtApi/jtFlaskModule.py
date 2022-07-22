# -*- coding: utf-8 -*-
from datetime import date, datetime, timezone
# jsonify serializes data to JavaScript Object Notation (JSON) format, wraps it
# in a Response object with the application/json mimetype.
from flask import flash, Flask, g, jsonify, make_response, redirect, request, render_template, url_for
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from forms import *
from jinja2 import Template
import json
from jt_utils import get_available_end_to_end_models, get_stops_by_route, predict_journey_time, \
                     query_results_as_json, query_results_as_compressed_csv, time_rounded_to_hrs_mins_as_string, \
                     JourneyPrediction, StepStop
import logging
from models import Agency, Calendar, CalendarDates, Routes, Shapes, Stop, StopTime, Trips, Transfers, JT_User
import os, os.path
from pickle import NONE
from sqlalchemy import text, func

# Imports for Model/Pickle Libs
#import pandas as pd

CONST_DLTYPE  = 'dltype'
CONST_JSONFILE = 'json'
CONST_CSVFILE  = 'csv'

# In a fully configured environment, a scheduled job updates this list each morning
# at 03:30. It can also be updated manually by calling the URL: /update_model_list.do
AVAILABLE_MODEL_ROUTE_SHORTNAMES = []

logging.basicConfig(format='%(levelname)s: %(message)s', encoding='utf-8', level=os.environ.get("LOGLEVEL", "INFO"))
log = logging.getLogger(__name__)  # Standard naming...

# According to the article here:
#    -> https://towardsdatascience.com/simple-trick-to-work-with-relative-paths-in-python-c072cdc9acb9
# ... Python, if needing to use relative paths in order to make it easier to 
# relocate an application, one can determine the directory that a specific code
# module is located in using os.path.dirname(__file__). A full path name can then
# be constructed by using os.path.join()...
# Application Startup...
jtFlaskModDir = os.path.dirname(__file__)
jtFlaskModParentDir = os.path.dirname(jtFlaskModDir)
log.info("===================================================================")
log.info("jtFlaskApp: Application Start-up.")
log.info("            Module Directory is -> " + str(jtFlaskModDir))
log.info("            Parent Dir. is -> " + str(jtFlaskModParentDir))

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

@jtFlaskApp.route('/invalid_dataset.html')
def invalid_dataset():
    # This route renders a template from the template folder
    return render_template('invalid_dataset.html')

@jtFlaskApp.route('/about.html')
def about():
    # This route renders a template from the template folder
    return render_template('about.html')

@jtFlaskApp.route('/TKTESTING.do', methods=['GET'])
def TKTESTING():
    # This route renders a template from the template folder
    return render_template('test_forms.html', form=UpdateUserForm())

@jtFlaskApp.route('/downloads.html')
def downloads():
    return render_template ('downloads.html')

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

def get_dataset_in_format_requested(request, query, filename):
    args = request.args
    download_type = args.get(CONST_DLTYPE)  # will be blank sometimes...

    if download_type == CONST_CSVFILE:
        # User requested everything as a .csv file. This is our preferred
        # option (minimum bandwidth), serve the user a compressed .csv file
        response = query_results_as_compressed_csv(query, filename)
    else:
        # User requested everything as EITHER straighforward json or the json
        # returned as an attachement. Some of the tables are large, so we do
        # some checks before completing the request...

        # Find out how many records are involved...
        total_records = query.count()
        dl_row_limit_json        = int(jtFlaskApp.config['DOWNLOAD_ROW_LIMIT_JSON'])
        dl_row_limit_json_attach = int(jtFlaskApp.config['DOWNLOAD_ROW_LIMIT_JSON_ATTACHMENT'])

        # NOTE: For the data we have at the moment, every 1,000,000 records
        # corresponds (quite roughly) to 100MB of filesize.  So... if we want
        # a 10MB limit, this corresponds to circa 100,000 rows

        if download_type == CONST_JSONFILE:
            # User requested everything as a .json file.
            if total_records > dl_row_limit_json_attach:
                #======================================================================================
                # WE'RE GONNA LIMIT THE NUMBER OF ROWS RETURNED - HOW DO WE TELL THE USER!!!!!!!???????
                #======================================================================================
                return query_results_as_json(query.limit(dl_row_limit_json_attach), filename, limit_exceeded=True)
            else:
                return query_results_as_json(query, filename)
        else:
            # User wants JSON direct to the screen (not as an attached file)
            if total_records > dl_row_limit_json:
                #======================================================================================
                # WE'RE GONNA LIMIT THE NUMBER OF ROWS RETURNED - HOW DO WE TELL THE USER!!!!!!!???????
                #======================================================================================
                list = []
                dl_lim_json        = jtFlaskApp.config['DOWNLOAD_ROW_LIMIT_JSON']
                dl_lim_json_attach = jtFlaskApp.config['DOWNLOAD_ROW_LIMIT_JSON_ATTACHMENT']
                warning = {}
                warning['filesize_warning'] = {}
                warning['filesize_warning']['warning'] = 'WARNING'
                warning['filesize_warning']['description'] = 'The number of records in this extract exceeds the current streamed .json file limit'
                warning['filesize_warning']['limits1'] = 'A maximum of ' + dl_lim_json + ' records can be delivered directly to a clients browswer'
                warning['filesize_warning']['limits2'] = 'A maximum of ' + dl_lim_json_attach + ' records can be delivered as a .json file attachment'
                warning['filesize_warning']['limits3'] = 'There is currently no limit on filesizes downloaded as compressed .csv.gz'
                list.append(warning)

                list.append([row.serialize() for row in query.limit(dl_row_limit_json).all()])
                response = jsonify(list)
            else:
                # Requested data set is under the row limit, send it!
                response = jsonify([row.serialize() for row in query.all()])
    
    return response

# Endpoint for Agency model
# user can use EITHER:
#   'agency name' as a key (to get json response for just one agency)
# -OR-
#   supply argument '?dltype' ('json' or 'csv') to download content as a file
@jtFlaskApp.route("/agency", defaults={'agency_name':None})
@jtFlaskApp.route("/agency/<agency_name>")
def get_agency(agency_name):
    agencyQuery = db.session.query(Agency)

    response = None
    if agency_name != None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        agencyQuery = agencyQuery.filter(Agency.agency_name ==  agency_name)
        agencyQuery = agencyQuery.order_by(text('agency_name asc'))

        response = jsonify([row.serialize() for row in agencyQuery.all()]) # ".one" causes a TypeError, ".all" returns just the specified agency
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = get_dataset_in_format_requested(request, agencyQuery, 'agency')

    return response

# endpoint for Calendar model
@jtFlaskApp.route("/calendar", defaults={'service_id':None})
@jtFlaskApp.route("/calendar/<service_id>")
def get_calendar(service_id):
    calendarQuery = db.session.query(Calendar)
 
    response = None
    if service_id != None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        calendarQuery = calendarQuery.filter(Calendar.service_id == service_id)
        calendarQuery = calendarQuery.order_by(text('service_id asc'))

        response = jsonify([row.serialize() for row in calendarQuery.all()]) # ".one" causes a TypeError, ".all" returns just the specified agency
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = get_dataset_in_format_requested(request, calendarQuery, 'calendar')

    return response

# endpoint for CalendarDates
@jtFlaskApp.route("/calendardates", defaults={'date':None})
@jtFlaskApp.route("/calendardates/<date>")
def get_calendar_dates(date):
    calendardatesQuery = db.session.query(CalendarDates)

    response = None
    if date != None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        calendardatesQuery = calendardatesQuery.filter(CalendarDates.date == date)
        calendardatesQuery = calendardatesQuery.order_by(text('date asc'))

        response = jsonify([row.serialize() for row in calendardatesQuery.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = get_dataset_in_format_requested(request, calendardatesQuery, 'calendar_dates')

    return response

@jtFlaskApp.route("/routes", defaults={'route_id': None})
@jtFlaskApp.route("/routes/<route_id>")
def get_routes(route_id):
    routeQuery = db.session.query(Routes)

    response = None
    if route_id != None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        routeQuery = routeQuery.filter(Routes.route_id == route_id)
        routeQuery = routeQuery.order_by(text('route_id asc'))

        response = jsonify([row.serialize() for row in routeQuery.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = get_dataset_in_format_requested(request, routeQuery, 'routes')

    return response

# endpoint for Shapes
@jtFlaskApp.route("/shapes", defaults={'shape_id':None})
@jtFlaskApp.route("/shapes/<shape_id>")
def get_shape(shape_id):
    shapeQuery = db.session.query(Shapes)

    response = None
    if shape_id != None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        shapeQuery = shapeQuery.filter(Shapes.shape_id == shape_id)
        shapeQuery = shape_id.order_by(text('shape_id asc'))

        response = jsonify([row.serialize() for row in shapeQuery.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = get_dataset_in_format_requested(request, shapeQuery, 'shapes')

    return response

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

    response = None
    if stop_id != None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        stopQuery = stopQuery.filter(Stop.stop_id == stop_id)
        stopQuery = stopQuery.order_by(text('stop_id asc'))

        response = jsonify([row.serialize() for row in stopQuery.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = get_dataset_in_format_requested(request, stopQuery, 'stops')

    return response

# endpoint for StopTime model, should work because TK has written serialize function
# within StopTime
@jtFlaskApp.route("/stoptimes", defaults={'trip_id':None})
@jtFlaskApp.route("/stoptimes/<trip_id>")
def get_stop_times(trip_id):
    stoptimeQuery = db.session.query(StopTime)

    response = None
    if trip_id != None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        stoptimeQuery = stoptimeQuery.filter(StopTime.trip_id == trip_id)
        stoptimeQuery = stoptimeQuery.order_by(text('trip_id asc'))

        response = jsonify([row.serialize() for row in stoptimeQuery.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = get_dataset_in_format_requested(request, stoptimeQuery, 'stoptimes')

    return response
    
# endpoint for Transfers
@jtFlaskApp.route("/transfers", defaults={'from_stop_id':None})
@jtFlaskApp.route("/transfers/<from_stop_id>")
def get_transfers(from_stop_id):
    transferQuery = db.session.query(Transfers)

    response = None
    if from_stop_id != None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        transferQuery = transferQuery.filter(Transfers.from_stop_id == from_stop_id)
        transferQuery = transferQuery.order_by(text('from_stop_id asc'))

        response = jsonify([row.serialize() for row in transferQuery.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = get_dataset_in_format_requested(request, transferQuery, 'transfers')

    return response

# endpoint for Trips
# Trips is a large table - so we don't return the json directly to user in the
# resonse, instead we stream them a file with the json inside!
@jtFlaskApp.route("/trips", defaults={'trip_id':None})
@jtFlaskApp.route("/trips/<trip_id>")
def get_trips(trip_id):
    tripsQuery = db.session.query(Trips)

    response = None
    if trip_id != None:
        # Simplest use case - user requires information on single trip
        # No option to download this as a file (currently) - just return requested
        # information as json.
        tripsQuery = tripsQuery.filter(Trips.trip_id == trip_id)

        response = jsonify([row.serialize() for row in tripsQuery.all()]) # ".one" causes a TypeError, ".all" returns just the specified trip
    else:
        # No specific trip requested - decide how (and exactly what) to return
        # to the user...
        response = get_dataset_in_format_requested(request, tripsQuery, 'trips')

    return response


##########################################################################################
#  GROUP 3: COMPLEX QUERIES
##########################################################################################

# ??????????????? Should I bother updating this to accept a POSTed json input??????
# Was only used for demo purposes...

@jtFlaskApp.route("/getStopsByShortname", methods=['GET'])
def get_stops_by_shortname():
    """Returns an ordered list of stops for a selected Route Shortname (a.k.a. 'Line_Id')
    
    Each route_shortname can potentially refer to multiples routes.
    Each route can refer to multiple trips.
    The user has chosen departure datetime...
    ...Starting from a chosen stop (identified by `departure lat/lon coordinates)
    ...Arriving at a second chosen stop (identified by `arrival' lat/lon coordinates)
    If no trip is found, no stops are returned.
    """
    # /getStopsByRoute?rsn=<route_short_name>&jrny_dt=<yyyymmddhhmmss>
    #     &depstoplat=<departure_stop_lat>&depstoplon=<departure_stop_lon>
    #     &arrstoplat=<arrival_stop_lat>&arrstoplon=<arrival_stop_lon>
    # e.g.: https://journeyti.me/getStopsByRoute?rsn=17&jrny_dt=20220703165400&depstoplat=53.3351498&depstoplon=-6.2943145

    # We have three pieces of information from Google Directions:
    #   -> the route shortname
    #   -> the datetime of the desired trip
    #   -> the departure stop lat/lon
    args = request.args
    route_short_name = args.get('rsn')
    jrny_dt = args.get('jrny_dt')  
    departure_stop_lat = args.get('depstoplat')
    departure_stop_lon = args.get('depstoplon')
    arrival_stop_lat = args.get('arrstoplat')
    arrival_stop_lon = args.get('arrstoplon')

    #jrny_date = datetime.strptime(jrny_dt[0:8], "%Y%m%d").date()
    jrny_time = datetime.strptime(jrny_dt[8:], "%H%M%S").time()

    step_stops = get_stops_by_route(db, route_short_name, jrny_time, \
        departure_stop_lat, departure_stop_lon, \
        arrival_stop_lat, arrival_stop_lon)
    
    return jsonify([ss.serialize() for ss in step_stops])


# TESTING: Simple endpoint to allow submission of json and return it to the user...
@jtFlaskApp.route('/json_parrot.do', methods=['POST'])
@csrf.exempt
def json_parrot():
    return jsonify(request.json)


# Simple endpoint to submission of json and return it to the user...
@jtFlaskApp.route('/update_model_list.do', methods=['GET'])
# The following decorator means this function will run once just before the first
# request is processed (NOT on startup, just before the first request)
@jtFlaskApp.before_first_request
def update_model_list():
    AVAILABLE_MODEL_ROUTE_SHORTNAMES = get_available_end_to_end_models()

    return jsonify(AVAILABLE_MODEL_ROUTE_SHORTNAMES)


@jtFlaskApp.route('/get_journey_time.do', methods=['POST'])
@csrf.exempt
def get_journey_time():
    resp = get_failure_response()  # Assume failure

    # If no json submitted - this is a dud request...
    if request.json:
        # A valid prediction request will confirm to the specification laid out
        # in JourneyPredictionRequestSpec.json.  We can conveniently get the JSON
        # POST'ed to the server (as a python dictionary) using:
        prediction_request_json = request.json
        print("get_journey_time.do: request.json type is -> ", type(request.json))

        # The incoming json should contain one (or more) routes.  Each route will
        # be made up of steps, where each step is a seperate bus journey for that
        # route.
        log.debug('looping over routes')
        for route in prediction_request_json['routes']:
             # def JourneyPrediction():
            no_of_steps_this_route = len(route['steps'])
            print("\tno_of_steps_this_route -> " + str(no_of_steps_this_route))

            print('\tlooping over steps')
            for step in route['steps']:
                
                planned_time_s  = step['duration']['value']
                route_shortname = step['transit_details']['line']['short_name']
                route_shortname_pickle_exists = True if route_shortname in AVAILABLE_MODEL_ROUTE_SHORTNAMES else False

                # Google Directions API times are 'timestamp' expressed in seconds
                # elapsed since the Unix epoch, 1970-01-01 00:00:00 UTC
                # Using datetime to construct our date seems to nicely cater
                # for daylight savings times, differences from UTC etc. ...
                planned_departure_datetime = datetime.fromtimestamp(step['transit_details']['departure_time']['value'])
                print("\t\tdatatime converted from google epoch based timestamp -> " + str(planned_departure_datetime))

                # Extend the json to contain stop-by-stop route information...
                # NOTE The mappings between Googles supplied data and the GTFSR
                #      fields are *inferred* - I could not find documentation
                #      guaranteeing the mappings.
                route_name = step['transit_details']['line']['name']
                route_short_name = step['transit_details']['line']['short_name']
                stop_headsign = step['transit_details']['headsign']
                departure_time = datetime.fromtimestamp(step['transit_details']['departure_time']['value']).time()
                departure_stop_name = step['transit_details']['departure_stop']['name']
                departure_stop_lat = step['transit_details']['departure_stop']['location']['lat']
                departure_stop_lon = step['transit_details']['departure_stop']['location']['lng']
                arrival_stop_name = step['transit_details']['arrival_stop']['name']
                arrival_stop_lat = step['transit_details']['arrival_stop']['location']['lat']
                arrival_stop_lon = step['transit_details']['arrival_stop']['location']['lng']

                step_stops = get_stops_by_route(db, route_name, route_short_name, stop_headsign, departure_time, \
                    departure_stop_name, departure_stop_lat, departure_stop_lon, \
                    arrival_stop_name, arrival_stop_lat, arrival_stop_lon)
                print("\t\twe found the following number of step_stops -> " + str(len(step_stops)))

                # Bundle everything we need to make a prediction into a convenient
                # object. We can then pass this object to the prediction routine
                journey_pred = JourneyPrediction( \
                    route_shortname, route_shortname_pickle_exists, \
                    planned_time_s, planned_departure_datetime, step_stops)

                # Call a function to get the predicted journey time for this step.
                journey_pred = predict_journey_time(journey_pred)

                # Extend the json to contain the prediction information...
                predicted_duration = journey_pred.get_predicted_duration_s()
                step['predicted_duration'] = {}
                step['predicted_duration']['text'] = time_rounded_to_hrs_mins_as_string(predicted_duration)
                step['predicted_duration']['value'] = predicted_duration

                # Where possible - extend the json to contain the step_stops information
                if len(step_stops) > 0:
                    step['stop_sequence'] = {}
                    step['stop_sequence']['stops'] = []
                    for step_stop in step_stops:
                        step_stop_dict = {}
                        step_stop_dict['stop_id'] = step_stop.get_stop().stop_id
                        step_stop_dict['name'] = step_stop.get_stop().stop_name
                        step_stop_dict['location'] = {}
                        step_stop_dict['location']['lat'] = step_stop.get_stop().stop_lat
                        step_stop_dict['location']['lng'] = step_stop.get_stop().stop_lon
                        step_stop_dict['sequence_no'] = step_stop.get_stop_sequence()
                        step_stop_dict['dist_from_last_stop'] = step_stop.get_shape_dist_traveled()
                        step['stop_sequence']['stops'].append(step_stop_dict)

        resp = jsonify(prediction_request_json)

    return resp

##########################################################################################
#  GROUP 4: JT_UI RESTful SUPPORT FUNCTIONS
##########################################################################################

def get_success_response():
    resp = jsonify(success=True)
    resp.status_code = 200  # Success
    return resp

def get_failure_response():
    resp = jsonify(success=False)
    resp.status_code = 401  # Unauthorized
    return resp

def log_errors(errors):
    print("ERRORS Detected on form:")
    for key in errors:
        for message in errors[key]:
            print("\t" + str(key)+ " : " + message)
    return


@jtFlaskApp.route("/check_username_available.do", methods=['POST'])
@csrf.exempt
def check_username_available():
    """Check if the supplied username is available

    Returns RESTful success/fail
    """
    check_form = CheckUsernameAvailableForm(meta={'csrf': False})  # see forms.py

    resp = get_failure_response()  # Assume not available
    # 'validate_on_submit' ensures BOTH post AND form checks passed!
    if check_form.validate_on_submit():
        try:
            desired_username = check_form.username.data
            count_users_with_username = db.session.query(JT_User).filter_by(username=desired_username).count()
            if count_users_with_username == 0:
                resp = get_success_response()
        except:
            pass

    return resp

@jtFlaskApp.route("/register.do", methods=['POST'])
@csrf.exempt
def register():
    #form = UserForm(CombinedMultiDict((request.files, request.form)))  # see forms.py
    #   -> 'request.form' only contains form input data.
    #   -> 'request.files' contains file upload data.
    # You need to pass the combination of both to the form. Since a form inherits
    # from Flask-WTF's Form (now called FlaskForm), it will handle this automatically
    # if you don't pass anything to the form!!
    reg_form = RegisterForm(meta={'csrf': False})  # see forms.py

    resp = get_failure_response()  # Assume failure
    if reg_form.validate_on_submit():
        try:
            new_user = JT_User()
            reg_form.populate_obj(new_user)

            db.session.add(new_user)
            db.session.flush()
            db.session.commit()

            resp = get_success_response()
        except:                   # * see comment below
            db.session.rollback()
    else:
        # 'form.errors' is only populated when you call either validate() or
        # validate_on_submit.  So you can't check this in advance!
        # Log any errors in the server log (while devloping at least...)
        log_errors(reg_form.errors)

    return resp

@jtFlaskApp.route("/login.do", methods=['POST'])
@csrf.exempt
def login():
    """For the supplied username and hashed password, attempt login

    Returns
    """
    login_form = LoginForm(meta={'csrf': False})  # see forms.py

    resp = get_failure_response()  # Assume failure
    if login_form.validate_on_submit():
        try:
            jt_user = db.session.query(JT_User).filter_by(username=login_form.username.data).one()
            if jt_user.password_hash == login_form.password_hash.data:
                resp = get_success_response()
        except:                   # * see comment below
            pass
    else:
        log_errors(login_form.errors)

    return resp

@jtFlaskApp.route("/update_user.do", methods=['POST'])
@csrf.exempt
def update_user():
    #form = UserForm(CombinedMultiDict((request.files, request.form)))  # see forms.py
    #   -> 'request.form' only contains form input data.
    #   -> 'request.files' contains file upload data.
    # You need to pass the combination of both to the form. Since a form inherits
    # from Flask-WTF's Form (now called FlaskForm), it will handle this automatically
    # if you don't pass anything to the form!!
    upd_usr_form = UpdateUserForm(meta={'csrf': False})  # see forms.py

    resp = get_failure_response()  # Assume failure
    if upd_usr_form.validate_on_submit():
        try:
            # print("username ->", upd_usr_form.username.data, "-", type(upd_usr_form.username.data))
            # print("password_hash ->", upd_usr_form.password_hash.data, "-", type(upd_usr_form.password_hash.data))
            # print("nickname ->", upd_usr_form.nickname.data, "-", type(upd_usr_form.nickname.data))
            # print("colour ->", upd_usr_form.colour.data, "-", type(upd_usr_form.colour.data))
            # print("profile_picture ->", upd_usr_form.profile_picture.data, "-", type(upd_usr_form.profile_picture.data))
            jt_user = db.session.query(JT_User).filter_by(username=upd_usr_form.username.data).one()
            upd_usr_form.populate_obj(jt_user)  # Overwrite old values
            # It appears the 'populate_obj' doesn't handle files well - so pos
            # populate_obj we do file fields manually...
            if upd_usr_form.profile_picture.data.filename:
                jt_user.profile_picture_filename = upd_usr_form.profile_picture.data.filename
                jt_user.profile_picture = upd_usr_form.profile_picture.data.read()
            else:
                jt_user.profile_picture_filename = None
                jt_user.profile_picture = None

            db.session.flush()
            db.session.commit()

            resp = get_success_response()
        except:                   # * see comment below
            db.session.rollback()

    else:
        log_errors(upd_usr_form.errors)

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