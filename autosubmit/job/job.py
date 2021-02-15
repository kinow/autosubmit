#!/usr/bin/env python

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

"""
Main module for Autosubmit. Only contains an interface class to all functionality implemented on Autosubmit
"""

import os
import re
import time
import json
import datetime
import textwrap
from collections import OrderedDict
import copy

from bscearth.utils.config_parser import ConfigParserFactory

from autosubmit.config.config_common import AutosubmitConfig
from autosubmit.job.job_common import Status, Type, increase_wallclock_by_chunk
from autosubmit.job.job_common import StatisticsSnippetBash, StatisticsSnippetPython
from autosubmit.job.job_common import StatisticsSnippetR, StatisticsSnippetEmpty
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.database.db_jobdata import JobDataStructure
from bscearth.utils.date import date2str, parse_date, previous_day, chunk_end_date, chunk_start_date, Log, subs_dates
from time import sleep
from threading import Thread
from autosubmit.platforms.paramiko_submitter import ParamikoSubmitter
from log.log import Log, AutosubmitCritical, AutosubmitError
Log.get_logger("Autosubmit")

# A wrapper for encapsulate threads , TODO: Python 3+ to be replaced by the < from concurrent.futures >


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.name = "JOB_" + str(args[0].name)
        thread.start()
        return thread
    return wrapper


