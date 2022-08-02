# -*- coding: utf-8 -*-
"""jt_utils: General Purpose Utility module for the Journeyti.me Web Application
"""

# Standard Library Imports
from datetime import datetime
import json
import logging
from pathlib import Path
import pickle
import os
import sys
import struct
import time
import zlib

# Related Third Party Imports
from flask import Response
import numpy as np
import pandas as pd
import requests as rq
from sqlalchemy import asc, text, func
#from sqlalchemy.dialects import mysql
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound  # Exceptions


# Local Application Imports
from models import Routes, Stop, StopTime, Trips

# According to the article here:
#   https://towardsdatascience.com
#     /simple-trick-to-work-with-relative-paths-in-python-c072cdc9acb9
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
    with open( \
        os.path.join(jt_utils_parent_dir, 'journeytime.json'), \
        'r', \
        encoding="utf-8" \
        ) as file:
        _credentials = json.load(file)

    return _credentials


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
    chunk_size = int(credentials['DOWNLOAD_CHUNK_SIZE'])
    rows_chunk = 0
    if rows_remain > 0:
        if rows_remain >= chunk_size:
            rows_chunk  = chunk_size
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
        #   -> https://stackoverflow.com/questions
        #          /44185486/generate-and-stream-compressed-file-with-flask
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
        last_row_pk    = 0

        # I still got memory overruns trying to use query.yield_per()... which
        # looked almost tailor made for our objective.  So perhaps I was doing
        # something wrong...
        # query.yield_per(rows_chunk)

        # Instead I did an old fashioned loop to let me use smaller queries, to
        # keep the memory footprint down...
        while True:
            rows_this_chunk = query.filter(model.id > last_row_pk).limit(rows_chunk).all()
            if not rows_this_chunk or len(rows_this_chunk) == 0:
                break
            for row in rows_this_chunk:
                last_row_pk = row.id

                # If we build up the string we plan to send by repeatedly appending,
                # we're creating a new string each time. This is quite memory expensive
                # and inefficient.
                # Instead we build a list of strings - which we will later convert to
                # a single string.
                # 'row_list' will be a list of strings...
                row_list.append( \
                    '"' \
                    + '","'.join([str(value) for value in row.serialize().values()]) \
                    + '"')
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
    response.headers['Content-Disposition'] = \
        'attachment; filename=' + model.__table__.name + '.csv.gz'
    return response


