from datetime import datetime
from app import db


class Device(db.Model):
    __tablename__ = 'device'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=True, unique=True)
    ip = db.Column(db.String(15))
    connected = db.Column(db.Boolean)
    recording = db.Column(db.Boolean)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    data_points = db.relationship('Roomdata', lazy='select',
                                  backref=db.backref('device', lazy='joined',
                                                     passive_deletes=True))


class Year(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, default=datetime.utcnow().year)
    months = db.relationship('Month', lazy='select',
                             backref=db.backref('year', lazy='joined'))


class Month(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Integer, default=datetime.utcnow().month)
    year_id = db.Column(db.Integer, db.ForeignKey('year.id'))
    days = db.relationship('Day', lazy='select',
                           backref=db.backref('month', lazy='joined'))


class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer, default=datetime.utcnow().day)
    month_id = db.Column(db.Integer, db.ForeignKey('month.id'))
    hours = db.relationship('Hour', lazy='select',
                            backref=db.backref('day', lazy='joined'))


class Hour(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hour = db.Column(db.Integer, default=datetime.utcnow().hour)
    movement_detection = db.Column(db.Integer, default=0)
    day_id = db.Column(db.Integer, db.ForeignKey('day.id'))
    data_points = db.relationship('Roomdata', lazy='select',
                                  backref=db.backref('hour', lazy='joined'))


class Roomdata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Integer, nullable=True)
    humidity = db.Column(db.Integer, nullable=True)
    movement_detection = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    hour_id = db.Column(db.Integer, db.ForeignKey('hour.id'), nullable=False)
    device_id = db.Column(db.Integer,
                          db.ForeignKey('device.id', ondelete='CASCADE'),
                          nullable=True)
