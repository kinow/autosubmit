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


class Pbs12Header(object):
    """Class to handle the Archer headers of a job"""

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

    SERIAL = textwrap.dedent("""\
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
