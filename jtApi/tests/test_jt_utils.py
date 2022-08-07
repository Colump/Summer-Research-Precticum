# -*- coding: utf-8 -*-
"""test_jt_utils: Unit Tests for jt_utils
"""

# Standard Library Imports
from datetime import datetime
import os
import sys
import traceback
import unittest

# Related Third Party Imports
import flask_testing
import sqlalchemy as sqlalchemy_db
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from sqlalchemy.orm import sessionmaker

# Local Application Imports
test_jt_utils_dir = os.path.dirname(__file__)
test_jt_utils_parent_dir = os.path.dirname(test_jt_utils_dir)
sys.path.insert(0, test_jt_utils_parent_dir)
from jt_flask_module import db, CONST_MODEL_STOP_TO_STOP, create_test_app
from jt_utils \
    import JourneyPrediction, StepStop, \
            load_credentials, _get_next_chunk_size, \
            query_results_as_compressed_csv, query_results_as_json, \
            get_available_end_to_end_models, get_valid_route_shortnames, \
            get_stops_by_route, weather_information, \
            predict_journey_time
from models import Agency, Trips

print('Test_JT_Utils: Loading credentials.')
credentials = load_credentials()

#-------------------------------------------------------------------------------

class TestBasicFunctions(unittest.TestCase):
    """Test 'basic' functions (simple logic, no db connections)
    """

    @classmethod
    def setUpClass(cls):
        print("Starting Basic Tests.")

    @classmethod
    def tearDownClass(cls):
        print("\tBasic Tests Complete.\n")


    def test_load_credentials(self):
        """Test function "load_credentials()"
        """
        creds = load_credentials()
        self.assertEqual(creds['DUBLIN_CC']['lat'], 53.347269)
        self.assertEqual(creds['DUBLIN_CC']['lon'], -6.259107)
        self.assertEqual(creds["title"], "JourneyTime JSON Credentials Store")
        self.assertEqual( \
            creds["open-weather"]["api-key"], \
            "f68d42db4825fd344dd408b4fac20dc3"
            )

    def test_get_next_chunk_size(self):
        """Test function "get_next_chunk_size()"
        """
        self.assertEqual(_get_next_chunk_size(54302), 32768)
        self.assertEqual(_get_next_chunk_size(21534), 21534)

    def test_journey_prediction(self):
        """Test JourneyPrediction creation and property assigment
        """
        rt_sname           = 'test_route'
        rt_sname_pickle_tf = True
        planned_dur_s      = 61543
        planned_dep_dt     = datetime.now()
        step_stops         = []
        # Create new instance...
        journey_prediction = \
            JourneyPrediction( \
                rt_sname, rt_sname_pickle_tf, \
                planned_dur_s, planned_dep_dt, \
                step_stops
            )
        # Verify property assignment
        self.assertEqual( \
            journey_prediction.route_shortname, rt_sname)
        self.assertEqual( \
            journey_prediction.route_shortname_pickle_exists, rt_sname_pickle_tf)
        self.assertEqual( \
            journey_prediction.planned_duration_s, planned_dur_s)
        self.assertEqual( \
            journey_prediction.planned_departure_datetime, planned_dep_dt)
        self.assertEqual( \
            journey_prediction.step_stops, step_stops)
        self.assertEqual( \
            journey_prediction.predicted_duration_s, 0)

    def test_step_stop(self):
        """Test StepStop creation and property assigment
        """
        stp            = '<Dummy Stop Object>'
        stp_seq        = []
        shap_dist_trav = 123456789
        # Create new instance...
        step_stop = StepStop(stp, stp_seq, shap_dist_trav)
        # Verify property assignment
        self.assertEqual( \
            step_stop.stop, stp)
        self.assertEqual( \
            step_stop.stop_sequence, stp_seq)
        self.assertEqual( \
            step_stop.shape_dist_traveled, shap_dist_trav)
        self.assertEqual( \
            step_stop.dist_from_first_stop_m, 0)
        self.assertEqual( \
            step_stop.predicted_time_from_first_stop_s, 0)

    def test_get_available_end_to_end_models(self):
        """Test function "get_available_end_to_end_models()"
        """
        available_end_to_end_models = get_available_end_to_end_models()
        # Best way to test this is against known state.
        # I have it hard coded to TK's PC for testing.  Better approach??
        self.assertEqual(len(available_end_to_end_models), 21)

    def test_weather_information(self):
        """Test function "weather_information()"
        """
        predicted_temp_k = weather_information(datetime.now().hour)
        # Guessed a reasonable temperature range for testing
        self.assertTrue(predicted_temp_k < 313.5)  # 40-degrees-C
        self.assertTrue(predicted_temp_k > 268.15)  # -5-degrees-C


