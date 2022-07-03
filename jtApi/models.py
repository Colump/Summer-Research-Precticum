#from flask_sqlalchemy import SQLAlchemy
from re import T
from tokenize import Double
from sqlalchemy import Column, ForeignKey, Integer, Table, null
from sqlalchemy.schema import Index
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy import String, DateTime, Float, Integer, SmallInteger
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# # The flask_sqlalchemy module does not have to be initialized with the app right away
# # We declare it here, with our Models, import it into our main app and initialise
# # it there...
# db = SQLAlchemy()

class Stop(Base):
    __tablename__ = 'stops'
    # Note how we never define an __init__ method on the stops class? That’s
    # because SQLAlchemy adds an implicit constructor to all model classes which
    # accepts keyword arguments for all its columns and relationships. If you
    # decide to override the constructor for any reason, make sure to keep accepting
    # **kwargs and call the super constructor with those **kwargs to preserve this
    # behavior.
    stop_id = Column(String(12), primary_key=True)
    stop_name = Column(String(64), unique=False, nullable=False)
    stop_lat = Column(Float, unique=False, nullable=False)
    stop_lon = Column(Float, unique=False, nullable=False)
    dist_from_cc = Column(Float, unique=False, nullable=True)

    # Notes on SQLAlchemy relationship definitions here:
    # https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html
    #stop_times = relationship("StopTime")

    # NOTES: If writing a method to serialize an SQLAlchemy object, if that object
    #       contains a date you might see the error "TypeError: Object of type
    #       'datetime' is not JSON serializable".  One approach to work around
    #       that is:
    #         -> if isinstance(o, (datetime.date, datetime.time)):
    #                'my_date': self.my_date.isoformat(),
    #         -> if isinstance(o, datetime.timedelta):
    #                'my_date': str(self.my_date),

    def serialize_norels(self):
       """Return object data in easily serializeable format, no relationships"""
       return  {
            'stop_id': self.stop_id,
            'stop_name': self.stop_name,
            'stop_lat': self.stop_lat,
            'stop_lon': self.stop_lon,
            'dist_from_cc': self.dist_from_cc,
        }

    def __repr__(self):
        return '<Stop %r>' % self.stop_name

class StopTime(Base):
    __tablename__ = 'stop_times'
    trip_id = Column(String(32), primary_key=True, nullable=False)
    arrival_time = Column(DateTime, primary_key=True, nullable=False)
    departure_time = Column(DateTime, primary_key=True, nullable=False)
    #stop_id = Column(String(12), ForeignKey("stops.stop_id"), primary_key=True, nullable=False)
    stop_id = Column(String(12), primary_key=True, nullable=False)
    stop_sequence = Column(SmallInteger, primary_key=True, nullable=False)
    stop_headsign = Column(String(64), nullable=False)
    pickup_type = Column(SmallInteger, nullable=False)
    drop_off_type = Column(SmallInteger, nullable=False)
    # Note the American spelling of traveled - it caught me out - but thats what
    # is used in GTFS...
    shape_dist_traveled = Column(Float, nullable=False)

    def serialize(self):
       """Return object data in easily serializeable format"""
       return  {
            'trip_id': self.trip_id,
            'arrival_time': str(self.arrival_time),
            'departure_time': str(self.departure_time),
            'stop_id': self.stop_id,
            'stop_sequence': self.stop_sequence,
            'stop_headsign': self.stop_headsign,
            'pickup_type': self.pickup_type,
            'drop_off_type': self.drop_off_type,
            'shape_dist_traveled': self.shape_dist_traveled
        }

    def __repr__(self):
        return f'StopTime("{self.trip_id}",{self.arrival_time},{self.departure_time},"{self.stop_id}",{self.stop_sequence})'
        #return '<StopTime %r>' % (self.trip_id, self.arrival_time, self.departure_time, self.stop_id, self.stop_sequence)

