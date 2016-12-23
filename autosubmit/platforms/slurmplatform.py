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

from xml.dom.minidom import parseString

from autosubmit.platforms.paramiko_platform import ParamikoPlatform


class SlurmPlatform(ParamikoPlatform):
    """
    Class to manage jobs to host using SLURM scheduler

    :param expid: experiment's identifier
    :type expid: str
    """

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_queue_directive(self, job):
        """
        Returns queue directive for the specified job

        :param job: job to create queue directive for
        :type job: Job
        :return: queue directive
        :rtype: str
        """
        # There is no queue, so directive is empty
        return "#"

    def __init__(self, expid, name, config):
        ParamikoPlatform.__init__(self, expid, name, config)
        self._header = SlurmHeader()
        self.job_status = dict()

        self.job_status['COMPLETED'] = ['COMPLETED']
        self.job_status['RUNNING'] = ['RUNNING']
        self.job_status['QUEUING'] = ['PENDING', 'CONFIGURING', 'RESIZING']
        self.job_status['FAILED'] = ['FAILED', 'CANCELLED', 'NODE_FAIL', 'PREEMPTED', 'SUSPENDED', 'TIMEOUT']
        self._pathdir = "\$HOME/LOG_" + self.expid
        self.update_cmds()

    def update_cmds(self):
        """
        Updates commands for platforms
        """
        self.root_dir = os.path.join(self.scratch, self.project, self.user, self.expid)
        self.remote_log_dir = os.path.join(self.root_dir, "LOG_" + self.expid)
        self.cancel_cmd = "scancel"
        self._checkhost_cmd = "echo 1"
        self._submit_cmd = 'sbatch -D {1} {1}/'.format(self.host, self.remote_log_dir)
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
        return output.strip().split(' ')[0].strip()

    def get_submitted_job_id(self, output):
        return output.split(' ')[3]

    def jobs_in_queue(self):
        dom = parseString('')
        jobs_xml = dom.getElementsByTagName("JB_job_number")
        return [int(element.firstChild.nodeValue) for element in jobs_xml]

    def get_submit_cmd(self, job_script, job):
        return self._submit_cmd + job_script

    def get_checkjob_cmd(self, job_id):
        return 'sacct -n -j {1} -o "State"'.format(self.host, job_id)


class SlurmHeader:
    """Class to handle the SLURM headers of a job"""

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
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
            return "SBATCH -p {0}".format(job.parameters['CURRENT_QUEUE'])

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_account_directive(self, job):
        """
        Returns account directive for the specified job

        :param job: job to create account directive for
        :type job: Job
        :return: account directive
        :rtype: str
        """
        # There is no account, so directive is empty
        if job.parameters['CURRENT_PROJ'] != '':
            return "SBATCH -A {0}".format(job.parameters['CURRENT_PROJ'])
        return ""

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_memory_directive(self, job):
        """
        Returns memory directive for the specified job

        :param job: job to create memory directive for
        :type job: Job
        :return: memory directive
        :rtype: str
        """
        # There is no memory, so directive is empty
        if job.parameters['MEMORY'] != '':
            return "SBATCH --mem {0}".format(job.parameters['MEMORY'])
        return ""

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_memory_per_task_directive(self, job):
        """
        Returns memory per task directive for the specified job

        :param job: job to create memory per task directive for
        :type job: Job
        :return: memory per task directive
        :rtype: str
        """
        # There is no memory per task, so directive is empty
        if job.parameters['MEMORY_PER_TASK'] != '':
            return "SBATCH --mem-per-cpu {0}".format(job.parameters['MEMORY_PER_TASK'])
        return ""

    SERIAL = textwrap.dedent("""\
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #%QUEUE_DIRECTIVE%
            #%ACCOUNT_DIRECTIVE%
            #%MEMORY_DIRECTIVE%
            #%MEMORY_PER_TASK_DIRECTIVE%
            #SBATCH -n %NUMPROC%
            #SBATCH -t %WALLCLOCK%:00
            #SBATCH -J %JOBNAME%
            #SBATCH -o %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%OUT_LOG_DIRECTIVE%
            #SBATCH -e %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%ERR_LOG_DIRECTIVE%
            #
            ###############################################################################
           """)

    PARALLEL = textwrap.dedent("""\
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #%QUEUE_DIRECTIVE%
            #%ACCOUNT_DIRECTIVE%
            #%MEMORY_DIRECTIVE%
            #%MEMORY_PER_TASK_DIRECTIVE%
            #SBATCH -n %NUMPROC%
            #SBATCH -t %WALLCLOCK%:00
            #SBATCH -J %JOBNAME%
            #SBATCH -o %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%OUT_LOG_DIRECTIVE%
            #SBATCH -e %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%ERR_LOG_DIRECTIVE%
            #
            ###############################################################################
            """)