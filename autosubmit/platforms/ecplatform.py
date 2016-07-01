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

from autosubmit.platforms.paramiko_platform import ParamikoPlatform, ParamikoPlatformException
from autosubmit.config.log import Log


class EcPlatform(ParamikoPlatform):
    """
    Class to manage queues with eceacces

    :param expid: experiment's identifier
    :type expid: str
    :param scheduler: scheduler to use
    :type scheduler: str (pbs, loadleveler)
    """

    def __init__(self, expid, name, config, scheduler):
        ParamikoPlatform.__init__(self, expid, name, config)
        if scheduler == 'pbs':
            self._header = EcCcaHeader()
        elif scheduler == 'loadleveler':
            self._header = EcHeader()
        else:
            raise ParamikoPlatformException('ecaccess scheduler {0} not supported'.format(scheduler))
        self.job_status = dict()
        self.job_status['COMPLETED'] = ['DONE']
        self.job_status['RUNNING'] = ['EXEC']
        self.job_status['QUEUING'] = ['INIT', 'RETR', 'STDBY', 'WAIT']
        self.job_status['FAILED'] = ['STOP']
        self._pathdir = "\$HOME/LOG_" + self.expid
        self.update_cmds()

    def update_cmds(self):
        """
        Updates commands for platforms
        """
        self.root_dir = os.path.join(self.scratch, self.project, self.user, self.expid)
        self.remote_log_dir = os.path.join(self.root_dir, "LOG_" + self.expid)
        self.cancel_cmd = "eceaccess-job-delete"
        self._checkjob_cmd = "ecaccess-job-list "
        self._checkhost_cmd = "ecaccess-certificate-list"
        self._submit_cmd = ("ecaccess-job-submit -distant -queueName " + self.host + " " + self.host + ":" +
                            self.remote_log_dir + "/")
        self.put_cmd = "ecaccess-file-put"
        self.get_cmd = "ecaccess-file-get"
        self.del_cmd = "ecaccess-file-delete"
        self.mkdir_cmd = ("ecaccess-file-mkdir " + self.host + ":" + self.scratch + "/" + self.project + "/" +
                          self.user + "/" + self.expid + "; " + "ecaccess-file-mkdir " + self.host + ":" +
                          self.remote_log_dir)

    def get_checkhost_cmd(self):
        return self._checkhost_cmd

    def get_remote_log_dir(self):
        return self.remote_log_dir

    def get_mkdir_cmd(self):
        return self.mkdir_cmd

    def parse_job_output(self, output):
        job_state = output.split('\n')
        if len(job_state) > 7:
            job_state = job_state[7].split()
            if len(job_state) > 1:
                return job_state[1]
        return 'DONE'

    def get_submitted_job_id(self, output):
        return output

    def jobs_in_queue(self):
        """
        Returns empty list because ecacces does not support this command

        :return: empty list
        :rtype: list
        """
        return ''.split()

    def get_checkjob_cmd(self, job_id):
        return self._checkjob_cmd + str(job_id)

    def get_submit_cmd(self, job_script):
        return self._submit_cmd + job_script

    def connect(self):
        """
        In this case, it does nothing because connection is established foe each command

        :return: True
        :rtype: bool
        """
        return True

    def send_command(self, command):
        try:
            output = subprocess.check_output(command, shell=True)
        except subprocess.CalledProcessError as e:
            Log.error('Could not execute command {0} on {1}'.format(e.cmd, self.host))
            return False
        self._ssh_output = output
        return True

    def send_file(self, filename):
        self.check_remote_log_dir()
        self.delete_file(filename)
        command = '{0} {1} {3}:{2}'.format(self.put_cmd, os.path.join(self.tmp_path, filename),
                                           os.path.join(self.get_files_path(), filename), self.host)
        try:
            subprocess.check_call(command, shell=True)
        except subprocess.CalledProcessError:
            Log.error('Could not send file {0} to {1}'.format(os.path.join(self.tmp_path, filename),
                                                              os.path.join(self.get_files_path(), filename)))
            raise
        return True

    def get_file(self, filename, must_exist=True):
        local_path = os.path.join(self.tmp_path, filename)
        if os.path.exists(local_path):
            os.remove(local_path)

        command = '{0} {3}:{2} {1}'.format(self.get_cmd, local_path, os.path.join(self.get_files_path(), filename),
                                           self.host)
        try:
            subprocess.check_call(command, shell=True)
        except subprocess.CalledProcessError:
            if not must_exist:
                raise Exception('File {0} does not exists'.format(filename))
            return False
        return True

    def delete_file(self, filename):
        command = '{0} {1}:{2}'.format(self.del_cmd, self.host, os.path.join(self.get_files_path(), filename))
        try:
            subprocess.check_call(command, shell=True)
        except subprocess.CalledProcessError:
            Log.debug('Could not remove file {0}'.format(os.path.join(self.get_files_path(), filename)))
            return False
        return True

    def get_ssh_output(self):
        return self._ssh_output


class EcHeader:
    """Class to handle the ECMWF headers of a job"""

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

    # noinspection PyPep8
    SERIAL = textwrap.dedent("""\
            #!/bin/ksh
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #@ shell            = /usr/bin/ksh
            #@ class            = ns
            #@ job_type         = serial
            #@ job_name         = %JOBNAME%
            #@ output           = %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).out
            #@ error            = %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).err
            #@ notification     = error
            #@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
            #@ wall_clock_limit = %WALLCLOCK%:00
            #@ platforms
            #
            ###############################################################################
            """)

    # noinspection PyPep8
    PARALLEL = textwrap.dedent("""\
            #!/bin/ksh
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #@ shell            = /usr/bin/ksh
            #@ class            = np
            #@ job_type         = parallel
            #@ job_name         = %JOBNAME%
            #@ output           = %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).out
            #@ error            = %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).err
            #@ notification     = error
            #@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
            #@ ec_smt           = no
            #@ total_tasks      = %NUMPROC%
            #@ wall_clock_limit = %WALLCLOCK%:00
            #@ platforms
            #
            ###############################################################################
            """)


class EcCcaHeader:
    """Class to handle the ECMWF headers of a job"""

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
             #
             #PBS -N %JOBNAME%
             #PBS -q ns
             #PBS -l walltime=%WALLCLOCK%:00
             #PBS -l EC_billing_account=%CURRENT_BUDG%
             #
             ###############################################################################

            """)

    PARALLEL = textwrap.dedent("""\
             #!/bin/bash
             ###############################################################################
             #                   %TASKTYPE% %EXPID% EXPERIMENT
             ###############################################################################
             #
             #PBS -N %JOBNAME%
             #PBS -q np
             #PBS -l EC_total_tasks=%NUMPROC%
             #PBS -l EC_threads_per_task=%NUMTHREADS%
             #PBS -l EC_tasks_per_node=%NUMTASK%
             #PBS -l walltime=%WALLCLOCK%:00
             #PBS -l EC_billing_account=%CURRENT_BUDG%
             #
             ###############################################################################
            """)
