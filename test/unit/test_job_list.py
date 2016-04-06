from random import randrange
from unittest import TestCase

# compatibility with both versions (2 & 3)
from sys import version_info

from autosubmit.job.job_common import Status

from autosubmit.job.job import Job
from autosubmit.job.job_list import JobList

if version_info.major == 2:
    pass
else:
    pass


class TestJobList(TestCase):
    def setUp(self):
        self.experiment_id = 'random-id'
        self.job_list = JobList(self.experiment_id)

        # creating jobs for self list
        self.completed_job = self._createDummyJobWithStatus(Status.COMPLETED)
        self.completed_job2 = self._createDummyJobWithStatus(Status.COMPLETED)
        self.completed_job3 = self._createDummyJobWithStatus(Status.COMPLETED)
        self.completed_job4 = self._createDummyJobWithStatus(Status.COMPLETED)

        self.submitted_job = self._createDummyJobWithStatus(Status.SUBMITTED)
        self.submitted_job2 = self._createDummyJobWithStatus(Status.SUBMITTED)
        self.submitted_job3 = self._createDummyJobWithStatus(Status.SUBMITTED)

        self.running_job = self._createDummyJobWithStatus(Status.RUNNING)
        self.running_job2 = self._createDummyJobWithStatus(Status.RUNNING)

        self.queuing_job = self._createDummyJobWithStatus(Status.QUEUING)

        self.failed_job = self._createDummyJobWithStatus(Status.FAILED)
        self.failed_job2 = self._createDummyJobWithStatus(Status.FAILED)
        self.failed_job3 = self._createDummyJobWithStatus(Status.FAILED)
        self.failed_job4 = self._createDummyJobWithStatus(Status.FAILED)

        self.ready_job = self._createDummyJobWithStatus(Status.READY)
        self.ready_job2 = self._createDummyJobWithStatus(Status.READY)
        self.ready_job3 = self._createDummyJobWithStatus(Status.READY)

        self.waiting_job = self._createDummyJobWithStatus(Status.WAITING)
        self.waiting_job2 = self._createDummyJobWithStatus(Status.WAITING)

        self.unknown_job = self._createDummyJobWithStatus(Status.UNKNOWN)

        self.job_list._job_list = [self.completed_job, self.completed_job2, self.completed_job3, self.completed_job4,
                                   self.submitted_job, self.submitted_job2, self.submitted_job3, self.running_job,
                                   self.running_job2, self.queuing_job, self.failed_job, self.failed_job2,
                                   self.failed_job3, self.failed_job4, self.ready_job, self.ready_job2,
                                   self.ready_job3, self.waiting_job, self.waiting_job2, self.unknown_job]

    def test_get_completed_returns_only_the_completed(self):
        completed = self.job_list.get_completed()

        self.assertEquals(4, len(completed))
        self.assertTrue(self.completed_job in completed)
        self.assertTrue(self.completed_job2 in completed)
        self.assertTrue(self.completed_job3 in completed)
        self.assertTrue(self.completed_job4 in completed)

    def test_get_submitted_returns_only_the_submitted(self):
        submitted = self.job_list.get_submitted()

        self.assertEquals(3, len(submitted))
        self.assertTrue(self.submitted_job in submitted)
        self.assertTrue(self.submitted_job2 in submitted)
        self.assertTrue(self.submitted_job3 in submitted)

    def test_get_running_returns_only_which_are_running(self):
        running = self.job_list.get_running()

        self.assertEquals(2, len(running))
        self.assertTrue(self.running_job in running)
        self.assertTrue(self.running_job2 in running)

    def test_get_running_returns_only_which_are_queuing(self):
        queuing = self.job_list.get_queuing()

        self.assertEquals(1, len(queuing))
        self.assertTrue(self.queuing_job in queuing)

    def _createDummyJobWithStatus(self, status):
        job_name = 'random-name'
        job_id = randrange(1, 999)

        return Job(job_name, job_id, status, 0)


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
