from datetime import datetime

from flask import flash, g, redirect, render_template, request, session, \
    url_for
from flask.ext.login import current_user, login_required, login_user, \
    logout_user
from flask.ext.bcrypt import Bcrypt

from app import app, db, login_manager
from app.forms import BarkForm, LoginChecker, LoginForm, EmailForm, \
    RegistrationForm, ResetPWChecker, ResetPasswordForm, \
    FollowForm
from app.models import Backup, User


login_manager.login_view = 'login'


@app.route('/', methods=['GET', 'POST'])
def index():
    """Redirect to home view."""
    return redirect(url_for('login'))


@app.route('/backups', methods=['GET', 'POST'])
@login_required
def backups():
    """Route for the backups page."""

    return render_template('backups.html', title='Backups')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Route for the login page."""

    if is_logged_in():
        return redirect(url_for('backups'))

    login_form = LoginForm(request.form)

    if login_form.validate_on_submit():
        login_validator = LoginChecker(email=request.form.get('email'),
                                       password=request.form.get('password'))
        if login_validator.is_valid:
            login_user(login_validator.lookup_user, remember=True)
            return redirect(url_for('backups'))
        flash('Invalid Login', 'danger')

    return render_template('login.html', title='Login', form=login_form)
    
    
@app.route("/logout")
def logout():
    """Redirect page for invalid logins."""
    logout_user()
    flash('You have been logged out.', "info")
    return redirect(url_for('login'))


def is_logged_in():
    """Returns True if the user is logged in."""
    if g.user is not None and g.user.is_authenticated():
        return True
    return False


@app.before_request
def before_request():
    """Before the request, notify flask of the current user."""
    g.user = current_user


@login_manager.user_loader
def load_user(user_id):
    """Returns a user, given a user id."""
    return User.query.get(int(user_id))
