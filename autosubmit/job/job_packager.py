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
from autosubmit.job.job_packages import JobPackageSimple, JobPackageHybrid, JobPackageVertical, JobPackageHorizontal, \
    JobPackageSimpleWrapped
from operator import attrgetter

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
        remote_dependencies_dict = dict()

        jobs_ready = self._jobs_list.get_ready(self._platform)
        if jobs_ready == 0:
            return packages_to_submit, remote_dependencies_dict
        if not (self._max_wait_jobs_to_submit > 0 and self._max_jobs_to_submit > 0):
            return packages_to_submit, remote_dependencies_dict

        available_sorted = sorted(jobs_ready, key=lambda k: k.long_name.split('_')[1][:6])
        list_of_available = sorted(available_sorted, key=lambda k: k.priority, reverse=True)
        num_jobs_to_submit = min(self._max_wait_jobs_to_submit, len(jobs_ready), self._max_jobs_to_submit)
        jobs_to_submit = list_of_available[0:num_jobs_to_submit]

        jobs_in_wrapper = self._as_config.get_wrapper_jobs()

        jobs_to_submit_by_section = JobPackager._divide_list_by_section(jobs_to_submit, jobs_in_wrapper)

        wrapper_type = self._as_config.get_wrapper_type()
        crossdate = self._as_config.get_wrapper_crossdate()
        remote_dependencies = self._as_config.get_remote_dependencies()
        max_jobs = min(self._max_wait_jobs_to_submit, self._max_jobs_to_submit)

        for section in jobs_to_submit_by_section:
            if self._platform.allow_wrappers and wrapper_type in ['horizontal', 'vertical', 'vertical-mixed', 'hybrid'] and \
                    (jobs_in_wrapper == 'None' or section in jobs_in_wrapper):

                max_wrapped_jobs = int(self._as_config.jobs_parser.get_option(section, "MAX_WRAPPED", self._as_config.get_max_wrapped_jobs()))

                if wrapper_type in ['vertical', 'vertical-mixed']:
                    built_packages, max_jobs, remote_dependencies_dict = JobPackager._build_vertical_packages(
                                                                        self._jobs_list.get_ordered_jobs_by_date_member(),
                                                                        jobs_to_submit_by_section[section],
                                                                        max_jobs, self._platform.max_wallclock,
                                                                        max_wrapped_jobs, wrapper_type,
                                                                        remote_dependencies)
                    packages_to_submit += built_packages
                elif wrapper_type == 'horizontal':
                    built_packages, max_jobs, remote_dependencies_dict = JobPackager._build_horizontal_packages(jobs_to_submit_by_section[section],
                                                                                    max_jobs, self._platform.max_processors,
                                                                                    max_wrapped_jobs, section, remote_dependencies)
                    packages_to_submit += built_packages

                elif wrapper_type == 'hybrid':
                    built_packages, max_jobs = JobPackager._build_hybrid_package(jobs_to_submit_by_section[section],
                                                        max_jobs, self._platform.max_wallclock,
                                                        max_wrapped_jobs, self._platform.max_processors, section, crossdate)

                    packages_to_submit.append(built_packages)
            else:
                # No wrapper allowed / well-configured
                for job in jobs_to_submit_by_section[section]:
                    if job.type == Type.PYTHON and not self._platform.allow_python_jobs:
                        package = JobPackageSimpleWrapped([job])
                    else:
                        package = JobPackageSimple([job])
                    packages_to_submit.append(package)

        return packages_to_submit, remote_dependencies_dict

    @staticmethod
    def _divide_list_by_section(jobs_list, jobs_in_wrapper):
        """
        Returns a dict() with as many keys as 'jobs_list' different sections
        The value for each key is a list() with all the jobs with the key section.

        :param jobs_list: list of jobs to be divided
        :rtype: dict
        """
        sections_split = jobs_in_wrapper.split()

        jobs_section = dict()
        for job in jobs_list:
            section = next((s for s in sections_split if job.section in s and '&' in s), None)
            if section is None:
                section = job.section
            if section not in jobs_section:
                jobs_section[section] = list()
            jobs_section[section].append(job)
        return jobs_section

    @staticmethod
    def _build_horizontal_packages(section_list, max_jobs, max_processors, max_wrapped_jobs, section, remote_dependencies=False):
        packages = []
        remote_dependencies_dict = dict()

        horizontal_packager = JobPackagerHorizontal(section_list, max_processors, max_wrapped_jobs, max_jobs)

        package_jobs = horizontal_packager.build_horizontal_package()
        current_package = None
        if package_jobs:
            current_package = JobPackageHorizontal(package_jobs)
            packages.append(current_package)

        if remote_dependencies and current_package:
            remote_dependencies_dict['name_to_id'] = dict()
            remote_dependencies_dict['dependencies'] = dict()
            packages += horizontal_packager.get_next_packages(section, potential_dependency=current_package.name, remote_dependencies_dict=remote_dependencies_dict)

        return packages, max_jobs, remote_dependencies_dict

    @staticmethod
    def _build_vertical_packages(dict_jobs, section_list, max_jobs, max_wallclock, max_wrapped_jobs, type,
                                 remote_dependencies=False):
        packages = []
        potential_dependency = None
        remote_dependencies_dict = dict()
        if remote_dependencies:
            remote_dependencies_dict['name_to_id'] = dict()
            remote_dependencies_dict['dependencies'] = dict()

        for job in section_list:
            if max_jobs > 0:
                if job.packed == False:
                    job.packed = True

                    if type == 'vertical-mixed':
                        job_vertical_packager = JobPackagerVerticalMixed(dict_jobs, job, [job], job.wallclock, max_jobs,
                                                                                       max_wrapped_jobs, max_wallclock)
                    else:
                        job_vertical_packager = JobPackagerVerticalSimple([job], job.wallclock, max_jobs,
                                                                            max_wrapped_jobs, max_wallclock)

                    jobs_list = job_vertical_packager.build_vertical_package(job)
                    max_jobs -= len(jobs_list)
                    if job.status is Status.READY:
                        packages.append(JobPackageVertical(jobs_list))
                    else:
                        package = JobPackageVertical(jobs_list, potential_dependency)
                        packages.append(package)
                        remote_dependencies_dict['name_to_id'][potential_dependency] = -1
                        remote_dependencies_dict['dependencies'][package.name] = potential_dependency
                    if remote_dependencies:
                        child = job_vertical_packager.get_wrappable_child(jobs_list[-1])
                        if child is not None:
                            section_list.insert(section_list.index(job) + 1, child)
                            potential_dependency = packages[-1].name
            else:
                break
        return packages, max_jobs, remote_dependencies_dict

    @staticmethod
    def _build_hybrid_package(jobs_list, max_jobs, max_wallclock, max_wrapped_jobs, max_processors, section, crossdate, processors_per_node):
        package = []

        current_package = []
        total_wallclock = '00:00'
        total_processors = 0

        ## READY JOBS ##
        ## Create the horizontal ##
        horizontal_packager = JobPackagerHorizontal(jobs_list, max_processors, max_wrapped_jobs, max_jobs)
        horizontal_package = horizontal_packager.build_horizontal_package()

        if horizontal_package:
            if crossdate:
                ## Get the next horizontal packages ##
                current_package = [horizontal_package]
                for job in horizontal_package:
                    if job.tasks in ['0', '1']:
                        total_processors += job.total_processors
                    else:
                        if int(job.tasks) < job.total_processors:
                            nodes = job.total_processors/int(job.tasks)
                        total_processors += 48*nodes

                job = max(horizontal_package, key=attrgetter('total_wallclock'))
                wallclock = job.wallclock

                current_package += horizontal_packager.get_next_packages(section, max_wallclock=max_wallclock)

                for i in range(len(current_package)):
                    total_wallclock = sum_str_hours(total_wallclock, wallclock)

            else:
                ## Create the vertical ##
                for job in horizontal_package:
                    job_list = JobPackagerVerticalSimple([job], job.wallclock, max_jobs,
                                                         max_wrapped_jobs, max_wallclock).build_vertical_package(job)
                    current_package.append(job_list)

                for job_list in current_package:
                    for job in job_list:
                        total_wallclock = sum_str_hours(total_wallclock, job.wallclock)
                        total_processors = job.total_processors
                    total_processors = total_processors*len(current_package)
                    break

            package = JobPackageHybrid(current_package, total_processors, total_wallclock, crossdate=crossdate)

        return package, max_jobs

