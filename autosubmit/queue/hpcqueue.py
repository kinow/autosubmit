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


class HPCQueue:
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
        self._serial_queue = None
        self._ssh_config = None
        self._user_config_file = None
        self._host_config = None
        self._host_config_id = None

    @property
    def header(self):
        return self._header

    def connect(self):
        try:
            self._ssh = paramiko.SSHClient()
            self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._ssh_config = paramiko.SSHConfig()
            self._user_config_file = os.path.expanduser("~/.ssh/config")
            if os.path.exists(self._user_config_file):
                with open(self._user_config_file) as f:
                    self._ssh_config.parse(f)
            self._host_config = self._ssh_config.lookup(self._host)
            if 'identityfile' in self._host_config:
                self._host_config_id = self._host_config['identityfile']

            self._ssh.connect(self._host_config['hostname'], 22, username=self._host_config['user'],
                              key_filename=self._host_config_id)
            return True
        except BaseException as e:
            Log.error('Can not create ssh connection to {0}: {1}', self._host, e.message)
            return False

    def send_command(self, command):
        if self._ssh is None:
            if not self.connect():
                return None
        try:
            stdin, stdout, stderr = self._ssh.exec_command(command)
            stderr_readlines = stderr.readlines()
            if len(stderr_readlines) > 0:
                Log.warning('Command {0} in {1} warning: {2}', command, self._host, stderr_readlines)
            self._ssh_output = stdout.read().rstrip()
            if stdout.channel.recv_exit_status() == 0:
                Log.debug('Command {0} in {1} successful with out message: {2}', command, self._host, self._ssh_output)
                return True
            else:
                Log.error('Command {0} in {1} failed with error message: {2}', command, self._host, stderr_readlines)
                return False
        except BaseException as e:
            Log.error('Can not send command {0} to {1}: {2}', command, self._host, e.message)
            return False

    def send_file(self, local_path, root_path):
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
        Log.debug('Output {0}', self._ssh_output)
        return self._ssh_output

    def close_connection(self):
        if self._ssh is None:
            return
        self._ssh.close()

    def get_serial_queue(self):
        if self._serial_queue is None:
            return self
        else:
            return self._serial_queue

    def set_serial_queue(self, value):
        self._serial_queue = value

    def cancel_job(self, job_id):
        Log.debug(self.cancel_cmd + ' ' + str(job_id))
        self.send_command(self.cancel_cmd + ' ' + str(job_id))

    def check_job(self, job_id):
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
        checkhost_cmd = self.get_checkhost_cmd()
        if not self.send_command(checkhost_cmd):
            self.connect()
            if not self.send_command(checkhost_cmd):
                Log.debug('The host ' + self._host + ' is down')
                return False
        Log.debug('The host ' + self._host + ' is up')
        return True

    def check_remote_log_dir(self):
        if self.send_command(self.get_mkdir_cmd()):
            Log.debug('{0} has been created on {1} .', self.remote_log_dir, self._host)
        else:
            Log.error('Could not create the DIR {0} on HPC {1}'.format(self.remote_log_dir, self._host))

    def send_script(self, job_script):
        if self.send_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.expid, 'tmp', str(job_script)),
                          os.path.join(self.remote_log_dir, str(job_script))):
            Log.debug('The script {0} has been sent'.format(job_script))
        else:
            Log.error('The script {0} has not been sent'.format(job_script))

    def get_completed_files(self, jobname):

        filename = jobname + '_COMPLETED'
        completed_local_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.expid, BasicConfig.LOCAL_TMP_DIR, filename)
        if os.path.exists(completed_local_path):
            os.remove(completed_local_path)
        completed_remote_path = os.path.join(self.remote_log_dir, filename)
        if self.get_file(completed_remote_path, completed_local_path):
            Log.debug('The COMPLETED files have been transfered')
            return True

        # wait five seconds to check get file
        sleep(5)
        if self.get_file(completed_remote_path, completed_local_path):
            Log.debug('The COMPLETED files have been transfered')
            return True
        Log.debug('Something did not work well when transferring the COMPLETED files')
        return False

    def submit_job(self, job_script):
        if self.send_command(self.get_submit_cmd(job_script)):
            job_id = self.get_submitted_job_id(self.get_ssh_output())
            Log.debug(job_id)
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
        self._host = new_host

    def set_scratch(self, new_scratch):
        self.scratch = new_scratch

    def set_project(self, new_project):
        self.project = new_project

    def set_user(self, new_user):
        self.user = new_user

    def set_remote_log_dir(self, new_remote_log_dir):
        self.remote_log_dir = new_remote_log_dir

    def get_checkhost_cmd(self):
        raise NotImplementedError

    def get_mkdir_cmd(self):
        raise NotImplementedError

    def parse_job_output(self, output):
        raise NotImplementedError

    def jobs_in_queue(self):
        raise NotImplementedError

    def get_submitted_job_id(self, output):
        raise NotImplementedError

    def get_header(self, job):
        if job.processors > 1:
            return self.header.PARALLEL
        else:
            return self.header.SERIAL

    def get_checkjob_cmd(self, job_id):
        raise NotImplementedError

    def get_submit_cmd(self, job_script):
        raise NotImplementedError

    def get_shcall(self, job_script):
        return 'nohup /bin/sh {0} > {0}.out 2> {0}.err & echo $!'.format(os.path.join(self.remote_log_dir,
                                                                                            job_script))

    @staticmethod
    def get_pscall(job_id):
        return 'nohup kill -0 {0}; echo $?'.format(job_id)

    @staticmethod
    def get_qstatjob(job_id):
        return '''if [[ $(qstat | grep {0}) != '' ]];
        then echo $(qstat | grep {0} | awk '{{print $5}}' | head -n 1); else echo 'c'; fi'''.format(job_id)