# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from flask import Response, stream_with_context
from haversine import haversine, Unit
import json
import logging
import os, sys
from models import Routes, Stop, StopTime, Trips
import numpy as np
import pandas as pd
from pathlib import Path
import pickle
import requests as rq
from sqlalchemy import asc, desc, text, func
from sqlalchemy.dialects import mysql
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound  # Exceptions
import struct
import time
import zlib

# According to the article here:
#    -> https://towardsdatascience.com/simple-trick-to-work-with-relative-paths-in-python-c072cdc9acb9
# ... Python, if needing to use relative paths in order to make it easier to 
# relocate an application, one can determine the directory that a specific code
# module is located in using os.path.dirname(__file__). A full path name can then
# be constructed by using os.path.join()...
# (the value of __file__ is a string, which is set when module was imported by a loader)
# Application Startup...
jt_utils_dir = os.path.dirname(__file__)
jt_utils_parent_dir = os.path.dirname(jt_utils_dir)

log = logging.getLogger(__name__)  # Standard naming...

def load_credentials():
    """Load the credentials required for accessing the Weather API, Google Maps, etc.

    Returns a JSON object with the required credentials.
    Implemented in a method as Credential storage will be subject to change.
    """
    # Our credentials are just stored in a JSON file (for now)
    # This file is not saved to GitHub and is placed on each EC2 instance
    # by a team member.
    # Load the JSON file
    file = open(os.path.join(jt_utils_parent_dir, 'journeytime.json'), 'r')
    credentials = json.load(file)
    file.close  # Can close the file now we have the data loaded...
    return credentials


# Each point is represented by a tuple, (lat, lon). Define a fixed point for
# Dublin City Center...
credentials = load_credentials()
CONST_DUBLIN_CC = (credentials['DUBLIN_CC']['lat'], credentials['DUBLIN_CC']['lon'])


##########################################################################################
#  Extracts (JSON, .CSV)
##########################################################################################


# 'Module Private' helper function for the various methods that download files...
def _get_next_chunk_size(rows_remain):
    """Calculate the next chunk size for a data set

    Based on the remaining rows and the paramaterised optimimum chunk size
    """
    CHUNK_SIZE = int(credentials['DOWNLOAD_CHUNK_SIZE'])
    rows_chunk = 0
    if rows_remain > 0:
        if rows_remain >= CHUNK_SIZE:
            rows_chunk  = CHUNK_SIZE
        else:
            rows_chunk  = rows_remain

    return rows_chunk


