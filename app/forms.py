from __future__ import absolute_import
from flask.ext.wtf import Form
from wtforms import BooleanField, IntegerField, PasswordField, SelectField, \
    StringField, validators
from flask.ext.bcrypt import Bcrypt

from app import app, db
from app.models import User


bcrypt = Bcrypt(app)


class BackupForm(Form):
    """
    Backup form and its fields.
    """
    name = StringField('name', 
                       validators=[validators.DataRequired(),
                                   validators.Length(min=1, max=140)])
    server = StringField('server', 
                       validators=[validators.DataRequired(),
                                   validators.Length(min=1, max=256)])
    port = IntegerField('port', 
                        validators=[validators.DataRequired(),
                                    validators.NumberRange(min=1, max=65536)])
    protocol = SelectField(choices=[(1, 'SMB')], coerce=int)

    location = StringField('location', 
                           validators=[validators.DataRequired(),
                                       validators.Length(min=1, max=512)])
    start_day = SelectField(choices=[(1, 'Sunday'), (2, 'Monday'),
                                     (3, 'Tuesday'), (4, 'Wednesday'),
                                     (5, 'Thursday'), (6, 'Friday'),
                                     (7, 'Sunday')],
                            coerce=int)

    start_time = SelectField(choices=[(1, '1 AM'), (2, '2 AM'), (3, '3 AM'),
                                      (4, '4 AM'), (5, '5 AM'), (6, '6 AM'),
                                      (7, '7 AM'), (8, '8 AM'), (9, '9 AM'),
                                      (10, '10 AM'), (11, '11 AM'), 
                                      (12, '12 PM'), (13, '1 PM'),
                                      (14, '2 PM'), (15, '3 PM'),
                                      (16, '4 PM'), (17, '5 PM'),
                                      (18, '6 PM'), (19, '7 PM'),
                                      (20, '8 PM'), (21, '9 PM'),
                                      (22, '10 PM'), (23, '11 PM'),
                                      (24, '12 AM')],
                             coerce=int)
    interval = SelectField(choices=[(1, 'Daily'), (2, 'Weekly'),
                                    (3, 'Monthly')],
                           coerce=int)


class DeleteBackupForm(Form):
    """
    Form for deleting a backup.
    """
    pass


class LoginForm(Form):
    """
    Login form and its fields.
    """
    email = StringField('email', validators=[validators.DataRequired()])
    password = PasswordField('password',
                             validators=[validators.DataRequired()])
    remember_me = BooleanField('remember_me', default=False)


class LoginChecker(object):
    """
    Form that checks if a login is valid.
    """
    def __init__(self, email, password):
        self._email = email
        self._password = password

    @property
    def is_valid(self):
        user = self.lookup_user
        if user is not None:
            # check typed password against hashed pw in DB
            if bcrypt.check_password_hash(user.password, self._password):
                return True
        return False

    @property
    def lookup_user(self):
        """ Returns the user that is being validated. """
        return db.session.query(User).filter_by(email=self._email).first()
