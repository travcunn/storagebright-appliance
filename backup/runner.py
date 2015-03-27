import sys
import time

from app.models import Backup
from backup.backup import BackupJob, RdiffBackupWrapper
from backup.fs_mount import CIFSMountFS


def run(backup_id):
    """ Runs backup jobs. """
    while True:
        try:
            backup = Backup.query.filter(Backup.id==backup_id).first()
        except:
            time.sleep(60)
            continue

        if backup.should_run:
            job = BackupJob(backup=backup, mount_fs=CIFSMountFS,
                            backup_wrapper=RdiffBackupWrapper)
            job.run()

        time.sleep(60)


backup_id = int(sys.argv[1])
run(backup_id=backup_id)
