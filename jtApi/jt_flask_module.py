# -*- coding: utf-8 -*-
"""Main Flask Module for the Journeyti.me Web Application
"""

# Standard Library Imports
from datetime import datetime
import json
import logging
import os
import os.path
import pickle
import traceback

# Related Third Party Imports
# jsonify serializes data to JavaScript Object Notation (JSON) format, wraps it
# in a Response object with the application/json mimetype.
from flask import Flask, jsonify, make_response, request, render_template
#from flask import flash
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, DBAPIError

# Local Application Imports
from forms import CheckUsernameAvailableForm, LoginForm, RegisterForm, UpdateUserForm
from jt_utils import get_available_end_to_end_models, get_stops_by_route, \
                     get_valid_route_shortnames, predict_journey_time, \
                     query_results_as_json, query_results_as_compressed_csv, \
                     time_rounded_to_hrs_mins_as_string, \
                     JourneyPrediction
from models import Agency, Calendar, CalendarDates, Routes, \
    Shapes, Stop, StopTime, Trips, Transfers, JT_User

# Imports for Model/Pickle Libs
#import pandas as pd

CONST_DLTYPE  = 'dltype'
CONST_JSONFILE = 'json'
CONST_CSVFILE  = 'csv'

# In a fully configured environment, a scheduled job updates this list each morning
# at 03:30. It can also be updated manually by calling the URL: /update_model_list.do
AVAILABLE_MODEL_ROUTE_SHORTNAMES = []
# There are bus operators in the Dublin Region not contained in the Transport For
# Ireland GTFS data set (e.g. the Swords Express company that operates 9 bus routes
# in the Dublin area).  We keep a list of 'valid' route shortnames in memory (updated
# each morning after thee daily download).  This was we can easily identify routes
# that our prediction service supports - and those it doesn't.
VALID_ROUTE_SHORTNAMES = []

logging.basicConfig(
    format='%(levelname)s: %(message)s',
    encoding='utf-8',
    level=os.environ.get("LOGLEVEL", "INFO")
    )
log = logging.getLogger(__name__)  # Standard naming...

# According to the article here:
#    -> https://towardsdatascience.com
#       /simple-trick-to-work-with-relative-paths-in-python-c072cdc9acb9
# ... Python, if needing to use relative paths in order to make it easier to
# relocate an application, one can determine the directory that a specific code
# module is located in using os.path.dirname(__file__). A full path name can then
# be constructed by using os.path.join()...
# Application Startup...
jt_flask_mod_dir = os.path.dirname(__file__)
jt_flask_mod_parent_dir = os.path.dirname(jt_flask_mod_dir)
log.info("===================================================================")
log.info("jt_flask_app: Application Start-up.")
log.info("              Module Directory is -> %s", jt_flask_mod_dir)
log.info("              Parent Dir. is -> %s", jt_flask_mod_parent_dir)

# Create our flask app.
# Static files are server from the 'static' directory
jt_flask_app = Flask(__name__, static_url_path='')

# In Flask, regardless of how you load your config, there is a 'config' object
# available which holds the loaded configuration values: The 'config' attribute
# of the Flask object
# The config is actually a subclass of a dictionary and can be modified just like
# any dictionary.  E.g. to update multiple keys at once you can use the dict.update()
# method:
#     jt_flask_app.config.update(
#         TESTING=True,
#         SECRET_KEY='192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'
#     )
#
# NOTE: Configuration Keys *** MUST BE ALL IN CAPITALS ***
#       (Ask me how I know...)
#
# This first line loads config from a Python object:
#jt_flask_app.config.from_object('config')
# This next one loads up our good old json object!!!
jt_flask_app.config.from_file(os.path.join(jt_flask_mod_parent_dir, 'journeytime.json'), json.load)
# Following line disables some older stuff we don't use that is deprecated (and
# suppresses a warning about using it). Please just leave it hard-coded here.
jt_flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
#   -> a SQLAlchemy.create_all() and SQLAlchemy.drop_all() methods to create
#      and drop tables according to the models.
#   -> a Model baseclass that is a configured declarative base.
# The Model declarative base class behaves like a regular Python class but has a
# query attribute attached that can be used to query the model. (Model and BaseQuery)
# We have to commit the session, but we don’t have to remove it at the end of the
# request, Flask-SQLAlchemy does that for us.
jt_flask_app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://" \
            + jt_flask_app.config['DB_USER'] + ":" + jt_flask_app.config['DB_PASS'] \
            + "@" \
            + jt_flask_app.config['DB_SRVR'] + ":" + jt_flask_app.config['DB_PORT']\
            + "/" + jt_flask_app.config['DB_NAME'] + "?charset=utf8mb4"

