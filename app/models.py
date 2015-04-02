from __future__ import absolute_import
import datetime

from app import bcrypt
from app import db


class User(db.Model):
    """
    User model.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password = db.Column(db.String(20))

    def set_password(self, password):
        """ Sets the passwrod for a user. """
        pw_hash = bcrypt.generate_password_hash(password)
        self.password = pw_hash

    def is_authenticated(self):
        """ Returns authentication status of a user. """
        return True

    def is_active(self):
        """ Returns true if the user is active. """
        return True

    def get_id(self):
        """ Returns the id of a user. """
        return self.id

    def __repr__(self):
        return '<User %r>' % (self.email)
 

class Backup(db.Model):
    """
    Backup model that represents the backup job.
    """

    class STATUS():
        """ Enumeration of backup status. """
        RUNNING = 1
        FINISHED = 2
        ERROR = 3
        NEVER_STARTED = 4

    class PROTOCOL():
        """ Enumeration of backup server protocols. """
        SMB = 1

    class INTERVAL():
        """ Enumeration of backup intervals. """
        DAILY = 1
        WEEKLY = 2
        MONTHLY = 3

    class DAY():
        """ Enumeration of days of the week. """
        SUNDAY = 1
        MONDAY = 2
        TUESDAY = 3
        WEDNESDAY = 4
        THURSDAY = 5
        FRIDAY = 6
        SATURDAY = 7

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))

    server = db.Column(db.String(256))
    port = db.Column(db.Integer)
    protocol = db.Column(db.Integer)
    location = db.Column(db.String(512))
    username = db.Column(db.String(256))
    password = db.Column(db.String(256))

    # Start day of the week of the backup job
    start_day = db.Column(db.Integer)
    # Start time (hour of the day) of the backup job
    start_time = db.Column(db.Integer)

    # Interval based on INTERVAL enumeration
    interval = db.Column(db.Integer)
    last_backup = db.Column(db.DateTime)

    # Days to keep backups
    retention = db.Column(db.Integer)

    status = db.Column(db.Integer)
    error_message = db.Column(db.String(512))

    def __init__(self, name, server, port, protocol, location, username,
                 password, start_day, start_time, interval, retention):
        self.name = name

        self.server = server
        self.port = port
        self.protocol = protocol
        self.location = location
        self.username = username
        self.password = password

        self.start_day = start_day
        self.start_time = start_time
        self.interval = interval
        self.retention = retention

        # Default properties of a new Backup
        self.status = self.STATUS.NEVER_STARTED
        self.error_message = ''

    def finished(self):
        """ Called when a backup has finished successfully. """
        self.last_backup = datetime.datetime.now()
        self.status = self.STATUS.FINISHED
        self.error_message = ''

    def failed(self, error_message):
        """ Called when a backup has failed. """
        self.status = self.STATUS.ERROR
        self.error_message = error_message

    def started(self):
        """ Called when a backup has started. """
        self.status = self.STATUS.RUNNING
        self.error_message = ''


    def __repr__(self):
        return '<Backup %r>' % (self.name)
