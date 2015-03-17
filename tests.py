import os
import random
import string
import tempfile
import unittest

from app import app, db
from app.models import Bark, Friendship, User
from flask.ext.bcrypt import Bcrypt
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


class BaseLoginTestCase(BaseTestCase):
    """
    Abstract test case for login testing.
    """
    def __init__(self, *args, **kwargs):
        super(BaseLoginTestCase, self).__init__(*args, **kwargs)

    def login(self, email, password):
        """ Login to the app. """
        return self.app.post('/login', data={'email': email,
                                             'password': password},
                             follow_redirects=True)

    def logout(self):
        """ Logout from the app. """
        return self.app.get('/logout', follow_redirects=True) 
    
    def forgotPassword(self, email):
        """ Forgot password - enter email. """
        return self.app.post('/forgotPassword', data={'email': email},
                             follow_redirects=True)
                             
    def resetPassword(self, email, securityAnswer1, securityAnswer2,
                      securityAnswer3, password, password2):
        """ Reset Password - Answer Security Questions. """
        self.forgotPassword(email)

        reset_data = {'securityAnswer1': securityAnswer1,
                      'securityAnswer2': securityAnswer2,
        	      'securityAnswer3': securityAnswer3,
        	      'password': password,
                      'password_match': password}

        return self.app.post('/resetPassword', data=reset_data,
                             follow_redirects=True)

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
        self.login('vader@deathstar.com', 'noarms')

    def tearDown(self):
        # Delete all barks
        Bark.query.delete()
        # Delete all friendships
        Friendship.query.delete()

        db.session.commit()

        super(BaseAuthenticatedTestCase, self).setUp()


class AuthenticatedViewTestCase(BaseAuthenticatedTestCase):
    """
    Tests related to misc actions when the user is logged in.
    """
    def test_login_page_already_authenticated(self):
        """ Test viewing the login page while authenticated. """
        response = self.app.get('/login', follow_redirects=True)
        # The user is redirected elsewhere
        assert 'Log In - dogpound' not in response.data

    def test_register_page_already_authenticated(self):
        """ Test viewing the registration page while authenticated. """
        response = self.app.get('/registration', follow_redirects=True)
        # The user is redirected elsewhere
        assert 'Log In - dogpound' not in response.data


class UnauthenticatedViewTestCase(BaseTestCase):
    """
    Tests related to checking that unauthenticated users cannot access
    protected resources without logging in first.
    """
    def test_stream_view(self):
        """ Test accessing the stream view without being logged in. """
        response = self.app.get('/index', follow_redirects=True)
        assert 'Log In - dogpound' in response.data


class LoginTestCase(BaseLoginTestCase):
    """
    Tests related to logging in and logging out.
    """
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
        assert 'Home - dogpound' in response.data


class BaseRegistrationTestCase(BaseLoginTestCase):
    def register(self, firstName, lastName, email, password, password2, 
    		 securityQuestion1, securityQuestion2, securityQuestion3, 
    		 securityAnswer1, securityAnswer2, securityAnswer3):
        """ Register user. """
        registration_data = {
            'firstName': firstName,
            'lastName': lastName,
            'email': email,
            'password': password,
            'password_match': password2,
            'securityQuestion1': securityQuestion1,
            'securityQuestion2': securityQuestion2,
            'securityQuestion3': securityQuestion3,
            'securityAnswer1': securityAnswer1,
            'securityAnswer2': securityAnswer2,
            'securityAnswer3': securityAnswer3
        }

        return self.app.post('/registration', data=registration_data,
                             follow_redirects=True)

    def tearDown(self):
        # Delete the successfully registrated user.
        created_user = User.query.filter(User.email=='test@email.com').first()
        if created_user is not None:
            db.session.delete(created_user)
            db.session.commit()

        super(BaseRegistrationTestCase, self).tearDown()


