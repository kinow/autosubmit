#!/usr/bin/env python3

# Copyright 2017-2020 Earth Sciences Department, BSC-CNS

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


class SlurmHeader(object):
    """Class to handle the SLURM headers of a job"""

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_queue_directive(self, job, het=-1):
        """
        Returns queue directive for the specified job

        :param job: job to create queue directive for
        :type job: Job
        :return: queue directive
        :rtype: str
        """
        # There is no queue, so directive is empty
        if het > -1 and len(job.het['CURRENT_QUEUE']) > 0:
            if job.het['CURRENT_QUEUE'][het] != '':
                return "SBATCH --qos={0}".format(job.het['CURRENT_QUEUE'][het])
        else:
            if job.parameters['CURRENT_QUEUE'] != '':
                return "SBATCH --qos={0}".format(job.parameters['CURRENT_QUEUE'])
    def get_proccesors_directive(self, job, het=-1):
        """
        Returns processors directive for the specified job

        :param job: job to create processors directive for
        :type job: Job
        :return: processors directive
        :rtype: str
        """
        if het > -1 and len(job.het['NODES']) > 0:
            if job.het['NODES'][het] == '':
                job_nodes = 0
            else:
                job_nodes = job.het['NODES'][het]
            if job.het['PROCESSORS'][het] == '' or job.het['PROCESSORS'][het] == '1' and int(job_nodes) > 1:
                return ""
            else:
                return "SBATCH -n {0}".format(job.het['PROCESSORS'][het])
        if job.nodes == "":
            job_nodes = 0
        else:
            job_nodes = job.nodes
        if job.processors == '' or job.processors == '1' and int(job_nodes) > 1:
            return ""
        else:
            return "SBATCH -n {0}".format(job.processors)


    def get_tasks_directive(self,job, het=-1):
        """
        Returns tasks directive for the specified job
        :param job: job to create tasks directive for
        :return: tasks directive
        :rtype: str
        """
        if het > -1 and len(job.het['TASKS']) > 0:
            if job.het['TASKS'][het] != '':
                return "SBATCH --ntasks-per-node={0}".format(job.het['TASKS'][het])
        else:
            if job.parameters['TASKS'] != '':
                return "SBATCH --ntasks-per-node={0}".format(job.parameters['TASKS'])
        return ""
    def get_partition_directive(self, job, het=-1):
        """
        Returns partition directive for the specified job

        :param job: job to create partition directive for
        :type job: Job
        :return: partition directive
        :rtype: str
        """
        if het > -1 and len(job.het['PARTITION']) > 0:
            if job.het['PARTITION'][het] != '':
                return "SBATCH --partition={0}".format(job.het['PARTITION'][het])
        else:
            if job.partition != '':
                return "SBATCH --partition={0}".format(job.partition)
        return ""
    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_account_directive(self, job, het=-1):
        """
        Returns account directive for the specified job

        :param job: job to create account directive for
        :type job: Job
        :return: account directive
        :rtype: str
        """
        if het > -1 and len(job.het['CURRENT_PROJ']) > 0:
            if job.het['CURRENT_PROJ'][het] != '':
                return "SBATCH -A {0}".format(job.het['CURRENT_PROJ'][het])
        else:
            if job.parameters['CURRENT_PROJ'] != '':
                return "SBATCH -A {0}".format(job.parameters['CURRENT_PROJ'])
        return ""
    def get_exclusive_directive(self, job, het=-1):
        """
        Returns account directive for the specified job

        :param job: job to create account directive for
        :type job: Job
        :return: account directive
        :rtype: str
        """
        if het > -1 and len(job.het['EXCLUSIVE']) > 0:
            if job.het['EXCLUSIVE'][het] != '':
                return "SBATCH --exclusive"
        else:
            if job.parameters['EXCLUSIVE'] != '':
                return "SBATCH --exclusive"
        return ""

    def get_nodes_directive(self, job, het=-1):
        """
        Returns nodes directive for the specified job
        :param job: job to create nodes directive for
        :type job: Job
        :return: nodes directive
        :rtype: str
        """
        if het > -1 and len(job.het['NODES']) > 0:
            if job.het['NODES'][het] != '':
                return "SBATCH --nodes={0}".format(job.het['NODES'][het])
        else:
            if job.parameters['NODES'] != '':
                return "SBATCH --nodes={0}".format(job.parameters['NODES'])
        return ""
    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_memory_directive(self, job, het=-1):
        """
        Returns memory directive for the specified job

        :param job: job to create memory directive for
        :type job: Job
        :return: memory directive
        :rtype: str
        """
        if het > -1 and len(job.het['MEMORY']) > 0:
            if job.het['MEMORY'][het] != '':
                return "SBATCH --mem={0}".format(job.het['MEMORY'][het])
        else:
            if job.parameters['MEMORY'] != '':
                return "SBATCH --mem={0}".format(job.parameters['MEMORY'])
        return ""

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_memory_per_task_directive(self, job, het=-1):
        """
        Returns memory per task directive for the specified job

        :param job: job to create memory per task directive for
        :type job: Job
        :return: memory per task directive
        :rtype: str
        """
        if het > -1 and len(job.het['MEMORY_PER_TASK']) > 0:
            if job.het['MEMORY_PER_TASK'][het] != '':
                return "SBATCH --mem-per-cpu={0}".format(job.het['MEMORY_PER_TASK'][het])
        else:
            if job.parameters['MEMORY_PER_TASK'] != '':
                return "SBATCH --mem-per-cpu={0}".format(job.parameters['MEMORY_PER_TASK'])
        return ""
    def get_threads_per_task(self, job, het=-1):
        """
        Returns threads per task directive for the specified job

        :param job: job to create threads per task directive for
        :type job: Job
        :return: threads per task directive
        :rtype: str
        """
        # There is no threads per task, so directive is empty
        if het > -1 and len(job.het['NUMTHREADS']) > 0:
            if job.het['NUMTHREADS'][het] != '':
                return f"SBATCH --cpus-per-task={job.het['NUMTHREADS'][het]}"
        else:
            if job.parameters['NUMTHREADS'] != '':
                return "SBATCH --cpus-per-task={0}".format(job.parameters['NUMTHREADS'])
        return ""

    # noinspection PyMethodMayBeStatic,PyUnusedLocal

    def get_reservation_directive(self, job, het=-1):
        """
        Returns reservation directive for the specified job
        :param job:
        :param het:
        :return:
        """

        if het > -1 and len(job.het['RESERVATION']) > 0:
            if job.het['RESERVATION'][het] != '':
                return "SBATCH --reservation={0}".format(job.het['RESERVATION'][het])
        else:
            if job.parameters['RESERVATION'] != '':
                return "SBATCH --reservation={0}".format(job.parameters['RESERVATION'])
        return ""

    def get_custom_directives(self, job, het=-1):
        """
        Returns custom directives for the specified job

        :param job: job to create custom directive for
        :type job: Job
        :return: custom directives
        :rtype: str
        """
        # There is no custom directives, so directive is empty
        if het > -1 and len(job.het['CUSTOM_DIRECTIVES']) > 0:
            if job.het['CUSTOM_DIRECTIVES'][het] != '':
                return '\n'.join(str(s) for s in job.het['CUSTOM_DIRECTIVES'][het])
        else:
            if job.parameters['CUSTOM_DIRECTIVES'] != '':
                return '\n'.join(str(s) for s in job.parameters['CUSTOM_DIRECTIVES'])
        return ""



    def get_tasks_per_node(self, job, het=-1):
        """
        Returns memory per task directive for the specified job

        :param job: job to create tasks per node directive for
        :type job: Job
        :return: tasks per node directive
        :rtype: str
        """
        if het > -1 and len(job.het['TASKS']) > 0:
            if int(job.het['TASKS'][het]):
                return "SBATCH --tasks-per-node={0}".format(job.het['TASKS'][het])
        else:
            if int(job.parameters['TASKS']) > 1:
                return "SBATCH --tasks-per-node={0}".format(job.parameters['TASKS'])
        return ""

    def calculate_het_header(self, job):
        header = textwrap.dedent("""\
        ###############################################################################
        #                   %TASKTYPE% %DEFAULT.EXPID% EXPERIMENT
        ###############################################################################
        #                   Common directives
        ###############################################################################
        #
        #SBATCH -t %WALLCLOCK%:00
        #SBATCH -J %JOBNAME%
        #SBATCH --output=%CURRENT_SCRATCH_DIR%/%CURRENT_PROJ_DIR%/%CURRENT_USER%/%DEFAULT.EXPID%/LOG_%DEFAULT.EXPID%/%OUT_LOG_DIRECTIVE%
        #SBATCH --error=%CURRENT_SCRATCH_DIR%/%CURRENT_PROJ_DIR%/%CURRENT_USER%/%DEFAULT.EXPID%/LOG_%DEFAULT.EXPID%/%ERR_LOG_DIRECTIVE%
        #%X11%
        #
            """)
        if job.x11 == "true":
            header = header.replace(
                '%X11%', "SBATCH --x11=batch")
        for components in range(job.het['HETSIZE']):
            header += textwrap.dedent(f"""\
            ###############################################################################
            #                 HET_GROUP:{components} 
            ###############################################################################
            #%QUEUE_DIRECTIVE_{components}%
            #%PARTITION_DIRECTIVE_{components}%
            #%ACCOUNT_DIRECTIVE_{components}%
            #%MEMORY_DIRECTIVE_{components}%
            #%MEMORY_PER_TASK_DIRECTIVE_{components}%
            #%THREADS_PER_TASK_DIRECTIVE_{components}%
            #%NODES_DIRECTIVE_{components}%
            #%NUMPROC_DIRECTIVE_{components}%
            #%RESERVATION_DIRECTIVE_{components}%
            #%TASKS_PER_NODE_DIRECTIVE_{components}%
            %CUSTOM_DIRECTIVES_{components}%
            #SBATCH hetjob
            """)

            header = header.replace(
                f'%QUEUE_DIRECTIVE_{components}%', self.get_queue_directive(job, components))
            header = header.replace(
                f'%PARTITION_DIRECTIVE_{components}%', self.get_partition_directive(job, components))
            header = header.replace(
                f'%ACCOUNT_DIRECTIVE_{components}%', self.get_account_directive(job, components))
            header = header.replace(
                f'%MEMORY_DIRECTIVE_{components}%', self.get_memory_directive(job, components))
            header = header.replace(
                f'%MEMORY_PER_TASK_DIRECTIVE_{components}%', self.get_memory_per_task_directive(job, components))
            header = header.replace(
                f'%THREADS_PER_TASK_DIRECTIVE_{components}%', self.get_threads_per_task(job, components))
            header = header.replace(
                f'%NODES_DIRECTIVE_{components}%', self.get_nodes_directive(job, components))
            header = header.replace(
                f'%NUMPROC_DIRECTIVE_{components}%', self.get_proccesors_directive(job, components))
            header = header.replace(
                f'%RESERVATION_DIRECTIVE_{components}%', self.get_reservation_directive(job, components))
            header = header.replace(
                f'%TASKS_PER_NODE_DIRECTIVE_{components}%', self.get_tasks_per_node(job, components))
            header = header.replace(
                f'%CUSTOM_DIRECTIVES_{components}%', self.get_custom_directives(job, components))
        header = header[:-len("#SBATCH hetjob\n")]  # last element

        return header


    SERIAL = textwrap.dedent("""\
###############################################################################
#                   %TASKTYPE% %DEFAULT.EXPID% EXPERIMENT
###############################################################################
#
#%QUEUE_DIRECTIVE%
#%PARTITION_DIRECTIVE%
#%ACCOUNT_DIRECTIVE%
#%MEMORY_DIRECTIVE%
#%THREADS_PER_TASK_DIRECTIVE%
#%TASKS_PER_NODE_DIRECTIVE%
#%NODES_DIRECTIVE%
#%NUMPROC_DIRECTIVE%
#%RESERVATION_DIRECTIVE%
#SBATCH -t %WALLCLOCK%:00
#SBATCH -J %JOBNAME%
#SBATCH --output=%CURRENT_SCRATCH_DIR%/%CURRENT_PROJ_DIR%/%CURRENT_USER%/%DEFAULT.EXPID%/LOG_%DEFAULT.EXPID%/%OUT_LOG_DIRECTIVE%
#SBATCH --error=%CURRENT_SCRATCH_DIR%/%CURRENT_PROJ_DIR%/%CURRENT_USER%/%DEFAULT.EXPID%/LOG_%DEFAULT.EXPID%/%ERR_LOG_DIRECTIVE%
%CUSTOM_DIRECTIVES%
#%X11%
#
###############################################################################
           """)

    PARALLEL = textwrap.dedent("""\
###############################################################################
#                   %TASKTYPE% %DEFAULT.EXPID% EXPERIMENT
###############################################################################
#
#%QUEUE_DIRECTIVE%
#%PARTITION_DIRECTIVE%
#%ACCOUNT_DIRECTIVE%
#%MEMORY_DIRECTIVE%
#%MEMORY_PER_TASK_DIRECTIVE%
#%THREADS_PER_TASK_DIRECTIVE%
#%NODES_DIRECTIVE%
#%NUMPROC_DIRECTIVE%
#%RESERVATION_DIRECTIVE%
#%TASKS_PER_NODE_DIRECTIVE%
#SBATCH -t %WALLCLOCK%:00
#SBATCH -J %JOBNAME%
#SBATCH --output=%CURRENT_SCRATCH_DIR%/%CURRENT_PROJ_DIR%/%CURRENT_USER%/%DEFAULT.EXPID%/LOG_%DEFAULT.EXPID%/%OUT_LOG_DIRECTIVE%
#SBATCH --error=%CURRENT_SCRATCH_DIR%/%CURRENT_PROJ_DIR%/%CURRENT_USER%/%DEFAULT.EXPID%/LOG_%DEFAULT.EXPID%/%ERR_LOG_DIRECTIVE%
%CUSTOM_DIRECTIVES%
#%X11%
#
###############################################################################
    """)