#-------------------------------------------------------------------------------

# Define some basic unit tests to ensure all the methods defined above
# are sound.
class TestFunctionsUsingSessionForQuery(unittest.TestCase):
    """Test those functions using 'session.query' for queries.
    """
    # Class Variables
    connection    = None
    session_maker = None

    @classmethod
    def setUpClass(cls):
        """Set Up unittest.TestCase
        """
        print('Starting \"Session For Query\" Db Function Tests')
        try:
            print("\tCreating SQLAlchemy db engine.")
            # We only want to initialise the engine and create a db connection once
            # as its expensive (i.e. time consuming)
            connection_string = "mysql+mysqlconnector://" \
                + credentials['DB_USER'] + ":" + credentials['DB_PASS'] \
                + "@" \
                + credentials['DB_SRVR'] + ":" + credentials['DB_PORT']\
                + "/" + credentials['DB_NAME'] + "?charset=utf8mb4"
            #print('Connection String: ' + connectionString + '\n')
            engine = sqlalchemy_db.create_engine(connection_string)

            # engine.begin() runs a transaction
            with engine.begin() as TestBasicFunctions.connection:

                TestBasicFunctions.session_maker = sessionmaker(bind=engine)

        except (SQLAlchemyError, DBAPIError):
            # if there is any problem, print the traceback
            print("ERROR Database Error")
            print(traceback.format_exc())

    @classmethod
    def tearDownClass(cls):
        """Tear Down unittest.TestCase
        """
        # Make sure to close the connection - a memory leak on this would kill
        # us...
        if TestBasicFunctions.connection is not None:
            print("\tClosing SQLAlchemy db connection.")
            TestBasicFunctions.connection.close()
        print("\t\"Session For Query\" Db Function Tests Complete.\n")

    def test_query_results_as_compressed_csv(self):
        """Test function "query_results_as_compressed_csv()"
        """
        session = TestBasicFunctions.session_maker()
        trips_query = session.query(Trips)
        trips_response = query_results_as_compressed_csv(Trips, trips_query)
        # Consume the entire streamed response...
        _ = trips_response.get_data()
        self.assertEqual(trips_response.status_code, 200)

    def test_query_results_as_json(self):
        """Test function "()"
        """
        session = TestBasicFunctions.session_maker()
        trips_query = session.query(Trips)
        trips_query = \
            trips_query.filter(Trips.trip_id == '3992624.1.10-100-e20-1.214.I')
        trips_response = query_results_as_json(Trips, trips_query)
        trips_json = trips_response.json
        self.assertTrue(len(trips_json) > 0)
        self.assertTrue( \
                trips_json['trips'][0]['trip_id'] == '3992624.1.10-100-e20-1.214.I' \
            )
        # Consume the entire streamed response...
        _ = trips_response.get_data()

        # Do a second check - this time with the limits exceeded flag set...
        trips_response = query_results_as_json(Trips, trips_query, limit_exceeded=True)
        trips_json = trips_response.json
        self.assertTrue(len(trips_json) > 0)
        self.assertTrue( \
                trips_json['trips'][0]['trip_id'] == '3992624.1.10-100-e20-1.214.I' \
            )
        # Consume the entire streamed response...
        _ = trips_response.get_data()
        # How many JSON checks... are enough JSON checks...
        # Could I validate this against a schema perhaps?

