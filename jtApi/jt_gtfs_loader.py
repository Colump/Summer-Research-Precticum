# 2022-06-20 TK/BF/YC/CP; Group 3, "Raduno", "JourneyTi.me" Project
#            Comp47360 Research Practicum
"""jt_gtfs_loader; Load Latest GTFS-R Data into Journeyti.me Database.

"""

# Standard Library Imports
import csv
from datetime import datetime
import logging
import os
from os.path import exists
import sys
import traceback
import zipfile
from zipfile import ZipFile

# Related Third Party Imports
from haversine import haversine
import requests
import sqlalchemy as db
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from sqlalchemy.orm import sessionmaker

# Local Application Imports
# To make sure we can import modules from the folder where jt_gtfs_loader is
# installed (e.g. if called as an installed endpoint) - we always add the
# module directory to the python path. Endpoints can be called from any
# 'working directory' - but modules can only be imported from the python path.
jt_gtfs_module_dir = os.path.dirname(__file__)
sys.path.insert(0, jt_gtfs_module_dir)
from jt_utils import load_credentials
from models import Agency, Calendar, CalendarDates, Routes, Shapes, StopTime, Stop, Transfers, Trips

log = logging.getLogger(__name__)  # Standard naming...

# Each point is represented by a tuple, (lat, lon). Define a fixed point for
# Dublin City Center...
print('\tLoading credentials.')
credentials = load_credentials()
CONST_DUBLIN_CC = (credentials['DUBLIN_CC']['lat'], credentials['DUBLIN_CC']['lon'])

CONST_OBJ_PER_SESS_MAX = 50000


def download_gtfs_schedule_data(import_dir):
    """Download the latest version of the GTFS Schedule Data.

    """
    print('\tRetrieving GTFS Schedule data from NTA.')
    # NOTE: We must download the combined schedule file as some bus routes are
    #       operated by Dublin Bus, some by Go-Ahead Ireland and others by yet
    #       more operators.  To cover all of Dublin - we need it all...
    gtfs_schedule_data_file = os.path.join(import_dir, 'google_transit_combined.zip')

    # If a .zip from a previous download exists - we don't really care. It's all
    # about having the most up to date data. Log a warning, but proceed...
    if os.path.exists(gtfs_schedule_data_file):
        print('\tWARNING: Old Schedule Data file found - Deleting...')
        os.remove(gtfs_schedule_data_file)

    # Would it be better to use the python 'wget' module??
    #     response = wget.download( \
    #         credentials['nta-gtfs']['gtfs-schedule-data-url'], \
    #         "import/google_transit_dublinbus.zip" \
    #         )
    # Open file for binary write...
    # ... and write to it!
    response = requests.get(credentials['nta-gtfs']['gtfs-schedule-data-url'])
    if response.status_code == 200:
        print('\tSaving GTFS Schedule data to disk.')
        with open(gtfs_schedule_data_file, "wb") as gtfs_zip:
            gtfs_zip.write(response.content)
    else:
        # Our call to the API failed for some reason...  print some information
        # Who knows... someone may even look at the logs!!
        print("ERROR: Call to GTFS Schedule API failed with status code: ", response.status_code)
        print("       The response reason was \'" + str(response.reason) + "\'")

    return gtfs_schedule_data_file


def extract_gtfs_data_from_zip(gtfs_schedule_data_file, import_dir, cronitor_uri):
    """Extract the contents of the GTFS Schedule Data zip to the import directory

    """
    # Verify the downloaded zipfile is well formed...
    if zipfile.is_zipfile(gtfs_schedule_data_file):
        # IMPORTANT NOTE: ZipFile OVERWRITES files without asking. In this case,
        # that is the behaviour we require. But it's important to be aware of it.
        with ZipFile(gtfs_schedule_data_file, 'r') as gtfs_zip:
            # Extract all the contents of zip file in current directory
            gtfs_zip.extractall(path=import_dir)
        print('\tGTFS Schedule Data Extract Complete - Removing .Zip Archive.')
        os.remove(gtfs_schedule_data_file)
    else:
        print('ERROR: Downloaded GTFS Schedule Data is not a valid .Zip file!')
        print('       Aborting...')
        # Send a Cronitor request to signal our process has failed.
        requests.get(cronitor_uri + "?state=fail")
        # We don't have to clear down the file - it will get automatically cleared
        # during the next pass...


