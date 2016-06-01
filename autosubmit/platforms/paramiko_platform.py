import datetime
import subprocess
from time import sleep

import os
import paramiko

from autosubmit.config.log import Log
from autosubmit.date.chunk_date_lib import date2str
from autosubmit.job.job_common import Status, Type
from autosubmit.platforms.platform import Platform


class ParamikoPlatform(Platform):
    """
    Class to manage the connections to the different platforms with the Paramiko library.
    """

    def __init__(self, expid, name, config):
        """

        :param config:
        :param expid:
        :param name:
        """
        Platform.__init__(self, expid, name, config)
        self.expid = None
        self._default_queue = None
        self._ssh = None
        self._ssh_config = None
        self._user_config_file = None
        self._host_config = None
        self._host_config_id = None

    def connect(self):
        """
        Creates ssh connection to host

        :return: True if connection is created, False otherwise
        :rtype: bool
        """
        try:
            self._ssh = paramiko.SSHClient()
            self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._ssh_config = paramiko.SSHConfig()
            self._user_config_file = os.path.expanduser("~/.ssh/config")
            if os.path.exists(self._user_config_file):
                with open(self._user_config_file) as f:
                    # noinspection PyTypeChecker
                    self._ssh_config.parse(f)
            self._host_config = self._ssh_config.lookup(self._host)
            if 'identityfile' in self._host_config:
                self._host_config_id = self._host_config['identityfile']
            if 'proxycommand' in self._host_config:
                self._proxy = paramiko.ProxyCommand(self._host_config['proxycommand'])
                self._ssh.connect(self._host_config['hostname'], 22, username=self.user,
                                  key_filename=self._host_config_id, sock=self._proxy)
            else:
                self._ssh.connect(self._host_config['hostname'], 22, username=self.user,
                                  key_filename=self._host_config_id)
            return True
        except IOError as e:
            Log.error('Can not create ssh connection to {0}: {1}', self._host, e.strerror)
            return False

    def send_file(self, filename):
        """
        Sends a local file to the platform
        :param filename: name of the file to send
        :type filename: str
        """

        if self._ssh is None:
            if not self.connect():
                return None

        try:
            ftp = self._ssh.open_sftp()
            ftp.put(local_path, root_path)
            ftp.close()
            return True
        except BaseException as e:
            Log.error('Can not send file {0} to {1}: {2}', local_path, root_path, e.message)
            return False

    def get_file(self, filename, must_exist=True, omit_error=False):
        """
        Copies a file from the current platform to experiment's tmp folder

        :param omit_error:
        :param filename: file name
        :type filename: str
        :param must_exist: If True, raises an exception if file can not be copied
        :type must_exist: bool
        :return: True if file is copied succesfully, false otherwise
        :rtype: bool
        """
        if self._ssh is None:
            if not self.connect():
                return None

        try:
            ftp = self._ssh.open_sftp()
            ftp.get(remote_path, local_path)
            ftp.close()
            return True
        except BaseException as e:
            if not omit_error:
                Log.error('Can not get file from {0} to {1}: {2}', remote_path, local_path, e.message)
            return False

    def exists_file(self, filename):
        """
        Checks if a file exists on this platform

        :param filename: file name
        :type filename: str
        :return: True if it exists, False otherwise
        """
        # noinspection PyBroadException
        if not self.directory:
            try:
                if self.type == 'local':
                    # noinspection PyTypeChecker
                    self.directory = saga.filesystem.Directory("file://{0}".format(os.path.join(self.tmp_path,
                                                                                                'LOG_' + self.expid)))
                else:
                    # noinspection PyTypeChecker
                    self.directory = saga.filesystem.Directory("sftp://{0}{1}".format(self.host, self.get_files_path()))
            except:
                return False

        # noinspection PyBroadException
        try:
            self.directory.list(filename)
        except:
            return False

        return True

    def delete_file(self, filename):
        """
        Deletes a file from this platform

        :param filename: file name
        :type filename: str
        :return: True if succesful or file does no exists
        :rtype: bool
        """
        if self.type == 'ecaccess':
            try:
                subprocess.check_call(['ecaccess-file-delete',
                                       '{0}:{1}'.format(self.host, os.path.join(self.get_files_path(), filename))])
                return True
            except subprocess.CalledProcessError:
                return True

        if not self.exists_file(filename):
            return True

        try:
            if self.type == 'local':
                # noinspection PyTypeChecker
                out = saga.filesystem.File("file://{0}".format(os.path.join(self.tmp_path, 'LOG_' + self.expid,
                                                                            filename)))
            else:
                # noinspection PyTypeChecker
                out = saga.filesystem.File("sftp://{0}{1}".format(self.host, os.path.join(self.get_files_path(),
                                                                                          filename)))
            out.remove()
            out.close()
            return True
        except saga.DoesNotExist:
            return True

    def submit_job(self, job, scriptname):
        """
        Creates a saga job from a given job object.

        :param job: job object
        :type job: autosubmit.job.job.Job
        :param scriptname: job script's name
        :rtype scriptname: str
        :return: saga job object for the given job
        :rtype: saga.job.Job
        """

        saga_job = self.create_saga_job(job, scriptname)
        saga_job.run()
        return saga_job.id

    def check_job(self, jobid, default_status=Status.COMPLETED, retries=30):
        """
        Checks job running status

        :param retries: retries
        :param jobid: job id
        :type jobid: str
        :param default_status: status to assign if it can be retrieved from the platform
        :type default_status: autosubmit.job.job_common.Status
        :return: current job status
        :rtype: autosubmit.job.job_common.Status
        """
        job_status = Status.UNKNOWN

        if type(job_id) is not int:
            # URi: logger
            Log.error('check_job() The job id ({0}) is not an integer.', job_id)
            # URi: value ?
            return job_status

        while not self.send_command(self.get_checkjob_cmd(job_id)) and retries > 0:
            retries -= 1
            Log.warning('Retrying check job command: {0}', self.get_checkjob_cmd(job_id))
            Log.error('Can not get job status for job id ({0}), retrying in 10 sec', job_id)
            sleep(10)

        if retries > 0:
            Log.debug('Successful check job command: {0}', self.get_checkjob_cmd(job_id))
            job_status = self.parse_job_output(self.get_ssh_output())
            # URi: define status list in HPC Queue Class
            if job_status in self.job_status['COMPLETED'] or retry == 0:
                job_status = Status.COMPLETED
            elif job_status in self.job_status['RUNNING']:
                job_status = Status.RUNNING
            elif job_status in self.job_status['QUEUING']:
                job_status = Status.QUEUING
            elif job_status in self.job_status['FAILED']:
                job_status = Status.FAILED
            else:
                job_status = Status.UNKNOWN
        else:
            # BOUOUOUOU	NOT	GOOD!
            job_status = Status.UNKNOWN
            Log.error('check_job() The job id ({0}) status is {1}.', job_id, job_status)
        return job_status
