import os
import random
import string
import tempfile
import unittest

from flask.ext.bcrypt import Bcrypt

from app import app, db
from app.models import User

bcrypt = Bcrypt(app)


def random_string(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))


class BaseTestCase(unittest.TestCase):
    """
    Abstract base test class for this app.
    """
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
    """
    Abstract test case for login testing.
    """
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
    """
    Base test case for testing authenticated views.
    """
    def setUp(self):
        super(BaseAuthenticatedTestCase, self).setUp()
        # Create a test user
        self.create_test_user('vader@deathstar.com', 'noarms')
        # Login as the test user
        self.login('vader@deathstar.com', 'noarms')


class AuthenticatedViewTestCase(BaseAuthenticatedTestCase):
    """
    Tests related to misc actions when the user is logged in.
    """
    def test_login_page_already_authenticated(self):
        """ Test viewing the login page while authenticated. """
        response = self.app.get('/login', follow_redirects=True)
        # The user is redirected elsewhere
        assert 'Backups | Dragon Backups Appliance' in response.data

    def test_index_page_already_authenticated(self):
        """ Test viewing the index page while authenticated. """
        response = self.app.get('/', follow_redirects=True)
        # The user is redirected elsewhere
        assert 'Backups | Dragon Backups Appliance' in response.data


class UnauthenticatedViewTestCase(BaseTestCase):
    """
    Tests related to checking that unauthenticated users cannot access
    protected resources without logging in first.
    """
    def test_stream_view(self):
        """ Test accessing the stream view without being logged in. """
        response = self.app.get('/home/backups', follow_redirects=True)
        assert 'Login | Dragon Backups Appliance' in response.data


class LoginTestCase(BaseLoginTestCase):
    """
    Tests related to logging in and logging out.
    """

    def setUp(self):
        super(LoginTestCase, self).setUp()
        # Create a test user
        self.create_test_user('vader@deathstar.com', 'noarms')

    def test_invalid_email(self):
        """ Test an invalid email address. """
        response = self.login('invaliduser', 'notfound')
        assert 'Invalid Login' in response.data

    def test_blank_email(self):
        """ Test a blank email address. """
        response = self.login('', 'notfound')
        assert 'This field is required' in response.data

    def test_invalid_password(self):
        """ Test an invalid password with a valid email. """
        response = self.login('vader@deathstar.com', 'default')
        assert 'Invalid Login' in response.data

    def test_blank_password(self):
        """ Test a blank password with a valid email. """
#         pw_hash = bcrypt.generate_password_hash('')
        response = self.login('vader@deathstar.com', '')
        assert 'This field is required' in response.data

    def test_valid_login(self):
        """ Test a valid email and a valid password. """

        response = self.login('vader@deathstar.com', 'noarms')
        assert 'Backups | Dragon Backups Appliance' in response.data


if __name__ == '__main__':
    unittest.main()