class JobPackagerVertical(object):

    def __init__(self, jobs_list, total_wallclock, max_jobs, max_wrapped_jobs, max_wallclock):
        self.jobs_list = jobs_list
        self.total_wallclock = total_wallclock
        self.max_jobs = max_jobs
        self.max_wrapped_jobs = max_wrapped_jobs
        self.max_wallclock = max_wallclock

    def build_vertical_package(self, job):
        if len(self.jobs_list) >= self.max_jobs or len(self.jobs_list) >= self.max_wrapped_jobs:
            return self.jobs_list
        child = self.get_wrappable_child(job)
        if child is not None:
            self.total_wallclock = sum_str_hours(self.total_wallclock, child.wallclock)
            if self.total_wallclock <= self.max_wallclock:
                child.packed = True
                self.jobs_list.append(child)
                return self.build_vertical_package(child)
        return self.jobs_list

    def get_wrappable_child(self, job):
        pass

    def _is_wrappable(self, job):
        pass

class JobPackagerVerticalSimple(JobPackagerVertical):

    def __init__(self, jobs_list, total_wallclock, max_jobs, max_wrapped_jobs, max_wallclock):
        super(JobPackagerVerticalSimple, self).__init__(jobs_list, total_wallclock, max_jobs, max_wrapped_jobs, max_wallclock)

    def get_wrappable_child(self, job):
        for child in job.children:
            if self._is_wrappable(child, job):
                return child
            continue
        return None

    def _is_wrappable(self, job, parent=None):
        if job.section != parent.section:
            return False
        for other_parent in job.parents:
            if other_parent.status != Status.COMPLETED and other_parent not in self.jobs_list:
                return False
        return True

