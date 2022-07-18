#from flask_sqlalchemy import SQLAlchemy
from re import T
from tokenize import Double
from sqlalchemy import Column, DateTime, Float, ForeignKey, func, Integer
from sqlalchemy import LargeBinary, SmallInteger, String, Table, null
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.schema import Index
from sqlalchemy.types import UserDefinedType

Base = declarative_base()

# # The flask_sqlalchemy module does not have to be initialized with the app right away
# # We declare it here, with our Models, import it into our main app and initialise
# # it there...
# db = SQLAlchemy()

#===============================================================================
#===============================================================================
#===============================================================================

class Point(UserDefinedType):
    cache_ok=True
    def get_col_spec(self):
        return "POINT"

    def bind_expression(self, bindvalue):
        return func.ST_GeomFromText(bindvalue, type_=self)

    def column_expression(self, col):
        return func.ST_AsText(col, type_=self)

#===============================================================================
#===============================================================================
#===============================================================================

class Agency(Base):
    __tablename__ = 'agency'
    agency_id = Column(String(3), primary_key=True, nullable=False)
    agency_name = Column(String(32), nullable=False)
    agency_url = Column(String(45), nullable=False)
    agency_timezone = Column(String(32), nullable=False)
    agency_lang = Column(String(32), nullable=False)
    agency_phone = Column(String(32), nullable=False) 
    agencycol = Column(String(45), nullable=True)

    def serialize(self):
       """Return object data in easily serializeable format"""
       return{
           'agency_id': self.agency_id,
           'agency_name': self.agency_name,
           'agency_url': self.agency_url,
           'agency_timezone': self.agency_timezone,
           'agency_lang': self.agency_lang,
           'agency_phone': self.agency_phone,
           'agencycol': self.agencycol,
       }

    def __repr__(self):
        return '<Agency %r>' % (self.agency_id, self.agency_name)

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

    def serialize(self):
        """Return object data in easily serializeable format"""
        return{
            'service_id': self.service_id,
            'monday': self.monday,
            'tuesday': self.tuesday,
            'wednesday': self.wednesday,
            'thursday': self.thursday,
            'friday': self.friday,
            'saturday': self.saturday,
            'sunday': self.sunday,
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
    def __repr__(self):
        return '<Calendar %r>' % (self.service_id, self.start_date, self.end_date)

class CalendarDates(Base):
    __tablename__ = 'calendar_dates'
    service_id = Column(String(32), primary_key=True, nullable=False)
    date = Column(DateTime, primary_key=True, nullable=False)
    exception_type = Column(Integer, nullable=True)

    def serialize(self):
        """Return object data in easily serializeable format"""
        return{
            'service_id': self.service_id,
            'date': str(self.date),
            'exception_type': self.exception_type,
        }
    def __repr__(self):
        return '<CalendarDates %r>' % (self.service_id, self.date)


class Routes(Base):
    __tablename__ = 'routes'
    route_id = Column(String(32), ForeignKey("trips.route_id"), primary_key=True, nullable=False)
    agency_id = Column(String(3), ForeignKey("agency.agency_id"), nullable=False)
    route_short_name = Column(String(16), nullable=False)
    route_long_name = Column(String(72), nullable=False)
    route_type = Column(Integer, nullable=False)

    def serialize(self):
        """Return object data in easily serializeable format"""
        return{
            'route_id': self.route_id,
            'agency_id': self.agency_id,
            'route_short_name': self.route_short_name,
            'route_long_name': self.route_long_name,
            'route_type': self.route_type,
        }

    def __repr__(self):
        return '<Routes %r>' % (self.route_id, self.route_short_name, self.route_long_name, self.route_type)    

class Shapes(Base):
    __tablename__ = 'shapes'
    shape_id = Column(String(32), primary_key=True, nullable=False)
    shape_pt_lat = Column(Float, primary_key=True, nullable=False)
    shape_pt_lon = Column(Float, primary_key=True, nullable=False)
    shape_pt_sequence = Column(Float, primary_key=True, nullable=False)
    shape_dist_traveled = Column(Float, nullable=False)

    def serialize(self):
        return{
            'shape_id': self.shape_id,
            'shape_pt_lat': self.shape_pt_lat,
            'shape_pt_lon': self.shape_pt_lon,
            'shape_pt_sequence': self.shape_pt_sequence,
            'shape_dist_traveled': self.shape_dist_traveled,
        }

    def __repr__(self):
        return '<Routes %r>' % (self.shape_id, self.shape_pt_lat, self.shape_pt_lon)    


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
    stop_position = Column(Point, unique=False, nullable=False)
    dist_from_cc = Column(Float, unique=False, nullable=False)

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

    def serialize(self):
       """Return object data in easily serializeable format, no relationships"""
       return  {
            'stop_id': self.stop_id,
            'stop_name': self.stop_name,
            'stop_lat': self.stop_lat,
            'stop_lon': self.stop_lon
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


class Trips(Base):
    __tablename__ = 'trips'
    route_id = Column(String(32), primary_key=True, nullable=False)
    service_id = Column(String(32), nullable=False)
    trip_id = Column(String(32), primary_key=True, nullable=False)
    shape_id = Column(String(32), primary_key=True, nullable=False)
    trip_headsign = Column(String(73), nullable=False)
    direction_id = Column(SmallInteger, nullable=False)

    def serialize(self):
        return {
            'route_id': self.route_id,
            'service_id': self.service_id,
            'trip_id': self.trip_id,
            'shape_id': self.shape_id,
            'trip_headsign': self.trip_headsign,
            'direction_id': self.direction_id,
        }

    def __repr__(self):
        return '<Trips %r>' % (self.route_id, self.service_id, self.trip_id, self.shape_id, self.trip_headsign)


class Transfers(Base):
    __tablename__ = 'transfers'
    from_stop_id = Column(String(12), primary_key=True, nullable=False)
    to_stop_id = Column(String(12), primary_key=True, nullable=False)
    transfer_type = Column(SmallInteger, nullable=False)
    min_transfer_time = Column(Integer, nullable=False)

    def serialize(self):
       return{
           'from_stop_id': self.from_stop_id,
           'to_stop_id': self.to_stop_id,
           'transfer_type': self.transfer_type,
           'min_transfer_time': self.min_transfer_time
       }
    def __repr__(self):
        return '<Transfers %r>' % (self.from_stop_id, self.to_stop_id, self.transfer_type, self.min_transfer_time)

class JT_User(Base):
    __tablename__ = 'jt_user'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)  # Auto-increment should be default
    username = Column(String(256), primary_key=True, nullable=False)
    password_hash = Column(String(60), nullable=False)
    nickname = Column(String(256), nullable=True)
    colour = Column(String(6), nullable=True)
    profile_picture_filename = Column(String(256), nullable=True)
    profile_picture = Column(LargeBinary, nullable=True)

    def __repr__(self):
        return f'StopTime("{self.id}","{self.name}"'
        
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