#!/usr/bin/env python

# Copyright 2017 Earth Sciences Department, BSC-CNS

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


class EcCcaHeader(object):
    """Class to handle the ECMWF headers of a job"""

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
        return ""

    # noinspection PyMethodMayBeStatic
    def get_tasks_per_node(self, job):
        if not isinstance(job.tasks, str):
            return ""
        else:
            return '#PBS -l EC_tasks_per_node={0}'.format(job.tasks)

    # noinspection PyMethodMayBeStatic
    def get_threads_per_task(self, job):
        if not isinstance(job.threads, str):
            return ""
        else:
            return '#PBS -l EC_threads_per_task={0}'.format(job.threads)

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
            return "#PBS -l EC_memory_per_task={0}mb".format(job.parameters['MEMORY_PER_TASK'])
        return ""

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_hyperthreading_directive(self, job):
        """
        Returns hyperthreading directive for the specified job

        :param job: job to create hyperthreading directive for
        :type job: Job
        :return: hyperthreading per task directive
        :rtype: str
        """
        # There is no memory per task, so directive is empty
        if job.parameters['CURRENT_HYPERTHREADING'] == 'true':
            return "#PBS -l EC_hyperthreads=2"
        return "#PBS -l EC_hyperthreads=1"

    SERIAL = textwrap.dedent("""\
             ###############################################################################
             #                   %TASKTYPE% %EXPID% EXPERIMENT
             ###############################################################################
             #
             #PBS -N %JOBNAME%
             #PBS -o %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%OUT_LOG_DIRECTIVE%
             #PBS -e %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%ERR_LOG_DIRECTIVE%
             #PBS -q ns
             #PBS -l walltime=%WALLCLOCK%:00
             #PBS -l EC_billing_account=%CURRENT_BUDG%
             #
             ###############################################################################

            """)

    PARALLEL = textwrap.dedent("""\
             ###############################################################################
             #                   %TASKTYPE% %EXPID% EXPERIMENT
             ###############################################################################
             #
             #PBS -N %JOBNAME%
             #PBS -o %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%OUT_LOG_DIRECTIVE%
             #PBS -e %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%ERR_LOG_DIRECTIVE%
             #PBS -q np
             #PBS -l EC_total_tasks=%NUMPROC%
             %THREADS_PER_TASK_DIRECTIVE%
             %TASKS_PER_NODE_DIRECTIVE%
             %MEMORY_PER_TASK_DIRECTIVE%
             %HYPERTHREADING_DIRECTIVE%
             #PBS -l walltime=%WALLCLOCK%:00
             #PBS -l EC_billing_account=%CURRENT_BUDG%
             #
             ###############################################################################
            """)
