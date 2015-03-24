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
from ConfigParser import SafeConfigParser
import json

import os
import pickle
from time import localtime, strftime
from sys import setrecursionlimit
from shutil import move

from autosubmit.job.job_common import Status
from autosubmit.job.job import Job
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.config.log import Log


class JobList:
    """
    Class to manage the list of jobs to be run by autosubmit
    """
    def __init__(self, expid):
        self._pkl_path = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/"
        self._update_file = "updated_list_" + expid + ".txt"
        self._failed_file = "failed_job_list_" + expid + ".pkl"
        self._job_list_file = "job_list_" + expid + ".pkl"
        self._job_list = list()
        self._expid = expid
        self._stat_val = Status()
        self._parameters = []

    @property
    def expid(self):
        """
        Experiment identifier
        """
        return self._expid

    def create(self, date_list, member_list, starting_chunk, num_chunks, parameters):
        """
        Creates all jobs needed for the current workflow

        :param date_list: list of start dates
        :param member_list: list of members
        :param starting_chunk: number of starting chunk
        :param num_chunks: number of chunks to run
        :param parameters: parameters for the jobs
        """
        self._parameters = parameters

        parser = SafeConfigParser()
        parser.optionxform = str
        parser.read(os.path.join(BasicConfig.LOCAL_ROOT_DIR, self._expid, 'conf', "jobs_" + self._expid + ".conf"))

        chunk_list = range(starting_chunk, starting_chunk + num_chunks)

        self._date_list = date_list
        self._member_list = member_list
        self._chunk_list = chunk_list

        dic_jobs = DicJobs(self, parser, date_list, member_list, chunk_list)
        self._dic_jobs = dic_jobs
        priority = 0

        Log.info("Creating jobs...")
        for section in parser.sections():
            Log.debug("Creating {0} jobs".format(section))
            dic_jobs.read_section(section, priority)
            priority += 1

        Log.info("Adding dependencies...")
        for section in parser.sections():
            Log.debug("Adding dependencies for {0} jobs".format(section))
            if not parser.has_option(section, "DEPENDENCIES"):
                continue
            dependencies = parser.get(section, "DEPENDENCIES").split()
            dep_section = dict()
            dep_distance = dict()
            dep_running = dict()
            for dependency in dependencies:
                if '-' in dependency:
                    dependency_split = dependency.split('-')
                    dep_section[dependency] = dependency_split[0]
                    dep_distance[dependency] = int(dependency_split[1])
                    dep_running[dependency] = dic_jobs.get_option(dependency_split[0], 'RUNNING', 'once').lower()
                else:
                    dep_section[dependency] = dependency

            for job in dic_jobs.get_jobs(section):
                for dependency in dependencies:
                    chunk = job.chunk
                    member = job.member
                    date = job.date

                    section_name = dep_section[dependency]

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

                    for parent in dic_jobs.get_jobs(section_name, date, member, chunk):
                        job.add_parent(parent)

                    if job.wait and job.frequency > 1:
                        if job.chunk is not None:
                            max_distance = (chunk_list.index(chunk)+1) % job.frequency
                            if max_distance == 0:
                                max_distance = job.frequency
                            for distance in range(1, max_distance, 1):
                                for parent in dic_jobs.get_jobs(section_name, date, member, chunk - distance):
                                    job.add_parent(parent)
                        elif job.member is not None:
                            max_distance = (member_list.index(chunk)+1) % job.frequency
                            if max_distance == 0:
                                max_distance = job.frequency
                            for distance in range(1, max_distance, 1):
                                for parent in dic_jobs.get_jobs(section_name, date, member - distance, chunk):
                                    job.add_parent(parent)
                        elif job.date is not None:
                            max_distance = (date_list.index(chunk)+1) % job.frequency
                            if max_distance == 0:
                                max_distance = job.frequency
                            for distance in range(1, max_distance, 1):
                                for parent in dic_jobs.get_jobs(section_name, date - distance, member, chunk):
                                    job.add_parent(parent)

        Log.info("Removing redundant dependencies...")
        self.update_genealogy()
        for job in self._job_list:
            job.parameters = parameters

    def __len__(self):
        return self._job_list.__len__()

    def get_job_list(self):
        """
        Get inner job list

        :return: job list
        """
        return self._job_list

    def get_completed(self):
        """
        Returns a list of completed jobs
        """
        return [job for job in self._job_list if job.status == Status.COMPLETED]

    def get_submitted(self):
        """
        Returns a list of submitted jobs
        """
        return [job for job in self._job_list if job.status == Status.SUBMITTED]

    def get_running(self):
        """
        Returns a list of jobs running
        """
        return [job for job in self._job_list if job.status == Status.RUNNING]

    def get_queuing(self):
        """
        Returns a list of jobs queuing
        """
        return [job for job in self._job_list if job.status == Status.QUEUING]

    def get_failed(self):
        """
        Returns a list of failed jobs
        """
        return [job for job in self._job_list if job.status == Status.FAILED]

    def get_ready(self):
        """
        Returns a list of ready jobs
        """
        return [job for job in self._job_list if job.status == Status.READY]

    def get_waiting(self):
        """
        Returns a list of jobs waiting
        """
        return [job for job in self._job_list if job.status == Status.WAITING]

    def get_unknown(self):
        """
        Returns a list of jobs unknown
        """
        return [job for job in self._job_list if job.status == Status.UNKNOWN]

    def get_in_queue(self):
        """
        Returns a list of jobs in the queue (Submitted, Running, Queuing)
        """
        return self.get_submitted() + self.get_running() + self.get_queuing()

    def get_not_in_queue(self):
        """
        Returns a list of jobs NOT in the queue (Ready, Waiting)
        """
        return self.get_ready() + self.get_waiting()

    def get_finished(self):
        """
        Returns a list of jobs finished (Completed, Failed)
        """
        return self.get_completed() + self.get_failed()

    def get_active(self):
        """
        Returns a list of active jobs (In queue, Ready)
        """
        return self.get_in_queue() + self.get_ready() + self.get_unknown()

    def get_job_by_name(self, name):
        """
        Returns the job that its name matches parameter name

        :parameter name: name to look for
        """
        for job in self._job_list:
            if job.name == name:
                return job
        Log.warning("We could not find that job {0} in the list!!!!", name)

    def sort_by_name(self):
        """
        Returns a list of jobs sorted by name

        :return: job list
        """
        return sorted(self._job_list, key=lambda k: k.name)

    def sort_by_id(self):
        """
        Returns a list of jobs sorted by id

        :return: job list
        """
        return sorted(self._job_list, key=lambda k: k.id)

    def sort_by_type(self):
        """
        Returns a list of jobs sorted by type

        :return: job list
        """
        return sorted(self._job_list, key=lambda k: k.type)

    def sort_by_status(self):
        """
        Returns a list of jobs sorted by status

        :return: job list
        """
        return sorted(self._job_list, key=lambda k: k.status)

    @staticmethod
    def load_file(filename):
        """
        Recreates an stored joblist from the pickle file

        :param filename:
        :return: loaded joblist object
        """
        if os.path.exists(filename):
            return pickle.load(file(filename, 'r'))
        else:
            Log.critical('File {0} does not exist'.format(filename))
            return list()

    def load(self):
        """
        Recreates an stored joblist from the pickle file

        :param filename:
        :return: loaded joblist object
        """
        Log.info("Loading JobList: " + self._pkl_path + self._job_list_file)
        return JobList.load_file(self._pkl_path + self._job_list_file)

    def load_updated(self):
        Log.info("Loading updated list: " + self._pkl_path + self._update_file)
        return JobList.load_file(self._pkl_path + self._update_file)

    def load_failed(self):
        Log.info("Loading failed list: " + self._pkl_path + self._failed_file)
        return JobList.load_file(self._pkl_path + self._failed_file)

    def save_failed(self, failed_list):
        # URi: should we check that the path exists?
        Log.info("Saving failed list: " + self._pkl_path + self._failed_file)
        pickle.dump(failed_list, file(self._pkl_path + self._failed_file, 'w'))

    def save(self):
        """
        Stores joblist as a pickle file

        :return: loaded joblist object
        """
        setrecursionlimit(50000)
        Log.debug("Saving JobList: " + self._pkl_path + self._job_list_file)
        pickle.dump(self, file(self._pkl_path + self._job_list_file, 'w'))

    def update_from_file(self, store_change=True):
        if os.path.exists(self._pkl_path + self._update_file):
            for line in open(self._pkl_path + self._update_file):
                if line.strip() == '':
                    continue
                job = self.get_job_by_name(line.split()[0])
                if job:
                    job.status = self._stat_val.retval(line.split()[1])
                    job.fail_count = 0
            now = localtime()
            output_date = strftime("%Y%m%d_%H%M", now)
            if store_change:
                move(self._pkl_path + self._update_file, self._pkl_path + self._update_file + "_" + output_date)

    def update_parameters(self, parameters):
        self._parameters = parameters
        for job in self._job_list:
            job.parameters = parameters

    def update_list(self, store_change=True):
        # load updated file list
        self.update_from_file(store_change)

        # reset jobs that has failed less ethan 10 times
        if 'RETRIALS' in self._parameters:
            retrials = int(self._parameters['RETRIALS'])
        else:
            retrials = 4

        for job in self.get_failed():
            job.inc_fail_count()
            if job.fail_count < retrials:
                job.status = Status.READY

        # if waiting jobs has all parents completed change its State to READY
        for job in self.get_waiting():
            tmp = [parent for parent in job.parents if parent.status == Status.COMPLETED]
            # for parent in job.parents:
            # if parent.status != Status.COMPLETED:
            # break
            if len(tmp) == len(job.parents):
                job.status = Status.READY
        if store_change:
            self.save()

    def update_shortened_names(self):
        """
        In some cases the scheduler only can operate with names shorter than 15 characters.
        Update the job list replacing job names by the corresponding shortened job name
        """
        for job in self._job_list:
            job.name = job.short_name

    def update_genealogy(self):
        """
        When we have created the joblist, every type of job is created.
        Update genealogy remove jobs that have no templates
        """

        # Use a copy of job_list because original is modified along iterations
        for job in self._job_list[:]:
            if job.file is None or job.file == '':
                self._remove_job(job)

        # Simplifing dependencies: if a parent is alreaday an ancestor of another parent,
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
        """
        out = True
        for job in self._job_list:
            if not job.check_script(as_conf):
                out = False
                Log.warning("Invalid parameter substitution in {0}!!!" % job.name)

        return out

    def _remove_job(self, job):
        for child in job.children:
            for parent in job.parents:
                child.add_parent(parent)
            child.delete_parent(job)

        for parent in job.parents:
            parent.children.remove(job)

        self._job_list.remove(job)

    def rerun(self, chunk_list):
        parser = SafeConfigParser()
        parser.optionxform = str
        parser.read(os.path.join(BasicConfig.LOCAL_ROOT_DIR, self._expid, 'conf', "jobs_" + self._expid + ".conf"))

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
                if '-' in dependency:
                    dependency_split = dependency.split('-')
                    dep_section[section][dependency] = dependency_split[0]
                    dep_distance[section][dependency] = int(dependency_split[1])
                    dep_running[section][dependency] = self._dic_jobs.get_option(dependency_split[0], 'RUNNING',
                                                                                 'once').lower()
                else:
                    dep_section[section][dependency] = dependency

        for job in self._job_list:
            job.status = Status.COMPLETED

        data = json.loads(chunk_list)
        for d in data['sds']:
            date = d['sd']
            Log.debug("Date: " + date)
            for m in d['ms']:
                member = m['m']
                Log.debug("Member: " + member)
                for c in m['cs']:
                    Log.debug("Chunk: " + c)
                    chunk = int(c)
                    for job in [i for i in self._job_list if i.date == date and i.member == member
                                and i.chunk == chunk]:
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

        self.update_genealogy()
        del self._dic_jobs

    def remove_rerun_only_jobs(self):
        flag = False
        for job in self._job_list:
            if job.rerun_only:
                self._remove_job(job)
                flag = True

        if flag:
            self.update_genealogy()
        del self._dic_jobs


class DicJobs:
    def __init__(self, joblist, parser, date_list, member_list, chunk_list):
        self._date_list = date_list
        self._joblist = joblist
        self._member_list = member_list
        self._chunk_list = chunk_list
        self._parser = parser
        self._dic = dict()

    def read_section(self, section, priority):
        running = 'once'
        if self._parser.has_option(section, 'RUNNING'):
            running = self._parser.get(section, 'RUNNING').lower()
        frequency = int(self.get_option(section, "FREQUENCY", 1))
        if running == 'once':
            self._create_jobs_once(section, priority)
        elif running == 'startdate':
            self._create_jobs_startdate(section, priority, frequency)
        elif running == 'member':
            self._create_jobs_member(section, priority, frequency)
        elif running == 'chunk':
            self._create_jobs_chunk(section, priority, frequency)

    def _create_jobs_once(self, section, priority):
        self._dic[section] = self._create_job(section, priority, None, None, None)

    def _create_jobs_startdate(self, section, priority, frequency):
        self._dic[section] = dict()
        count = 0
        for date in self._date_list:
            count += 1
            if count % frequency == 0 or count == len(self._date_list):
                self._dic[section][date] = self._create_job(section, priority, date, None, None)

    def _create_jobs_member(self, section, priority, frequency):
        self._dic[section] = dict()
        for date in self._date_list:
            self._dic[section][date] = dict()
            count = 0
            for member in self._member_list:
                count += 1
                if count % frequency == 0 or count == len(self._member_list):
                    self._dic[section][date][member] = self._create_job(section, priority, date, member, None)

    def _create_jobs_chunk(self, section, priority, frequency):
        self._dic[section] = dict()
        for date in self._date_list:
            self._dic[section][date] = dict()
            for member in self._member_list:
                self._dic[section][date][member] = dict()
                count = 0
                for chunk in self._chunk_list:
                    count += 1
                    if count % frequency == 0 or count == len(self._chunk_list):
                        self._dic[section][date][member][chunk] = self._create_job(section, priority, date, member,
                                                                                   chunk)

    def get_jobs(self, section, date=None, member=None, chunk=None):
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
            name += "_" + date
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

        job.frequency = int(self.get_option(section, "FREQUENCY", 1))
        job.wait = self.get_option(section, "WAIT", 'false').lower() == 'true'
        job.rerun_only = self.get_option(section, "RERUN_ONLY", 'false').lower() == 'true'

        job.queue_name = self.get_option(section, "QUEUE", None)
        if job.queue_name is not None:
            job.queue_name = job.queue_name.lower()
        job.file = self.get_option(section, "FILE", None)

        job.processors = self.get_option(section, "PROCESSORS", 1)
        job.threads = self.get_option(section, "THREADS", 1)
        job.tasks = self.get_option(section, "TASKS", 1)

        job.wallclock = self.get_option(section, "WALLCLOCK", '')
        self._joblist.get_job_list().append(job)
        return job

    def get_option(self, section, option, default):
        if self._parser.has_option(section, option):
            return self._parser.get(section, option)
        else:
            return default