#-------------------------------------------------------------------------------

class TestFunctionsUsingFlaskSQLAlchemyDbForConn(flask_testing.TestCase):
    """Test those functions using a Flask SQLAlchemy 'db' for db connections.
    """

    # According to: https://pythonhosted.org/Flask-Testing/
    # "You must specify the create_app method, which should return a Flask instance"
    def create_app(self):
        """Required 'create_app' method, which returns a Flask instance:
        """
        return create_test_app()  # From jt_flask_module.py

    def setUp(self):
        """Set Up flask_testing.TestCase
        """
        # Setup runs once per test routine. Could be used for a db.create_all() etc.

    def tearDown(self):
        """Tear Down flask_testing.TestCase
        """
        db.session.remove()

    def test_get_valid_route_shortnames(self):
        """Test function "get_valid_route_shortnames()"
        """
        valid_route_shortnames = get_valid_route_shortnames(db)
        #print(len(valid_route_shortnames), valid_route_shortnames)
        assert len(valid_route_shortnames) > 0
        assert len(valid_route_shortnames) == 390

    @classmethod
    def _get_list_of_stops_good_match(cls):
        """Get a list of stops for the Number 15 for Testing (good matching)...
        """
        route_name      = 'Main Street - Ballycullen Road (Hunter\'s Avenue)'
        route_shortname = 15
        stop_headsign   = 'Clongriffin'
        jrny_time       = datetime.strptime('2022-07-15 16:44:03', '%Y-%m-%d %H:%M:%S')
        departure_stop_name = 'Eden Quay, stop 299'
        departure_stop_lat  = 53.3482354
        departure_stop_lon  = -6.2561569
        arrival_stop_name   = 'Connolly'
        arrival_stop_lat    = 53.3505441
        arrival_stop_lon    = -6.2507091
        stops_by_route = get_stops_by_route( \
                db, route_name, route_shortname, \
                stop_headsign, jrny_time, \
                departure_stop_name, departure_stop_lat, departure_stop_lon, \
                arrival_stop_name, arrival_stop_lat, arrival_stop_lon \
            )
        return stops_by_route

    @classmethod
    def _get_list_of_stops_poor_match(cls):
        """Get a list of stops for the Number 15 for Testing...
        """
        route_name      = 'this-name-has-been-altered-to-force-poor-match'
        route_shortname = 15
        stop_headsign   = 'Clongriffin'
        jrny_time       = datetime.strptime('2022-07-15 16:44:03', '%Y-%m-%d %H:%M:%S')
        departure_stop_name = 'Eden Quay, stop 299'
        departure_stop_lat  = 53.3482354
        departure_stop_lon  = -6.2561569
        arrival_stop_name   = 'Connolly'
        arrival_stop_lat    = 53.3505441
        arrival_stop_lon    = -6.2507091
        stops_by_route = get_stops_by_route( \
                db, route_name, route_shortname, \
                stop_headsign, jrny_time, \
                departure_stop_name, departure_stop_lat, departure_stop_lon, \
                arrival_stop_name, arrival_stop_lat, arrival_stop_lon \
            )
        return stops_by_route

    def test_get_stops_by_route_good_match(self):
        """Test function "get_stops_by_route()"
        """
        stops_by_route = \
            TestFunctionsUsingFlaskSQLAlchemyDbForConn._get_list_of_stops_good_match()
        assert len(stops_by_route) == 2
        print(f'\tFound {len(stops_by_route)} stops on our test route (expected two).')
        assert stops_by_route[0].stop.stop_name == 'Eden Quay, stop 299'
        assert stops_by_route[1].stop.stop_name == 'Connolly, stop 497'
        # assert len(valid_route_shortnames) == 390

    def test_get_stops_by_route_poor_match(self):
        """Test function "get_stops_by_route()"
        """
        stops_by_route = \
            TestFunctionsUsingFlaskSQLAlchemyDbForConn._get_list_of_stops_poor_match()
        assert len(stops_by_route) == 2
        print(f'\tFound {len(stops_by_route)} stops on our test route (expected two).')
        assert stops_by_route[0].stop.stop_name == 'Eden Quay, stop 299'
        assert stops_by_route[1].stop.stop_name == 'Connolly, stop 497'
        # assert len(valid_route_shortnames) == 390

    def test_predict_journey_time_end_to_end(self):
        """Test function "predict_journey_time(), expecting and end-to-end model"
        """
        rt_sname           = '15'
        rt_sname_pickle_tf = True
        planned_dur_s      = 61543
        planned_dep_dt     = datetime.now()
        step_stops         =  \
            TestFunctionsUsingFlaskSQLAlchemyDbForConn._get_list_of_stops_good_match()
        # Create new instance...
        journey_prediction = \
            JourneyPrediction( \
                rt_sname, rt_sname_pickle_tf, \
                planned_dur_s, planned_dep_dt, \
                step_stops
            )
        prediction = predict_journey_time(journey_prediction, CONST_MODEL_STOP_TO_STOP)
        assert len(prediction.step_stops) == 2
        assert prediction.predicted_duration_s > 0
        print(f'Predicted duration was {prediction.predicted_duration_s} (should be around 7k)')

    def test_predict_journey_time_stop_to_stop(self):
        """Test function "predict_journey_time(), expecting and stop-to-stop model"
        """
        rt_sname           = '15'
        rt_sname_pickle_tf = False
        planned_dur_s      = 61543
        planned_dep_dt     = datetime.now()
        step_stops         =  \
            TestFunctionsUsingFlaskSQLAlchemyDbForConn._get_list_of_stops_good_match()
        # Create new instance...
        journey_prediction = \
            JourneyPrediction( \
                rt_sname, rt_sname_pickle_tf, \
                planned_dur_s, planned_dep_dt, \
                step_stops
            )
        prediction = predict_journey_time(journey_prediction, CONST_MODEL_STOP_TO_STOP)
        assert len(prediction.step_stops) == 2
        assert prediction.predicted_duration_s > 0
        print(f'Predicted duration was {prediction.predicted_duration_s} (should be around 7k)')

