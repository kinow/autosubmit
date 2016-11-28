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
from autosubmit.job.job_package import JobPackageSimple
from autosubmit.job.job_package import JobPackageArray
from autosubmit.config.log import Log
from autosubmit.date.chunk_date_lib import date2str, parse_date

from networkx import DiGraph
from autosubmit.job.job_utils import transitive_reduction


class JobList:
    """
    Class to manage the list of jobs to be run by autosubmit

    """

    def __init__(self, expid, config, parser_factory, job_list_persistence):
        self._persistence_path = os.path.join(config.LOCAL_ROOT_DIR, expid, "pkl")
        self._update_file = "updated_list_" + expid + ".txt"
        self._failed_file = "failed_job_list_" + expid + ".pkl"
        self._persistence_file = "job_list_" + expid
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
        self._persistence = job_list_persistence
        self._graph = DiGraph()

    @property
    def expid(self):
        """
        Returns the experiment identifier

        :return: experiment's identifier
        :rtype: str
        """
        return self._expid

    @property
    def graph(self):
        """
        Returns the graph

        :return: graph
        :rtype: networkx graph
        """
        return self._graph

    @graph.setter
    def graph(self, value):
        self._graph = value

    def generate(self, date_list, member_list, num_chunks, parameters, date_format, default_retrials, default_job_type,
                 new=True):
        """
        Creates all jobs needed for the current workflow

        :param default_job_type: default type for jobs
        :type default_job_type: str
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
        :param new: is it a new generation?
        :type new: bool
        """
        self._parameters = parameters
        self._date_list = date_list
        self._member_list = member_list

        chunk_list = range(1, num_chunks + 1)
        self._chunk_list = chunk_list

        jobs_parser = self._get_jobs_parser()

        dic_jobs = DicJobs(self, jobs_parser, date_list, member_list, chunk_list, date_format, default_retrials)
        self._dic_jobs = dic_jobs
        priority = 0

        Log.info("Creating jobs...")
        jobs_data = dict()
        if not new:
            jobs_data = {str(row[0]): row for row in self.load()}
        self._create_jobs(dic_jobs, jobs_parser, priority, default_job_type, jobs_data)

        Log.info("Adding dependencies...")
        self._add_dependencies(date_list, member_list, chunk_list, dic_jobs, jobs_parser, self.graph)

        Log.info("Removing redundant dependencies...")
        self.update_genealogy(new)
        for job in self._job_list:
            job.parameters = parameters

    @staticmethod
    def _add_dependencies(date_list, member_list, chunk_list, dic_jobs, jobs_parser, graph, option="DEPENDENCIES"):
        for job_section in jobs_parser.sections():
            Log.debug("Adding dependencies for {0} jobs".format(job_section))

            # If does not has dependencies, do nothing
            if not jobs_parser.has_option(job_section, option):
                continue

            dependencies_keys = jobs_parser.get(job_section, option).split()
            dependencies = JobList._manage_dependencies(dependencies_keys, dic_jobs)

            for job in dic_jobs.get_jobs(job_section):
                JobList._manage_job_dependencies(dic_jobs, job, date_list, member_list, chunk_list, dependencies_keys,
                                                 dependencies, graph)

    @staticmethod
    def _manage_dependencies(dependencies_keys, dic_jobs):
        dependencies = dict()
        for key in dependencies_keys:
            if '-' not in key and '+' not in key:
                dependencies[key] = Dependency(key)
            else:
                sign = '-' if '-' in key else '+'
                key_split = key.split(sign)
                dependency_running_type = dic_jobs.get_option(key_split[0], 'RUNNING', 'once').lower()
                dependency = Dependency(key_split[0], int(key_split[1]), dependency_running_type, sign)
                dependencies[key] = dependency
        return dependencies

    @staticmethod
    def _manage_job_dependencies(dic_jobs, job, date_list, member_list, chunk_list, dependencies_keys, dependencies, graph):
        for key in dependencies_keys:
            dependency = dependencies[key]
            skip, (chunk, member, date) = JobList._calculate_dependency_metadata(job.chunk, chunk_list,
                                                                                 job.member, member_list,
                                                                                 job.date, date_list,
                                                                                 dependency)
            if skip:
                continue

            for parent in dic_jobs.get_jobs(dependency.section, date, member, chunk):
                job.add_parent(parent)
                graph.add_edge(parent.name, job.name)

            JobList.handle_frequency_interval_dependencies(chunk, chunk_list, date, date_list, dic_jobs, job, member,
                                                           member_list, dependency.section, graph)

    @staticmethod
    def _calculate_dependency_metadata(chunk, chunk_list, member, member_list, date, date_list, dependency):
        skip = False
        if dependency.sign is '-':
            if chunk is not None and dependency.running == 'chunk':
                chunk_index = chunk_list.index(chunk)
                if chunk_index >= dependency.distance:
                    chunk = chunk_list[chunk_index - dependency.distance]
                else:
                    skip = True
            elif member is not None and dependency.running in ['chunk', 'member']:
                member_index = member_list.index(member)
                if member_index >= dependency.distance:
                    member = member_list[member_index - dependency.distance]
                else:
                    skip = True
            elif date is not None and dependency.running in ['chunk', 'member', 'startdate']:
                date_index = date_list.index(date)
                if date_index >= dependency.distance:
                    date = date_list[date_index - dependency.distance]
                else:
                    skip = True

        if dependency.sign is '+':
            if chunk is not None and dependency.running == 'chunk':
                chunk_index = chunk_list.index(chunk)
                if (chunk_index + dependency.distance) < len(chunk_list):
                    chunk = chunk_list[chunk_index + dependency.distance]
                else:  # calculating the next one possible
                    temp_distance = dependency.distance
                    while temp_distance > 0:
                        temp_distance -= 1
                        if (chunk_index + temp_distance) < len(chunk_list):
                            chunk = chunk_list[chunk_index + temp_distance]
                            break

            elif member is not None and dependency.running in ['chunk', 'member']:
                member_index = member_list.index(member)
                if (member_index + dependency.distance) < len(member_list):
                    member = member_list[member_index + dependency.distance]
                else:
                    skip = True
            elif date is not None and dependency.running in ['chunk', 'member', 'startdate']:
                date_index = date_list.index(date)
                if (date_index + dependency.distance) < len(date_list):
                    date = date_list[date_index - dependency.distance]
                else:
                    skip = True
        return skip, (chunk, member, date)

    @staticmethod
    def handle_frequency_interval_dependencies(chunk, chunk_list, date, date_list, dic_jobs, job, member, member_list,
                                               section_name, graph):
        if job.wait and job.frequency > 1:
            if job.chunk is not None:
                max_distance = (chunk_list.index(chunk) + 1) % job.frequency
                if max_distance == 0:
                    max_distance = job.frequency
                for distance in range(1, max_distance):
                    for parent in dic_jobs.get_jobs(section_name, date, member, chunk - distance):
                        job.add_parent(parent)
                        graph.add_edge(parent.name, job.name)
            elif job.member is not None:
                member_index = member_list.index(job.member)
                max_distance = (member_index + 1) % job.frequency
                if max_distance == 0:
                    max_distance = job.frequency
                for distance in range(1, max_distance, 1):
                    for parent in dic_jobs.get_jobs(section_name, date,
                                                    member_list[member_index - distance], chunk):
                        job.add_parent(parent)
                        graph.add_edge(parent.name, job.name)
            elif job.date is not None:
                date_index = date_list.index(job.date)
                max_distance = (date_index + 1) % job.frequency
                if max_distance == 0:
                    max_distance = job.frequency
                for distance in range(1, max_distance, 1):
                    for parent in dic_jobs.get_jobs(section_name, date_list[date_index - distance],
                                                    member, chunk):
                        job.add_parent(parent)
                        graph.add_edge(parent.name, job.name)

    @staticmethod
    def _create_jobs(dic_jobs, parser, priority, default_job_type, jobs_data=dict()):
        for section in parser.sections():
            Log.debug("Creating {0} jobs".format(section))
            dic_jobs.read_section(section, priority, default_job_type, jobs_data)
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
        return [job for job in self._job_list if (platform is None or job.platform is platform) and
                job.status == Status.COMPLETED]

    def get_submitted(self, platform=None):
        """
        Returns a list of submitted jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: submitted jobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.platform is platform) and
                job.status == Status.SUBMITTED]

    def get_running(self, platform=None):
        """
        Returns a list of jobs running

        :param platform: job platform
        :type platform: HPCPlatform
        :return: running jobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.platform is platform) and
                job.status == Status.RUNNING]

    def get_queuing(self, platform=None):
        """
        Returns a list of jobs queuing

        :param platform: job platform
        :type platform: HPCPlatform
        :return: queuedjobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.platform is platform) and
                job.status == Status.QUEUING]

    def get_failed(self, platform=None):
        """
        Returns a list of failed jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: failed jobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.platform is platform) and
                job.status == Status.FAILED]

    def get_ready(self, platform=None):
        """
        Returns a list of ready jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: ready jobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.platform is platform) and
                job.status == Status.READY]

    def get_waiting(self, platform=None):
        """
        Returns a list of jobs waiting

        :param platform: job platform
        :type platform: HPCPlatform
        :return: waiting jobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.platform is platform) and
                job.status == Status.WAITING]

    def get_unknown(self, platform=None):
        """
        Returns a list of jobs on unknown state

        :param platform: job platform
        :type platform: HPCPlatform
        :return: unknown state jobs
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.platform is platform) and
                job.status == Status.UNKNOWN]

    def get_in_queue(self, platform=None):
        """
        Returns a list of jobs in the platforms (Submitted, Running, Queuing, Unknown)

        :param platform: job platform
        :type platform: HPCPlatform
        :return: jobs in platforms
        :rtype: list
        """
        return self.get_submitted(platform) + self.get_running(platform) + self.get_queuing(
            platform) + self.get_unknown(platform)

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
        return self.get_in_queue(platform) + self.get_ready(platform)

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
        Recreates an stored job list from the persistence

        :return: loaded job list object
        :rtype: JobList
        """
        Log.info("Loading JobList")
        return self._persistence.load(self._persistence_path, self._persistence_file)

    def save(self):
        """
        Persists the job list
        """
        self._persistence.save(self._persistence_path, self._persistence_file, self._job_list)

    def update_from_file(self, store_change=True):
        """
        Updates joblist on the fly from and update file
        :param store_change: if True, renames the update file to avoid reloading it at the next iteration
        """
        if os.path.exists(os.path.join(self._persistence_path, self._update_file)):
            Log.info("Loading updated list: {0}".format(os.path.join(self._persistence_path, self._update_file)))
            for line in open(os.path.join(self._persistence_path, self._update_file)):
                if line.strip() == '':
                    continue
                job = self.get_job_by_name(line.split()[0])
                if job:
                    job.status = self._stat_val.retval(line.split()[1])
                    job.fail_count = 0
            now = localtime()
            output_date = strftime("%Y%m%d_%H%M", now)
            if store_change:
                move(os.path.join(self._persistence_path, self._update_file),
                     os.path.join(self._persistence_path, self._update_file +
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

            if job.fail_count <= retrials:
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
            if len(tmp) == len(job.parents):
                job.status = Status.READY
                save = True
                Log.debug("Resetting job: {0} status to: READY (all parents completed)...".format(job.name))
        Log.debug('Update finished')
        return save

    def update_genealogy(self, new=True):
        """
        When we have created the job list, every type of job is created.
        Update genealogy remove jobs that have no templates
        :param new: if it is a new job list or not
        :type new: bool
        """

        # Use a copy of job_list because original is modified along iterations
        for job in self._job_list[:]:
            if job.file is None or job.file == '':
                self._remove_job(job)

        # Simplifying dependencies: if a parent is already an ancestor of another parent,
        # we remove parent dependency
        self.graph = transitive_reduction(self.graph)
        for job in self._job_list:
            children_to_remove = [child for child in job.children if child.name not in self.graph.neighbors(job.name)]
            for child in children_to_remove:
                job.children.remove(child)
                child.parents.remove(job)

        for job in self._job_list:
            if not job.has_parents() and new:
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
        Updates job list to rerun the jobs specified by chunk_list

        :param chunk_list: list of chunks to rerun
        :type chunk_list: str
        """
        jobs_parser = self._get_jobs_parser()

        Log.info("Adding dependencies...")
        for job_section in jobs_parser.sections():
            Log.debug("Reading rerun dependencies for {0} jobs".format(job_section))

            # If does not has rerun dependencies, do nothing
            if not jobs_parser.has_option(job_section, "RERUN_DEPENDENCIES"):
                continue

            dependencies_keys = jobs_parser.get(job_section, "RERUN_DEPENDENCIES").split()
            dependencies = JobList._manage_dependencies(dependencies_keys, self._dic_jobs)

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

                        job_section = job.section
                        if job_section not in dependencies:
                            continue

                        for key in dependencies_keys:
                            skip, (chunk, member, date) = JobList._calculate_dependency_metadata(chunk, member, date,
                                                                                                 dependencies[key])
                            if skip:
                                continue

                            section_name = dependencies[key].section
                            for parent in self._dic_jobs.get_jobs(section_name, current_date, current_member,
                                                                  current_chunk):
                                parent.status = Status.WAITING
                                Log.debug("Parent: " + parent.name)

        for job in [j for j in self._job_list if j.status == Status.COMPLETED]:
            self._remove_job(job)

        for job in [j for j in self._job_list if j.status == Status.COMPLETED]:
            self._remove_job(job)

        self.update_genealogy()

    def _get_jobs_parser(self):
        jobs_parser = self._parser_factory.create_parser()
        jobs_parser.optionxform = str
        jobs_parser.read(
            os.path.join(self._config.LOCAL_ROOT_DIR, self._expid, 'conf', "jobs_" + self._expid + ".conf"))
        return jobs_parser

    def remove_rerun_only_jobs(self):
        """
        Removes all jobs to be run only in reruns
        """
        flag = False
        for job in set(self._job_list):
            if job.rerun_only:
                self._remove_job(job)
                flag = True

        if flag:
            self.update_genealogy()
        del self._dic_jobs

    def get_ready_packages(self, platform):
        # Check there are ready jobs
        jobs_available = self.get_ready(platform)
        if len(jobs_available) == 0:
            return list()
        Log.info("\nJobs ready for {1}: {0}", len(jobs_available), platform.name)
        # Checking available submission slots
        max_waiting_jobs = platform.max_waiting_jobs
        waiting_jobs = len(self.get_submitted(platform) + self.get_queuing(platform))
        max_wait_jobs_to_submit = max_waiting_jobs - waiting_jobs
        max_jobs_to_submit = platform.total_jobs - len(self.get_in_queue(platform))
        # Logging obtained data
        Log.debug("Number of jobs ready: {0}", len(jobs_available))
        Log.debug("Number of jobs available: {0}", max_wait_jobs_to_submit)
        Log.info("Jobs to submit: {0}", min(max_wait_jobs_to_submit, len(jobs_available)))
        # If can submit jobs
        if max_wait_jobs_to_submit > 0 and max_jobs_to_submit > 0:
            available_sorted = sorted(jobs_available, key=lambda k: k.long_name.split('_')[1][:6])
            list_of_available = sorted(available_sorted, key=lambda k: k.priority, reverse=True)
            num_jobs_to_submit = min(max_wait_jobs_to_submit, len(jobs_available), max_jobs_to_submit)
            jobs_to_submit = list_of_available[0:num_jobs_to_submit]
            jobs_to_submit_by_section = self.divide_list_by_section(jobs_to_submit)
            packages_to_submit = list()
            if platform.allow_arrays:
                for section_list in jobs_to_submit_by_section.values():
                    packages_to_submit.append(JobPackageArray(section_list))
                return packages_to_submit
            for job in jobs_to_submit:
                packages_to_submit.append(JobPackageSimple([job]))
            return packages_to_submit
        return list()  # no packages to submit

    @staticmethod
    def divide_list_by_section(jobs_list):
        """
        Returns a dict() with as many keys as 'jobs_list' different sections.
        The value for each key is a list() with all the jobs with the key section.

        :param jobs_list: list of jobs to be divided
        :rtype: dict
        """
        by_section = dict()
        for job in jobs_list:
            if job.section not in by_section:
                by_section[job.section] = list()
            by_section[job.section].append(job)
        return by_section


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

    def read_section(self, section, priority, default_job_type, jobs_data=dict()):
        """
        Read a section from jobs conf and creates all jobs for it

        :param default_job_type: default type for jobs
        :type default_job_type: str
        :param jobs_data: dictionary containing the plain data from jobs
        :type jobs_data: dict
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
            self._create_jobs_once(section, priority, default_job_type, jobs_data)
        elif running == 'date':
            self._create_jobs_startdate(section, priority, frequency, default_job_type, jobs_data)
        elif running == 'member':
            self._create_jobs_member(section, priority, frequency, default_job_type, jobs_data)
        elif running == 'chunk':
            synchronize = self.get_option(section, "SYNCHRONIZE", None)
            self._create_jobs_chunk(section, priority, frequency, default_job_type, synchronize, jobs_data)

    def _create_jobs_once(self, section, priority, default_job_type, jobs_data=dict()):
        """
        Create jobs to be run once

        :param section: section to read
        :type section: str
        :param priority: priority for the jobs
        :type priority: int
        """
        self._dic[section] = self.build_job(section, priority, None, None, None, default_job_type, jobs_data)
        self._joblist.graph.add_node(self._dic[section].name)

    def _create_jobs_startdate(self, section, priority, frequency, default_job_type, jobs_data=dict()):
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
                self._dic[section][date] = self.build_job(section, priority, date, None, None, default_job_type,
                                                          jobs_data)
                self._joblist.graph.add_node(self._dic[section][date].name)

    def _create_jobs_member(self, section, priority, frequency, default_job_type, jobs_data=dict()):
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
                    self._dic[section][date][member] = self.build_job(section, priority, date, member, None,
                                                                      default_job_type, jobs_data)
                    self._joblist.graph.add_node(self._dic[section][date][member].name)

    '''
        Maybe a good choice could be split this function or ascend the
        conditional decision to the father which makes the call
    '''

    def _create_jobs_chunk(self, section, priority, frequency, default_job_type, synchronize=None, jobs_data=dict()):
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
                        tmp_dic[chunk] = self.build_job(section, priority, None, None,
                                                        chunk, default_job_type, jobs_data)
                    elif synchronize == 'member':
                        tmp_dic[chunk] = dict()
                        for date in self._date_list:
                            tmp_dic[chunk][date] = self.build_job(section, priority, date, None,
                                                                  chunk, default_job_type, jobs_data)
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
                            self._dic[section][date][member][chunk] = self.build_job(section, priority, date, member,
                                                                                     chunk, default_job_type, jobs_data)
                        self._joblist.graph.add_node(self._dic[section][date][member][chunk].name)

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

        if section not in self._dic:
            return jobs

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

    def build_job(self, section, priority, date, member, chunk, default_job_type, jobs_data=dict()):
        name = self._joblist.expid
        if date is not None:
            name += "_" + date2str(date, self._date_format)
        if member is not None:
            name += "_" + member
        if chunk is not None:
            name += "_{0}".format(chunk)
        name += "_" + section
        if name in jobs_data:
            job = Job(name, jobs_data[name][1], jobs_data[name][2], priority)
            job.local_logs = (jobs_data[name][8], jobs_data[name][9])
            job.remote_logs = (jobs_data[name][10], jobs_data[name][11])
        else:
            job = Job(name, 0, Status.WAITING, priority)
        job.section = section
        job.date = date
        job.member = member
        job.chunk = chunk
        job.date_format = self._date_format

        job.frequency = int(self.get_option(section, "FREQUENCY", 1))
        job.wait = self.get_option(section, "WAIT", 'true').lower() == 'true'
        job.rerun_only = self.get_option(section, "RERUN_ONLY", 'false').lower() == 'true'

        type = self.get_option(section, "TYPE", default_job_type).lower()
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
        job.queue = self.get_option(section, "QUEUE", None)
        if self.get_option(section, "CHECK", 'True').lower() == 'true':
            job.check = True
        else:
            job.check = False

        job.processors = self.get_option(section, "PROCESSORS", 1)
        job.threads = self.get_option(section, "THREADS", '')
        job.tasks = self.get_option(section, "TASKS", '')
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


class Dependency(object):
    """
    Class to manage the metadata related with a dependency

    """

    def __init__(self, section, distance=None, running=None, sign=None):
        self.section = section
        self.distance = distance
        self.running = running
        self.sign = sign
