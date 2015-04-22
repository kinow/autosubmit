#!/usr/bin/env python

# Copyright 2014 Climate Forecasting Unit, IC3

# This file is part of Autosubmit.

# Autosubmit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Autosubmit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Autosubmit.  If not, see <http://www.gnu.org/licenses/>.


import os
import paramiko
from time import sleep
from sys import exit

from autosubmit.job.job_common import Status
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.config.log import Log


SLEEPING_TIME = 30


class HPCPlatform:
    """
    Base class to manage schedulers
    """
    def __init__(self):
        self._submit_cmd = None
        self.get_cmd = None
        self._checkjob_cmd = None
        self.job_status = None
        self.expid = None
        self.put_cmd = None
        self.mkdir_cmd = None
        self.cancel_cmd = None
        self._header = None
        self._default_queue = None
        self._serial_platform = None
        self._serial_queue = None
        self._ssh_config = None
        self._user_config_file = None
        self._host_config = None
        self._host_config_id = None

    @property
    def header(self):
        """
        Header to add to jobs for scheduler cofiguration

        :return: header
        :rtype: object
        """
        return self._header

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

            self._ssh.connect(self._host_config['hostname'], 22, username=self.user,
                              key_filename=self._host_config_id)
            return True
        except BaseException as e:
            Log.error('Can not create ssh connection to {0}: {1}', self._host, e.message)
            return False

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
                    Log.warning('Command {0} in {1} warning: {2}', command, self._host, '\n'.join(stderr_readlines))
                Log.debug('Command {0} in {1} successful with out message: {2}', command, self._host, self._ssh_output)
                return True
            else:
                Log.error('Command {0} in {1} failed with error message: {2}',
                          command, self._host, '\n'.join(stderr_readlines))
                return False
        except BaseException as e:
            Log.error('Can not send command {0} to {1}: {2}', command, self._host, e.message)
            return False

    def send_file(self, local_path, root_path):
        """
        Copies file in local_path to remote_path

        :param local_path: path to the local file to copy
        :type local_path: str
        :param root_path: path to the remote file to create
        :type root_path: str
        :return: True if succesful, False if failed
        :rtype: bool
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

    def get_file(self, remote_path, local_path):
        """
        Copies file in remote_path to local_path

        :param remote_path: path to the remote file to copy
        :type remote_path: str
        :param local_path: path to the local file to create
        :type local_path: str
        :return: True if succesful, False if failed
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
            Log.error('Can not get file from {0} to {1}: {2}', remote_path, local_path, e.message)
            return False

    def get_ssh_output(self):
        """
        Gets output from last command executed

        :return: output from last command
        :rtype: str
        """
        Log.debug('Output {0}', self._ssh_output)
        return self._ssh_output

    def close_connection(self):
        """
        Closes ssh connection to host
        """
        if self._ssh is None:
            return
        self._ssh.close()

    def get_queue(self):
        """
        Returns default queue for current host. If not configured, returns empty string

        :return: default queue for host
        :rtype: str
        """
        if self._default_queue is None:
            return ''
        return self._default_queue

    def set_queue(self, value):
        """
        Configures default queue for current host.

        :param value: serial queue for host
        :type value: str
        """
        self._default_queue = value

    def get_serial_queue(self):
        """
        Returns serial queue for current host. If not configured, returns empty string

        :return: serial queue for host
        :rtype: str
        """
        if self._serial_queue is None:
            return self.get_queue()
        return self._serial_queue

    def set_serial_queue(self, value):
        """
        Configures serial queue for current host.

        :param value: serial queue for host
        :type value: str
        """
        self._serial_queue = value

    def get_serial_platform(self):
        """
        Returns serial platforms for current host. If not configured, returns self

        :return: serial platforms for host
        :rtype: HPCPlatform
        """
        if self._serial_platform is None:
            return self
        else:
            return self._serial_platform

    def set_serial_platform(self, value):
        """
        Configures serial platforms for current host.

        :param value: serial platforms for host
        :type value: HPCPlatform
        """
        self._serial_platform = value

    def cancel_job(self, job_id):
        """
        Cancels job

        :param job_id: job to cancel
        :type job_id: int
        """
        Log.debug(self.cancel_cmd + ' ' + str(job_id))
        self.send_command(self.cancel_cmd + ' ' + str(job_id))

    def check_job(self, job_id):
        """
        Checks job statuts

        :param job_id: job to check
        :type job_id: int
        :return: current job status
        :rtype: Status
        """
        job_status = Status.UNKNOWN

        if type(job_id) is not int:
            # URi: logger
            Log.error('check_job() The job id ({0}) is not an integer.', job_id)
            # URi: value ?
            return job_status

        retry = 10
        while not self.send_command(self.get_checkjob_cmd(job_id)) and retry > 0:
            retry -= 1
            Log.warning('Retrying check job command: {0}', self.get_checkjob_cmd(job_id))
            Log.error('Can not get job status for job id ({0}), retrying in 10 sec', job_id)
            sleep(10)

        if retry > 0:
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

    def check_host(self):
        """
        Checks host availability

        :return: True if host is available, False otherwise
        :rtype: bool
        """
        checkhost_cmd = self.get_checkhost_cmd()
        if not self.send_command(checkhost_cmd):
            self.connect()
            if not self.send_command(checkhost_cmd):
                Log.debug('The host ' + self._host + ' is down')
                return False
        Log.debug('The host ' + self._host + ' is up')
        return True

    def check_remote_log_dir(self):
        """
        Creates log dir on remote host
        """
        if self.send_command(self.get_mkdir_cmd()):
            Log.debug('{0} has been created on {1} .', self.remote_log_dir, self._host)
        else:
            Log.error('Could not create the DIR {0} on HPC {1}'.format(self.remote_log_dir, self._host))

    def send_script(self, job_script):
        """
        Send a script to remote host

        :param job_script: name of script to send
        :type job_script: str
        """
        if self.send_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.expid, 'tmp', str(job_script)),
                          os.path.join(self.remote_log_dir, str(job_script))):
            Log.debug('The script {0} has been sent'.format(job_script))
        else:
            Log.error('The script {0} has not been sent'.format(job_script))

    def get_completed_files(self, jobname, retries=1):
        """
        Copies *COMPLETED* files from remote to local

        :param jobname: name of job to check
        :type jobname: str
        :return: True if succesful, False otherwise
        :rtype: bool
        """
        filename = jobname + '_COMPLETED'
        completed_local_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.expid, BasicConfig.LOCAL_TMP_DIR, filename)
        if os.path.exists(completed_local_path):
            os.remove(completed_local_path)
        completed_remote_path = os.path.join(self.remote_log_dir, filename)
        if self.get_file(completed_remote_path, completed_local_path):
            Log.debug('The COMPLETED files have been transfered')
            return True

        while retries > 0:
            # wait five seconds to check get file
            sleep(5)
            if self.get_file(completed_remote_path, completed_local_path):
                Log.debug('The COMPLETED files have been transfered')
                return True
            retries -= 1

        Log.debug('Something did not work well when transferring the COMPLETED files')
        return False

    def submit_job(self, job_script):
        """
        Submits job to scheduler and returns job id

        :param job_script: script path
        :type job_script: str
        :return: job id
        :rtype: int
        """
        if self.send_command(self.get_submit_cmd(job_script)):
            job_id = self.get_submitted_job_id(self.get_ssh_output())
            Log.debug("Job ID: {0}", job_id)
            return int(job_id)
        else:
            return None

    # noinspection PyUnusedLocal
    def normal_stop(self, arg1, arg2):
        for job_id in self.jobs_in_queue():
            self.cancel_job(job_id)
        exit(0)

    def smart_stop(self):
        while self.jobs_in_queue():
            sleep(SLEEPING_TIME)
        exit(0)

    def set_host(self, new_host):
        """
        Sets host name
        :param new_host: host
        :type new_host: str
        """
        self._host = new_host

    def set_scratch(self, new_scratch):
        """
        Sets scracth directory name
        :param new_scratch: scratch path
        :type new_scratch: str
        """
        self.scratch = new_scratch

    def set_project(self, new_project):
        """
        Sets project name
        :param new_project: project
        :type new_project: str
        """
        self.project = new_project

    def set_budget(self, new_budget):
        """
        Sets budget
        :param new_budget: project
        :type new_budget: str
        """
        self.budget = new_budget

    def set_user(self, new_user):
        """
        Sets user name
        :param new_user: user
        :type new_user: str
        """
        self.user = new_user

    def set_remote_log_dir(self, new_remote_log_dir):
        """
        Sets remote directory for logs
        :param new_remote_log_dir: path to log directory
        :type new_remote_log_dir: str
        """
        self.remote_log_dir = new_remote_log_dir

    def get_checkhost_cmd(self):
        """
        Gets command to check platforms availability

        :return: command to check platforms availability
        :rtype: str
        """
        raise NotImplementedError

    def get_mkdir_cmd(self):
        """
        Gets command to create directories on HPC

        :return: command to create directories on HPC
        :rtype: str
        """
        raise NotImplementedError

    def parse_job_output(self, output):
        """
        Parses check job command output so it can be interpreted by autosubmit

        :param output: output to parse
        :type output: str
        :return: job status
        :rtype: str
        """
        raise NotImplementedError

    def jobs_in_queue(self):
        """
        Get jobs in platforms in this host

        :return: jobs in platforms
        :rtype: list
        """
        raise NotImplementedError

    def get_submitted_job_id(self, output):
        """
        Parses submit command output to extract job id
        :param output: output to parse
        :type output: str
        :return: job id
        :rtype: str
        """
        raise NotImplementedError

    def update_cmds(self):
        """
        Updates commands for platforms
        """
        raise NotImplementedError

    def get_remote_log_dir(self):
        """
        Gets remote directory for logs

        :return: log directory path
        :rtype: str
        """
        raise NotImplementedError

    # noinspection PyUnresolvedReferences
    def get_header(self, job):
        """
        Gets header to be used by the job

        :param job: job
        :type job: Job
        :return: header to use
        :rtype: str
        """
        if job.processors > 1:
            header = self.header.PARALLEL
        else:
            header = self.header.SERIAL

        header = header.replace('%QUEUE_DIRECTIVE%', self.header.get_queue_directive(job))
        return header

    def get_checkjob_cmd(self, job_id):
        """
        Returns command to check job status on remote platforms

        :param job_id: id of job to check
        :param job_id: int
        :return: command to check job status
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

    def get_shcall(self, job_script):
        """
        Gets execution command for given job

        :param job_script: script to run
        :type job_script: str
        :return: command to execute script
        :rtype: str
        """
        return 'nohup bash {0} > {0}.out 2> {0}.err & echo $!'.format(os.path.join(self.remote_log_dir,
                                                                                   job_script))

    @staticmethod
    def get_pscall(job_id):
        """
        Gets command to check if a job is running given process identifier

        :param job_id: process indentifier
        :type job_id: int
        :return: command to check job status script
        :rtype: str
        """
        return 'nohup kill -0 {0}; echo $?'.format(job_id)

    @staticmethod
    def get_qstatjob(job_id):
        """
        Gets qstat command for given job id

        :param job_id: job to check
        :type job_id: int
        :return: qstat command for job
        :rtype: str
        """
        return '''if [[ $(qstat | grep {0}) != '' ]];
        then echo $(qstat | grep {0} | awk '{{print $5}}' | head -n 1); else echo 'c'; fi'''.format(job_id)


class HPCPlatformException(Exception):
    """
    Exception raised from HPC queues
    """
    def __init__(self, msg):
        self.message = msg
