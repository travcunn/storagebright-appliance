from flask.ext.wtf import Form
from wtforms import BooleanField, PasswordField, StringField, TextAreaField
from wtforms.validators import DataRequired
from flask.ext.bcrypt import Bcrypt

from app import app, db
from app.models import User


bcrypt = Bcrypt(app)


class LoginForm(Form):
    """
    Login form and its fields.
    """
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)


class EmailForm(Form):
    """
    Form for forgot password - submit email
    """
    email = StringField('email', validators=[DataRequired()])


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
