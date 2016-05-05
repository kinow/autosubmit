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
try:
    # noinspection PyCompatibility
    from configparser import SafeConfigParser
except ImportError:
    # noinspection PyCompatibility
    from ConfigParser import SafeConfigParser
import json

import os
import pickle
from time import localtime, strftime
from sys import setrecursionlimit
from shutil import move

from autosubmit.job.job_common import Status, Type
from autosubmit.job.job import Job
from autosubmit.config.log import Log
from autosubmit.date.chunk_date_lib import date2str, parse_date


class JobList:
    """
    Class to manage the list of jobs to be run by autosubmit

    :param expid: experiment's identifier
    :type expid: str
    """

    def __init__(self, expid, config, parser_factory):
        self._pkl_path = os.path.join(config.LOCAL_ROOT_DIR, expid, "pkl")
        self._update_file = "updated_list_" + expid + ".txt"
        self._failed_file = "failed_job_list_" + expid + ".pkl"
        self._job_list_file = "job_list_" + expid + ".pkl"
        self._job_list = list()
        self._expid = expid
        self._config = config
        self._parser_factory = parser_factory
        self._stat_val = Status()
        self._parameters = []
        self._date_list = []
        self._member_list = []
        self._chunk_list = []
        self._dic_jobs = dict()

    @property
    def expid(self):
        """
        Returns experiment identifier

        :return: experiment's identifier
        :rtype: str
        """
        return self._expid

    def create(self, date_list, member_list, num_chunks, parameters, date_format, default_retrials):
        """
        Creates all jobs needed for the current workflow

        :param date_list: start dates
        :type date_list: list
        :param member_list: members
        :type member_list: list
        :param num_chunks: number of chunks to run
        :type num_chunks: int
        :param parameters: parameters for the jobs
        :type parameters: dict
        :param date_format: option to format dates
        :type date_format: str
        :param default_retrials: default retrials for ech job
        :type default_retrials: int
        """
        self._parameters = parameters
        self._date_list = date_list
        self._member_list = member_list

        chunk_list = range(1, num_chunks + 1)
        self._chunk_list = chunk_list

        parser = self._parser_factory.create_parser()
        parser.optionxform = str
        parser.read(os.path.join(self._config.LOCAL_ROOT_DIR, self._expid, 'conf', "jobs_" + self._expid + ".conf"))

        dic_jobs = DicJobs(self, parser, date_list, member_list, chunk_list, date_format, default_retrials)
        self._dic_jobs = dic_jobs
        priority = 0

        Log.info("Creating jobs...")
        self._create_jobs(dic_jobs, parser, priority)

        Log.info("Adding dependencies...")
        self._add_dependencies(date_list, member_list, chunk_list, dic_jobs, parser)

        Log.info("Removing redundant dependencies...")
        self.update_genealogy()
        for job in self._job_list:
            job.parameters = parameters

    @staticmethod
    def _add_dependencies(date_list, member_list, chunk_list, dic_jobs, parser):
        for section in parser.sections():
            Log.debug("Adding dependencies for {0} jobs".format(section))
            if not parser.has_option(section, "DEPENDENCIES"):
                continue
            dependencies = parser.get(section, "DEPENDENCIES").split()
            dep_section = dict()
            dep_distance = dict()
            dep_running = dict()

            for dependency in dependencies:
                JobList._treat_dependency(dep_distance, dep_running, dep_section, dependency, dic_jobs)

            for job in dic_jobs.get_jobs(section):
                JobList._treat_job(dic_jobs, job, date_list, member_list, chunk_list, dependencies, dep_distance,
                                   dep_running, dep_section)

    @staticmethod
    def _treat_job(dic_jobs, job, date_list, member_list, chunk_list, dependencies, dep_distance, dep_running,
                   dep_section):
        for dependency in dependencies:
            chunk = job.chunk
            member = job.member
            date = job.date

            section_name = dep_section[dependency]

            # Case dependency with previous execution of same job
            if '-' in dependency:
                distance = dep_distance[dependency]
                if chunk is not None and dep_running[dependency] == 'chunk':
                    chunk_index = chunk_list.index(chunk)
                    if chunk_index >= distance:
                        chunk = chunk_list[chunk_index - distance]
                    else:
                        continue
                elif member is not None and dep_running[dependency] in ['chunk', 'member']:
                    member_index = member_list.index(member)
                    if member_index >= distance:
                        member = member_list[member_index - distance]
                    else:
                        continue
                elif date is not None and dep_running[dependency] in ['chunk', 'member', 'startdate']:
                    date_index = date_list.index(date)
                    if date_index >= distance:
                        date = date_list[date_index - distance]
                    else:
                        continue

            # Adding the dependencies (parents) calculated above
            for parent in dic_jobs.get_jobs(section_name, date, member, chunk):
                job.add_parent(parent)

            JobList.handle_frequency_interval_dependencies(chunk, chunk_list, date, date_list, dic_jobs, job, member,
                                                           member_list, section_name)

    @staticmethod
    def handle_frequency_interval_dependencies(chunk, chunk_list, date, date_list, dic_jobs, job, member, member_list,
                                               section_name):
        if job.wait and job.frequency > 1:
            if job.chunk is not None:
                max_distance = (chunk_list.index(chunk) + 1) % job.frequency
                if max_distance == 0:
                    max_distance = job.frequency
                for distance in range(1, max_distance):
                    for parent in dic_jobs.get_jobs(section_name, date, member, chunk - distance):
                        job.add_parent(parent)
            elif job.member is not None:
                member_index = member_list.index(job.member)
                max_distance = (member_index + 1) % job.frequency
                if max_distance == 0:
                    max_distance = job.frequency
                for distance in range(1, max_distance, 1):
                    for parent in dic_jobs.get_jobs(section_name, date,
                                                    member_list[member_index - distance], chunk):
                        job.add_parent(parent)
            elif job.date is not None:
                date_index = date_list.index(job.date)
                max_distance = (date_index + 1) % job.frequency
                if max_distance == 0:
                    max_distance = job.frequency
                for distance in range(1, max_distance, 1):
                    for parent in dic_jobs.get_jobs(section_name, date_list[date_index - distance],
                                                    member, chunk):
                        job.add_parent(parent)

    @staticmethod
    def _treat_dependency(dep_distance, dep_running, dep_section, dependency, dic_jobs):
        if '-' in dependency:
            dependency_split = dependency.split('-')
            dep_section[dependency] = dependency_split[0]
            dep_distance[dependency] = int(dependency_split[1])
            dep_running[dependency] = dic_jobs.get_option(dependency_split[0], 'RUNNING', 'once').lower()
        else:
            dep_section[dependency] = dependency

    @staticmethod
    def _create_jobs(dic_jobs, parser, priority):
        for section in parser.sections():
            Log.debug("Creating {0} jobs".format(section))
            dic_jobs.read_section(section, priority)
            priority += 1

    def __len__(self):
        return self._job_list.__len__()

    def get_job_list(self):
        """
        Get inner job list

        :return: job list
        :rtype: list
        """
        return self._job_list

    def get_completed(self, platform=None):
        """
        Returns a list of completed jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: completed jobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.get_platform() is platform) and
                job.status == Status.COMPLETED]

    def get_submitted(self, platform=None):
        """
        Returns a list of submitted jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: submitted jobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.get_platform() is platform) and
                job.status == Status.SUBMITTED]

    def get_running(self, platform=None):
        """
        Returns a list of jobs running

        :param platform: job platform
        :type platform: HPCPlatform
        :return: running jobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.get_platform() is platform) and
                job.status == Status.RUNNING]

    def get_queuing(self, platform=None):
        """
        Returns a list of jobs queuing

        :param platform: job platform
        :type platform: HPCPlatform
        :return: queuedjobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.get_platform() is platform) and
                job.status == Status.QUEUING]

    def get_failed(self, platform=None):
        """
        Returns a list of failed jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: failed jobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.get_platform() is platform) and
                job.status == Status.FAILED]

    def get_ready(self, platform=None):
        """
        Returns a list of ready jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: ready jobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.get_platform() is platform) and
                job.status == Status.READY]

    def get_waiting(self, platform=None):
        """
        Returns a list of jobs waiting

        :param platform: job platform
        :type platform: HPCPlatform
        :return: waiting jobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.get_platform() is platform) and
                job.status == Status.WAITING]

    def get_unknown(self, platform=None):
        """
        Returns a list of jobs on unknown state

        :param platform: job platform
        :type platform: HPCPlatform
        :return: unknown state jobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.get_platform() is platform) and
                job.status == Status.UNKNOWN]

    def get_in_queue(self, platform=None):
        """
        Returns a list of jobs in the platforms (Submitted, Running, Queuing)

        :param platform: job platform
        :type platform: HPCPlatform
        :return: jobs in platforms
        :rtype: list
        """
        return self.get_submitted(platform) + self.get_running(platform) + self.get_queuing(platform)

    def get_not_in_queue(self, platform=None):
        """
        Returns a list of jobs NOT in the platforms (Ready, Waiting)

        :param platform: job platform
        :type platform: HPCPlatform
        :return: jobs not in platforms
        :rtype: list
        """
        return self.get_ready(platform) + self.get_waiting(platform)

    def get_finished(self, platform=None):
        """
        Returns a list of jobs finished (Completed, Failed)


        :param platform: job platform
        :type platform: HPCPlatform
        :return: finsihed jobs
        :rtype: list
        """
        return self.get_completed(platform) + self.get_failed(platform)

    def get_active(self, platform=None):
        """
        Returns a list of active jobs (In platforms, Ready)

        :param platform: job platform
        :type platform: HPCPlatform
        :return: active jobs
        :rtype: list
        """
        return self.get_in_queue(platform) + self.get_ready(platform) + self.get_unknown(platform)

    def get_job_by_name(self, name):
        """
        Returns the job that its name matches parameter name

        :parameter name: name to look for
        :type name: str
        :return: found job
        :rtype: job
        """
        for job in self._job_list:
            if job.name == name:
                return job
        Log.warning("We could not find that job {0} in the list!!!!", name)

    def sort_by_name(self):
        """
        Returns a list of jobs sorted by name

        :return: jobs sorted by name
        :rtype: list
        """
        return sorted(self._job_list, key=lambda k: k.name)

    def sort_by_id(self):
        """
        Returns a list of jobs sorted by id

        :return: jobs sorted by ID
        :rtype: list
        """
        return sorted(self._job_list, key=lambda k: k.id)

    def sort_by_type(self):
        """
        Returns a list of jobs sorted by type

        :return: job sorted by type
        :rtype: list
        """
        return sorted(self._job_list, key=lambda k: k.type)

    def sort_by_status(self):
        """
        Returns a list of jobs sorted by status

        :return: job sorted by status
        :rtype: list
        """
        return sorted(self._job_list, key=lambda k: k.status)

    @staticmethod
    def load_file(filename):
        """
        Recreates an stored joblist from the pickle file

        :param filename: pickle file to load
        :type filename: str
        :return: loaded joblist object
        :rtype: JobList
        """
        if os.path.exists(filename):
            fd = open(filename, 'rw')
            return pickle.load(fd)
        else:
            Log.critical('File {0} does not exist'.format(filename))
            return list()

    def load(self):
        """
        Recreates an stored joblist from the pickle file

        :return: loaded joblist object
        :rtype: JobList
        """
        Log.info("Loading JobList: " + self._pkl_path + self._job_list_file)
        return JobList.load_file(self._pkl_path + self._job_list_file)

    def save(self):
        """
        Stores joblist as a pickle file

        :return: loaded joblist object
        :rtype: JobList
        """
        path = os.path.join(self._pkl_path, self._job_list_file)
        fd = open(path, 'w')
        setrecursionlimit(50000)
        Log.debug("Saving JobList: " + path)
        pickle.dump(self, fd)
        Log.debug('Joblist saved')

    def update_from_file(self, store_change=True):
        """
        Updates joblist on the fly from and update file
        :param store_change: if True, renames the update file to avoid reloading it at the next iteration
        """
        if os.path.exists(os.path.join(self._pkl_path, self._update_file)):
            Log.info("Loading updated list: {0}".format(os.path.join(self._pkl_path, self._update_file)))
            for line in open(os.path.join(self._pkl_path, self._update_file)):
                if line.strip() == '':
                    continue
                job = self.get_job_by_name(line.split()[0])
                if job:
                    job.status = self._stat_val.retval(line.split()[1])
                    job.fail_count = 0
            now = localtime()
            output_date = strftime("%Y%m%d_%H%M", now)
            if store_change:
                move(os.path.join(self._pkl_path, self._update_file), os.path.join(self._pkl_path, self._update_file +
                                                                                   "_" + output_date))

    @property
    def parameters(self):
        """
        List of parameters common to all jobs
        :return: parameters
        :rtype: dict
        """
        return self._parameters

    @parameters.setter
    def parameters(self, value):
        self._parameters = value

    def update_list(self, as_conf):
        """
        Updates job list, resetting failed jobs and changing to READY all WAITING jobs with all parents COMPLETED

        :param as_conf: autosubmit config object
        :type as_conf: AutosubmitConfig
        :return: True if job status were modified, False otherwise
        :rtype: bool
        """
        # load updated file list
        save = False
        if self.update_from_file():
            save = True

        # reset jobs that has failed less than 10 times
        Log.debug('Updating FAILED jobs')
        for job in self.get_failed():
            job.inc_fail_count()
            if not hasattr(job, 'retrials') or job.retrials is None:
                retrials = as_conf.get_retrials()
            else:
                retrials = job.retrials

            if job.fail_count < retrials:
                tmp = [parent for parent in job.parents if parent.status == Status.COMPLETED]
                if len(tmp) == len(job.parents):
                    job.status = Status.READY
                    save = True
                    Log.debug("Resetting job: {0} status to: READY for retrial...".format(job.name))
                else:
                    job.status = Status.WAITING
                    save = True
                    Log.debug("Resetting job: {0} status to: WAITING for parents completion...".format(job.name))

        # if waiting jobs has all parents completed change its State to READY
        Log.debug('Updating WAITING jobs')
        for job in self.get_waiting():
            tmp = [parent for parent in job.parents if parent.status == Status.COMPLETED]
            # for parent in job.parents:
            # if parent.status != Status.COMPLETED:
            # break
            if len(tmp) == len(job.parents):
                job.status = Status.READY
                save = True
                Log.debug("Resetting job: {0} status to: READY (all parents completed)...".format(job.name))
        Log.debug('Update finished')
        return save

    def update_genealogy(self):
        """
        When we have created the joblist, every type of job is created.
        Update genealogy remove jobs that have no templates
        """

        # Use a copy of job_list because original is modified along iterations
        for job in self._job_list[:]:
            if job.file is None or job.file == '':
                self._remove_job(job)

        # Simplifying dependencies: if a parent is already an ancestor of another parent,
        # we remove parent dependency
        for job in self._job_list:
            for parent in list(job.parents):
                for ancestor in parent.ancestors:
                    if ancestor in job.parents:
                        job.parents.remove(ancestor)
                        ancestor.children.remove(job)

        for job in self._job_list:
            if not job.has_parents():
                job.status = Status.READY

    def check_scripts(self, as_conf):
        """
        When we have created the scripts, all parameters should have been substituted.
        %PARAMETER% handlers not allowed

        :param as_conf: experiment configuration
        :type as_conf: AutosubmitConfig
        """
        Log.info("Checking scripts...")
        out = True
        sections_checked = set()
        for job in self._job_list:
            if job.section in sections_checked:
                continue
            if not job.check_script(as_conf, self.parameters):
                out = False
                Log.warning("Invalid parameter substitution in {0} template!!!", job.section)
            sections_checked.add(job.section)
        if out:
            Log.result("Scripts OK")
        else:
            Log.error("Scripts check failed")
            Log.user_warning("Running after failed scripts check is at your own risk!")
        return out

    def _remove_job(self, job):
        """
        Remove a job from the list

        :param job: job to remove
        :type job: Job
        """
        for child in job.children:
            for parent in job.parents:
                child.add_parent(parent)
            child.delete_parent(job)

        for parent in job.parents:
            parent.children.remove(job)

        self._job_list.remove(job)

    def rerun(self, chunk_list):
        """
        Updates joblist to rerun the jobs specified by chunk_list

        :param chunk_list: list of chunks to rerun
        :type chunk_list: str
        """
        parser = self._parser_factory.create_parser()
        parser.optionxform = str
        parser.read(os.path.join(self._config.LOCAL_ROOT_DIR, self._expid, 'conf', "jobs_" + self._expid + ".conf"))

        Log.info("Adding dependencies...")
        dep_section = dict()
        dep_distance = dict()
        dependencies = dict()
        dep_running = dict()
        for section in parser.sections():
            Log.debug("Reading rerun dependencies for {0} jobs".format(section))
            if not parser.has_option(section, "RERUN_DEPENDENCIES"):
                continue
            dependencies[section] = parser.get(section, "RERUN_DEPENDENCIES").split()
            dep_section[section] = dict()
            dep_distance[section] = dict()
            dep_running[section] = dict()
            for dependency in dependencies[section]:
                JobList._treat_dependency(dep_distance[section], dep_running[section], dep_section[section], dependency,
                                          self._dic_jobs)

        for job in self._job_list:
            job.status = Status.COMPLETED

        data = json.loads(chunk_list)
        for d in data['sds']:
            date = parse_date(d['sd'])
            Log.debug("Date: {0}", date)
            for m in d['ms']:
                member = m['m']
                Log.debug("Member: " + member)
                previous_chunk = 0
                for c in m['cs']:
                    Log.debug("Chunk: " + c)
                    chunk = int(c)
                    for job in [i for i in self._job_list if i.date == date and i.member == member and
                                    i.chunk == chunk]:
                        if not job.rerun_only or chunk != previous_chunk + 1:
                            job.status = Status.WAITING
                            Log.debug("Job: " + job.name)
                        section = job.section
                        if section not in dependencies:
                            continue
                        for dependency in dependencies[section]:
                            current_chunk = chunk
                            current_member = member
                            current_date = date
                            if '-' in dependency:
                                distance = dep_distance[section][dependency]
                                running = dep_running[section][dependency]
                                if current_chunk is not None and running == 'chunk':
                                    chunk_index = self._chunk_list.index(current_chunk)
                                    if chunk_index >= distance:
                                        current_chunk = self._chunk_list[chunk_index - distance]
                                    else:
                                        continue
                                elif current_member is not None and running in ['chunk', 'member']:
                                    member_index = self._member_list.index(current_member)
                                    if member_index >= distance:
                                        current_member = self._member_list[member_index - distance]
                                    else:
                                        continue
                                elif current_date is not None and running in ['chunk', 'member', 'startdate']:
                                    date_index = self._date_list.index(current_date)
                                    if date_index >= distance:
                                        current_date = self._date_list[date_index - distance]
                                    else:
                                        continue
                            section_name = dep_section[section][dependency]
                            for parent in self._dic_jobs.get_jobs(section_name, current_date, current_member,
                                                                  current_chunk):
                                parent.status = Status.WAITING
                                Log.debug("Parent: " + parent.name)

        for job in [j for j in self._job_list if j.status == Status.COMPLETED]:
            self._remove_job(job)

        for job in [j for j in self._job_list if j.status == Status.COMPLETED]:
            self._remove_job(job)

        self.update_genealogy()

    def remove_rerun_only_jobs(self):
        """
        Removes all jobs to be runned only in reruns
        """
        flag = False
        for job in set(self._job_list):
            if job.rerun_only:
                self._remove_job(job)
                flag = True

        if flag:
            self.update_genealogy()
        del self._dic_jobs


