import os
import random
import string
import tempfile
import unittest

from flask.ext.bcrypt import Bcrypt

from app import app, db
from app.models import Backup, User

bcrypt = Bcrypt(app)


def random_string(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))


class BaseTestCase(unittest.TestCase):
    """ Abstract base test class for this app. """

    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.app = app.test_client()
        db.create_all()
 
    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

        # Delete all users
        User.query.delete()
        db.session.commit()

    def create_test_user(self, email, password):
        # Create a test user
        user = User()
        user.email = email
        user.set_password(password)
        db.session.add(user)
        db.session.commit()


class BaseLoginTestCase(BaseTestCase):
    """ Abstract test case for login testing. """

    def __init__(self, *args, **kwargs):
        super(BaseLoginTestCase, self).__init__(*args, **kwargs)

    def login(self, email, password):
        """ Login to the app. """

        data = {
            'email': email,
            'password': password,
        }
        return self.app.post('/login', data=data, follow_redirects=True)

    def logout(self):
        """ Logout from the app. """

        return self.app.get('/logout', follow_redirects=True) 
    
    def tearDown(self):
        # logout after running all tests
        self.logout()
        super(BaseLoginTestCase, self).tearDown()


class BaseAuthenticatedTestCase(BaseLoginTestCase):
    """ Base test case for testing authenticated views. """
    
    def setUp(self):
        super(BaseAuthenticatedTestCase, self).setUp()
        # Create a test user
        self.create_test_user('vader@deathstar.com', 'noarms')
        # Login as the test user
        self.login('vader@deathstar.com', 'noarms')


class AuthenticatedViewTestCase(BaseAuthenticatedTestCase):
    """ Tests related to misc actions when the user is logged in. """
    
    def test_login_page_already_authenticated(self):
        """ Test viewing the login page while authenticated. """
        resp = self.app.get('/login', follow_redirects=True)
        # The user is redirected elsewhere
        assert 'Backups | StorageBright Backup Appliance' in resp.data

    def test_index_page_already_authenticated(self):
        """ Test viewing the index page while authenticated. """
        resp = self.app.get('/', follow_redirects=True)
        # The user is redirected elsewhere
        assert 'Backups | StorageBright Backup Appliance' in resp.data


class UnauthenticatedViewTestCase(BaseTestCase):
    """
    Tests related to checking that unauthenticated users cannot access
    protected resources without logging in first.
    """

    def test_stream_view(self):
        """ Test accessing the stream view without being logged in. """
        resp = self.app.get('/backups', follow_redirects=True)
        assert 'Login | StorageBright Backup Appliance' in resp.data


class LoginTestCase(BaseLoginTestCase):
    """ Tests related to logging in and logging out. """

    def setUp(self):
        super(LoginTestCase, self).setUp()
        # Create a test user
        self.create_test_user('vader@deathstar.com', 'noarms')

    def test_invalid_email(self):
        """ Test an invalid email address. """
        resp = self.login('invaliduser', 'notfound')
        assert 'Invalid Login' in resp.data

    def test_blank_email(self):
        """ Test a blank email address. """
        resp = self.login('', 'notfound')
        assert 'This field is required' in resp.data

    def test_invalid_password(self):
        """ Test an invalid password with a valid email. """
        resp = self.login('vader@deathstar.com', 'default')
        assert 'Invalid Login' in resp.data

    def test_blank_password(self):
        """ Test a blank password with a valid email. """
        resp = self.login('vader@deathstar.com', '')
        assert 'This field is required' in resp.data

    def test_valid_login(self):
        """ Test a valid email and a valid password. """

        resp = self.login('vader@deathstar.com', 'noarms')
        assert 'Backups | StorageBright Backup Appliance' in resp.data

    def test_logout(self):
        """ Test logging out after logging in. """

        # Login as the test user
        self.login('vader@deathstar.com', 'noarms')

        self.app.get('/logout', follow_redirects=True)
        
        resp = self.app.get('/backups', follow_redirects=True)
        assert 'Login | StorageBright Backup Appliance' in resp.data


