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

from autosubmit.job.job import Job
from bscearth.utils.date import date2str
from autosubmit.job.job_common import Status, Type
from log.log import Log, AutosubmitError, AutosubmitCritical
from collections.abc import Iterable
class DicJobs:
    """
    Class to create jobs from conf file and to find jobs by start date, member and chunk

    :param jobs_list: jobs list to use
    :type jobs_list: Joblist

    :param date_list: start dates
    :type date_list: list
    :param member_list: member
    :type member_list: list
    :param chunk_list: chunks
    :type chunk_list: list
    :param date_format: option to format dates
    :type date_format: str
    :param default_retrials: default retrials for ech job
    :type default_retrials: int
    :type default_retrials: config_common
    """

    def __init__(self, jobs_list, date_list, member_list, chunk_list, date_format, default_retrials,jobs_data,experiment_data):
        self._date_list = date_list
        self._jobs_list = jobs_list
        self._member_list = member_list
        self._chunk_list = chunk_list
        self._jobs_data = jobs_data
        self._date_format = date_format
        self.default_retrials = default_retrials
        self._dic = dict()
        self.experiment_data = experiment_data

    def read_section(self, section, priority, default_job_type, jobs_data=dict()):
        """
        Read a section from jobs conf and creates all jobs for it

        :param default_job_type: default type for jobs
        :type default_job_type: str
        :param jobs_data: dictionary containing the plain data from jobs
        :type jobs_data: dict
        :param section: section to read, and it's info
        :type section: tuple(str,dict)
        :param priority: priority for the jobs
        :type priority: int
        """
        parameters = self.experiment_data["JOBS"]

        splits = int(parameters[section].get("SPLITS", -1))
        running = str(parameters[section].get('RUNNING',"once")).lower()
        frequency = int(parameters[section].get("FREQUENCY", 1))
        if running == 'once':
            self._create_jobs_once(section, priority, default_job_type, jobs_data,splits)
        elif running == 'date':
            self._create_jobs_startdate(section, priority, frequency, default_job_type, jobs_data,splits)
        elif running == 'member':
            self._create_jobs_member(section, priority, frequency, default_job_type, jobs_data,splits)
        elif running == 'chunk':
            synchronize = str(parameters[section].get("SYNCHRONIZE", ""))
            delay = int(parameters[section].get("DELAY", -1))
            self._create_jobs_chunk(section, priority, frequency, default_job_type, synchronize, delay, splits, jobs_data)



        pass

    def _create_jobs_startdate(self, section, priority, frequency, default_job_type, jobs_data=dict(), splits=-1):
        """
        Create jobs to be run once per start date

        :param section: section to read
        :type section: str
        :param priority: priority for the jobs
        :type priority: int
        :param frequency: if greater than 1, only creates one job each frequency startdates. Always creates one job
                          for the last
        :type frequency: int
        """
        self._dic[section] = dict()
        tmp_dic = dict()
        tmp_dic[section] = dict()
        count = 0
        for date in self._date_list:
            count += 1
            if count % frequency == 0 or count == len(self._date_list):
                if splits <= 0:
                    self._dic[section][date] = self.build_job(section, priority, date, None, None, default_job_type,
                                                              jobs_data)
                    self._jobs_list.graph.add_node(self._dic[section][date].name)
                else:
                    tmp_dic[section][date] = []
                    self._create_jobs_split(splits, section, date, None, None, priority,
                                            default_job_type, jobs_data, tmp_dic[section][date])
                    self._dic[section][date] = tmp_dic[section][date]

    def _create_jobs_member(self, section, priority, frequency, default_job_type, jobs_data=dict(),splits=-1):
        """
        Create jobs to be run once per member

        :param section: section to read
        :type section: str
        :param priority: priority for the jobs
        :type priority: int
        :param frequency: if greater than 1, only creates one job each frequency members. Always creates one job
                          for the last
        :type frequency: int
        :type excluded_members: list
        :param excluded_members: if member index is listed there, the job won't run for this member.

        """
        self._dic[section] = dict()
        tmp_dic = dict()
        tmp_dic[section] = dict()
        for date in self._date_list:
            self._dic[section][date] = dict()
            count = 0
            for member in self._member_list:
                count += 1
                if count % frequency == 0 or count == len(self._member_list):
                    if splits <= 0:
                        self._dic[section][date][member] = self.build_job(section, priority, date, member, None,default_job_type, jobs_data,splits)
                        self._jobs_list.graph.add_node(self._dic[section][date][member].name)
                    else:
                        self._create_jobs_split(splits, section, date, member, None, priority,
                                                default_job_type, jobs_data, tmp_dic[section][date][member])
                        self._dic[section][date][member] = tmp_dic[section][date][member]

    def _create_jobs_once(self, section, priority, default_job_type, jobs_data=dict(),splits=0):
        """
        Create jobs to be run once

        :param section: section to read
        :type section: str
        :param priority: priority for the jobs
        :type priority: int
        """


        if splits <= 0:
            job = self.build_job(section, priority, None, None, None, default_job_type, jobs_data, -1)
            self._dic[section] = job
            self._jobs_list.graph.add_node(job.name)
        else:
            self._dic[section] = []
        total_jobs = 1
        while total_jobs <= splits:
            job = self.build_job(section, priority, None, None, None, default_job_type, jobs_data, total_jobs)
            self._dic[section].append(job)
            self._jobs_list.graph.add_node(job.name)
            total_jobs += 1
        pass

        #self._dic[section] = self.build_job(section, priority, None, None, None, default_job_type, jobs_data)
        #self._jobs_list.graph.add_node(self._dic[section].name)
    def _create_jobs_chunk(self, section, priority, frequency, default_job_type, synchronize=None, delay=0, splits=0, jobs_data=dict()):
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
        :param delay: if this parameter is set, the job is only created for the chunks greater than the delay
        :type delay: int
        """
        # Temporally creation for unified jobs in case of synchronize
        tmp_dic = dict()
        if synchronize is not None and len(str(synchronize)) > 0:
            count = 0
            for chunk in self._chunk_list:
                count += 1
                if delay == -1 or delay < chunk:
                    if count % frequency == 0 or count == len(self._chunk_list):
                        if splits > 1:
                            if synchronize == 'date':
                                tmp_dic[chunk] = []
                                self._create_jobs_split(splits, section, None, None, chunk, priority,
                                                   default_job_type, jobs_data, tmp_dic[chunk])
                            elif synchronize == 'member':
                                tmp_dic[chunk] = dict()
                                for date in self._date_list:
                                    tmp_dic[chunk][date] = []
                                    self._create_jobs_split(splits, section, date, None, chunk, priority,
                                                            default_job_type, jobs_data, tmp_dic[chunk][date])

                        else:
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
                    if delay == -1 or delay < chunk:
                        if count % frequency == 0 or count == len(self._chunk_list):
                            if synchronize == 'date':
                                if chunk in tmp_dic:
                                    self._dic[section][date][member][chunk] = tmp_dic[chunk]
                            elif synchronize == 'member':
                                if chunk in tmp_dic:
                                    self._dic[section][date][member][chunk] = tmp_dic[chunk][date]

                            if splits > 1 and (synchronize is None or not synchronize):
                                self._dic[section][date][member][chunk] = []
                                self._create_jobs_split(splits, section, date, member, chunk, priority, default_job_type, jobs_data, self._dic[section][date][member][chunk])
                                pass
                            elif synchronize is None or not synchronize:
                                self._dic[section][date][member][chunk] = self.build_job(section, priority, date, member,
                                                                                             chunk, default_job_type, jobs_data)
                                self._jobs_list.graph.add_node(self._dic[section][date][member][chunk].name)

    def _create_jobs_split(self, splits, section, date, member, chunk, priority, default_job_type, jobs_data, dict_):
        total_jobs = 1
        while total_jobs <= splits:
            job = self.build_job(section, priority, date, member, chunk, default_job_type, jobs_data, total_jobs)
            dict_.append(job)
            self._jobs_list.graph.add_node(job.name)
            total_jobs += 1

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
        #once jobs
        if type(dic) is list:
            jobs = dic
        elif type(dic) is not dict:
            jobs.append(dic)
        else:
            if date is not None and len(str(date)) > 0:
                self._get_date(jobs, dic, date, member, chunk)
            else:
                for d in self._date_list:
                    self._get_date(jobs, dic, d, member, chunk)
        if len(jobs) > 1 and isinstance(jobs[0], Iterable):
            try:
                jobs_flattened = [job for jobs_to_flatten in jobs for job in jobs_to_flatten]
                jobs = jobs_flattened
            except TypeError as e:
                pass
        return jobs

    def _get_date(self, jobs, dic, date, member, chunk):
        if date not in dic:
            return jobs
        dic = dic[date]
        if type(dic) is list:
            for job in dic:
                jobs.append(job)
        elif type(dic) is not dict:
            jobs.append(dic)
        else:
            if member is not None and len(str(member)) > 0:
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
            if chunk is not None and len(str(chunk)) > 0:
                if chunk in dic:
                    jobs.append(dic[chunk])
            else:
                for c in self._chunk_list:
                    if c not in dic:
                        continue
                    jobs.append(dic[c])
        return jobs

    def build_job(self, section, priority, date, member, chunk, default_job_type, jobs_data=dict(), split=-1):
        parameters = self.experiment_data["JOBS"]
        name = self._jobs_list.expid
        if date is not None and len(str(date)) > 0:
            name += "_" + date2str(date, self._date_format)
        if member is not None and len(str(member)) > 0:
            name += "_" + member
        if chunk is not None and len(str(chunk)) > 0:
            name += "_{0}".format(chunk)
        if split > -1:
            name += "_{0}".format(split)
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
        job.delete_when_edgeless = str(parameters[section].get("DELETE_WHEN_EDGELESS", "true")).lower()

        if split > -1:
            job.split = split

        job.frequency = int(parameters[section].get( "FREQUENCY", 1))
        job.delay = int(parameters[section].get( "DELAY", -1))
        job.wait = str(parameters[section].get( "WAIT", True)).lower()
        job.rerun_only = str(parameters[section].get( "RERUN_ONLY", False)).lower()
        job_type = str(parameters[section].get( "TYPE", default_job_type)).lower()

        job.dependencies = parameters[section].get( "DEPENDENCIES", "")
        if job.dependencies and type(job.dependencies) is not dict:
            job.dependencies = str(job.dependencies).split()
        if job_type == 'bash':
            job.type = Type.BASH
        elif job_type == 'python' or job_type == 'python3':
            job.type = Type.PYTHON3
        elif job_type == 'python2':
            job.type = Type.PYTHON2
        elif job_type == 'r':
            job.type = Type.R
        job.executable = str(parameters[section].get( "EXECUTABLE", ""))
        hpcarch = self.experiment_data.get("DEFAULT",{})
        hpcarch = hpcarch.get("HPCARCH","")
        job.platform_name = str(parameters[section].get("PLATFORM", hpcarch)).upper()
        if self.experiment_data["PLATFORMS"].get(job.platform_name, "") == "" and job.platform_name.upper() != "LOCAL":
            raise AutosubmitCritical("Platform does not exists, check the value of %JOBS.{0}.PLATFORM% = {1} parameter".format(job.section,job.platform_name),7000,"List of platforms: {0} ".format(self.experiment_data["PLATFORMS"].keys()) )
        job.file = str(parameters[section].get( "FILE", ""))
        job.additional_files = parameters[section].get( "ADDITIONAL_FILES", [])

        job.queue = str(parameters[section].get( "QUEUE", ""))
        job.ec_queue = str(parameters[section].get("EC_QUEUE", ""))
        if job.ec_queue == "" and job.platform_name != "LOCAL":
            job.ec_queue = str(self.experiment_data["PLATFORMS"][job.platform_name].get("EC_QUEUE","hpc"))

        job.partition = str(parameters[section].get( "PARTITION", ""))
        if job.partition == "" and job.platform_name.upper() not in ["LOCAL",""]:
            job.partition = str(self.experiment_data["PLATFORMS"][job.platform_name].get("PARTITION",""))
        job.check = str(parameters[section].get( "CHECK", "true")).lower()
        job.export = str(parameters[section].get( "EXPORT", ""))
        job.processors = str(parameters[section].get( "PROCESSORS", ""))
        job.threads = str(parameters[section].get( "THREADS", ""))
        job.tasks = str(parameters[section].get( "TASKS", ""))
        job.memory = str(parameters[section].get("MEMORY", ""))
        job.memory_per_task = str(parameters[section].get("MEMORY_PER_TASK", ""))
        remote_max_wallclock = self.experiment_data["PLATFORMS"].get(job.platform_name,{})
        remote_max_wallclock = remote_max_wallclock.get("MAX_WALLCLOCK",None)
        job.wallclock = parameters[section].get("WALLCLOCK", remote_max_wallclock)
        job.retrials = int(parameters[section].get( 'RETRIALS', 0))
        job.delay_retrials = int(parameters[section].get( 'DELAY_RETRY_TIME', "-1"))
        if job.wallclock is None and job.platform_name.upper() != "LOCAL":
            job.wallclock = "01:59"
        elif job.wallclock is None and job.platform_name.upper() != "LOCAL":
            job.wallclock = "00:00"
        elif job.wallclock is None:
            job.wallclock = "00:00"
        if job.retrials == -1:
            job.retrials = None
        notify_on = parameters[section].get("NOTIFY_ON",None)
        if type(notify_on) == str:
            job.notify_on = [x.upper() for x in notify_on.split(' ')]
        else:
            job.notify_on = ""
        job.synchronize = str(parameters[section].get( "SYNCHRONIZE", ""))
        job.check_warnings = str(parameters[section].get("SHOW_CHECK_WARNINGS", False)).lower()
        job.running = str(parameters[section].get( 'RUNNING', 'once'))
        job.x11 = str(parameters[section].get( 'X11', False )).lower()
        job.skippable = str(parameters[section].get( "SKIPPABLE", False)).lower()
        self._jobs_list.get_job_list().append(job)

        return job