class DicJobs:
    """
    Class to create jobs from conf file and to find jobs by stardate, member and chunk

    :param joblist: joblist to use
    :type joblist: JobList
    :param parser: jobs conf file parser
    :type parser: SafeConfigParser
    :param date_list: startdates
    :type date_list: list
    :param member_list: member
    :type member_list: list
    :param chunk_list: chunks
    :type chunk_list: list
    :param date_format: option to formate dates
    :type date_format: str
    :param default_retrials: default retrials for ech job
    :type default_retrials: int

    """

    def __init__(self, joblist, parser, date_list, member_list, chunk_list, date_format, default_retrials):
        self._date_list = date_list
        self._joblist = joblist
        self._member_list = member_list
        self._chunk_list = chunk_list
        self._parser = parser
        self._date_format = date_format
        self.default_retrials = default_retrials
        self._dic = dict()

    def read_section(self, section, priority):
        """
        Read a section from jobs conf and creates all jobs for it

        :param section: section to read
        :type section: str
        :param priority: priority for the jobs
        :type priority: int
        """
        running = 'once'
        if self._parser.has_option(section, 'RUNNING'):
            running = self._parser.get(section, 'RUNNING').lower()
        frequency = int(self.get_option(section, "FREQUENCY", 1))
        if running == 'once':
            self._create_jobs_once(section, priority)
        elif running == 'date':
            self._create_jobs_startdate(section, priority, frequency)
        elif running == 'member':
            self._create_jobs_member(section, priority, frequency)
        elif running == 'chunk':
            synchronize = self.get_option(section, "SYNCHRONIZE", None)
            self._create_jobs_chunk(section, priority, frequency, synchronize)

    def _create_jobs_once(self, section, priority):
        """
        Create jobs to be run once

        :param section: section to read
        :type section: str
        :param priority: priority for the jobs
        :type priority: int
        """
        self._dic[section] = self._create_job(section, priority, None, None, None)

    def _create_jobs_startdate(self, section, priority, frequency):
        """
        Create jobs to be run once per startdate

        :param section: section to read
        :type section: str
        :param priority: priority for the jobs
        :type priority: int
        :param frequency: if greater than 1, only creates one job each frequency startdates. Allways creates one job
                          for the last
        :type frequency: int
        """
        self._dic[section] = dict()
        count = 0
        for date in self._date_list:
            count += 1
            if count % frequency == 0 or count == len(self._date_list):
                self._dic[section][date] = self._create_job(section, priority, date, None, None)

    def _create_jobs_member(self, section, priority, frequency):
        """
        Create jobs to be run once per member

        :param section: section to read
        :type section: str
        :param priority: priority for the jobs
        :type priority: int
        :param frequency: if greater than 1, only creates one job each frequency members. Allways creates one job
                          for the last
        :type frequency: int
        """
        self._dic[section] = dict()
        for date in self._date_list:
            self._dic[section][date] = dict()
            count = 0
            for member in self._member_list:
                count += 1
                if count % frequency == 0 or count == len(self._member_list):
                    self._dic[section][date][member] = self._create_job(section, priority, date, member, None)

    '''
        Maybe a good choice could be split this function or ascend the
        conditional decision to the father which makes the call
    '''

    def _create_jobs_chunk(self, section, priority, frequency, synchronize=None):
        """
        Create jobs to be run once per chunk

        :param synchronize:
        :param section: section to read
        :type section: str
        :param priority: priority for the jobs
        :type priority: int
        :param frequency: if greater than 1, only creates one job each frequency chunks. Always creates one job
                          for the last
        :type frequency: int
        """
        # Temporally creation for unified jobs in case of synchronize
        if synchronize is not None:
            tmp_dic = dict()
            count = 0
            for chunk in self._chunk_list:
                count += 1
                if count % frequency == 0 or count == len(self._chunk_list):
                    if synchronize == 'date':
                        tmp_dic[chunk] = self._create_job(section, priority, None, None,
                                                          chunk)
                    elif synchronize == 'member':
                        tmp_dic[chunk] = dict()
                        for date in self._date_list:
                            tmp_dic[chunk][date] = self._create_job(section, priority, date, None,
                                                                    chunk)
        # Real dic jobs assignment/creation
        self._dic[section] = dict()
        for date in self._date_list:
            self._dic[section][date] = dict()
            for member in self._member_list:
                self._dic[section][date][member] = dict()
                count = 0
                for chunk in self._chunk_list:
                    count += 1
                    if count % frequency == 0 or count == len(self._chunk_list):
                        if synchronize == 'date':
                            self._dic[section][date][member][chunk] = tmp_dic[chunk]
                        elif synchronize == 'member':
                            self._dic[section][date][member][chunk] = tmp_dic[chunk][date]
                        else:
                            self._dic[section][date][member][chunk] = self._create_job(section, priority, date, member,
                                                                                       chunk)

    def get_jobs(self, section, date=None, member=None, chunk=None):
        """
        Return all the jobs matching section, date, member and chunk provided. If any parameter is none, returns all
        the jobs without checking that parameter value. If a job has one parameter to None, is returned if all the
        others match parameters passed

        :param section: section to return
        :type section: str
        :param date: stardate to return
        :type date: str
        :param member: member to return
        :type member: str
        :param chunk: chunk to return
        :type chunk: int
        :return: jobs matching parameters passed
        :rtype: list
        """
        jobs = list()
        dic = self._dic[section]
        if type(dic) is not dict:
            jobs.append(dic)
        else:
            if date is not None:
                self._get_date(jobs, dic, date, member, chunk)
            else:
                for d in self._date_list:
                    self._get_date(jobs, dic, d, member, chunk)
        return jobs

    def _get_date(self, jobs, dic, date, member, chunk):
        if date not in dic:
            return jobs
        dic = dic[date]
        if type(dic) is not dict:
            jobs.append(dic)
        else:
            if member is not None:
                self._get_member(jobs, dic, member, chunk)
            else:
                for m in self._member_list:
                    self._get_member(jobs, dic, m, chunk)

        return jobs

    def _get_member(self, jobs, dic, member, chunk):
        if member not in dic:
            return jobs
        dic = dic[member]
        if type(dic) is not dict:
            jobs.append(dic)
        else:
            if chunk is not None and chunk in dic:
                jobs.append(dic[chunk])
            else:
                for c in self._chunk_list:
                    if c not in dic:
                        continue
                    jobs.append(dic[c])
        return jobs

    def _create_job(self, section, priority, date, member, chunk):
        name = self._joblist.expid
        if date is not None:
            name += "_" + date2str(date, self._date_format)
        if member is not None:
            name += "_" + member
        if chunk is not None:
            name += "_{0}".format(chunk)
        name += "_" + section
        job = Job(name, 0, Status.WAITING, priority)
        job.section = section
        job.date = date
        job.member = member
        job.chunk = chunk
        job.date_format = self._date_format

        job.frequency = int(self.get_option(section, "FREQUENCY", 1))
        job.wait = self.get_option(section, "WAIT", 'true').lower() == 'true'
        job.rerun_only = self.get_option(section, "RERUN_ONLY", 'false').lower() == 'true'

        type = self.get_option(section, "TYPE", 'bash').lower()
        if type == 'bash':
            job.type = Type.BASH
        elif type == 'python':
            job.type = Type.PYTHON
        elif type == 'r':
            job.type = Type.R

        job.platform_name = self.get_option(section, "PLATFORM", None)
        if job.platform_name is not None:
            job.platform_name = job.platform_name
        job.file = self.get_option(section, "FILE", None)
        job.set_queue(self.get_option(section, "QUEUE", None))
        if self.get_option(section, "CHECK", 'True').lower() == 'true':
            job.check = True
        else:
            job.check = False

        job.processors = self.get_option(section, "PROCESSORS", 1)
        job.threads = self.get_option(section, "THREADS", 1)
        job.tasks = self.get_option(section, "TASKS", 1)
        job.memory = self.get_option(section, "MEMORY", '')
        job.wallclock = self.get_option(section, "WALLCLOCK", '')
        job.retrials = int(self.get_option(section, 'RETRIALS', -1))
        if job.retrials == -1:
            job.retrials = None
        job.notify_on = [x.upper() for x in self.get_option(section, "NOTIFY_ON", '').split(' ')]
        self._joblist.get_job_list().append(job)
        return job

    def get_option(self, section, option, default):
        """
        Returns value for a given option

        :param section: section name
        :type section: str
        :param option: option to return
        :type option: str
        :param default: value to return if not defined in configuration file
        :type default: object
        """
        if self._parser.has_option(section, option):
            return self._parser.get(section, option)
        else:
            return default