class Agency(Base):
    __tablename__ = 'agency'
    agency_id = Column(String(3), primary_key=True, nullable=False)
    agency_name = Column(String(32), nullable=False)
    agency_url = Column(String(45), nullable=False)
    agency_timezone = Column(String(32), nullable=False)
    agency_lang = Column(String(32), nullable=False)
    agency_phone = Column(String(32), nullable=False) 
    agencycol = Column(String(45), nullable=True)

class Calendar(Base):
    __tablename__ = 'calendar'
    service_id = Column(String(32), primary_key=True, nullable=False)
    monday = Column(Integer, nullable=False)
    tuesday = Column(Integer,nullable=False)
    wednesday = Column(Integer,nullable=False)
    thursday = Column(Integer,nullable=False)
    friday = Column(Integer,nullable=False)
    saturday = Column(Integer,nullable=False)
    sunday = Column(Integer,nullable=False)
    start_date = Column(DateTime, primary_key=True, nullable=False) 
    end_date = Column(DateTime, primary_key=True, nullable=False)

class CalendarDates(Base):
    __tablename__ = 'calendar_dates'
    service_id = Column(String(32), primary_key=True, nullable=False)
    date = Column(DateTime, primary_key=True, nullable=False)
    exception_type = Column(Integer, nullable=True)

class Routes(Base):
    __tablename__ = 'routes'
    route_id = Column(String(32), ForeignKey("trips.route_id"), primary_key=True, nullable=False)
    agency_id = Column(String(3), ForeignKey("agency.agency_id"), nullable=False)
    route_short_name = Column(String(16), nullable=False)
    route_long_name = Column(String(72), nullable=False)
    route_type = Column(Integer, nullable=False)
class Shapes(Base):
    __tablename__ = 'shapes'
    shape_id = Column(String(32), primary_key=True, nullable=False)
    shape_pt_lat = Column(Float, primary_key=True, nullable=False)
    shape_pt_lon = Column(Float, primary_key=True, nullable=False)
    shape_pt_sequence = Column(Float, primary_key=True, nullable=False)
    shape_dist_traveled = Column(Float, nullable=False)

class Transfers(Base):
   __tablename__ = 'transfers'
   from_stop_id = Column(String(12), primary_key=True, nullable=False)
   to_stop_id = Column(String(12), primary_key=True, nullable=False)
   transfer_type = Column(SmallInteger, nullable=False)
   min_transfer_time = Column(Integer, nullable=True)

class Trips(Base):
    __tablename__ = 'trips'
    route_id = Column(String(32), primary_key=True, nullable=False)
    service_id = Column(String(32), nullable=False)
    trip_id = Column(String(32), primary_key=True, nullable=False)
    shape_id = Column(String(32), primary_key=True, nullable=False)
    trip_headsign = Column(String(73), nullable=False)
    direction_id = Column(SmallInteger, nullable=False)





# class weatherHistory(db.Model):
#     __tablename__ = 'weatherHistory'
#     weatherTime = db.Column(db.DateTime, primary_key=True)
#     latitude = db.Column(db.Float)
#     longitude = db.Column(db.Float)
#     main = db.Column(db.String(45), nullable=True)
#     description = db.Column(db.String(256), nullable=True)
#     temp = db.Column(db.Float, nullable=True)
#     feels_like = db.Column(db.Float, nullable=True)
#     temp_min = db.Column(db.Float, nullable=True)
#     temp_max = db.Column(db.Float, nullable=True)
#     pressure = db.Column(db.Integer, nullable=True)
#     humidity = db.Column(db.Integer, nullable=True)
#     sea_level = db.Column(db.Integer, nullable=True)
#     grnd_level = db.Column(db.Integer, nullable=True)
#     wind_speed = db.Column(db.Float, nullable=True)
#     wind_deg = db.Column(db.Integer, nullable=True)
#     wind_gust = db.Column(db.Float, nullable=True)
#     clouds_all = db.Column(db.Integer, nullable=True)
#     country = db.Column(db.String(64), nullable=True)
#     name = db.Column(db.String(128), nullable=True)

#     def __repr__(self):
#         return '<Station %r>' % self.stationName