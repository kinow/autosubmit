from unittest import TestCase

import inspect
import shutil
import tempfile
from mock import Mock, MagicMock
from random import randrange

from autosubmit.job.job import Job
from autosubmit.job.job_common import Status
from autosubmit.job.job_list import JobList
from autosubmit.job.job_list_persistence import JobListPersistenceDb
from autosubmitconfigparser.config.yamlparser import YAMLParserFactory


class TestJobList(TestCase):
    def setUp(self):
        self.experiment_id = 'random-id'
        self.as_conf = Mock()
        self.as_conf.experiment_data = dict()
        self.as_conf.experiment_data["JOBS"] = dict()
        self.as_conf.jobs_data = self.as_conf.experiment_data["JOBS"]
        self.as_conf.experiment_data["PLATFORMS"] = dict()
        self.temp_directory = tempfile.mkdtemp()
        self.job_list = JobList(self.experiment_id, FakeBasicConfig, YAMLParserFactory(),
                                JobListPersistenceDb(self.temp_directory, 'db'), self.as_conf)
        dummy_serial_platform = MagicMock()
        dummy_serial_platform.name = 'serial'
        dummy_platform = MagicMock()
        dummy_platform.serial_platform = dummy_serial_platform
        dummy_platform.name = 'dummy_platform'
        # creating jobs for self list
        self.completed_job = self._createDummyJobWithStatus(Status.COMPLETED)
        self.completed_job.platform = dummy_platform
        self.completed_job2 = self._createDummyJobWithStatus(Status.COMPLETED)
        self.completed_job2.platform = dummy_platform
        self.completed_job3 = self._createDummyJobWithStatus(Status.COMPLETED)
        self.completed_job3.platform = dummy_platform
        self.completed_job4 = self._createDummyJobWithStatus(Status.COMPLETED)
        self.completed_job4.platform = dummy_platform
        self.submitted_job = self._createDummyJobWithStatus(Status.SUBMITTED)
        self.submitted_job.platform = dummy_platform
        self.submitted_job2 = self._createDummyJobWithStatus(Status.SUBMITTED)
        self.submitted_job2.platform = dummy_platform
        self.submitted_job3 = self._createDummyJobWithStatus(Status.SUBMITTED)
        self.submitted_job3.platform = dummy_platform

        self.running_job = self._createDummyJobWithStatus(Status.RUNNING)
        self.running_job.platform = dummy_platform
        self.running_job2 = self._createDummyJobWithStatus(Status.RUNNING)
        self.running_job2.platform = dummy_platform

        self.queuing_job = self._createDummyJobWithStatus(Status.QUEUING)
        self.queuing_job.platform = dummy_platform

        self.failed_job = self._createDummyJobWithStatus(Status.FAILED)
        self.failed_job.platform = dummy_platform
        self.failed_job2 = self._createDummyJobWithStatus(Status.FAILED)
        self.failed_job2.platform = dummy_platform
        self.failed_job3 = self._createDummyJobWithStatus(Status.FAILED)
        self.failed_job3.platform = dummy_platform
        self.failed_job4 = self._createDummyJobWithStatus(Status.FAILED)
        self.failed_job4.platform = dummy_platform
        self.ready_job = self._createDummyJobWithStatus(Status.READY)
        self.ready_job.platform = dummy_platform
        self.ready_job2 = self._createDummyJobWithStatus(Status.READY)
        self.ready_job2.platform = dummy_platform
        self.ready_job3 = self._createDummyJobWithStatus(Status.READY)
        self.ready_job3.platform = dummy_platform

        self.waiting_job = self._createDummyJobWithStatus(Status.WAITING)
        self.waiting_job.platform = dummy_platform
        self.waiting_job2 = self._createDummyJobWithStatus(Status.WAITING)
        self.waiting_job2.platform = dummy_platform

        self.unknown_job = self._createDummyJobWithStatus(Status.UNKNOWN)
        self.unknown_job.platform = dummy_platform


        self.job_list._job_list = [self.completed_job, self.completed_job2, self.completed_job3, self.completed_job4,
                                   self.submitted_job, self.submitted_job2, self.submitted_job3, self.running_job,
                                   self.running_job2, self.queuing_job, self.failed_job, self.failed_job2,
                                   self.failed_job3, self.failed_job4, self.ready_job, self.ready_job2,
                                   self.ready_job3, self.waiting_job, self.waiting_job2, self.unknown_job]
        self.waiting_job.parents.add(self.ready_job)
        self.waiting_job.parents.add(self.completed_job)
        self.waiting_job.parents.add(self.failed_job)
        self.waiting_job.parents.add(self.submitted_job)
        self.waiting_job.parents.add(self.running_job)
        self.waiting_job.parents.add(self.queuing_job)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_directory)

    def test_add_edge_job(self):
        special_variables = dict()
        special_variables["STATUS"] = Status.VALUE_TO_KEY[Status.COMPLETED]
        special_variables["FROM_STEP"] = 0
        for p in self.waiting_job.parents:
            self.waiting_job.add_edge_info(p, special_variables)
        for parent in self.waiting_job.parents:
            self.assertEqual(self.waiting_job.edge_info[special_variables["STATUS"]][parent.name],
                             (parent, special_variables.get("FROM_STEP", 0)))


    def test_add_edge_info_joblist(self):
        special_conditions = dict()
        special_conditions["STATUS"] = Status.VALUE_TO_KEY[Status.COMPLETED]
        special_conditions["FROM_STEP"] = 0
        self.job_list._add_edge_info(self.waiting_job, special_conditions["STATUS"])
        self.assertEqual(len(self.job_list.jobs_edges.get(Status.VALUE_TO_KEY[Status.COMPLETED],[])),1)
        self.job_list._add_edge_info(self.waiting_job2, special_conditions["STATUS"])
        self.assertEqual(len(self.job_list.jobs_edges.get(Status.VALUE_TO_KEY[Status.COMPLETED],[])),2)

    def test_check_special_status(self):
        self.waiting_job.edge_info = dict()

        self.job_list.jobs_edges = dict()
        # Adds edge info for waiting_job in the list
        self.job_list._add_edge_info(self.waiting_job, Status.VALUE_TO_KEY[Status.COMPLETED])
        self.job_list._add_edge_info(self.waiting_job, Status.VALUE_TO_KEY[Status.READY])
        self.job_list._add_edge_info(self.waiting_job, Status.VALUE_TO_KEY[Status.RUNNING])
        self.job_list._add_edge_info(self.waiting_job, Status.VALUE_TO_KEY[Status.SUBMITTED])
        self.job_list._add_edge_info(self.waiting_job, Status.VALUE_TO_KEY[Status.QUEUING])
        self.job_list._add_edge_info(self.waiting_job, Status.VALUE_TO_KEY[Status.FAILED])
        # Adds edge info for waiting_job
        special_variables = dict()
        for p in self.waiting_job.parents:
            special_variables["STATUS"] = Status.VALUE_TO_KEY[p.status]
            special_variables["FROM_STEP"] = 0
            self.waiting_job.add_edge_info(p,special_variables)
        # call to special status
        jobs_to_check = self.job_list.check_special_status()
        for job in jobs_to_check:
            tmp = [parent for parent in job.parents if
                   parent.status == Status.COMPLETED or parent in self.jobs_edges["ALL"]]
            assert len(tmp) == len(job.parents)
        self.waiting_job.add_parent(self.waiting_job2)
        for job in jobs_to_check:
            tmp = [parent for parent in job.parents if
                   parent.status == Status.COMPLETED or parent in self.jobs_edges["ALL"]]
            assert len(tmp) == len(job.parents)



    def _createDummyJobWithStatus(self, status):
        job_name = str(randrange(999999, 999999999))
        job_id = randrange(1, 999)
        job = Job(job_name, job_id, status, 0)
        job.type = randrange(0, 2)
        return job

class FakeBasicConfig:
    def __init__(self):
        pass
    def props(self):
        pr = {}
        for name in dir(self):
            value = getattr(self, name)
            if not name.startswith('__') and not inspect.ismethod(value) and not inspect.isfunction(value):
                pr[name] = value
        return pr
    DB_DIR = '/dummy/db/dir'
    DB_FILE = '/dummy/db/file'
    DB_PATH = '/dummy/db/path'
    LOCAL_ROOT_DIR = '/dummy/local/root/dir'
    LOCAL_TMP_DIR = '/dummy/local/temp/dir'
    LOCAL_PROJ_DIR = '/dummy/local/proj/dir'
    DEFAULT_PLATFORMS_CONF = ''
    DEFAULT_JOBS_CONF = ''
