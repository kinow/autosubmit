from unittest import TestCase

import os
from mock import Mock,MagicMock, mock_open , call
from mock import patch

from autosubmit.job.job_packages import JobPackageSimple
from autosubmit.job.job import Job
from autosubmit.job.job_common import Status


class TestJobPackage(TestCase):

    def setUp(self):
        self.platform = MagicMock()
        self.jobs = [Job('dummy1', 0, Status.READY, 0),
                     Job('dummy2', 0, Status.READY, 0)]
        self.jobs[0]._platform = self.jobs[1]._platform = self.platform
        self.job_package = JobPackageSimple(self.jobs)

    def test_job_package_default_init(self):
        with self.assertRaises(Exception):
            JobPackageSimple([])

    def test_job_package_different_platforms_init(self):
        self.jobs[0]._platform = MagicMock()
        self.jobs[1]._platform = MagicMock()
        with self.assertRaises(Exception):
            JobPackageSimple(self.jobs)

    def test_job_package_none_platforms_init(self):
        self.jobs[0]._platform = None
        self.jobs[1]._platform = None
        with self.assertRaises(Exception):
            JobPackageSimple(self.jobs)

    def test_job_package_length(self):
        self.assertEqual(2, len(self.job_package))

    def test_job_package_jobs_getter(self):
        self.assertEqual(self.jobs, self.job_package.jobs)

    def test_job_package_platform_getter(self):
        self.assertEqual(self.platform, self.job_package.platform)

    @patch("builtins.open",MagicMock())
    def test_job_package_submission(self):
        # arrange
        MagicMock().write = MagicMock()

        for job in self.jobs:
            job._tmp_path = MagicMock()
            job._get_paramiko_template = MagicMock("false","empty")

        self.job_package._create_scripts = MagicMock()
        self.job_package._send_files = MagicMock()
        self.job_package._do_submission = MagicMock()
        for job in self.jobs:
            job.update_parameters = MagicMock()
        # act
        self.job_package.submit('fake-config', 'fake-params')
        # assert
        for job in self.jobs:
            job.update_parameters.assert_called_once_with('fake-config', 'fake-params')
        self.job_package._create_scripts.is_called_once_with()
        self.job_package._send_files.is_called_once_with()
        self.job_package._do_submission.is_called_once_with()
