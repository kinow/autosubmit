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
import textwrap


class Status:
    """
    Class to handle the status of a job
    """
    WAITING = 0
    READY = 1
    SUBMITTED = 2
    QUEUING = 3
    RUNNING = 4
    COMPLETED = 5
    FAILED = -1
    UNKNOWN = -2
    SUSPENDED = -3

    def retval(self, value):
        return getattr(self, value)


# noinspection PyPep8
class StatisticsSnippet:
    """
    Class to handle the statistics snippet of a job. It contains header and tailer for
    local and remote jobs
    """

    AS_HEADER_LOC = textwrap.dedent("""\

            ###################
            # Autosubmit header
            ###################

            set -x
            job_name_ptrn=%CURRENT_ROOTDIR%/tmp/LOG_%EXPID%/%JOBNAME%
            job_cmd_stamp=$(stat -c %Z $job_name_ptrn.cmd)
            job_start_time=$(date +%s)

            rm -f ${job_name_ptrn}_COMPLETED

            ###################
            # Autosubmit job
            ###################

            """)

    # noinspection PyPep8
    AS_TAILER_LOC = textwrap.dedent("""\
            ###################
            # Autosubmit tailer
            ###################

            set -x
            job_end_time=$(date +%s)
            job_run_time=$((job_end_time - job_start_time))
            errfile_ptrn="\.e"

            failed_jobs=$(($(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | wc -l) - 1))
            failed_errfiles=$(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | head -n $failed_jobs)
            failed_jobs_rt=0

            for failed_errfile in $failed_errfiles; do
                failed_errfile_stamp=$(stat -c %Z $failed_errfile)
                failed_jobs_rt=$((failed_jobs_rt + $((failed_errfile_stamp - $(grep "job_start_time=" $failed_errfile | head -n 2 | tail -n 1 | cut -d '=' -f 2)))))
            done
            echo "$job_end_time 0 $job_run_time $failed_jobs 0 $failed_jobs_rt" > ${job_name_ptrn}_COMPLETED
            exit 0
            """)

    AS_HEADER_REM = textwrap.dedent("""\

            ###################
            # Autosubmit header
            ###################

            set -x
            job_name_ptrn=%CURRENT_ROOTDIR%/%JOBNAME%
            job_cmd_stamp=$(stat -c %Z $job_name_ptrn.cmd)
            job_start_time=$(date +%s)

            rm -f ${job_name_ptrn}_COMPLETED

            ###################
            # Autosubmit job
            ###################

            """)

    # noinspection PyPep8
    AS_TAILER_REM = textwrap.dedent("""\
            ###################
            # Autosubmit tailer
            ###################

            set -x
            job_end_time=$(date +%s)
            job_run_time=$((job_end_time - job_start_time))
            errfile_ptrn="\.e"

            failed_jobs=$(($(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | wc -l) - 1))
            failed_errfiles=$(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | head -n $failed_jobs)
            failed_jobs_rt=0

            for failed_errfile in $failed_errfiles; do
                failed_errfile_stamp=$(stat -c %Z $failed_errfile)
                failed_jobs_rt=$((failed_jobs_rt + $((failed_errfile_stamp - $(grep "job_start_time=" $failed_errfile | head -n 2 | tail -n 1 | cut -d '=' -f 2)))))
            done
            echo "$job_end_time 0 $job_run_time $failed_jobs 0 $failed_jobs_rt" > ${job_name_ptrn}_COMPLETED
            exit 0
            """)
