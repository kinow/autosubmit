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
from xml.dom.minidom import parseString
import platform

from autosubmit.queue.hpcqueue import HPCQueue
from autosubmit.config.basicConfig import BasicConfig


class PsQueue(HPCQueue):
    def __init__(self, expid):
        HPCQueue.__init__(self)
        self._host = platform.node()
        self._scratch = ""
        self._project = ""
        self._user = ""
        self.expid = expid
        self.job_status = dict()
        self.job_status['COMPLETED'] = ['1']
        self.job_status['RUNNING'] = ['0']
        self.job_status['QUEUING'] = ['qw', 'hqw', 'hRwq']
        self.job_status['FAILED'] = ['Eqw', 'Ehqw', 'EhRqw']
        self._pathdir = "\$HOME/LOG_" + self.expid
        self.update_cmds()

    def update_cmds(self):
        self.remote_log_dir = os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.expid, "tmp", 'LOG_' + self.expid)
        # Ellen-->self.remote_log_dir = self._scratch + "/" + self._project + "/" + self._user + "/" +
        # self._expid + "/LOG_" + self._expid
        # Local-->self._local_log_dir = "/cfu/autosubmit" + "/" + self._expid + "/LOG_" + self._expid
        self._remote_common_dir = os.path.join(BasicConfig.LOCAL_ROOT_DIR, "common")
        # Ellen -->self._remote_common_dir = "/cfs/klemming/nobackup/a/asifsami/common/autosubmit"
        # Local-->self._local_common_dir = "/cfu/autosubmit/common"
        self._status_cmd = "ssh " + self._host + " bjobs -w -X"
        self.cancel_cmd = "ssh " + self._host + " kill -SIGINT"
        self.checkjob_cmd = "ssh " + self._host + " " + self._remote_common_dir + "/" + "pscall.sh"
        self._checkhost_cmd = "ssh " + self._host + " echo 1"
        self.submit_cmd = ("ssh " + self._host + " " + self._remote_common_dir + "/" + "shcall.sh " +
                           self.remote_log_dir + " ")
        self.put_cmd = "scp"
        self.get_cmd = "scp"
        self.mkdir_cmd = "ssh " + self._host + " mkdir -p " + self.remote_log_dir

    def get_checkhost_cmd(self):
        return self._checkhost_cmd

    def get_submit_cmd(self):
        return self.submit_cmd

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


# def main():
# q = PsQueue()
#     q.check_job(1688)
#     j = q.submit_job("/cfu/autosubmit/l002/templates/l002.sim")
#     sleep(10)
#     print q.check_job(j)
#     q.cancel_job(j)
#
#
# if __name__ == "__main__":
#     main()
