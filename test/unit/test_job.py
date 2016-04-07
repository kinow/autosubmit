from unittest import TestCase
import os
import sys
from autosubmit.config.config_common import AutosubmitConfig
from autosubmit.job.job_common import Status
from autosubmit.job.job import Job
from autosubmit.platforms.platform import Platform
from mock import Mock, MagicMock
from mock import patch

# compatibility with both versions (2 & 3)
from sys import version_info

if version_info.major == 2:
    import __builtin__ as builtins
else:
    import builtins


class TestJob(TestCase):
    def setUp(self):
        self.experiment_id = 'random-id'
        self.job_name = 'random-name'
        self.job_id = 999
        self.job_priority = 0

        self.job = Job(self.job_name, self.job_id, Status.WAITING, self.job_priority)

    def test_when_the_job_has_more_than_one_processor_returns_the_parallel_platform(self):
        platform = Platform(self.experiment_id, 'parallel-platform', FakeBasicConfig)
        platform.serial_platform = 'serial-platform'

        self.job._platform = platform
        self.job.processors = 999

        returned_platform = self.job.get_platform()

        self.assertEquals(platform, returned_platform)

    def test_when_the_job_has_only_one_processor_returns_the_serial_platform(self):
        platform = Platform(self.experiment_id, 'parallel-platform', FakeBasicConfig)
        platform.serial_platform = 'serial-platform'

        self.job._platform = platform
        self.job.processors = 1

        returned_platform = self.job.get_platform()

        self.assertEquals('serial-platform', returned_platform)

    def test_set_platform(self):
        dummy_platform = Platform('whatever', 'rand-name', FakeBasicConfig)
        self.assertNotEquals(dummy_platform, self.job._platform)

        self.job.set_platform(dummy_platform)

        self.assertEquals(dummy_platform, self.job._platform)

    def test_when_the_job_has_a_queue_returns_that_queue(self):
        dummy_queue = 'whatever'
        self.job._queue = dummy_queue

        returned_queue = self.job.get_queue()

        self.assertEquals(dummy_queue, returned_queue)

    def test_when_the_job_has_not_a_queue_and_some_processors_returns_the_queue_of_the_platform(self):
        dummy_queue = 'whatever-parallel'
        dummy_platform = Platform('whatever', 'rand-name', FakeBasicConfig)
        dummy_platform.queue = dummy_queue
        self.job.set_platform(dummy_platform)

        self.assertIsNone(self.job._queue)

        returned_queue = self.job.get_queue()

        self.assertIsNotNone(returned_queue)
        self.assertEquals(dummy_queue, returned_queue)

    def test_when_the_job_has_not_a_queue_and_one_processor_returns_the_queue_of_the_serial_platform(self):
        serial_queue = 'whatever-serial'
        parallel_queue = 'whatever-parallel'

        dummy_serial_platform = Platform('whatever', 'serial', FakeBasicConfig)
        dummy_serial_platform.serial_queue = serial_queue

        dummy_platform = Platform('whatever', 'parallel', FakeBasicConfig)
        dummy_platform.serial_platform = dummy_serial_platform
        dummy_platform.queue = parallel_queue

        self.job.set_platform(dummy_platform)
        self.job.processors = 1

        self.assertIsNone(self.job._queue)

        returned_queue = self.job.get_queue()

        self.assertIsNotNone(returned_queue)
        self.assertEquals(serial_queue, returned_queue)
        self.assertNotEquals(parallel_queue, returned_queue)

    def test_set_queue(self):
        dummy_queue = 'whatever'
        self.assertNotEquals(dummy_queue, self.job._queue)

        self.job.set_queue(dummy_queue)

        self.assertEquals(dummy_queue, self.job._queue)

    def test_that_the_increment_fails_count_only_adds_one(self):
        initial_fail_count = self.job.fail_count
        self.job.inc_fail_count()
        incremented_fail_count = self.job.fail_count

        self.assertEquals(initial_fail_count + 1, incremented_fail_count)

    def test_parents_and_children_management(self):
        random_job1 = Job('dummy-name', 111, Status.WAITING, 0)
        random_job2 = Job('dummy-name2', 222, Status.WAITING, 0)
        random_job3 = Job('dummy-name3', 333, Status.WAITING, 0)

        self.job.add_parent(random_job1,
                            random_job2,
                            random_job3)

        # assert added
        self.assertEquals(3, len(self.job.parents))
        self.assertEquals(1, len(random_job1.children))
        self.assertEquals(1, len(random_job2.children))
        self.assertEquals(1, len(random_job3.children))

        # assert contains
        self.assertTrue(self.job.parents.__contains__(random_job1))
        self.assertTrue(self.job.parents.__contains__(random_job2))
        self.assertTrue(self.job.parents.__contains__(random_job3))

        self.assertTrue(random_job1.children.__contains__(self.job))
        self.assertTrue(random_job2.children.__contains__(self.job))
        self.assertTrue(random_job3.children.__contains__(self.job))

        # assert has
        self.assertFalse(self.job.has_children())
        self.assertTrue(self.job.has_parents())

        # assert deletions
        self.job.delete_parent(random_job3)
        self.assertEquals(2, len(self.job.parents))

        random_job1.delete_child(self.job)
        self.assertEquals(0, len(random_job1.children))

    def test_create_script(self):
        # arrange
        self.job.parameters = dict()
        self.job.parameters['NUMPROC'] = 999
        self.job.parameters['NUMTHREADS'] = 777
        self.job.parameters['NUMTASK'] = 666

        self.job._tmp_path = '/dummy/tmp/path'

        update_content_mock = Mock(return_value='some-content: %NUMPROC%, %NUMTHREADS%, %NUMTASK% %% %%')
        self.job.update_content = update_content_mock

        config = Mock(spec=AutosubmitConfig)
        config.get_project_dir = Mock(return_value='/project/dir')

        chmod_mock = Mock()
        sys.modules['os'].chmod = chmod_mock

        write_mock = Mock().write = Mock()
        open_mock = Mock(return_value=write_mock)
        with patch.object(builtins, "open", open_mock):
            # act
            self.job.create_script(config)

        # assert
        update_content_mock.assert_called_with('/project/dir')
        open_mock.assert_called_with(os.path.join(self.job._tmp_path, self.job.name + '.cmd'), 'w')
        write_mock.write.assert_called_with('some-content: 999, 777, 666 % %')
        chmod_mock.assert_called_with(os.path.join(self.job._tmp_path, self.job.name + '.cmd'), 0o775)

    def test_that_check_script_returns_true_when_it_is_not_needed(self):
        # arrange
        self.job.check = False

        # act
        result = self.job.check_script(Mock(), dict())

        # assert
        self.assertTrue(result)

    def test_that_check_script_returns_false_when_there_is_an_unbound_template_variable(self):
        # arrange
        update_content_mock = Mock(return_value='some-content: %UNBOUND%')
        self.job.update_content = update_content_mock

        update_parameters_mock = Mock(return_value=self.job.parameters)
        self.job.update_parameters = update_parameters_mock

        config = Mock(spec=AutosubmitConfig)
        config.get_project_dir = Mock(return_value='/project/dir')

        # act
        checked = self.job.check_script(config, self.job.parameters)

        # assert
        update_parameters_mock.assert_called_with(config, self.job.parameters)
        update_content_mock.assert_called_with('/project/dir')
        self.assertFalse(checked)

    def test_check_script(self):
        # arrange
        self.job.parameters = dict()
        self.job.parameters['NUMPROC'] = 999
        self.job.parameters['NUMTHREADS'] = 777
        self.job.parameters['NUMTASK'] = 666

        update_content_mock = Mock(return_value='some-content: %NUMPROC%, %NUMTHREADS%, %NUMTASK%')
        self.job.update_content = update_content_mock

        update_parameters_mock = Mock(return_value=self.job.parameters)
        self.job.update_parameters = update_parameters_mock

        config = Mock(spec=AutosubmitConfig)
        config.get_project_dir = Mock(return_value='/project/dir')

        create_script_mock = Mock()
        self.job.create_script = create_script_mock

        # act
        checked = self.job.check_script(config, self.job.parameters)

        # assert
        update_parameters_mock.assert_called_with(config, self.job.parameters)
        update_content_mock.assert_called_with('/project/dir')
        create_script_mock.assert_called_with(config)
        self.assertTrue(checked)

    def test_exists_completed_file_then_sets_status_to_completed(self):
        # arrange
        exists_mock = Mock(return_value=True)
        sys.modules['os'].path.exists = exists_mock

        # act
        self.job.check_completion()

        # assert
        exists_mock.assert_called_once_with(os.path.join(self.job._tmp_path, self.job.name + '_COMPLETED'))
        self.assertEquals(Status.COMPLETED, self.job.status)

    def test_completed_file_not_exists_then_sets_status_to_failed(self):
        # arrange
        exists_mock = Mock(return_value=False)
        sys.modules['os'].path.exists = exists_mock

        # act
        self.job.check_completion()

        # assert
        exists_mock.assert_called_once_with(os.path.join(self.job._tmp_path, self.job.name + '_COMPLETED'))
        self.assertEquals(Status.FAILED, self.job.status)


class FakeBasicConfig:
    DB_DIR = '/dummy/db/dir'
    DB_FILE = '/dummy/db/file'
    DB_PATH = '/dummy/db/path'
    LOCAL_ROOT_DIR = '/dummy/local/root/dir'
    LOCAL_TMP_DIR = '/dummy/local/temp/dir'
    LOCAL_PROJ_DIR = '/dummy/local/proj/dir'
    DEFAULT_PLATFORMS_CONF = ''
    DEFAULT_JOBS_CONF = ''



