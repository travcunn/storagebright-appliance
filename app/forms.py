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


class ResetPWChecker(object):
    """
    Form that checks if email and security questions are valid.
    """
    def __init__(self, email, securityAnswer1, securityAnswer2,
                 securityAnswer3):
        self._email = email
        self._securityAnswer1 = securityAnswer1
        self._securityAnswer2 = securityAnswer2
        self._securityAnswer3 = securityAnswer3

    @property
    def is_valid(self):
        user = self.lookup_user
        if user is not None:    
            # check typed password against hashed pw in DB
            if (user.securityAnswer1==self._securityAnswer1) and \
                    (user.securityAnswer2==self._securityAnswer2) and \
                    (user.securityAnswer3==self._securityAnswer3):
	        return True
        return False

    @property
    def lookup_user(self):
        """ Returns the user that is being validated. """
        return db.session.query(User).filter_by(email=self._email).first()


class BarkForm(Form):
    """
    New bark form.
    """
    barkBody = TextAreaField('bark', validators=[DataRequired()])


class FollowForm(Form):
    """
    Form for following other users
    """
    email = StringField('email', validators=[DataRequired()])


class RegistrationForm(Form):
    """
    Registration form and its fields. All of the fields are required.
    """
    firstName = StringField('firstName', validators=[DataRequired()])
    lastName = StringField('firstName', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    password_match = PasswordField('password_match',
                                   validators=[DataRequired()])
    securityQuestion1 = StringField('securityQuestion1',
                                    validators=[DataRequired()])
    securityAnswer1 = StringField('securityAnswer1',
                                  validators=[DataRequired()])
    securityQuestion2 = StringField('securityQuestion2',
                                    validators=[DataRequired()])
    securityAnswer2 = StringField('securityAnswer2',
                                  validators=[DataRequired()])
    securityQuestion3 = StringField('securityQuestion3',
                                    validators=[DataRequired()])
    securityAnswer3 = StringField('securityAnswer3',
                                  validators=[DataRequired()])
    
class ResetPasswordForm(Form):
    """
    Registration form and its fields. All of the fields are required.
    """
    password = PasswordField('password', validators=[DataRequired()])
    password_match = PasswordField('password_match',
                                   validators=[DataRequired()])
    securityAnswer1 = StringField('securityAnswer1',
                                  validators=[DataRequired()])
    securityAnswer2 = StringField('securityAnswer2',
                                  validators=[DataRequired()])
    securityAnswer3 = StringField('securityAnswer3',
                                  validators=[DataRequired()])
