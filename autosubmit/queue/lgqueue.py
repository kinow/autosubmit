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


from autosubmit.queue.hpcqueue import HPCQueue
from autosubmit.config.log import Log
from autosubmit.job.job_headers import LgHeader


class LgQueue(HPCQueue):
    def __init__(self, expid):
        HPCQueue.__init__(self)
        self._host = "lindgren"
        self._scratch = ""
        self._project = ""
        self._user = ""
        self._header = LgHeader()
        self.expid = expid
        self.job_status = dict()
        self.job_status['COMPLETED'] = ['C', 'E']
        self.job_status['RUNNING'] = ['R']
        self.job_status['QUEUING'] = ['Q', 'H', 'S', 'T', 'W']
        self.job_status['FAILED'] = ['Failed', 'Node_fail', 'Timeout']
        self._pathdir = "\$HOME/LOG_" + self.expid
        self.update_cmds()

    def update_cmds(self):
        self.remote_log_dir = (self._scratch + "/" + self._project + "/" + self._user + "/" +
                               self.expid + "/LOG_" + self.expid)
        self.cancel_cmd = "ssh " + self._host + " qdel"
        self.checkjob_cmd = "ssh " + self._host + " qstat"
        self._checkhost_cmd = "ssh " + self._host + " echo 1"
        self.submit_cmd = "ssh " + self._host + " qsub -d " + self.remote_log_dir + " " + self.remote_log_dir + "/ "
        self._status_cmd = "ssh " + self._host + " qsub -u \$USER | tail -n +6|cut -d' ' -f1"
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
        job_state = output.split('\n')[2].split()[4]
        return job_state

    def get_submitted_job_id(self, output):
        return output.split('.')[0]

    def jobs_in_queue(self, output):
        Log.debug(output)
        return output.split()

    def get_checkjob_cmd(self, job_id):
        return self.checkjob_cmd + str(job_id)

    def get_submit_cmd(self, job_script):
        return self.submit_cmd + job_script


# def main():
# q = LgQueue()
#     q.check_job(1688)
#     j = q.submit_job("/cfu/autosubmit/l002/templates/l002.sim")
#     sleep(10)
#     print q.check_job(j)
#     q.cancel_job(j)
#
#
# if __name__ == "__main__":
#     main()
