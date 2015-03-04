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

import os
import pickle
from time import localtime, strftime
from sys import setrecursionlimit
from shutil import move

from job_common import Status
from autosubmit.job.job import Job
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.config.log import Log


class JobList:
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
        return self._expid

    def create(self, date_list, member_list, starting_chunk, num_chunks, parameters):
        self._parameters = parameters

        parser = SafeConfigParser()
        parser.optionxform = str
        parser.read(os.path.join(BasicConfig.LOCAL_ROOT_DIR, self._expid, 'conf', "jobs_" + self._expid + ".conf"))

        chunk_list = range(starting_chunk, starting_chunk + num_chunks)
        dic_jobs = DicJobs(self, parser, date_list, member_list, chunk_list)

        priority = 0
        for section in parser.sections():
            dic_jobs.read_section(section, priority)
            priority += 1

        for section in parser.sections():
            if not parser.has_option(section, "DEPENDENCIES"):
                continue
            dependencies = parser.get(section, "DEPENDENCIES").split()
            for job in dic_jobs.get_jobs(section):
                for dependency in dependencies:
                    chunk = job.chunk
                    member = job.member
                    date = job.date
                    if '-' in dependency:
                        dep_section = dependency.split('-')[0]
                        distance = int(dependency.split('-')[1])
                        if chunk is not None:
                            if chunk_list.index(chunk) >= distance:
                                chunk = chunk_list[chunk_list.index(chunk)-distance]
                            else:
                                continue
                        elif member is not None:
                            if member_list.index(member) >= distance:
                                member = member_list[member_list.index(member)-distance]
                            else:
                                continue
                        elif date is not None:
                            if date_list.index(date) >= distance:
                                date = date_list[date_list.index(date)-distance]
                            else:
                                continue
                    else:
                        dep_section = dependency
                    for parent in dic_jobs.get_jobs(dep_section, date, member, chunk):
                        job.add_parent(parent)
                    if job.wait:
                        if job.chunk is not None:
                            max_distance = (chunk_list.index(job.chunk)+1) % job.frequency
                            if max_distance == 0:
                                max_distance = job.frequency
                            for distance in range(1, max_distance, 1):
                                for parent in dic_jobs.get_jobs(dep_section, date, member, chunk - distance):
                                    job.add_parent(parent)
                        elif job.member is not None:
                            max_distance = (member_list.index(job.member)+1) % job.frequency
                            if max_distance == 0:
                                max_distance = job.frequency
                            for distance in range(1, max_distance, 1):
                                for parent in dic_jobs.get_jobs(dep_section, date, member - distance, chunk):
                                    job.add_parent(parent)
                        elif job.date is not None:
                            max_distance = (date_list.index(job.date)+1) % job.frequency
                            if max_distance == 0:
                                max_distance = job.frequency
                            for distance in range(1, max_distance, 1):
                                for parent in dic_jobs.get_jobs(dep_section, date - distance, member, chunk):
                                    job.add_parent(parent)

        self.update_genealogy()
        for job in self._job_list:
            job.parameters = parameters

    def __len__(self):
        return self._job_list.__len__()

    def get_job_list(self):
        return self._job_list

    def get_completed(self):
        """Returns a list of completed jobs"""
        return [job for job in self._job_list if job.status == Status.COMPLETED]

    def get_submitted(self):
        """Returns a list of submitted jobs"""
        return [job for job in self._job_list if job.status == Status.SUBMITTED]

    def get_running(self):
        """Returns a list of jobs running"""
        return [job for job in self._job_list if job.status == Status.RUNNING]

    def get_queuing(self):
        """Returns a list of jobs queuing"""
        return [job for job in self._job_list if job.status == Status.QUEUING]

    def get_failed(self):
        """Returns a list of failed jobs"""
        return [job for job in self._job_list if job.status == Status.FAILED]

    def get_ready(self):
        """Returns a list of jobs ready"""
        return [job for job in self._job_list if job.status == Status.READY]

    def get_waiting(self):
        """Returns a list of jobs waiting"""
        return [job for job in self._job_list if job.status == Status.WAITING]

    def get_unknown(self):
        """Returns a list of jobs unknown"""
        return [job for job in self._job_list if job.status == Status.UNKNOWN]

    def get_in_queue(self):
        """Returns a list of jobs in the queue (Submitted, Running, Queuing)"""
        return self.get_submitted() + self.get_running() + self.get_queuing()

    def get_not_in_queue(self):
        """Returns a list of jobs NOT in the queue (Ready, Waiting)"""
        return self.get_ready() + self.get_waiting()

    def get_finished(self):
        """Returns a list of jobs finished (Completed, Failed)"""
        return self.get_completed() + self.get_failed()

    def get_active(self):
        """Returns a list of active jobs (In queue, Ready)"""
        return self.get_in_queue() + self.get_ready() + self.get_unknown()

    def get_job_by_name(self, name):
        """Returns the job that its name matches name"""
        for job in self._job_list:
            if job.name == name:
                return job
        Log.warning("We could not find that job %s in the list!!!!", name)

    def sort_by_name(self):
        return sorted(self._job_list, key=lambda k: k.name)

    def sort_by_id(self):
        return sorted(self._job_list, key=lambda k: k.id)

    def sort_by_type(self):
        return sorted(self._job_list, key=lambda k: k.type)

    def sort_by_status(self):
        return sorted(self._job_list, key=lambda k: k.status)

    @staticmethod
    def load_file(filename):
        if os.path.exists(filename):
            return pickle.load(file(filename, 'r'))
        else:
            # URi: print ERROR
            return list()

    def load(self):
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
        # URi: should we check that the path exists?
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
        """In some cases the scheduler only can operate with names shorter than 15 characters.
        Update the job list replacing job names by the corresponding shortened job name"""
        for job in self._job_list:
            job.name = job.short_name

    def update_genealogy(self):
        """When we have created the joblist, every type of job is created.
        Update genealogy remove jobs that have no templates"""

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
        """When we have created the scripts, all parameters should have been substituted.
        %PARAMETER% handlers not allowed"""
        out = True
        for job in self._job_list:
            if not job.check_script(as_conf):
                out = False
                Log.warning("Invalid parameter substitution in %s!!!" % job.name)

        return out

    def _remove_job(self, job):
        for child in job.children:
            for parent in job.parents:
                child.add_parent(parent)
            child.parents.remove(job)

        for parent in job.parents:
            parent.children.remove(job)

        self._job_list.remove(job)


