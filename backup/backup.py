import logging
import os
import random
import string

import envoy

import sys
sys.path.append("..")

from app import db

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


BACKUPS_DIR = '/var/backups'


class Job(object):
    """
    Provides a file system mount for a job that requires a connection to
    a remote file system.
    """

    def __init__(self, backup, mount_fs, backup_wrapper):
        """
        backup (Backup object) - Backup object containing server credentials
        mount_fs (AbstractMountFS type) - FS to mount
        backup_wrapper (RdiffBackupWrapper) - rdiff-backup wrapper to use
        """
        self.backup = backup

        # Setup temp space for the job
        tmp_name = ''.join(random.choice(string.ascii_lowercase) \
            for _ in range(12))
        self.temp_dir = os.path.join('/tmp', tmp_name)

        # Mount the FS needed for hte job
        self.fs = mount_fs(username=self.backup.username,
                           password=self.backup.password,
                           remote_addr=self.backup.server,
                           remote_port=self.backup.port,
                           remote_path=self.backup.location,
                           local_path=self.temp_dir)
        self.fs.mount()

        # Get backup directory of the backup job
        self.local_backup_path = os.path.join(BACKUPS_DIR,
                                              str(self.backup.id))

        # Create temp folders if they don't exist
        if not os.exists(BACKUPS_DIR):
            os.makedirs(BACKUPS_DIR)
        if not os.exists(self.local_backup_path):
            os.makedirs(self.local_backup_path)

        # Create a new backup_job object
        self.backup_job = backup_wrapper(remote_dir=self.temp_dir,
                                         backup_dir=self.local_backup_path)
        
    def done(self):
        self.backup.finished()
        self.fs.unmount()
        os.removedirs(self.temp_dir)


class BackupJob(Job):
    def run(self):
        self.backup.started()
        try:
            self.backup_job.backup()
        except Exception as e:
            self.backup.failed(e)
        else:
            self.done()
        db.session.commit()


class RestoreJob(Job):
    def run(self, path, time_format):
        raise NotImplementedError("Run the restore job here.")
        self.done()


class RdiffBackupWrapper(object):
    """
    RdiffBackupWrapper provides a wrapper around rdiff-backup
    """

    def __init__(self, remote_dir, backup_dir):
        """
        remote_dir (str) - Remote directory to backup (mounted locally)
        backup_dir (str) - Destination directory to store backups
        """

        self.remote_dir = remote_dir
        self.backup_dir = backup_dir

    def backup(self):
        """ Backup the remote location. """

        template = "rdiff-backup {remote_dir} {backup_dir}"

        arguments = {
            'remote_dir': self.remote_dir,
            'backup_dir': self.backup_dir
        }

        command = template.format(**arguments)

        # Timeout of 7 days
        r = envoy.run(command, timeout=604800)

        LOGGER.debug("Backup command: {}".format(command))
        LOGGER.debug("Backup command stdout: {}".format(r.std_out))
        if r.std_err:
            raise RdiffBackupException(r.std_err)
        
        LOGGER.info("Backup: Backed up {} to {} successfully."\
            .format(self.remote_dir, self.backup_dir))

    def restore(self, path='/', time_format="1D"):
        """
        Restore a path, recursively to the remote location.
        
        path (str) - Path to restore
        time_format (str) - Time format passed into rdiff-backup to specify
            version of backup to restore.
        """

        template = "rdiff-backup -r {time_format} {src} {dest}"

        arguments = {
            'time_format': time_format,
            'src': os.path.join(self.backup_dir, path),
            'dest': os.path.join(self.remote_dir, path),
        }

        command = template.format(**arguments)

        # Timeout of 4 days
        r = envoy.run(command, timeout=345600)

        LOGGER.debug("Restore command: {}".format(command))
        LOGGER.debug("Restore command stdout: {}".format(r.std_out))
        if r.std_err:
            raise RdiffRestoreException(r.std_err)
        
        LOGGER.info("Restore: Restored (time: {}) {} to {} successfully."\
            .format(time_format, arguments['src'], arguments['dest']))


class RdiffBackupException(Exception):
    pass


class RdiffRestoreException(Exception):
    pass
