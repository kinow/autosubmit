from unittest import TestCase

import shutil
import tempfile
from mock import Mock
from random import randrange

from autosubmit.job.job import Job
from autosubmit.job.job_common import Status
from autosubmit.job.job_common import Type
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

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_directory)

    def test_get_job_list_returns_the_right_list(self):
        job_list = self.job_list.get_job_list()
        self.assertEqual(self.job_list._job_list, job_list)

    def test_get_completed_returns_only_the_completed(self):
        completed = self.job_list.get_completed()

        self.assertEqual(4, len(completed))
        self.assertTrue(self.completed_job in completed)
        self.assertTrue(self.completed_job2 in completed)
        self.assertTrue(self.completed_job3 in completed)
        self.assertTrue(self.completed_job4 in completed)

    def test_get_submitted_returns_only_the_submitted(self):
        submitted = self.job_list.get_submitted()

        self.assertEqual(3, len(submitted))
        self.assertTrue(self.submitted_job in submitted)
        self.assertTrue(self.submitted_job2 in submitted)
        self.assertTrue(self.submitted_job3 in submitted)

    def test_get_running_returns_only_which_are_running(self):
        running = self.job_list.get_running()

        self.assertEqual(2, len(running))
        self.assertTrue(self.running_job in running)
        self.assertTrue(self.running_job2 in running)

    def test_get_running_returns_only_which_are_queuing(self):
        queuing = self.job_list.get_queuing()

        self.assertEqual(1, len(queuing))
        self.assertTrue(self.queuing_job in queuing)

    def test_get_failed_returns_only_the_failed(self):
        failed = self.job_list.get_failed()

        self.assertEqual(4, len(failed))
        self.assertTrue(self.failed_job in failed)
        self.assertTrue(self.failed_job2 in failed)
        self.assertTrue(self.failed_job3 in failed)
        self.assertTrue(self.failed_job4 in failed)

    def test_get_ready_returns_only_the_ready(self):
        ready = self.job_list.get_ready()

        self.assertEqual(3, len(ready))
        self.assertTrue(self.ready_job in ready)
        self.assertTrue(self.ready_job2 in ready)
        self.assertTrue(self.ready_job3 in ready)

    def test_get_waiting_returns_only_which_are_waiting(self):
        waiting = self.job_list.get_waiting()

        self.assertEqual(2, len(waiting))
        self.assertTrue(self.waiting_job in waiting)
        self.assertTrue(self.waiting_job2 in waiting)

    def test_get_unknown_returns_only_which_are_unknown(self):
        unknown = self.job_list.get_unknown()

        self.assertEqual(1, len(unknown))
        self.assertTrue(self.unknown_job in unknown)

    def test_get_in_queue_returns_only_which_are_queuing_submitted_and_running(self):
        in_queue = self.job_list.get_in_queue()

        self.assertEqual(7, len(in_queue))
        self.assertTrue(self.queuing_job in in_queue)
        self.assertTrue(self.running_job in in_queue)
        self.assertTrue(self.running_job2 in in_queue)
        self.assertTrue(self.submitted_job in in_queue)
        self.assertTrue(self.submitted_job2 in in_queue)
        self.assertTrue(self.submitted_job3 in in_queue)
        self.assertTrue(self.unknown_job in in_queue)

    def test_get_not_in_queue_returns_only_which_are_waiting_and_ready(self):
        not_in_queue = self.job_list.get_not_in_queue()

        self.assertEqual(5, len(not_in_queue))
        self.assertTrue(self.waiting_job in not_in_queue)
        self.assertTrue(self.waiting_job2 in not_in_queue)
        self.assertTrue(self.ready_job in not_in_queue)
        self.assertTrue(self.ready_job2 in not_in_queue)
        self.assertTrue(self.ready_job3 in not_in_queue)

    def test_get_finished_returns_only_which_are_completed_and_failed(self):
        finished = self.job_list.get_finished()

        self.assertEqual(8, len(finished))
        self.assertTrue(self.completed_job in finished)
        self.assertTrue(self.completed_job2 in finished)
        self.assertTrue(self.completed_job3 in finished)
        self.assertTrue(self.completed_job4 in finished)
        self.assertTrue(self.failed_job in finished)
        self.assertTrue(self.failed_job2 in finished)
        self.assertTrue(self.failed_job3 in finished)
        self.assertTrue(self.failed_job4 in finished)

    def test_get_active_returns_only_which_are_in_queue_ready_and_unknown(self):
        active = self.job_list.get_active()

        self.assertEqual(10, len(active))
        self.assertTrue(self.queuing_job in active)
        self.assertTrue(self.running_job in active)
        self.assertTrue(self.running_job2 in active)
        self.assertTrue(self.submitted_job in active)
        self.assertTrue(self.submitted_job2 in active)
        self.assertTrue(self.submitted_job3 in active)
        self.assertTrue(self.ready_job in active)
        self.assertTrue(self.ready_job2 in active)
        self.assertTrue(self.ready_job3 in active)
        self.assertTrue(self.unknown_job in active)

    def test_get_job_by_name_returns_the_expected_job(self):
        job = self.job_list.get_job_by_name(self.completed_job.name)

        self.assertEqual(self.completed_job, job)

    def test_sort_by_name_returns_the_list_of_jobs_well_sorted(self):
        sorted_by_name = self.job_list.sort_by_name()

        for i in range(len(sorted_by_name) - 1):
            self.assertTrue(
                sorted_by_name[i].name <= sorted_by_name[i + 1].name)

    def test_sort_by_id_returns_the_list_of_jobs_well_sorted(self):
        sorted_by_id = self.job_list.sort_by_id()

        for i in range(len(sorted_by_id) - 1):
            self.assertTrue(sorted_by_id[i].id <= sorted_by_id[i + 1].id)

    def test_sort_by_type_returns_the_list_of_jobs_well_sorted(self):
        sorted_by_type = self.job_list.sort_by_type()

        for i in range(len(sorted_by_type) - 1):
            self.assertTrue(
                sorted_by_type[i].type <= sorted_by_type[i + 1].type)

    def test_sort_by_status_returns_the_list_of_jobs_well_sorted(self):
        sorted_by_status = self.job_list.sort_by_status()

        for i in range(len(sorted_by_status) - 1):
            self.assertTrue(
                sorted_by_status[i].status <= sorted_by_status[i + 1].status)

    def test_that_create_method_makes_the_correct_calls(self):
        parser_mock = Mock()
        parser_mock.read = Mock()

        factory = YAMLParserFactory()
        factory.create_parser = Mock(return_value=parser_mock)

        job_list = JobList(self.experiment_id, FakeBasicConfig,
                           factory, JobListPersistenceDb(self.temp_directory, 'db2'), self.as_conf)
        job_list._create_jobs = Mock()
        job_list._add_dependencies = Mock()
        job_list.update_genealogy = Mock()
        job_list._job_list = [Job('random-name', 9999, Status.WAITING, 0),
                              Job('random-name2', 99999, Status.WAITING, 0)]
        date_list = ['fake-date1', 'fake-date2']
        member_list = ['fake-member1', 'fake-member2']
        num_chunks = 999
        chunk_list = list(range(1, num_chunks + 1))
        parameters = {'fake-key': 'fake-value',
                      'fake-key2': 'fake-value2'}
        graph_mock = Mock()
        job_list.graph = graph_mock
        # act
        job_list.generate(date_list, member_list, num_chunks,
                          1, parameters, 'H', 9999, Type.BASH, 'None', update_structure=True)

        # assert
        self.assertEqual(job_list.parameters, parameters)
        self.assertEqual(job_list._date_list, date_list)
        self.assertEqual(job_list._member_list, member_list)
        self.assertEqual(job_list._chunk_list, list(range(1, num_chunks + 1)))

        cj_args, cj_kwargs = job_list._create_jobs.call_args
        self.assertEqual(0, cj_args[2])
        job_list._add_dependencies.assert_called_once_with(date_list, member_list, chunk_list, cj_args[0],
                                                           graph_mock)
        # Adding flag update structure
        job_list.update_genealogy.assert_called_once_with(
            True, False, update_structure=True)
        for job in job_list._job_list:
            self.assertEqual(parameters, job.parameters)

    def test_that_create_job_method_calls_dic_jobs_method_with_increasing_priority(self):
        # arrange
        dic_mock = Mock()
        dic_mock.read_section = Mock()
        dic_mock._jobs_data = dict()
        dic_mock._jobs_data["JOBS"] = {'fake-section-1': {}, 'fake-section-2': {}}
        self.job_list.experiment_data["JOBS"] = {'fake-section-1': {}, 'fake-section-2': {}}

        # act
        JobList._create_jobs(dic_mock, 0, Type.BASH, jobs_data=dict())

        # arrange
        dic_mock.read_section.assert_any_call(
            'fake-section-1', 0, Type.BASH, dict())
        dic_mock.read_section.assert_any_call(
            'fake-section-2', 1, Type.BASH, dict())

    def _createDummyJobWithStatus(self, status):
        job_name = str(randrange(999999, 999999999))
        job_id = randrange(1, 999)
        job = Job(job_name, job_id, status, 0)
        job.type = randrange(0, 2)
        return job


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
