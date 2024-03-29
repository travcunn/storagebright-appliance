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
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }
        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 1

    def test_create_backup_with_missing_name_setting(self):
        """ Test creating a new backup job with missing name setting. """
        
        data = {
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'This field is required' in resp.data

    def test_create_backup_with_missing_server_setting(self):
        """ Test creating a new backup job with missing server setting. """
        
        data = {
            'name': 'Teacher Backups',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'This field is required' in resp.data

    def test_create_backup_with_missing_port_setting(self):
        """ Test creating a new backup job with missing port setting. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'This field is required' in resp.data

    def test_create_backup_with_missing_protocol_setting(self):
        """ Test creating a new backup job with missing protocol setting. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'Not a valid choice' in resp.data

    def test_create_backup_with_missing_start_time_setting(self):
        """
        Test creating a new backup job with missing start_time setting.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'Not a valid choice' in resp.data

    def test_create_backup_with_missing_start_day_setting(self):
        """
        Test creating a new backup job with missing start_time setting.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'Not a valid choice' in resp.data

    def test_create_backup_with_missing_interval_setting(self):
        """ Test creating a new backup job with missing interval setting. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'retention': 14,
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'Not a valid choice' in resp.data

    def test_create_backup_with_name_length_below_minimum(self):
        """
        Test creating a new backup job with name length below the minimum.
        """
        
        data = {
            'name': '',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'This field is required.' in resp.data

    def test_create_backup_with_name_length_above_maximum(self):
        """
        Test creating a new backup job with name length above the maximum.
        """
        
        data = {
            'name': 'X'*141,
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'Field must be between 1 and 140 characters long.' in resp.data

    def test_create_backup_with_port_number_below_minimum(self):
        """
        Test creating a new backup job with a port number below the minimum
        allowed value.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 0,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }
        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'This field is required' in resp.data

    def test_create_backup_with_port_number_above_maximum(self):
        """
        Test creating a new backup job with a port number above the maximum
        allowed value.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 65537,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }
        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'Number must be between 1 and 65536.' in resp.data

    def test_create_backup_with_interval_below_minimum(self):
        """
        Test creating a new backup job with an interval below the minimum
        allowed value.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 0,
            'retention': 14,
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'Not a valid choice' in resp.data

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
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 4,
            'retention': 14,
        }

        resp = self.app.post('/backups/new', data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert Backup.query.count() == 0
        assert 'Not a valid choice' in resp.data


class EditBackupTestCase(BaseAuthenticatedTestCase):
    """ Test editing backup jobs. """

    def setUp(self):
        super(EditBackupTestCase, self).setUp()

        # New Backup object for each test
        self.new_backup = Backup(name='Teachers Backup', server='winshare01', 
                                 port=445, protocol=Backup.PROTOCOL.SMB,
                                 location='F:/teachers',
                                 username='testuser', password='password',
                                 start_time=1, 
                                 start_day=Backup.DAY.SUNDAY,
                                 interval=24, retention=14)

        db.session.add(self.new_backup)
        db.session.commit()

        # URL for editing the newly created Backup object
        self.edit_backup_url = "/backups/edit/{}".format(self.new_backup.id)

    def tearDown(self):
        super(EditBackupTestCase, self).tearDown()

        Backup.query.delete()
        db.session.commit()

    def test_edit_backup_default_fields(self):
        """ Test the default field values when editing a backup. """
        
        resp = self.app.get(self.edit_backup_url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'value="Teachers Backup"' in resp.data
        assert 'value="winshare01"' in resp.data
        assert 'value="445"' in resp.data
        assert 'value="F:/teachers"' in resp.data
        assert 'value="1"' in resp.data
        assert 'value="24"' in resp.data
        assert 'value="14"' in resp.data

    def test_edit_backup_with_valid_settings(self):
        """ Test editing a backup job with valid settings. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }
        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200

    def test_edit_invalid_backup(self):
        """
        Test editing an invalid backup, or a backup job that doesn't exist.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }
        resp = self.app.post('/backups/edit/12345', data=data,
                             follow_redirects=True)
        assert resp.status_code == 404

    def test_edit_backup_with_missing_name_setting(self):
        """ Test editing a backup job with missing name setting. """
        
        data = {
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert 'This field is required' in resp.data

    def test_edit_backup_with_missing_server_setting(self):
        """ Test editing a backup job with missing server setting. """
        
        data = {
            'name': 'Teacher Backups',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert 'This field is required' in resp.data

    def test_edit_backup_with_missing_port_setting(self):
        """ Test editing a backup job with missing port setting. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert 'This field is required' in resp.data

    def test_edit_backup_with_missing_protocol_setting(self):
        """ Test editing a backup job with missing protocol setting. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Not a valid choice' in resp.data

    def test_edit_backup_with_missing_start_time_setting(self):
        """
        Test editing a backup job with missing start_time setting.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Not a valid choice' in resp.data

    def test_edit_backup_with_missing_start_day_setting(self):
        """
        Test editing a backup job with missing start_time setting.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Not a valid choice' in resp.data

    def test_edit_backup_with_missing_interval_setting(self):
        """ Test editing a backup job with missing interval setting. """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'retention': 14,
        }

        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Not a valid choice' in resp.data

    def test_edit_backup_with_name_length_below_minimum(self):
        """
        Test editing a backup job with name length below the minimum.
        """
        
        data = {
            'name': '',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert 'This field is required.' in resp.data

    def test_edit_backup_with_name_length_above_maximum(self):
        """
        Test editing a backup job with name length above the maximum.
        """
        
        data = {
            'name': 'X'*141,
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }

        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Field must be between 1 and 140 characters long.' in resp.data

    def test_edit_backup_with_port_number_below_minimum(self):
        """
        Test editing a backup job with a port number below the minimum
        allowed value.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 0,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }
        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert 'This field is required' in resp.data

    def test_edit_backup_with_port_number_above_maximum(self):
        """
        Test editing a backup job with a port number above the maximum
        allowed value.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 65537,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 1,
            'retention': 14,
        }
        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Number must be between 1 and 65536.' in resp.data

    def test_edit_backup_with_interval_below_minimum(self):
        """
        Test editing a backup job with an interval below the minimum
        allowed value.
        """
        
        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 0,
            'retention': 14,
        }

        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Not a valid choice' in resp.data

    def test_edit_backup_with_interval_above_maximum(self):
        """
        Test editing a backup job with an interval above the maximum
        value.
        """
        
        # There are 17531.6 hours in 2 years

        data = {
            'name': 'Teacher Backups',
            'server': '192.168.11.52',
            'port': 445,
            'protocol': 1,
            'location': '/teachers',
            'username': 'testuser',
            'password': 'testpass',
            'start_time': 1,
            'start_day': 1,
            'interval': 4,
            'retention': 14,
        }

        resp = self.app.post(self.edit_backup_url, data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Not a valid choice' in resp.data
    

class DeleteBackupTestCase(BaseAuthenticatedTestCase):
    """ Test deleting backup jobs. """

    def setUp(self):
        super(DeleteBackupTestCase, self).setUp()

        # New Backup object for each test
        self.new_backup = Backup(name='Teachers Backup', server='winshare01', 
                                 port=445, protocol=Backup.PROTOCOL.SMB,
                                 location='F:/teachers',
                                 username='testuser', password='password',
                                 start_time=1,
                                 start_day=Backup.DAY.SUNDAY,
                                 interval=24, retention=14)

        db.session.add(self.new_backup)
        db.session.commit()

        # URL for deleting the newly created Backup object
        self.delete_backup_url = "/backups/delete/{}".format(self.new_backup.id)

    def tearDown(self):
        super(DeleteBackupTestCase, self).tearDown()

        Backup.query.delete()
        db.session.commit()

    def test_delete_valid_backup(self):
        """ Test deleting a valid backup. """

        resp = self.app.get(self.delete_backup_url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Delete Forever' in resp.data

        resp = self.app.post(self.delete_backup_url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Backup job was deleted successfully.' in resp.data

        assert not Backup.query.count()

    def test_delete_invalid_backup(self):
        """ Test deleting an invalid backup. """

        assert Backup.query.count() == 1

        resp = self.app.get('/backups/delete/12345', follow_redirects=True)
        assert resp.status_code == 404

        resp = self.app.post('/backups/delete/12345', follow_redirects=True)
        assert resp.status_code == 404
        
        assert Backup.query.count() == 1


class DisableBackupTestCase(BaseAuthenticatedTestCase):
    """ Test disabling backup jobs. """

    def setUp(self):
        super(DisableBackupTestCase, self).setUp()

        # New Backup object for each test
        self.new_backup = Backup(name='Teachers Backup', server='winshare01', 
                                 port=445, protocol=Backup.PROTOCOL.SMB,
                                 location='F:/teachers',
                                 username='testuser', password='password',
                                 start_time=1,
                                 start_day=Backup.DAY.SUNDAY,
                                 interval=24, retention=14)

        db.session.add(self.new_backup)
        db.session.commit()

        # URL for disabling the newly created Backup object
        self.disable_backup_url = "/backups/disable/{}".format(self.new_backup.id)

    def tearDown(self):
        super(DisableBackupTestCase, self).tearDown()

        Backup.query.delete()
        db.session.commit()

    def test_disable_valid_backup(self):
        """ Test disabling a valid backup. """

        assert Backup.query.filter(Backup.id==self.new_backup.id).first().enabled

        resp = self.app.get(self.disable_backup_url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Disable Backup' in resp.data

        resp = self.app.post(self.disable_backup_url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Backup job was disabled successfully.' in resp.data

        assert not Backup.query.filter(Backup.id==self.new_backup.id).first().enabled

    def test_disabling_invalid_backup(self):
        """ Test disabling an invalid backup. """

        assert Backup.query.count() == 1

        resp = self.app.get('/backups/disable/12345', follow_redirects=True)
        assert resp.status_code == 404

        resp = self.app.post('/backups/disable/12345', follow_redirects=True)
        assert resp.status_code == 404
        
        assert Backup.query.count() == 1


class EnableBackupTestCase(BaseAuthenticatedTestCase):
    """ Test enabling backup jobs. """

    def setUp(self):
        super(EnableBackupTestCase, self).setUp()

        # New Backup object for each test
        self.new_backup = Backup(name='Teachers Backup', server='winshare01', 
                                 port=445, protocol=Backup.PROTOCOL.SMB,
                                 location='F:/teachers',
                                 username='testuser', password='password',
                                 start_time=1,
                                 start_day=Backup.DAY.SUNDAY,
                                 interval=24, retention=14)
        self.new_backup.enabled = False

        db.session.add(self.new_backup)
        db.session.commit()

        # URL for disabling the newly created Backup object
        self.enable_backup_url = "/backups/enable/{}".format(self.new_backup.id)

    def tearDown(self):
        super(EnableBackupTestCase, self).tearDown()

        Backup.query.delete()
        db.session.commit()

    def test_enable_valid_backup(self):
        """ Test enabling a valid backup. """

        assert not Backup.query.filter(Backup.id==self.new_backup.id).first().enabled

        resp = self.app.get(self.enable_backup_url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Enable Backup' in resp.data

        resp = self.app.post(self.enable_backup_url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Backup job was enabled successfully.' in resp.data

        assert Backup.query.filter(Backup.id==self.new_backup.id).first().enabled

    def test_disabling_invalid_backup(self):
        """ Test disabling an invalid backup. """

        resp = self.app.get('/backups/enable/12345', follow_redirects=True)
        assert resp.status_code == 404

        resp = self.app.post('/backups/enable/12345', follow_redirects=True)
        assert resp.status_code == 404
        

class StartBackupTestCase(BaseAuthenticatedTestCase):
    """ Test starting backup jobs. """

    def setUp(self):
        super(StartBackupTestCase, self).setUp()

        # New Backup object for each test
        self.new_backup = Backup(name='Teachers Backup', server='winshare01', 
                                 port=445, protocol=Backup.PROTOCOL.SMB,
                                 location='F:/teachers',
                                 username='testuser', password='password',
                                 start_time=1,
                                 start_day=Backup.DAY.SUNDAY,
                                 interval=24, retention=14)
        self.new_backup.enabled = True

        db.session.add(self.new_backup)
        db.session.commit()

        # URL for disabling the newly created Backup object
        self.start_backup_url = "/backups/start/{}".format(self.new_backup.id)

    def tearDown(self):
        super(StartBackupTestCase, self).tearDown()

        Backup.query.delete()
        db.session.commit()

    def test_start_valid_backup(self):
        """ Test enabling a valid backup. """

        assert not Backup.query.filter(Backup.id==self.new_backup.id).first()\
            .should_start

        resp = self.app.get(self.start_backup_url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Start Backup' in resp.data

        resp = self.app.post(self.start_backup_url, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Backup job was scheduled to start.' in resp.data

        assert Backup.query.filter(Backup.id==self.new_backup.id).first()\
            .should_start

    def test_start_invalid_backup(self):
        """ Test enabling an invalid backup. """
        resp = self.app.get('/backups/start/12345', follow_redirects=True)
        assert resp.status_code == 404

        resp = self.app.post('/backups/start/12345', follow_redirects=True)
        assert resp.status_code == 404


class ListBackupTestCase(BaseAuthenticatedTestCase):
    """ Test listing backup jobs. """

    def setUp(self):
        super(ListBackupTestCase, self).setUp()

    def tearDown(self):
        super(ListBackupTestCase, self).tearDown()

        Backup.query.delete()
        db.session.commit()

    def test_view_backups_list(self):
        """ Test viewing the list of all backups. """

        # Create 3 backups
        new_backup_1 = Backup(name='Teachers Backup', server='winshare01', 
                              port=445, protocol=Backup.PROTOCOL.SMB,
                              location='F:/teachers',
                              username='testuser', password='password',
                              start_time=1, 
                              start_day=Backup.DAY.SUNDAY, interval=24,
                              retention=14)
        db.session.add(new_backup_1)

        new_backup_2 = Backup(name='Students Backup', server='winshare01', 
                              port=445, protocol=Backup.PROTOCOL.SMB,
                              location='F:/students',
                              username='testuser', password='password',
                              start_time=1,
                              start_day=Backup.DAY.SUNDAY, interval=24,
                              retention=14)
        db.session.add(new_backup_2)

        new_backup_3 = Backup(name='Admin Backup', server='winshare01', 
                              port=445, protocol=Backup.PROTOCOL.SMB,
                              location='F:/admin',
                              username='testuser', password='password',
                              start_time=1,
                              start_day=Backup.DAY.SUNDAY, interval=24,
                              retention=14)
        db.session.add(new_backup_3)

        # Save changes to the database
        db.session.commit()

        resp = self.app.get('/backups', follow_redirects=True)
        assert resp.status_code == 200

        for backup in Backup.query.all():
            assert backup.name in resp.data
            assert backup.location in resp.data

    def test_view_backups_list_empty(self):
        """ Test viewing the list of all backups, although it is empty. """

        resp = self.app.get('/backups', follow_redirects=True)
        assert resp.status_code == 200
        assert 'To get started, schedule a backup job.' in resp.data


class EditAccountTestCase(BaseAuthenticatedTestCase):
    """ Test editing a user account. """

    def test_edit_account_password(self):
        """ Test editing an account with matching passwords. """
        
        data = {
            'email': 'luke@skywalker.com',
            'password': 'testpassword',
            'repeat_password': 'testpassword',
        }
        resp = self.app.post('/account/edit', data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'Your account was saved successfully.' in resp.data

        # Attempt login with new credentials
        self.logout()
        self.login('luke@skywalker.com', 'testpassword')
        assert resp.status_code == 200
        assert 'Invalid Login' not in resp.data

    def test_edit_password_no_match(self):
        """
        Test editing an account without matching passwords.
        
        The password should not change.
        """
        
        data = {
            'email': 'luke@skywalker.com',
            'password': 'testpassword',
            'repeat_password': 'prowssaptset',
        }
        resp = self.app.post('/account/edit', data=data,
                             follow_redirects=True)
        assert resp.status_code == 200
        assert 'Passwords do not match.' in resp.data

        # Attempt login with old credentials
        self.logout()
        self.login('vader@deathstar.com', 'noarms')
        assert resp.status_code == 200
        assert 'Invalid Login' not in resp.data


if __name__ == '__main__':
    unittest.main()
