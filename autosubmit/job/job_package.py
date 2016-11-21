#!/usr/bin/env python

# Copyright 2016 Earth Sciences Department, BSC-CNS

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

from autosubmit.job.job_common import Status
from autosubmit.config.log import Log


class JobPackage(object):
    """
    Class to manage the package of jobs to be submitted by autosubmit

    """

    def __init__(self, jobs):
        self._jobs = jobs
        self._job_scripts = {}
        try:
            self._platform = jobs[0].platform
            for job in jobs:
                if job.platform != self._platform or job.platform is None:
                    raise Exception('Only one valid platform per package')
        except IndexError:
            raise Exception('No jobs given')

    def __len__(self):
        return self._jobs.__len__()

    @property
    def jobs(self):
        """
        Returns the jobs

        :return: jobs
        :rtype: List[Job]
        """
        return self._jobs

    @property
    def platform(self):
        """
        Returns the platform

        :return: platform
        :rtype: Platform
        """
        return self._platform

    def submit(self, configuration, parameters):
        for job in self.jobs:
            job.update_parameters(configuration, parameters)
        self._create_scripts(configuration)
        self._send_files()
        self._do_submission()

    def _create_scripts(self, configuration):
        for job in self.jobs:
            self._job_scripts[job.name] = job.create_script(configuration)

    def _send_files(self):
        for job in self.jobs:
            self.platform.send_file(self._job_scripts[job.name])

    def _do_submission(self):
        for job in self.jobs:
            self.platform.remove_stat_file(job.name)
            self.platform.remove_completed_file(job.name)
            job.id = self.platform.submit_job(job, self._job_scripts[job.name])
            if job.id is None:
                continue
            Log.info("{0} submitted", job.name)
            job.status = Status.SUBMITTED
            job.write_submit_time()
