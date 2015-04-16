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
import textwrap
from xml.dom.minidom import parseString

from autosubmit.platforms.hpcplatform import HPCPlatform
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.config.log import Log


class LocalPlatform(HPCPlatform):
    """
    Class to manage jobs to localhost

    :param expid: experiment's identifier
    :type expid: str
    """
    def __init__(self, expid):
        HPCPlatform.__init__(self)
        self._host = ""
        self.scratch = ""
        self.project = ""
        self.user = ""
        self._header = LocalHeader()
        self.expid = expid
        self.job_status = dict()
        self.job_status['COMPLETED'] = ['1']
        self.job_status['RUNNING'] = ['0']
        self.job_status['QUEUING'] = []
        self.job_status['FAILED'] = []
        self.update_cmds()

    def update_cmds(self):
        self.root_dir = os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.expid)
        self.remote_log_dir = os.path.join(self.root_dir, "tmp", 'LOG_' + self.expid)
        self.cancel_cmd = "kill -SIGINT"
        self._checkhost_cmd = "echo 1"
        self.put_cmd = "cp -p"
        self.get_cmd = "cp"
        self.mkdir_cmd = "mkdir -p " + self.remote_log_dir

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

    def jobs_in_queue(self):
        dom = parseString('')
        jobs_xml = dom.getElementsByTagName("JB_job_number")
        return [int(element.firstChild.nodeValue) for element in jobs_xml]

    def get_submit_cmd(self, job_script):
        return self.get_shcall(job_script)

    def get_checkjob_cmd(self, job_id):
        return self.get_pscall(job_id)

    def connect(self):
        return True

    def send_command(self, command):
        (status, output) = getstatusoutput(command)
        if status != 0:
            Log.error('Could not execute command {0} on {1}'.format(command, self._host))
            return False
        self._ssh_output = output
        return True

    def send_file(self, local_path, remote_path):
        command = '{0} {1} {2}'.format(self.put_cmd, local_path, remote_path)
        (status, output) = getstatusoutput(command)
        if status != 0:
            Log.error('Could not send file {0} to {1}'.format(local_path, remote_path))
            return False
        return True

    def get_file(self, remote_path, local_path):
        command = '{0} {2} {1}'.format(self.get_cmd, local_path, remote_path)
        (status, output) = getstatusoutput(command)
        if status != 0:
            Log.error('Could not get file {0} from {1}'.format(local_path, remote_path))
            return False
        return True

    def get_ssh_output(self):
        return self._ssh_output


class LocalHeader:
    """Class to handle the Ps headers of a job"""

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_queue_directive(self, job):
        """
        Returns queue directive for the specified job

        :param job: job to create queue directibve for
        :type job: Job
        :return: queue directive
        :rtype: str
        """
        # There is no queue, so directive is empty
        return ""

    SERIAL = textwrap.dedent("""\
            #!/bin/bash
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            """)

    PARALLEL = textwrap.dedent("""\
            #!/bin/bash
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            """)

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