def query_results_as_compressed_csv(model, query):
    """

    Returns a CSV File with one row per record in the query result set.
    """

    def get_chunk(row_list, first_chunk_tf, query):
        if first_chunk_tf:
            # We need to build the string for the first line of the .csv - the column headers
            col_headers = ''
            for column_desc in query.statement.columns.keys():
                # Each 'column_desc is a dict, with several properties per column.
                col_headers += column_desc + ','
            if len(col_headers) > 1:
                col_headers = col_headers[:-1]

            chunk = col_headers + '\n'
            first_chunk_tf = False
        else:
            chunk = '\n'
        chunk += '\n'.join(row_list)  # csv - join the elements with 'commas'
        return chunk.encode(), first_chunk_tf
    
    def generate(query):
        # I simply could not have implemented this method without:
        #   -> https://stackoverflow.com/questions/44185486/generate-and-stream-compressed-file-with-flask
        # ... as a reference.  I have not researched the Gzip file specification
        # in detail (https://datatracker.ietf.org/doc/html/rfc1952#section-2.2),
        # rather I've copied the values supplied by Martijn Pieters in the
        # stackoverflow article above and adopted his approach to suit my needs.

        # Yield a gzip file header first.
        yield bytes([
            # 0x1f0x8b is the Magic number identifying file type
            # 0x08 is the compression method (deflate)
            0x1F, 0x8B, 0x08, 0x00,  # Gzip file, deflate, no file flags
            *struct.pack('<L', int(time.time())),  # compression start time
            0x02, 0xFF,  # maximum compression, no OS specified
        ])

        # bookkeeping: the compression state, running CRC and total length
        compressor = zlib.compressobj(
            9, zlib.DEFLATED, -zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL, 0)
        crc = zlib.crc32(b"")

        length = 0
        rows_remain    = query.count()
        rows_chunk     = _get_next_chunk_size(rows_remain)
        row_count      = 0
        row_list       = []
        first_chunk_tf = True
        lastRowPK      = 0

        # I still got memory overruns trying to use query.yield_per()... which
        # looked almost tailor made for our objective.  So perhaps I was doing
        # something wrong...
        # query.yield_per(rows_chunk)

        # Instead I did an old fashioned loop to let me use smaller queries, to
        # keep the memory footprint down...
        while True:
            rows_this_chunk = query.filter(model.id > lastRowPK).limit(rows_chunk).all()
            if not rows_this_chunk or len(rows_this_chunk) == 0: 
                break
            for row in rows_this_chunk:
                lastRowPK = row.id
 
                # If we build up the string we plan to send by repeatedly appending,
                # we're creating a new string each time. This is quite memory expensive
                # and inefficient.
                # Instead we build a list of strings - which we will later convert to
                # a single string.
                # 'row_list' will be a list of strings...
                row_list.append( '"' + '","'.join([str(value) for value in row.serialize().values()]) + '"')
                row_count += 1

                if row_count >= rows_chunk:
                    rows_remain -= rows_chunk  # we've just competed a chunk
                                            # this condition finally exits the loop
                    rows_chunk = _get_next_chunk_size(rows_remain)
                    # print("Completed a chunk:")
                    # print("\tRows Remaining ->", rows_remain)
                    # print("\tRows This Chunk ->", rows_chunk)

                    chunk, first_chunk_tf = get_chunk(row_list, first_chunk_tf, query)
                    chunk_compressed = compressor.compress(chunk)
                    if chunk_compressed:
                        log.debug("yielding a chunk...")
                        yield chunk_compressed
                    crc = zlib.crc32(chunk, crc) & 0xFFFFFFFF  # Keep the CRC up to date...
                    length += len(chunk)

                    row_list = []
                    row_count = 0

        # Finishing off, send remainder of the compressed data, and CRC and length
        yield compressor.flush()
        yield struct.pack("<2L", crc, length & 0xFFFFFFFF)

    # Test - do we need 'stream_with_context'?  If I understand the docs correctly
    # then I don't think we do! It's just a method to keep the context alive while
    # streaming).  But time/testing will tell...
    #response = Response(stream_with_context(generate(query, name)), mimetype='application/gzip')
    response = Response(generate(query), mimetype='application/gzip')
    response.headers['Content-Disposition'] = 'attachment; filename=' + model.__table__.name + '.csv.gz'
    return response


