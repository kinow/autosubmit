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

import os
import time
import random
from autosubmit.job.job_common import Status
from autosubmit.config.log import Log
from autosubmit.job.job_exceptions import WrongTemplateException
from autosubmit.job.job import Job
from autosubmit.date.chunk_date_lib import sum_str_hours


class JobPackageBase(object):
    """
    Class to manage the package of jobs to be submitted by autosubmit
    """

    def __init__(self, jobs):
        self._jobs = jobs
        try:
            self._tmp_path = jobs[0]._tmp_path
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
            if job.check.lower() == Job.CHECK_ON_SUBMISSION:
                if not job.check_script(configuration, parameters):
                    raise WrongTemplateException(job.name)
            job.update_parameters(configuration, parameters)
        self._create_scripts(configuration)
        self._send_files()
        self._do_submission()

    def _create_scripts(self, configuration):
        raise Exception('Not implemented')

    def _send_files(self):
        raise Exception('Not implemented')

    def _do_submission(self):
        raise Exception('Not implemented')


class JobPackageSimple(JobPackageBase):
    """
    Class to manage the package of jobs to be submitted by autosubmit
    """

    def __init__(self, jobs):
        self._job_scripts = {}
        super(JobPackageSimple, self).__init__(jobs)

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


class JobPackageArray(JobPackageBase):
    """
    Class to manage the package of jobs to be submitted by autosubmit
    """

    def __init__(self, jobs):
        self._job_inputs = {}
        self._job_scripts = {}
        self._common_script = None
        self._array_size_id = "[1-" + str(len(jobs)) + "]"
        self._wallclock = '00:00'
        self._num_processors = '1'
        for job in jobs:
            if job.wallclock > self._wallclock:
                self._wallclock = job.wallclock
            if job.processors > self._num_processors:
                self._num_processors = job.processors
        super(JobPackageArray, self).__init__(jobs)

    def _create_scripts(self, configuration):
        timestamp = str(int(time.time()))
        for i in range(1, len(self.jobs) + 1):
            self._job_scripts[self.jobs[i - 1].name] = self.jobs[i - 1].create_script(configuration)
            self._job_inputs[self.jobs[i - 1].name] = self._create_i_input(timestamp, i)
            self.jobs[i - 1].remote_logs = (timestamp + ".{0}.out".format(i), timestamp + ".{0}.err".format(i))
        self._common_script = self._create_common_script(timestamp)

    def _create_i_input(self, filename, index):
        filename += '.{0}'.format(index)
        input_content = self._job_scripts[self.jobs[index - 1].name]
        open(os.path.join(self._tmp_path, filename), 'w').write(input_content)
        os.chmod(os.path.join(self._tmp_path, filename), 0o775)
        return filename

    def _create_common_script(self, filename):
        script_content = self.platform.header.array_header(filename, self._array_size_id, self._wallclock,
                                                           self._num_processors)
        filename += '.cmd'
        open(os.path.join(self._tmp_path, filename), 'w').write(script_content)
        os.chmod(os.path.join(self._tmp_path, filename), 0o775)
        return filename

    def _send_files(self):
        for job in self.jobs:
            self.platform.send_file(self._job_scripts[job.name])
            self.platform.send_file(self._job_inputs[job.name])
        self.platform.send_file(self._common_script)

    def _do_submission(self):
        for job in self.jobs:
            self.platform.remove_stat_file(job.name)
            self.platform.remove_completed_file(job.name)

        package_id = self.platform.submit_job(None, self._common_script)

        if package_id is None:
            raise Exception('Submission failed')

        for i in range(1, len(self.jobs) + 1):
            Log.info("{0} submitted", self.jobs[i - 1].name)
            self.jobs[i - 1].id = str(package_id) + '[{0}]'.format(i)
            self.jobs[i - 1].status = Status.SUBMITTED
            self.jobs[i - 1].write_submit_time()


class JobPackageThread(JobPackageBase):
    """
    Class to manage the package of jobs to be submitted by autosubmit
    """
    FILE_PREFIX = 'ASThread'

    def __init__(self, jobs, dependency=None):
        super(JobPackageThread, self).__init__(jobs)
        self._job_scripts = {}
        self._job_dependency = dependency
        self._common_script = None
        self._wallclock = '00:00'
        self._num_processors = '0'
        for job in jobs:
            if job.processors > self._num_processors:
                self._num_processors = job.processors
            self._wallclock = sum_str_hours(self._wallclock, job.wallclock)
        self._name = self.FILE_PREFIX + "_{0}_{1}_{2}".format(str(int(time.time())) + str(random.randint(1, 10000)),
                                                              self._num_processors,
                                                              len(self._jobs))

    def _create_scripts(self, configuration):
        for i in range(1, len(self.jobs) + 1):
            self._job_scripts[self.jobs[i - 1].name] = self.jobs[i - 1].create_script(configuration)
            self.jobs[i - 1].remote_logs = (
                self._job_scripts[self.jobs[i - 1].name] + ".{0}.out".format(i - 1),
                self._job_scripts[self.jobs[i - 1].name] + ".{0}.err".format(i - 1)
            )
        self._common_script = self._create_common_script()

    def _create_common_script(self):
        script_content = self.platform.header.thread_header(self._name, self._wallclock,
                                                            self._num_processors, self.jobs_scripts,
                                                            self._dependency_directive())
        script_file = self.name + '.cmd'
        open(os.path.join(self._tmp_path, script_file), 'w').write(script_content)
        os.chmod(os.path.join(self._tmp_path, script_file), 0o775)
        return script_file

    def _send_files(self):
        for job in self.jobs:
            self.platform.send_file(self._job_scripts[job.name])
        self.platform.send_file(self._common_script)

    def _do_submission(self):
        for job in self.jobs:
            self.platform.remove_stat_file(job.name)
            self.platform.remove_completed_file(job.name)

        package_id = self.platform.submit_job(None, self._common_script)

        if package_id is None:
            raise Exception('Submission failed')

        for i in range(1, len(self.jobs) + 1):
            Log.info("{0} submitted", self.jobs[i - 1].name)
            self.jobs[i - 1].id = str(package_id)
            self.jobs[i - 1].status = Status.SUBMITTED
            self.jobs[i - 1].write_submit_time()

    def _dependency_directive(self):
        return '#' if self._job_dependency is None else '#BSUB -w \'done("{0}")\' [-ti]'.format(self._job_dependency)

    @property
    def name(self):
        return self._name

    @property
    def jobs_scripts(self):
        jobs_scripts = []
        for job in self.jobs:
            jobs_scripts.append(self._job_scripts[job.name])
        return jobs_scripts
