import os
import tempfile
import unittest

from flask.ext.bcrypt import Bcrypt

from app import app, db
from app.models import Backup

bcrypt = Bcrypt(app)


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


class BackupModelTestCase(BaseTestCase):
    """
    Test the Backup database model.
    """
    def test_backup_failure(self):
        b = Backup(name='Teachers Backup', server='winshare01', port=445,
                   protocol=Backup.PROTOCOL.SMB, location='F:/teachers',
                   username='testuser', password='testpassword',
                   start_time=1, start_day=Backup.DAY.SUNDAY, interval=24,
                   retention=14)
        b.failed("Something has gone wrong.")
        assert not b.last_backup
        assert b.status == Backup.STATUS.ERROR
        assert b.error_message == "Something has gone wrong."

    def test_backup_finish_job(self):
        b = Backup(name='Teachers Backup', server='winshare01', port=445,
                   protocol=Backup.PROTOCOL.SMB, location='F:/teachers',
                   username='testuser', password='testpassword',
                   start_time=1, start_day=Backup.DAY.SUNDAY, interval=24,
                   retention=14)
        b.finished()
        assert b.last_backup
        assert b.status == Backup.STATUS.FINISHED
        assert b.error_message == ''

    def test_backup_started(self):
        b = Backup(name='Teachers Backup', server='winshare01', port=445,
                   protocol=Backup.PROTOCOL.SMB, location='F:/teachers',
                   username='testuser', password='testpassword',
                   start_time=1, start_day=Backup.DAY.SUNDAY, interval=24,
                   retention=24)
        b.started()
        assert b.status == Backup.STATUS.RUNNING
        assert b.error_message == ''

    def test_backup_never_started(self):
        b = Backup(name='Teachers Backup', server='winshare01', port=445,
                   protocol=Backup.PROTOCOL.SMB, location='F:/teachers',
                   username='testuser', password='testpassword',
                   start_time=1, start_day=Backup.DAY.SUNDAY, interval=24,
                   retention=24)
        assert b.status == Backup.STATUS.NEVER_STARTED
        assert b.error_message == ''


if __name__ == '__main__':
    unittest.main()
