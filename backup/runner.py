import time

import sys
sys.path.append("..")

from app.models import Backup
from backup import BackupJob, RdiffBackupWrapper
from fs_mount import CIFSMountFS


def run():
    """ Runs all backup jobs. """
    while True:
        try:
            backups = Backup.query.all()
        except:
            time.sleep(10)
            continue

        for backup in backups:
            if backup.should_run:
                print("Running backup ID: {}".format(backup.id))
                job = BackupJob(backup=backup, mount_fs=CIFSMountFS,
                                backup_wrapper=RdiffBackupWrapper)
                job.run()

        time.sleep(10)

run()