class RerunJobList(JobList):
    def __init__(self, expid):
        JobList.__init__(self, expid)
        self._pkl_path = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/"
        self._update_file = "updated_list_" + expid + ".txt"
        self._failed_file = "failed_job_list_" + expid + ".pkl"
        self._job_list_file = "rerun_job_list_" + expid + ".pkl"
        self._job_list = list()
        self._expid = expid
        self._stat_val = Status()
        self._parameters = []

    def create(self, date_list, member_list, starting_chunk, num_chunks, parameters):
        """
        DO NOT USE THIS METHOD. It's inherited from base class but has no meaning here.
        """
        # Create method on base class is not valid. Just preventing calling it by error
        raise NotImplementedError

    # Not intended to override
    # noinspection PyMethodOverriding,PyRedeclaration
    def create(self, chunk_list, starting_chunk, num_chunks, parameters):
        pass
        # Log.info("Creating job list...")
        # data = json.loads(chunk_list)
        # Log.debug("Data: %s", data)
        # self._parameters = parameters
        #
        # localsetupjob_name = self._expid + "_"
        # localsetup_job = Job(localsetupjob_name + "localsetup", 0, Status.READY, Type.LOCALSETUP)
        # remotesetupjob_name = self._expid + "_"
        # remotesetup_job = Job(remotesetupjob_name + "remotesetup", 0, Status.WAITING, Type.REMOTESETUP)
        # remotesetup_job.add_parent(localsetup_job)
        #
        # for date in data['sds']:
        #     Log.debug("Date: " + date['sd'])
        #     for member in date['ms']:
        #         Log.debug(member['m'])
        #         Log.debug(member['cs'])
        #
        #         first_chunk = int(member['cs'][0])
        #
        #         if len(member['cs']) > 1:
        #             second_chunk = int(member['cs'][1])
        #             last_chunk = int(member['cs'][len(member['cs']) - 1])
        #             second_last_chunk = int(member['cs'][len(member['cs']) - 2])
        #         else:
        #             last_chunk = first_chunk
        #             second_last_chunk = None
        #             second_chunk = None
        #
        #         inijob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_"
        #         ini_job = Job(inijob_name + "ini", 0, Status.WAITING, Type.INITIALISATION)
        #         ini_job.add_parent(remotesetup_job)
        #
        #         transjob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_"
        #         trans_job = Job(transjob_name + "trans", 0, Status.WAITING, Type.TRANSFER)
        #
        #         self._job_list += [ini_job]
        #         self._job_list += [trans_job]
        #
        #         for chunk in member['cs']:
        #             chunk = int(chunk)
        #             rootjob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(chunk) + "_"
        #             post_job = Job(rootjob_name + "post", 0, Status.WAITING, Type.POSTPROCESSING)
        #             clean_job = Job(rootjob_name + "clean", 0, Status.WAITING, Type.CLEANING)
        #             sim_job = Job(rootjob_name + "sim", 0, Status.WAITING, Type.SIMULATION)
        #             # set dependency of postprocessing jobs
        #             post_job.add_parent(sim_job)
        #             clean_job.add_parent(post_job)
        #             if chunk == last_chunk or chunk == second_last_chunk:
        #                 trans_job.add_parent(clean_job)
        #
        #             # Link parents:
        #             # if chunk is 1 then not needed to add the previous clean job
        #             if chunk == 1:
        #                 sim_job.add_parent(ini_job)
        #                 self._job_list += [sim_job, post_job, clean_job]
        #             elif chunk == first_chunk:
        #                 prev_new_job_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(
        #                     chunk - 1) + "_" + "clean"
        #                 prev_new_clean_job = Job(prev_new_job_name, 0, Status.WAITING, Type.CLEANING)
        #                 sim_job.add_parent(prev_new_clean_job)
        #                 prev_new_clean_job.add_parent(ini_job)
        #                 self._job_list += [prev_new_clean_job, sim_job, post_job, clean_job]
        #             else:
        #                 if chunk > first_chunk:
        #                     prev_chunk = int(member['cs'][member['cs'].index(str(chunk)) - 1])
        #                     # in case reruning no consecutive chunk we need to create the previous
        #                     # clean job in the basis of chunk-1
        #                     if prev_chunk != chunk - 1:
        #                         prev_new_job_name = self._expid + "_" + str(date['sd']) + "_" + str(
        #                             member['m']) + "_" + str(chunk - 1) + "_" + "clean"
        #                         prev_new_clean_job = Job(prev_new_job_name, 0, Status.WAITING, Type.CLEANING)
        #                         sim_job.add_parent(prev_new_clean_job)
        #                         # Link parent and child for new clean job:
        #                         prev_clean_job_name = self._expid + "_" + str(date['sd']) + "_" + str(
        #                             member['m']) + "_" + str(prev_chunk) + "_" + "clean"
        #                         prev_new_clean_job.add_parent(self.get_job_by_name(prev_clean_job_name))
        #                         # Add those to the list
        #                         self._job_list += [prev_new_clean_job, sim_job, post_job, clean_job]
        #                     # otherwise we should link backwards to the immediate before clean job
        #                     else:
        #                         prev_sim_job_name = self._expid + "_" + str(date['sd']) + "_" + str(
        #                             member['m']) + "_" + str(prev_chunk) + "_" + "sim"
        #                         sim_job.add_parent(self.get_job_by_name(prev_sim_job_name))
        #                         if chunk > second_chunk:cra
        #                             prev_prev_chunk = int(member['cs'][member['cs'].index(str(chunk)) - 2])
        #                             prev_clean_job_name = self._expid + "_" + str(date['sd']) + "_" + str(
        #                                 member['m']) + "_" + str(prev_prev_chunk) + "_" + "clean"
        #                             sim_job.add_parent(self.get_job_by_name(prev_clean_job_name))
        #                         # Add those to the list
        #                         self._job_list += [sim_job, post_job, clean_job]
        #
        #             if not member['cs']:
        #                 clean_job = ini_job
        #             if last_chunk != num_chunks:
        #                 finaljob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(
        #                     num_chunks) + "_" + "clean"
        #                 final_job = Job(finaljob_name, 0, Status.WAITING, Type.CLEANING)
        #                 final_job.add_parent(clean_job)
        #                 self._job_list += [final_job]
        #
        # self._job_list += [localsetup_job, remotesetup_job]
        #
        # self.update_genealogy()
        # for job in self._job_list:
        #     job.parameters = parameters


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
            for d in self._date_list:
                if date is not None and date != d:
                    continue
                if d not in dic:
                    continue
                if type(dic[d]) is not dict:
                    jobs.append(dic[d])
                else:
                    for m in self._member_list:
                        if member is not None and member != m:
                            continue
                        if m not in dic[d]:
                            continue
                        if type(dic[d][m]) is not dict:
                            jobs.append(dic[d][m])
                        else:
                            for c in self._chunk_list:
                                if chunk is not None and chunk != c:
                                    continue
                                if c not in dic[d][m]:
                                    continue
                                jobs.append(dic[d][m][c])
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
        job.wait = bool(self.get_option(section, "WAIT", False))

        job.queue_name = self.get_option(section, "QUEUE", None)
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