#!/usr/bin/env python

# Copyright 2017 Earth Sciences Department, BSC-CNS

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

from autosubmit.job.job_common import Status
from bscearth.utils.date import date2str
import copy

class JobGrouping(object):

    def __init__(self, group_by, jobs, job_list, date_format, expand_list=list()):
        self.group_by = group_by
        self.automatic = False
        self.jobs = jobs
        self.job_list = job_list
        self.date_format = date_format
        self.expand_list = expand_list
        if group_by == 'automatic':
            self.group_by = 'chunk'
            self.automatic = True

    def group_jobs(self):
        groups_dict = dict()

        jobs_group_dict = dict()
        self.group_status_dict = dict()
        blacklist = list()
        groups_map = dict()

        for date in reversed(self.job_list.get_date_list()):
            if self.group_by == 'date' or not self.job_list.get_member_list():
                self.create_group(jobs_group_dict, date, blacklist=blacklist)
            elif self.group_by in ['member', 'chunk', 'split']:
                for member in reversed(self.job_list.get_member_list()):
                    if self.group_by == 'member' or not self.job_list.get_chunk_list():
                        self.create_group(jobs_group_dict, date, member, blacklist=blacklist)
                    else:
                        for chunk in reversed(self.job_list.get_chunk_list()):
                            self.create_group(jobs_group_dict, date, member, chunk, blacklist=blacklist)

        for group, statuses in self.group_status_dict.items():
            status = self.set_group_status(statuses)
            self.group_status_dict[group] = status

        if self.automatic:
            self.create_higher_level_group(self.group_status_dict.keys(), groups_map)

        final_jobs_group = dict()
        for job, groups in jobs_group_dict.items():
            for group in groups:
                if group not in blacklist and group in self.group_status_dict: #to remove the jobs belonging to groups that should be expanded
                    while group in groups_map:
                        group = groups_map[group]
                    if job not in final_jobs_group:
                        final_jobs_group[job] = list()
                    final_jobs_group[job].append(group)

        jobs_group_dict = final_jobs_group

        groups_dict['jobs'] = jobs_group_dict
        groups_dict['status'] = self.group_status_dict

        return groups_dict

    def create_group(self, jobs_group_dict, date=None, member=None, chunk=None, blacklist=list()):
        if chunk is not None:
            name = date2str(date, self.date_format) + '_' + member + '_' +str(chunk)
        elif member is not None:
            name = date2str(date, self.date_format) + '_' + member
        else:
            name = date2str(date, self.date_format)

        for i in reversed(range(len(self.jobs))):
            job = self.jobs[i]

            if self.group_by == 'date':
                condition = (job.date == date or (job.date is None and job.chunk is not None)) and name not in blacklist
            elif self.group_by == 'member':
                condition = (job.date == date and job.member == member) or (job.date in [date, None] and job.member is None and job.chunk is not None) and name not in blacklist
            elif self.group_by  == 'chunk':
                condition = (job.member in [member, None] and job.date in [date, None] and job.chunk == chunk) and name not in blacklist
            elif self.group_by == 'split':
                idx = job.name.rfind("_")
                name = job.name[:idx - 1] + job.name[idx + 1:]
                condition = job.split is not None and name not in blacklist

            if (condition):
                if (job.chunk is None) or (job.member is not None and job.date is not None and job.chunk is not None):
                    self.jobs.pop(i) #if synchronized does not remove
                if name not in self.group_status_dict:
                    self.group_status_dict[name] = set()
                self.group_status_dict[name].add(job.status)

                if job.status in self.expand_list or (self.automatic and name in self.group_status_dict and (len(self.group_status_dict[name]) > 1)):
                    self.group_status_dict.pop(name)
                    blacklist.append(name)
                    break

                if job.name not in jobs_group_dict:
                    jobs_group_dict[job.name] = list()
                jobs_group_dict[job.name].append(name)

    def check_valid_group(self, groups_list, name, groups_map):
        group_status = self.group_status_dict[groups_list[0]]
        for group in groups_list[1:]:
            status = self.group_status_dict[group]
            if status != group_status:
                return False

        for group in groups_list:
            self.group_status_dict.pop(group)
            groups_map[group] = name
        self.group_status_dict[name] = group_status
        return True

    def create_higher_level_group(self, groups_to_check, groups_map):
        checked_groups = list()
        for group in groups_to_check:
            if group in self.group_status_dict:
                split_count = len(group.split('_'))
                if split_count > 0:
                    new_group = group[:(group.rfind("_"))]

                    num_groups = len(self.job_list.get_chunk_list()) if split_count == 3 else len(self.job_list.get_member_list())

                    if new_group not in checked_groups:
                        checked_groups.append(new_group)
                        possible_groups = [existing_group for existing_group in list(self.group_status_dict.keys()) if
                                              new_group in existing_group]

                        if len(possible_groups) == num_groups:
                            if self.check_valid_group(possible_groups, new_group, groups_map):
                                groups_to_check.append(new_group)

    def set_group_status(self, statuses):
        if isinstance(statuses, int):
            return statuses
        if len(statuses) == 1:
            return next(iter(statuses))
        else:
            if Status.FAILED in statuses:
                return Status.FAILED
            elif Status.RUNNING in statuses:
                return Status.RUNNING
            elif Status.SUBMITTED in statuses:
                return Status.SUBMITTED
            elif Status.QUEUING in statuses:
                return Status.QUEUING
            elif Status.READY in statuses:
                return Status.READY
            elif Status.WAITING in statuses:
                return Status.WAITING
            elif Status.SUSPENDED in statuses:
                return Status.SUSPENDED
            elif Status.UNKNOWN in statuses:
                return Status.UNKNOWN