from __future__ import absolute_import

from flask import abort, flash, g, redirect, render_template, request,\
    url_for
from flask.ext.login import current_user, login_required, login_user, \
    logout_user

from app import app, db, login_manager
from app.forms import BackupForm, DeleteBackupForm, DisableBackupForm, \
    EnableBackupForm, LoginChecker, LoginForm
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

    all_backups = Backup.query.all()

    return render_template('backups.html', title='Backups',
                           all_backups=all_backups)


@app.route('/backups/new', methods=['GET', 'POST'])
@login_required
def new_backup():
    """Route for the new backup page."""

    form = BackupForm(request.form)

    if form.validate_on_submit():
        new_backup = Backup(name=form.name.data, server=form.server.data,
                            port=form.port.data, protocol=form.protocol.data,
                            location=form.location.data,
                            username=form.username.data,
                            password=form.password.data,
                            start_time=form.start_time.data,
                            start_day=form.start_day.data,
                            interval=form.interval.data,
                            retention=form.retention.data)

        db.session.add(new_backup)
        db.session.commit()

        flash("Backup job was created successfully.", "success")
        return redirect(url_for('index'))

    return render_template('new-backup.html', title='New Backup',
                           form=form)


@app.route('/backups/edit/<backup_id>', methods=['GET', 'POST'])
@login_required
def edit_backup(backup_id):
    """Route for the edit single backup page."""

    backup_query = Backup.query.filter(Backup.id==backup_id)

    if backup_query.first() is None:
        return abort(404)

    backup = backup_query.first()

    if request.method == "POST":
        form = BackupForm(request.form)
    else:
        form = BackupForm(name=backup.name, server=backup.server,
                          port=backup.port, protocol=backup.protocol,
                          location=backup.location, 
                          username=backup.username,
                          password=backup.password,
                          start_time=backup.start_time,
                          start_day=backup.start_day,
                          interval=backup.interval,
                          retention=backup.retention)

    if form.validate_on_submit():
        # Modify the existing backup
        backup.name = form.name.data
        backup.server = form.server.data
        backup.port = form.port.data
        backup.protocol = form.protocol.data
        backup.location = form.location.data
        backup.username = form.username.data
        if len(form.password.data) > 0:
            backup.password = form.password.data
        backup.start_time = form.start_time.data
        backup.start_day = form.start_day.data
        backup.interval = form.interval.data
        backup.retention = form.retention.data

        # Save changes to the database
        db.session.commit()

        flash("Backup job was saved successfully.", "success")
        return redirect(url_for('index'))

    return render_template('edit-backup.html', title='Edit Backup',
                           form=form)


@app.route('/backups/delete/<backup_id>', methods=['GET', 'POST'])
@login_required
def delete_backup(backup_id):
    """Route for the delete backup page."""

    backup = Backup.query.filter(Backup.id==backup_id)

    if backup.first() is None:
        return abort(404)
    
    form = DeleteBackupForm(request.form)

    if form.validate_on_submit():
        backup.delete()
        db.session.commit()

        flash("Backup job was deleted successfully.", "success")
        return redirect(url_for('index'))

    return render_template('delete-backup.html', title='Delete Backup',
                           form=form)


@app.route('/backups/disable/<backup_id>', methods=['GET', 'POST'])
@login_required
def disable_backup(backup_id):
    """Route for the disable backup page."""

    backup = Backup.query.filter(Backup.id==backup_id)

    if backup.first() is None:
        return abort(404)

    backup = backup.first()

    form = DisableBackupForm(request.form)

    if form.validate_on_submit():
        backup.enabled = False
        db.session.commit()

        flash("Backup job was disabled successfully.", "success")
        return redirect(url_for('index'))

    return render_template('disable-backup.html', title='Disable Backup',
                           form=form)


@app.route('/backups/enable/<backup_id>', methods=['GET', 'POST'])
@login_required
def enable_backup(backup_id):
    """Route for the enable backup page."""

    backup = Backup.query.filter(Backup.id==backup_id)

    if backup.first() is None:
        return abort(404)

    backup = backup.first()

    form = EnableBackupForm(request.form)

    if form.validate_on_submit():
        backup.enabled = True
        db.session.commit()

        flash("Backup job was enabled successfully.", "success")
        return redirect(url_for('index'))

    return render_template('enable-backup.html', title='Enable Backup',
                           form=form)


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
