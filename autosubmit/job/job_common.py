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
import os
import datetime


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
class StatisticsSnippetBash:
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
            echo "
            $job_end_time 0 $job_run_time $failed_jobs 0 $failed_jobs_rt" > ${job_name_ptrn}_COMPLETED
            exit 0
            """)

    AS_HEADER_REM = textwrap.dedent("""\

            ###################
            # Autosubmit header
            ###################

            set -x
            job_name_ptrn=%CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%JOBNAME%
            job_cmd_stamp=$(stat -c %Z $job_name_ptrn.cmd)
            job_start_time=$(date +%s)
            job_queue_time=$((job_start_time - job_cmd_stamp))

            if [[ %CURRENT_TYPE% == ecaccess ]]; then
              hpcversion=%CURRENT_VERSION%
              if [[ ! -z ${hpcversion+x} ]]; then
                if [[ $hpcversion == pbs ]]; then
                  filein="$(ls -rt %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/.ecaccess_DO_NOT_REMOVE/job.i* | xargs grep -l %JOBNAME% | tail -1)"
                  jobid="$(echo "$filein" | cut -d. -f3 | cut -c2-)"
                  fileout="%CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/.ecaccess_DO_NOT_REMOVE/job.o"$jobid"_0"
                  ln -s ${fileout} ${job_name_ptrn}_${jobid}.out
                  fileerr="%CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/.ecaccess_DO_NOT_REMOVE/job.e"$jobid"_0"
                  ln -s ${fileerr} ${job_name_ptrn}_${jobid}.err
                fi
              fi
            fi

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
            case %CURRENT_TYPE% in
             sge)       errfile_created="TRUE"; errfile_ptrn="\.e" ;;
             lsf)       errfile_created="TRUE"; errfile_ptrn="\.err" ;;
             ecaccess)  errfile_created="TRUE"; errfile_ptrn="\.err" ;;
             pbs)       errfile_created="FALSE"; errfile_ptrn="\.e" ;;
             slurm)     errfile_created="TRUE"; errfile_ptrn="\.err" ;;
             ps)        errfile_created="TRUE"; errfile_ptrn="\.err" ;;
             *) echo "!!! %CURRENT_TYPE% is not valid scheduler !!!"; exit 1 ;;
            esac
            failed_jobs=0; failed_errfiles=""
            set +e; ls -1 ${job_name_ptrn}* | grep $errfile_ptrn
            if [[ $? -eq 0 ]]; then
             case $errfile_created in
              TRUE)
                failed_jobs=$(($(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | wc -l) - 1))
                failed_errfiles=$(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | head -n $failed_jobs)
              ;;
              FALSE)
                failed_jobs=$(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | wc -l)
                failed_errfiles=$(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn)
              ;;
              *) "!!! $errfile_created is not valid errfile_created option !!!"; exit 1 ;;
             esac
            fi; set -e
            failed_jobs_qt=0; failed_jobs_rt=0
            for failed_errfile in $failed_errfiles; do
             failed_errfile_stamp=$(stat -c %Z $failed_errfile)
             job_qt=$(grep "job_queue_time=" $failed_errfile | head -n 2 | tail -n 1 | cut -d '=' -f 2)
             if [[ ! -z ${job_qt+x} ]]; then
               job_qt=0
             fi
             failed_jobs_qt=$((failed_jobs_qt + job_qt))
             job_st=$(grep "job_start_time=" $failed_errfile | head -n 2 | tail -n 1 | cut -d '=' -f 2)
             if [[ ! -z ${job_qt+x} ]]; then
               job_st=0
             fi
             failed_jobs_rt=$((failed_jobs_rt + $((failed_errfile_stamp - job_st))))
            done

            echo "$job_end_time $job_queue_time $job_run_time $failed_jobs $failed_jobs_qt $failed_jobs_rt" > ${job_name_ptrn}_COMPLETED
            exit 0
            """)


# noinspection PyPep8
class StatisticsSnippetPython:
    """
    Class to handle the statistics snippet of a job. It contains header and tailer for
    local and remote jobs
    """

    AS_HEADER_LOC = textwrap.dedent("""\

            ###################
            # Autosubmit header
            ###################

            job_name_ptrn='%CURRENT_ROOTDIR%/tmp/LOG_%EXPID%/%JOBNAME%'
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
            echo "
            $job_end_time 0 $job_run_time $failed_jobs 0 $failed_jobs_rt" > ${job_name_ptrn}_COMPLETED
            exit 0
            """)

    AS_HEADER_REM = textwrap.dedent("""\

            ###################
            # Autosubmit header
            ###################

            set -x
            job_name_ptrn=%CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%JOBNAME%
            job_cmd_stamp=$(stat -c %Z $job_name_ptrn.cmd)
            job_start_time=$(date +%s)
            job_queue_time=$((job_start_time - job_cmd_stamp))

            if [[ %CURRENT_TYPE% == ecaccess ]]; then
              hpcversion=%CURRENT_VERSION%
              if [[ ! -z ${hpcversion+x} ]]; then
                if [[ $hpcversion == pbs ]]; then
                  filein="$(ls -rt %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/.ecaccess_DO_NOT_REMOVE/job.i* | xargs grep -l %JOBNAME% | tail -1)"
                  jobid="$(echo "$filein" | cut -d. -f3 | cut -c2-)"
                  fileout="%CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/.ecaccess_DO_NOT_REMOVE/job.o"$jobid"_0"
                  ln -s ${fileout} ${job_name_ptrn}_${jobid}.out
                  fileerr="%CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/.ecaccess_DO_NOT_REMOVE/job.e"$jobid"_0"
                  ln -s ${fileerr} ${job_name_ptrn}_${jobid}.err
                fi
              fi
            fi

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
            case %CURRENT_TYPE% in
             sge)       errfile_created="TRUE"; errfile_ptrn="\.e" ;;
             lsf)       errfile_created="TRUE"; errfile_ptrn="\.err" ;;
             ecaccess)  errfile_created="TRUE"; errfile_ptrn="\.err" ;;
             pbs)       errfile_created="FALSE"; errfile_ptrn="\.e" ;;
             slurm)     errfile_created="TRUE"; errfile_ptrn="\.err" ;;
             ps)        errfile_created="TRUE"; errfile_ptrn="\.err" ;;
             *) echo "!!! %CURRENT_TYPE% is not valid scheduler !!!"; exit 1 ;;
            esac
            failed_jobs=0; failed_errfiles=""
            set +e; ls -1 ${job_name_ptrn}* | grep $errfile_ptrn
            if [[ $? -eq 0 ]]; then
             case $errfile_created in
              TRUE)
                failed_jobs=$(($(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | wc -l) - 1))
                failed_errfiles=$(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | head -n $failed_jobs)
              ;;
              FALSE)
                failed_jobs=$(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | wc -l)
                failed_errfiles=$(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn)
              ;;
              *) "!!! $errfile_created is not valid errfile_created option !!!"; exit 1 ;;
             esac
            fi; set -e
            failed_jobs_qt=0; failed_jobs_rt=0
            for failed_errfile in $failed_errfiles; do
             failed_errfile_stamp=$(stat -c %Z $failed_errfile)
             job_qt=$(grep "job_queue_time=" $failed_errfile | head -n 2 | tail -n 1 | cut -d '=' -f 2)
             if [[ ! -z ${job_qt+x} ]]; then
               job_qt=0
             fi
             failed_jobs_qt=$((failed_jobs_qt + job_qt))
             job_st=$(grep "job_start_time=" $failed_errfile | head -n 2 | tail -n 1 | cut -d '=' -f 2)
             if [[ ! -z ${job_qt+x} ]]; then
               job_st=0
             fi
             failed_jobs_rt=$((failed_jobs_rt + $((failed_errfile_stamp - job_st))))
            done

            echo "$job_end_time $job_queue_time $job_run_time $failed_jobs $failed_jobs_qt $failed_jobs_rt" > ${job_name_ptrn}_COMPLETED
            exit 0
            """)


####################
# Main Program
####################
def main():
    job_start_time = datetime.datetime.now()
    log_directory = '/home/Earth/jvegas/debug/autosubmit/a000/tmp/LOG_a000'
    job_name_ptrn = os.path.join(log_directory, 'a000_LOCAL_SETUP')
    job_stamp = datetime.datetime.fromtimestamp(os.path.getmtime('{0}.cmd'.format(job_name_ptrn)))

    try:
        os.remove('{0}_COMPLETED'.format(job_name_ptrn))
    except OSError:
        pass

    ###################
    # Autosubmit job
    ###################

    ###################
    # Autosubmit tailer
    ###################

    job_end_time = datetime.datetime.now()
    job_run_time = job_end_time - job_start_time

    failed_errfiles = [filename for filename in os.listdir(log_directory)
                       if os.path.isfile(os.path.join(log_directory, filename)) and '.e' in filename]

    failed_jobs = 0
    failed_jobs_rt = 0

    for failed_errfile in failed_errfiles:
        failed_err_stamp = datetime.datetime.fromtimestamp(os.path.getmtime('{0}'.format(os.path.join(log_directory,
                                                                                                      failed_errfile))))
        failed_jobs += 1

    file_completed = open('{0}_COMPLETED'.format(job_name_ptrn), 'w')
    queued_time = job_start_time - job_stamp
    file_completed.write('{0} {1} {2} {3} {4} {5}'.format(job_end_time, queued_time, job_run_time,
                                                          failed_jobs, 0, failed_jobs_rt))
    file_completed.flush()
    file_completed.close()

    return 0

if __name__ == "__main__":
    main()