class JobPackagerVerticalMixed(JobPackagerVertical):

    def __init__(self, dict_jobs, ready_job, jobs_list, total_wallclock, max_jobs, max_wrapped_jobs, max_wallclock):
        super(JobPackagerVerticalMixed, self).__init__(jobs_list, total_wallclock, max_jobs, max_wrapped_jobs, max_wallclock)
        self.ready_job = ready_job
        self.dict_jobs = dict_jobs

        date = dict_jobs.keys()[-1]
        member = dict_jobs[date].keys()[-1]
        if ready_job.date is not None:
            date = ready_job.date
        if ready_job.member is not None:
            member = ready_job.member

        self.sorted_jobs = dict_jobs[date][member]
        self.index = 0

    def get_wrappable_child(self, job):
        sorted_jobs = self.sorted_jobs

        for index in range(self.index, len(sorted_jobs)):
            child = sorted_jobs[index]
            if self._is_wrappable(child):
                self.index = index+1
                return child
            continue
        return None

    def _is_wrappable(self, job):
        if job.packed == False and (job.status == Status.READY or job.status == Status.WAITING):
            for parent in job.parents:
                if parent not in self.jobs_list and parent.status != Status.COMPLETED:
                    return False
            return True
        return False

class JobPackagerHorizontal(object):
    def __init__(self, job_list, max_processors, max_wrapped_jobs, max_jobs):
        self.max_processors = max_processors
        self.max_wrapped_jobs = max_wrapped_jobs
        self.job_list = job_list
        self.max_jobs = max_jobs

    def build_horizontal_package(self):
        current_package = []
        current_processors = 0
        for job in self.job_list:
            if self.max_jobs > 0 and len(current_package) < self.max_wrapped_jobs:
                self.max_jobs -= 1
                if (current_processors + job.total_processors) <= int(self.max_processors):
                    current_package.append(job)
                    current_processors += job.total_processors
                else:
                    current_package = [job]
                    current_processors = job.total_processors
            else:
                break
        return current_package

    def get_next_packages(self, jobs_sections, max_wallclock=None, potential_dependency=None, remote_dependencies_dict=dict()):
        packages = []
        job = max(self.job_list, key=attrgetter('total_wallclock'))
        wallclock = job.wallclock
        total_wallclock = wallclock

        while self.max_jobs > 0:
            next_section_list = []
            for job in self.job_list:
                for child in job.children:
                    if job.section == child.section or (job.section in jobs_sections and child.section in jobs_sections) \
                            and child.status in [Status.READY, Status.WAITING]:
                        wrappable = True
                        for other_parent in child.parents:
                            if other_parent.status != Status.COMPLETED and other_parent not in self.job_list:
                                wrappable = False
                        if wrappable and child not in next_section_list:
                            next_section_list.append(child)

            self.job_list = next_section_list
            package_jobs = self.build_horizontal_package()

            if package_jobs:
                if max_wallclock:
                    total_wallclock = sum_str_hours(total_wallclock, wallclock)
                    if total_wallclock > max_wallclock:
                        return packages
                packages.append(package_jobs)
                if remote_dependencies_dict:
                    current_package = JobPackageHorizontal(package_jobs, potential_dependency)
                    remote_dependencies_dict['name_to_id'][potential_dependency] = -1
                    remote_dependencies_dict['dependencies'][current_package.name] = potential_dependency
            else:
                break

        return packages