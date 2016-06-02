from time import sleep

import os
import paramiko

from autosubmit.config.log import Log
from autosubmit.job.job_common import Status
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
        self._default_queue = None
        self.job_status = None
        self._ssh = None
        self._ssh_config = None
        self._ssh_output = None
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
            ftp.put(os.path.join(self.tmp_path, filename), os.path.join(self.get_files_path(), filename))
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

    def delete_file(self, filename):
        """
        Deletes a file from this platform

        :param filename: file name
        :type filename: str
        :return: True if succesful or file does no exists
        :rtype: bool
        """
        if self._ssh is None:
            if not self.connect():
                return None

        try:
            ftp = self._ssh.open_sftp()
            ftp.remove(filename)
            ftp.close()
            return True
        except BaseException as e:
            if not omit_error:
                Log.error('Can not remove file from {0} to {1}: {2}', remote_path, local_path, e.message)
            return False

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
        # TODO-R: Update docstring
        if self.send_command(self.get_submit_cmd(job_script)):
            job_id = self.get_submitted_job_id(self.get_ssh_output())
            Log.debug("Job ID: {0}", job_id)
            return int(job_id)
        else:
            return None

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

    def get_checkjob_cmd(self, job_id):
        """
        Returns command to check job status on remote platforms

        :param job_id: id of job to check
        :param job_id: int
        :return: command to check job status
        :rtype: str
        """
        raise NotImplementedError

    def send_command(self, command):
        """
        Sends given command to HPC

        :param command: command to send
        :type command: str
        :return: True if executed, False if failed
        :rtype: bool
        """
        if self._ssh is None:
            if not self.connect():
                return None
        try:
            stdin, stdout, stderr = self._ssh.exec_command(command)
            stderr_readlines = stderr.readlines()
            self._ssh_output = stdout.read().rstrip()
            if stdout.channel.recv_exit_status() == 0:
                if len(stderr_readlines) > 0:
                    Log.warning('Command {0} in {1} warning: {2}', command, self.host, '\n'.join(stderr_readlines))
                Log.debug('Command {0} in {1} successful with out message: {2}', command, self.host, self._ssh_output)
                return True
            else:
                Log.error('Command {0} in {1} failed with error message: {2}',
                          command, self.host, '\n'.join(stderr_readlines))
                return False
        except BaseException as e:
            Log.error('Can not send command {0} to {1}: {2}', command, self.host, e.message)
            return False

    def parse_job_output(self, output):
        """
        Parses check job command output so it can be interpreted by autosubmit

        :param output: output to parse
        :type output: str
        :return: job status
        :rtype: str
        """
        raise NotImplementedError

    def get_submit_cmd(self, job_script):
        """
        Get command to add job to scheduler

        :param job_script: path to job script
        :param job_script: str
        :return: command to submit job to platforms
        :rtype: str
        """
        raise NotImplementedError

    def get_ssh_output(self):
        """
        Gets output from last command executed

        :return: output from last command
        :rtype: str
        """
        Log.debug('Output {0}', self._ssh_output)
        return self._ssh_output

    def get_submitted_job_id(self, output):
        """
        Parses submit command output to extract job id
        :param output: output to parse
        :type output: str
        :return: job id
        :rtype: str
        """
        raise NotImplementedError


class ParamikoPlatformException(Exception):
    """
    Exception raised from HPC queues
    """

    def __init__(self, msg):
        self.message = msg