def query_results_as_json(model, query, **kwargs):
    """

    Returns a JSON List with one object per record in the query result set.
    """
    incl_limit_exceeded_warning = False
    if 'limit_exceeded' in kwargs:
        if kwargs['limit_exceeded'] == True:
            incl_limit_exceeded_warning = True
    
    def get_chunk(json_list, first_chunk, name):
        if first_chunk:
            chunk = '{\n'
            if incl_limit_exceeded_warning:
                dl_lim_json        = credentials['DOWNLOAD_ROW_LIMIT_JSON']
                dl_lim_json_attach = credentials['DOWNLOAD_ROW_LIMIT_JSON_ATTACHMENT']

                chunk += '\"filesize_warning\": {\n'
                chunk += '\"1_warning\": \"WARNING\",\n'
                chunk += '\"2_description\": \"The number of records in this extract exceeds the current streamed .json file limit\",\n'
                chunk += '\"3_limits1\": \"A maximum of ' + dl_lim_json + ' records can be delivered directly to a clients browswer\",\n'
                chunk += '\"4_limits2\": \"A maximum of ' + dl_lim_json_attach + ' records can be delivered as a .json file attachment\",\n'
                chunk += '\"5_limits3\": \"There is currently no limit on filesizes downloaded as compressed .csv.gz\"\n'
                chunk += '},\n'
            chunk += '\"' + name + '\": [\n'
            first_chunk = False
        else:
            chunk = ',\n'
        chunk += ',\n'.join(json_list)
        return chunk, first_chunk
    
    # See...
    #https://stackoverflow.com/questions/19926089/python-equivalent-of-java-stringbuffer
    # ... for some benchmarking on a number of approaches to concatenating lots of strings...
    # json_list=[i.serialize() for i in tripsQuery.all()]
    # return jsonify(json_list)
    def generate(model, query):
        row_count = 0

        # "tripsQuery.all()" is a python list of results
        #rows_remain = len(tripsQuery.all())
        rows_remain = query.count()
        rows_chunk  = _get_next_chunk_size(rows_remain)
        row_count   = 0
        json_list   = []
        first_chunk = True
        for row in query:
            # Don't have to consider empty queries - if we have no results
            # we will never enter this iterator.

            # We removed the indent of four spaces from our generated json. It does look
            # prettier - but it increases download sizes by circa 13% (these extracts are
            # already large)
            #json_list.append( json.dumps(row.serialize(), indent=4) )
            json_list.append( json.dumps(row.serialize()) )
            row_count += 1
            
            # Every time we complete a chunk we yield it and reset out list
            # to an empty list...
            if row_count >= rows_chunk:
                rows_remain -= rows_chunk  # we've jusr competed a chunk
                rows_chunk = _get_next_chunk_size(rows_remain)
                log.debug("Completed a chunk:")
                log.debug("\tRows Remaining ->", rows_remain)
                log.debug("\tRows This Chunk ->", rows_chunk)

                buffer, first_chunk = get_chunk(json_list, first_chunk, model.__table__.name)
                if buffer:
                    yield buffer
                
                json_list = []
                row_count = 0

        # Finishing off, send remainder of the compressed data, and CRC and length
        yield "\n]\n}"  # <- We close the list after the last buffer yield

    return Response(generate(model, query), mimetype='application/json', \
        headers={'Content-disposition': 'attachment; filename=' + model.__table__.name + '.json'})


##########################################################################################
#  Predictions
##########################################################################################


class JourneyPrediction:
    """Model representing journey time prediction information

    INPUTS are included
    RESULTS are included
    Other factors are involved in choosing which input model to use: whether an
    end-to-end model is available, etc.. But those factors are common to all
    predictions, the data encapsulated here is for a single journey
    """
    def __init__(self, route_shortname, route_shortname_pickle_exists, planned_duration_s, planned_departure_datetime, step_stpps):
        # Instance Variables
        self.set_route_shortname(route_shortname)
        self.set_route_shortname_pickle_exists(route_shortname_pickle_exists)
        self.set_planned_duration_s(planned_duration_s)
        self.set_planned_departure_datetime(planned_departure_datetime)
        # 'step_stops' is a list of StepStop model objects for the current journey step.
        self.set_step_stpps(step_stpps)
        self.set_predicted_duration_s(0)

    def set_route_shortname(self, route_shortname):
        self._route_shortname = route_shortname
    def set_route_shortname_pickle_exists(self, route_shortname_pickle_exists):
        self._route_shortname_pickle_exists = route_shortname_pickle_exists
    def set_planned_duration_s(self, planned_duration_s):
        self._planned_duration_s = planned_duration_s
    def set_planned_departure_datetime(self, planned_departure_datetime):
        self._planned_departure_datetime = planned_departure_datetime
    def set_step_stpps(self, step_stpps):
        self._step_stpps = step_stpps
    def set_predicted_duration_s(self, predicted_duration_s):
        self._predicted_duration_s = predicted_duration_s

    def get_route_shortname(self):
        return self._route_shortname
    def get_route_shortname_pickle_exists(self):
        return self._route_shortname_pickle_exists
    def get_planned_duration_s(self):
        return self._planned_duration_s
    def get_planned_departure_datetime(self):
        return self._planned_departure_datetime
    def get_step_stpps(self):
        return self._step_stpps
    def get_predicted_duration_s(self):
        return self._predicted_duration_s


