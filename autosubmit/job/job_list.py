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
try:
    # noinspection PyCompatibility
    from configparser import SafeConfigParser
except ImportError:
    # noinspection PyCompatibility
    from ConfigParser import SafeConfigParser
import json
import re
import os
import pickle
import traceback
import math

from time import localtime, strftime, mktime
from shutil import move
from autosubmit.job.job import Job
from autosubmit.job.job_package_persistence import JobPackagePersistence
from autosubmit.job.job_dict import DicJobs
from autosubmit.job.job_utils import Dependency
from autosubmit.job.job_common import Status, bcolors
from bscearth.utils.date import date2str, parse_date
import autosubmit.database.db_structure as DbStructure
import datetime
from networkx import DiGraph
from autosubmit.job.job_utils import transitive_reduction
from log.log import AutosubmitCritical, AutosubmitError, Log
from threading import Thread, Lock
import multiprocessing
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.config.config_common import AutosubmitConfig
from autosubmit.helpers.data_transfer import JobRow
from typing import List, Dict
import log.fd_show
# Log.get_logger("Log.Autosubmit")


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.name = "data_processing"
        thread.start()
        return thread
    return wrapper


class JobList(object):
    """
    Class to manage the list of jobs to be run by autosubmit

    """

    def __init__(self, expid, config, parser_factory, job_list_persistence):
        self._persistence_path = os.path.join(
            config.LOCAL_ROOT_DIR, expid, "pkl")
        self._update_file = "updated_list_" + expid + ".txt"
        self._failed_file = "failed_job_list_" + expid + ".pkl"
        self._persistence_file = "job_list_" + expid
        self._job_list = list()
        self._base_job_list = list()
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

        self.packages_dict = dict()
        self._ordered_jobs_by_date_member = dict()

        self.packages_id = dict()
        self.job_package_map = dict()
        self.sections_checked = set()
        self._run_members = None
        self.jobs_to_run_first = list()
        self.rerun_job_list = list()
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

    @property
    def run_members(self):
        return self._run_members

    @run_members.setter
    def run_members(self, value):
        if value is not None:
            self._run_members = value
            self._base_job_list = [job for job in self._job_list]            
            found_member = False
            processed_job_list = []
            for job in self._job_list: # We are assuming that the jobs are sorted in topological order (which is the default)
                if (job.member is None and found_member == False) or job.member in self._run_members or job.status not in [Status.WAITING, Status.READY]:
                    processed_job_list.append(job)
                if job.member is not None:
                    found_member = True
            self._job_list = processed_job_list    
            # Old implementation that also considered children of the members.        
            # self._job_list = [job for job in old_job_list if len(
            #     job.parents) == 0 or len(set(old_job_list_names).intersection(set([jobp.name for jobp in job.parents]))) == len(job.parents)]

    def create_dictionary(self, date_list, member_list, num_chunks, chunk_ini, date_format, default_retrials, wrapper_jobs):
        chunk_list = range(chunk_ini, num_chunks + 1)

        jobs_parser = self._get_jobs_parser()
        dic_jobs = DicJobs(self, jobs_parser, date_list, member_list,
                           chunk_list, date_format, default_retrials)
        self._dic_jobs = dic_jobs
        # Perhaps this should be done by default independent of the wrapper_type supplied
        for wrapper_section in wrapper_jobs:
            if wrapper_jobs[wrapper_section] != 'None':
                self._ordered_jobs_by_date_member[wrapper_section] = self._create_sorted_dict_jobs(wrapper_jobs[wrapper_section])
            else:
                self._ordered_jobs_by_date_member[wrapper_section] = {}
        pass
    def generate(self, date_list, member_list, num_chunks, chunk_ini, parameters, date_format, default_retrials,
                 default_job_type, wrapper_type=None, wrapper_jobs=dict(), new=True, notransitive=False, update_structure=False, run_only_members=[],show_log=True):
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
        :param chunk_ini: the experiment will start by the given chunk
        :type chunk_ini: int
        :param parameters: parameters for the jobs
        :type parameters: dict
        :param date_format: option to format dates
        :type date_format: str
        :param default_retrials: default retrials for ech job
        :type default_retrials: int
        :param new: is it a new generation?
        :type new: bool \n
        :param wrapper_type: Type of wrapper defined by the user in autosubmit_.conf [wrapper] section. \n
        :type wrapper type: String \n
        :param wrapper_jobs: Job types defined in autosubmit_.conf [wrapper sections] to be wrapped. \n
        :type wrapper_jobs: String \n
        """
        self._parameters = parameters
        self._date_list = date_list
        self._member_list = member_list
        chunk_list = range(chunk_ini, num_chunks + 1)
        self._chunk_list = chunk_list

        jobs_parser = self._get_jobs_parser()

        dic_jobs = DicJobs(self, jobs_parser, date_list, member_list,chunk_list, date_format, default_retrials)
        self._dic_jobs = dic_jobs
        priority = 0
        if show_log:
            Log.info("Creating jobs...")
        jobs_data = dict()
        # jobs_data includes the name of the .our and .err files of the job in LOG_expid
        if not new:
            try:
                jobs_data = {str(row[0]): row for row in self.load()}
            except:
                jobs_data = {str(row[0]): row for row in self.backup_load()}
        self._create_jobs(dic_jobs, jobs_parser, priority,
                          default_job_type, jobs_data)
        if show_log:
            Log.info("Adding dependencies...")
        self._add_dependencies(date_list, member_list,chunk_list, dic_jobs, jobs_parser, self.graph)

        if show_log:
            Log.info("Removing redundant dependencies...")
        self.update_genealogy(
            new, notransitive, update_structure=update_structure)
        for job in self._job_list:
            job.parameters = parameters
        # Checking for member constraints
        if len(run_only_members) > 0:
            # Found
            if show_log:
                Log.info("Considering only members {0}".format(
                    str(run_only_members)))
            old_job_list = [job for job in self._job_list]
            self._job_list = [
                job for job in old_job_list if job.member is None or job.member in run_only_members or job.status not in [Status.WAITING, Status.READY]]
            for job in self._job_list:
                for jobp in job.parents:
                    if jobp in self._job_list:
                        job.parents.add(jobp)
                for jobc in job.children:
                    if jobc in self._job_list:
                        job.children.add(jobc)

        # Perhaps this should be done by default independent of the wrapper_type supplied
        try:
            for wrapper_section in wrapper_jobs:
                if wrapper_jobs[wrapper_section] != 'None':
                    self._ordered_jobs_by_date_member[wrapper_section] = self._create_sorted_dict_jobs(wrapper_jobs[wrapper_section])
                else:
                    self._ordered_jobs_by_date_member[wrapper_section] = {}
        except BaseException as e:
            raise AutosubmitCritical("Some section jobs of the wrapper:{0} are not in the current job_list defined in jobs.conf".format(wrapper_section),7014,e.message)
        pass


    @staticmethod
    def _add_dependencies(date_list, member_list, chunk_list, dic_jobs, jobs_parser, graph, option="DEPENDENCIES"):
        for job_section in jobs_parser.sections():
            Log.debug("Adding dependencies for {0} jobs".format(job_section))
            # If does not have dependencies, do nothing
            if not jobs_parser.has_option(job_section, option):
                continue

            dependencies_keys = jobs_parser.get(job_section, option).split()
            dependencies = JobList._manage_dependencies(dependencies_keys, dic_jobs, job_section)

            for job in dic_jobs.get_jobs(job_section):
                num_jobs = 1
                if isinstance(job, list):
                    num_jobs = len(job)
                for i in xrange(num_jobs):
                    _job = job[i] if num_jobs > 1 else job
                    JobList._manage_job_dependencies(dic_jobs, _job, date_list, member_list, chunk_list, dependencies_keys,
                                                     dependencies, graph)


    @staticmethod
    def _manage_dependencies(dependencies_keys, dic_jobs, job_section):
        dependencies = dict()
        for key in dependencies_keys:
            distance = None
            splits = None
            sign = None

            if '-' not in key and '+' not in key and '*' not in key and '?' not in key:
                section = key
            else:
                if '?' in key:
                    sign = '?'
                    section = key[:-1]
                else:
                    if '-' in key:
                        sign = '-'
                    elif '+' in key:
                        sign = '+'
                    elif '*' in key:
                        sign = '*'
                    key_split = key.split(sign)
                    section = key_split[0]
                    distance = int(key_split[1])

            if '[' in section:
                section_name = section[0:section.find("[")]
                splits_section = int(
                    dic_jobs.get_option(section_name, 'SPLITS', -1))
                splits = JobList._calculate_splits_dependencies(
                    section, splits_section)
                section = section_name

            dependency_running_type = dic_jobs.get_option(
                section, 'RUNNING', 'once').lower()
            delay = int(dic_jobs.get_option(section, 'DELAY', -1))
            select_chunks_opt = dic_jobs.get_option(job_section, 'SELECT_CHUNKS', None)
            selected_chunks = []
            if select_chunks_opt is not None:
                if '*' in select_chunks_opt:
                    sections_chunks = select_chunks_opt.split(' ')
                    for section_chunk in sections_chunks:
                        info = section_chunk.split('*')
                        if info[0] in key:
                            auxiliar_relation_list = []
                            for relation in xrange(1, len(info)):
                                auxiliar_relation_list.append(dic_jobs.parse_relation(section,False,info[relation],"Select_chunks"))
                            selected_chunks.append(auxiliar_relation_list)
                else:
                    raise AutosubmitCritical("Wrong syntax for select_chunks. The correct Syntax is:Dependency_KEY*[#chunk_number,#chunk_number...] Dependency_Key...",7011)
            select_member_opt = dic_jobs.get_option(job_section, 'SELECT_MEMBERS', None)
            selected_member = []
            if select_member_opt is not None:
                if '*' in select_member_opt:
                    sections_members = select_member_opt.split(' ')
                    for section_member in sections_members:
                        info = section_member.split('*')
                        if info[0] in key:
                            auxiliar_relation_list = []
                            for relation in xrange(1, len(info)):
                                auxiliar_relation_list.append(dic_jobs.parse_relation(section, True, info[relation], "Select_Members"))
                            selected_member.append(auxiliar_relation_list)
                else:
                    raise AutosubmitCritical(
                        "Wrong syntax for select_members. The correct Syntax is:Dependency_KEY*[#member_index,#member_index...]*... Dependency_Key...",
                        7011)
            if len(selected_chunks) >= 1 and len(selected_member) >= 1:
               dependency = Dependency(section, distance, dependency_running_type, sign, delay, splits, selected_chunks, selected_member)
            elif len(selected_chunks) >= 1:
                dependency = Dependency(section, distance, dependency_running_type, sign, delay, splits,selected_chunks, [])
            elif len(selected_member) >= 1:
                dependency = Dependency(section, distance, dependency_running_type, sign, delay, splits,[], selected_member)
            else:
                dependency = Dependency(section, distance, dependency_running_type, sign, delay, splits, [], [])
            dependencies[key] = dependency
        return dependencies

    @staticmethod
    def _calculate_splits_dependencies(section, max_splits):
        splits_list = section[section.find("[") + 1:section.find("]")]
        splits = []
        for str_split in splits_list.split(","):
            if str_split.find(":") != -1:
                numbers = str_split.split(":")
                # change this to be checked in job_common.py
                max_splits = min(int(numbers[1]), max_splits)
                for count in xrange(int(numbers[0]), max_splits + 1):
                    splits.append(int(str(count).zfill(len(numbers[0]))))
            else:
                if int(str_split) <= max_splits:
                    splits.append(int(str_split))
        return splits

    @staticmethod
    def _manage_job_dependencies(dic_jobs, job, date_list, member_list, chunk_list, dependencies_keys, dependencies,
                                 graph):
        visited_parents = set()
        other_parents   = set()
        for key in dependencies_keys:
            dependency = dependencies[key]
            skip, (chunk, member, date) = JobList._calculate_dependency_metadata(job.chunk, chunk_list,
                                                                                 job.member, member_list,
                                                                                 job.date, date_list,
                                                                                 dependency)
            if skip:
                continue
            chunk_relations_to_add = list()
            member_relations_to_add = list()
            # Get current job dependency relations. Used for select chunk option. This is the job in where select chunks option is defined
            if len(dependency.select_chunks_orig) > 0:  # find chunk relation
                other_parents = dic_jobs.get_jobs(dependency.section, date, member, None)
                chunk_relation_indx = 0
                while chunk_relation_indx < len(dependency.select_chunks_orig):
                    if job.running in ["once"] or len(dependency.select_chunks_orig[chunk_relation_indx]) == 0 or job.chunk in dependency.select_chunks_orig[chunk_relation_indx]:
                        chunk_relations_to_add.append(chunk_relation_indx)
                    chunk_relation_indx += 1
                chunk_relation_indx -= 1
            # Get current job dependency relations. Used for select members option. This is the job in where select members option is defined
            if len(dependency.select_members_orig) > 0:  # find member relation
                member_relation_indx = 0
                other_parents = dic_jobs.get_jobs(dependency.section, date, None, chunk)
                while member_relation_indx < len(dependency.select_members_orig):
                    if job.running in ["once"] or len(dependency.select_members_orig[member_relation_indx]) == 0 or member_list.index(job.member) in dependency.select_members_orig[member_relation_indx] :
                        member_relations_to_add.append(member_relation_indx)
                    member_relation_indx += 1
                member_relation_indx -= 1
            #Now calculate the dependencies of jobs. If parent is not chunk or member it will be added to the dependency set,
            parents_jobs = dic_jobs.get_jobs(dependency.section, date, member, chunk)
            for parent in parents_jobs:
                # Generic for all dependencies
                if dependency.delay == -1 or chunk > dependency.delay:
                    if isinstance(parent, list):
                        if job.split is not None:
                            parent = filter(
                                lambda _parent: _parent.split == job.split, parent)[0]
                        else:
                            if dependency.splits is not None:
                                parent = filter(
                                    lambda _parent: _parent.split in dependency.splits, parent)
                #Select chunk + select member
                if parent.running in ["once"] or ( len(dependency.select_members_orig) <= 0 and len(dependency.select_chunks_orig) <= 0):
                    job.add_parent(parent)
                    JobList._add_edge(graph, job, parent)
                elif len(dependency.select_members_orig) > 0:
                    for relation_indx in member_relations_to_add:
                        if member_list.index(parent.member) in dependency.select_members_dest[relation_indx] or len(dependency.select_members_dest[relation_indx]) <= 0:
                            if parent not in visited_parents:
                                job.add_parent(parent)
                                JobList._add_edge(graph, job, parent)
                                other_parents.remove(parent)
                        visited_parents.add(parent)
                elif len(dependency.select_chunks_orig) > 0:
                    for relation_indx in chunk_relations_to_add:
                        if parent.chunk in dependency.select_chunks_dest[relation_indx] or len(
                                dependency.select_chunks_dest[relation_indx]) == 0:
                            if parent not in visited_parents:
                                job.add_parent(parent)
                                JobList._add_edge(graph, job, parent)
                                other_parents.remove(parent)
                        visited_parents.add(parent)

            JobList.handle_frequency_interval_dependencies(chunk, chunk_list, date, date_list, dic_jobs, job, member,
                                                           member_list, dependency.section, graph, other_parents)

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
                                               section_name, graph,visited_parents):
        if job.wait and job.frequency > 1:
            if job.chunk is not None:
                max_distance = (chunk_list.index(chunk) + 1) % job.frequency
                if max_distance == 0:
                    max_distance = job.frequency
                for distance in xrange(1, max_distance):
                    for parent in dic_jobs.get_jobs(section_name, date, member, chunk - distance):
                        if parent not in visited_parents:
                            job.add_parent(parent)
                            JobList._add_edge(graph, job, parent)
            elif job.member is not None:
                member_index = member_list.index(job.member)
                max_distance = (member_index + 1) % job.frequency
                if max_distance == 0:
                    max_distance = job.frequency
                for distance in xrange(1, max_distance, 1):
                    for parent in dic_jobs.get_jobs(section_name, date,
                                                    member_list[member_index - distance], chunk):
                        if parent not in visited_parents:
                            job.add_parent(parent)
                            JobList._add_edge(graph, job, parent)
            elif job.date is not None:
                date_index = date_list.index(job.date)
                max_distance = (date_index + 1) % job.frequency
                if max_distance == 0:
                    max_distance = job.frequency
                for distance in xrange(1, max_distance, 1):
                    for parent in dic_jobs.get_jobs(section_name, date_list[date_index - distance],
                                                    member, chunk):
                        if parent not in visited_parents:
                            job.add_parent(parent)
                            JobList._add_edge(graph, job, parent)

    @staticmethod
    def _add_edge(graph, job, parents):
        num_parents = 1
        if isinstance(parents, list):
            num_parents = len(parents)
        for i in xrange(num_parents):
            parent = parents[i] if isinstance(parents, list) else parents
            graph.add_edge(parent.name, job.name)
            pass

    @staticmethod
    def _create_jobs(dic_jobs, parser, priority, default_job_type, jobs_data=dict()):
        for section in parser.sections():
            Log.debug("Creating {0} jobs".format(section))
            dic_jobs.read_section(section, priority, default_job_type, jobs_data)
            priority += 1

    def _create_sorted_dict_jobs(self, wrapper_jobs):
        """
        Creates a sorting of the jobs whose job.section is in wrapper_jobs, according to the following filters in order of importance:
        date, member, RUNNING, and chunk number; where RUNNING is defined in jobs_.conf for each section.

        If the job does not have a chunk number, the total number of chunks configured for the experiment is used.

        :param wrapper_jobs: User defined job types in autosubmit_,conf [wrapper] section to be wrapped. \n
        :type wrapper_jobs: String \n
        :return: Sorted Dictionary of Dictionary of List that represents the jobs included in the wrapping process. \n
        :rtype: Dictionary Key: date, Value: (Dictionary Key: Member, Value: List of jobs that belong to the date, member, and are ordered by chunk number if it is a chunk job otherwise num_chunks from JOB TYPE (section)
        """
        # Dictionary Key: date, Value: (Dictionary Key: Member, Value: List)
        dict_jobs = dict()
        for date in self._date_list:
            dict_jobs[date] = dict()
            for member in self._member_list:
                dict_jobs[date][member] = list()
        num_chunks = len(self._chunk_list)


        sections_running_type_map = dict()
        if "&" in wrapper_jobs:
            char = "&"
        else:
            char = " "
        wrapper_jobs_reverse = wrapper_jobs.split(char)
        for section in wrapper_jobs_reverse:
            # RUNNING = once, as default. This value comes from jobs_.conf
            sections_running_type_map[section] = self._dic_jobs.get_option(section, "RUNNING", 'once')

        # Select only relevant jobs, those belonging to the sections defined in the wrapper

        sections_to_filter = ""
        for section in sections_running_type_map:
            sections_to_filter += section

        filtered_jobs_list = filter(lambda job: job.section in sections_running_type_map, self._job_list)

        filtered_jobs_fake_date_member, fake_original_job_map = self._create_fake_dates_members(
            filtered_jobs_list)

        for date in self._date_list:
            str_date = self._get_date(date)
            for member in self._member_list:
                # Filter list of fake jobs according to date and member, result not sorted at this point
                sorted_jobs_list = filter(lambda job: job.name.split("_")[1] == str_date and
                                          job.name.split("_")[2] == member, filtered_jobs_fake_date_member)

                previous_job = sorted_jobs_list[0]

                # get RUNNING for this section
                section_running_type = sections_running_type_map[previous_job.section]

                jobs_to_sort = [previous_job]
                previous_section_running_type = None
                # Index starts at 1 because 0 has been taken in a previous step
                for index in xrange(1, len(sorted_jobs_list) + 1):
                    # If not last item
                    if index < len(sorted_jobs_list):
                        job = sorted_jobs_list[index]
                        # Test if section has changed. e.g. from INI to SIM
                        if previous_job.section != job.section:
                            previous_section_running_type = section_running_type
                            section_running_type = sections_running_type_map[job.section]
                    # Test if RUNNING is different between sections, or if we have reached the last item in sorted_jobs_list
                    if (previous_section_running_type != None and previous_section_running_type != section_running_type) \
                            or index == len(sorted_jobs_list):

                        # Sorting by date, member, chunk number if it is a chunk job otherwise num_chunks from JOB TYPE (section)
                        # Important to note that the only differentiating factor would be chunk OR num_chunks
                        jobs_to_sort = sorted(jobs_to_sort, key=lambda k: (k.name.split('_')[1], (k.name.split('_')[2]),
                                                                           (int(k.name.split('_')[3])
                                                                            if len(k.name.split('_')) == 5 else num_chunks + 1)))

                        # Bringing back original job if identified
                        for idx in xrange(0, len(jobs_to_sort)):
                            # Test if it is a fake job
                            if jobs_to_sort[idx] in fake_original_job_map:
                                fake_job = jobs_to_sort[idx]
                                # Get original
                                jobs_to_sort[idx] = fake_original_job_map[fake_job]
                        # Add to result, and reset jobs_to_sort
                        # By adding to the result at this step, only those with the same RUNNIN have been added.
                        dict_jobs[date][member] += jobs_to_sort
                        jobs_to_sort = []
                    if len(sorted_jobs_list) > 1 :
                        jobs_to_sort.append(job)
                        previous_job = job

        return dict_jobs

    def _create_fake_dates_members(self, filtered_jobs_list):
        """
        Using the list of jobs provided, creates clones of these jobs and modifies names conditionted on job.date, job.member values (testing None).
        The purpose is that all jobs share the same name structure.

        :param filtered_jobs_list: A list of jobs of only those that comply with certain criteria, e.g. those belonging to a user defined job type for wrapping. \n
        :type filetered_jobs_list: List() of Job Objects \n
        :return filtered_jobs_fake_date_member: List of fake jobs. \n
        :rtype filtered_jobs_fake_date_member: List of Job Objects \n
        :return fake_original_job_map: Dictionary that maps fake job to original one. \n
        :rtype fake_original_job_map: Dictionary Key: Job Object, Value: Job Object
        """
        filtered_jobs_fake_date_member = []
        fake_original_job_map = dict()

        import copy
        for job in filtered_jobs_list:
            fake_job = None
            # running once and synchronize date
            if job.date is None and job.member is None:
                # Declare None values as if they were the last items in corresponding list
                date = self._date_list[-1]
                member = self._member_list[-1]
                fake_job = copy.deepcopy(job)
                # Use previous values to modify name of fake job
                fake_job.name = fake_job.name.split('_', 1)[0] + "_" + self._get_date(date) + "_" \
                    + member + "_" + fake_job.name.split("_", 1)[1]
                # Filling list of fake jobs, only difference is the name
                filtered_jobs_fake_date_member.append(fake_job)
                # Mapping fake jobs to orignal ones
                fake_original_job_map[fake_job] = job
            # running date or synchronize member
            elif job.member is None:
                # Declare None value as if it were the last items in corresponding list
                member = self._member_list[-1]
                fake_job = copy.deepcopy(job)
                # Use it to modify name of fake job
                fake_job.name = fake_job.name.split('_', 2)[0] + "_" + fake_job.name.split('_', 2)[
                    1] + "_" + member + "_" + fake_job.name.split("_", 2)[2]
                # Filling list of fake jobs, only difference is the name
                filtered_jobs_fake_date_member.append(fake_job)
                # Mapping fake jobs to orignal ones
                fake_original_job_map[fake_job] = job
            # There was no result
            if fake_job is None:
                filtered_jobs_fake_date_member.append(job)

        return filtered_jobs_fake_date_member, fake_original_job_map

    def _get_date(self, date):
        """
        Parses a user defined Date (from [experiment] DATELIST) to return a special String representation of that Date

        :param date: String representation of a date in format YYYYYMMdd. \n
        :type date: String \n
        :return: String representation of date according to format. \n
        :rtype: String \n
        """
        date_format = ''
        if date.hour > 1:
            date_format = 'H'
        if date.minute > 1:
            date_format = 'M'
        str_date = date2str(date, date_format)
        return str_date

    def __len__(self):
        return self._job_list.__len__()

    def get_date_list(self):
        """
        Get inner date list

        :return: date list
        :rtype: list
        """
        return self._date_list

    def get_member_list(self):
        """
        Get inner member list

        :return: member list
        :rtype: list
        """
        return self._member_list

    def get_chunk_list(self):
        """
        Get inner chunk list

        :return: chunk list
        :rtype: list
        """
        return self._chunk_list

    def get_job_list(self):
        """
        Get inner job list

        :return: job list
        :rtype: list
        """
        return self._job_list

    def get_date_format(self):
        date_format = ''
        for date in self.get_date_list():
            if date.hour > 1:
                date_format = 'H'
            if date.minute > 1:
                date_format = 'M'
        return date_format

    def copy_ordered_jobs_by_date_member(self):
        pass
    def get_ordered_jobs_by_date_member(self,section):
        """
        Get the dictionary of jobs ordered according to wrapper's expression divided by date and member

        :return: jobs ordered divided by date and member
        :rtype: dict
        """
        if len(self._ordered_jobs_by_date_member) > 0:
            return self._ordered_jobs_by_date_member[section]

    def get_completed(self, platform=None, wrapper=False):
        """
        Returns a list of completed jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: completed jobs
        :rtype: list
        """

        completed_jobs = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                          job.status == Status.COMPLETED]
        if wrapper:
            return [job for job in completed_jobs if job.packed is False]

        else:
            return completed_jobs

    def get_uncompleted(self, platform=None, wrapper=False):
        """
        Returns a list of completed jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: completed jobs
        :rtype: list
        """
        uncompleted_jobs = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                            job.status != Status.COMPLETED]

        if wrapper:
            return [job for job in uncompleted_jobs if job.packed is False]
        else:
            return uncompleted_jobs

    def get_uncompleted_and_not_waiting(self, platform=None, wrapper=False):
        """
        Returns a list of completed jobs and waiting

        :param platform: job platform
        :type platform: HPCPlatform
        :return: completed jobs
        :rtype: list
        """
        uncompleted_jobs = [job for job in self._job_list if
                            (platform is None or job.platform.name.lower() == platform.name.lower()) and
                            job.status != Status.COMPLETED and job.status != Status.WAITING]

        if wrapper:
            return [job for job in uncompleted_jobs if job.packed is False]
        else:
            return uncompleted_jobs

    def get_submitted(self, platform=None, hold=False, wrapper=False):
        """
        Returns a list of submitted jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: submitted jobs
        :rtype: list
        """
        submitted = list()
        if hold:
            submitted = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                         job.status == Status.SUBMITTED and job.hold == hold]
        else:
            submitted = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                         job.status == Status.SUBMITTED]
        if wrapper:
            return [job for job in submitted if job.packed is False]
        else:
            return submitted

    def get_running(self, platform=None, wrapper=False):
        """
        Returns a list of jobs running

        :param platform: job platform
        :type platform: HPCPlatform
        :return: running jobs
        :rtype: list
        """
        running = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                   job.status == Status.RUNNING]
        if wrapper:
            return [job for job in running if job.packed is False]
        else:
            return running

    def get_queuing(self, platform=None, wrapper=False):
        """
        Returns a list of jobs queuing

        :param platform: job platform
        :type platform: HPCPlatform
        :return: queuedjobs
        :rtype: list
        """
        queuing = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                   job.status == Status.QUEUING]
        if wrapper:
            return [job for job in queuing if job.packed is False]
        else:
            return queuing

    def get_failed(self, platform=None, wrapper=False):
        """
        Returns a list of failed jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: failed jobs
        :rtype: list
        """
        failed = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                  job.status == Status.FAILED]
        if wrapper:
            return [job for job in failed if job.packed is False]
        else:
            return failed

    def get_unsubmitted(self, platform=None, wrapper=False):
        """
        Returns a list of unsummited jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: all jobs
        :rtype: list
        """
        unsubmitted = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                       (job.status != Status.SUBMITTED and job.status != Status.QUEUING and job.status == Status.RUNNING and job.status == Status.COMPLETED)]

        if wrapper:
            return [job for job in unsubmitted if job.packed is False]
        else:
            return unsubmitted

    def get_all(self, platform=None, wrapper=False):
        """
        Returns a list of all jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: all jobs
        :rtype: list
        """
        all = [job for job in self._job_list]

        if wrapper:
            return [job for job in all if job.packed is False]
        else:
            return all

    def get_job_names(self,lower_case=False):
        """
        Returns a list of all job names

        :param platform: job platform
        :type platform: HPCPlatform
        :return: all jobs
        :rtype: list
        """
        if lower_case:
            all_jobs = [job.name.lower() for job in self._job_list]
        else:
            all_jobs = [job.name for job in self._job_list]

        return all_jobs

    def update_two_step_jobs(self):
        prev_jobs_to_run_first = self.jobs_to_run_first
        if len(self.jobs_to_run_first) > 0:
            self.jobs_to_run_first  = [ job for job in self.jobs_to_run_first if job.status != Status.COMPLETED ]
            keep_running = False
            for job in self.jobs_to_run_first:
                running_parents = [parent for parent in job.parents if parent.status != Status.WAITING and parent.status != Status.FAILED ] #job is parent of itself
                if len(running_parents) == len(job.parents):
                    keep_running = True
            if len(self.jobs_to_run_first) > 0 and keep_running is False:
                raise AutosubmitCritical("No more jobs to run first, there were still pending jobs but they're unable to run without their parents or there are failed jobs.",7014)

    def parse_jobs_by_filter(self, unparsed_jobs,two_step_start = True):
        jobs_to_run_first = list()
        select_jobs_by_name = "" #job_name
        select_all_jobs_by_section = "" #  all
        filter_jobs_by_section = ""  # Select, chunk / member
        if "&" in unparsed_jobs: # If there are explicit jobs add them
            jobs_to_check = unparsed_jobs.split("&")
            select_jobs_by_name = jobs_to_check[0]
            unparsed_jobs = jobs_to_check[1]
        if not ";" in unparsed_jobs:
            if '[':
                select_all_jobs_by_section = unparsed_jobs
                filter_jobs_by_section = ""
            else:
                select_all_jobs_by_section = ""
                filter_jobs_by_section = unparsed_jbos
        else:
            aux = unparsed_jobs.split(';')
            select_all_jobs_by_section = aux[0]
            filter_jobs_by_section = aux[1]
        if two_step_start:
            try:
                self.jobs_to_run_first = self.get_job_related(select_jobs_by_name=select_jobs_by_name,select_all_jobs_by_section=select_all_jobs_by_section,filter_jobs_by_section=filter_jobs_by_section)
            except:
                raise AutosubmitCritical("Check the {0} format.\nFirst filter is optional ends with '&'.\nSecond filter ends with ';'.\nThird filter must contain '['. ".format(unparsed_jobs))
        else:
            try:
                self.rerun_job_list = self.get_job_related(select_jobs_by_name=select_jobs_by_name,
                                                              select_all_jobs_by_section=select_all_jobs_by_section,
                                                              filter_jobs_by_section=filter_jobs_by_section,two_step_start=two_step_start)
            except:
                raise AutosubmitCritical(
                    "Check the {0} format.\nFirst filter is optional ends with '&'.\nSecond filter ends with ';'.\nThird filter must contain '['. ".format(
                        unparsed_jobs))

    def get_job_related(self, select_jobs_by_name="",select_all_jobs_by_section="",filter_jobs_by_section="",two_step_start=True):
        """
        :param select_jobs_by_name: job name
        :param select_all_jobs_by_section: section name
        :param filter_jobs_by_section: section, date , member? , chunk?
        :return: jobs_list names
        :rtype: list
        """
        ultimate_jobs_list = []
        # First Filter {select job by name}
        if select_jobs_by_name != "":
            jobs_by_name = [ job for job in self._job_list if re.search("(^|[^0-9a-z_])"+job.name.lower()+"([^a-z0-9_]|$)",select_jobs_by_name.lower()) is not None ]
            jobs_by_name_no_expid = [job for job in self._job_list if
                            re.search("(^|[^0-9a-z_])" + job.name.lower()[5:] + "([^a-z0-9_]|$)",
                                      select_jobs_by_name.lower()) is not None]
            ultimate_jobs_list.extend(jobs_by_name)
            ultimate_jobs_list.extend(jobs_by_name_no_expid)

        # Second Filter { select all }
        if select_all_jobs_by_section != "":
            all_jobs_by_section = [ job for job in self._job_list if re.search("(^|[^0-9a-z_])"+job.section.lower()+"([^a-z0-9_]|$)",select_all_jobs_by_section.lower()) is not None ]
            ultimate_jobs_list.extend(all_jobs_by_section)
        # Third Filter N section { date , member? , chunk?}
        # Section[date[member][chunk]]
        # filter_jobs_by_section="SIM[20[C:000][M:1]],DA[20 21[M:000 001][C:1]]"
        if filter_jobs_by_section != "":
            section_name=""
            section_dates=""
            section_chunks=""
            section_members=""
            jobs_final = list()
            for complete_filter_by_section in filter_jobs_by_section.split(','):
                section_list = complete_filter_by_section.split('[')
                section_name = section_list[0].strip('[]')
                section_dates = section_list[1].strip('[]')
                if 'c' in section_list[2].lower():
                    section_chunks = section_list[2].strip('cC:[]')
                elif 'm' in section_list[2].lower():
                    section_members = section_list[2].strip('Mm:[]')
                if len(section_list) > 3:
                    if 'c' in section_list[3].lower():
                        section_chunks = section_list[3].strip('Cc:[]')
                    elif 'm' in section_list[3].lower():
                        section_members = section_list[3].strip('mM:[]')


                if section_name != "":
                    jobs_filtered = [job for job in self._job_list if
                                           re.search("(^|[^0-9a-z_])" + job.section.lower() + "([^a-z0-9_]|$)",
                                                     section_name.lower()) is not None]
                if section_dates != "":
                    jobs_date = [ job for job in jobs_filtered if re.search("(^|[^0-9a-z_])" + date2str(job.date, job.date_format) + "([^a-z0-9_]|$)", section_dates.lower()) is not None or job.date is None  ]

                if section_chunks != "" or section_members != "":
                    jobs_final = [job for job in jobs_date if ( section_chunks == "" or re.search("(^|[^0-9a-z_])" + str(job.chunk) + "([^a-z0-9_]|$)",section_chunks)  is not None ) and ( section_members == "" or re.search("(^|[^0-9a-z_])" + str(job.member) + "([^a-z0-9_]|$)",section_members.lower()) is not None  )  ]
                ultimate_jobs_list.extend(jobs_final)
        # Duplicates out
        ultimate_jobs_list = list(set(ultimate_jobs_list))
        Log.debug("List of jobs filtered by TWO_STEP_START parameter:\n{0}".format([job.name for job in ultimate_jobs_list]))
        return ultimate_jobs_list

    def get_logs(self):
        """
        Returns a dict of logs by jobs_name jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: logs
        :rtype: dict(tuple)
        """
        logs = dict()
        for job in self._job_list:
            logs[job.name] = (job.local_logs, job.remote_logs)
        return logs

    def add_logs(self, logs):
        """
        add logs to the current job_list

        :param platform: job platform
        :type platform: HPCPlatform
        :return: logs
        :rtype: dict(tuple)
        """

        for job in self._job_list:
            if job.name in logs:
                job.local_logs = logs[job.name][0]
                job.remote_logs = logs[job.name][1]

    def get_ready(self, platform=None, hold=False, wrapper=False):
        """
        Returns a list of ready jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: ready jobs
        :rtype: list
        """
        ready = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                 job.status == Status.READY and job.hold is hold]

        if wrapper:
            return [job for job in ready if job.packed is False]
        else:
            return ready

    def get_prepared(self, platform=None):
        """
        Returns a list of prepared jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: prepared jobs
        :rtype: list
        """
        prepared = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                    job.status == Status.PREPARED]
        return prepared
    def get_delayed(self, platform=None):
        """
        Returns a list of delayed jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: delayed jobs
        :rtype: list
        """
        delayed = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                    job.status == Status.DELAYED]
        return delayed
    def get_skipped(self, platform=None):
        """
        Returns a list of skipped jobs

        :param platform: job platform
        :type platform: HPCPlatform
        :return: skipped jobs
        :rtype: list
        """
        skipped = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                   job.status == Status.SKIPPED]
        return skipped

    def get_waiting(self, platform=None, wrapper=False):
        """
        Returns a list of jobs waiting

        :param platform: job platform
        :type platform: HPCPlatform
        :return: waiting jobs
        :rtype: list
        """
        waiting_jobs = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                        job.status == Status.WAITING]
        if wrapper:
            return [job for job in waiting_jobs if job.packed is False]
        else:
            return waiting_jobs

    def get_waiting_remote_dependencies(self, platform_type='slurm'.lower()):
        """
        Returns a list of jobs waiting on slurm scheduler

        :param platform: job platform
        :type platform: HPCPlatform
        :return: waiting jobs
        :rtype: list
        """
        waiting_jobs = [job for job in self._job_list if (
            job.platform.type == platform_type and job.status == Status.WAITING)]
        return waiting_jobs

    def get_held_jobs(self, platform=None):
        """
        Returns a list of jobs in the platforms (Held)

        :param platform: job platform
        :type platform: HPCPlatform
        :return: jobs in platforms
        :rtype: list
        """
        return [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                job.status == Status.HELD]

    def get_unknown(self, platform=None, wrapper=False):
        """
        Returns a list of jobs on unknown state

        :param platform: job platform
        :type platform: HPCPlatform
        :return: unknown state jobs
        :rtype: list
        """
        submitted = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                     job.status == Status.UNKNOWN]
        if wrapper:
            return [job for job in submitted if job.packed is False]
        else:
            return submitted

    def get_suspended(self, platform=None, wrapper=False):
        """
        Returns a list of jobs on unknown state

        :param platform: job platform
        :type platform: HPCPlatform
        :return: unknown state jobs
        :rtype: list
        """
        suspended = [job for job in self._job_list if (platform is None or job.platform.name.lower() == platform.name.lower()) and
                     job.status == Status.SUSPENDED]
        if wrapper:
            return [job for job in suspended if job.packed is False]
        else:
            return suspended

    def get_in_queue(self, platform=None, wrapper=False):
        """
        Returns a list of jobs in the platforms (Submitted, Running, Queuing, Unknown,Held)

        :param platform: job platform
        :type platform: HPCPlatform
        :return: jobs in platforms
        :rtype: list
        """

        in_queue = self.get_submitted(platform) + self.get_running(platform) + self.get_queuing(
            platform) + self.get_unknown(platform) + self.get_held_jobs(platform)
        if wrapper:
            return [job for job in in_queue if job.packed is False]
        else:
            return in_queue

    def get_not_in_queue(self, platform=None, wrapper=False):
        """
        Returns a list of jobs NOT in the platforms (Ready, Waiting)

        :param platform: job platform
        :type platform: HPCPlatform
        :return: jobs not in platforms
        :rtype: list
        """
        not_queued = self.get_ready(platform) + self.get_waiting(platform)
        if wrapper:
            return [job for job in not_queued if job.packed is False]
        else:
            return not_queued

    def get_finished(self, platform=None, wrapper=False):
        """
        Returns a list of jobs finished (Completed, Failed)


        :param platform: job platform
        :type platform: HPCPlatform
        :return: finished jobs
        :rtype: list
        """
        finished = self.get_completed(platform) + self.get_failed(platform)
        if wrapper:
            return [job for job in finished if job.packed is False]
        else:
            return finished

    def get_active(self, platform=None, wrapper=False):
        """
        Returns a list of active jobs (In platforms queue + Ready)

        :param platform: job platform
        :type platform: HPCPlatform
        :return: active jobs
        :rtype: list
        """
        active = self.get_in_queue(platform) + self.get_ready(
            platform=platform, hold=True) + self.get_ready(platform=platform, hold=False) + self.get_delayed(platform=platform)
        tmp = [job for job in active if job.hold and not (job.status ==
               Status.SUBMITTED or job.status == Status.READY or job.status == Status.DELAYED) ]
        if len(tmp) == len(active):  # IF only held jobs left without dependencies satisfied
            if len(tmp) != 0 and len(active) != 0:
                raise AutosubmitCritical(
                    "Only Held Jobs active. Exiting Autosubmit (TIP: This can happen if suspended or/and Failed jobs are found on the workflow)", 7066)
            active = []
        return active

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
    def get_jobs_by_section(self, section_list):
        """
        Returns the job that its name matches parameter section

        :parameter name: name to look for
        :type section: str
        :return: found job
        :rtype: job
        """
        jobs_by_section = list()
        for job in self._job_list:
            if job.section in section_list:
                jobs_by_section.append(job)
        return jobs_by_section

    def get_in_queue_grouped_id(self, platform):
        # type: (object) -> Dict[int, List[Job]]
        jobs = self.get_in_queue(platform)
        jobs_by_id = dict()
        for job in jobs:
            if job.id not in jobs_by_id:
                jobs_by_id[job.id] = list()
            jobs_by_id[job.id].append(job)
        return jobs_by_id

    def get_in_ready_grouped_id(self, platform):
        jobs = []
        [jobs.append(job) for job in jobs if (
            platform is None or job.platform.name is platform.name)]

        jobs_by_id = dict()
        for job in jobs:
            if job.id not in jobs_by_id:
                jobs_by_id[job.id] = list()
            jobs_by_id[job.id].append(job)
        return jobs_by_id

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
        try:
            if os.path.exists(filename):
                fd = open(filename, 'rw')
                return pickle.load(fd)
            else:
                return list()
        except IOError:
            Log.printlog(
                "Autosubmit will use a backup for recover the job_list", 6010)
            return list()

    def load(self):
        """
        Recreates an stored job list from the persistence

        :return: loaded job list object
        :rtype: JobList
        """
        Log.info("Loading JobList")
        return self._persistence.load(self._persistence_path, self._persistence_file)

    def backup_load(self):
        """
        Recreates an stored job list from the persistence

        :return: loaded job list object
        :rtype: JobList
        """
        Log.info("Loading backup JobList")
        return self._persistence.load(self._persistence_path, self._persistence_file + "_backup")

    def save(self):
        """
        Persists the job list
        """
        try:
            job_list = None
            if self.run_members is not None:
                job_names = [job.name for job in self._job_list]
                job_list = [job for job in self._job_list]
                for job in self._base_job_list:
                    if job.name not in job_names:
                        job_list.append(job)
            #Log.info("update_status_log start: {0}".format(log.fd_show.fd_table_status_str()))
            self.update_status_log()
            #Log.info("update_status_log end: {0}".format(log.fd_show.fd_table_status_str()))

            try:
                self._persistence.save(self._persistence_path,
                                       self._persistence_file, self._job_list if self.run_members is None or job_list is None else job_list)
                # Log.info("_persistence end: {0}".format(log.fd_show.fd_table_status_str()))
                pass
            except BaseException as e:
                raise AutosubmitError(e.message,6040,"Failure while saving the job_list")
        except AutosubmitError as e:
            raise
        except BaseException as e:
            raise AutosubmitError(e.message,6040,"Unknown failure while saving the job_list")


    def backup_save(self):
        """
        Persists the job list
        """
        self._persistence.save(self._persistence_path,
                               self._persistence_file + "_backup", self._job_list)

    def update_status_log(self):

        exp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.expid)
        tmp_path = os.path.join(exp_path, BasicConfig.LOCAL_TMP_DIR)
        aslogs_path = os.path.join(tmp_path, BasicConfig.LOCAL_ASLOG_DIR)
        Log.reset_status_file(os.path.join(aslogs_path,"jobs_active_status.log"),"status")
        Log.reset_status_file(os.path.join(aslogs_path,"jobs_failed_status.log"),"status_failed")
        job_list = self.get_completed()[-5:] + self.get_in_queue()
        failed_job_list = self.get_failed()
        if len(job_list) > 0:
            Log.status("\n{0:<35}{1:<15}{2:<15}{3:<20}{4:<15}", "Job Name",
                       "Job Id", "Job Status", "Job Platform", "Job Queue")
        if len(failed_job_list) > 0:
            Log.status_failed("\n{0:<35}{1:<15}{2:<15}{3:<20}{4:<15}", "Job Name",
                       "Job Id", "Job Status", "Job Platform", "Job Queue")
        for job in job_list:
            if len(job.queue) < 1:
                queue = "no-scheduler"
            else:
                queue = job.queue
            Log.status("{0:<35}{1:<15}{2:<15}{3:<20}{4:<15}", job.name, job.id, Status(
            ).VALUE_TO_KEY[job.status], job.platform.name, queue)
        for job in failed_job_list:
            if len(job.queue) < 1:
                queue = "no-scheduler"
            else:
                queue = job.queue
            Log.status_failed("{0:<35}{1:<15}{2:<15}{3:<20}{4:<15}", job.name, job.id, Status(
            ).VALUE_TO_KEY[job.status], job.platform.name, queue)

    def update_from_file(self, store_change=True):
        """
        Updates jobs list on the fly from and update file
        :param store_change: if True, renames the update file to avoid reloading it at the next iteration
        """
        if os.path.exists(os.path.join(self._persistence_path, self._update_file)):
            Log.info("Loading updated list: {0}".format(
                os.path.join(self._persistence_path, self._update_file)))
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

    def get_skippable_jobs(self, jobs_in_wrapper):
        job_list_skip = [job for job in self.get_job_list() if job.skippable is True and (job.status == Status.QUEUING or job.status ==
                                                                                          Status.RUNNING or job.status == Status.COMPLETED or job.status == Status.READY) and jobs_in_wrapper.find(job.section) == -1]
        skip_by_section = dict()
        for job in job_list_skip:
            if job.section not in skip_by_section:
                skip_by_section[job.section] = [job]
            else:
                skip_by_section[job.section].append(job)
        return skip_by_section

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

    def update_list(self, as_conf, store_change=True, fromSetStatus=False, submitter=None, first_time=False):
        # type: (AutosubmitConfig, bool, bool, object, bool) -> bool
        """
        Updates job list, resetting failed jobs and changing to READY all WAITING jobs with all parents COMPLETED

        :param as_conf: autosubmit config object
        :type as_conf: AutosubmitConfig
        :return: True if job status were modified, False otherwise
        :rtype: bool
        """
        # load updated file list
        save = False
        if self.update_from_file(store_change):
            save = store_change
        Log.debug('Updating FAILED jobs')
        write_log_status = False
        if not first_time:
            for job in self.get_failed():
                if not hasattr(job, 'retrials') or job.retrials is None:
                    retrials = as_conf.get_retrials()
                else:
                    retrials = job.retrials
                if job.fail_count < retrials:
                    job.inc_fail_count()
                    tmp = [
                        parent for parent in job.parents if parent.status == Status.COMPLETED]
                    if len(tmp) == len(job.parents):
                        if not hasattr(job, 'DELAY_RETRY_TIME') or job.retrials is None:
                            delay_retry_time = as_conf.get_delay_retry_time()
                        else:
                            delay_retry_time = job.retry_delay
                        if "+" in delay_retry_time:
                            retry_delay = job.fail_count * int(delay_retry_time[:-1]) + int(delay_retry_time[:-1])
                        elif "*" in delay_retry_time:
                            retry_delay = int(delay_retry_time[1:])
                            for retrial_amount in range(0,job.fail_count):
                                retry_delay += retry_delay * 10
                        else:
                            retry_delay = int(delay_retry_time)
                        if retry_delay > 0:
                            job.status = Status.DELAYED
                            job.delay_end = datetime.datetime.now() + datetime.timedelta(seconds=retry_delay)
                            Log.debug(
                                "Resetting job: {0} status to: DELAYED for retrial...".format(job.name))
                        else:
                            job.status = Status.READY
                            Log.debug(
                                "Resetting job: {0} status to: READY for retrial...".format(job.name))
                        job.id = None
                        job.packed = False
                        save = True

                    else:
                        job.status = Status.WAITING
                        save = True
                        job.packed = False
                        Log.debug(
                            "Resetting job: {0} status to: WAITING for parents completion...".format(job.name))
                else:
                    job.status = Status.FAILED
                    job.packed = False
                    save = True
        # if waiting jobs has all parents completed change its State to READY
        for job in self.get_completed():
            if job.synchronize is not None:
                tmp = [parent for parent in job.parents if parent.status == Status.COMPLETED]
                if len(tmp) != len(job.parents):
                    tmp2 = [parent for parent in job.parents if
                            parent.status == Status.COMPLETED or parent.status == Status.SKIPPED or parent.status == Status.FAILED]
                    if len(tmp2) == len(job.parents):
                        for parent in job.parents:
                            if parent.section + '?' not in job.dependencies and parent.status != Status.COMPLETED:
                                job.status = Status.WAITING
                                save = True
                                Log.debug(
                                    "Resetting sync job: {0} status to: WAITING for parents completion...".format(
                                        job.name))
                                break
                    else:
                        job.status = Status.WAITING
                        save = True
                        Log.debug(
                            "Resetting sync job: {0} status to: WAITING for parents completion...".format(
                                job.name))


        Log.debug('Updating WAITING jobs')
        if not fromSetStatus:
            all_parents_completed = []
            for job in self.get_delayed():
                if datetime.datetime.now() >= job.delay_end:
                    job.status = Status.READY
            for job in self.get_waiting():
                tmp = [parent for parent in job.parents if parent.status == Status.COMPLETED or parent.status == Status.SKIPPED]
                tmp2 = [parent for parent in job.parents if parent.status == Status.COMPLETED or parent.status == Status.SKIPPED or parent.status == Status.FAILED]
                tmp3 = [parent for parent in job.parents if parent.status == Status.SKIPPED or parent.status == Status.FAILED]
                if job.parents is None or len(tmp) == len(job.parents):
                    job.status = Status.READY
                    job.hold = False
                    Log.debug(
                        "Setting job: {0} status to: READY (all parents completed)...".format(job.name))
                    if as_conf.get_remote_dependencies():
                        all_parents_completed.append(job.name)
                if job.status != Status.READY:
                    if len(tmp3) != len(job.parents):
                        if len(tmp2) == len(job.parents):
                            for parent in job.parents:
                                if parent.section+'?' in job.dependencies:
                                    job.status = Status.READY
                                    job.hold = False
                                    Log.debug(
                                        "Setting job: {0} status to: READY (conditional jobs are completed/failed)...".format(job.name))
                                    break
                            if as_conf.get_remote_dependencies():
                                all_parents_completed.append(job.name)
                    else:
                        if len(tmp3) == 1 and len(job.parents) == 1:
                            for parent in job.parents:
                                if parent.section + '?' in job.dependencies:
                                    job.status = Status.READY
                                    job.hold = False
                                    Log.debug(
                                        "Setting job: {0} status to: READY (conditional jobs are completed/failed)...".format(
                                            job.name))
                                    break
            if as_conf.get_remote_dependencies():
                for job in self.get_prepared():
                    tmp = [
                        parent for parent in job.parents if parent.status == Status.COMPLETED]
                    tmp2 = [parent for parent in job.parents if
                            parent.status == Status.COMPLETED or parent.status == Status.SKIPPED or parent.status == Status.FAILED]
                    tmp3 = [parent for parent in job.parents if
                            parent.status == Status.SKIPPED or parent.status == Status.FAILED]
                    if len(tmp2) == len(job.parents) and len(tmp3) != len(job.parents):
                        job.status = Status.READY
                        job.packed = False
                        job.hold = False
                        save = True
                        Log.debug(
                            "A job in prepared status has all parent completed, job: {0} status set to: READY ...".format(job.name))
                Log.debug('Updating WAITING jobs eligible for be prepared')
                for job in self.get_waiting_remote_dependencies('slurm'):
                    if job.name not in all_parents_completed:
                        tmp = [parent for parent in job.parents if (
                            (parent.status == Status.SKIPPED or parent.status == Status.COMPLETED or parent.status == Status.QUEUING or parent.status == Status.RUNNING) and "setup" not in parent.name.lower())]
                        if len(tmp) == len(job.parents):
                            job.status = Status.PREPARED
                            job.hold = True
                            Log.debug(
                                "Setting job: {0} status to: Prepared for be held (all parents queuing, running or completed)...".format(job.name))

                Log.debug('Updating Held jobs')
                if self.job_package_map:
                    held_jobs = [job for job in self.get_held_jobs() if (
                        job.id not in self.job_package_map.keys())]
                    held_jobs += [wrapper_job for wrapper_job in self.job_package_map.values()
                                  if wrapper_job.status == Status.HELD]
                else:
                    held_jobs = self.get_held_jobs()

                for job in held_jobs:
                    if self.job_package_map and job.id in self.job_package_map.keys():  # Wrappers and inner jobs
                        hold_wrapper = False
                        for inner_job in job.job_list:
                            valid_parents = [
                                parent for parent in inner_job.parents if parent not in job.job_list]
                            tmp = [
                                parent for parent in valid_parents if parent.status == Status.COMPLETED]
                            if len(tmp) < len(valid_parents):
                                hold_wrapper = True
                        job.hold = hold_wrapper
                        if not job.hold:
                            for inner_job in job.job_list:
                                inner_job.hold = False                                                               
                            Log.debug(
                                "Setting job: {0} status to: Queuing (all parents completed)...".format(
                                    job.name))
                    else:  # Non-wrapped jobs
                        tmp = [
                            parent for parent in job.parents if parent.status == Status.COMPLETED]
                        if len(tmp) == len(job.parents):
                            job.hold = False                                                    
                            Log.debug(
                                "Setting job: {0} status to: Queuing (all parents completed)...".format(
                                    job.name))
                        else:
                            job.hold = True
            jobs_to_skip = self.get_skippable_jobs(
                as_conf.get_wrapper_jobs())  # Get A Dict with all jobs that are listed as skipabble

            for section in jobs_to_skip:
                for job in jobs_to_skip[section]:
                    # Check only jobs to be pending of canceled if not started
                    if job.status == Status.READY or job.status == Status.QUEUING:
                        jobdate = date2str(job.date, job.date_format)
                        if job.running == 'chunk':
                            for related_job in jobs_to_skip[section]:
                                if job.chunk < related_job.chunk and job.member == related_job.member and jobdate == date2str(
                                        related_job.date,
                                        related_job.date_format):  # Check if there is some related job with an higher chunk
                                    try:
                                        if job.status == Status.QUEUING:
                                            job.platform.send_command(job.platform.cancel_cmd + " " + str(job.id),
                                                                      ignore_log=True)
                                    except:
                                        pass  # jobid finished already
                                    job.status = Status.SKIPPED
                                    save = True
                        elif job.running == 'member':
                            members = as_conf.get_member_list()
                            for related_job in jobs_to_skip[section]:
                                if members.index(job.member) < members.index(
                                        related_job.member) and job.chunk == related_job.chunk and jobdate == date2str(
                                        related_job.date, related_job.date_format):
                                    try:
                                        if job.status == Status.QUEUING:
                                            job.platform.send_command(job.platform.cancel_cmd + " " + str(job.id),
                                                                      ignore_log=True)
                                    except:
                                        pass  # job_id finished already
                                    job.status = Status.SKIPPED
                                    save = True
            #save = True
        self.update_two_step_jobs()
        Log.debug('Update finished')
        return save

    def update_genealogy(self, new=True, notransitive=False, update_structure=False):
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
        if not notransitive:
            # Transitive reduction required
            current_structure = None
            db_path = os.path.join(
                self._config.STRUCTURES_DIR, "structure_" + self.expid + ".db")
            m_time_db = None
            jobs_conf_path = os.path.join(
                self._config.LOCAL_ROOT_DIR, self.expid, "conf", "jobs_{0}.conf".format(self.expid))
            m_time_job_conf = None
            if os.path.exists(db_path):
                try:
                    current_structure = DbStructure.get_structure(
                        self.expid, self._config.STRUCTURES_DIR)
                    m_time_db = os.stat(db_path).st_mtime
                    if os.path.exists(jobs_conf_path):
                        m_time_job_conf = os.stat(jobs_conf_path).st_mtime
                except Exception as exp:
                    pass
            structure_valid = False
            # If there is a current structure, and the number of jobs in JobList is equal to the number of jobs in the structure
            if ((current_structure) and (len(self._job_list) == len(current_structure)) and update_structure == False):
                structure_valid = True
                # Further validation
                # Structure exists and is valid, use it as a source of dependencies
                if m_time_job_conf:
                    if m_time_job_conf > m_time_db:
                        Log.info(
                            "File jobs_{0}.conf has been modified since the last time the structure persistence was saved.".format(self.expid))
                        structure_valid = False
                else:
                    Log.info(
                        "File jobs_{0}.conf was not found.".format(self.expid))

                if structure_valid == True:
                    for job in self._job_list:
                        if current_structure.get(job.name, None) is None:
                            structure_valid = False
                            break

                if structure_valid == True:
                    Log.info("Using existing valid structure.")
                    for job in self._job_list:
                        children_to_remove = [
                            child for child in job.children if child.name not in current_structure[job.name]]
                        for child in children_to_remove:
                            job.children.remove(child)
                            child.parents.remove(job)
            if structure_valid == False:
                # Structure does not exist or it is not be updated, attempt to create it.
                Log.info("Updating structure persistence...")
                self.graph = transitive_reduction(self.graph) # add threads for large experiments? todo
                if self.graph:
                    for job in self._job_list:
                        children_to_remove = [
                            child for child in job.children if child.name not in self.graph.neighbors(job.name)]
                        for child in children_to_remove:
                            job.children.remove(child)
                            child.parents.remove(job)
                    try:
                        DbStructure.save_structure(
                            self.graph, self.expid, self._config.STRUCTURES_DIR)
                    except Exception as exp:
                        Log.warning(str(exp))
                        pass

        for job in self._job_list:
            if not job.has_parents() and new:
                job.status = Status.READY

    @threaded
    def check_scripts_threaded(self, as_conf):
        """
        When we have created the scripts, all parameters should have been substituted.
        %PARAMETER% handlers not allowed (thread test)

        :param as_conf: experiment configuration
        :type as_conf: AutosubmitConfig
        """
        as_conf.reload()
        out = True
        for job in self._job_list:
            show_logs = job.check_warnings
            if not job.check_script(as_conf, self.parameters, show_logs):
                out = False
        return out

    def check_scripts(self, as_conf):
        """
        When we have created the scripts, all parameters should have been substituted.
        %PARAMETER% handlers not allowed

        :param as_conf: experiment configuration
        :type as_conf: AutosubmitConfig
        """
        Log.info("Checking scripts...")
        out = True
        # Implementing checking scripts feedback to the users in a minimum of 4 messages
        count = stage = 0
        for job in self._job_list:
            count += 1
            if (count >= len(self._job_list) / 4 * (stage + 1)) or count == len(self._job_list):
                stage += 1
                Log.info("{} of {} checked".format(count, len(self._job_list)))

            show_logs = job.check_warnings
            if job.check.lower() == 'on_submission':
                Log.info(
                    'Template {0} will be checked in running time'.format(job.section))
                continue
            elif job.check.lower() != 'true':
                Log.info(
                    'Template {0} will not be checked'.format(job.section))
                continue
            else:
                if job.section in self.sections_checked:
                    show_logs = False
            if not job.check_script(as_conf, self.parameters, show_logs):
                out = False
            self.sections_checked.add(job.section)
        if out:
            Log.result("Scripts OK")
        else:
            Log.printlog(
                "Scripts check failed\n Running after failed scripts is at your own risk!", 3000)
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

    def rerun(self, job_list_unparsed, monitor=False):
        """
        Updates job list to rerun the jobs specified by a job list

        :param chunk_list: list of chunks to rerun
        :type chunk_list: str
        """
        self.parse_jobs_by_filter(job_list_unparsed,two_step_start=False)
        member_list = set()
        chunk_list = set()
        date_list = set()
        job_sections = set()
        for job in self.get_all():
            if not monitor:
                job.status = Status.COMPLETED
            if job in self.rerun_job_list:
                job_sections.add(job.section)
                if not monitor:
                    job.status = Status.WAITING
                if job.member is not None:
                    member_list.add(job.member)
                if job.chunk is not None:
                    chunk_list.add(job.chunk)
                if job.date is not None:
                    date_list.add(job.date)
            else:
                self._remove_job(job)
        self._member_list = list(member_list)
        self._chunk_list = list(chunk_list)
        self._date_list = list(date_list)
        jobs_parser = self._get_jobs_parser()
        Log.info("Adding dependencies...")
        dependencies = dict()

        for job_section in job_sections:
            Log.debug(
                "Reading rerun dependencies for {0} jobs".format(job_section))
            if jobs_parser.has_option(job_section, 'DEPENDENCIES'):
                dependencies_keys = jobs_parser.get(job_section, "DEPENDENCIES").split()
                dependencies = JobList._manage_dependencies(dependencies_keys, self._dic_jobs, job_section)
                for job in self.get_jobs_by_section(job_section):
                    for key in dependencies_keys:
                        dependency = dependencies[key]
                        skip, (chunk, member, date) = JobList._calculate_dependency_metadata(job.chunk, self._chunk_list, job.member, self._member_list, job.date, self._date_list, dependency)
                        if skip:
                            continue
                        section_name = dependencies[key].section
                        for parent in self._dic_jobs.get_jobs(section_name, job.date, job.member,job.chunk):
                            if not monitor:
                                parent.status = Status.WAITING
                            Log.debug("Parent: " + parent.name)

    def _get_jobs_parser(self):
        jobs_parser = self._parser_factory.create_parser()
        jobs_parser.optionxform = str
        jobs_parser.read(
            os.path.join(self._config.LOCAL_ROOT_DIR, self._expid, 'conf', "jobs_" + self._expid + ".conf"))
        return jobs_parser

    def remove_rerun_only_jobs(self, notransitive=False):
        """
        Removes all jobs to be run only in reruns
        """
        flag = False
        for job in set(self._job_list):
            if job.rerun_only:
                self._remove_job(job)
                flag = True

        if flag:
            self.update_genealogy(notransitive=notransitive)
        del self._dic_jobs

    def print_with_status(self, statusChange=None, nocolor=False, existingList=None):
        """
        Returns the string representation of the dependency tree of
        the Job List

        :param statusChange: List of changes in the list, supplied in set status
        :type statusChange: List of strings
        :param nocolor: True if the result should not include color codes
        :type nocolor: Boolean
        :param existingList: External List of Jobs that will be printed, this excludes the inner list of jobs.
        :type existingList: List of Job Objects
        :return: String representation
        :rtype: String
        """
        # nocolor = True
        allJobs = self.get_all() if existingList is None else existingList
        # Header
        result = (bcolors.BOLD if nocolor == False else '') + \
            "## String representation of Job List [" + str(len(allJobs)) + "] "
        if statusChange is not None:
            result += "with " + (bcolors.OKGREEN if nocolor == False else '') + str(len(statusChange.keys())
                                                                                    ) + " Change(s) ##" + (bcolors.ENDC + bcolors.ENDC if nocolor == False else '')
        else:
            result += " ## "

        # Find root
        root = None
        for job in allJobs:
            if job.has_parents() == False:
                root = job
        visited = list()
        #print(root)
        # root exists
        if root is not None:
            result += self._recursion_print(root, 0, visited,
                                            statusChange=statusChange, nocolor=nocolor)
        else:
            result += "\nCannot find root."

        return result

    def __str__(self):
        """
        Returns the string representation of the class.
        Usage print(class)

        :return: String representation.
        :rtype: String
        """
        allJobs = self.get_all()
        result = "## String representation of Job List [" + str(
            len(allJobs)) + "] ##"

        # Find root
        root = None
        for job in allJobs:
            if job.has_parents() == False:
                root = job

        # root exists
        if root is not None:
            result += self._recursion_print(root, 0)
        else:
            result += "\nCannot find root."

        return result

    def _recursion_print(self, job, level, visited, statusChange=None, nocolor=False):
        """
        Returns the list of children in a recursive way
        Traverses the dependency tree

        :return: parent + list of children
        :rtype: String
        """
        result = ""
        if job.name not in visited:
            visited.append(job.name)
            prefix = ""
            for i in xrange(level):
                prefix += "|  "
            # Prefix + Job Name
            result = "\n" + prefix + \
                (bcolors.BOLD + bcolors.CODE_TO_COLOR[job.status] if nocolor == False else '') + \
                job.name + \
                (bcolors.ENDC + bcolors.ENDC if nocolor == False else '')
            if len(job._children) > 0:
                level += 1
                children = job._children
                total_children = len(job._children)
                # Writes children number and status if color are not being showed
                result += " ~ [" + str(total_children) + (" children] " if total_children > 1 else " child] ") + \
                    ("[" + Status.VALUE_TO_KEY[job.status] +
                     "] " if nocolor == True else "")
                if statusChange is not None:
                    # Writes change if performed
                    result += (bcolors.BOLD +
                               bcolors.OKGREEN if nocolor == False else '')
                    result += (statusChange[job.name]
                               if job.name in statusChange else "")
                    result += (bcolors.ENDC +
                               bcolors.ENDC if nocolor == False else "")

                for child in children:
                    # Continues recursion
                    result += self._recursion_print(
                        child, level, visited, statusChange=statusChange, nocolor=nocolor)
            else:
                result += (" [" + Status.VALUE_TO_KEY[job.status] +
                           "] " if nocolor == True else "")

        return result
    
    @staticmethod
    def retrieve_packages(BasicConfig, expid, current_jobs=None):
        """
        Retrieves dictionaries that map the collection of packages in the experiment

        :param BasicConfig: Basic configuration 
        :type BasicConfig: Configuration Object
        :param expid: Experiment Id
        :type expid: String
        :param current_jobs: list of names of current jobs
        :type current_jobs: list
        :return: job to package, package to jobs, package to package_id, package to symbol  
        :rtype: Dictionary(Job Object, Package), Dictionary(Package, List of Job Objects), Dictionary(String, String), Dictionary(String, String)
        """
        # monitor = Monitor()
        packages = None
        try:
            packages = JobPackagePersistence(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl"),
                                             "job_packages_" + expid).load(wrapper=False)
        except Exception as ex:
            print("Wrapper table not found, trying packages.")
            packages = None
            try:
                packages = JobPackagePersistence(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl"),
                                                 "job_packages_" + expid).load(wrapper=True)
            except Exception as exp2:
                packages = None
                pass
            pass

        job_to_package = dict()
        package_to_jobs = dict()
        package_to_package_id = dict()
        package_to_symbol = dict()
        if (packages):
            try:
                for exp, package_name, job_name in packages:
                    if len(str(package_name).strip()) > 0:
                        if (current_jobs):
                            if job_name in current_jobs:
                                job_to_package[job_name] = package_name
                        else:
                            job_to_package[job_name] = package_name
                    # list_packages.add(package_name)
                for name in job_to_package:
                    package_name = job_to_package[name]
                    package_to_jobs.setdefault(package_name, []).append(name)
                    # if package_name not in package_to_jobs.keys():
                    #     package_to_jobs[package_name] = list()
                    # package_to_jobs[package_name].append(name)
                for key in package_to_jobs:
                    package_to_package_id[key] = key.split("_")[2]
                list_packages = job_to_package.values()
                for i in range(len(list_packages)):
                    if i % 2 == 0:
                        package_to_symbol[list_packages[i]] = 'square'
                    else:
                        package_to_symbol[list_packages[i]] = 'hexagon'
            except Exception as ex:
                print(traceback.format_exc())

        return (job_to_package, package_to_jobs, package_to_package_id, package_to_symbol)

    @staticmethod
    def retrieve_times(status_code, name, tmp_path, make_exception=False, job_times=None, seconds=False, job_data_collection=None):
        """
        Retrieve job timestamps from database.  
        :param status_code: Code of the Status of the job  
        :type status_code: Integer  
        :param name: Name of the job  
        :type name: String  
        :param tmp_path: Path to the tmp folder of the experiment  
        :type tmp_path: String  
        :param make_exception: flag for testing purposes  
        :type make_exception: Boolean
        :param job_times: Detail from as_times.job_times for the experiment
        :type job_times: Dictionary Key: job name, Value: 5-tuple (submit time, start time, finish time, status, detail id)
        :return: minutes the job has been queuing, minutes the job has been running, and the text that represents it  
        :rtype: int, int, str
        """
        status = "NA"
        energy = 0
        seconds_queued = 0
        seconds_running = 0
        queue_time = running_time = 0
        submit_time = datetime.timedelta()
        start_time = datetime.timedelta()
        finish_time = datetime.timedelta()
        running_for_min = datetime.timedelta()
        queuing_for_min = datetime.timedelta()

        try:
            # Getting data from new job database
            if job_data_collection is not None:
                job_data = next(
                    (job for job in job_data_collection if job.job_name == name), None)
                if job_data:
                    status = Status.VALUE_TO_KEY[status_code]
                    if status == job_data.status:
                        energy = job_data.energy
                        t_submit = job_data.submit
                        t_start = job_data.start
                        t_finish = job_data.finish
                        # Test if start time does not make sense
                        if t_start >= t_finish:
                            if job_times:
                                _, c_start, c_finish, _, _ = job_times.get(
                                    name, (0, t_start, t_finish, 0, 0))
                                t_start = c_start if t_start > c_start else t_start
                                job_data.start = t_start

                        if seconds == False:
                            queue_time = math.ceil(
                                job_data.queuing_time() / 60)
                            running_time = math.ceil(
                                job_data.running_time() / 60)
                        else:
                            queue_time = job_data.queuing_time()
                            running_time = job_data.running_time()

                        if status_code in [Status.SUSPENDED]:
                            t_submit = t_start = t_finish = 0

                        return JobRow(job_data.job_name, int(queue_time), int(running_time), status, energy, JobList.ts_to_datetime(t_submit), JobList.ts_to_datetime(t_start), JobList.ts_to_datetime(t_finish), job_data.ncpus, job_data.run_id)

            # Using standard procedure
            if status_code in [Status.RUNNING, Status.SUBMITTED, Status.QUEUING, Status.FAILED] or make_exception == True:
                # COMPLETED adds too much overhead so these values are now stored in a database and retrieved separatedly
                submit_time, start_time, finish_time, status = JobList._job_running_check(
                    status_code, name, tmp_path)
                if status_code in [Status.RUNNING, Status.FAILED]:
                    running_for_min = (finish_time - start_time)
                    queuing_for_min = (start_time - submit_time)
                    submit_time = mktime(submit_time.timetuple())
                    start_time = mktime(start_time.timetuple())
                    finish_time = mktime(finish_time.timetuple()) if status_code in [
                        Status.FAILED] else 0
                else:
                    queuing_for_min = (
                        datetime.datetime.now() - submit_time)
                    running_for_min = datetime.datetime.now() - datetime.datetime.now()
                    submit_time = mktime(submit_time.timetuple())
                    start_time = 0
                    finish_time = 0

                submit_time = int(submit_time)
                start_time = int(start_time)
                finish_time = int(finish_time)
                seconds_queued = queuing_for_min.total_seconds()
                seconds_running = running_for_min.total_seconds()

            else:
                # For job times completed we no longer use timedeltas, but timestamps
                status = Status.VALUE_TO_KEY[status_code]
                if (job_times) and status_code not in [Status.READY, Status.WAITING, Status.SUSPENDED]:
                    if name in job_times.keys():
                        submit_time, start_time, finish_time, status, detail_id = job_times[
                            name]
                        seconds_running = finish_time - start_time
                        seconds_queued = start_time - submit_time
                        submit_time = int(submit_time)
                        start_time = int(start_time)
                        finish_time = int(finish_time)
                else:
                    submit_time = 0
                    start_time = 0
                    finish_time = 0

        except Exception as exp:
            print(traceback.format_exc())
            return

        seconds_queued = seconds_queued * \
            (-1) if seconds_queued < 0 else seconds_queued
        seconds_running = seconds_running * \
            (-1) if seconds_running < 0 else seconds_running
        if seconds == False:
            queue_time = math.ceil(
                seconds_queued / 60) if seconds_queued > 0 else 0
            running_time = math.ceil(
                seconds_running / 60) if seconds_running > 0 else 0
        else:
            queue_time = seconds_queued
            running_time = seconds_running

        return JobRow(name, 
                    int(queue_time), 
                    int(running_time), 
                    status, 
                    energy, 
                    JobList.ts_to_datetime(submit_time), 
                    JobList.ts_to_datetime(start_time), 
                    JobList.ts_to_datetime(finish_time), 
                    0,
                    0)
    
    @staticmethod
    def _job_running_check(status_code, name, tmp_path):
        """
        Receives job data and returns the data from its TOTAL_STATS file in an ordered way.  
        :param status_code: Status of job  
        :type status_code: Integer  
        :param name: Name of job  
        :type name: String  
        :param tmp_path: Path to the tmp folder of the experiment  
        :type tmp_path: String  
        :return: submit time, start time, end time, status  
        :rtype: 4-tuple in datetime format
        """
        # name = "a2d0_20161226_001_124_ARCHIVE"
        values = list()
        status_from_job = str(Status.VALUE_TO_KEY[status_code])
        now = datetime.datetime.now()
        submit_time = now
        start_time = now
        finish_time = now
        current_status = status_from_job
        path = os.path.join(tmp_path, name + '_TOTAL_STATS')
        # print("Looking in " + path)
        if os.path.exists(path):
            request = 'tail -1 ' + path
            last_line = os.popen(request).readline()
            # print(last_line)

            values = last_line.split()
            # print(last_line)
            try:
                if status_code in [Status.RUNNING]:
                    submit_time = parse_date(
                        values[0]) if len(values) > 0 else now
                    start_time = parse_date(values[1]) if len(
                        values) > 1 else submit_time
                    finish_time = now
                elif status_code in [Status.QUEUING, Status.SUBMITTED, Status.HELD]:
                    submit_time = parse_date(
                        values[0]) if len(values) > 0 else now
                    start_time = parse_date(
                        values[1]) if len(values) > 1 and values[0] != values[1] else now
                elif status_code in [Status.COMPLETED]:
                    submit_time = parse_date(
                        values[0]) if len(values) > 0 else now
                    start_time = parse_date(
                        values[1]) if len(values) > 1 else submit_time
                    if len(values) > 3:
                        finish_time = parse_date(values[len(values) - 2])
                    else:
                        finish_time = submit_time
                else:
                    submit_time = parse_date(
                        values[0]) if len(values) > 0 else now
                    start_time = parse_date(values[1]) if len(
                        values) > 1 else submit_time
                    finish_time = parse_date(values[2]) if len(
                        values) > 2 else start_time
            except Exception as exp:
                start_time = now
                finish_time = now
                # NA if reading fails
                current_status = "NA"

        current_status = values[3] if (len(values) > 3 and len(
            values[3]) != 14) else status_from_job
        # TOTAL_STATS last line has more than 3 items, status is different from pkl, and status is not "NA"
        if len(values) > 3 and current_status != status_from_job and current_status != "NA":
            current_status = "SUSPICIOUS"
        return (submit_time, start_time, finish_time, current_status)
    
    @staticmethod
    def ts_to_datetime(timestamp):
        if timestamp and timestamp > 0:
            # print(datetime.datetime.utcfromtimestamp(
            #     timestamp).strftime('%Y-%m-%d %H:%M:%S'))
            return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        else:
            return None