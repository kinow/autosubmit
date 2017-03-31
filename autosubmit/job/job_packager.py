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

from bscearth.utils.log import Log
from autosubmit.job.job_common import Status, Type
from bscearth.utils.date import date2str, parse_date, sum_str_hours
from autosubmit.job.job_packages import JobPackageSimple, JobPackageArray, JobPackageVertical, JobPackageHorizontal, \
    JobPackageSimpleWrapped


class JobPackager(object):
    """
    The main responsibility of this class is to manage the packages of jobs that have to be submitted.
    """

    def __init__(self, as_config, platform, jobs_list):
        self._as_config = as_config
        self._platform = platform
        self._jobs_list = jobs_list

        waiting_jobs = len(jobs_list.get_submitted(platform) + jobs_list.get_queuing(platform))
        self._max_wait_jobs_to_submit = platform.max_waiting_jobs - waiting_jobs
        self._max_jobs_to_submit = platform.total_jobs - len(jobs_list.get_in_queue(platform))

        Log.debug("Number of jobs ready: {0}", len(jobs_list.get_ready(platform)))
        Log.debug("Number of jobs available: {0}", self._max_wait_jobs_to_submit)
        if len(jobs_list.get_ready(platform)) > 0:
            Log.info("Jobs ready for {0}: {1}", self._platform.name, len(jobs_list.get_ready(platform)))

    def build_packages(self):
        """
        Returns the list of the built packages to be submitted

        :return: list of packages
        :rtype list
        """
        packages_to_submit = list()
        jobs_ready = self._jobs_list.get_ready(self._platform)
        if jobs_ready == 0:
            return packages_to_submit
        if not (self._max_wait_jobs_to_submit > 0 and self._max_jobs_to_submit > 0):
            return packages_to_submit

        available_sorted = sorted(jobs_ready, key=lambda k: k.long_name.split('_')[1][:6])
        list_of_available = sorted(available_sorted, key=lambda k: k.priority, reverse=True)
        num_jobs_to_submit = min(self._max_wait_jobs_to_submit, len(jobs_ready), self._max_jobs_to_submit)
        jobs_to_submit = list_of_available[0:num_jobs_to_submit]
        jobs_to_submit_by_section = JobPackager._divide_list_by_section(jobs_to_submit)

        # If wrapper allowed / well-configured
        wrapper_type = self._as_config.get_wrapper_type()
        if self._platform.allow_wrappers and wrapper_type in ['horizontal', 'vertical']:
            remote_dependencies = self._as_config.get_remote_dependencies()
            max_jobs = min(self._max_wait_jobs_to_submit, self._max_jobs_to_submit)
            if wrapper_type == 'vertical':
                for section_list in jobs_to_submit_by_section.values():
                    built_packages, max_jobs = JobPackager._build_vertical_packages(section_list,
                                                                                    max_jobs,
                                                                                    self._platform.max_wallclock,
                                                                                    remote_dependencies)
                    packages_to_submit += built_packages
                return packages_to_submit
            elif wrapper_type == 'horizontal':
                for section_list in jobs_to_submit_by_section.values():
                    built_packages, max_jobs = JobPackager._build_horizontal_packages(section_list,
                                                                                      max_jobs,
                                                                                      self._platform.max_processors,
                                                                                      remote_dependencies)
                    packages_to_submit += built_packages
                return packages_to_submit
        # No wrapper allowed / well-configured
        for job in jobs_to_submit:
            if job.type == Type.PYTHON and not self._platform.allow_python_jobs:
                package = JobPackageSimpleWrapped([job])
            else:
                package = JobPackageSimple([job])
            packages_to_submit.append(package)
        return packages_to_submit

    @staticmethod
    def _divide_list_by_section(jobs_list):
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

    @staticmethod
    def _build_horizontal_packages(section_list, max_jobs, max_processors, remote_dependencies=False):
        # TODO: Implement remote dependencies for horizontal wrapper
        packages = []
        current_package = []
        current_processors = 0
        for job in section_list:
            if max_jobs > 0:
                max_jobs -= 1
                if (current_processors + job.total_processors) <= int(max_processors):
                    current_package.append(job)
                    current_processors += job.total_processors
                else:
                    packages.append(JobPackageHorizontal(current_package))
                    current_package = [job]
                    current_processors = job.total_processors
            else:
                break
        if len(current_package) > 0:
            packages.append(JobPackageHorizontal(current_package))
        return packages, max_jobs

    @staticmethod
    def _build_vertical_packages(section_list, max_jobs, max_wallclock, remote_dependencies=False):
        packages = []
        potential_dependency = None
        for job in section_list:
            if max_jobs > 0:
                jobs_list = JobPackager._build_vertical_package(job, [job], job.wallclock, max_jobs, max_wallclock)
                max_jobs -= len(jobs_list)
                if job.status is Status.READY:
                    packages.append(JobPackageVertical(jobs_list))
                else:
                    packages.append(JobPackageVertical(jobs_list, potential_dependency))
                if remote_dependencies:
                    child = JobPackager._get_wrappable_child(jobs_list[-1], JobPackager._is_wrappable)
                    if child is not None:
                        section_list.insert(section_list.index(job) + 1, child)
                        potential_dependency = packages[-1].name
            else:
                break
        return packages, max_jobs

    @staticmethod
    def _build_vertical_package(job, jobs_list, total_wallclock, max_jobs, max_wallclock):
        if len(jobs_list) >= max_jobs:
            return jobs_list
        child = JobPackager._get_wrappable_child(job, JobPackager._is_wrappable)
        if child is not None:
            total_wallclock = sum_str_hours(total_wallclock, child.wallclock)
            if total_wallclock <= max_wallclock:
                jobs_list.append(child)
                return JobPackager._build_vertical_package(child, jobs_list, total_wallclock, max_jobs, max_wallclock)
        return jobs_list

    @staticmethod
    def _get_wrappable_child(job, check_function):
        for child in job.children:
            if check_function(job, child):
                return child
            continue
        return None

    @staticmethod
    def _is_wrappable(parent, child):
        if child.section != parent.section:
            return False
        if len(child.parents) > 1:
            return False
        return True