class StepStop:
    """Model representing a stop on one step of a journey (part of a 'trip')

    """
    def __init__(self, stop, stop_sequence, shape_dist_traveled):
        # Instance Variables
        self.set_stop(stop)
        self.set_stop_sequence(stop_sequence)
        self.set_shape_dist_traveled(shape_dist_traveled)

    def set_stop(self, stop):
        self._stop = stop
    def set_stop_sequence(self, stop_sequence):
        self._stop_sequence = stop_sequence
    def set_shape_dist_traveled(self, shape_dist_traveled):
        self._shape_dist_traveled = shape_dist_traveled
    def set_shape_predicted_time_traveled_s(self, shape_predicted_time_traveled_s):
        self._shape_predicted_time_traveled_s = shape_predicted_time_traveled_s

    def get_stop(self):
        return self._stop
    def get_stop_sequence(self):
        return self._stop_sequence
    def get_shape_dist_traveled(self):
        return self._shape_dist_traveled
    def get_shape_predicted_time_traveled_s(self):
        return self._shape_predicted_time_traveled_s

    def serialize(self):
       """Return object data in easily serializeable format"""
       return  {
            'stop_id': self.stop.stop_id,
            'stop_name': self.stop.stop_name,
            'stop_lat': self.stop.stop_lat,
            'stop_lon': self.stop.stop_lon,
            'stop_sequence': self.get_stop_sequence(),
            'stop_shape_dist_traveled': self.get_shape_dist_traveled(),
            'stop_shape_predicted_time_traveled_s': self.get_shape_predicted_time_traveled_s()
        }


def get_available_end_to_end_models():
    """Return a list of all End-to-End model pickles currently on disk
    """
    AVAILABLE_MODEL_ROUTE_SHORTNAMES = []
    end_to_end_model_dir = jt_utils_dir + '/pickles/end_to_end'

    # iterate over files in that directory
    files = Path(end_to_end_model_dir).glob('*.pickle')
    for file in files:
        AVAILABLE_MODEL_ROUTE_SHORTNAMES.append(Path(file).stem)

    return AVAILABLE_MODEL_ROUTE_SHORTNAMES


def get_valid_route_shortnames(db):
    """Return a list of all valid route shortnamees
    """
    VALID_ROUTE_SHORTNAMES = []
    
    route_shortname_query = db.session.query(Routes.route_short_name)
    route_shortname_query = route_shortname_query.order_by(asc(Routes.route_short_name))
    route_shortnames = route_shortname_query.all()
    if len(route_shortnames) > 0:
        VALID_ROUTE_SHORTNAMES = [row[0] for row in route_shortnames]
        log.debug('\tFound ' + str(len(VALID_ROUTE_SHORTNAMES)) + ' route-shortnames')
        
    return VALID_ROUTE_SHORTNAMES



