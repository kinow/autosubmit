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


from queue.hpcqueue import HPCQueue


class Mn3Queue(HPCQueue):
    def __init__(self, expid):
        HPCQueue.__init__(self)
        self._host = "mn-ecm86"
        self._scratch = ""
        self._project = ""
        self._user = ""
        self.expid = expid
        self.job_status = dict()
        self.job_status['COMPLETED'] = ['DONE']
        self.job_status['RUNNING'] = ['RUN']
        self.job_status['QUEUING'] = ['PEND', 'FW_PEND']
        self.job_status['FAILED'] = ['SSUSP', 'USUSP', 'EXIT']
        self.update_cmds()

    def update_cmds(self):
        self.remote_log_dir = (self._scratch + "/" + self._project + "/" + self._user + "/" + self.expid + "/LOG_"
                               + self.expid)
        self.cancel_cmd = "ssh " + self._host + " bkill"
        self.checkjob_cmd = "ssh " + self._host + " bjobs"
        self._checkhost_cmd = "ssh " + self._host + " echo 1"
        self.submit_cmd = "ssh " + self._host + " bsub \< " + self.remote_log_dir + "/"
        self._status_cmd = "ssh " + self._host + " bjobs -w -X"
        self.put_cmd = "scp"
        self.get_cmd = "scp"
        self.mkdir_cmd = "ssh " + self._host + " mkdir -p " + self.remote_log_dir

    def get_checkhost_cmd(self):
        return self._checkhost_cmd

    def get_submit_cmd(self):
        return self.submit_cmd

    def get_mkdir_cmd(self):
        return self.mkdir_cmd

    def get_remote_log_dir(self):
        return self.remote_log_dir

    def parse_job_output(self, output):
        job_state = output.split('\n')[1].split()[2]
        return job_state

    def get_submitted_job_id(self, output):
        return output.split('<')[1].split('>')[0]

    def jobs_in_queue(self, output):
        return zip(*[line.split() for line in output.split('\n')])[0][1:]
