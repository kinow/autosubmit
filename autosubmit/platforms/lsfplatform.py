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

from autosubmit.platforms.paramiko_platform import ParamikoPlatform


class LsfPlatform(ParamikoPlatform):
    """
    Class to manage jobs to host using LSF scheduler

    :param expid: experiment's identifier
    :type expid: str
    """
    def __init__(self, expid, name, config):
        ParamikoPlatform.__init__(self, expid, name, config)
        self._header = LsfHeader()
        self.job_status = dict()
        self.job_status['COMPLETED'] = ['DONE']
        self.job_status['RUNNING'] = ['RUN']
        self.job_status['QUEUING'] = ['PEND', 'FW_PEND']
        self.job_status['FAILED'] = ['SSUSP', 'USUSP', 'EXIT']
        self._allow_arrays = True
        self.update_cmds()

    def update_cmds(self):
        """
        Updates commands for platforms
        """
        self.root_dir = os.path.join(self.scratch, self.project, self.user, self.expid)
        self.remote_log_dir = os.path.join(self.root_dir, "LOG_" + self.expid)
        self.cancel_cmd = "bkill"
        self._checkjob_cmd = "bjobs "
        self._checkhost_cmd = "echo 1"
        self._submit_cmd = "bsub -cwd " + self.remote_log_dir + " < " + self.remote_log_dir + "/"
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
        job_state = output.split('\n')
        if len(job_state) > 1:
            job_state = job_state[1].split()
            if len(job_state) > 2:
                return job_state[2]
        # If we can not process output, assuming completed. Then we will look for completed files and status will
        # change to failed if COMPLETED file is not present.
        return 'DONE'

    def get_submitted_job_id(self, output):
        return output.split('<')[1].split('>')[0]

    def jobs_in_queue(self):
        return zip(*[line.split() for line in ''.split('\n')])[0][1:]

    def get_checkjob_cmd(self, job_id):
        return self._checkjob_cmd + str(job_id)

    def get_submit_cmd(self, job_script, job):
        return self._submit_cmd + job_script


class LsfHeader:
    """Class to handle the MareNostrum3 headers of a job"""

    # noinspection PyMethodMayBeStatic
    def get_queue_directive(self, job):
        """
        Returns queue directive for the specified job

        :param job: job to create queue directive for
        :type job: Job
        :return: queue directive
        :rtype: str
        """
        if job.parameters['CURRENT_QUEUE'] == '':
            return ""
        else:
            return "BSUB -q {0}".format(job.parameters['CURRENT_QUEUE'])

    # noinspection PyMethodMayBeStatic
    def get_scratch_free_space(self, job):
        if not isinstance(job.scratch_free_space, int):
            return ""
        else:
            return '#BSUB -R "select[(scratch<{0})]"'.format(job.scratch_free_space)

    # noinspection PyMethodMayBeStatic
    def get_tasks_per_node(self, job):
        if not isinstance(job.tasks, int):
            return ""
        else:
            return '#BSUB -R "span[ptile={0}]"'.format(job.tasks)

    # noinspection PyMethodMayBeStatic
    def get_exclusivity(self, job):
        if job.platform.exclusivity == 'true':
            return "#BSUB -x"
        else:
            return ""

    @classmethod
    def array_header(cls, filename, array_id, wallclock, num_processors):
        return textwrap.dedent("""\
            ###############################################################################
            #              {0}
            ###############################################################################
            #
            #
            #BSUB -J {0}{1}
            #BSUB -oo {0}.%I.out
            #BSUB -eo {0}.%I.err
            #BSUB -W {2}
            #BSUB -n {3}
            #
            ###############################################################################

            SCRIPT=$(cat {0}.$LSB_JOBINDEX | awk 'NR==1')
            chmod +x $SCRIPT
            ./$SCRIPT
            """.format(filename, array_id, wallclock, num_processors))

    @classmethod
    def thread_header(cls, filename, wallclock, num_processors, num_jobs, job_scripts):
        return textwrap.dedent("""\
            #!/usr/bin/env python
            ###############################################################################
            #              {0}
            ###############################################################################
            #
            #BSUB -J {0}
            #BSUB -o {0}.out
            #BSUB -e {0}.err
            #BSUB -W {1}
            #BSUB -n {2}
            #
            ###############################################################################

            import os
            import sys
            from threading import Thread
            from commands import getstatusoutput

            class JobThread(Thread):
                def __init__ (self, template, id_run):
                    Thread.__init__(self)
                    self.template = template
                    self.id_run = id_run

                def run(self):
                    out = str(self.template) + '.' + str(self.id_run) + '.out'
                    err = str(self.template) + '.' + str(self.id_run) + '.err'
                    command = str(self.template) + ' ' + str(self.id_run) + ' ' + os.getcwd()
                    (self.status) = getstatusoutput(command + ' > ' + out + ' 2> ' + err)

            scripts = {3}

            for i in range(len(scripts)):
                current = JobThread(scripts[i], i)
                current.start()
                current.join()
                completed_filename = scripts[i].replace('.cmd', '_COMPLETED')
                completed_path = os.path.join(os.getcwd(), completed_filename)
                if os.path.exists(completed_path):
                    print "The job ", current.template," has been COMPLETED"
                else:
                    print "The job ", current.template," has FAILED"
                    os._exit(1)
            """.format(filename, wallclock, num_processors, str(job_scripts)))

    SERIAL = textwrap.dedent("""\
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #%QUEUE_DIRECTIVE%
            #BSUB -J %JOBNAME%
            #BSUB -oo %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%OUT_LOG_DIRECTIVE%
            #BSUB -eo %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%ERR_LOG_DIRECTIVE%
            #BSUB -W %WALLCLOCK%
            #BSUB -n %NUMPROC%
            %EXCLUSIVITY_DIRECTIVE%
            #
            ###############################################################################
            """)

    PARALLEL = textwrap.dedent("""\
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            #
            #%QUEUE_DIRECTIVE%
            #BSUB -J %JOBNAME%
            #BSUB -oo %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%OUT_LOG_DIRECTIVE%
            #BSUB -eo %CURRENT_SCRATCH_DIR%/%CURRENT_PROJ%/%CURRENT_USER%/%EXPID%/LOG_%EXPID%/%ERR_LOG_DIRECTIVE%
            #BSUB -W %WALLCLOCK%
            #BSUB -n %NUMPROC%
            %TASKS_PER_NODE_DIRECTIVE%
            %SCRATCH_FREE_SPACE_DIRECTIVE%
            #
            ###############################################################################
            """)