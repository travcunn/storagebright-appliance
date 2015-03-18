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
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.email)
 

class Backup(db.Model):
    """
    Backup model that represents the backup job.
    """

    class STATUS():
        RUNNING = 1
        FINISHED = 2
        ERROR = 3
        NEVER_STARTED = 4

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    location = db.Column(db.String(512))
    start_time = db.Column(db.DateTime)
    # Interval in hours
    interval = db.Column(db.Integer)
    last_backup = db.Column(db.DateTime)
    status = db.Column(db.Integer)
    error_message = db.Column(db.String(512))

    def __init__(self):
        self.status = self.STATUS.NEVER_STARTED
        self.error_message = ''

    def get_schedule_text(self):
        pass

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
