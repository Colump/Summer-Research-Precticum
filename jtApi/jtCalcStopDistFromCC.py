# 2022-06-20 TK/BF/YC/CP; "JourneyTi.me" Project
#            Comp47360 Research Practicum 
"""
PseudoCode Solution:

define a function which
    return 

define a main function
    print finished.

if script is being run as a script (not imported) call main() function

"""

import sys
from haversine import haversine, Unit
from jtFlaskModule import loadCredentials

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from models import db, stop

def loopOverAllStopsAndCalcDistFromCC():
    """
    """
    # Each point is represented by a tuple, (lat, lon)
    dublinCc = (53.347269, -6.259107)

    credentials = loadCredentials()

    dbConnStr = "mysql+mysqlconnector://" \
            + credentials['DB_USER'] + ":" + credentials['DB_PASS'] \
            + "@" \
            + credentials['DB_SRVR'] + ":" + credentials['DB_PORT']\
            + "/" + credentials['DB_NAME'] + "?charset=utf8mb4"
    # print("dbstr -> " + dbConnStr)

    # The start of any SQLAlchemy application is an object called the Engine.
    # This object acts as a central source of connections...
    engine = create_engine(dbConnStr, echo=True, future=True)

    with Session(engine) as session:
        stmt = text("SELECT * FROM stops")
        query = session.execute(stmt)
        for stop in query:
            currentStopCoordinates = (stop.stop_lat, stop.stop_lon)

            # Calculate distance to city center using haversine (in km) and then
            # update the value stored on stop...
            stop.distanceToCc = haversine(dublinCc, currentStopCoordinates)

            stop.update()

def main():
    """
    """
    print('This program will calculate the distance from the Dublin City Center for each stop')
    print('in the stops table, updating the record as it goes.\n')
    print('For our calculation we consider the center of O\'Connell Bridge to be the center')
    print('of the city as many of the bus terminus stop surround that point (53.347269°-6.259107°).')
    print('')

    loopOverAllStopsAndCalcDistFromCC()

    print('\r\nFinished!')
    sys.exit()

if __name__ == '__main__':
    main()