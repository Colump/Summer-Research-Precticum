# -*- coding: utf-8 -*-
"""Test_jt_gtfs_loader: Unit Tests for jt_gtfs_loader
"""

# Standard Library Imports
from datetime import datetime
import os
import sys
import traceback
import unittest

# Related Third Party Imports
import sqlalchemy as sqlalchemy_db
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from sqlalchemy.orm import sessionmaker

# Local Application Imports
test_jt_gtfs_loader_dir = os.path.dirname(__file__)
test_jt_gtfs_loader_parent_dir = os.path.dirname(test_jt_gtfs_loader_dir)
sys.path.insert(0, test_jt_gtfs_loader_parent_dir)
from jt_utils import load_credentials
from jt_gtfs_loader \
    import download_gtfs_schedule_data, extract_gtfs_data_from_zip, \
        import_gtfs_txt_files_to_db

print('Test_jt_gtfs_loader: Loading credentials.')
credentials = load_credentials()

import_dir = os.path.join(test_jt_gtfs_loader_parent_dir, 'import')

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


    def test_download_gtfs_schedule_data(self):
        """Test function "download_gtfs_schedule_data()"
        """
        # First, guarantee no file exists...
        gtfs_sched_zip_file = os.path.join(import_dir, 'google_transit_combined.zip')
        if os.path.exists(gtfs_sched_zip_file):
            os.remove(gtfs_sched_zip_file)
        # Next download the file.
        gtfs_schedule_data_file = download_gtfs_schedule_data(import_dir)
        # Check it exists
        self.assertTrue(os.path.exists(gtfs_schedule_data_file))
        # Download the file again to trigger the 'clear file code'
        gtfs_schedule_data_file = download_gtfs_schedule_data(import_dir)

        # At the end of this test   - a .zip file remains on disk.

    def test_extract_gtfs_data_from_zip(self):
        """Test function "extract_gtfs_data_from_zip()"
        """
        # First, guarantee no file exists...
        gtfs_schedule_data_file = os.path.join(import_dir, 'google_transit_combined.zip')
        if not os.path.exists(gtfs_schedule_data_file):
            # Download the file.
            gtfs_schedule_data_file = download_gtfs_schedule_data(import_dir)
        # Download the file again to trigger the 'clear file code'
        extract_gtfs_data_from_zip(gtfs_schedule_data_file, import_dir, 'http://dummy.cronitor.uri')
        self.assertTrue(not os.path.exists(gtfs_schedule_data_file))
        self.assertTrue(os.path.exists(os.path.join(import_dir, 'agency.txt')))
        self.assertTrue(os.path.exists(os.path.join(import_dir, 'calendar.txt')))
        self.assertTrue(os.path.exists(os.path.join(import_dir, 'calendar_dates.txt')))
        self.assertTrue(os.path.exists(os.path.join(import_dir, 'routes.txt')))
        self.assertTrue(os.path.exists(os.path.join(import_dir, 'shapes.txt')))
        self.assertTrue(os.path.exists(os.path.join(import_dir, 'stops.txt')))
        self.assertTrue(os.path.exists(os.path.join(import_dir, 'stop_times.txt')))
        self.assertTrue(os.path.exists(os.path.join(import_dir, 'transfers.txt')))
        self.assertTrue(os.path.exists(os.path.join(import_dir, 'trips.txt')))


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
                + "/" + credentials['DB_NAME'] + "_testing?charset=utf8mb4"
            print('\tConnection String: ' + connection_string + '\n')
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

    def test_import_gtfs_txt_files_to_db(self):
        """Test function "import_gtfs_txt_files_to_db()"
        """
        import_gtfs_txt_files_to_db(import_dir, TestBasicFunctions.session_maker)
        # TO-DO Testing here is appalling - I run to fail? Update methods to return
        #      counts and then possibly verify? Discuss...


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
    suite_list.append( \
            unittest.TestLoader().loadTestsFromTestCase(TestFunctionsUsingSessionForQuery) \
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