# 'csrf' gives us a mechanism for controlling csrf behaviour on forms (enabled by default)
csrf = CSRFProtect(jt_flask_app)

db = SQLAlchemy(jt_flask_app)

# Load the 'stop-to-stop' prediction model
# The journeyti.me application uses two classes of predictive model:
#   -> Targetted models, trained per LineId (the 'real world route short name')
#   -> A generic model that predicts times based on distance from the city center
#      (used in cases where our training data - from 2018 - did not contain
#       information for lines that exist currently).
# We keep the stop-to-stop model in memory - to improve performance.
stop_to_stop_filepath=os.path.join(jt_flask_mod_dir, 'pickles')
stop_to_stop_filepath=os.path.join(stop_to_stop_filepath, 'stop_to_stop' )
stop_to_stop_filepath=os.path.join(stop_to_stop_filepath, 'rfstoptostop.pickle' )
with open(stop_to_stop_filepath, 'rb') as file:
    # TODO:: Agree what action we should take if the pickle is invalid/not found.
    CONST_MODEL_STOP_TO_STOP = pickle.load(file)

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

@jt_flask_app.route('/')
@jt_flask_app.route('/index.html')
def root():
    """api.journeyti.me Home Page"""

    # This route simply serves 'static/index.html'
    #return jt_flask_app.send_static_file('index.html')
    # This route renders a template from the template folder
    return render_template('index.html')
    # This route renders a template from the template folder
    #return render_template('index.html', MAPS_API_KEY=jt_flask_app.config["MAPS_API_KEY"])

@jt_flask_app.route('/documentation.html')
def documentation():
    """api.journeyti.me Documentation Page"""
    # This route renders a template from the template folder
    return render_template('documentation.html')

@jt_flask_app.route('/invalid_dataset.html')
def invalid_dataset():
    """api.journeyti.me Invalid Dataset Page"""
    # This route renders a template from the template folder
    return render_template('invalid_dataset.html')

@jt_flask_app.route('/about.html')
def about():
    """api.journeyti.me About Page"""
    # This route renders a template from the template folder
    return render_template('about.html')

@jt_flask_app.route('/tk_testing.do', methods=['GET'])
def tk_testing():
    """api.journeyti.me development/testing page for TK"""
    # This route renders a template from the template folder
    return render_template('test_forms.html', form=UpdateUserForm())

@jt_flask_app.route('/downloads.html')
def downloads():
    """api.journeyti.me Downloads Page"""
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

def _get_dataset_in_requested_format(file_request, model, query):
    """Generate a response for the model requested, appropriately formatted

    Looks at the request args for argument 'dltype' to determine format
    """
    args = file_request.args
    download_type = args.get(CONST_DLTYPE)  # will be blank sometimes...

    if download_type == CONST_CSVFILE:
        # User requested everything as a .csv file. This is our preferred
        # option (minimum bandwidth), serve the user a compressed .csv file
        response = query_results_as_compressed_csv(model, query)
    else:
        # User requested everything as EITHER straighforward json or the json
        # returned as an attachement. Some of the tables are large, so we do
        # some checks before completing the request...

        # Find out how many records are involved...
        total_records = query.count()
        dl_row_limit_json        = int(jt_flask_app.config['DOWNLOAD_ROW_LIMIT_JSON'])
        dl_row_limit_json_attach = int(jt_flask_app.config['DOWNLOAD_ROW_LIMIT_JSON_ATTACHMENT'])

        # NOTE: For the data we have at the moment, every 1,000,000 records
        # corresponds (quite roughly) to 100MB of filesize.  So... if we want
        # a 10MB limit, this corresponds to circa 100,000 rows

        response = None
        if download_type == CONST_JSONFILE:
            # User requested everything as a .json file.
            if total_records > dl_row_limit_json_attach:
                response = query_results_as_json(
                    model, query.limit(dl_row_limit_json_attach), limit_exceeded=True
                    )
            else:
                response = query_results_as_json(model, query)
        else:
            # User wants JSON direct to the screen (not as an attached file)
            if total_records > dl_row_limit_json:
                outer_list = []
                dl_lim_json        = jt_flask_app.config['DOWNLOAD_ROW_LIMIT_JSON']
                dl_lim_json_attach = jt_flask_app.config['DOWNLOAD_ROW_LIMIT_JSON_ATTACHMENT']
                warning = {}
                warning['filesize_warning'] = {}
                warning['filesize_warning']['1_warning'] = 'WARNING'
                warning['filesize_warning']['2_description'] = \
                    'The number of records in this extract exceeds the current ' \
                    + 'streamed .json file limit'
                warning['filesize_warning']['3_limits1'] = \
                    'A maximum of ' + dl_lim_json \
                    + ' records can be delivered directly to a clients browswer'
                warning['filesize_warning']['4_limits2'] = \
                    'A maximum of ' + dl_lim_json_attach \
                    + ' records can be delivered as a .json file attachment'
                warning['filesize_warning']['5_limits3'] = \
                    'There is currently no limit on filesizes downloaded as compressed .csv.gz'
                outer_list.append(warning)

                outer_list.append([row.serialize() for row in query.limit(dl_row_limit_json).all()])
                response = jsonify(outer_list)
            else:
                # Requested data set is under the row limit, send it!
                response = jsonify([row.serialize() for row in query.all()])

    return response

