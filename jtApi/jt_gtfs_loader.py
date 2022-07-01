# 2022-07-01 TK/BF/YC/CP; Group 3, "Raduno"
#            COMP47360 Research Practicum
"""

"""

import os, sys
import csv
import zipfile
from zipfile import ZipFile
import requests
import json
from jtUtils import loadCredentials
import traceback
import sqlalchemy as db
from datetime import datetime

#===============================================================================
#===============================================================================
#===============================================================================

# def saveStationDataToDb(connection, jsonData, timestampAsStr):
#     """
#     """
#     # Station Data:
#     # number ('Id'), contract_name, name, address, position {lat, lng}, banking, bonus
#     # (banking indicates whether this station has a payment terminal,
#     #  bonus indicates whether this is a bonus station)
#     # Availability Data (For station)
#     # number ('Id'), bike_stands, available_bike_stands, available_bikes, status, last_update

#     # Look over the jsonData, which contains a both static and dynamic information
#     # in a big soup...
#     for row in jsonData:

#         # Each row contains both 'Station' (almost static) data AND activity
#         # data for that station.  I seperate them out just to make the code
#         # more legible
#         station = extractStation(row)
#         stationSate = extractStationState(row)

#         # Would prefer to use ORM rather than straight SQL - but the
#         # priority for now is to have something working. Will return to this
#         # if time (and the burndown chart) permits...
#         # Session = db.sessionmaker(bind=engine)
#         # session = Session()

#         # Have we already stored this station?
#         if (stationExists(connection, station)):
#             # If the stationExists we update it
#             # (It's not efficient to update every time... but... yeah...)
#             updateStation(connection, station)
#         else:
#             insertStation(connection, station)

#         # Whether we inserted or updated - doesn't matter - the station
#         # definitely exists now.  Look up the id so we can insert the detail
#         # record...
#         stationId = getStationId(connection, station)
        
#         # Once we're confident the station exists and is up to date we insert
#         # the Status Updata data for this station!
#         insertStationState(connection, stationId, timestampAsStr, stationSate)

#     return



#===============================================================================
#===============================================================================
#===============================================================================

def main():
    """Load Data the National transport Authority GTFS Data for Dublin Bus


    """
    # We want to timestamp our records so we can tie station state to
    # weather data etc..  So we generate a timestamp now at the beginning of
    # this 'Data Load' pass and use it a couple of times below:
    timestamp = datetime.now()
    timestampAsStr = timestamp.strftime('%Y-%m-%d %H:%M:%S')

    print("JT_GTFS_Loader: Start of iteration (" + timestampAsStr + ")")

    print("\tLoading credentials.")
    # Load our private credentials from a JSON file
    credentials = loadCredentials()
    working_dir = os.path.dirname(__file__)

    print("\tRegistering start with cronitor.")
    # The DudeWMB Data Loader uses the 'Cronitor' web service (https://cronitor.io/)
    # to monitor the running data loader process.  This way if there is a failure
    # in the job etc. our team is notified by email.  In addition, if the job
    # or the EC2 instance suspends for some reason, cronitor informs us of the 
    # lack of activity so we can log in and investigate.
    # Send a request to log the start of a run
    cronitorURI = credentials['cronitor']['TelemetryURL']
    requests.get(cronitorURI + "?state=run")

    print("\tRetrieving GTFS Schedule data from NTA.")

    import_dir  = working_dir + "/import/"
    gtfs_schedule_data_file = import_dir + "google_transit_dublinbus.zip"

    # If a .zip from a previous download exists - we don't really care. It's all
    # about having the most up to date data. Log a warning, but proceed...
    if os.path.exists(gtfs_schedule_data_file):
        print("\tWARNING: Old Schedule Data file found - Deleting...")
        os.remove(gtfs_schedule_data_file)

    # check if file exists!
    # if it does just remove it!!
    # relative directory - sort it out!!!
    # Would it be better to use the python 'wget' module??
    # ????? response = wget.download(credentials['nta-gtfs']['gtfs-schedule-data-url'], "import/google_transit_dublinbus.zip")
    # Open file for binary write...
    # ... and write to it!
    print("\tDownloading GTFS Schedule data.")
    response = requests.get(credentials['nta-gtfs']['gtfs-schedule-data-url'])
    if (response.status_code == 200):
        print("\tSaving GTFS Schedule data to disk.")
        with open(gtfs_schedule_data_file, "wb") as gtfs_zip:
            gtfs_zip.write(response.content)
    else:
        # Our call to the API failed for some reason...  print some information
        # Who knows... someone may even look at the logs!!
        print("ERROR: Call to GTFS Schedule API failed with status code: ", response.status_code)
        print("       The response reason was \'" + str(response.reason) + "\'")

    # Verify the downloaded zipfile is well formed...
    if zipfile.is_zipfile(gtfs_schedule_data_file):
        # IMPORTANT NOTE: ZipFile OVERWRITES files without asking. In this case,
        # that is the behaviour we require. But it's important to be aware of it.
        with ZipFile(gtfs_schedule_data_file, 'r') as gtfs_zip:
            # Extract all the contents of zip file in current directory
            gtfs_zip.extractall(path=import_dir)
        print("\tGTFS Schedule Data Extract Complete - Removing .Zip Archive.")
        os.remove(gtfs_schedule_data_file)
    else:
        print("ERROR: Downloaded GTFS Schedule Data is not a valid .Zip file!")
        print("       Aborting...")
        # Send a Cronitor request to signal our process has failed.
        requests.get(cronitorURI + "?state=fail")
        # We don't have to clear down the file - it will get automatically cleared
        # during the next pass...

    # Now... load all the files, by name...???????
    # Use a csv reader as it is quite memory efficient and some of the files are
    # large...  csv is an iterator - it does not load the whole file into memory!!!
    data = csv.reader(csv_file, delimiter=",")
    # Skip over the first line - header row!
    next(data)
    # process the file line-by-line...
    for row in data:

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
# REMEMBER to commit any outstanding items at the end!!!!!

    print("\tRegistering completion with cronitor.")
    # Send a Cronitor request to signal our process has completed.
    requests.get(cronitorURI + "?state=complete")

    

    # (following returns a timedelta object)
    elapsedTime = datetime.now() - timestamp
    
    # returns (minutes, seconds)
    #minutes = divmod(elapsedTime.seconds, 60) 
    minutes = divmod(elapsedTime.total_seconds(), 60) 
    print('\tIteration Complete! (Elapsed time:', minutes[0], 'minutes',
                                    minutes[1], 'seconds)\n')
    sys.exit()

if __name__ == '__main__':
    main()



        # try:
    #     print("\tCreating SQLAlchemy db engine.")
    #     # We only want to initialise the engine and create a db connection once
    #     # as its expensive (i.e. time consuming). So we only want to do that once
    #     connectionString = "mysql+mysqlconnector://" \
    #         + credentials['DB_USER'] + ":" + credentials['DB_PASS'] \
    #         + "@" \
    #         + credentials['DB_SRVR'] + ":" + credentials['DB_PORT']\
    #         + "/" + credentials['DB_NAME'] + "?charset=utf8mb4"
    #     #print("Connection String: " + connectionString + "\n")
    #     engine = db.create_engine(connectionString)

    #     # engine.begin() runs a transaction
    #     with engine.begin() as connection: