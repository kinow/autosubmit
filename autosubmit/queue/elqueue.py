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
from autosubmit.queue.lgqueue import LgHeader


class ElQueue(HPCQueue):
    def __init__(self, expid):
        HPCQueue.__init__(self)
        self._host = "ellen"
        self.scratch = "/cfu/scratch"
        self.project = ""
        self.user = ""
        self._header = LgHeader()
        self.expid = expid
        self.job_status = dict()
        self.job_status['COMPLETED'] = ['1']
        self.job_status['RUNNING'] = ['0']
        self.job_status['QUEUING'] = ['qw', 'hqw', 'hRwq']
        self.job_status['FAILED'] = ['Eqw', 'Ehqw', 'EhRqw']
        self._pathdir = "\$HOME/LOG_" + self.expid
        self.update_cmds()

    def update_cmds(self):
        self.remote_log_dir = (self.scratch + "/" + self.project + "/" + self.user + "/" + self.expid + "/LOG_" +
                               self.expid)
        self._status_cmd = "ssh " + self._host + " bjobs -w -X"
        self.cancel_cmd = "ssh " + self._host + " kill -SIGINT"
        self._checkhost_cmd = "ssh " + self._host + " echo 1"
        self.put_cmd = "scp"
        self.get_cmd = "scp"
        self.mkdir_cmd = "ssh " + self._host + " mkdir -p " + self.remote_log_dir

    def get_checkhost_cmd(self):
        return self._checkhost_cmd

    def get_remote_log_dir(self):
        return self.remote_log_dir

    def get_mkdir_cmd(self):
        return self.mkdir_cmd

    def parse_job_output(self, output):
        return output

    def get_submitted_job_id(self, output):
        return output

    def jobs_in_queue(self, output):
        dom = parseString(output)
        jobs_xml = dom.getElementsByTagName("JB_job_number")
        return [int(element.firstChild.nodeValue) for element in jobs_xml]

    def get_submit_cmd(self, job_script):
        return "ssh " + self._host + " " + self.get_shcall(job_script)

    def get_checkjob_cmd(self, job_id):
        return "ssh " + self._host + " " + HPCQueue.get_pscall(job_id)

