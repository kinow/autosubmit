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
from pxssh import pxssh
import textwrap

from autosubmit.queue.hpcqueue import HPCQueue
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.config.log import Log


class EcQueue(HPCQueue):

    def __init__(self, expid, scheduler):
        HPCQueue.__init__(self)
        self._host = ""
        self.scratch = ""
        self.project = ""
        self.user = ""
        if scheduler == 'pbs':
            self._header = EcCcaHeader()
        elif scheduler == 'loadleveler':
            self._header = EcHeader()
        else:
            Log.error('ecaccess scheduler {0} not supported'.format(scheduler))
            exit(1)
        self.expid = expid
        self.job_status = dict()
        self.job_status['COMPLETED'] = ['DONE']
        self.job_status['RUNNING'] = ['EXEC']
        self.job_status['QUEUING'] = ['INIT', 'RETR', 'STDBY', 'WAIT']
        self.job_status['FAILED'] = ['STOP']
        self._pathdir = "\$HOME/LOG_" + self.expid
        self.update_cmds()

    def update_cmds(self):
        self.remote_log_dir = (self.scratch + "/" + self.project + "/" + self.user + "/" + self.expid + "/LOG_" +
                               self.expid)
        self.cancel_cmd = "eceaccess-job-delete"
        self._checkjob_cmd = "ecaccess-job-list "
        self._checkhost_cmd = "ecaccess-certificate-list"
        self._submit_cmd = ("ecaccess-job-submit -queueName " + self._host + " " + BasicConfig.LOCAL_ROOT_DIR + "/" +
                            self.expid + "/tmp/")
        self.put_cmd = "ecaccess-file-put"
        self.get_cmd = "ecaccess-file-get"
        self.mkdir_cmd = ("ecaccess-file-mkdir " + self._host + ":" + self.scratch + "/" + self.project + "/" +
                          self.user + "/" + self.expid + "; " + "ecaccess-file-mkdir " + self._host + ":" +
                          self.remote_log_dir)

    def get_checkhost_cmd(self):
        return self._checkhost_cmd

    def get_remote_log_dir(self):
        return self.remote_log_dir

    def get_mkdir_cmd(self):
        return self.mkdir_cmd

    def parse_job_output(self, output):
        job_state = output.split('\n')[7].split()[1]
        return job_state

    def get_submitted_job_id(self, output):
        return output

    def jobs_in_queue(self):
        return ''.split()

    def get_checkjob_cmd(self, job_id):
        return self._checkjob_cmd + str(job_id)

    def get_submit_cmd(self, job_script):
        return self._submit_cmd + job_script


class EcHeader:
    """Class to handle the ECMWF headers of a job"""

    SERIAL = textwrap.dedent("""
            #!/bin/ksh
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #@ shell            = /usr/bin/ksh
            #@ class            = ns
            #@ job_type         = serial
            #@ job_name         = %JOBNAME%
            #@ output           = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).out
            #@ error            = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).err
            #@ notification     = error
            #@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
            #@ wall_clock_limit = %WALLCLOCK%:00
            #@ queue
            #
            ###############################################################################
            """)

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
            #@ output           = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).out
            #@ error            = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).err
            #@ notification     = error
            #@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
            #@ ec_smt           = no
            #@ total_tasks      = %NUMPROC%
            #@ wall_clock_limit = %WALLCLOCK%:00
            #@ queue
            #
            ###############################################################################
            """)


class EcCcaHeader:
    """Class to handle the ECMWF headers of a job"""

    SERIAL = textwrap.dedent("""
             #!/bin/bash
             ###############################################################################
             #                   %TASKTYPE% %EXPID% EXPERIMENT
             ###############################################################################
             #
             #PBS -N %JOBNAME%
             #PBS -q ns
             #PBS -l walltime=%WALLCLOCK_SETUP%:00
             #PBS -l EC_billing_account=%HPCPROJ%
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
             #PBS -l EC_total_tasks=%NUMPROC_SIM%
             #PBS -l EC_threads_per_task=%NUMTHREAD_SIM%
             #PBS -l EC_tasks_per_node=%NUMTASK_SIM%
             #PBS -l walltime=%WALLCLOCK_SIM%:00
             #PBS -l EC_billing_account=%HPCPROJ%
             #
             ###############################################################################
            """)