import subprocess
import sys
from unittest import TestCase

import os
import re
import saga
from mock import Mock
from mock import patch

from autosubmit.job.job_common import Status
from autosubmit.job.job_common import Type
from autosubmit.platforms.platform import Platform


class TestPlatform(TestCase):
    def setUp(self):
        self.experiment_id = 'random-id'
        self.platform = Platform(self.experiment_id, 'test', FakeBasicConfig)

    def test_check_status_returns_completed_if_job_id_not_exists(self):
        # arrange
        self.platform.service = FakeService([])
        # act
        status = self.platform.check_job('any-id')
        # assert
        self.assertEquals(Status.COMPLETED, status)

    def test_check_status_returns_the_right_states(self):
        # arrange
        self.platform.service = FakeService(['any-id'])
        self.platform.service.get_job = Mock(side_effect=[FakeJob('any-name', saga.job.UNKNOWN),
                                                          FakeJob('any-name', saga.job.PENDING),
                                                          FakeJob('any-name', saga.job.FAILED),
                                                          FakeJob('any-name', saga.job.CANCELED),
                                                          FakeJob('any-name', saga.job.DONE),
                                                          FakeJob('any-name', saga.job.RUNNING),
                                                          FakeJob('any-name', saga.job.SUSPENDED)])
        # act
        should_be_unknown = self.platform.check_job('any-id')
        should_be_queuing = self.platform.check_job('any-id')
        should_be_failed = self.platform.check_job('any-id')
        should_be_failed2 = self.platform.check_job('any-id')
        should_be_completed = self.platform.check_job('any-id')
        should_be_running = self.platform.check_job('any-id')
        should_be_suspended = self.platform.check_job('any-id')

        # assert
        self.assertEquals(Status.UNKNOWN, should_be_unknown)
        self.assertEquals(Status.QUEUING, should_be_queuing)
        self.assertEquals(Status.FAILED, should_be_failed)
        self.assertEquals(Status.FAILED, should_be_failed2)
        self.assertEquals(Status.COMPLETED, should_be_completed)
        self.assertEquals(Status.RUNNING, should_be_running)
        self.assertEquals(Status.SUSPENDED, should_be_suspended)

    def test_creates_a_saga_job_correctly(self):
        parameters = {'WALLCLOCK': '',
                      'CURRENT_QUEUE': 'queue',
                      'CURRENT_BUDG': 'project',
                      'NUMPROC': 666,
                      'NUMTASK': 777,
                      'NUMTHREADS': 888,
                      'MEMORY': 999}
        job = FakeJob('any-name', saga.job.RUNNING, Type.BASH, parameters)
        jd = FakeJobDescription()
        sys.modules['saga'].job.Description = Mock(return_value=jd)
        self.platform.add_attribute = Mock()
        self.platform.service = FakeService([])
        self.platform.service.create_job = Mock(return_value='created-job')

        # act
        created_job = self.platform.create_saga_job(job, 'scriptname')

        # assert
        self.assertEquals('LOG_random-id/scriptname', jd.executable)
        self.assertEquals('LOG_random-id', jd.working_directory)
        self.assertIsNotNone(re.match('any-name.[0-9]*.out', jd.output))
        self.assertIsNotNone(re.match('any-name.[0-9]*.err', jd.error))
        self.platform.add_attribute.assert_any_call(jd, 'Name', job.name)
        self.platform.add_attribute.assert_any_call(jd, 'WallTimeLimit', 0)
        self.platform.add_attribute.assert_any_call(jd, 'Queue', parameters["CURRENT_QUEUE"])
        self.platform.add_attribute.assert_any_call(jd, 'Project', parameters["CURRENT_BUDG"])
        self.platform.add_attribute.assert_any_call(jd, 'TotalCPUCount', parameters["NUMPROC"])
        self.platform.add_attribute.assert_any_call(jd, 'ProcessesPerHost', parameters["NUMTASK"])
        self.platform.add_attribute.assert_any_call(jd, 'ThreadsPerProcess', parameters["NUMTHREADS"])
        self.platform.add_attribute.assert_any_call(jd, 'TotalPhysicalMemory', parameters["MEMORY"])
        self.assertEquals('created-job', created_job)

    def test_deleting_file_returns_true_if_not_exists(self):
        self.platform.exists_file = Mock(return_value=False)
        deleted = self.platform.delete_file('filename')
        self.assertTrue(deleted)

    def test_deleting_file_on_ecaccess_platform_makes_the_right_call(self):
        self.platform.type = 'ecaccess'
        sys.modules['subprocess'].check_call = Mock()

        deleted = self.platform.delete_file('file/path')

        self.assertTrue(deleted)
        sys.modules['subprocess'].check_call.assert_called_once_with(
            ['ecaccess-file-delete', '{0}:{1}'.format(self.platform.host, os.path.join(self.platform.get_files_path(),
                                                                                       'file/path'))])

    def test_deleting_file_on_ecaccess_platform_returns_true_on_error(self):
        self.platform.type = 'ecaccess'

        check_call_mock = Mock()
        check_call_mock.side_effect = subprocess.CalledProcessError
        sys.modules['subprocess'].check_call = check_call_mock

        deleted = self.platform.delete_file('file/path')
        self.assertTrue(deleted)

    def test_deleting_file_on_local_platform_makes_the_right_call(self):
        self.platform.type = 'local'
        self.platform.exists_file = Mock(return_value=True)
        out_mock = Mock()
        out_mock.remove = Mock()
        out_mock.close = Mock()
        sys.modules['saga'].filesystem.File = Mock(return_value=out_mock)

        deleted = self.platform.delete_file('file/path')

        self.assertTrue(deleted)
        sys.modules['saga'].filesystem.File.assert_called_once_with(
            "file://{0}".format(os.path.join(self.platform.tmp_path, 'LOG_' + self.platform.expid,
                                                                            'file/path')))
        out_mock.remove.assert_called_once_with()
        out_mock.close.assert_called_once_with()

    def test_deleting_file_on_non_local_platform_makes_the_right_call(self):
        self.platform.exists_file = Mock(return_value=True)
        out_mock = Mock()
        out_mock.remove = Mock()
        out_mock.close = Mock()
        sys.modules['saga'].filesystem.File = Mock(return_value=out_mock)

        deleted = self.platform.delete_file('file/path')

        self.assertTrue(deleted)
        sys.modules['saga'].filesystem.File.assert_called_once_with(
            "sftp://{0}{1}".format(self.platform.host, os.path.join(self.platform.get_files_path(),
                                                                                          'file/path')))
        out_mock.remove.assert_called_once_with()
        out_mock.close.assert_called_once_with()

    @patch('autosubmit.platforms.platform.sleep')
    def test_that_get_completed_makes_the_right_number_of_retries_when_not_found(self, mock_sleep):
        retries = 5
        self.platform.get_file = Mock(return_value=False)

        found = self.platform.get_completed_files('any-name', retries)

        self.assertFalse(found)
        self.assertEquals(retries+1, self.platform.get_file.call_count)


class FakeService:
    def __init__(self, jobs):
        self.jobs = jobs


class FakeJob:
    def __init__(self, name, state, type=None, parameters={}):
        self.name = name
        self.state = state
        self.type = type
        self.parameters = parameters


class FakeJobDescription:
    def __init__(self):
        self.executable = None
        self.working_directory = None
        self.output = None
        self.error = None


class FakeBasicConfig:
    def __init__(self):
        pass

    DB_DIR = '/dummy/db/dir'
    DB_FILE = '/dummy/db/file'
    DB_PATH = '/dummy/db/path'
    LOCAL_ROOT_DIR = '/dummy/local/root/dir'
    LOCAL_TMP_DIR = '/dummy/local/temp/dir'
    LOCAL_PROJ_DIR = '/dummy/local/proj/dir'
    DEFAULT_PLATFORMS_CONF = ''
    DEFAULT_JOBS_CONF = ''