def import_gtfs_txt_files_to_db(import_dir, session_maker):
    """Iterate Over the GTFS Txt Files, Import them to the db

    """

    import_dir_enc = os.fsencode(import_dir)
    for file in os.listdir(import_dir_enc):
        # 'file' is a handle on the actual file...
        filename = os.fsdecode(file)
        path_this_item = os.path.join(import_dir, filename)

        if os.path.isdir(path_this_item):
                # skip directories
                pass
        elif filename == ".gitignore":
            # Expected extraneous file... ignore...
            pass
        else:
            print('----------------------------------------')
            print('Processing \"' + str(filename) + '\".' \
                + ' Time is: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            if filename.endswith(".txt"):
                # Now... load all the files, by name...
                # There may be a better abstraction for this but as we're only dealing
                # with ten files we're taking the following expedient approach.

                # Some of the files are large... 'stop_times.txt' is 220MB. We use a
                # 'csv reader' as it is quite memory efficient. It is an iterator -
                # so it processes the file line by line and does not load the whole
                # file into memory (which would be bad).
                with open(
                        os.path.join(import_dir, filename), \
                        newline='', \
                        encoding='utf-8' \
                    ) as gtfs_csv:
                    data = csv.reader(gtfs_csv, delimiter=",")
                    # Skip over the first line (header row)
                    next(data)

                    # Instantiate a session *per file* so we can talk to the database!
                    session = session_maker()
                    objects_this_session = []  # We build a list of objects for bulk insert...

                    # Process the files line-by-line...
                    # -> Some files are small (e.g. agency - 1 record). We process
                    #    the entire file and move on.
                    # -> Some files are large (e.g. stop-times, 2M+ records). We
                    #    process these in batches to make better use of each session

                    # RISK!!!!  We truncate the table before re-populating...
                    #           What if population fails???

                    if filename == "agency.txt":
                        import_agency(data, session, objects_this_session)

                    elif filename == "calendar.txt":
                        import_calendar(data, session, objects_this_session)

                    elif filename == "calendar_dates.txt":
                        import_calendar_dates(data, session, objects_this_session)

                    elif filename == "routes.txt":
                        import_routes(data, session, objects_this_session)

                    elif filename == "shapes.txt":
                        session, objects_this_session = \
                            import_shapes(data, session, session_maker, objects_this_session)

                    elif filename == "stops.txt":
                        import_stops(data, session, objects_this_session)

                    elif filename == "stop_times.txt":
                        session, objects_this_session = \
                            import_stop_times(data, session, session_maker, objects_this_session)

                    elif filename == "transfers.txt":
                        import_transfers(data, session, objects_this_session)

                    elif filename == "trips.txt":
                        session, objects_this_session = \
                            import_trips(data, session, session_maker, objects_this_session)

                    else:
                        print('WARNING: Unexpected .txt file encountered -> ' + str(filename))
                        print('         Ignoring...')

                    # To see a list of updated objects we can use:
                    #   -> print('session.dirty -> ', session.dirty)
                    # To see a list of new objects we can use:
                    #   -> print('session.new -> ', session.new)

                    # Save outstanding insertions to the db...
                    if len(objects_this_session) > 0:
                        print('#', end='')
                        session.bulk_save_objects(objects_this_session)
                        session.commit()
            else:
                print('WARNING: Unexpected file encountered -> ' + str(filename))
                print('         Ignoring...')

            print('')


def import_agency(data, session, objects_this_session):
    """Import content from data into the Agency table

    """
    truncate_table(session, Agency)

    print('          -> ', end='')
    for row in data:
        agency = Agency(agency_id=row[0],
                        agency_name=row[1],
                        agency_url=row[2],
                        agency_timezone=row[3],
                        agency_lang=row[4],
                        agency_phone=row[5]
                        #db has field "agencycol" - what for??
                        )
        objects_this_session.append(agency)


def import_calendar(data, session, objects_this_session):
    """Import content from data into the Calendar table

    """
    truncate_table(session, Calendar)

    print('          -> ', end='')
    for row in data:
        calendar = Calendar(
                                service_id=row[0],
                                monday=row[1],
                                tuesday=row[2],
                                wednesday=row[3],
                                thursday=row[4],
                                friday=row[5],
                                saturday=row[6],
                                sunday=row[7],
                                start_date=row[8],
                                end_date=row[9]
                            )
        objects_this_session.append(calendar)


def import_calendar_dates(data, session, objects_this_session):
    """Import content from data into the CalendarDates table

    """
    truncate_table(session, CalendarDates)

    print('          -> ', end='')
    for row in data:
        calendar_date = CalendarDates(
                                service_id=row[0],
                                date=row[1],
                                exception_type=row[2]
                            )
        objects_this_session.append(calendar_date)


def import_routes(data, session, objects_this_session):
    """Import content from data into the Routes table

    """
    truncate_table(session, Routes)

    print('          -> ', end='')
    for row in data:
        route = Routes(
                                route_id=row[0],
                                agency_id=row[1],
                                route_short_name=row[2],
                                route_long_name=row[3],
                                route_type=row[4]
                            )
        objects_this_session.append(route)


def import_shapes(data, session, session_maker, objects_this_session):
    """Import content from data into the Shapes table

    """
    truncate_table(session, Shapes)

    print('        Processing records in batches of', CONST_OBJ_PER_SESS_MAX)
    print('          -> ', end='')
    for row in data:
        shape = Shapes(
                                shape_id=row[0],
                                shape_pt_lat=row[1],
                                shape_pt_lon=row[2],
                                shape_pt_sequence=row[3],
                                shape_dist_traveled=row[4]
                            )
        objects_this_session.append(shape)

        if len(objects_this_session) >= CONST_OBJ_PER_SESS_MAX:
            session = commit_batch_and_start_new_session( \
                                    objects_this_session, session, session_maker \
                                    )
            objects_this_session = []  # Resume with an empty list...
    return session,objects_this_session


def import_stops(data, session, objects_this_session):
    """Import content from data into the Stop table

    """
    truncate_table(session, Stop)

    print('          -> ', end='')
    for row in data:
        stop = Stop(stop_id=row[0],
                    stop_name=row[1],
                    stop_lat=row[2],
                    stop_lon=row[3],
                    # (See custom 'Point' type in models.py for following...)
                    # Note that spatial points are defined "lon-lat"
                    stop_position = 'POINT(' + row[3] + ' ' + row[2] + ')',
                    # 'stop_position' is binary information.  If you want to
                    # "see" it in a query the easiest way is to use one of
                    # the built in functions to display it. E.g:
                    #   SELECT stop_lat,stop_lon, ST_ASTEXT(stop_position)
                    #   FROM stops
                    # Calculate distance to city center using haversine (in km) ...
                    dist_from_cc = haversine(
                        CONST_DUBLIN_CC,
                        (float(row[2]), float(row[3]))
                        )
                    )
        objects_this_session.append(stop)


def import_stop_times(data, session, session_maker, objects_this_session):
    """Import content from data into the StopTimes table

    Processed in batches of "CONST_OBJ_PER_SESS_MAX" records.
    """
    truncate_table(session, StopTime)

    print('        Processing records in batches of', CONST_OBJ_PER_SESS_MAX)
    print('          -> ', end='')
    for row in data:
        stop_time = StopTime(trip_id=row[0],
                            arrival_time=row[1],
                            departure_time=row[2],
                            stop_id=row[3],
                            stop_sequence=row[4],
                            stop_headsign=row[5],
                            pickup_type=row[6],
                            drop_off_type=row[7],
                            shape_dist_traveled=row[8]
                            )
        objects_this_session.append(stop_time)

        if len(objects_this_session) >= CONST_OBJ_PER_SESS_MAX:
            session = commit_batch_and_start_new_session( \
                                    objects_this_session, session, session_maker \
                                    )
            objects_this_session = []  # Resume with an empty list...

    return session,objects_this_session


def import_transfers(data, session, objects_this_session):
    """Import content from data into the Transfers table

    """
    truncate_table(session, Transfers)

    print('          -> ', end='')
    for row in data:
        transfer = Transfers(from_stop_id=row[0],
                            to_stop_id=row[1],
                            transfer_type=row[2],
                            min_transfer_time=row[3] if row[3] != '' else None
                            )
        objects_this_session.append(transfer)


def import_trips(data, session, session_maker, objects_this_session):
    """Import content from data into the Trips table

    Processed in batches of "CONST_OBJ_PER_SESS_MAX" records.
    """
    truncate_table(session, Trips)

    print('        Processing records in batches of', CONST_OBJ_PER_SESS_MAX)
    print('          -> ', end='')
    for row in data:
        trip = Trips(route_id=row[0],
                    service_id=row[1],
                    trip_id=row[2],
                    shape_id=row[3],
                    trip_headsign=row[4],
                    direction_id=row[5]
                    )
        objects_this_session.append(trip)

        if len(objects_this_session) >= CONST_OBJ_PER_SESS_MAX:
            session = commit_batch_and_start_new_session( \
                                    objects_this_session, session, session_maker \
                                    )
            objects_this_session = []  # Resume with an empty list...

    return session,objects_this_session


#-------------------------------------------------------------------------------


def commit_batch_and_start_new_session(list_of_objects, session, session_maker):
    """Commit the session once the object session limit is reached.

    Also prints a '# to the console as a type of 'chunk progress indicator' for the logs...
    """
    # Once our session is holding a fair chunk of data we commit and begin a new session...
    # We print a '#' to the console as a type of 'chunk progress indicator' for the logs...
    print('#', end='')
    session.bulk_save_objects(list_of_objects)
    session.commit()
    session = session_maker()

    return session


def _truncate_tables(session_maker):
    """Truncate (Delete All Rows From) the all GTFS Tables
    """

    session = session_maker()

    _truncate_table(session, Agency)
    _truncate_table(session, Calendar)
    _truncate_table(session, CalendarDates)
    _truncate_table(session, Routes)
    _truncate_table(session, Shapes)
    _truncate_table(session, Stop)
    _truncate_table(session, StopTime)
    _truncate_table(session, Transfers)
    _truncate_table(session, Trips)

    session.commit()


def _truncate_table(session, model):
    """Truncate (Delete All Rows From) the Supplied Database Table

    Prints a nicely formattted message for the module logs
    """
    print('        Truncating Table ' + model.__table__.name + '.')
    num_rows_deleted = session.query(model).delete()
    print('          -> Resetting auto-increment id...' )
    session.execute('ALTER TABLE ' + model.__table__.name + ' AUTO_INCREMENT = 1')
    print('          -> Truncate Complete. ' + str(num_rows_deleted) + ' Rows Deleted.')


# If we need reference objects - load that shit in advance!  That way we're not loading for each
# row...
# product_categories = {p_category.code: p_category for p_category in ProductCategory.objects.all()}
# for row in data:
#     product_category_code = row[4]
#     product_category = product_categories.get(product_category_code)
#     if not product_category:
#         product_category = ProductCategory.objects.create(name=row[3], code=row[4])
#         product_categories[product_category.code] = product_category

# don't save one element at a time...
# instead build a list and then commit the list
# product = Product(
#     name=row[0],
#     code=row[1],
#     price=row[2],
#     product_category=product_category
# )
# products.append(product)  # products are defined before for loop
# if len(products) > 5000:
#     Product.objects.bulk_create(products)
#     products = []  # clean the list;
#session.add_all([<list>]
# REMEMBER to commit any outstanding items at the end!!!!!

#===============================================================================
#===============================================================================
#===============================================================================

def main():
    """Load Data the National transport Authority GTFS Data for Dublin Bus


    """

    start_time = datetime.now()

    print('JT_GTFS_Loader: Start of iteration (' + start_time.strftime('%Y-%m-%d %H:%M:%S') + ')')

    import_dir = os.path.join(jt_gtfs_module_dir, 'import')

    print('\tRegistering start with cronitor.')
    # The DudeWMB Data Loader uses the 'Cronitor' web service (https://cronitor.io/)
    # to monitor the running data loader process.  This way if there is a failure
    # in the job etc. our team is notified by email.  In addition, if the job
    # or the EC2 instance suspends for some reason, cronitor informs us of the
    # lack of activity so we can log in and investigate.
    # Send a request to log the start of a run
    cronitor_uri = credentials['cronitor']['TelemetryURL']
    requests.get(cronitor_uri + "?state=run")

    # Download the GTFS Schedule Data File (it comes down as a ".zip")
    gtfs_schedule_data_file = download_gtfs_schedule_data(import_dir)

    # Extract the contents of the GTFS Schedule Data .zip to the import directory...
    extract_gtfs_data_from_zip(gtfs_schedule_data_file, import_dir, cronitor_uri)

    # The following functions require a db commection...
    connection = None
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
        engine = db.create_engine(connection_string)

        print('')
        # engine.begin() runs a transaction
        with engine.begin() as connection:

            session_maker = sessionmaker(bind=engine)

            # With the CSV files (bizarrely, with a .txt extension) extracted to disk,
            # we import the content to the db.
            import_gtfs_txt_files_to_db(import_dir, session_maker)
    except (SQLAlchemyError, DBAPIError):
        # if there is any problem, print the traceback
        print("ERROR Database Error")
        print(traceback.format_exc())
        print('\tRegistering error with cronitor.')
        # Send a Cronitor request to signal our process has failed.
        requests.get(cronitor_uri + "?state=fail")
    finally:
        # Make sure to close the connection - a memory leak on this would kill
        # us...
        if connection is not None:
            connection.close()

    print('\nUpdating Valid Route Name List in API Server.')
    # Send a api.journeyti.me a request to update the 'valid route shortname' list
    # now that we've loaded a fresh dataset.
    requests.get(credentials['GTFS_LOADER']['JTAPI_SRVR'] + '/update_valid_route_shortnames.do')

    print('\nRegistering completion with cronitor.')
    # Send a Cronitor request to signal our process has completed.
    requests.get(cronitor_uri + "?state=complete")

    # (following returns a timedelta object)
    elapsed_time = datetime.now() - start_time

    # returns (minutes, seconds)
    #minutes = divmod(elapsedTime.seconds, 60)
    minutes = divmod(elapsed_time.total_seconds(), 60)
    print('Iteration Complete! (Elapsed time:', minutes[0], 'minutes', minutes[1], 'seconds)\n')
    print('--------------------------------------------------------------------------------')
    print('================================================================================')
    print('--------------------------------------------------------------------------------\n')
    sys.exit()

if __name__ == '__main__':
    main()
