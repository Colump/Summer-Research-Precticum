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
from jtUtils import loadCredentials

from sqlalchemy import create_engine, text, update
from sqlalchemy.orm import sessionmaker, Session
from models import Stop

def loopOverAllStopsAndCalcDistFromCC():
    """
    """
    # Each point is represented by a tuple, (lat, lon). Define a fixed point for
    # Dublin City Center...
    dublinCc = (53.347269, -6.259107)

    credentials = loadCredentials()

    # For more information on SqlAlchemy and using ORM see:
    #   -> https://docs.sqlalchemy.org/en/14/orm/tutorial.html

    dbConnStr = "mysql+mysqlconnector://" \
            + credentials['DB_USER'] + ":" + credentials['DB_PASS'] \
            + "@" \
            + credentials['DB_SRVR'] + ":" + credentials['DB_PORT']\
            + "/" + credentials['DB_NAME'] + "?charset=utf8mb4"
    # print("dbstr -> " + dbConnStr)

    # The start of any SQLAlchemy application is an object called the Engine.
    # This object acts as a central source of connections...
    # In the following:
    #   -> The echo flag is a shortcut to setting up SQLAlchemy logging, which is accomplished
    #      via Python’s standard logging module. With it enabled, we’ll see all the generated
    #      SQL produced. If you want less output generated, set it to False
    engine = create_engine(dbConnStr, echo=False, future=True)
    # The first time a method like Engine.execute() or Engine.connect() is called, the Engine
    # establishes a real DBAPI connection to the database, which is then used to emit the SQL.
    # When using the ORM, we typically don’t use the Engine directly once created; instead, it’s
    # used behind the scenes by the ORM.

    # The ORM’s “handle” to the database is the Session. When we first set up the application,
    # at the same level as our create_engine() statement, we define a Session class which will
    # serve as a factory for new Session objects:
    Session = sessionmaker(bind=engine)
    # NOTE: the Session works within a transaction

    # Whenever you need to have a conversation with the database, you instantiate a Session:
    session = Session()
    # The above Session is associated with our MySQL-enabled Engine, but it hasn’t opened any
    # connections yet. When it’s first used, it retrieves a connection from a pool of connections
    # maintained by the Engine, and holds onto it until we commit all changes and/or close the
    # session object.

    #session.query(Stop).update(Stop.dist_from_cc : haversine(dublinCc, (Stop.stop_lat, Stop.stop_lon)))
    # Using the 'with Session(engine) as session' syntax we do all the 'session' work above in
    # a single line!
    #with Session(engine) as session:
        #stmt = text("SELECT * FROM stops")
        #query = session.execute(stmt)
    all_stops = session.query(Stop).order_by(Stop.stop_id)

    for stop in all_stops:
        currentStopCoordinates = (stop.stop_lat, stop.stop_lon)
        #print(currentStopCoordinates)
        # Calculate distance to city center using haversine (in km) and then
        # update the value stored on stop...
        stop.dist_from_cc = haversine(dublinCc, currentStopCoordinates)
        #print(stop.dist_from_cc)

    # Tell the Session that we’d like to issue all remaining changes to the database and commit
    # the transaction, which has been in progress throughout.
    session.commit()

    return

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