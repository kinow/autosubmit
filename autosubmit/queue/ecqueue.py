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
from autosubmit.config.basicConfig import BasicConfig
from log import Log


class EcQueue(HPCQueue):
    def __init__(self, expid):
        HPCQueue.__init__(self)
        self._host = "c2a"
        self._scratch = "/scratch/ms"
        self._project = "spesiccf"
        self._user = "c3m"
        self.expid = expid
        self.job_status = dict()
        self.job_status['COMPLETED'] = ['DONE']
        self.job_status['RUNNING'] = ['EXEC']
        self.job_status['QUEUING'] = ['INIT', 'RETR', 'STDBY', 'WAIT']
        self.job_status['FAILED'] = ['STOP']
        self._pathdir = "\$HOME/LOG_" + self.expid
        self.update_cmds()

    def update_cmds(self):
        self.remote_log_dir = (self._scratch + "/" + self._project + "/" + self._user + "/" + self.expid + "/LOG_" +
                               self.expid)
        self.cancel_cmd = "eceaccess-job-delete"
        self.checkjob_cmd = "ecaccess-job-list"
        self._checkhost_cmd = "ecaccess-certificate-list"
        self.submit_cmd = ("ecaccess-job-submit -queueName " + self._host + " " + BasicConfig.LOCAL_ROOT_DIR + "/" +
                           self.expid + "/tmp/")
        self._status_cmd = "ecaccess-job-get"
        self.put_cmd = "ecaccess-file-put"
        self.get_cmd = "ecaccess-file-get"
        self.mkdir_cmd = ("ecaccess-file-mkdir " + self._host + ":" + self._scratch + "/" + self._project + "/" +
                          self._user + "/" + self.expid + "; " + "ecaccess-file-mkdir " + self._host + ":" +
                          self.remote_log_dir)

    def get_checkhost_cmd(self):
        return self._checkhost_cmd

    def get_submit_cmd(self):
        return self.submit_cmd

    def get_remote_log_dir(self):
        return self.remote_log_dir

    def get_mkdir_cmd(self):
        return self.mkdir_cmd

    def parse_job_output(self, output):
        job_state = output.split('\n')[7].split()[1]
        return job_state

    def get_submitted_job_id(self, output):
        return output

    def jobs_in_queue(self, output):
        Log.debug(output)
        return output.split()

#
# def main():
#     q = EcQueue()
#     q.check_job(3431854)
#     j = q.submit_job("/cfu/autosubmit/e000/templates/e000.sim")
#     sleep(10)
#     print q.check_job(j)
#     q.cancel_job(j)
#
#
# if __name__ == "__main__":
#     main()
