from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import Index
from sqlalchemy.dialects.mysql import TINYINT

# The flask_sqlalchemy module does not have to be initialized with the app right away
# We declare it here, with our Models, import it into our main app and initialise
# it there...
db = SQLAlchemy()

class Stop(db.Model):
    __tablename__ = 'stops'
    # Note how we never define an __init__ method on the stops class? That’s
    # because SQLAlchemy adds an implicit constructor to all model classes which
    # accepts keyword arguments for all its columns and relationships. If you
    # decide to override the constructor for any reason, make sure to keep accepting
    # **kwargs and call the super constructor with those **kwargs to preserve this
    # behavior.
    stop_id = db.Column(db.String(12), primary_key=True)
    stop_name = db.Column(db.String(64), unique=False, nullable=True)
    stop_lat = db.Column(db.Float, unique=False, nullable=True)
    stop_lon = db.Column(db.Float, unique=False, nullable=True)
    dist_from_cc = db.Column(db.Float, unique=False, nullable=True)

    # Notes on SQLAlchemy relationship definitions here:
    # https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html
    fred = db.relationship("StopTime")

    def to_json(self):
        json_stop = {
            'stop_id': self.stop_id,
            'stop_name': self.stop_name,
            'stop_lat': self.stop_lat,
            'stop_lon': self.stop_lon,
            'dist_from_cc': self.dist_from_cc
        }

        return json_stop

    def __repr__(self):
        return '<Stop %r>' % self.stop_name

class StopTime(db.Model):
    __tablename__ = 'stop_times'
    trip_id = db.Column(db.String(32), primary_key=True, nullable=False)
    arrival_time = db.Column(db.DateTime, primary_key=True, nullable=False)
    departure_time = db.Column(db.DateTime, primary_key=True, nullable=False)
    stop_id = db.Column(db.String(12), db.ForeignKey('Stop.stop_id'), primary_key=True, nullable=False)
    stop_sequence = db.Column(db.SmallInteger, primary_key=True, nullable=False)
    stop_headsign = db.Column(db.String(64), nullable=False)
    pickup_type = db.Column(db.SmallInteger, nullable=False)
    drop_off_type = db.Column(db.SmallInteger, nullable=False)
    shape_dist_travelled = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return '<StopTime %r>' % (self.trip_id, self.arrival_time, self.departure_time, self.stop_id, self.stop_sequence)

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