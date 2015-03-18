import os
import tempfile
import unittest

from app import app, db
from app.models import User
from app.views import time_interval


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


class TimeIntervalTemplateFilterTestCase(BaseTestCase):
    """ 
    Test the template filter that calculates time human readable intervals
    based upon an hour input.

    Example #1:
        in: 8
        out: Every 8 Hours
    Example #2:
        in: 24
        out: Every day
    """

    def test_1_hour(self):
        assert time_interval(hours=1) == 'Every hour'

    def test_2_hours(self):
        assert time_interval(hours=2) == 'Every 2 hours'

    def test_1_day(self):
        assert time_interval(hours=24) == 'Every day'

    def test_2_days(self):
        assert time_interval(hours=48) == 'Every 2 days'

    def test_1_week(self):
        assert time_interval(hours=168) == 'Every week'

    def test_2_weeks(self):
        assert time_interval(hours=336) == 'Every 2 weeks'

    def test_1_month(self):
        assert time_interval(hours=730) == 'Every month'

    def test_2_months(self):
        assert time_interval(hours=1460) == 'Every 2 months'

    def test_1_year(self):
        assert time_interval(hours=8765) == 'Every year'

    def test_2_years(self):
        assert time_interval(hours=17531) == 'Every 2 years'


if __name__ == '__main__':
    unittest.main()