def query_results_as_json(model, query, **kwargs):
    """

    Returns a JSON List with one object per record in the query result set.
    """
    incl_limit_exceeded_warning = False
    if 'limit_exceeded' in kwargs:
        if kwargs['limit_exceeded'] is True:
            incl_limit_exceeded_warning = True

    def get_chunk(json_list, first_chunk, name):
        if first_chunk:
            chunk = '{\n'
            if incl_limit_exceeded_warning:
                dl_lim_json        = credentials['DOWNLOAD_ROW_LIMIT_JSON']
                dl_lim_json_attach = credentials['DOWNLOAD_ROW_LIMIT_JSON_ATTACHMENT']

                chunk += '\"filesize_warning\": {\n'
                chunk += '\"1_warning\": \"WARNING\",\n'
                chunk += '\"2_description\": ' \
                    + '\"The number of records in this extract exceeds the current ' \
                    + 'streamed .json file limit\",\n'
                chunk += '\"3_limits1\": ' \
                    + '\"A maximum of ' + dl_lim_json + ' records can be delivered ' \
                    + 'directly to a clients browswer\",\n'
                chunk += '\"4_limits2\": ' \
                    + '\"A maximum of ' + dl_lim_json_attach + ' records can be ' \
                    + 'delivered as a .json file attachment\",\n'
                chunk += '\"5_limits3\": ' \
                    + '\"There is currently no limit on filesizes downloaded as ' \
                    + 'compressed .csv.gz\"\n'
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
                log.debug("\tRows Remaining -> %d", rows_remain)
                log.debug("\tRows This Chunk -> %d", rows_chunk)

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

    # pylint: disable=too-many-instance-attributes
    # Twelve is reasonable in this case (6 property, 6 private).
    # (pylint counts BOTH properties and the associated private variables)

    def __init__( \
            self, route_shortname, route_shortname_pickle_exists, \
            planned_duration_s, planned_departure_datetime, \
            step_stops
            ):
        # Instance Variables
        self.route_shortname = route_shortname
        self.route_shortname_pickle_exists = route_shortname_pickle_exists
        self.planned_duration_s = planned_duration_s
        self.planned_departure_datetime = planned_departure_datetime
        # 'step_stops' is a list of StepStop model objects for the current journey step.
        self.step_stops = step_stops
        self.predicted_duration_s = 0

    @property
    def route_shortname(self):
        """The route shortname for this journey."""
        return self.__route_shortname
    @property
    def route_shortname_pickle_exists(self):
        """If a 'route shortname' (a.k.a. 'end-to-end') pickle exists for this journey."""
        return self.__route_shortname_pickle_exists
    @property
    def planned_duration_s(self):
        """The planned duration for this journey."""
        return self.__planned_duration_s
    @property
    def planned_departure_datetime(self):
        """The planned departure datetime for this journey."""
        return self.__planned_departure_datetime
    @property
    def step_stops(self):
        """The list of step-stops for this journey."""
        return self.__step_stops
    @property
    def predicted_duration_s(self):
        """The predicted duration in s for this journey."""
        return self.__predicted_duration_s

    @route_shortname.setter
    def route_shortname(self, route_shortname):
        self.__route_shortname = route_shortname
    @route_shortname_pickle_exists.setter
    def route_shortname_pickle_exists(self, route_shortname_pickle_exists):
        self.__route_shortname_pickle_exists = route_shortname_pickle_exists
    @planned_duration_s.setter
    def planned_duration_s(self, planned_duration_s):
        self.__planned_duration_s = planned_duration_s
    @planned_departure_datetime.setter
    def planned_departure_datetime(self, planned_departure_datetime):
        self.__planned_departure_datetime = planned_departure_datetime
    @step_stops.setter
    def step_stops(self, step_stops):
        self.__step_stops = step_stops
    @predicted_duration_s.setter
    def predicted_duration_s(self, predicted_duration_s):
        self.__predicted_duration_s = predicted_duration_s


class StepStop:
    """Model representing a stop on one step of a journey (part of a 'trip')

    """

    # pylint: disable=too-many-instance-attributes
    # Ten is reasonable in this case (5 property, 5 private).
    # (pylint counts BOTH properties and the associated private variables)

    def __init__(self, stop, stop_sequence, shape_dist_traveled):
        # Instance Variables
        self.stop = stop
        self.stop_sequence = stop_sequence
        self.shape_dist_traveled = shape_dist_traveled
        self.dist_from_first_stop_m = 0
        self.predicted_time_from_first_stop_s = 0

    @property
    def stop(self):
        """A stop model."""
        return self.__stop
    @property
    def stop_sequence(self):
        """The sequence number of this stop, in a step."""
        return self.__stop_sequence
    @property
    def shape_dist_traveled(self):
        """The distance traveled from the terminus to this stop."""
        return self.__shape_dist_traveled
    @property
    def dist_from_first_stop_m(self):
        """The distance from the first stop in this step."""
        return self.__dist_from_first_stop_m
    @property
    def predicted_time_from_first_stop_s(self):
        """The time from the first stop in this step."""
        return self.__predicted_time_from_first_stop_s

    @stop.setter
    def stop(self, stop):
        self.__stop = stop
    @stop_sequence.setter
    def stop_sequence(self, stop_sequence):
        self.__stop_sequence = stop_sequence
    @shape_dist_traveled.setter
    def shape_dist_traveled(self, shape_dist_traveled):
        self.__shape_dist_traveled = shape_dist_traveled
    @dist_from_first_stop_m.setter
    def dist_from_first_stop_m(self, dist_from_first_stop_m):
        self.__dist_from_first_stop_m = dist_from_first_stop_m
    @predicted_time_from_first_stop_s.setter
    def predicted_time_from_first_stop_s(self, predicted_time_from_first_stop_s):
        self.__predicted_time_from_first_stop_s = predicted_time_from_first_stop_s

    def serialize(self):
        """Return object data in easily serializeable format"""
        return  {
            'stop_id': self.stop.stop_id,
            'stop_name': self.stop.stop_name,
            'stop_lat': self.stop.stop_lat,
            'stop_lon': self.stop.stop_lon,
            'stop_sequence': self.stop_sequence,
            'stop_shape_dist_traveled': self.shape_dist_traveled,
            'stop_dist_from_first_stop_m': self.dist_from_first_stop_m,
            'stop_predicted_time_from_first_stop_s': self.predicted_time_from_first_stop_s
        }