class CreateBackupTestCase(BaseAuthenticatedTestCase):
    """ Test creating backup jobs. """

    def test_create_backup_with_valid_settings(self):
        """ Test creating a new backup job with valid settings. """
        
        assert Backup.query.count() == 0

        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }
        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 1

    def test_create_backup_with_missing_name_setting(self):
        """ Test creating a new backup job with missing name setting. """
        
        data = {
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'The backup name was not specified.' in resp.data

    def test_create_backup_with_missing_server_setting(self):
        """ Test creating a new backup job with missing server setting. """
        
        data = {
            'name': 'Teacher Backups',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'The server address was not specified.' in resp.data

    def test_create_backup_with_missing_port_setting(self):
        """ Test creating a new backup job with missing port setting. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'The server port was not specified.' in resp.data

    def test_create_backup_with_missing_protocol_setting(self):
        """ Test creating a new backup job with missing protocol setting. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'The server protocol was not specified.' in resp.data

    def test_create_backup_with_missing_start_time_setting(self):
        """
        Test creating a new backup job with missing start_time setting.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'interval': 24
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'The start time was not specified.' in resp.data

    def test_create_backup_with_missing_interval_setting(self):
        """ Test creating a new backup job with missing interval setting. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'The interval was not specified.' in resp.data

    def test_create_backup_with_name_length_below_minimum(self):
        """
        Test creating a new backup job with name length below the minimum.
        """
        
        data = {
            'name': '',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'The name must contain at least 1 characters.' in resp.data

    def test_create_backup_with_name_length_above_maximum(self):
        """
        Test creating a new backup job with name length above the maximum.
        """
        
        data = {
            'name': 'X'*141,
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'The name must be less than 140 characters.' in resp.data

    def test_create_backup_with_port_number_below_minimum(self):
        """
        Test creating a new backup job with a port number below the minimum
        allowed value.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 0,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }
        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'Invalid port number.' in resp.data

    def test_create_backup_with_port_number_above_maximum(self):
        """
        Test creating a new backup job with a port number above the maximum
        allowed value.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 65536,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }
        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'Invalid port number.' in resp.data

    def test_create_backup_with_interval_below_minimum(self):
        """
        Test creating a new backup job with an interval below the minimum
        allowed value.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 0
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'The interval must be at least 1 hour.' in resp.data

    def test_create_backup_with_interval_above_maximum(self):
        """
        Test creating a new backup job with an interval above the maximum
        value.
        """
        
        # There are 17531.6 hours in 2 years

        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 17532
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'The interval must be less than 2 years.' in resp.data


class EditBackupTestCase(BaseAuthenticatedTestCase):
    """ Test editing backup jobs. """

    def setUp(self):
        super(EditBackupTestCase, self).setUp()

        # New Backup object for each test
        self.new_backup = Backup()

        db.session.add(self.new_backup)
        db.session.commit()

        # URL for editing the newly created Backup object
        self.edit_backup_url = "/backups/edit/{}".format(self.new_backup.id)

    def tearDown(self):
        super(EditBackupTestCase, self).tearDown()

        Backup.query.delete()
        db.session.commit()

    def test_edit_backup_with_valid_settings(self):
        """ Test editing a backup job with valid settings. """
       
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }
        resp = self.app.post(self.edit_backup_url, data=data,
                             follow_redirects=True)
        assert resp.status_code == 200

        backup = Backup.query.first()
        assert backup.name == data['name']
        assert backup.server == data['server']
        assert backup.port == data['port']
        assert backup.protocol == data['protocol']
        assert backup.start_time == data['start_time']
        assert backup.interval == data['interval']

    def test_edit_backup_with_missing_name_setting(self):
        """ Test editing a new backup job with missing name setting. """
        
        data = {
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }

        resp = self.app.post(self.edit_backup_url, data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'The backup name was not specified.' in resp.data

        backup = Backup.query.first()
        assert not backup.server == data['server']
        assert not backup.port == data['port']
        assert not backup.protocol == data['protocol']
        assert not backup.start_time == data['start_time']
        assert not backup.interval == data['interval']

    def test_edit_backup_with_missing_server_setting(self):
        """ Test editing a new backup job with missing server setting. """
        
        data = {
            'name': 'Teacher Backups',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }

        resp = self.app.post(self.edit_backup_url, data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'The server address was not specified.' in resp.data

        backup = Backup.query.first()
        assert not backup.name == data['name']
        assert not backup.port == data['port']
        assert not backup.protocol == data['protocol']
        assert not backup.start_time == data['start_time']
        assert not backup.interval == data['interval']

    def test_edit_backup_with_missing_port_setting(self):
        """ Test editing a new backup job with missing port setting. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }

        resp = self.app.post(self.edit_backup_url, data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'The server port was not specified.' in resp.data
        
        backup = Backup.query.first()
        assert not backup.name == data['name']
        assert not backup.server == data['server']
        assert not backup.protocol == data['protocol']
        assert not backup.start_time == data['start_time']
        assert not backup.interval == data['interval']

    def test_edit_backup_with_missing_protocol_setting(self):
        """ Test editing a new backup job with missing protocol setting. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }

        resp = self.app.post(self.edit_backup_url, data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'The server protocol was not specified.' in resp.data
        
        backup = Backup.query.first()
        assert not backup.name == data['name']
        assert not backup.server == data['server']
        assert not backup.port == data['port']
        assert not backup.start_time == data['start_time']
        assert not backup.interval == data['interval']

    def test_edit_backup_with_missing_start_time_setting(self):
        """ Test editing a new backup job with missing start_time setting. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'interval': 24
        }

        resp = self.app.post(self.edit_backup_url, data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'The start time was not specified.' in resp.data
        
        backup = Backup.query.first()
        assert not backup.name == data['name']
        assert not backup.server == data['server']
        assert not backup.port == data['port']
        assert not backup.protocol == data['protocol']
        assert not backup.interval == data['interval']

    def test_edit_backup_with_missing_interval_setting(self):
        """ Test editing a new backup job with missing interval setting. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
        }

        resp = self.app.post(self.edit_backup_url, data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'The interval was not specified.' in resp.data
        
        backup = Backup.query.first()
        assert not backup.name == data['name']
        assert not backup.server == data['server']
        assert not backup.port == data['port']
        assert not backup.protocol == data['protocol']
        assert not backup.start_time == data['start_time']

    def test_edit_backup_with_name_length_below_minimum(self):
        """
        Test editing a new backup job with name length below the minimum.
        """
        
        data = {
            'name': '',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }

        resp = self.app.post(self.edit_backup_url, data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'The name must contain at least 1 characters.' in resp.data
        
        backup = Backup.query.first()
        assert not backup.name == data['name']
        assert not backup.server == data['server']
        assert not backup.port == data['port']
        assert not backup.protocol == data['protocol']
        assert not backup.start_time == data['start_time']
        assert not backup.interval == data['interval']

    def test_edit_backup_with_name_length_above_maximum(self):
        """
        Test editing a new backup job with name length above the maximum.
        """
        
        data = {
            'name': 'X'*141,
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }

        resp = self.app.post(self.edit_backup_url, data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'The name must be less than 140 characters.' in resp.data
        
        backup = Backup.query.first()
        assert not backup.name == data['name']
        assert not backup.server == data['server']
        assert not backup.port == data['port']
        assert not backup.protocol == data['protocol']
        assert not backup.start_time == data['start_time']
        assert not backup.interval == data['interval']

    def test_edit_backup_with_port_number_below_minimum(self):
        """
        Test editing a new backup job with a port number below the minimum
        allowed value.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 0,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }
        resp = self.app.post(self.edit_backup_url, data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'Invalid port number.' in resp.data
        
        backup = Backup.query.first()
        assert not backup.name == data['name']
        assert not backup.server == data['server']
        assert not backup.port == data['port']
        assert not backup.protocol == data['protocol']
        assert not backup.start_time == data['start_time']
        assert not backup.interval == data['interval']

    def test_edit_backup_with_port_number_above_maximum(self):
        """
        Test editing a new backup job with a port number above the maximum
        allowed value.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 65536,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 24
        }
        resp = self.app.post(self.edit_backup_url, data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'Invalid port number.' in resp.data
        
        backup = Backup.query.first()
        assert not backup.name == data['name']
        assert not backup.server == data['server']
        assert not backup.port == data['port']
        assert not backup.protocol == data['protocol']
        assert not backup.start_time == data['start_time']
        assert not backup.interval == data['interval']

    def test_edit_backup_with_interval_below_minimum(self):
        """
        Test editing a new backup job with an interval below the minimum
        allowed value.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 0
        }

        resp = self.app.post(self.edit_backup_url, data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'The interval must be at least 1 hour.' in resp.data
        
        backup = Backup.query.first()
        assert not backup.name == data['name']
        assert not backup.server == data['server']
        assert not backup.port == data['port']
        assert not backup.protocol == data['protocol']
        assert not backup.start_time == data['start_time']
        assert not backup.interval == data['interval']

    def test_edit_backup_with_interval_above_maximum(self):
        """
        Test editing a new backup job with an interval above the maximum
        value.
        """
        
        # There are 17531.6 hours in 2 years

        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 'SMB',
            'start_time': '1/21/14 01:04:00',
            'interval': 17532
        }

        resp = self.app.post(self.edit_backup_url, data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'The interval must be less than 2 years.' in resp.data
        
        backup = Backup.query.first()
        assert not backup.name == data['name']
        assert not backup.server == data['server']
        assert not backup.port == data['port']
        assert not backup.protocol == data['protocol']
        assert not backup.start_time == data['start_time']
        assert not backup.interval == data['interval']


class DeleteBackupTestCase(BaseAuthenticatedTestCase):
    """ Test deleting backup jobs. """

    def setUp(self):
        super(EditBackupTestCase, self).setUp()

        # New Backup object for each test
        self.new_backup = Backup()

        db.session.add(self.new_backup)
        db.session.commit()

        # URL for deleting the newly created Backup object
        self.edit_backup_url = "/backups/delete/{}".format(self.new_backup.id)

    def tearDown(self):
        super(EditBackupTestCase, self).tearDown()

        Backup.query.delete()
        db.session.commit()

    def test_delete_valid_backup(self):
        """ Test deleting a valid backup. """

        resp = self.app.get(self.delete_backup_url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Are you sure you want to delete this backup?' in resp.data

        resp = self.app.post(self.delete_backup_url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Backup was deleted successfully.' in resp.data

        assert not Backup.query.count()

    def test_delete_invalid_backup(self):
        """ Test deleting an invalid backup. """

        assert Backup.query.count() == 1

        resp = self.app.get(self.delete_backup_url, follow_redirects=True)
        assert resp.status_code == 404

        resp = self.app.post(self.delete_backup_url, follow_redirects=True)
        assert resp.status_code == 404
        
        assert Backup.query.count() == 1


if __name__ == '__main__':
    unittest.main()
