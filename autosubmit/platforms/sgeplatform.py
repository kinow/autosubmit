#!/usr/bin/env python

# Copyright 2015 Earth Sciences Department, BSC-CNS

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
import textwrap
import os
import subprocess

from xml.dom.minidom import parseString

from autosubmit.platforms.paramiko_platform import ParamikoPlatform


class SgePlatform(ParamikoPlatform):
    """
    Class to manage jobs to host using SGE scheduler

    :param expid: experiment's identifier
    :type expid: str
    """
    def __init__(self, expid, name, config):
        ParamikoPlatform.__init__(self, expid, name, config)
        self._header = SgeHeader()
        self.job_status = dict()
        self.job_status['COMPLETED'] = ['c']
        self.job_status['RUNNING'] = ['r', 't', 'Rr', 'Rt']
        self.job_status['QUEUING'] = ['qw', 'hqw', 'hRwq', 'Rs', 'Rts', 'RS', 'RtS', 'RT', 'RtT']
        self.job_status['FAILED'] = ['Eqw', 'Ehqw', 'EhRqw', 's', 'ts', 'S', 'tS', 'T', 'tT', 'dr', 'dt', 'dRr', 'dRt',
                                     'ds', 'dS', 'dT', 'dRs', 'dRS', 'dRT']
        self._pathdir = "\$HOME/LOG_" + self.expid
        self.update_cmds()

    def update_cmds(self):
        """
        Updates commands for platforms
        """
        self.root_dir = os.path.join(self.scratch, self.project, self.user, self.expid)
        self.remote_log_dir = os.path.join(self.root_dir, "LOG_" + self.expid)
        self.cancel_cmd = "qdel"
        self._checkhost_cmd = "echo 1"
        self._submit_cmd = "qsub -wd " + self.remote_log_dir + " " + self.remote_log_dir + "/"
        self.put_cmd = "scp"
        self.get_cmd = "scp"
        self.mkdir_cmd = "mkdir -p " + self.remote_log_dir

    def get_checkhost_cmd(self):
        return self._checkhost_cmd

    def get_mkdir_cmd(self):
        return self.mkdir_cmd

    def get_remote_log_dir(self):
        return self.remote_log_dir

    def parse_job_output(self, output):
        return output

    def get_submitted_job_id(self, output):
        return output.split(' ')[2]

    def jobs_in_queue(self):
        output = subprocess.check_output('qstat -xml'.format(self.host), shell=True)
        dom = parseString(output)
        jobs_xml = dom.getElementsByTagName("JB_job_number")
        return [int(element.firstChild.nodeValue) for element in jobs_xml]

    def get_submit_cmd(self, job_script, job):
        return self._submit_cmd + job_script

    def get_checkjob_cmd(self, job_id):
        return self.get_qstatjob(job_id)


class SgeHeader:
    """Class to handle the Ithaca headers of a job"""

    # noinspection PyMethodMayBeStatic
    def get_queue_directive(self, job):
        """
        Returns queue directive for the specified job

        :param job: job to create queue directive for
        :type job: Job
        :return: queue directive
        :rtype: str
        """
        # There is no queue, so directive is empty
        if job.parameters['CURRENT_QUEUE'] == '':
            return ""
        else:
            return "$ -q {0}".format(job.parameters['CURRENT_QUEUE'])

    SERIAL = textwrap.dedent("""\
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #$ -S /bin/sh
            #$ -N %JOBNAME%
            #$ -e %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/
            #$ -o %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/
            #$ -V
            #$ -l h_rt=%WALLCLOCK%:00
            #$ -l s_rt=%WALLCLOCK%:00
            #%QUEUE_DIRECTIVE%
            #
            ###############################################################################
            """)

    PARALLEL = textwrap.dedent("""\
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #$ -S /bin/sh
            #$ -N %JOBNAME%
            #$ -e %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/
            #$ -o %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/
            #$ -V
            #$ -l h_rt=%WALLCLOCK%:00
            #$ -l s_rt=%WALLCLOCK%:00
            #$ -pe orte %NUMPROC%
            #%QUEUE_DIRECTIVE%
            #
            ###############################################################################
            """)