def get_available_end_to_end_models():
    """Return a list of all End-to-End model pickles currently on disk
    """
    available_model_names = []
    end_to_end_model_dir = jt_utils_dir + '/pickles/end_to_end'

    # iterate over files in that directory
    files = Path(end_to_end_model_dir).glob('*.pickle')
    for file in files:
        available_model_names.append(Path(file).stem)

    return available_model_names


def get_valid_route_shortnames(database):
    """Return a list of all valid route shortnamees
    """
    valid_route_shortnames = []

    route_shortname_query = database.session.query(Routes.route_short_name)
    route_shortname_query = route_shortname_query.order_by(asc(Routes.route_short_name))
    route_shortnames = route_shortname_query.all()
    if len(route_shortnames) > 0:
        valid_route_shortnames = [row[0] for row in route_shortnames]
        log.debug('\tFound %d route-shortnames', len(valid_route_shortnames))

    return valid_route_shortnames


def get_stops_by_route(database, route_name, route_shortname, \
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

    def _identify_stop(database, name, lat, lon):
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
            stop_query = database.session.query(Stop)
            stop_query = stop_query.filter(Stop.stop_name == name)
            stop = stop_query.one()
        except NoResultFound:
            # log.warning('\tNo Stops found for stop name: ' + name)
            log.debug('\tNo stop found based on name %s', name)
            position_match_required = True
        except MultipleResultsFound:
            # log.warning('\tMultiple Stops found for stop name: ' + name)
            log.debug('\tMultiple stops found based on name %s', name)
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
            # result = database.engine.execute(raw_sql).one()
            #position = func.ST_MakePoint(lon, lat)

            # MySQL Spatial Function reference:
            #   https://dev.mysql.com/doc/refman/8.0/en/spatial-function-reference.html
            distance_col = func.ST_Distance_Sphere( \
                Stop.stop_position, \
                func.ST_PointFromText('point(' + str(lon) + ' ' + str(lat) + ')')
                )
            stop_query = database.session.query(Stop, distance_col)
            stop_query = stop_query.order_by(asc(distance_col))
            result = stop_query.first()
            # print('stop name is ' + result[0].stop_name)
            # print('distance is -> ' + str(result[1]))

            stop = result[0]
            log.debug('\tBest match for lat %s and lon %s is stop %s (at lat %s, lon %s)', \
                lat, lon, stop.stop_name, stop.stop_lat, stop.stop_lon)

        return stop

    log.debug(
        'get_stops_by_route: Starting search for route \"%s\", at %s',
        route_shortname, str(jrny_time))

    stoptimes_whole_trip = []
    if (route_shortname is None) or (jrny_time is None) \
        or (departure_stop_name is None) \
        or (departure_stop_lat is None) or (departure_stop_lon is None) \
        or (arrival_stop_name is None) \
        or (arrival_stop_lat is None) or (arrival_stop_lon is None):
        # required parameters missing
        # ALERT the LERTS!!!!!
        pass
    else:
        # First - identify the stops!
        # Identify the departure stop (by name ideally, if that fails then by lat/lon)
        depstop = _identify_stop(
            database, departure_stop_name, departure_stop_lat, departure_stop_lon
            )
        log.debug('\tIdentified departure stop -> %s', depstop.stop_name)

        # Identify the departure stop (by name ideally, if that fails then by lat/lon)
        arrstop = _identify_stop(
            database, arrival_stop_name, arrival_stop_lat, arrival_stop_lon
            )
        log.debug('\tIdentified arrival stop -> %s', arrstop.stop_name)

        #----------

        routes_for_shortname, poor_route_matching = \
            _search_for_routes(database, route_name, route_shortname)

        trips_for_routes = _trips_for_route_ids(database, routes_for_shortname)

        # ***
        # THIS IS THE MAGIC - WHERE ROUTES, STEPS... BECOME A SINGLE TRIP
        # ***

        if poor_route_matching:
            # Replace the 'poor_route_matching' list with our freshly filtered list
            filtered_trips_list = \
                _trips_with_stops_in_correct_order(
                    database, trips_for_routes, depstop, arrstop
                    )

            trips_for_routes.clear()
            trips_for_routes.extend(filtered_trips_list)

        trip_from_stoptimes = database.session.query(StopTime.trip_id)
        #stop_times_query = stop_times_query.join(Stop, Stop.stop_id == StopTime.stop_id)
        trip_from_stoptimes = trip_from_stoptimes.filter(StopTime.trip_id.in_(trips_for_routes))
        # Additionally filtering by 'trip_headsign' in most cases ensures we never
        # mistake an inbound trip for an outbound trip.
        if stop_headsign:
            # A lot of the GTFS data have leading spaces, the google data does not...
            # ... so func.ltrim
            trip_from_stoptimes = \
                trip_from_stoptimes.filter(func.ltrim(StopTime.stop_headsign) == stop_headsign)
        trip_from_stoptimes = trip_from_stoptimes.filter(StopTime.stop_id == depstop.stop_id)
        trip_from_stoptimes = trip_from_stoptimes.filter(StopTime.arrival_time <= jrny_time)  #!!<-
        trip_from_stoptimes = trip_from_stoptimes.order_by(text('arrival_time desc'))
        #log.debug('\tMost likely trip query:', \
        # trip_from_stoptimes.statement.compile(compile_kwargs={"literal_binds": True}))
        trip_query_result = trip_from_stoptimes.limit(1).all()

        trip_id = None
        for row in trip_query_result:
            trip_id = row[0]
            log.debug('\tMost likely trip identified: %s', trip_id)

        # At this point we've hopefully identified the * most likely * trip_id for
        # the requested journey! Sweet - now we just return the list of stops for
        # this trip_id!
        step_stops  = []
        if trip_id:
            stepstops_info_for_trip = \
                database.session.query(StopTime.stop_sequence, StopTime.shape_dist_traveled, Stop)
            stepstops_info_for_trip = \
                stepstops_info_for_trip.join(Stop, StopTime.stop_id == Stop.stop_id)
            stepstops_info_for_trip = \
                stepstops_info_for_trip.filter(StopTime.trip_id == trip_id)
            stepstops_info_for_trip = \
                stepstops_info_for_trip.order_by(text('stop_sequence'))
            # All stops selected, omit stop_times detail
            stoptimes_whole_trip = stepstops_info_for_trip.all()

            stops_in_step = False
            # 'stoptimes_whole_trip' is in stop_sequence order remember...
            for row in stoptimes_whole_trip:
                stop = row[2]
                if (stop.stop_id == depstop.stop_id) or (stops_in_step):
                    step_stops.append(StepStop(stop, row[0], row[1]))
                    stops_in_step = True
                if stop.stop_id == arrstop.stop_id:
                    stops_in_step = False
                    break

    # NOTE step_stops may well be empty.  We can only do our best!!
    return step_stops

def _trips_for_route_ids(database, routes_ids):
    """Find all the trip_id's for the supplied list of route_id's
    """
    # We now have a list of route_ids, we can use that list to get a list of
    # trips for those routes...  we don't cater for 'no trips found' scenario
    trips = database.session.query(Trips)
    trips = trips.filter(Trips.route_id.in_(routes_ids))

        # Extract a list of trip_id's from the 'trips' query result...
    trip_ids_for_routes = []
    for trip in trips.all():
        trip_ids_for_routes.append(trip.trip_id)
    log.debug('\tFound %d trips for routes.', len(trip_ids_for_routes))

    return trip_ids_for_routes


def _trips_with_stops_in_correct_order(database, trips_for_routes, depstop, arrstop):
    """Filter a list of trips_ids, selecting only Trips where depstop preceeds arrstop
    """
    # If we didn't get an exact match on routes then it's likely we have both
    # inbound and outbound trips. Filter our trips - removing any trips where the
    # depstop is AFTER the arrstop (this implies a trip in the wrong direction)
    trips_with_stops_in_correct_order = []

    stoptimes_all_trips_query = database.session.query(StopTime)
            #stop_times_query = stop_times_query.join(Stop, Stop.stop_id == StopTime.stop_id)
    stoptimes_all_trips_query = \
        stoptimes_all_trips_query.filter(StopTime.trip_id.in_(trips_for_routes))
    stoptimes_all_trips_query = \
        stoptimes_all_trips_query.order_by(StopTime.trip_id.asc(),StopTime.stop_sequence.asc())
    stoptimes_all_trips = stoptimes_all_trips_query.all()

    log.debug(
            'Poor route matching cost us a loop over %d stoptimes records',
            len(stoptimes_all_trips)
            )

    # Iterate over the results in trip order
    wcurr_trip = ''
    for stoptime in stoptimes_all_trips:
                # On change of trip...
        if stoptime.trip_id != wcurr_trip:
            wcurr_trip = stoptime.trip_id
            wdepstop_found = False
            wfinished      = False

        if not wfinished:
            if stoptime.stop_id == depstop.stop_id:
                wdepstop_found = True

            if stoptime.stop_id == arrstop.stop_id:
                # We have found the arrival stop!
                # If the departure stop was already found for this trip then
                # the stops are in the correct order and we can proceed. If
                # not then this trip is a dud - we can just ignore it...
                if wdepstop_found:
                    trips_with_stops_in_correct_order.append(stoptime.trip_id)
                    wfinished = True

    return trips_with_stops_in_correct_order


def _search_for_routes(
        database, route_name, route_shortname):
    """Returns a list of the the 'most likely' Routes (sqlachemy models) for the supplied inputs
    Returns a boolean indicating if the match was good (both names) or poor (shortname only)

    Attempts to identify Route by exact match on shortname/name first.
    If that fails we load all routes by shortname, and then filter that list
    further using the depstop, arrstop information
    """
    # Look up routes for supplied shortname/name...
    routes_base_query = database.session.query(Routes.route_id)
    routes_base_query = routes_base_query.filter(Routes.route_short_name == route_shortname)
    routes_base_query = routes_base_query.order_by(text('route_id asc'))

    route_ids_by_name = []
    poor_match = False

    routes_full_match = routes_base_query.filter(Routes.route_long_name == route_name)
    if routes_full_match.count() > 0:
        # Great! This is the best solution - we found a full match - just grab
        # all these routes...
        for route in routes_full_match.all():
            route_ids_by_name.append(route.route_id)

        log.debug('\tFound %d routes on exact match shortname \"%s\" / name \"%s\"', \
            len(route_ids_by_name), route_shortname, route_name)
    else:
        # Awww... no exact match found.  What we do next is attempt to match on
        # just shortname. Testing has revealed many cases where the route
        # shortname is in the data - but the long name has been altered (e.g.
        # for the 155 our database shows a long name of "St.Margaret's Road -
        # Outside Train Station" but the google directions returns "Ballymun to Bray"
        for route in routes_base_query.all():
            # BUT this gives us BOTH inbound and outbound routes.  Which is bad
            # naturally... we only want to consider trips where the bus is going
            # in the correct direction!
            route_ids_by_name.append(route.route_id)

        poor_match = True

        log.debug('\tFound %d routes matched on shortname \"%s\" only', \
            len(route_ids_by_name), route_shortname)

    return route_ids_by_name, poor_match


def weather_information(inputtime):
    """Return the predicted temperature at the provided time.

    Uses the open-weather weather prediction service.
    """
    # Call the weather prediction service
    # This returns hourly weather predictions for four days from now
    url=credentials['open-weather']['url'] \
        + '?lat=' + str(CONST_DUBLIN_CC[0]) \
        + '&lon=' + str(CONST_DUBLIN_CC[1]) \
        + '&appid=' + credentials['open-weather']['api-key']
    weather_json = rq.get(url).json()
    # Following produces a lot of json... only enable when required.
    #log.debug(weather_json)
    #weatherforecast_json = \
    # request_weatherforecast_data(latitude=str(position_lat), longitude=str(position_lng))

    # Loop over the hourly data - find the first hour??? @YC - What about date??
    predicted_temp = None
    for each_hour_data in weather_json['list']:
        forecast_datetime = datetime.fromtimestamp(each_hour_data['dt'])
        hour=forecast_datetime.hour
        if hour==inputtime:
            predicted_temp = each_hour_data['main']['temp']

    return predicted_temp


def predict_journey_time(journey_prediction, model_stop_to_stop):
    """Predict the journey timee for journey represented by the 'prediction_request' object

    Returns an updated JourneyPrediction model.
    If the pickle for the prediction model exists we use the end-to-end model.
    Else we use the stop-to-stop model.
    """
    if journey_prediction.route_shortname_pickle_exists:
        journey_prediction = _predict_jt_end_to_end(journey_prediction)
    else:
        # TODO - should we abort here if not step-stops information exists!
        journey_prediction = _predict_jt_stop_to_stop(journey_prediction, model_stop_to_stop)

    return journey_prediction


def _predict_jt_end_to_end(journey_prediction):
    """Predict the journey timee for journey represented by the 'prediction_request' object

    Returns an updated JourneyPrediction model.
    Uses the end-to-end model
    """

    # Pull the required information from the JourneyPrediction object.
    duration = journey_prediction.planned_duration_s
    planned_departure_datetime = journey_prediction.planned_departure_datetime
    hour=planned_departure_datetime.hour
    week=planned_departure_datetime.isoweekday()
    month=planned_departure_datetime.month
    lineid=journey_prediction.route_shortname
    temperature=weather_information(hour)

    week_sin  = np.sin(2 * np.pi * week/6.0)
    week_cos  = np.cos(2 * np.pi * week/6.0)
    hour_sin  = np.sin(2 * np.pi * hour/23.0)
    hour_cos  = np.cos(2 * np.pi * hour/23.0)
    month_sin = np.sin(2 * np.pi * month/12.0)
    month_cos = np.cos(2 * np.pi * month/12.0)

    # load the prediction model
    end_to_end_filepath=os.path.join(jt_utils_dir, 'pickles')
    end_to_end_filepath=os.path.join(end_to_end_filepath, 'end_to_end' )
    end_to_end_filepath=os.path.join(end_to_end_filepath, lineid+'.pickle' )
    with open(end_to_end_filepath, 'rb') as file:
        model_for_line = pickle.load(file)

    # create a pandas dataframe
    #dic_list = [{'PLANNED_JOURNEY_TIME':duration,'HOUR':10,'temp':6.8,'week':6,'Month':1}]
    dic_list = [
        {'PLANNED_JOURNEY_TIME':duration,
        'week_sin':week_sin,'week_cos':week_cos,
        'hour_sin':hour_sin,'hour_cos':hour_cos,
        'month_sin':month_sin,'month_cos':month_cos,
        'temp':temperature}
        ]
    input_to_pickle_data_frame = pd.DataFrame(dic_list)
    # Pass the dataframe into model and predict time
    # !!! Model returns a NumPy NDArray - not a number! Grab the number from the array...
    predict_result=model_for_line.predict(input_to_pickle_data_frame)[0]
    log.debug("\tEnd-to-end prediction result -> %d", predict_result)
    journey_prediction.predicted_duration_s = predict_result

    # With the end-to-end time predicted we need to split the journey time out
    # so we can display 'stop by stop' journey time predictions.  We do this
    # proportionally using distance along the shape travelled.  This is not
    # fantastic, but sufficient to give the user an idea of the predicted
    # arrival times:
    list_of_stops_for_journey = journey_prediction.step_stops

    # There will be cases where we fail to identify a list of stops for a route
    # In these cases we don't want to crash - we simply ignore the missing information...
    if len(list_of_stops_for_journey) > 0:
        # Assuming we have a stop-to-stop journey breakdown available...
        # ... portion out the time for the journey based on % fraction of the
        # total journey distance.
        start_distance = list_of_stops_for_journey[0].shape_dist_traveled
        end_distance = list_of_stops_for_journey[-1].shape_dist_traveled

        total_dis_m = end_distance - start_distance

        cumulative_time = 0
        for index,stepstop in enumerate(list_of_stops_for_journey):
            stepstop_current = stepstop
            if index != 0:
                stepstop_prev = stepstop_current
                stepstop_current  = stepstop

                dist_from_last_stop = \
                    stepstop_current.shape_dist_traveled - stepstop_prev.shape_dist_traveled
                predicted_time_stop_to_stop=predict_result*(dist_from_last_stop/total_dis_m)

                cumulative_time += + predicted_time_stop_to_stop

                # Set the predicted journey distance/time on the current 'StepStop' Object
                stepstop_current.dist_from_first_stop_m = \
                    stepstop_current.shape_dist_traveled - start_distance
                stepstop_current.predicted_time_from_first_stop_s = cumulative_time

    #journey_prediction.predicted_duration_s = 600

    return journey_prediction  # Return the updated prediction_request


def _predict_jt_stop_to_stop(journey_prediction, model_stop_to_stop):
    """Predict the journey timee for journey represented by the 'prediction_request' object

    Returns an updated JourneyPrediction model.
    Uses the stop-to-stop model
    ASSUMES the stop to stop model is in memory (global) as 'CONST_MODEL_STOP_TO_STOP'
    """

    duration = journey_prediction.planned_duration_s
    planned_departure_datetime = journey_prediction.planned_departure_datetime
    hour=planned_departure_datetime.hour
    week=planned_departure_datetime.isoweekday()
    # month=time.month
    # lineid=journey_prediction.route_shortname
    temperature=weather_information(hour)
    #temperature=20
    week_sin= np.sin(2 * np.pi * week/6.0)
    week_cos = np.cos(2 * np.pi * week/6.0)
    hour_sin = np.sin(2 * np.pi * hour/23.0)
    hour_cos  = np.cos(2 * np.pi * hour/23.0)
    #  month_sin = np.sin(2 * np.pi * month/12.0)
    #  month_cos  = np.cos(2 * np.pi * month/12.0)

    list_of_stops_for_journey = journey_prediction.step_stops

    total_dis_m=0.001  # Sensible default - avoid divide by zero error
    total_time=0

    if len(list_of_stops_for_journey) > 0:
        # Assuming we have a stop-to-stop journey breakdown available...
        # ... portion out the time for the journey based on % fraction of the
        # total journey distance.
        start_distance = list_of_stops_for_journey[0].shape_dist_traveled
        end_distance = list_of_stops_for_journey[-1].shape_dist_traveled

        total_dis_m = end_distance - start_distance

        cumulative_time = 0
        for index,stepstop in enumerate(list_of_stops_for_journey):
            if index != 0:
                stepstop_prev = list_of_stops_for_journey[index-1]
                stepstop_now  = stepstop

                stop_prev_dist_from_cc = stepstop_prev.stop.dist_from_cc
                stop_now_dist_from_cc = stepstop_now.stop.dist_from_cc

                dis_twostop = \
                    stepstop_now.shape_dist_traveled - stepstop_prev.shape_dist_traveled

                plantime_partial=duration*(dis_twostop/total_dis_m)

                #dic_list = [{'PLANNED_JOURNEY_TIME':duration,'HOUR':10,'temp':6.8,'week':6,'Month':1}]
                dic_list = [
                    {'PLANNED_JOURNEY_TIME':plantime_partial, \
                    'dis_twostop':dis_twostop, \
                    'dis_prestop_city':stop_prev_dist_from_cc, \
                    'dis_stopnow_city':stop_now_dist_from_cc, \
                    'temp':temperature, \
                    'week_sin':week_sin,'week_cos':week_cos, \
                    'hour_sin':hour_sin,'hour_cos':hour_cos}
                    ]
                input_to_pickle_data_frame = pd.DataFrame(dic_list).values
                # throw the dataframe into model and predict time
                # !!! Model returns a NumPy NDArray - not a number! Grab the number from the array...
                predict_result=model_stop_to_stop.predict(input_to_pickle_data_frame)[0]
                log.debug("\tStop-to-stop prediction result -> %d", predict_result)
                cumulative_time += predict_result

                # Set the predicted journey distance/time on the current 'StepStop' Object
                stepstop_now.dist_from_first_stop_m = \
                    stepstop_now.shape_dist_traveled - start_distance
                stepstop_now.predicted_time_from_first_stop_s = cumulative_time

                total_time=predict_result+total_time

        # At the end set the total predicted journey time on the journey_prediction object
        log.debug(total_time)
        journey_prediction.predicted_duration_s = total_time
    else:
        # There will be cases where we fail to identify a list of stops for a route
        # In these cases we don't want to crash - we simply ignore the missing information...
        # Yes... for the stop-to-stop model failing to ID a route is a big problem...
        log.warning(
            'No Route Breakdown (stop by stop) found for %s', \
            journey_prediction.route_shortname
        )

    return journey_prediction  # Return the updated rediction_request


def time_rounded_to_hrs_mins_as_string(seconds):
    """Time (seconds) supplied converted to a String as hrs and mins

    Timne is rounded to the nearest minute.
    """
    # divmod() accepts two ints as parameters, returns a tuple containing the
    # quotient and remainder of their division
    mins, secs = divmod(seconds, 60)  # secs is 'remaining seconds'
                                      # not shown, but used for rounding...
    hrs, mins = divmod(mins,60)
    if secs >= 30:
        mins += 1

    time_string = ''
    if hrs > 0:
        time_string += str(hrs) + 'hrs, '
    time_string += str(mins) + 'mins'  # Rounded to nearest minute...

    return time_string

#===============================================================================
#===============================================================================
#===============================================================================

def main():
    """Only Used for Testing

    """

    print('JT_Utils: Main Method')
    pickle_path= os.path.join(jt_utils_dir, 'pickles')

    stop_to_stop_filepath=os.path.join(pickle_path, 'stop_to_stop' )
    stop_to_stop_filepath=os.path.join(stop_to_stop_filepath, 'rfstoptostop.pickle' )
    with open(stop_to_stop_filepath, 'rb') as file:
        # TODO:: Agree what action we should take if the pickle is invalid/not found.
        model_stop_to_stop = pickle.load(file)

    with (open(os.path.join(pickle_path, 'JourneyPrediction-r15-s1.pickle'), "rb")) as jp_pickle:
        journey_pred = pickle.load(jp_pickle)
        # # Call a function to get the predicted journey time for this step.
        journey_pred = predict_journey_time(journey_pred, model_stop_to_stop)

    sys.exit()

if __name__ == '__main__':
    main()
