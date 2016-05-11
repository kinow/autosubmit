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

"""
Main module for autosubmit. Only contains an interface class to all functionality implemented on autosubmit
"""
import os
import re
import time

from autosubmit.job.job_common import Status, Type
from autosubmit.job.job_common import StatisticsSnippetBash, StatisticsSnippetPython, StatisticsSnippetR
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.date.chunk_date_lib import *


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
    :param status: job initial status
    :type status: Status
    :param priority: job's priority
    :type priority: int
    """

    def __str__(self):
        return "{0} STATUS: {1}".format(self.name, self.status)

    def __init__(self, name, jobid, status, priority):
        self._platform = None
        self._queue = None
        self.platform_name = None
        self.section = None
        self.wallclock = None
        self.tasks = None
        self.threads = None
        self.processors = None
        self.memory = None
        self.chunk = None
        self.member = None
        self.date = None
        self.memory = None
        self.name = name
        self._long_name = None
        self.long_name = name
        self.date_format = ''
        self.type = Type.BASH

        self.id = jobid
        self.file = None
        self.status = status
        self.priority = priority
        self._parents = set()
        self._children = set()
        self.fail_count = 0
        self.expid = name.split('_')[0]
        self.parameters = dict()
        self._tmp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.expid, BasicConfig.LOCAL_TMP_DIR)
        self._ancestors = None
        self.write_start = False
        self._platform = None
        self.check = True

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
            return self._platform.serial_platform

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
            return self._platform.queue
        else:
            return self._platform.serial_platform.serial_queue

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

    # Maybe should be renamed to the plural?
    def add_parent(self, *new_parent):
        """
        Add parents for the job. It also adds current job as a child for all the new parents

        :param new_parent: job's parents to add
        :type new_parent: *Job
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
        return self.status < other.status

    def compare_by_id(self, other):
        """
        Compare jobs by ID

        :param other: job to compare
        :type other: Job
        :return: comparison result
        :rtype: bool
        """
        return self.id < other.id

    def compare_by_name(self, other):
        """
        Compare jobs by name

        :param other: job to compare
        :type other: Job
        :return: comparison result
        :rtype: bool
        """
        return self.name < other.name

    def _get_from_stat(self, index):
        """
        Returns value from given row index position in STAT file asociated to job

        :param index: row position to retrieve
        :type index: int
        :return: value in index position
        :rtype: int
        """
        logname = os.path.join(self._tmp_path, self.name + '_STAT')
        if os.path.exists(logname):
            lines = open(logname).readlines()
            if len(lines) >= index + 1:
                return int(lines[index])
            else:
                return 0
        else:
            return 0

    def _get_from_total_stats(self, index):
        """
        Returns list of values from given column index position in TOTAL_STATS file asociated to job

        :param index: column position to retrieve
        :type index: int
        :return: list of values in column index position
        :rtype: list[datetime.datetime]
        """
        logname = os.path.join(self._tmp_path, self.name + '_TOTAL_STATS')
        lst = []
        if os.path.exists(logname):
            f = open(logname)
            lines = f.readlines()
            for line in lines:
                fields = line.split()
                if len(fields) >= index + 1:
                    lst.append(parse_date(fields[index]))
        return lst

    def check_end_time(self):
        """
        Returns end time from stat file

        :return: date and time
        :rtype: str
        """
        return self._get_from_stat(1)

    def check_start_time(self):
        """
        Returns job's start time

        :return: start time
        :rtype: str
        """
        return self._get_from_stat(0)

    def check_retrials_submit_time(self):
        """
        Returns list of submit datetime for retrials from total stats file

        :return: date and time
        :rtype: list[int]
        """
        return self._get_from_total_stats(0)

    def check_retrials_end_time(self):
        """
        Returns list of end datetime for retrials from total stats file

        :return: date and time
        :rtype: list[int]
        """
        return self._get_from_total_stats(2)

    def check_retrials_start_time(self):
        """
        Returns list of start datetime for retrials from total stats file

        :return: date and time
        :rtype: list[int]
        """
        return self._get_from_total_stats(1)

    def update_status(self, new_status):
        """
        Updates job status, checking COMPLETED file if needed

        :param new_status: job status retrieved from the platform
        :type: Status
        """
        previous_status = self.status

        if new_status == Status.COMPLETED:
            Log.debug("This job seems to have completed...checking")
            self.get_platform().get_completed_files(self.name)
            self.check_completion()
        else:
            self.status = new_status
        if self.status is Status.QUEUING:
            Log.info("Job {0} is QUEUING", self.name)
        elif self.status is Status.RUNNING:
            Log.info("Job {0} is RUNNING", self.name)
        elif self.status is Status.COMPLETED:
            Log.result("Job {0} is COMPLETED", self.name)
        elif self.status is Status.FAILED:
            Log.user_warning("Job {0} is FAILED", self.name)
        elif self.status is Status.UNKNOWN:
            Log.debug("Job {0} in UNKNOWN status. Checking completed files", self.name)
            self.get_platform().get_completed_files(self.name)
            self.check_completion(Status.UNKNOWN)
            if self.status is Status.UNKNOWN:
                Log.warning('Job {0} in UNKNOWN status', self.name)
        elif self.status is Status.SUBMITTED:
            # after checking the jobs , no job should have the status "submitted"
            Log.warning('Job {0} in SUBMITTED status after checking.', self.name)

        if previous_status != Status.RUNNING and self.status in [Status.COMPLETED, Status.FAILED, Status.UNKNOWN,
                                                                 Status.RUNNING]:
            self.write_start_time()
        if self.status in [Status.COMPLETED, Status.FAILED, Status.UNKNOWN]:
            self.write_end_time(self.status == Status.COMPLETED)
        return self.status

    def check_completion(self, default_status=Status.FAILED):
        """
        Check the presence of *COMPLETED* file.
        Change status to COMPLETED if *COMPLETED* file exists and to FAILED otherwise.
        :param default_status: status to set if job is not completed. By default is FAILED
        :type default_status: Status
        """
        logname = os.path.join(self._tmp_path, self.name + '_COMPLETED')
        if os.path.exists(logname):
            self.status = Status.COMPLETED
        else:
            Log.warning("Job {0} seemed to be completed but there is no COMPLETED file", self.name)
            self.status = default_status

    def update_parameters(self, as_conf, parameters):
        """
        Refresh parameters value

        :param as_conf:
        :type as_conf: AutosubmitConfig
        :param parameters:
        :type parameters: dict
        """
        parameters = parameters.copy()
        parameters['JOBNAME'] = self.name
        parameters['FAIL_COUNT'] = str(self.fail_count)

        parameters['SDATE'] = date2str(self.date, self.date_format)
        parameters['MEMBER'] = self.member

        if hasattr(self, 'retrials'):
            parameters['RETRIALS'] = self.retrials

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

            parameters['RUN_DAYS'] = str(subs_dates(chunk_start, chunk_end, cal))
            parameters['Chunk_End_IN_DAYS'] = str(subs_dates(self.date, chunk_end, cal))

            parameters['Chunk_START_DATE'] = date2str(chunk_start, self.date_format)
            parameters['Chunk_START_YEAR'] = str(chunk_start.year)
            parameters['Chunk_START_MONTH'] = str(chunk_start.month).zfill(2)
            parameters['Chunk_START_DAY'] = str(chunk_start.day).zfill(2)
            parameters['Chunk_START_HOUR'] = str(chunk_start.hour).zfill(2)

            parameters['Chunk_END_DATE'] = date2str(chunk_end_1, self.date_format)
            parameters['Chunk_END_YEAR'] = str(chunk_end_1.year)
            parameters['Chunk_END_MONTH'] = str(chunk_end_1.month).zfill(2)
            parameters['Chunk_END_DAY'] = str(chunk_end_1.day).zfill(2)
            parameters['Chunk_END_HOUR'] = str(chunk_end_1.hour).zfill(2)

            parameters['PREV'] = str(subs_dates(self.date, chunk_start, cal))

            if chunk == 1:
                parameters['Chunk_FIRST'] = 'TRUE'
            else:
                parameters['Chunk_FIRST'] = 'FALSE'

            if total_chunk == chunk:
                parameters['Chunk_LAST'] = 'TRUE'
            else:
                parameters['Chunk_LAST'] = 'FALSE'

        self.processors = as_conf.get_processors(self.section)
        self.threads = as_conf.get_threads(self.section)
        self.tasks = as_conf.get_tasks(self.section)
        self.memory = as_conf.get_memory(self.section)
        self.wallclock = as_conf.get_wallclock(self.section)

        parameters['NUMPROC'] = self.processors
        parameters['MEMORY'] = self.memory
        parameters['NUMTHREADS'] = self.threads
        parameters['NUMTASK'] = self.tasks
        parameters['WALLCLOCK'] = self.wallclock
        parameters['TASKTYPE'] = self.section
        parameters['MEMORY'] = self.memory

        job_platform = self.get_platform()
        parameters['CURRENT_ARCH'] = job_platform.name
        parameters['CURRENT_HOST'] = job_platform.host
        parameters['CURRENT_QUEUE'] = self.get_queue()
        parameters['CURRENT_USER'] = job_platform.user
        parameters['CURRENT_PROJ'] = job_platform.project
        parameters['CURRENT_BUDG'] = job_platform.budget
        parameters['CURRENT_TYPE'] = job_platform.type
        parameters['CURRENT_SCRATCH_DIR'] = job_platform.scratch
        parameters['CURRENT_ROOTDIR'] = job_platform.root_dir
        parameters['CURRENT_LOGDIR'] = job_platform.get_files_path()

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
            template_file = open(os.path.join(project_dir, self.file), 'r')
            template = template_file.read()
        else:
            if self.type == Type.BASH:
                template = 'sleep 5'
            elif self.type == Type.PYTHON:
                template = 'time.sleep(5)'
            elif self.type == Type.R:
                template = 'Sys.sleep(5)'
            else:
                template = ''

        if self.type == Type.BASH:
            snippet = StatisticsSnippetBash
        elif self.type == Type.PYTHON:
            snippet = StatisticsSnippetPython
        elif self.type == Type.R:
            snippet = StatisticsSnippetR
        else:
            raise Exception('Job type {0} not supported'.format(self.type))

        template_content = ''.join([snippet.AS_HEADER,
                                   template,
                                   snippet.AS_TAILER])

        return template_content

    def create_script(self, as_conf):
        """
        Creates script file to be run for the job

        :param as_conf: configuration object
        :type as_conf: AutosubmitConfig
        :return: script's filename
        :rtype: str
        """
        parameters = self.parameters
        template_content = self.update_content(as_conf.get_project_dir())
        for key, value in parameters.items():
            template_content = re.sub('%(?<!%%)' + key + '%(?!%%)', str(parameters[key]), template_content,
                                      flags=re.IGNORECASE)
        template_content = template_content.replace("%%", "%")

        scriptname = self.name + '.cmd'
        open(os.path.join(self._tmp_path, scriptname), 'w').write(template_content)
        os.chmod(os.path.join(self._tmp_path, scriptname), 0o775)

        return scriptname

    def check_script(self, as_conf, parameters):
        """
        Checks if script is well formed

        :param parameters: script parameters
        :type parameters: dict
        :param as_conf: configuration file
        :type as_conf: AutosubmitConfig
        :return: true if not problem has been detected, false otherwise
        :rtype: bool
        """
        if not self.check:
            Log.info('Template {0} will not be checked'.format(self.section))
            return True
        parameters = self.update_parameters(as_conf, parameters)
        template_content = self.update_content(as_conf.get_project_dir())

        variables = re.findall('%(?<!%%)\w+%(?!%%)', template_content)
        variables = [variable[1:-1] for variable in variables]
        out = set(parameters).issuperset(set(variables))

        if not out:
            Log.warning("The following set of variables to be substituted in template script is not part of "
                        "parameters set: {0}", str(set(variables) - set(parameters)))
        else:
            self.create_script(as_conf)

        return out

    def write_submit_time(self):
        """
        Writes submit date and time to TOTAL_STATS file
        """
        path = os.path.join(self._tmp_path, self.name + '_TOTAL_STATS')
        if os.path.exists(path):
            f = open(path, 'a')
            f.write('\n')
        else:
            f = open(path, 'w')
        f.write(date2str(datetime.datetime.now(), 'S'))

    def write_start_time(self):
        """
        Writes start date and time to TOTAL_STATS file
        :return: True if succesful, False otherwise
        :rtype: bool
        """
        if self.get_platform().get_stat_file(self.name, retries=5):
            start_time = self.check_start_time()
        else:
            Log.warning('Could not get start time for {0}. Using current time as an aproximation', self.name)
            start_time = time.time()

        path = os.path.join(self._tmp_path, self.name + '_TOTAL_STATS')
        f = open(path, 'a')
        f.write(' ')
        # noinspection PyTypeChecker
        f.write(date2str(datetime.datetime.fromtimestamp(start_time), 'S'))
        return True

    def write_end_time(self, completed):
        """
        Writes ends date and time to TOTAL_STATS file
        :param completed: True if job was completed succesfuly, False otherwise
        :type completed: bool
        """
        self.get_platform().get_stat_file(self.name, retries=5)
        end_time = self.check_end_time()
        path = os.path.join(self._tmp_path, self.name + '_TOTAL_STATS')
        f = open(path, 'a')
        f.write(' ')
        if end_time > 0:
            # noinspection PyTypeChecker
            f.write(date2str(datetime.datetime.fromtimestamp(end_time), 'S'))
        else:
            f.write(date2str(datetime.datetime.now(), 'S'))
        f.write(' ')
        if completed:
            f.write('COMPLETED')
        else:
            f.write('FAILED')

    def check_started_after(self, date_limit):
        """
        Checks if the job started after the given date
        :param date_limit: reference date
        :type date_limit: datetime.datetime
        :return: True if job started after the given date, false otherwise
        :rtype: bool
        """
        if any(parse_date(str(date_retrial)) > date_limit for date_retrial in self.check_retrials_start_time()):
            return True
        else:
            return False

    def check_running_after(self, date_limit):
        """
        Checks if the job was running after the given date
        :param date_limit: reference date
        :type date_limit: datetime.datetime
        :return: True if job was running after the given date, false otherwise
        :rtype: bool
        """
        if any(parse_date(str(date_end)) > date_limit for date_end in self.check_retrials_end_time()):
            return True
        else:
            return False