class RegistrationTestCase(BaseRegistrationTestCase):
    """
    Tests related to Registration.
    """
    def test_valid_registration(self):
        """ Test a valid registration. """
        response = self.register('TestFirst', 'TestLast', 'test@email.com',
                                 'test', 'test',
        	                 'What was your first pet\'s name?',
                                 'spike', 'Favorite Food?', 'Pizza',
                                 'School Name?', 'IUPUI')
        assert 'Successful Registration!' in response.data
        login_response = self.login('test@email.com', 'test')
        assert 'Home - dogpound' in login_response.data

    def test_blank_firstName(self):
        """ Test a blank first name with all others valid. """
        response = self.register('', 'TestLast', 'test@email.com', 'test', 'test', 
        	'What was your first pet\'s name?', 'spike', 'Favorite Food?', 'Pizza', 'School Name?', 'IUPUI')
        assert 'This field is required' in response.data
        
    def test_blank_lastName(self):
        """ Test a blank last name with all others valid. """
        response = self.register('TestFirst', '', 'test@email.com', 'test', 'test', 
        	'What was your first pet\'s name?', 'spike', 'Favorite Food?', 'Pizza', 'School Name?', 'IUPUI')
        assert 'This field is required' in response.data
    
	def test_blank_email(self):
		""" Test a blank email with all others valid. """
        response = self.register('TestFirst', 'TestLast', '', 'test', 'test', 
        	'What was your first pet\'s name?', 'spike', 'Favorite Food?', 'Pizza', 'School Name?', 'IUPUI')
        assert 'This field is required' in response.data
     
    def test_blank_password1(self):
        """ Test a blank password1 with all others valid. """
        response = self.register('TestFirst', 'TestLast', 'test@email.com', '', 'test', 
        	'What was your first pet\'s name?', 'spike', 'Favorite Food?', 'Pizza', 'School Name?', 'IUPUI')
        assert 'This field is required' in response.data
        
    def test_blank_password2(self):
        """ Test a blank retyped password with all others valid. """
        response = self.register('TestFirst', 'TestLast', 'test@email.com', 'test', '', 
        	'What was your first pet\'s name?', 'spike', 'Favorite Food?', 'Pizza', 'School Name?', 'IUPUI')
        assert 'This field is required' in response.data
    
    def test_blank_securityQuestion1(self):
        """ Test a blank security question 1 with all others valid. """
        response = self.register('TestFirst', 'TestLast', 'test@email.com', 'test', 'test', 
        	'', 'spike', 'Favorite Food?', 'Pizza', 'School Name?', 'IUPUI')
        assert 'This field is required' in response.data
        
    def test_blank_securityAnswer1(self):
        """ Test a blank security answer 1 with all others valid. """
        response = self.register('TestFirst', 'TestLast', 'test@email.com', 'test', 'test', 
        	'What was your first pet\'s name?', '', 'Favorite Food?', 'Pizza', 'School Name?', 'IUPUI')
        assert 'This field is required' in response.data   
        
    def test_blank_securityQuestion2(self):
        """ Test a blank security question 2 with all others valid. """
        response = self.register('TestFirst', 'TestLast', 'test@email.com', 'test', 'test', 
        	'What was your first pet\'s name?', 'spike', '', 'Pizza', 'School Name?', 'IUPUI')
        assert 'This field is required' in response.data   
        
    def test_blank_securityAnswer2(self):
        """ Test a blank security answer 2 with all others valid. """
        response = self.register('TestFirst', 'TestLast', 'test@email.com', 'test', 'test', 
        	'What was your first pet\'s name?', 'spike', 'Favorite Food?', '', 'School Name?', 'IUPUI')
        assert 'This field is required' in response.data   
        
    def test_blank_securityQuestion3(self):
        """ Test a blank security question 3 with all others valid. """
        response = self.register('TestFirst', 'TestLast', 'test@email.com', 'test', 'test', 
        	'What was your first pet\'s name?', 'spike', 'Favorite Food?', 'Pizza', '', 'IUPUI')
        assert 'This field is required' in response.data   
        
    def test_blank_securityAnswer3(self):
        """ Test a blank security answer 3 with all others valid. """
        response = self.register('TestFirst', 'TestLast', 'test@email.com', 'test', 'test', 
        	'What was your first pet\'s name?', 'spike', 'Favorite Food?', 'Pizza', 'School Name?', '')
        assert 'This field is required' in response.data