#===============================================================================

def main():
    """Load Data the National transport Authority GTFS Data for Dublin Bus


    """

    start_time = datetime.now()
    print('Test_JT_Utils: Start of test pass (' + start_time.strftime('%Y-%m-%d %H:%M:%S') + ')')

    suite_list = []
    # Test the basic functions
    suite_list.append( \
            unittest.TestLoader().loadTestsFromTestCase(TestBasicFunctions) \
        )
    # Test the functions using session for query
    suite_list.append( \
            unittest.TestLoader().loadTestsFromTestCase(TestFunctionsUsingSessionForQuery) \
        )
    # Test the functions with Flask app db connections
    suite_list.append( \
            unittest.TestLoader().loadTestsFromTestCase( \
                    TestFunctionsUsingFlaskSQLAlchemyDbForConn
                ) \
        )
    overall_suite = unittest.TestSuite(suite_list)

    unittest.TextTestRunner(verbosity=4).run(overall_suite)

    # (following returns a timedelta object)
    elapsed_time = datetime.now() - start_time

    # returns (minutes, seconds)
    #minutes = divmod(elapsedTime.seconds, 60)
    minutes = divmod(elapsed_time.total_seconds(), 60)
    print('Iteration Complete! (Elapsed time:', minutes[0], 'minutes', minutes[1], 'seconds)\n')
    sys.exit()

if __name__ == '__main__':
    main()
