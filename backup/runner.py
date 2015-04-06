import time

import sys
sys.path.append("..")

from app import db
from app.models import Backup
from backup import BackupJob, RdiffBackupWrapper
from fs_mount import CIFSMountFS


def run():
    """ Runs all backup jobs. """
    while True:
        db.session.expire_all()
        try:
            backups = Backup.query.all()
        except:
            time.sleep(1)
            continue

        for backup in backups:
            if backup.should_start:
                try:
                    job = BackupJob(backup=backup, mount_fs=CIFSMountFS,
                                    backup_wrapper=RdiffBackupWrapper)
                except Exception as e:
                    print(e)
                    backup.failed(e.message)
                    db.session.commit()
                else:
                    job.run()

        time.sleep(1)

run()
