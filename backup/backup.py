import logging
import os

import envoy

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


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

        # These should not be instantiated...
        self.mount_fs = mount_fs
        self.backup_wrapper = backup_wrapper

        raise NotImplementedError("FS should be instantiated.")
        raise NotImplementedError("Backup wrapper should be instantiated.")

    def done(self):
        raise NotImplementedError("FS should be unmounted.")


class BackupJob(Job):
    def run(self):
        raise NotImplementedError("Run the backup job here.")
        self.done()


class RestoreJob(Job):
    def run(self):
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

        # Timeout of 4 days
        r = envoy.run(command, timeout=345600)

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
