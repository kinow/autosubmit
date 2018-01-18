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

class JobGrouping(object):

    def __init__(self, group_by, jobs, job_list, expand_list=list(), expanded_status=list()):
        self.group_by = group_by
        self.jobs = jobs
        self.job_list = job_list
        self.date_format = job_list.get_date_format()
        self.expand_list = expand_list
        self.expand_status = expanded_status
        self.automatic = False
        self.group_status_dict = dict()
        self.ungrouped_jobs = list()

    def group_jobs(self):
        if self.expand_list:
            self._set_ungrouped_jobs()
            self.jobs = list(set(self.jobs) - set(self.ungrouped_jobs))

        jobs_group_dict = dict()
        blacklist = list()

        groups_map = dict()
        if self.group_by == 'automatic':
            self.automatic = True
            jobs_group_dict = self._automatic_grouping(groups_map)
        else:
            self._group_jobs_by(jobs_group_dict, blacklist)

            for group, statuses in self.group_status_dict.items():
                status = self._set_group_status(statuses)
                self.group_status_dict[group] = status

        final_jobs_group = dict()
        for job, groups in jobs_group_dict.items():
            for group in groups:
                if group not in blacklist:
                    while group in groups_map:
                        group = groups_map[group]
                    # to remove the jobs belonging to groups that should be expanded
                    if group in self.group_status_dict:
                        if job not in final_jobs_group:
                            final_jobs_group[job] = list()
                        final_jobs_group[job].append(group)

        jobs_group_dict = final_jobs_group

        groups_dict = dict()
        groups_dict['jobs'] = jobs_group_dict
        groups_dict['status'] = self.group_status_dict

        return groups_dict

    def _set_ungrouped_jobs(self):
        text = self.expand_list

        from pyparsing import nestedExpr
        """
        Function to parse rerun specification from json format

        :param text: text to parse
        :type text: list
        :return: parsed output
        """
        count = 0

        out = nestedExpr('[', ']').parseString(text).asList()

        depth = lambda L: isinstance(L, list) and max(map(depth, L)) + 1

        if self.group_by == 'date':
            if depth(out) == 2:
                dates = list()
                for date in out[0]:
                    dates.append(date)
                self.ungrouped_jobs = [job for job in self.jobs if date2str(job.date, self.date_format) in dates]
            else:
                raise ValueError("Please check the syntax of the expand parameter including only dates")
        elif self.group_by == 'member':
            if depth(out) == 3:
                for element in out[0]:
                    if count % 2 == 0:
                        date = out[0][count]
                        members = out[0][count + 1]
                        self.ungrouped_jobs = self.ungrouped_jobs + [job for job in self.jobs if date2str(job.date, self.date_format) == date and job.member in members]
                        count += 1
                    else:
                        count += 1
            else:
                raise ValueError("Please check the syntax of the expand parameter including dates and the corresponding members")
        elif self.group_by == 'chunk':
            if depth(out) == 4:
                for element in out[0]:
                    if count % 2 == 0:
                        date = out[0][count]
                        member_chunks = out[0][count + 1]
                        member_count = 0
                        for element_member in member_chunks:
                            if member_count % 2 == 0:
                                member = member_chunks[member_count]
                                chunks = list()
                                for chunk in member_chunks[member_count + 1]:
                                    if chunk.find("-") != -1:
                                        numbers = chunk.split("-")
                                        for count in range(int(numbers[0]), int(numbers[1]) + 1):
                                            chunks.append(count)
                                    else:
                                        chunks.append(int(chunk))

                                self.ungrouped_jobs = self.ungrouped_jobs + \
                                                      [job for job in self.jobs if date2str(job.date, self.date_format) == date
                                                       and job.member == member and job.chunk in chunks]
                            member_count += 1
                    count += 1
            else:
                raise ValueError("Please check the syntax of the expand parameter including dates and the corresponding members and chunks")

    def _set_group_status(self, statuses):
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

    def _group_jobs_by(self, jobs_group_dict, blacklist):
        for date in reversed(self.job_list.get_date_list()):
            if self.group_by == 'date' or not self.job_list.get_member_list():
                self._create_group(jobs_group_dict, date, blacklist=blacklist)
            elif self.group_by in ['member', 'chunk', 'split']:
                for member in reversed(self.job_list.get_member_list()):
                    if self.group_by == 'member' or not self.job_list.get_chunk_list():
                        self._create_group(jobs_group_dict, date, member, blacklist=blacklist)
                    else:
                        for chunk in reversed(self.job_list.get_chunk_list()):
                            self._create_group(jobs_group_dict, date, member, chunk, blacklist=blacklist)

    def _create_group(self, jobs_group_dict, date=None, member=None, chunk=None, blacklist=list()):
        if chunk is not None:
            name = date2str(date, self.date_format) + '_' + member + '_' +str(chunk)
        elif member is not None:
            name = date2str(date, self.date_format) + '_' + member
        else:
            name = date2str(date, self.date_format)

        for i in reversed(range(len(self.jobs))):
            job = self.jobs[i]

            if self.group_by == 'date':
                condition = (job.date == date or (job.date is None and job.chunk is not None))
            elif self.group_by == 'member':
                condition = (job.date == date and job.member == member) or \
                            (job.date in [date, None] and job.member is None and job.chunk is not None)
            elif self.group_by  == 'chunk':
                condition = (job.member in [member, None] and job.date in [date, None] and job.chunk == chunk)
            elif self.group_by == 'split':
                idx = job.name.rfind("_")
                name = job.name[:idx - 1] + job.name[idx + 1:]
                condition = job.split is not None

            condition = condition and name not in blacklist# and job not in self.ungrouped_jobs

            if (condition):
                if ((job.chunk is None) or (job.member is not None and job.date is not None and job.chunk is not None)):
                    self.jobs.pop(i) #if synchronized does not remove; neither if automatic and grouping the splits only
                if name not in self.group_status_dict:
                    self.group_status_dict[name] = set()
                self.group_status_dict[name].add(job.status)

                if job.status in self.expand_status or \
                        (self.automatic and name in self.group_status_dict and (len(self.group_status_dict[name]) > 1)):
                    self.group_status_dict.pop(name)
                    blacklist.append(name)
                    break

                if job.name not in jobs_group_dict:
                    jobs_group_dict[job.name] = list()
                jobs_group_dict[job.name].append(name)

    def _automatic_grouping(self, groups_map):
        all_jobs = self.jobs
        split_groups, split_groups_status = self._create_splits_groups()

        blacklist = list()
        jobs_group_dict = dict()
        self.group_status_dict = dict()
        self.group_by = 'chunk'
        self.jobs = all_jobs

        self._group_jobs_by(jobs_group_dict, blacklist)

        for group, statuses in self.group_status_dict.items():
            status = self._set_group_status(statuses)
            self.group_status_dict[group] = status

        self._create_higher_level_group(self.group_status_dict.keys(), groups_map)
        self._fix_splits_automatic_grouping(split_groups, split_groups_status, jobs_group_dict)

        # check if remaining jobs can be grouped
        for i in reversed(range(len(self.jobs))):
            job = self.jobs[i]
            for group, status in self.group_status_dict.items():
                if group in job.name and status == job.status:
                    jobs_group_dict[job.name] = [group]
                    self.jobs.pop(i)
    
        return jobs_group_dict

    def _create_splits_groups(self):
        jobs_group_dict = dict()

        self.group_by = 'split'
        self._group_jobs_by(jobs_group_dict, list())
        return jobs_group_dict, self.group_status_dict

    def _fix_splits_automatic_grouping(self, split_groups, split_groups_status, jobs_group_dict):
        if split_groups and split_groups_status:
            group_maps = dict()
            for group in self.group_status_dict.keys():
                matching_groups = [split_group for split_group in split_groups_status.keys() if group in split_group]
                for matching_group in matching_groups:
                    group_maps[matching_group] = group
                    split_groups_status.pop(matching_group)

            for split_group, statuses in split_groups_status.items():
                status = self._set_group_status(statuses)
                self.group_status_dict[split_group] = status

            for job, groups in split_groups.items():
                final_groups = list()
                for group in groups:
                    if group in group_maps:
                        group = group_maps[group]
                    final_groups.append(group)
                if final_groups:
                    jobs_group_dict[job] = final_groups

    def _check_valid_group(self, groups_list, name, groups_map):
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

    def _create_higher_level_group(self, groups_to_check, groups_map):
        checked_groups = list()
        for group in groups_to_check:
            if group in self.group_status_dict:
                split_count = len(group.split('_'))
                if split_count > 1:
                    new_group = group[:(group.rfind("_"))]

                    num_groups = len(self.job_list.get_chunk_list()) if split_count == 3 else len(self.job_list.get_member_list())

                    if new_group not in checked_groups:
                        checked_groups.append(new_group)
                        possible_groups = [existing_group for existing_group in list(self.group_status_dict.keys()) if
                                              new_group in existing_group]

                        if len(possible_groups) == num_groups:
                            if self._check_valid_group(possible_groups, new_group, groups_map):
                                groups_to_check.append(new_group)