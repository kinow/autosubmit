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

"""
Main module for autosubmit. Only contains an interface class to all functionality implemented on autosubmit
"""

import os
import re

from autosubmit.job.job_common import Status
from autosubmit.job.job_common import StatisticsSnippet
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.date.chunk_date_lib import *
from autosubmit.platforms.localplatform import LocalPlatform


class Job:
    """
    Class to handle all the tasks with Jobs at HPC.
    A job is created by default with a name, a jobid, a status and a type.
    It can have children and parents. The inheritance reflects the dependency between jobs.
    If Job2 must wait until Job1 is completed then Job2 is a child of Job1. Inversely Job1 is a parent of Job2

    :param name: job's name
    :type name: str
    :param jobid: job's identifier
    :type jobid: int
    :param status: job inicial status
    :type status: Status
    :param priority: job's priority
    :type priority: int
    """

    def __str__(self):
        return self.name

    def __init__(self, name, jobid, status, priority):
        self._platform = None
        self._queue = None
        self.platform_name = None
        self.section = None
        self.wallclock = None
        self.tasks = None
        self.threads = None
        self.processors = None
        self.chunk = None
        self.member = None
        self.date = None
        self.name = name
        self._long_name = None
        self.long_name = name
        self._short_name = None
        self.short_name = name
        self.date_format = ''

        self.id = jobid
        self.file = None
        self.status = status
        self.priority = priority
        self._parents = set()
        self._children = set()
        self.fail_count = 0
        self.expid = name.split('_')[0]
        self._complete = True
        self.parameters = dict()
        self._tmp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.expid, BasicConfig.LOCAL_TMP_DIR)
        self._ancestors = None

    def __getstate__(self):
        odict = self.__dict__
        if '_platform' in odict:
            odict = odict.copy()    # copy the dict since we change it
            del odict['_platform']              # remove filehandle entry
        return odict

    def print_job(self):
        """
        Prints debug information about the job
        """
        Log.debug('NAME: {0}', self.name)
        Log.debug('JOBID: {0}', self.id)
        Log.debug('STATUS: {0}', self.status)
        Log.debug('TYPE: {0}', self.priority)
        Log.debug('PARENTS: {0}', [p.name for p in self.parents])
        Log.debug('CHILDREN: {0}', [c.name for c in self.children])
        Log.debug('FAIL_COUNT: {0}', self.fail_count)
        Log.debug('EXPID: {0}', self.expid)

    # Properties
    @property
    def parents(self):
        """
        Return parent jobs list

        :return: parent jobs
        :rtype: set
        """
        return self._parents

    def get_platform(self):
        """
        Returns the platforms to be used by the job. Chooses between serial and parallel platforms

        :return HPCPlatform object for the job to use
        :rtype: HPCPlatform
        """
        if self.processors > 1:
            return self._platform
        else:
            return self._platform.get_serial_platform()

    def set_platform(self, value):
        """
        Sets the HPC platforms to be used by the job.

        :param value: platforms to set
        :type value: HPCPlatform
        """
        self._platform = value

    def get_queue(self):
        """
        Returns the queue to be used by the job. Chooses between serial and parallel platforms

        :return HPCPlatform object for the job to use
        :rtype: HPCPlatform
        """
        if self._queue is not None:
            return self._queue
        if self.processors > 1:
            return self._platform.get_queue()
        else:
            return self._platform.get_serial_platform().get_serial_queue()

    def set_queue(self, value):
        """
        Sets the queue to be used by the job.

        :param value: queue to set
        :type value: HPCPlatform
        """
        self._queue = value

    @property
    def ancestors(self):
        """
        Returns all job's ancestors

        :return: job ancestors
        :rtype: set
        """
        if self._ancestors is None:
            self._ancestors = set()
            if self.has_parents():
                for parent in self.parents:
                    self._ancestors.add(parent)
                    for ancestor in parent.ancestors:
                        self._ancestors.add(ancestor)
        return self._ancestors

    @property
    def children(self):
        """
        Returns a list containing all children of the job

        :return: child jobs
        :rtype: set
        """
        return self._children

    @property
    def long_name(self):
        """
        Job's long name. If not setted, returns name

        :return: long name
        :rtype: str
        """
        if hasattr(self, '_long_name'):
            return self._long_name
        else:
            return self.name

    @long_name.setter
    def long_name(self, value):
        """
        Sets long name for the job

        :param value: long name to set
        :type value: str
        """
        self._long_name = value

    @property
    def short_name(self):
        """
        Job short name

        :return: short name
        :rtype: str
        """
        return self._short_name

    @short_name.setter
    def short_name(self, value):
        """
        Sets short name

        :param value: short name
        :type value: str
        """
        n = value.split('_')
        if len(n) == 5:
            self._short_name = n[1][:6] + "_" + n[2][2:] + "_" + n[3] + n[4][:1]
        elif len(n) == 4:
            self._short_name = n[1][:6] + "_" + n[2][2:] + "_" + n[3][:1]
        elif len(n) == 2:
            self._short_name = n[1]
        else:
            self._short_name = n[0][:15]

    def log_job(self):
        """
        Prints job information in log
        """
        Log.info("{0}\t{1}\t{2}", "Job Name", "Job Id", "Job Status")
        Log.info("{0}\t\t{1}\t{2}", self.name, self.id, self.status)

    def print_parameters(self):
        """
        Print sjob parameters in log
        """
        Log.info(self.parameters)

    def inc_fail_count(self):
        """
        Increments fail count
        """
        self.fail_count += 1

    def add_parent(self, *new_parent):
        """
        Add parents for the job. It also adds current job as a child for all the new parents

        :param \*new_parent: job parent
        :type \*new_parent: Job
        """
        self._ancestors = None
        for parent in new_parent:
            self._parents.add(parent)
            parent.__add_child(self)

    def __add_child(self, new_child):
        """
        Adds a new child to the job

        :param new_child: new child to add
        :type new_child: Job
        """
        self.children.add(new_child)

    def delete_parent(self, parent):
        """
        Remove a parent from the job

        :param parent: parent to remove
        :type parent: Job
        """
        self._ancestors = None
        # careful, it is only possible to remove one parent at a time
        self.parents.remove(parent)

    def delete_child(self, child):
        """
        Removes a child from the job

        :param child: child to remove
        :type child: Job
        """
        # careful it is only possible to remove one child at a time
        self.children.remove(child)

    def has_children(self):
        """
        Returns true if job has any children, else return false

        :return: true if job has any children, otherwise return false
        :rtype: bool
        """
        return self.children.__len__()

    def has_parents(self):
        """
        Returns true if job has any parents, else return false

        :return: true if job has any parent, otherwise return false
        :rtype: bool
        """
        return self.parents.__len__()

    def compare_by_status(self, other):
        """
        Compare jobs by status value

        :param other: job to compare
        :type other: Job
        :return: comparison result
        :rtype: bool
        """
        return cmp(self.status, other.status)

    def compare_by_id(self, other):
        """
        Compare jobs by ID

        :param other: job to compare
        :type other: Job
        :return: comparison result
        :rtype: bool
        """
        return cmp(self.id, other.id)

    def compare_by_name(self, other):
        """
        Compare jobs by name

        :param other: job to compare
        :type other: Job
        :return: comparison result
        :rtype: bool
        """
        return cmp(self.name, other.name)

    def _get_from_completed(self, index):
        """
        Returns value from given index position in completed file asociated to job

        :param index: position to retrieve
        :type index: int
        :return: value in index position
        :rtype: str
        """
        logname = self._tmp_path + self.name + '_COMPLETED'
        if os.path.exists(logname):
            split_line = open(logname).readline().split()
            if len(split_line) >= index + 1:
                return split_line[index]
            else:
                return 0
        else:
            return 0

    def check_end_time(self):
        """
        Returns end time from completed file

        :return: completed date and time
        :rtype: str
        """
        return self._get_from_completed(0)

    def check_queued_time(self):
        """
        Returns job's waiting time in HPC

        :return: total time waiting in HPC platforms
        :rtype: str
        """
        return self._get_from_completed(1)

    def check_run_time(self):
        """
        Returns job's running time

        :return: total time running
        :rtype: str
        """
        return self._get_from_completed(2)

    def check_failed_times(self):
        """
        Returns number of failed attempts before completing the job

        :return: failed attempts to run
        :rtype: str
        """
        return self._get_from_completed(3)

    def check_fail_queued_time(self):
        """
        Returns total time spent waiting for failed jobs

        :return: total time waiting in HPC platforms for failed jobs
        :rtype: str
        """
        return self._get_from_completed(4)

    def check_fail_run_time(self):
        """
        Returns total time running for failed jobs

        :return: total time running in HPC  for failed jobs
        :rtype: str
        """
        return self._get_from_completed(5)

    def check_completion(self, default_status=Status.FAILED):
        """
        Check the presence of *COMPLETED* file and touch a Checked or failed file.
        Change statis to COMPLETED if *COMPLETED* file exists and to FAILED otherwise.
        """
        logname = os.path.join(self._tmp_path, self.name + '_COMPLETED')
        if os.path.exists(logname):
            self._complete = True
            os.system('touch ' + os.path.join(self._tmp_path, self.name + 'Checked'))
            self.status = Status.COMPLETED
        else:
            os.system('touch ' + os.path.join(self._tmp_path, self.name + 'Failed'))
            self.status = default_status

    def remove_dependencies(self):
        """
        Checks if job is completed and then remove dependencies for childs
        """
        if self._complete:
            self.status = Status.COMPLETED
            for child in self.children:
                if child.get_parents().__contains__(self):
                    child.delete_parent(self)
        else:
            self.status = Status.FAILED

    def update_parameters(self, as_conf):
        """
        Refresh parameters value

        :param as_conf:
        :type as_conf: AutosubmitConfig
        """
        parameters = self.parameters
        parameters['JOBNAME'] = self.name
        parameters['FAIL_COUNT'] = str(self.fail_count)

        parameters['SDATE'] = date2str(self.date, self.date_format)
        parameters['MEMBER'] = self.member
        if self.date is not None:
            if self.chunk is None:
                chunk = 1
            else:
                chunk = self.chunk

            parameters['CHUNK'] = chunk
            total_chunk = int(parameters['NUMCHUNKS'])
            chunk_length = int(parameters['CHUNKSIZE'])
            chunk_unit = parameters['CHUNKSIZEUNIT'].lower()
            cal = parameters['CALENDAR'].lower()
            chunk_start = chunk_start_date(self.date, chunk, chunk_length, chunk_unit, cal)
            chunk_end = chunk_end_date(chunk_start, chunk_length, chunk_unit, cal)
            chunk_end_1 = previous_day(chunk_end, cal)
            parameters['DAY_BEFORE'] = date2str(previous_day(self.date, cal), self.date_format)
            parameters['Chunk_START_DATE'] = date2str(chunk_start, self.date_format)
            parameters['Chunk_END_DATE'] = date2str(chunk_end_1, self.date_format)
            parameters['RUN_DAYS'] = str(subs_dates(chunk_start, chunk_end, cal))
            parameters['Chunk_End_IN_DAYS'] = str(subs_dates(self.date, chunk_end, cal))

            parameters['Chunk_START_YEAR'] = str(self.date.year)
            parameters['Chunk_START_MONTH'] = str(self.date.month)

            parameters['PREV'] = str(subs_dates(self.date, chunk_start, cal))

            if chunk == 1:
                parameters['Chunk_FIRST'] = 'TRUE'
            else:
                parameters['Chunk_FIRST'] = 'FALSE'

            if total_chunk == chunk:
                parameters['Chunk_LAST'] = 'TRUE'
            else:
                parameters['Chunk_LAST'] = 'FALSE'

        parameters['NUMPROC'] = self.processors
        parameters['NUMTHREADS'] = self.threads
        parameters['NUMTASK'] = self.tasks
        parameters['WALLCLOCK'] = self.wallclock
        parameters['TASKTYPE'] = self.section

        job_platform = self.get_platform()
        parameters['CURRENT_ARCH'] = job_platform.name
        parameters['CURRENT_QUEUE'] = self.get_queue()
        parameters['CURRENT_USER'] = job_platform.user
        parameters['CURRENT_PROJ'] = job_platform.project
        parameters['CURRENT_BUDG'] = job_platform.budget
        parameters['CURRENT_TYPE'] = job_platform.type
        parameters['CURRENT_VERSION'] = job_platform.version
        parameters['CURRENT_SCRATCH_DIR'] = job_platform.scratch
        parameters['CURRENT_ROOTDIR'] = job_platform.root_dir

        parameters['ROOTDIR'] = os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.expid)
        parameters['PROJDIR'] = as_conf.get_project_dir()

        self.parameters = parameters

        return parameters

    def update_content(self, project_dir):
        """
        Create the script content to be run for the job

        :param project_dir: project directory
        :type project_dir: str
        :return: script code
        :rtype: str
        """
        if self.parameters['PROJECT_TYPE'].lower() != "none":
            template_file = file(os.path.join(project_dir, self.file), 'r')
            template = template_file.read()
        else:
            template = ''
        current_platform = self.get_platform()
        if isinstance(current_platform, LocalPlatform):
            stats_header = StatisticsSnippet.AS_HEADER_LOC
            stats_tailer = StatisticsSnippet.AS_TAILER_LOC
        else:
            stats_header = StatisticsSnippet.AS_HEADER_REM
            stats_tailer = StatisticsSnippet.AS_TAILER_REM

        template_content = ''.join([current_platform.get_header(self),
                                   stats_header,
                                   template,
                                   stats_tailer])

        return template_content

    def create_script(self, as_conf):
        """
        Creates script file to be run for the job

        :param as_conf: configuration object
        :type as_conf: AutosubmitConfig
        :return: script's filename
        :rtype: str
        """
        parameters = self.update_parameters(as_conf)
        template_content = self.update_content(as_conf.get_project_dir())
        # print "jobType: %s" % self._type
        # print template_content

        for key, value in parameters.items():
            # print "%s:\t%s" % (key,parameters[key])
            template_content = template_content.replace("%" + key + "%", str(parameters[key]))

        scriptname = self.name + '.cmd'
        file(os.path.join(self._tmp_path, scriptname), 'w').write(template_content)
        os.chmod(os.path.join(self._tmp_path, scriptname), 0775)

        return scriptname

    def check_script(self, as_conf):
        """
        Checks if script is well formed

        :param as_conf: configuration file
        :type as_conf: AutosubmitConfig
        :return: true if not problem has been detected, false otherwise
        :rtype: bool
        """
        parameters = self.update_parameters(as_conf)
        template_content = self.update_content(as_conf.get_project_dir())

        variables = re.findall('%' + '(\w+)' + '%', template_content)
        # variables += re.findall('%%'+'(.+?)'+'%%', template_content)
        out = set(parameters).issuperset(set(variables))

        if not out:
            Log.warning("The following set of variables to be substituted in template script is not part of "
                        "parameters set: {0}", str(set(variables) - set(parameters)))
        else:
            self.create_script(as_conf)

        return out
