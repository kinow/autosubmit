from unittest import TestCase

import os
from mock import Mock
from mock import patch

from autosubmit.job.job_packages import JobPackageSimple
from autosubmit.job.job import Job
from autosubmit.job.job_common import Status


class TestJobPackage(TestCase):

    def setUp(self):
        self.platform = Mock()
        self.jobs = [Job('dummy1', 0, Status.READY, 0),
                     Job('dummy2', 0, Status.READY, 0)]
        self.jobs[0].platform = self.jobs[1].platform = self.platform
        self.job_package = JobPackageSimple(self.jobs)

    def test_job_package_default_init(self):
        with self.assertRaises(Exception):
            JobPackageSimple([])

    def test_job_package_different_platforms_init(self):
        self.jobs[0].platform = Mock()
        self.jobs[1].platform = Mock()
        with self.assertRaises(Exception):
            JobPackageSimple(this.jobs)

    def test_job_package_none_platforms_init(self):
        self.jobs[0].platform = None
        self.jobs[1].platform = None
        with self.assertRaises(Exception):
            JobPackageSimple(this.jobs)

    def test_job_package_length(self):
        self.assertEquals(2, len(self.job_package))

    def test_job_package_jobs_getter(self):
        self.assertEquals(self.jobs, self.job_package.jobs)

    def test_job_package_platform_getter(self):
        self.assertEquals(self.platform.serial_platform, self.job_package.platform)

    def test_job_package_submission(self):
        # arrange
        self.job_package._create_scripts = Mock()
        self.job_package._send_files = Mock()
        self.job_package._do_submission = Mock()
        for job in self.jobs:
            job.update_parameters = Mock()
        # act
        self.job_package.submit('fake-config', 'fake-params')
        # assert
        for job in self.jobs:
            job.update_parameters.assert_called_once_with('fake-config', 'fake-params')
        self.job_package._create_scripts.is_called_once_with()
        self.job_package._send_files.is_called_once_with()
        self.job_package._do_submission.is_called_once_with()
