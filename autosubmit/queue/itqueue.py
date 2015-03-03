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


class ItQueue(HPCQueue):
    def __init__(self, expid):
        HPCQueue.__init__(self)
        self._host = "ithaca"
        self._scratch = ""
        self._project = ""
        self._user = ""
        self.expid = expid
        self.job_status = dict()
        self.job_status['COMPLETED'] = ['c']
        self.job_status['RUNNING'] = ['r', 't', 'Rr', 'Rt']
        self.job_status['QUEUING'] = ['qw', 'hqw', 'hRwq', 'Rs', 'Rts', 'RS', 'RtS', 'RT', 'RtT']
        self.job_status['FAILED'] = ['Eqw', 'Ehqw', 'EhRqw', 's', 'ts', 'S', 'tS', 'T', 'tT', 'dr', 'dt', 'dRr', 'dRt',
                                     'ds', 'dS', 'dT', 'dRs', 'dRS', 'dRT']
        self._pathdir = "\$HOME/LOG_" + self.expid
        self.update_cmds()

    def update_cmds(self):
        self.remote_log_dir = (self._scratch + "/" + self._project + "/" + self._user + "/" + self.expid + "/LOG_" +
                               self.expid)
        self.cancel_cmd = "ssh " + self._host + " qdel"
        self.checkjob_cmd = "ssh " + self._host + " qstatjob.sh"
        self._checkhost_cmd = "ssh " + self._host + " echo 1"
        self.submit_cmd = "ssh " + self._host + " qsub -wd " + self.remote_log_dir + " " + self.remote_log_dir + "/"
        self.put_cmd = "scp"
        self.get_cmd = "scp"
        self.mkdir_cmd = "ssh " + self._host + " mkdir -p " + self.remote_log_dir

    def get_checkhost_cmd(self):
        return self._checkhost_cmd

    def get_mkdir_cmd(self):
        return self.mkdir_cmd

    def get_submit_cmd(self):
        return self.submit_cmd

    def get_remote_log_dir(self):
        return self.remote_log_dir

    def parse_job_output(self, output):
        return output

    def get_submitted_job_id(self, output):
        return output.split(' ')[2]

    def jobs_in_queue(self, output):
        dom = parseString(output)
        jobs_xml = dom.getElementsByTagName("JB_job_number")
        return [int(element.firstChild.nodeValue) for element in jobs_xml]


if __name__ == "__main__":
    q = ItQueue("i000")
# q.check_job(1688)
# j = q.submit_job("/home/cfu/omula/test/run_t159l62_orca1.ksh")
# sleep(10)
# print q.check_job(j)
# q.cancel_job(j)
