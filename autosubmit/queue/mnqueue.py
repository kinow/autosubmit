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


from xml.dom.minidom import parseString

from autosubmit.queue.hpcqueue import HPCQueue


class MnQueue(HPCQueue):
    def __init__(self, expid):
        HPCQueue.__init__(self)
        self._host = "mn-ecm86"
        self._scratch = "/gpfs/scratch"
        self._project = "ecm86"
        self._user = "ecm86603"
        self.expid = expid
        self.job_status = dict()
        self.job_status['COMPLETED'] = ['Completed']
        self.job_status['RUNNING'] = ['Running']
        self.job_status['QUEUING'] = ['Pending', 'Idle', 'Blocked']
        self.job_status['FAILED'] = ['Failed', 'Node_fail', 'Timeout', 'Removed']
        self.update_cmds()

    def update_cmds(self):
        self.remote_log_dir = "/gpfs/scratch/ecm86/\$USER/" + self.expid + "/LOG_" + self.expid
        self.cancel_cmd = "ssh " + self._host + " mncancel"
        self.checkjob_cmd = "ssh " + self._host + " checkjob --xml"
        self._checkhost_cmd = "ssh " + self._host + " echo 1"
        self.submit_cmd = ("ssh " + self._host + " mnsubmit -initialdir " + self.remote_log_dir + " " +
                           self.remote_log_dir + "/")
        self._status_cmd = "ssh " + self._host + " mnq --xml"
        self.put_cmd = "scp"
        self.get_cmd = "scp"
        self.mkdir_cmd = "ssh " + self._host + " mkdir -p " + self.remote_log_dir

    def get_checkhost_cmd(self):
        return self._checkhost_cmd

    def get_submit_cmd(self):
        return self.submit_cmd

    def get_remote_log_dir(self):
        self.remote_log_dir = "/gpfs/scratch/ecm86/\$USER/" + self.expid + "/LOG_" + self.expid
        return self.remote_log_dir

    def get_mkdir_cmd(self):
        return self.mkdir_cmd

    def parse_job_output(self, output):
        dom = parseString(output)
        job_xml = dom.getElementsByTagName("job")
        job_state = job_xml[0].getAttribute('State')
        return job_state

    def get_submitted_job_id(self, output):
        return output.split(' ')[3]

    def jobs_in_queue(self, output):
        dom = parseString(output)
        job_list = dom.getElementsByTagName("job")
        return [int(job.getAttribute('JobID')) for job in job_list]
