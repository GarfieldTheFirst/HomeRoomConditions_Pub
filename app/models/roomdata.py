from datetime import datetime
from flask_login import AnonymousUserMixin, UserMixin
import jwt
from app import db, login
from flask import current_app
from hashlib import md5
from time import time
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email in current_app.config['ADMINS']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except Exception:
            return
        return User.query.get(id)

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)


class Followers(db.Model):
    __tablename__ = "followers"
    id = db.Column(db.Integer, primary_key=True)
    follower = db.Column('follower_id', db.Integer, db.ForeignKey('user.id'))
    followed = db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


login.anonymous_user = AnonymousUser


class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    # What does the index=True do?
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.USER],
            'Administrator': [Permission.USER, Permission.ADMIN],
            'Tentative': [Permission.DEFAULT]
        }
        default_role = 'Tentative'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()


class Permission:
    DEFAULT = 1
    USER = 2
    ADMIN = 16


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
    day_id = db.Column(db.Integer, db.ForeignKey('day.id'))
    data_points = db.relationship('Roomdata', lazy='select',
                                  backref=db.backref('hour', lazy='joined'))


class Roomdata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Integer, nullable=True)
    humidity = db.Column(db.Integer, nullable=True)
    movement_detection = db.Column(db.Integer, nullable=True)
    date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    hour_id = db.Column(db.Integer, db.ForeignKey('hour.id'), nullable=False)
    device_id = db.Column(db.Integer,
                          db.ForeignKey('device.id', ondelete='CASCADE'),
                          nullable=True)