# Endpoint for Agency model
# user can use EITHER:
#   'agency name' as a key (to get json response for just one agency)
# -OR-
#   supply argument '?dltype' ('json' or 'csv') to download content as a file
@jt_flask_app.route("/agency", defaults={'agency_name':None})
@jt_flask_app.route("/agency/<agency_name>")
def get_agency(agency_name):
    """api.journeyti.me - Agency file download links"""
    agency_query = db.session.query(Agency)

    response = None
    if agency_name is not None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        agency_query = agency_query.filter(Agency.agency_name ==  agency_name)
        agency_query = agency_query.order_by(text('agency_name asc'))

        # ".one" causes a TypeError, ".all" returns just the specified agency
        response = jsonify([row.serialize() for row in agency_query.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = _get_dataset_in_requested_format(request, Agency, agency_query)

    return response

# endpoint for Calendar model
@jt_flask_app.route("/calendar", defaults={'service_id':None})
@jt_flask_app.route("/calendar/<service_id>")
def get_calendar(service_id):
    """api.journeyti.me - Calendar file download links"""
    calendar_query = db.session.query(Calendar)

    response = None
    if service_id is not None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        calendar_query = calendar_query.filter(Calendar.service_id == service_id)
        calendar_query = calendar_query.order_by(text('service_id asc'))

        # ".one" causes a TypeError, ".all" returns just the specified agency
        response = jsonify([row.serialize() for row in calendar_query.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = _get_dataset_in_requested_format(request, Calendar, calendar_query)

    return response

# endpoint for CalendarDates
@jt_flask_app.route("/calendardates", defaults={'date':None})
@jt_flask_app.route("/calendardates/<date>")
def get_calendar_dates(date):
    """api.journeyti.me - CalendarDates file download links"""
    calendardates_query = db.session.query(CalendarDates)

    response = None
    if date is not None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        calendardates_query = calendardates_query.filter(CalendarDates.date == date)
        calendardates_query = calendardates_query.order_by(text('date asc'))

        response = jsonify([row.serialize() for row in calendardates_query.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = _get_dataset_in_requested_format(request, CalendarDates, calendardates_query)

    return response

@jt_flask_app.route("/routes", defaults={'route_id': None})
@jt_flask_app.route("/routes/<route_id>")
def get_routes(route_id):
    """api.journeyti.me - Route file download links"""
    route_query = db.session.query(Routes)

    response = None
    if route_id is not None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        route_query = route_query.filter(Routes.route_id == route_id)
        route_query = route_query.order_by(text('route_id asc'))

        response = jsonify([row.serialize() for row in route_query.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = _get_dataset_in_requested_format(request, Routes, route_query)

    return response

# endpoint for Shapes
@jt_flask_app.route("/shapes", defaults={'shape_id':None})
@jt_flask_app.route("/shapes/<shape_id>")
def get_shape(shape_id):
    """api.journeyti.me - Shapes file download links"""
    shape_query = db.session.query(Shapes)

    response = None
    if shape_id is not None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        shape_query = shape_query.filter(Shapes.shape_id == shape_id)
        shape_query = shape_id.order_by(text('shape_id asc'))

        response = jsonify([row.serialize() for row in shape_query.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = _get_dataset_in_requested_format(request, Shapes, shape_query)

    return response

@jt_flask_app.route("/stops", defaults={'stop_id': None})
@jt_flask_app.route("/stops/<stop_id>")
def get_stops(stop_id):
    """api.journeyti.me - Stops file download links"""

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

    stop_query = db.session.query(Stop)

    response = None
    if stop_id is not None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        stop_query = stop_query.filter(Stop.stop_id == stop_id)
        stop_query = stop_query.order_by(text('stop_id asc'))

        response = jsonify([row.serialize() for row in stop_query.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = _get_dataset_in_requested_format(request, Stop, stop_query)

    return response

# endpoint for StopTime model, should work because TK has written serialize function
# within StopTime
@jt_flask_app.route("/stoptimes", defaults={'trip_id':None})
@jt_flask_app.route("/stoptimes/<trip_id>")
def get_stop_times(trip_id):
    """api.journeyti.me - Stoptimes file download links"""
    stoptime_query = db.session.query(StopTime)

    response = None
    if trip_id is not None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        stoptime_query = stoptime_query.filter(StopTime.trip_id == trip_id)
        stoptime_query = stoptime_query.order_by(text('trip_id asc'))

        response = jsonify([row.serialize() for row in stoptime_query.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = _get_dataset_in_requested_format(request, StopTime, stoptime_query)

    return response

# endpoint for Transfers
@jt_flask_app.route("/transfers", defaults={'from_stop_id':None})
@jt_flask_app.route("/transfers/<from_stop_id>")
def get_transfers(from_stop_id):
    """api.journeyti.me - Transfers file download links"""
    transfer_query = db.session.query(Transfers)

    response = None
    if from_stop_id is not None:
        # Simplest use case - user requires information on single agency
        # No option to download this as a file (currently) - just return requested
        # information as json.
        transfer_query = transfer_query.filter(Transfers.from_stop_id == from_stop_id)
        transfer_query = transfer_query.order_by(text('from_stop_id asc'))

        response = jsonify([row.serialize() for row in transfer_query.all()])
    else:
        # No specific agency requested - decide how (and exactly what) to return
        # to the user...
        response = _get_dataset_in_requested_format(request, Transfers, transfer_query)

    return response

# endpoint for Trips
# Trips is a large table - so we don't return the json directly to user in the
# resonse, instead we stream them a file with the json inside!
@jt_flask_app.route("/trips", defaults={'trip_id':None})
@jt_flask_app.route("/trips/<trip_id>")
def get_trips(trip_id):
    """api.journeyti.me - Trips file download links"""
    trips_query = db.session.query(Trips)

    response = None
    if trip_id is not None:
        # Simplest use case - user requires information on single trip
        # No option to download this as a file (currently) - just return requested
        # information as json.
        trips_query = trips_query.filter(Trips.trip_id == trip_id)

        # ".one" causes a TypeError, ".all" returns just the specified trip
        response = jsonify([row.serialize() for row in trips_query.all()])
    else:
        # No specific trip requested - decide how (and exactly what) to return
        # to the user...
        response = _get_dataset_in_requested_format(request, Trips, trips_query)

    return response


##########################################################################################
#  GROUP 3: COMPLEX QUERIES
##########################################################################################

# ??????????????? Following IS NOT WORKING
# Should I bother updating this to accept a POSTed json input??????
# Was only used during the development phase...

@jt_flask_app.route("/getStopsByShortname", methods=['GET'])
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
    # e.g.: https://journeyti.me/getStopsByRoute
    #               ?rsn=17&jrny_dt=20220703165400&depstoplat=53.3351498&depstoplon=-6.2943145

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
@jt_flask_app.route('/json_parrot.do', methods=['POST'])
@csrf.exempt
def json_parrot():
    """api.journeyti.me - return json posted to server as response

    This endpoint was used for testing json post requests during development
    """
    return jsonify(request.json)


# Simple endpoint to submission of json and return it to the user...
@jt_flask_app.route('/update_model_list.do', methods=['GET'])
# The following decorator means this function will run once just before the first
# request is processed (NOT on startup, just before the first request)
@jt_flask_app.before_first_request
def update_model_list():
    """api.journeyti.me - Update the current list of stored 'route shortname' models

    A cron job calls this URL hourly, so changes to the model set are automatically detected.
    """
    # We're careful to keep our original list reference alive and just empty
    # the list, then repopulate it.  To avoid referencing an object which only
    # exists in the scope of this endpoint.
    AVAILABLE_MODEL_ROUTE_SHORTNAMES.clear()
    AVAILABLE_MODEL_ROUTE_SHORTNAMES.extend(get_available_end_to_end_models())


    return jsonify(AVAILABLE_MODEL_ROUTE_SHORTNAMES)


# Simple endpoint to load list of valid route names
@jt_flask_app.route('/update_valid_route_shortnames.do', methods=['GET'])
# The following decorator means this function will run once just before the first
# request is processed (NOT on startup, just before the first request)
@jt_flask_app.before_first_request
def update_valid_route_shortnames():
    """api.journeyti.me - Update the current list of valid 'route shortnames' in the GTFS dataset

    This endpoint is called after each load of GTFS data, to ensure we always
    know which route shortnames the application can attempt prediction for.
    """
    # We're careful to keep our original list reference alive and just empty
    # the list, then repopulate it.  To avoid referencing an object which only
    # exists in the scope of this endpoint.
    VALID_ROUTE_SHORTNAMES.clear()
    VALID_ROUTE_SHORTNAMES.extend(get_valid_route_shortnames(db))

    return jsonify(VALID_ROUTE_SHORTNAMES)


@jt_flask_app.route('/get_journey_time.do', methods=['POST'])
@csrf.exempt
def get_journey_time():
    """api.journeyti.me - Predict Journey Time for a set of Routes

    This is the beating heart of the Journeyti.me application
    """
    resp = _get_failure_response()  # Assume failure

    # If no json submitted - this is a dud request...
    if request.json:
        # A valid prediction request will confirm to the specification laid out
        # in JourneyPredictionRequestSpec.json.  We can conveniently get the JSON
        # POST'ed to the server (as a python dictionary) using:
        prediction_request_json = request.json
        print("get_journey_time.do: request.json type is -> ", type(request.json))

        # pickles_dir='pickles'
        # TEMP_pickle_path= os.path.join(jtFlaskModDir, pickles_dir)

        # The incoming json should contain one (or more) routes.  Each route will
        # be made up of steps, where each step is a seperate bus journey for that
        # route.
        log.debug('looping over routes')
        for route_idx, route in enumerate(prediction_request_json['routes']):
             # def JourneyPrediction():
            no_of_steps_this_route = len(route['steps'])
            log.debug(
                '\tProcessing route %d, no_of_steps_this_route -> %d'
                , route_idx, no_of_steps_this_route
                )

            _predict_all_steps(route)

        # Hard code an updated title and description for the response so that
        # it's easier to understand at the client end.
        prediction_request_json['title'] = 'Journeyti.me Prediction Response'
        prediction_request_json['description'] = 'Journeyti.me Step-by-Step Prediction Response'

        resp = jsonify(prediction_request_json)

    return resp


def _predict_all_steps(route):
    """Convenience method to perform predictions for each step in a route.
    """
    log.debug('\tlooping over steps')
    for step_idx, step in enumerate(route['steps']):
        log.debug('\tProcessing step %s.', step_idx)

        _attempt_predict_this_step(step)

def _attempt_predict_this_step(step):
    """Attempt to perform a journey prediction for the current step

    Extracts the details required for prediction from the inbound json
    If route data is stored in the database we go ahead and make a prediction
    If we don't have information for this route, return a 'no prediction' message
    """
    planned_time_s  = step['duration']['value']
                # Extend the json to contain stop-by-stop route information...
                # NOTE The mappings between Googles supplied data and the GTFSR
                #      fields are *inferred* - I could not find documentation
                #      guaranteeing the mappings.
    route_name = step['transit_details']['line']['name']
    route_shortname = ''
    if 'short_name' in step['transit_details']['line'].keys():
                    # Dublin Bus use route shortname to list the line id's...
        route_shortname = step['transit_details']['line']['short_name']
    else:
                    # Other operators like Aircoach seem to use the name...
        route_shortname = step['transit_details']['line']['name']
                # Our best guess for line-id is now route-shortname. BUT there
                # are some routes in Dublin not covered by agencies in the
                # transportforireland data set.  If we encounter one of these
                # routes there's nothing we can do (we have no information about
                # the route at all).
    if route_shortname in VALID_ROUTE_SHORTNAMES:
        # We have supporting information in the database (route details etc.)
        # - let's go ahead and perform a prediction!
        _predict_this_step(step, planned_time_s, route_name, route_shortname)
    else:
                    # We have encountered an invalid route shortname. We abort
                    # with an error message...
        step['prediction_status'] = \
                        'Prediction Service not available for route \'' + route_shortname + '\'.'


def _predict_this_step(step, planned_time_s, route_name, route_shortname):
    """Perform a journey prediction for the current step

    Look up the stop sequence for this route from the GTFS data
    Perform a prediction once we have the stop information to hand.
    """
    step['prediction_status'] = 'Prediction Attempted'

    route_shortname_pickle_exists = \
                        route_shortname in AVAILABLE_MODEL_ROUTE_SHORTNAMES

                    # Dublin Bus times are 'timestamp' expressed in seconds
                    # elapsed since the Unix epoch, 1970-01-01 00:00:00 UTC
                    # Using datetime to construct our date seems to nicely cater
                    # for daylight savings times, differences from UTC etc. ...
                    # -
                    # Aircoach on the other hand appear to publish their times as strings
                    # So... we just fudge around it...
    planned_departure_datetime = _get_planned_departure_datetime(step)

    step_stops = _get_stops_for_this_step(step, route_name, route_shortname)

                    # Bundle everything we need to make a prediction into a convenient
                    # object. We can then pass this object to the prediction routine
    journey_pred = JourneyPrediction( \
                        route_shortname, route_shortname_pickle_exists, \
                        planned_time_s, planned_departure_datetime, step_stops)

                    # # Pickle the JourneyPrediction object - handy for testing!!
                    # with open(
                    #       os.path.join(
                    #           TEMP_pickle_path,
                    #           'JourneyPrediction-r' + str(route_idx)
                    #           + '-s' + str(step_idx) + '.pickle')
                    #       , 'wb+'
                    #       ) as handle:
                    #     pickle.dump(journey_pred, handle, protocol=pickle.HIGHEST_PROTOCOL)

                    # Call a function to get the predicted journey time for this step.
    journey_pred = predict_journey_time(journey_pred, CONST_MODEL_STOP_TO_STOP)

                    # Extend the json to contain the prediction information...
    predicted_duration = journey_pred.predicted_duration_s
    step['predicted_duration'] = {}
    step['predicted_duration']['text'] = \
                        time_rounded_to_hrs_mins_as_string(predicted_duration)
    step['predicted_duration']['value'] = predicted_duration

                    # Where possible - extend the json to contain the step_stops information
    if len(step_stops) > 0:
        _add_stop_seq_json_to_step(step, step_stops)
    else:
                        # No stop information available
        step['prediction_status'] = \
                            'Prediction Attempted - Stop-by-Stop information not available.'


def _get_planned_departure_datetime(step):
    """Get the planned departure datetime for this step

    Provides sensible defaults
    """
    planned_departure_datetime = datetime.now()
    if isinstance(step['transit_details']['departure_time']['value'], str):
        dep_datetime_str = step['transit_details']['departure_time']['value']
                        # We strip off the trailing 'GMT+0100' etc from the string before...
        last_period = dep_datetime_str.rfind('.')
        dep_datetime_str = dep_datetime_str[:last_period]
                        # ... converting it to a datetime object.
        planned_departure_datetime = \
                            datetime.strptime(dep_datetime_str, '%Y-%m-%dT%H:%M:%S')
    else:
                        # Dublin bus scenario...
        planned_departure_datetime = \
                            datetime.fromtimestamp(
                                step['transit_details']['departure_time']['value']
                                )
    log.debug(
                "\t\tdatatime converted from google epoch based timestamp -> %s",
                str(planned_departure_datetime)
            )

    return planned_departure_datetime


def _get_stops_for_this_step(step, route_name, route_shortname):
    """Get the sequence of stops for this step

    Each step has a sequence of stops (is a full or partial route)
    Extract the relevant details from the inbound json and look for the most
    likely trip for this step.
    """
    stop_headsign = step['transit_details']['headsign']
    departure_time = _get_departure_time(step)
    departure_stop_name = \
                        step['transit_details']['departure_stop']['name']
    departure_stop_lat = \
                        step['transit_details']['departure_stop']['location']['lat']
    departure_stop_lon = \
                        step['transit_details']['departure_stop']['location']['lng']
    arrival_stop_name = \
                        step['transit_details']['arrival_stop']['name']
    arrival_stop_lat = \
                        step['transit_details']['arrival_stop']['location']['lat']
    arrival_stop_lon = \
                        step['transit_details']['arrival_stop']['location']['lng']

    step_stops = get_stops_by_route(db, route_name, route_shortname, \
                        stop_headsign, departure_time, \
                        departure_stop_name, departure_stop_lat, departure_stop_lon, \
                        arrival_stop_name, arrival_stop_lat, arrival_stop_lon)
    log.debug(
                        "\t\twe found the following number of step_stops -> %d",
                        len(step_stops)
                        )

    return step_stops


def _get_departure_time(step):
    """Get the departure datetime for this step

    Provides sensible defaults
    """
    departure_time = datetime.now().time()
    if isinstance(step['transit_details']['departure_time']['value'], str):
        dep_datetime_str = step['transit_details']['departure_time']['value']
                        # We strip off the trailing 'GMT+0100' from the string before processing...
        last_period = dep_datetime_str.rfind('.')
        dep_datetime_str = dep_datetime_str[:last_period]
        departure_time = \
                            datetime.strptime(dep_datetime_str, '%Y-%m-%dT%H:%M:%S').time()
    else:
                        # Dublin bus scenario...
        departure_time = datetime.fromtimestamp(
                            step['transit_details']['departure_time']['value']
                            ).time()

    return departure_time


def _add_stop_seq_json_to_step(step, step_stops):
    """Convenience method to add the stop_sequence json to the supplied step
    """
    step['stop_sequence'] = {}
    step['stop_sequence']['stops'] = []
    for step_stop in step_stops:
        step_stop_dict = {}
        step_stop_dict['stop_id'] = step_stop.stop.stop_id
        step_stop_dict['name'] = step_stop.stop.stop_name
        step_stop_dict['location'] = {}
        step_stop_dict['location']['lat'] = step_stop.stop.stop_lat
        step_stop_dict['location']['lng'] = step_stop.stop.stop_lon
        step_stop_dict['sequence_no'] = step_stop.stop_sequence
        step_stop_dict['shape_dist_traveled'] = step_stop.shape_dist_traveled
        step_stop_dict['dist_from_first_stop_m'] = \
                                step_stop.dist_from_first_stop_m
        step_stop_dict['predicted_time_from_first_stop_s'] = \
                                step_stop.predicted_time_from_first_stop_s
        step['stop_sequence']['stops'].append(step_stop_dict)

##########################################################################################
#  GROUP 4: JT_UI RESTful SUPPORT FUNCTIONS
##########################################################################################

def _get_success_response():
    """Convenience method - generate a json Success response"""
    resp = jsonify(success=True)
    resp.status_code = 200  # Success
    return resp

def _get_failure_response():
    """Convenience method - generate a json Failure response"""
    resp = jsonify(success=False)
    resp.status_code = 401  # Unauthorized
    return resp

def _log_errors(errors):
    """Convenience method - loop over errors list, log each one"""
    log.error("ERRORS Detected on form:")
    for key in errors:
        for message in errors[key]:
            log.error("\t%s : %s",  key, message)


@jt_flask_app.route("/check_username_available.do", methods=['POST'])
@csrf.exempt
def check_username_available():
    """api.journeyti.me - Check if the supplied username is available

    Returns RESTful success/fail
    """
    check_form = CheckUsernameAvailableForm(meta={'csrf': False})  # see forms.py

    resp = _get_failure_response()  # Assume not available
    # 'validate_on_submit' ensures BOTH post AND form checks passed!
    if check_form.validate_on_submit():
        try:
            desired_username = check_form.username.data
            count_users_with_username = \
                db.session.query(JT_User).filter_by(username=desired_username).count()
            if count_users_with_username == 0:
                resp = _get_success_response()
        except (SQLAlchemyError, DBAPIError):
            print("ERROR Database Error")
            print(traceback.format_exc())

    return resp

@jt_flask_app.route("/register.do", methods=['POST'])
@csrf.exempt
def register():
    """api.journeyti.me - Register a new user for the journeyti.me application

    Returns RESTful success/fail
    """

    #form = UserForm(CombinedMultiDict((request.files, request.form)))  # see forms.py
    #   -> 'request.form' only contains form input data.
    #   -> 'request.files' contains file upload data.
    # You need to pass the combination of both to the form. Since a form inherits
    # from Flask-WTF's Form (now called FlaskForm), it will handle this automatically
    # if you don't pass anything to the form!!
    reg_form = RegisterForm(meta={'csrf': False})  # see forms.py

    resp = _get_failure_response()  # Assume failure
    if reg_form.validate_on_submit():
        try:
            new_user = JT_User()
            reg_form.populate_obj(new_user)

            db.session.add(new_user)
            db.session.flush()
            db.session.commit()

            resp = _get_success_response()
        except (SQLAlchemyError, DBAPIError):
            print("ERROR Database Error")
            print(traceback.format_exc())
    else:
        # 'form.errors' is only populated when you call either validate() or
        # validate_on_submit.  So you can't check this in advance!
        # Log any errors in the server log (while devloping at least...)
        _log_errors(reg_form.errors)

    return resp

@jt_flask_app.route("/login.do", methods=['POST'])
@csrf.exempt
def login():
    """api.journeyti.me - For the supplied username and hashed password, attempt login

    Returns RESTful success/fail
    """
    login_form = LoginForm(meta={'csrf': False})  # see forms.py

    resp = _get_failure_response()  # Assume failure
    if login_form.validate_on_submit():
        try:
            jt_user = db.session.query(JT_User).filter_by(username=login_form.username.data).one()
            if jt_user.password_hash == login_form.password_hash.data:
                resp = _get_success_response()
        except (SQLAlchemyError, DBAPIError):
            print("ERROR Database Error")
            print(traceback.format_exc())
    else:
        _log_errors(login_form.errors)

    return resp

@jt_flask_app.route("/update_user.do", methods=['POST'])
@csrf.exempt
def update_user():
    """api.journeyti.me - For the supplied username, update the user

    Returns RESTful success/fail
    """
    #form = UserForm(CombinedMultiDict((request.files, request.form)))  # see forms.py
    #   -> 'request.form' only contains form input data.
    #   -> 'request.files' contains file upload data.
    # You need to pass the combination of both to the form. Since a form inherits
    # from Flask-WTF's Form (now called FlaskForm), it will handle this automatically
    # if you don't pass anything to the form!!
    upd_usr_form = UpdateUserForm(meta={'csrf': False})  # see forms.py

    resp = _get_failure_response()  # Assume failure
    if upd_usr_form.validate_on_submit():
        try:
            # print("username ->", \
            #   upd_usr_form.username.data, "-", type(upd_usr_form.username.data))
            # print("password_hash ->", \
            #   upd_usr_form.password_hash.data, "-", type(upd_usr_form.password_hash.data))
            # print("nickname ->", \
            #   upd_usr_form.nickname.data, "-", type(upd_usr_form.nickname.data))
            # print("colour ->", \
            #   upd_usr_form.colour.data, "-", type(upd_usr_form.colour.data))
            # print("profile_picture ->", \
            #   upd_usr_form.profile_picture.data, "-", type(upd_usr_form.profile_picture.data))
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

            resp = _get_success_response()
        except (SQLAlchemyError, DBAPIError):
            print("ERROR Database Error")
            print(traceback.format_exc())

    else:
        _log_errors(upd_usr_form.errors)

    return resp

@jt_flask_app.route("/get_profile_picture.do", methods=['GET'])
def get_profile_picture():
    """api.journeyti.me - return the profile picture for the supplied username

    Returns image on success, 204 response if no picture available
    """
    args = request.args
    user_loaded = False

    gpp_username = args.get('username')
    if gpp_username:
        try:
            user = db.session.query(JT_User).filter_by(username=gpp_username).one()
            user_loaded = True
        except (SQLAlchemyError, DBAPIError):
            print("ERROR Database Error")
            print(traceback.format_exc())

    response = None
    if user_loaded and user.profile_picture:
        response = make_response(user.profile_picture)
        extension = os.path.splitext(user.profile_picture_filename)[1][1:].strip()
        response.headers.set('Content-Type', 'image/' + extension)
    else:
        # 'make_response' can be called with a single argument -OR- any of
        # (body, status, headers), (body, status), or (body, headers), where
        # headers is a dictionary or list of (key, value) tuples.
        response = make_response('', 204)  # 204 is the "No Content" status code

    return response


##########################################################################################
#  END: CLOSE APPLICATION
##########################################################################################

# Flask will automatically remove database sessions at the end of the request or
# when the application shuts down:
@jt_flask_app.teardown_appcontext
def shutdown_session(exception=None):
    """Generic Flask shutdown function"""
    db.session.remove()
    # sys.stdout.close()  # Close the file handle we have open
    # sys.stdout = sys.__stdout__ # Reset to the standard output

if __name__ == "__main__":
    # Reassign stdout so any debugs etc. generated by flask won't be lost when
    # running as a service on EC2
    # sys.stdout = open('dwmb_Flask_.logs', 'a')

    # print("DWMB Flask Application is starting: " + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    jt_flask_app.run(
        debug=True,
        host=jt_flask_app.config["FLASK_HOST"],
        port=jt_flask_app.config["FLASK_PORT"]
        )
