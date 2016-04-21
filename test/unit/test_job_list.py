from random import randrange
from unittest import TestCase

import os
from mock import Mock

from autosubmit.config.parser_factory import ConfigParserFactory
from autosubmit.job.job import Job
from autosubmit.job.job_common import Status
from autosubmit.job.job_list import JobList


class TestJobList(TestCase):
    def setUp(self):
        self.experiment_id = 'random-id'
        self.job_list = JobList(self.experiment_id, FakeBasicConfig, ConfigParserFactory())

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

    def test_get_job_list_returns_the_right_list(self):
        job_list = self.job_list.get_job_list()
        self.assertEquals(self.job_list._job_list, job_list)

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

    def test_get_failed_returns_only_the_failed(self):
        failed = self.job_list.get_failed()

        self.assertEquals(4, len(failed))
        self.assertTrue(self.failed_job in failed)
        self.assertTrue(self.failed_job2 in failed)
        self.assertTrue(self.failed_job3 in failed)
        self.assertTrue(self.failed_job4 in failed)

    def test_get_ready_returns_only_the_ready(self):
        ready = self.job_list.get_ready()

        self.assertEquals(3, len(ready))
        self.assertTrue(self.ready_job in ready)
        self.assertTrue(self.ready_job2 in ready)
        self.assertTrue(self.ready_job3 in ready)

    def test_get_waiting_returns_only_which_are_waiting(self):
        waiting = self.job_list.get_waiting()

        self.assertEquals(2, len(waiting))
        self.assertTrue(self.waiting_job in waiting)
        self.assertTrue(self.waiting_job2 in waiting)

    def test_get_unknown_returns_only_which_are_unknown(self):
        unknown = self.job_list.get_unknown()

        self.assertEquals(1, len(unknown))
        self.assertTrue(self.unknown_job in unknown)

    def test_get_in_queue_returns_only_which_are_queuing_submitted_and_running(self):
        in_queue = self.job_list.get_in_queue()

        self.assertEquals(6, len(in_queue))
        self.assertTrue(self.queuing_job in in_queue)
        self.assertTrue(self.running_job in in_queue)
        self.assertTrue(self.running_job2 in in_queue)
        self.assertTrue(self.submitted_job in in_queue)
        self.assertTrue(self.submitted_job2 in in_queue)
        self.assertTrue(self.submitted_job3 in in_queue)

    def test_get_not_in_queue_returns_only_which_are_waiting_and_ready(self):
        not_in_queue = self.job_list.get_not_in_queue()

        self.assertEquals(5, len(not_in_queue))
        self.assertTrue(self.waiting_job in not_in_queue)
        self.assertTrue(self.waiting_job2 in not_in_queue)
        self.assertTrue(self.ready_job in not_in_queue)
        self.assertTrue(self.ready_job2 in not_in_queue)
        self.assertTrue(self.ready_job3 in not_in_queue)

    def test_get_finished_returns_only_which_are_completed_and_failed(self):
        finished = self.job_list.get_finished()

        self.assertEquals(8, len(finished))
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

        self.assertEquals(10, len(active))
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

        self.assertEquals(self.completed_job, job)

    def test_sort_by_name_returns_the_list_of_jobs_well_sorted(self):
        sorted_by_name = self.job_list.sort_by_name()

        for i in xrange(len(sorted_by_name) - 1):
            self.assertTrue(sorted_by_name[i].name <= sorted_by_name[i + 1].name)

    def test_sort_by_id_returns_the_list_of_jobs_well_sorted(self):
        sorted_by_id = self.job_list.sort_by_id()

        for i in xrange(len(sorted_by_id) - 1):
            self.assertTrue(sorted_by_id[i].id <= sorted_by_id[i + 1].id)

    def test_sort_by_type_returns_the_list_of_jobs_well_sorted(self):
        sorted_by_type = self.job_list.sort_by_type()

        for i in xrange(len(sorted_by_type) - 1):
            self.assertTrue(sorted_by_type[i].type <= sorted_by_type[i + 1].type)

    def test_sort_by_status_returns_the_list_of_jobs_well_sorted(self):
        sorted_by_status = self.job_list.sort_by_status()

        for i in xrange(len(sorted_by_status) - 1):
            self.assertTrue(sorted_by_status[i].status <= sorted_by_status[i + 1].status)

    def test_that_create_method_makes_the_correct_calls(self):
        parser_mock = Mock()
        parser_mock.read = Mock()

        factory = ConfigParserFactory()
        factory.create_parser = Mock(return_value=parser_mock)

        job_list = JobList(self.experiment_id, FakeBasicConfig, factory)
        job_list._create_jobs = Mock()
        job_list._add_dependencies = Mock()
        job_list.update_genealogy = Mock()
        job_list._job_list = [Job('random-name', 9999, Status.WAITING, 0),
                              Job('random-name2', 99999, Status.WAITING, 0)]

        date_list = ['fake-date1', 'fake-date2']
        member_list = ['fake-member1', 'fake-member2']
        num_chunks = 999
        chunk_list = range(1, num_chunks + 1)
        parameters = {'fake-key': 'fake-value',
                      'fake-key2': 'fake-value2'}

        # act
        job_list.create(date_list, member_list, num_chunks, parameters, 'H', 9999)

        # assert
        self.assertEquals(job_list.parameters, parameters)
        self.assertEquals(job_list._date_list, date_list)
        self.assertEquals(job_list._member_list, member_list)
        self.assertEquals(job_list._chunk_list, range(1, num_chunks + 1))
        parser_mock.read.assert_called_once_with(os.path.join(FakeBasicConfig.LOCAL_ROOT_DIR, self.experiment_id,
                                                              'conf', "jobs_" + self.experiment_id + ".conf"))
        cj_args, cj_kwargs = job_list._create_jobs.call_args
        self.assertEquals(parser_mock, cj_args[1])
        self.assertEquals(0, cj_args[2])
        job_list._add_dependencies.assert_called_once_with(date_list, member_list, chunk_list, cj_args[0], parser_mock)
        job_list.update_genealogy.assert_called_once_with()
        for job in job_list._job_list:
            self.assertEquals(parameters, job.parameters)

    def test_that_create_job_method_calls_dic_jobs_method_with_increasing_priority(self):
        # arrange
        dic_mock = Mock()
        dic_mock.read_section = Mock()

        parser_mock = Mock()
        parser_mock.sections = Mock(return_value=['fake-section-1',
                                                  'fake-section-2'])
        # act
        JobList._create_jobs(dic_mock, parser_mock, 0)

        # arrange
        dic_mock.read_section.assert_any_call('fake-section-1', 0)
        dic_mock.read_section.assert_any_call('fake-section-2', 1)

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
