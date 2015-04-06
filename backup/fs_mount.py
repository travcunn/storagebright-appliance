"""
This module should be run as root to allow the 'mount' command to work.
"""

import logging

import envoy
from fs.path import relpath


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


"""
Warning:
    The 'mount' command does not allow for mounting to directories that
    contain numbers. To be safe, only use alphabetic characters in local_path
    names.
"""


class AbstractMountFS(object):
    """
    AbstractMountFS for mounting remote file shares.
    """

    def mount(self):
        raise NotImplementedError

    def unmount(self):
        raise NotImplementedError


class CIFSMountFS(AbstractMountFS):
    """
    CIFSMountFS for mounting CIFS remote file shares.
    """

    def __init__(self, username, password, remote_addr, remote_port,
                 remote_path, local_path):
        super(CIFSMountFS, self).__init__()

        self.username = username
        self.password = password
        self.remote_addr = remote_addr
        self.remote_port = remote_port
        self.remote_path = relpath(remote_path)
        self.local_path = local_path

    def mount(self):
        """ Mounts the CIFS share at the specified local_path. """

        template = """mount -t cifs -o """ \
                   """'user={username},password={password}' """ \
                   """'//{remote_addr}:{remote_port}/{remote_path}' """ \
                   """'{local_path}'"""

        arguments = {
            'username': self.username,
            'password': self.password,
            'remote_addr': self.remote_addr,
            'remote_port': self.remote_port,
            'remote_path': self.remote_path,
            'local_path': self.local_path,
        }

        command = template.format(**arguments)

        r = envoy.run(command, timeout=30)

        LOGGER.debug("CIFS command: {}".format(command))
        LOGGER.debug("CIFS stdout: {}".format(r.std_out))
        if r.std_err:
            raise CIFSException(r.std_err)
        
        LOGGER.info("CIFS: Mounted {}/{} to {} successfully."\
            .format(self.remote_addr, self.remote_path, self.local_path))

    def unmount(self):
        """ Ummounts the CIFS share from the specified local_path. """
        
        template = """umount {local_path}"""

        arguments = {
            'local_path': self.local_path,
        }

        command = template.format(**arguments)

        r = envoy.run(command, timeout=30)

        LOGGER.debug("CIFS command: {}".format(command))
        LOGGER.debug("CIFS stdout: {}".format(r.std_out))
        if r.std_err:
            raise CIFSException(r.std_err)
        
        LOGGER.info("CIFS: Unmounted {}/{} from {} successfully."\
            .format(self.remote_addr, self.remote_path, self.local_path))


class CIFSException(Exception):
    pass
