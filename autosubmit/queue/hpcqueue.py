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


from commands import getstatusoutput
import os
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

    @property
    def header(self):
        return self._header

    def cancel_job(self, job_id):
        Log.debug(self.cancel_cmd + ' ' + str(job_id))
        # noinspection PyUnusedLocal
        (status, output) = getstatusoutput(self.cancel_cmd + ' ' + str(job_id))

    def check_job(self, job_id):
        job_status = Status.UNKNOWN

        if type(job_id) is not int:
            # URi: logger
            Log.error('check_job() The job id (%s) is not an integer.' % job_id)
            # URi: value ?
            return job_status

        retry = 10
        (status, output) = getstatusoutput(self.get_checkjob_cmd(job_id))
        Log.debug(status)
        Log.debug(output)
        # retry infinitelly except if it was in the RUNNING state, because it can happen that we don't get a
        # COMPLETE status from autosubmit.queue due to the 5 min lifetime
        while status != 0 and retry > 0:
            # if(current_state == Status.RUNNING):
            retry -= 1
            Log.info('Can not get job status, retrying in 10 sec')
            (status, output) = getstatusoutput(self.get_checkjob_cmd(job_id))
            Log.debug(status)
            Log.debug(output)
            # URi: logger
            sleep(10)

        if status == 0:
            # URi: this command is specific of mn
            job_status = self.parse_job_output(output)
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
        return job_status

    def check_host(self):
        (status, output) = getstatusoutput(self.get_checkhost_cmd())
        if status == 0:
            Log.debug('The host ' + self._host + ' is up')
            return True
        else:
            Log.debug('The host ' + self._host + ' is down')
            return False

    def check_remote_log_dir(self):
        (status, output) = getstatusoutput(self.get_mkdir_cmd())
        Log.debug(self.mkdir_cmd)
        Log.debug(output)
        if status == 0:
            Log.debug('%s has been created on %s .' % (self.remote_log_dir, self._host))
        else:
            Log.error('Could not create the DIR on HPC')

    def send_script(self, job_script):
        (status, output) = getstatusoutput(self.put_cmd + ' ' + BasicConfig.LOCAL_ROOT_DIR + "/" + self.expid +
                                           '/tmp/' + str(job_script) + ' ' + self._host + ':' + self.remote_log_dir +
                                           "/" + str(job_script))
        Log.debug(self.put_cmd + ' ' + BasicConfig.LOCAL_ROOT_DIR + "/" + self.expid + '/tmp/' + str(
            job_script) + ' ' + self._host + ':' + self.remote_log_dir + "/" + str(job_script))
        if status == 0:
            Log.debug('The script has been sent')
        else:
            Log.error('The script has not been sent')

    def get_completed_files(self, jobname):
        # wait five seconds to check get file
        sleep(5)
        filename = jobname + '_COMPLETED'
        completed_local_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.expid, BasicConfig.LOCAL_TMP_DIR, filename)
        if os.path.exists(completed_local_path):
            os.remove(completed_local_path)
        (status, output) = getstatusoutput(self.get_cmd + ' ' + self._host + ':' + self.remote_log_dir + '/' +
                                           filename + ' ' + completed_local_path)
        Log.debug(self.get_cmd + ' ' + self._host + ':' + self.remote_log_dir + '/' + filename + ' ' +
                  completed_local_path)
        if status == 0:
            Log.debug('The COMPLETED files have been transfered')
            return True
        else:
            Log.debug('Something did not work well when transferring the COMPLETED files')
            return False

    def submit_job(self, job_script):
        (status, output) = getstatusoutput(self.get_submit_cmd(job_script))
        if status == 0:
            job_id = self.get_submitted_job_id(output)
            Log.debug(job_id)
            return int(job_id)

    def normal_stop(self):
        sleep(SLEEPING_TIME)
        (status, output) = getstatusoutput(self.get_checkjob_cmd(' '))
        for job_id in self.jobs_in_queue(output):
            self.cancel_job(job_id)

        exit(0)

    def smart_stop(self):
        sleep(SLEEPING_TIME)
        (status, output) = getstatusoutput(self.get_checkjob_cmd(' '))
        Log.debug(self.jobs_in_queue(output))
        while self.jobs_in_queue(output):
            Log.debug(self.jobs_in_queue(output))
            sleep(SLEEPING_TIME)
            (status, output) = getstatusoutput(self.get_checkjob_cmd(' '))
        exit(0)

    def set_host(self, new_host):
        self._host = new_host

    def set_scratch(self, new_scratch):
        self._scratch = new_scratch

    def set_project(self, new_project):
        self._project = new_project

    def set_user(self, new_user):
        self._user = new_user

    def set_remote_log_dir(self, new_remote_log_dir):
        self.remote_log_dir = new_remote_log_dir

    def get_checkhost_cmd(self):
        raise NotImplementedError

    def get_mkdir_cmd(self):
        raise NotImplementedError

    def parse_job_output(self, output):
        raise NotImplementedError

    def jobs_in_queue(self, output):
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
        return '"nohup /bin/sh {0} > {0}.stdout 2> {0}.stderr & echo \$!"'.format(os.path.join(self.remote_log_dir,
                                                                                               job_script))

    @staticmethod
    def get_pscall(job_id):
        return '"kill -0 {0} > {0}.stat.stdout 2> {0}.stat.stderr; echo \$?"'.format(job_id)

    @staticmethod
    def get_qstatjob(job_id):
        return '''"if [[ \$(qstat | grep {0}) != '' ]];
        then echo \$(qstat | grep {0} | awk '{{print \$5}}' | head -n 1); else echo 'c'; fi"'''.format(job_id)