class ResetPasswordTestCase(BaseLoginTestCase):
    """
    Tests related to resetting password.
    """
    def test_valid_email(self):
        """ Test a valid email address. """
        response = self.forgotPassword('vader@deathstar.com')
        assert 'Reset Password - dogpound' in response.data
        
    def test_valid_email_with_valid_answers(self):
        """ Test invalid answers with a valid email address. """
        response = self.resetPassword(email='han@falcon.com', 
                                      securityAnswer1='Burgers', 
                                      securityAnswer2='Spot',
                                      securityAnswer3='1980',
                                      password='newpassword',
                                      password2='newpassword')
        assert 'Password reset! Please log in.' \
            in response.data

    def test_valid_email_with_invalid_answers(self):
        """ Test invalid answers with a valid email address. """
        response = self.resetPassword(email='vader@deathstar.com', 
                                      securityAnswer1='132', 
                                      securityAnswer2='answer',
                                      securityAnswer3='answer',
                                      password='password',
                                      password2='password')
        assert 'Answers to security questions incorrect. Please try again.' \
            in response.data

    def test_invalid_email(self):
        """ Test an invalid email address. """
        response = self.forgotPassword('invaliduser')
        assert 'Invalid User Email' in response.data

    def test_blank_email(self):
        """ Test a blank email address. """
        response = self.forgotPassword('')
        assert 'This field is required' in response.data

    def test_blank_answer1(self):
        """ Test a blank answer 1. """
        response = self.resetPassword('email', '', 'answer', 'answer', 'password', 'password')
        assert 'This field is required' in response.data
        
    def test_blank_answer2(self):
    	""" Test a blank answer 2. """
    	response = self.resetPassword('email', 'answer', '', 'answer', 'password', 'password')
    	assert 'This field is required' in response.data
    	
    def test_blank_answer3(self):
    	""" Test a blank answer 3. """
    	response = self.resetPassword('email', 'answer', 'answer', '', 'password', 'password')
    	assert 'This field is required' in response.data


class BaseBarkTestCase(BaseAuthenticatedTestCase):
    """
    Tests related to the stream view.
    """
    def create_bark(self, body):
        """ Create a new bark given a content body. """
        return self.app.post('/index', data={'barkBody': body},
                             follow_redirects=True)


class CreateBarkTestCase(BaseBarkTestCase):
    def test_create_single_bark(self):
        """ Test creation of a new bark. """
        body = random_string(15)
        self.create_bark(body)

        response = self.app.get('/index', follow_redirects=True)
        assert body in response.data

    def test_create_multiple_barks(self):
        """ Test creation of multiple barks. """
        amount = 10

        contents = [random_string(15) for x in range(amount)]
        for content in contents:
            self.create_bark(content)

        response = self.app.get('/index', follow_redirects=True)
        for content in contents:
            assert content in response.data


class ViewBarkTestCase(BaseBarkTestCase):
    def test_view_only_friends_barks(self):
        """ Test that the stream contains only friend's barks. """
        
        user1 = User.query.filter(User.email=='vader@deathstar.com').first()
        user2 = User.query.filter(User.email=='luke@rebelbase.com').first()
        user3 = User.query.filter(User.email=='marty@delorean.com').first()

        user1_pass = 'noarms'
        user2_pass = 'TwinSister'
        user3_pass = 'Jennifer'

        user1_content = "hello world"
        user2_content = "world hello"
        user3_content = "whats up?"

        # Add user2 to user1's friends
        friendship = Friendship()
        friendship.user_id = user1.id
        friendship.friend_id = user2.id
        db.session.add(friendship)
        db.session.commit()

        user1 = User.query.filter(User.email=='vader@deathstar.com').first()
        user2 = User.query.filter(User.email=='luke@rebelbase.com').first()
        user3 = User.query.filter(User.email=='marty@delorean.com').first()

        # Create barks from all 3 users
        self.logout()
        self.login(user1.email, user1_pass)
        self.create_bark(user1_content)
        self.logout()
        self.login(user2.email, user2_pass)
        self.create_bark(user2_content)
        self.logout()
        self.login(user3.email, user3_pass)
        self.create_bark(user3_content)
        self.logout()

        # View stream as user 1
        self.login(user1.email, user1_pass)
        response = self.app.get('/index', follow_redirects=True)

        assert user1_content in response.data
        assert user2_content in response.data
        assert user3_content not in response.data


class FollowUserTestCase(BaseAuthenticatedTestCase):
    """
    Tests related to the following other users.
    """
    def follow_user(self, email):
        """ Follow a user given an email address. """
        return self.app.post('/follow', data={'email': email},
                             follow_redirects=True)

    def test_follow_user(self):
        """ Test following a user. """
        response = self.follow_user('luke@rebelbase.com') 
        assert "You are now following luke@rebelbase.com" in response.data

    def test_follow_invalid_user(self):
        """ Test following an invalid user. """
        response = self.follow_user('abcdefg@googlecom') 
        assert "User with that email does not exist." in response.data

    def test_follow_user_already_followed(self):
        """ Test following a user that is already being followed. """
        self.follow_user('doc@delorean.com') 
        # Attempt following again.
        response = self.follow_user('doc@delorean.com') 
        assert "You are already following this user." in response.data


if __name__ == '__main__':
    unittest.main()