def get_stops_by_route(db, route_name, route_shortname, \
    stop_headsign, jrny_time, \
    departure_stop_name, departure_stop_lat, departure_stop_lon, \
    arrival_stop_name, arrival_stop_lat, arrival_stop_lon):
    """Returns an ordered list of stops for a selected LineId
    
    Each route_shortname can (potentially) represent a collection of routes
    We identify the 'most likely route' based on a chosen datetime, starting
    from a chosen stop (identified by lat/lon coordinates)
    Returns an empty list on error
    Returns a list of 'StepStops' on success
    """
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

    def _identify_stop(db, name, lat, lon):
        """Returns a the 'most likely' Stop (sqlachemy model) for the supplied inputs
        
        Attempts to identify Stop by exact shortname match first.
        If that fails OR if multiple results are found then select the stop using
        the MySQL 'ST_DISTANCE_SPHERE' method to identify to stop closest to the
        supplied lat/long.
        """
        stop = None
        position_match_required = False
        try:
            # Exact MATCH based ON NAME
            stop_query = db.session.query(Stop)
            stop_query = stop_query.filter(Stop.stop_name == name)
            stop = stop_query.one()
        except NoResultFound as nrf:
            # log.warning('\tNo Stops found for stop name: ' + name)
            position_match_required = True
        except MultipleResultsFound as mrf:
            # log.warning('\tMultiple Stops found for stop name: ' + name)
            position_match_required = True
        
        if position_match_required:
            # # Initially I couldn't find a nice 'ORM' way to do the following so
            # # had resorted to MySQL syntax for speed.
            # raw_sql = \
            #     'SELECT *, ST_DISTANCE_SPHERE(' \
            #         + 'stops.stop_position, POINT(' + str(stop_lon) + ', ' + str(stop_lat) + ')' \
            #         + ')' \
            #         + ' AS distance' \
            #     + ' FROM stops' \
            #     + ' ORDER BY distance ASC' \
            #     + ' LIMIT 1'
            # log.debug(raw_sql)
            # result = db.engine.execute(raw_sql).one()
            #position = func.ST_MakePoint(lon, lat)

            # MySQL Spatial Function reference:
            #   https://dev.mysql.com/doc/refman/8.0/en/spatial-function-reference.html
            distance_col = func.ST_Distance_Sphere( \
                Stop.stop_position, \
                func.ST_PointFromText('point(' + str(lon) + ' ' + str(lat) + ')')
                )
            stop_query = db.session.query(Stop, distance_col)
            stop_query = stop_query.order_by(asc(distance_col))
            result = stop_query.first()
            # print('stop name is ' + result[0].stop_name)
            # print('distance is -> ' + str(result[1]))
            
            stop = result[0]

        return stop

    log.debug('get_stops_by_route: Starting search for route \"' + route_shortname + '\", at ' + str(jrny_time))

    stoptimes_whole_trip = []
    if (route_shortname is None) or (jrny_time is None) \
        or (departure_stop_name is None) or (departure_stop_lat is None) or (departure_stop_lon is None) \
        or (arrival_stop_name is None) or (arrival_stop_lat is None) or (arrival_stop_lon is None):
        # required parameters missing
        # ALERT the LERTS!!!!!
        pass
    else:
        # Look up routes for supplied short name. Should always find some...  we
        # don't cater for 'no routes found' scenario
        routes = db.session.query(Routes.route_id)
        routes = routes.filter(Routes.route_long_name == route_name)
        routes = routes.filter(Routes.route_short_name == route_shortname)
        routes = routes.order_by(text('route_id asc'))

        routes_for_shortname = []
        for r in routes.all():
            routes_for_shortname.append(r.route_id)
        log.debug('\tFound ' + str(len(routes_for_shortname)) + ' routes for shortname ' + route_shortname)
        
        # We now how a list of route_ids, we can use that list to get a list of trips
        # for those routes...  we don't cater for 'no trips found' scenario
        trips = db.session.query(Trips)
        trips = trips.filter(Trips.route_id.in_(routes_for_shortname))

        # Extract a list of trip_id's from the 'trips' query result...
        trips_for_routes = []
        for t in trips.all():
            trips_for_routes.append(t.trip_id)
        log.debug('\tFound ' + str(len(trips_for_routes)) + ' trips for above routes.')

        # Identify the departure stop (by name ideally, if that fails then by lat/lon)
        depstop = _identify_stop(db, departure_stop_name, departure_stop_lat, departure_stop_lon)
        log.debug('\tIdentified departure stop -> ' + depstop.stop_name)

        # Identify the departure stop (by name ideally, if that fails then by lat/lon)
        arrstop = _identify_stop(db, arrival_stop_name, arrival_stop_lat, arrival_stop_lon)
        log.debug('\tIdentified arrival stop -> ' + arrstop.stop_name)

        # ***
        # THIS IS THE MAGIC - WHERE ROUTES, STEPS... BECOME A SINGLE TRIP
        trip_from_stoptimes = db.session.query(StopTime.trip_id)
        #stop_times_query = stop_times_query.join(Stop, Stop.stop_id == StopTime.stop_id)
        trip_from_stoptimes = trip_from_stoptimes.filter(StopTime.trip_id.in_(trips_for_routes))
        # Additionally filtering by 'trip_headsign' in most cases ensures we never
        # mistake an inbound trip for an outbound trip.
        if stop_headsign:
            # A lot of the GTFS data have leading spaces, the google data does not...
            # ... so func.ltrim
            trip_from_stoptimes = trip_from_stoptimes.filter(func.ltrim(StopTime.stop_headsign) == stop_headsign)
        trip_from_stoptimes = trip_from_stoptimes.filter(StopTime.stop_id == depstop.stop_id)
        trip_from_stoptimes = trip_from_stoptimes.filter(StopTime.arrival_time <= jrny_time)
        trip_from_stoptimes = trip_from_stoptimes.order_by(text('arrival_time desc'))
        #log.debug('\tMost likely trip query:', trip_from_stoptimes.statement.compile(compile_kwargs={"literal_binds": True}))
        trip_query_result = trip_from_stoptimes.limit(1).all()

        trip_id = None
        for row in trip_query_result:
            trip_id = row[0]
            log.debug('\tMost likely trip identified: ' + str(trip_id))

        # At this point we've hopefully identified the * most likely * trip_id for
        # the requested journey! Sweet - now we just return the list of stops for
        # this trip_id!
        step_stops  = []
        if trip_id:
            stepstops_info_for_trip = db.session.query(StopTime.stop_sequence, StopTime.shape_dist_traveled, Stop)
            stepstops_info_for_trip = stepstops_info_for_trip.join(Stop, StopTime.stop_id == Stop.stop_id)
            stepstops_info_for_trip = stepstops_info_for_trip.filter(StopTime.trip_id == trip_id)
            stepstops_info_for_trip = stepstops_info_for_trip.order_by(text('stop_sequence'))
            # All stops selected, omit stop_times detail
            stoptimes_whole_trip = stepstops_info_for_trip.all()

            stops_in_step = False
            # 'stoptimes_whole_trip' is in stop_sequence order remember...
            for row in stoptimes_whole_trip:
                stop = row[2]
                if (stop.stop_id == depstop.stop_id) or (stops_in_step):
                    step_stops.append(StepStop(stop, row[0], row[1]))
                    stops_in_step = True
                if (stop.stop_id == arrstop.stop_id):
                    stops_in_step = False
                    break

    # NOTE step_stops may well be empty.  We can only do our best!!
    return step_stops