class Job(object):
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

    CHECK_ON_SUBMISSION = 'on_submission'

    def __str__(self):
        return "{0} STATUS: {1}".format(self.name, self.status)

    def __init__(self, name, job_id, status, priority):
        self._platform = None
        self._queue = None
        self.platform_name = None
        self.section = None
        self.wallclock = None
        self.wchunkinc = None
        self.tasks = '0'
        self.threads = '1'
        self.processors = '1'
        self.memory = ''
        self.memory_per_task = ''
        self.chunk = None
        self.member = None
        self.date = None
        self.name = name
        self.split = None
        self.delay = None
        self.frequency = None
        self.synchronize = None
        self.repacked = 0
        self._long_name = None
        self.long_name = name
        self.date_format = ''
        self.type = Type.BASH
        self.scratch_free_space = None
        self.custom_directives = []
        self.undefined_variables = None
        self.log_retries = 5
        self.id = job_id
        self.file = None
        self.executable = None
        self._local_logs = ('', '')
        self._remote_logs = ('', '')
        self.script_name = self.name + ".cmd"
        self.status = status
        self.prev_status = status
        self.old_status = self.status
        self.new_status = status
        self.priority = priority
        self._parents = set()
        self._children = set()
        self.fail_count = 0
        self.expid = name.split('_')[0]
        self.parameters = dict()
        self._tmp_path = os.path.join(
            BasicConfig.LOCAL_ROOT_DIR, self.expid, BasicConfig.LOCAL_TMP_DIR)
        self.write_start = False
        self._platform = None
        self.check = 'true'
        self.check_warnings = False
        self.packed = False
        self.hold = False
        self.distance_weight = 0
        self.level = 0

    def __getstate__(self):
        odict = self.__dict__
        if '_platform' in odict:
            odict = odict.copy()  # copy the dict since we change it
            del odict['_platform']  # remove filehandle entry
        return odict

    # def __str__(self):
    #     return self.name

    def print_job(self):
        """
        Prints debug information about the job
        """
        Log.debug('NAME: {0}', self.name)
        Log.debug('JOBID: {0}', self.id)
        Log.debug('STATUS: {0}', self.status)
        Log.debug('PRIORITY: {0}', self.priority)
        Log.debug('TYPE: {0}', self.type)
        Log.debug('PARENTS: {0}', [p.name for p in self.parents])
        Log.debug('CHILDREN: {0}', [c.name for c in self.children])
        Log.debug('FAIL_COUNT: {0}', self.fail_count)
        Log.debug('EXPID: {0}', self.expid)

    @property
    def parents(self):
        """
        Returns parent jobs list

        :return: parent jobs
        :rtype: set
        """
        return self._parents

    @parents.setter
    def parents(self, parents):
        """
        Sets the parents job list
        """
        self._parents = parents

    @property
    def is_serial(self):
        return str(self.processors) == '1'

    @property
    def platform(self):
        """
        Returns the platform to be used by the job. Chooses between serial and parallel platforms

        :return HPCPlatform object for the job to use
        :rtype: HPCPlatform
        """
        if self.is_serial:
            return self._platform.serial_platform
        else:
            return self._platform

    @platform.setter
    def platform(self, value):
        """
        Sets the HPC platforms to be used by the job.

        :param value: platforms to set
        :type value: HPCPlatform
        """
        self._platform = value

    @property
    def queue(self):
        """
        Returns the queue to be used by the job. Chooses between serial and parallel platforms

        :return HPCPlatform object for the job to use
        :rtype: HPCPlatform
        """
        if self._queue is not None:
            return self._queue
        if self.is_serial:
            return self._platform.serial_platform.serial_queue
        else:
            return self._platform.queue

    @queue.setter
    def queue(self, value):
        """
        Sets the queue to be used by the job.

        :param value: queue to set
        :type value: HPCPlatform
        """
        self._queue = value

    @property
    def children(self):
        """
        Returns a list containing all children of the job

        :return: child jobs
        :rtype: set
        """
        return self._children

    @children.setter
    def children(self, children):
        """
        Sets the children job list
        """
        self._children = children

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
    def local_logs(self):
        return self._local_logs

    @local_logs.setter
    def local_logs(self, value):
        self._local_logs = value

    @property
    def remote_logs(self):
        return self._remote_logs

    @remote_logs.setter
    def remote_logs(self, value):
        self._remote_logs = value

    @property
    def total_processors(self):
        if ':' in self.processors:
            return reduce(lambda x, y: int(x) + int(y), self.processors.split(':'))
        return int(self.processors)

    @property
    def total_wallclock(self):
        if self.wallclock:
            hours, minutes = self.wallclock.split(':')
            return float(minutes) / 60 + float(hours)
        return 0

    def log_job(self):
        """
        Prints job information in log
        """
        Log.debug("{0}\t{1}\t{2}", "Job Name", "Job Id", "Job Status")
        Log.debug("{0}\t\t{1}\t{2}", self.name, self.id, self.status)

        #Log.status("{0}\t{1}\t{2}", "Job Name", "Job Id", "Job Status")
        #Log.status("{0}\t\t{1}\t{2}", self.name, self.id, self.status)

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
    def add_parent(self, *parents):
        """
        Add parents for the job. It also adds current job as a child for all the new parents

        :param parents: job's parents to add
        :type parents: *Job
        """
        for parent in parents:
            num_parents = 1
            if isinstance(parent, list):
                num_parents = len(parent)
            for i in xrange(num_parents):
                new_parent = parent[i] if isinstance(parent, list) else parent
                self._parents.add(new_parent)
                new_parent.__add_child(self)

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
        Returns value from given row index position in STAT file associated to job

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
        Returns list of values from given column index position in TOTAL_STATS file associated to job

        :param index: column position to retrieve
        :type index: int
        :return: list of values in column index position
        :rtype: list[datetime.datetime]
        """
        log_name = os.path.join(self._tmp_path, self.name + '_TOTAL_STATS')
        lst = []
        if os.path.exists(log_name):
            f = open(log_name)
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

    def get_last_retrials(self):
        log_name = os.path.join(self._tmp_path, self.name + '_TOTAL_STATS')
        retrials_list = []
        if os.path.exists(log_name):
            already_completed = False
            for retrial in reversed(open(log_name).readlines()):
                retrial_fields = retrial.split()
                if Job.is_a_completed_retrial(retrial_fields):
                    if already_completed:
                        break
                    already_completed = True
                retrial_dates = map(lambda y: parse_date(y) if y != 'COMPLETED' and y != 'FAILED' else y,
                                    retrial_fields)
                retrials_list.insert(0, retrial_dates)
        return retrials_list

    def retrieve_logfiles_unthreaded(self, copy_remote_logs, local_logs):
        remote_logs = (self.script_name + ".out", self.script_name + ".err")
        out_exist = False
        err_exist = False
        retries = 3
        sleeptime = 0
        i = 0
        no_continue = False
        try:
            while (not out_exist and not err_exist) and i < retries:
                try:
                    out_exist = self._platform.check_file_exists(
                        remote_logs[0], True)
                except IOError as e:
                    out_exist = False
                try:
                    err_exist = self._platform.check_file_exists(
                        remote_logs[1], True)
                except IOError as e:
                    err_exists = False
                if not out_exist or not err_exist:
                    sleeptime = sleeptime + 5
                    i = i + 1
                    sleep(sleeptime)
            if i >= retries:
                if not out_exist or not err_exist:
                    Log.printlog("Failed to retrieve log files {1} and {2} e=6001".format(
                        retries, remote_logs[0], remote_logs[1]))
                    return
            if copy_remote_logs:
                # unifying names for log files
                if remote_logs != local_logs:
                    self.synchronize_logs(self._platform, remote_logs, local_logs)
                    remote_logs = copy.deepcopy(local_logs)
                self._platform.get_logs_files(self.expid, remote_logs)
                # Update the logs with Autosubmit Job Id Brand
                try:
                    for local_log in local_logs:
                        self._platform.write_jobid(self.id, os.path.join(
                            self._tmp_path, 'LOG_' + str(self.expid), local_log))
                except BaseException as e:
                    Log.printlog("Trace {0} \n Failed to write the {1} e=6001".format(
                        e.message, self.name))

        except AutosubmitError as e:
            Log.printlog("Trace {0} \nFailed to retrieve log file for job {1}".format(
                e.message, self.name), 6001)

        except AutosubmitCritical as e:  # Critical errors can't be recovered. Failed configuration or autosubmit error
            Log.printlog("Trace {0} \nFailed to retrieve log file for job {0}".format(
                e.message, self.name), 6001)
        return

    @threaded
    def retrieve_logfiles(self, copy_remote_logs, local_logs, remote_logs, expid, platform_name):
        try:
            as_conf = AutosubmitConfig(expid, BasicConfig, ConfigParserFactory())
            as_conf.reload()
            remote_logs = (self.script_name + ".out", self.script_name + ".err")
            submitter = self._get_submitter(as_conf)
            submitter.load_platforms(as_conf)
            self._platform = submitter.platforms[platform_name.lower()]
            try:
                self._platform.test_connection()
            except:
                pass
        except Exception as e:
            Log.printlog(
                "{0} \n Couldn't connect to the remote platform for this {1} job err/out files. ".format(e.message, self.name), 6001)
        out_exist = False
        err_exist = False
        retries = 5
        sleeptime = 0
        i = 0
        sleep(5)
        no_continue = False
        try:
            while (not out_exist and not err_exist) and i < retries:
                try:
                    out_exist = self._platform.check_file_exists(
                        remote_logs[0], True)
                except IOError as e:
                    out_exist = False
                try:
                    err_exist = self._platform.check_file_exists(
                        remote_logs[1], True)
                except IOError as e:
                    err_exists = False
                if not out_exist or not err_exist:
                    sleeptime = sleeptime + 5
                    i = i + 1
                    sleep(sleeptime)
                    try:
                        self._platform.restore_connection()
                    except BaseException as e:
                        Log.printlog("{0} \n Couldn't connect to the remote platform for this {1} job err/out files. ".format(
                            e.message, self.name), 6001)
            if i >= retries:
                if not out_exist or not err_exist:
                    Log.printlog("Failed to retrieve log files {1} and {2} e=6001".format(
                        retries, remote_logs[0], remote_logs[1]))
                    return
            if copy_remote_logs:
                # unifying names for log files
                if remote_logs != local_logs:
                    self.synchronize_logs(
                        self._platform, remote_logs, local_logs)
                    remote_logs = copy.deepcopy(local_logs)
                self._platform.get_logs_files(self.expid, remote_logs)
                # Update the logs with Autosubmit Job Id Brand
                try:
                    for local_log in local_logs:
                        self._platform.write_jobid(self.id, os.path.join(
                            self._tmp_path, 'LOG_' + str(self.expid), local_log))
                except BaseException as e:
                    Log.printlog("Trace {0} \n Failed to write the {1} e=6001".format(
                        e.message, self.name))
                    try:
                        self._platform.closeConnection()
                    except BaseException as e:
                        pass
                    return
        except AutosubmitError as e:
            Log.printlog("Trace {0} \nFailed to retrieve log file for job {1}".format(
                e.message, self.name), 6001)
            try:
                self._platform.closeConnection()
            except BaseException as e:
                pass

            return
        except AutosubmitCritical as e:  # Critical errors can't be recovered. Failed configuration or autosubmit error
            Log.printlog("Trace {0} \nFailed to retrieve log file for job {0}".format(
                e.message, self.name), 6001)
            try:
                self._platform.closeConnection()
            except:
                pass

            return
        sleep(5)  # safe wait before end a thread
        try:
            self._platform.closeConnection()
        except BaseException as e:
            pass
        return

    def update_status(self, copy_remote_logs=False):
        """
        Updates job status, checking COMPLETED file if needed

        :param new_status: job status retrieved from the platform
        :param copy_remote_logs: should copy remote logs when finished?
        :type: Status
        """
        previous_status = self.status
        self.prev_status = previous_status
        new_status = self.new_status
        if new_status == Status.COMPLETED:
            Log.debug(
                "{0} job seems to have completed: checking...".format(self.name))
            if not self._platform.get_completed_files(self.name, wrapper_failed=self.packed):
                log_name = os.path.join(
                    self._tmp_path, self.name + '_COMPLETED')

            self.check_completion()
        else:
            self.status = new_status

        if self.status == Status.RUNNING:
            Log.info("Job {0} is RUNNING", self.name)
        elif self.status == Status.QUEUING:
            Log.info("Job {0} is QUEUING", self.name)
        elif self.status == Status.HELD:
            Log.info("Job {0} is HELD", self.name)
        elif self.status == Status.COMPLETED:
            Log.result("Job {0} is COMPLETED", self.name)
        elif self.status == Status.FAILED:
            Log.printlog("Job {0} is FAILED. Checking completed files to confirm the failure...".format(
                self.name), 3000)
            self._platform.get_completed_files(
                self.name, wrapper_failed=self.packed)
            self.check_completion()
            if self.status == Status.COMPLETED:
                Log.result("Job {0} is COMPLETED", self.name)
            else:
                self.update_children_status()
        elif self.status == Status.UNKNOWN:
            Log.printlog("Job {0} is UNKNOWN. Checking completed files to confirm the failure...".format(
                self.name), 3000)
            self._platform.get_completed_files(
                self.name, wrapper_failed=self.packed)
            self.check_completion(Status.UNKNOWN)
            if self.status == Status.UNKNOWN:
                Log.printlog("Job {0} is UNKNOWN. Checking completed files to confirm the failure...".format(
                    self.name), 6009)
            elif self.status == Status.COMPLETED:
                Log.result("Job {0} is COMPLETED", self.name)
        elif self.status == Status.SUBMITTED:
            # after checking the jobs , no job should have the status "submitted"
            Log.printlog("Job {0} in SUBMITTED status. This should never happen on this step..".format(
                self.name), 6008)

        if previous_status != Status.RUNNING and self.status in [Status.COMPLETED, Status.FAILED, Status.UNKNOWN,
                                                                 Status.RUNNING]:
            self.write_start_time()
        # Updating logs
        if self.status in [Status.COMPLETED, Status.FAILED, Status.UNKNOWN]:
            self.write_end_time(self.status == Status.COMPLETED)
            # New thread, check if file exist
            expid = copy.deepcopy(self.expid)
            platform_name = copy.deepcopy(self.platform_name.lower())
            local_logs = copy.deepcopy(self.local_logs)
            remote_logs = copy.deepcopy(self.remote_logs)
            as_conf = AutosubmitConfig(expid, BasicConfig, ConfigParserFactory())
            as_conf.reload()
            if as_conf.get_disable_recovery_threads(self.platform.name):
                self.retrieve_logfiles_unthreaded(copy_remote_logs, local_logs)
            else:
                self.retrieve_logfiles(copy_remote_logs, local_logs, remote_logs, expid, platform_name)

        return self.status

    @staticmethod
    def _get_submitter(as_conf):
        """
        Returns the submitter corresponding to the communication defined on Autosubmit's config file

        :return: submitter
        :rtype: Submitter
        """
        communications_library = as_conf.get_communications_library()
        if communications_library == 'paramiko':
            return ParamikoSubmitter()
        # communications library not known
        raise AutosubmitCritical(
            'You have defined a not valid communications library on the configuration file', 7014)

    def update_children_status(self):
        children = list(self.children)
        for child in children:
            if child.level == 0 and child.status in [Status.SUBMITTED, Status.RUNNING, Status.QUEUING, Status.UNKNOWN]:
                child.status = Status.FAILED
                children += list(child.children)

    def check_completion(self, default_status=Status.FAILED):
        """
        Check the presence of *COMPLETED* file.
        Change status to COMPLETED if *COMPLETED* file exists and to FAILED otherwise.
        :param default_status: status to set if job is not completed. By default is FAILED
        :type default_status: Status
        """
        log_name = os.path.join(self._tmp_path, self.name + '_COMPLETED')

        if os.path.exists(log_name):  # TODO
            self.status = Status.COMPLETED
        else:
            Log.printlog("Job {0} completion check failed. There is no COMPLETED file".format(
                self.name), 6009)
            self.status = default_status

    def update_parameters(self, as_conf, parameters,
                          default_parameters={'d': '%d%', 'd_': '%d_%', 'Y': '%Y%', 'Y_': '%Y_%',
                                              'M': '%M%', 'M_': '%M_%', 'm': '%m%', 'm_': '%m_%'}):
        """
        Refresh parameters value

        :param default_parameters:
        :type default_parameters: dict
        :param as_conf:
        :type as_conf: AutosubmitConfig
        :param parameters:
        :type parameters: dict
        """
        chunk = 1
        parameters = parameters.copy()
        parameters.update(default_parameters)
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
            parameters['SPLIT'] = self.split
            parameters['DELAY'] = self.delay
            parameters['FREQUENCY'] = self.frequency
            parameters['SYNCHRONIZE'] = self.synchronize
            parameters['PACKED'] = self.packed
            total_chunk = int(parameters['NUMCHUNKS'])
            chunk_length = int(parameters['CHUNKSIZE'])
            chunk_unit = parameters['CHUNKSIZEUNIT'].lower()
            cal = parameters['CALENDAR'].lower()
            chunk_start = chunk_start_date(
                self.date, chunk, chunk_length, chunk_unit, cal)
            chunk_end = chunk_end_date(
                chunk_start, chunk_length, chunk_unit, cal)
            chunk_end_1 = previous_day(chunk_end, cal)

            parameters['DAY_BEFORE'] = date2str(
                previous_day(self.date, cal), self.date_format)

            parameters['RUN_DAYS'] = str(
                subs_dates(chunk_start, chunk_end, cal))
            parameters['Chunk_End_IN_DAYS'] = str(
                subs_dates(self.date, chunk_end, cal))

            parameters['Chunk_START_DATE'] = date2str(
                chunk_start, self.date_format)
            parameters['Chunk_START_YEAR'] = str(chunk_start.year)
            parameters['Chunk_START_MONTH'] = str(chunk_start.month).zfill(2)
            parameters['Chunk_START_DAY'] = str(chunk_start.day).zfill(2)
            parameters['Chunk_START_HOUR'] = str(chunk_start.hour).zfill(2)

            parameters['Chunk_END_DATE'] = date2str(
                chunk_end_1, self.date_format)
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

        job_platform = self._platform
        self.processors = as_conf.get_processors(self.section)
        self.threads = as_conf.get_threads(self.section)
        self.tasks = as_conf.get_tasks(self.section)
        if self.tasks == '0' and job_platform.processors_per_node:
            self.tasks = job_platform.processors_per_node
        self.memory = as_conf.get_memory(self.section)
        self.memory_per_task = as_conf.get_memory_per_task(self.section)
        self.wallclock = as_conf.get_wallclock(self.section)
        self.wchunkinc = as_conf.get_wchunkinc(self.section)
        # Increasing according to chunk
        self.wallclock = increase_wallclock_by_chunk(
            self.wallclock, self.wchunkinc, chunk)
        if self.wallclock == '':
            Log.debug(
                "Wallclock for {0} is not defined! , setting it to 02:00".format(self.name))
            self.wallclock = '02:00'
        self.scratch_free_space = as_conf.get_scratch_free_space(self.section)
        if self.scratch_free_space == 0:
            self.scratch_free_space = job_platform.scratch_free_space
        self.custom_directives = as_conf.get_custom_directives(self.section)
        if self.custom_directives != '':
            self.custom_directives = json.loads(
                as_conf.get_custom_directives(self.section))
            if job_platform.custom_directives:
                self.custom_directives = self.custom_directives + \
                    json.loads(job_platform.custom_directives)
        elif job_platform.custom_directives:
            self.custom_directives = json.loads(job_platform.custom_directives)
        elif self.custom_directives == '':
            self.custom_directives = []

        parameters['NUMPROC'] = self.processors
        parameters['MEMORY'] = self.memory
        parameters['MEMORY_PER_TASK'] = self.memory_per_task
        parameters['NUMTHREADS'] = self.threads
        parameters['THREADS'] = self.threads
        parameters['NUMTASK'] = self.tasks
        parameters['WALLCLOCK'] = self.wallclock
        parameters['TASKTYPE'] = self.section
        parameters['SCRATCH_FREE_SPACE'] = self.scratch_free_space
        parameters['CUSTOM_DIRECTIVES'] = self.custom_directives

        parameters['CURRENT_ARCH'] = job_platform.name
        parameters['CURRENT_HOST'] = job_platform.host
        parameters['CURRENT_QUEUE'] = self.queue
        parameters['CURRENT_USER'] = job_platform.user
        parameters['CURRENT_PROJ'] = job_platform.project
        parameters['CURRENT_BUDG'] = job_platform.budget
        parameters['CURRENT_RESERVATION'] = job_platform.reservation
        parameters['CURRENT_EXCLUSIVITY'] = job_platform.exclusivity
        parameters['CURRENT_HYPERTHREADING'] = job_platform.hyperthreading
        parameters['CURRENT_TYPE'] = job_platform.type
        parameters['CURRENT_SCRATCH_DIR'] = job_platform.scratch
        parameters['CURRENT_ROOTDIR'] = job_platform.root_dir
        parameters['CURRENT_LOGDIR'] = job_platform.get_files_path()

        parameters['ROOTDIR'] = os.path.join(
            BasicConfig.LOCAL_ROOT_DIR, self.expid)
        parameters['PROJDIR'] = as_conf.get_project_dir()

        parameters['NUMMEMBERS'] = len(as_conf.get_member_list())
        parameters['WRAPPER'] = as_conf.get_wrapper_type()

        self.parameters = parameters

        return parameters

    def update_content(self, as_conf):
        """
        Create the script content to be run for the job

        :param as_conf: config
        :type as_conf: config
        :return: script code
        :rtype: str
        """
        parameters = self.parameters
        if parameters['PROJECT_TYPE'].lower() != "none":
            template_file = open(os.path.join(
                as_conf.get_project_dir(), self.file), 'r')
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

        template_content = self._get_template_content(
            as_conf, snippet, template)

        return template_content

    def get_wrapped_content(self, as_conf):
        snippet = StatisticsSnippetEmpty
        template = 'python $SCRATCH/{1}/LOG_{1}/{0}.cmd'.format(
            self.name, self.expid)
        template_content = self._get_template_content(
            as_conf, snippet, template)
        return template_content

    def _get_template_content(self, as_conf, snippet, template):
        communications_library = as_conf.get_communications_library()
        if communications_library == 'paramiko':
            return self._get_paramiko_template(snippet, template)
        else:
            raise AutosubmitCritical(
                "Job {0} does not have an correct template// template not found".format(self.name), 7014)

    def _get_paramiko_template(self, snippet, template):
        current_platform = self._platform
        return ''.join([
            snippet.as_header(
                current_platform.get_header(self), self.executable),
            template,
            snippet.as_tailer()
        ])

    def queuing_reason_cancel(self, reason):
        try:
            if len(reason.split('(', 1)) > 1:
                reason = reason.split('(', 1)[1].split(')')[0]
                if 'Invalid' in reason or reason in ['AssociationJobLimit', 'AssociationResourceLimit', 'AssociationTimeLimit',
                                                     'BadConstraints', 'QOSMaxCpuMinutesPerJobLimit', 'QOSMaxWallDurationPerJobLimit',
                                                     'QOSMaxNodePerJobLimit', 'DependencyNeverSatisfied', 'QOSMaxMemoryPerJob',
                                                     'QOSMaxMemoryPerNode', 'QOSMaxMemoryMinutesPerJob', 'QOSMaxNodeMinutesPerJob',
                                                     'InactiveLimit', 'JobLaunchFailure', 'NonZeroExitCode', 'PartitionNodeLimit',
                                                     'PartitionTimeLimit', 'SystemFailure', 'TimeLimit', 'QOSUsageThreshold']:
                    return True
            return False
        except:
            return False

    @staticmethod
    def is_a_completed_retrial(fields):
        if len(fields) == 4:
            if fields[3] == 'COMPLETED':
                return True
        return False

    def create_script(self, as_conf):
        """
        Creates script file to be run for the job

        :param as_conf: configuration object
        :type as_conf: AutosubmitConfig
        :return: script's filename
        :rtype: str
        """
        parameters = self.parameters
        template_content = self.update_content(as_conf)
        for key, value in parameters.items():
            template_content = re.sub(
                '%(?<!%%)' + key + '%(?!%%)', str(parameters[key]), template_content)
        if self.undefined_variables:
            for variable in self.undefined_variables:
                template_content = re.sub(
                    '%(?<!%%)' + variable + '%(?!%%)', '', template_content)
        template_content = template_content.replace("%%", "%")
        script_name = '{0}.cmd'.format(self.name)
        self.script_name = '{0}.cmd'.format(self.name)
        open(os.path.join(self._tmp_path, script_name),
             'w').write(template_content)
        os.chmod(os.path.join(self._tmp_path, script_name), 0o755)
        return script_name

    def create_wrapped_script(self, as_conf, wrapper_tag='wrapped'):
        parameters = self.parameters
        template_content = self.get_wrapped_content(as_conf)
        for key, value in parameters.items():
            template_content = re.sub(
                '%(?<!%%)' + key + '%(?!%%)', str(parameters[key]), template_content)
        if self.undefined_variables:
            for variable in self.undefined_variables:
                template_content = re.sub(
                    '%(?<!%%)' + variable + '%(?!%%)', '', template_content)
        template_content = template_content.replace("%%", "%")
        script_name = '{0}.{1}.cmd'.format(self.name, wrapper_tag)
        self.script_name_wrapper = '{0}.{1}.cmd'.format(self.name, wrapper_tag)
        open(os.path.join(self._tmp_path, script_name),
             'w').write(template_content)
        os.chmod(os.path.join(self._tmp_path, script_name), 0o755)
        return script_name

    def check_script(self, as_conf, parameters, show_logs=False):
        """
        Checks if script is well formed

        :param parameters: script parameters
        :type parameters: dict
        :param as_conf: configuration file
        :type as_conf: AutosubmitConfig
        :param show_logs: Display output
        :type show_logs: Bool
        :return: true if not problem has been detected, false otherwise
        :rtype: bool
        """

        out = False
        parameters = self.update_parameters(as_conf, parameters)
        template_content = self.update_content(as_conf)
        if template_content is not False:
            variables = re.findall('%(?<!%%)\w+%(?!%%)', template_content)
            variables = [variable[1:-1] for variable in variables]
            out = set(parameters).issuperset(set(variables))

            # Check if the variables in the templates are defined in the configurations
            if not out:
                self.undefined_variables = set(variables) - set(parameters)
                if show_logs:
                    Log.printlog("The following set of variables to be substituted in template script is not part of parameters set, and will be replaced by a blank value: {0}".format(
                        self.undefined_variables), 6013)

            # Check which variables in the proj.conf are not being used in the templates
            if show_logs:
                if not set(variables).issuperset(set(parameters)):
                    Log.printlog("The following set of variables are not being used in the templates: {0}".format(
                        str(set(parameters) - set(variables))), 6013)
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
        # Writing database
        JobDataStructure(self.expid).write_submit_time(self.name, time.time(), Status.VALUE_TO_KEY[self.status] if self.status in Status.VALUE_TO_KEY.keys() else "UNKNOWN", self.processors,
                                                       self.wallclock, self._queue, self.date, self.member, self.section, self.chunk, self.platform_name, self.id, self.packed)

    def write_start_time(self):
        """
        Writes start date and time to TOTAL_STATS file
        :return: True if succesful, False otherwise
        :rtype: bool
        """
        if self._platform.get_stat_file(self.name, retries=5):
            start_time = self.check_start_time()
        else:
            Log.printlog('Could not get start time for {0}. Using current time as an approximation'.format(
                self.name), 3000)
            start_time = time.time()
        timestamp = date2str(datetime.datetime.now(), 'S')

        self.local_logs = (self.name + "." + timestamp +
                           ".out", self.name + "." + timestamp + ".err")

        path = os.path.join(self._tmp_path, self.name + '_TOTAL_STATS')
        f = open(path, 'a')
        f.write(' ')
        # noinspection PyTypeChecker
        f.write(date2str(datetime.datetime.fromtimestamp(start_time), 'S'))
        # Writing database
        JobDataStructure(self.expid).write_start_time(self.name, time.time(), Status.VALUE_TO_KEY[self.status] if self.status in Status.VALUE_TO_KEY.keys() else "UNKNOWN", self.processors,
                                                      self.wallclock, self._queue, self.date, self.member, self.section, self.chunk, self.platform_name, self.id, self.packed)
        return True

    def write_end_time(self, completed):
        """
        Writes ends date and time to TOTAL_STATS file
        :param completed: True if job was completed successfully, False otherwise
        :type completed: bool
        """
        self._platform.get_stat_file(self.name, retries=5)
        end_time = self.check_end_time()
        path = os.path.join(self._tmp_path, self.name + '_TOTAL_STATS')
        f = open(path, 'a')
        f.write(' ')
        finish_time = None
        final_status = None
        if end_time > 0:
            # noinspection PyTypeChecker
            f.write(date2str(datetime.datetime.fromtimestamp(end_time), 'S'))
            # date2str(datetime.datetime.fromtimestamp(end_time), 'S')
            finish_time = end_time
        else:
            f.write(date2str(datetime.datetime.now(), 'S'))
            finish_time = time.time()  # date2str(datetime.datetime.now(), 'S')
        f.write(' ')
        if completed:
            final_status = "COMPLETED"
            f.write('COMPLETED')
        else:
            final_status = "FAILED"
            f.write('FAILED')
        out, err = self.local_logs
        path_out = os.path.join(self._tmp_path, 'LOG_' + str(self.expid), out)
        # Launch first as simple non-threaded function
        JobDataStructure(self.expid).write_finish_time(self.name, finish_time, final_status, self.processors, self.wallclock, self._queue, self.date,
                                                       self.member, self.section, self.chunk, self.platform_name, self.id, self.platform, self.packed, [job.id for job in self._parents], True, None, out, err)
        # Launch second as threaded function
        thread_write_finish = Thread(target=JobDataStructure(self.expid).write_finish_time, args=(self.name, finish_time, final_status, self.processors,
                                                                                                  self.wallclock, self._queue, self.date, self.member, self.section, self.chunk, self.platform_name, self.id, self.platform, self.packed, [job.id for job in self._parents], False, path_out, out, err))
        thread_write_finish.start()

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

    def is_parent(self, job):
        """
        Check if the given job is a parent
        :param job: job to be checked if is a parent
        :return: True if job is a parent, false otherwise
        :rtype bool
        """
        return job in self.parents

    def is_ancestor(self, job):
        """
        Check if the given job is an ancestor
        :param job: job to be checked if is an ancestor
        :return: True if job is an ancestor, false otherwise
        :rtype bool
        """
        for parent in list(self.parents):
            if parent.is_parent(job):
                return True
            elif parent.is_ancestor(job):
                return True
        return False

    def remove_redundant_parents(self):
        """
        Checks if a parent is also an ancestor, if true, removes the link in both directions.
        Useful to remove redundant dependencies.
        """
        for parent in list(self.parents):
            if self.is_ancestor(parent):
                parent.children.remove(self)
                self.parents.remove(parent)

    def synchronize_logs(self, platform, remote_logs, local_logs):
        platform.move_file(remote_logs[0], local_logs[0], True)  # .out
        platform.move_file(remote_logs[1], local_logs[1], True)  # .err
        self.local_logs = local_logs
        self.remote_logs = copy.deepcopy(local_logs)


class WrapperJob(Job):
    """
    Defines a wrapper from a package.

    Calls Job constructor.

    :param name: Name of the Package \n
    :type name: String \n
    :param job_id: Id of the first Job of the package \n
    :type job_id: Integer \n
    :param status: 'READY' when coming from submit_ready_jobs() \n
    :type status: String \n
    :param priority: 0 when coming from submit_ready_jobs() \n
    :type priority: Integer \n
    :param job_list: List of jobs in the package \n
    :type job_list: List() of Job() objects \n
    :param total_wallclock: Wallclock of the package \n
    :type total_wallclock: String Formatted \n
    :param num_processors: Number of processors for the package \n
    :type num_processors: Integer \n
    :param platform: Platform object defined for the package \n
    :type platform: Platform Object. e.g. EcPlatform() \n
    :param as_config: Autosubmit basic configuration object \n
    :type as_config: AutosubmitConfig object \n
    """

    def __init__(self, name, job_id, status, priority, job_list, total_wallclock, num_processors, platform, as_config, hold):
        super(WrapperJob, self).__init__(name, job_id, status, priority)
        self.failed = False
        self.job_list = job_list
        # divide jobs in dictionary by state?
        self.wallclock = total_wallclock

        self.num_processors = num_processors
        self.running_jobs_start = OrderedDict()
        self._platform = platform
        self.as_config = as_config
        # save start time, wallclock and processors?!
        self.checked_time = datetime.datetime.now()
        self.hold = hold
        self.inner_jobs_running = list()

    def _queuing_reason_cancel(self, reason):
        try:
            if len(reason.split('(', 1)) > 1:
                reason = reason.split('(', 1)[1].split(')')[0]
                if 'Invalid' in reason or reason in ['AssociationJobLimit', 'AssociationResourceLimit', 'AssociationTimeLimit',
                                                     'BadConstraints', 'QOSMaxCpuMinutesPerJobLimit', 'QOSMaxWallDurationPerJobLimit',
                                                     'QOSMaxNodePerJobLimit', 'DependencyNeverSatisfied', 'QOSMaxMemoryPerJob',
                                                     'QOSMaxMemoryPerNode', 'QOSMaxMemoryMinutesPerJob', 'QOSMaxNodeMinutesPerJob',
                                                     'InactiveLimit', 'JobLaunchFailure', 'NonZeroExitCode', 'PartitionNodeLimit',
                                                     'PartitionTimeLimit', 'SystemFailure', 'TimeLimit', 'QOSUsageThreshold']:
                    return True
            return False
        except:
            return False

    def check_status(self, status):
        prev_status = self.status
        self.prev_status = prev_status
        self.status = status

        Log.debug('Checking inner jobs status')
        if self.status in [Status.HELD, Status.QUEUING]:  # If WRAPPER is QUEUED OR HELD
            # This will update the inner jobs to QUEUE or HELD (normal behaviour) or WAITING ( if they fails to be held)
            self._check_inner_jobs_queue(prev_status)
        elif self.status == Status.RUNNING:  # If wrapper is running
            #Log.info("Wrapper {0} is {1}".format(self.name, Status().VALUE_TO_KEY[self.status]))
            # This will update the status from submitted or hold to running (if safety timer is high enough or queue is fast enough)
            if prev_status in [Status.SUBMITTED]:
                for job in self.job_list:
                    job.status = Status.QUEUING
            self._check_running_jobs()  # Check and update inner_jobs status that are elegible
        # Completed wrapper will always come from check function.
        elif self.status == Status.COMPLETED:
            self.check_inner_jobs_completed(self.job_list)

        # Fail can come from check function or running/completed checkers.
        if self.status in [Status.FAILED, Status.UNKNOWN]:
            self.status = Status.FAILED
            if self.prev_status not in [Status.FAILED, Status.UNKNOWN]:
                sleep(1)
            else:
                self.failed = True
                self._check_running_jobs()
            if len(self.inner_jobs_running) > 0:
                still_running = True
                if not self.failed:
                    if self._platform.check_file_exists('WRAPPER_FAILED', wrapper_failed=True):
                        for job in self.inner_jobs_running:
                            if job.platform.check_file_exists('{0}_FAILED'.format(job.name), wrapper_failed=True):
                                Log.info(
                                    "Wrapper {0} Failed, checking inner_jobs...".format(self.name))
                                self.failed = True
                                self._platform.delete_file('WRAPPER_FAILED')
                                break
                if self.failed:
                    self.update_failed_jobs()
                    if len(self.inner_jobs_running) <= 0:
                        still_running = False
            else:
                still_running = False
            if not still_running:
                self.cancel_failed_wrapper_job()

    def check_inner_jobs_completed(self, jobs):
        not_completed_jobs = [
            job for job in jobs if job.status != Status.COMPLETED]
        not_completed_job_names = [job.name for job in not_completed_jobs]
        job_names = ' '.join(not_completed_job_names)
        if job_names:
            completed_files = self._platform.check_completed_files(job_names)
            completed_jobs = []
            for job in not_completed_jobs:
                if completed_files and len(completed_files) > 0:
                    if job.name in completed_files:
                        completed_jobs.append(job)
                        job.new_status = Status.COMPLETED
                        job.update_status(
                            self.as_config.get_copy_remote_logs() == 'true')
            for job in completed_jobs:
                self.running_jobs_start.pop(job, None)
            not_completed_jobs = list(
                set(not_completed_jobs) - set(completed_jobs))

        for job in not_completed_jobs:
            self._check_finished_job(job)

    def _check_inner_jobs_queue(self, prev_status):
        reason = str()
        if self._platform.type == 'slurm':
            self._platform.send_command(
                self._platform.get_queue_status_cmd(self.id))
            reason = self._platform.parse_queue_reason(
                self._platform._ssh_output, self.id)
            if self._queuing_reason_cancel(reason):
                Log.printlog("Job {0} will be cancelled and set to FAILED as it was queuing due to {1}".format(
                    self.name, reason), 6009)
                # while running jobs?
                self._check_running_jobs()  # todo
                self.update_failed_jobs(canceled_wrapper=True)
                self.cancel_failed_wrapper_job()

                return
            if reason == '(JobHeldUser)':
                if self.hold is False:
                    # SHOULD BE MORE CLASS (GET_scontrol realease but not sure if this can be implemented on others PLATFORMS
                    self._platform.send_command(
                        "scontrol release " + "{0}".format(self.id))
                    self.status = Status.QUEUING
                    for job in self.job_list:
                        job.hold = self.hold
                        job.status = self.status
                    Log.info("Job {0} is QUEUING {1}", self.name, reason)
                else:
                    self.status = Status.HELD
                    Log.info("Job {0} is HELD", self.name)
            elif reason == '(JobHeldAdmin)':
                Log.debug(
                    "Job {0} Failed to be HELD, canceling... ", self.name)
                self._platform.send_command(
                    self._platform.cancel_cmd + " {0}".format(self.id))
                self.status = Status.WAITING
            else:
                Log.info("Job {0} is QUEUING {1}", self.name, reason)
        if prev_status != self.status:
            for job in self.job_list:
                job.hold = self.hold
                job.status = self.status
                if self.status == Status.WAITING:
                    for job in self.job_list:
                        job.packed = False

    def _check_inner_job_wallclock(self, job):
        start_time = self.running_jobs_start[job]
        if self._is_over_wallclock(start_time, job.wallclock):
            # if self.as_config.get_wrapper_type() in ['vertical', 'horizontal']:
            Log.printlog("Job {0} inside wrapper {1} is running for longer than it's wallclock!".format(
                job.name, self.name), 6009)
            return True
        return False

    def _check_running_jobs(self):
        not_finished_jobs_dict = OrderedDict()
        self.inner_jobs_running = list()
        not_finished_jobs = [job for job in self.job_list if job.status not in [
            Status.COMPLETED, Status.FAILED]]
        for job in not_finished_jobs:
            tmp = [parent for parent in job.parents if parent.status ==
                   Status.COMPLETED or self.status == Status.COMPLETED]
            if job.parents is None or len(tmp) == len(job.parents):
                not_finished_jobs_dict[job.name] = job
                self.inner_jobs_running.append(job)
        if len(not_finished_jobs_dict.keys()) > 0:  # Only running jobs will enter there
            not_finished_jobs_names = ' '.join(not_finished_jobs_dict.keys())
            remote_log_dir = self._platform.get_remote_log_dir()
            # PREPARE SCRIPT TO SEND
            command = textwrap.dedent("""
            cd {1}
            for job in {0}
            do
                if [ -f "${{job}}_STAT" ]
                then
                        echo ${{job}} $(head ${{job}}_STAT)
                else
                        echo ${{job}}
                fi
            done
            """).format(str(not_finished_jobs_names), str(remote_log_dir), '\n'.ljust(13))

            log_dir = os.path.join(
                self._tmp_path, 'LOG_{0}'.format(self.expid))
            multiple_checker_inner_jobs = os.path.join(
                log_dir, "inner_jobs_checker.sh")
            if not os.stat(log_dir):
                os.mkdir(log_dir)
                os.chmod(log_dir, 0o770)
            open(multiple_checker_inner_jobs, 'w+').write(command)
            os.chmod(multiple_checker_inner_jobs, 0o770)
            self._platform.send_file(multiple_checker_inner_jobs, False)
            command = os.path.join(
                self._platform.get_files_path(), "inner_jobs_checker.sh")
            #
            wait = 2
            retries = 5
            over_wallclock = False
            content = ''
            while content == '' and retries > 0:
                self._platform.send_command(command, False)
                content = self._platform._ssh_output.split('\n')
                # content.reverse()
                for line in content[:-1]:
                    out = line.split()
                    if out:
                        jobname = out[0]
                        job = not_finished_jobs_dict[jobname]
                        if len(out) > 1:
                            if job not in self.running_jobs_start:
                                start_time = self._check_time(out, 1)
                                Log.info("Job {0} started at {1}".format(
                                    jobname, str(parse_date(start_time))))
                                self.running_jobs_start[job] = start_time
                                job.new_status = Status.RUNNING
                                #job.status = Status.RUNNING
                                job.update_status(
                                    self.as_config.get_copy_remote_logs() == 'true')
                            if len(out) == 2:
                                Log.info("Job {0} is RUNNING".format(jobname))
                                over_wallclock = self._check_inner_job_wallclock(
                                    job)  # messaged included
                                if over_wallclock:
                                    job.status = Status.FAILED
                                    Log.printlog(
                                        "Job {0} is FAILED".format(jobname), 6009)
                            elif len(out) == 3:
                                end_time = self._check_time(out, 2)
                                self._check_finished_job(job)
                                Log.info("Job {0} finished at {1}".format(
                                    jobname, str(parse_date(end_time))))
                if content == '':
                    sleep(wait)
                retries = retries - 1
            temp_list = self.inner_jobs_running
            self.inner_jobs_running = [
                job for job in temp_list if job.status == Status.RUNNING]
            if retries == 0:  # or over_wallclock:
                self.status = Status.FAILED

    def _check_finished_job(self, job, failed_file=False):
        if not failed_file:
            wait = 2
            retries = 2
            output = ''
            while output == '' and retries > 0:
                output = self._platform.check_completed_files(job.name)
                if output is None or output == '':
                    sleep(wait)
                retries = retries - 1
        if failed_file or (output is not None and output != '' and 'COMPLETED' in output):
            job.new_status = Status.COMPLETED
            job.update_status(self.as_config.get_copy_remote_logs() == 'true')
        else:
            #Log.info("No completed filed found, setting {0} to FAILED...".format(job.name))
            job.status = Status.FAILED
            #job.update_status(self.as_config.get_copy_remote_logs() == 'true')
        self.running_jobs_start.pop(job, None)

    def update_failed_jobs(self, canceled_wrapper=False):
        running_jobs = self.inner_jobs_running
        self.inner_jobs_running = list()
        for job in running_jobs:
            if job.platform.check_file_exists('{0}_FAILED'.format(job.name), wrapper_failed=True):
                if job.platform.get_file('{0}_FAILED'.format(job.name), False, wrapper_failed=True):
                    self._check_finished_job(job)
            else:
                self.inner_jobs_running.append(job)

    def cancel_failed_wrapper_job(self):
        Log.printlog("Cancelling job with id {0}".format(self.id), 6009)
        self._platform.send_command(
            self._platform.cancel_cmd + " " + str(self.id))
        for job in self.job_list:
            if job.status not in [Status.COMPLETED, Status.FAILED]:
                job.status = Status.WAITING

    def _update_completed_jobs(self):
        for job in self.job_list:
            if job.status == Status.RUNNING:
                self.running_jobs_start.pop(job, None)
                Log.debug('Setting job {0} to COMPLETED'.format(job.name))
                job.new_status = Status.COMPLETED
                job.update_status(
                    self.as_config.get_copy_remote_logs() == 'true')

    def _is_over_wallclock(self, start_time, wallclock):
        elapsed = datetime.datetime.now() - parse_date(start_time)
        wallclock = datetime.datetime.strptime(wallclock, '%H:%M')
        total = 0.0
        if wallclock.hour > 0:
            total = wallclock.hour
        if wallclock.minute > 0:
            total += wallclock.minute / 60.0
        if wallclock.second > 0:
            total += wallclock.second / 60.0 / 60.0
        total = total * 1.15
        hour = int(total)
        minute = int((total - int(total)) * 60.0)
        second = int(((total - int(total)) * 60 -
                      int((total - int(total)) * 60.0)) * 60.0)
        wallclock_delta = datetime.timedelta(hours=hour, minutes=minute,
                                             seconds=second)
        if elapsed > wallclock_delta:
            return True
        return False

    def _parse_timestamp(self, timestamp):
        value = datetime.datetime.fromtimestamp(timestamp)
        time = value.strftime('%Y-%m-%d %H:%M:%S')
        return time

    def _check_time(self, output, index):
        time = int(output[index])
        time = self._parse_timestamp(time)
        return time
