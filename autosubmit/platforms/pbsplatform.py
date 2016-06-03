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

from autosubmit.platforms.paramiko_platform import ParamikoPlatform, ParamikoPlatformException
from autosubmit.config.log import Log


class PBSPlatform(ParamikoPlatform):
    """
    Class to manage jobs to host using PBS scheduler

    :param expid: experiment's identifier
    :type expid: str
    :param version: scheduler version
    :type version: str
    """

    def __init__(self, expid, name, config, version):
        ParamikoPlatform.__init__(self, expid, name, config)
        self._version = version

        if str.startswith(version, '10'):
            self._header = Pbs10Header()
        elif str.startswith(version, '11'):
            self._header = Pbs11Header()
        elif str.startswith(version, '12'):
            self._header = Pbs12Header()
        else:
            Log.error('PBS version {0} not supported'.format(version))
            raise HPCPlatformException('PBS version {0} not supported'.format(version))

        self.job_status = dict()
        self.job_status['COMPLETED'] = ['F', 'E', 'c', 'C']
        self.job_status['RUNNING'] = ['R']
        self.job_status['QUEUING'] = ['Q', 'H', 'S', 'T', 'W', 'U', 'M']
        self.job_status['FAILED'] = ['Failed', 'Node_fail', 'Timeout']
        self.update_cmds()

    def update_cmds(self):
        """
        Updates commands for platforms
        """
        self.root_dir = os.path.join(self.scratch, self.project, self.user, self.expid)
        self.remote_log_dir = os.path.join(self.root_dir, "LOG_" + self.expid)
        self.cancel_cmd = "ssh " + self.host + " qdel"
        self._checkhost_cmd = "ssh " + self.host + " echo 1"
        self.put_cmd = "scp"
        self.get_cmd = "scp"
        self.mkdir_cmd = "ssh " + self.host + " mkdir -p " + self.remote_log_dir
        self._submit_cmd = "ssh " + self.host + " qsub -d " + self.remote_log_dir + " " + self.remote_log_dir + "/ "

        if str.startswith(self._version, '11'):
            self._checkjob_cmd = "ssh " + self.host + " qstat"

    def get_checkhost_cmd(self):
        return self._checkhost_cmd

    def get_remote_log_dir(self):
        return self.remote_log_dir

    def get_mkdir_cmd(self):
        return self.mkdir_cmd

    def parse_job_output(self, output):
        # job_state = output.split('\n')[2].split()[4]
        # return job_state
        return output

    def get_submitted_job_id(self, output):
        return output.split('.')[0]

    def jobs_in_queue(self):
        return ''.split()

    def get_submit_cmd(self, job_script):
        return self._submit_cmd + job_script

    def get_checkjob_cmd(self, job_id):
        if str.startswith(self._version, '11'):
            return self._checkjob_cmd + str(job_id)
        else:
            return "ssh " + self.host + " " + self.get_qstatjob(job_id)


class Pbs12Header:
    """Class to handle the Archer headers of a job"""

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
            #!/bin/sh
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #PBS -N %JOBNAME%
            #PBS -l select=serial=true:ncpus=1
            #PBS -l walltime=%WALLCLOCK%:00
            #PBS -A %CURRENT_BUDG%
            #
            ###############################################################################
            """)

    PARALLEL = textwrap.dedent("""\
            #!/bin/sh
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #PBS -N %JOBNAME%
            #PBS -l select=%NUMPROC%
            #PBS -l walltime=%WALLCLOCK%:00
            #PBS -A %CURRENT_BUDG%
            #
            ###############################################################################
            """)


class Pbs10Header:
    """Class to handle the Hector headers of a job"""

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
            #!/bin/sh
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #PBS -N %JOBNAME%
            #PBS -q serial
            #PBS -l cput=%WALLCLOCK%:00
            #PBS -A %CURRENT_BUDG%
            #
            ###############################################################################
            """)

    PARALLEL = textwrap.dedent("""\
            #!/bin/sh
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #PBS -N %JOBNAME%
            #PBS -l mppwidth=%NUMPROC%
            #PBS -l mppnppn=32
            #PBS -l walltime=%WALLCLOCK%:00
            #PBS -A %CURRENT_BUDG%
            #
            ###############################################################################
            """)


class Pbs11Header:
    """Class to handle the Lindgren headers of a job"""

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
            #!/bin/sh
            ###############################################################################
            #                         %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #!/bin/sh --login
            #PBS -N %JOBNAME%
            #PBS -l mppwidth=%NUMPROC%
            #PBS -l mppnppn=%NUMTASK%
            #PBS -l walltime=%WALLCLOCK%
            #PBS -e %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%
            #PBS -o %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%
            #
            ###############################################################################
            """)

    PARALLEL = textwrap.dedent("""\
            #!/bin/sh
            ###############################################################################
            #                         %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #!/bin/sh --login
            #PBS -N %JOBNAME%
            #PBS -l mppwidth=%NUMPROC%
            #PBS -l mppnppn=%NUMTASK%
            #PBS -l walltime=%WALLCLOCK%
            #PBS -e %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%
            #PBS -o %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%
            #
            ###############################################################################
            """)