def weather_information(inputtime):
    """
    """
    # Call the weather prediction service
    # This returns hourly weather predictions for four days from now
    url=credentials['open-weather']['url'] \
        + '?lat=' + str(CONST_DUBLIN_CC[0]) \
        + '&lon=' + str(CONST_DUBLIN_CC[1]) \
        + '&appid=' + credentials['open-weather']['api-key']
    weather_json = rq.get(url).json()
    log.debug(weather_json)
    #weatherforecast_json = request_weatherforecast_data(latitude=str(position_lat), longitude=str(position_lng))
    
    # Loop over the hourly data - find the first hour??? @YC - What about date??
    predicted_temp = None
    for each_hour_data in weather_json['list']:
        forecast_datetime = datetime.fromtimestamp(each_hour_data['dt'])
        hour=forecast_datetime.hour
        if hour==inputtime:
            predicted_temp = each_hour_data['main']['temp']

    return predicted_temp


def predict_journey_time(journey_prediction):
    """Predict the journey timee for journey represented by the 'prediction_request' object

    Returns an updated JourneyPrediction model.
    If the pickle for the prediction model exists we use the end-to-end model.
    Else we use the stop-to-stop model.
    """
    if journey_prediction.get_route_shortname_pickle_exists():
        journey_prediction = _predict_jt_end_to_end(journey_prediction)
    else:
        journey_prediction = _predict_jt_stop_to_stop(journey_prediction)

    return journey_prediction


def _predict_jt_end_to_end(journey_prediction):
    """Predict the journey timee for journey represented by the 'prediction_request' object

    Returns an updated JourneyPrediction model.
    Uses the end-to-end model
    """
  
    # Pull the required information from the JourneyPrediction object.
    duration = journey_prediction.get_planned_duration_s()
    time = journey_prediction.get_planned_departure_datetime()
    hour=time.hour
    week=time.isoweekday()
    month=time.month
    lineid=journey_prediction.get_route_shortname()
    temperature=weather_information(hour)

    week_sin= np.sin(2 * np.pi * week/6.0)
    week_cos = np.cos(2 * np.pi * week/6.0)
    hour_sin = np.sin(2 * np.pi * hour/23.0)
    hour_cos  = np.cos(2 * np.pi * hour/23.0)
    month_sin = np.sin(2 * np.pi * month/12.0)
    month_cos  = np.cos(2 * np.pi * month/12.0)

    # load the prediction model
    end_to_end_filepath='pickles/end_to_end/'+lineid+".pickle"
    #  f = open('test_rfc.pickle','rb')
    f= open(os.path.join(jt_utils_dir, end_to_end_filepath), 'rb')
    model_for_line = pickle.load(f)
    f.close()

    # create a pandas dataframe
    #dic_list = [{'PLANNED_JOURNEY_TIME':duration,'HOUR':10,'temp':6.8,'week':6,'Month':1}]
    dic_list = [{'PLANNED_JOURNEY_TIME':duration,'week_sin':week_sin,'week_cos':week_cos,'hour_sin':hour_sin,'hour_cos':hour_cos,'month_sin':month_sin,'month_cos':month_cos,'temp':temperature}]  
    input_to_pickle_data_frame = pd.DataFrame(dic_list)
    # Pass the dataframe into model and predict time 
    # !!! Model returns a NumPy NDArray - not a number! Grab the number from the array...
    predict_result=model_for_line.predict(input_to_pickle_data_frame)[0]
    journey_prediction.set_predicted_duration_s(predict_result)

    # With the end-to-end time predicted we need to split the journey time out
    # so we can display 'stop by stop' journey time predictions.  We do this
    # proportionally using distance along the shape travelled.  This is not
    # fantastic, but sufficient to give the user an idea of the predicted
    # arrival times:
    list_of_stops_for_journey = journey_prediction.get_step_stpps()

    last_stop = list_of_stops_for_journey[-1]
    first_stop = list_of_stops_for_journey[0]
    total_dis_m = last_stop.get_shape_dist_traveled() - first_stop.get_shape_dist_traveled()

    for index,stepstop in enumerate(list_of_stops_for_journey):
        stepstop_current = stepstop
        if index != 0:
            stepstop_prev = stepstop_current
            stepstop_current  = stepstop
            
            dist__from_last_stop=stepstop_current.get_shape_dist_traveled() - stepstop_prev.get_shape_dist_traveled()
            predicted_time_stop_to_stop=predict_result*(dist__from_last_stop/total_dis_m)

            # Set the predicted journey time on the current 'StepStop' Object
            stepstop_current.set_shape_predicted_time_traveled_s(predicted_time_stop_to_stop)

    #journey_prediction.set_predicted_duration_s(600)

    return journey_prediction  # Return the updated prediction_request


def _predict_jt_stop_to_stop(journey_prediction):
    """Predict the journey timee for journey represented by the 'prediction_request' object

    Returns an updated JourneyPrediction model.
    Uses the stop-to-stop model
    """

    # load the prediction model
    stop_to_stop_filepath='pickles/stop_to_stop/stoptostop2.pickle'
    #  f = open('test_rfc.pickle','rb')
    f= open(os.path.join(jt_utils_dir, stop_to_stop_filepath), 'rb')
    # TODO:: Agree what action we should take if the pickle is invalid/not found.
    model_stop_to_stop = pickle.load(f)
    f.close()

    duration = journey_prediction.get_planned_duration_s()
    time = journey_prediction.get_planned_departure_datetime()
    hour=time.hour
    week=time.isoweekday()
    # month=time.month
    # lineid=journey_prediction.get_route_shortname()
    temperature=weather_information(hour)
    #temperature=20
    week_sin= np.sin(2 * np.pi * week/6.0)
    week_cos = np.cos(2 * np.pi * week/6.0)
    hour_sin = np.sin(2 * np.pi * hour/23.0)
    hour_cos  = np.cos(2 * np.pi * hour/23.0)
    #  month_sin = np.sin(2 * np.pi * month/12.0)
    #  month_cos  = np.cos(2 * np.pi * month/12.0)

    list_of_stops_for_journey = journey_prediction.get_step_stpps()

    total_dis_m=0.001  # Sensible default - avoid divide by zero error
    total_time=0

    last_stop = list_of_stops_for_journey[-1]
    first_stop = list_of_stops_for_journey[0]
    total_dis_m = last_stop.get_shape_dist_traveled() - first_stop.get_shape_dist_traveled()

    for index,stepstop in enumerate(list_of_stops_for_journey):
        if index != 0:
            stepstop_prev = list_of_stops_for_journey[index-1]
            stepstop_now  = stepstop
            
            stop_prev_dist_from_cc = stepstop_prev.get_stop().dist_from_cc
            stop_now_dist_from_cc = stepstop_now.get_stop().dist_from_cc

            dis_twostop=stepstop_now.get_shape_dist_traveled() - stepstop_prev.get_shape_dist_traveled()

            plantime_partial=duration*(dis_twostop/total_dis_m)

            #dic_list = [{'PLANNED_JOURNEY_TIME':duration,'HOUR':10,'temp':6.8,'week':6,'Month':1}]
            dic_list = [
                {'PLANNED_JOURNEY_TIME':plantime_partial,	'dis_twostop':dis_twostop, \
                'dis_prestop_city':stop_prev_dist_from_cc, 'dis_stopnow_city':stop_now_dist_from_cc, \
                'temp':temperature,'week_sin':week_sin,'week_cos':week_cos,'hour_sin':hour_sin,'hour_cos':hour_cos}
                ]

            input_to_pickle_data_frame = pd.DataFrame(dic_list)
            # throw the dataframe into model and predict time 
            # !!! Model returns a NumPy NDArray - not a number! Grab the number from the array...
            predict_result=model_stop_to_stop.predict(input_to_pickle_data_frame)[0]
            # Set the predicted journey time on the current 'StepStop' Object
            stepstop_now.set_shape_predicted_time_traveled_s(predict_result)

            total_time=predict_result+total_time
            
    # At the end set the total predicted journey time on the journey_prediction object
    log.debug(predict_result)
    journey_prediction.set_predicted_duration_s(total_time)

    return journey_prediction  # Return the updated rediction_request


def time_rounded_to_hrs_mins_as_string(seconds):
    """Time (seconds) supplied converted to a String as hrs and mins

    Timne is rounded to the nearest minute.
    """
    # divmod() accepts two ints as parameters, returns a tuple containing the quotient and remainder of their division
    mins, secs = divmod(seconds, 60)  # secs is 'remaining seconds', we don't show them, but used for rounding...
    hrs, mins = divmod(mins,60)
    if secs >= 30:
        mins += 1

    time_string = ''
    if hrs > 0:
        time_string += str(hrs) + ' hrs, '
    time_string += str(mins) + ' mins'  # Rounded to nearest minute...

    return time_string

#===============================================================================
#===============================================================================
#===============================================================================

def main():
    """Only Used for Testing

    """

    print('JT_Utils: Main Method')
    pickles_dir='pickles'
    pickle_path= os.path.join(jt_utils_dir, pickles_dir)

    with (open(os.path.join(pickle_path, 'JourneyPrediction-r0-s0.pickle'), "rb")) as jp_pickle:
        journey_pred = pickle.load(jp_pickle)
        # # Call a function to get the predicted journey time for this step.
        journey_pred = predict_journey_time(journey_pred)

    sys.exit()

if __name__ == '__main__':
    main()