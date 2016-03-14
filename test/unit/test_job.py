from unittest import TestCase
from autosubmit.job.job_common import Status
from autosubmit.job.job import Job
from autosubmit.platforms.platform import Platform


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



class FakeBasicConfig:
    DB_DIR = '/dummy/db/dir'
    DB_FILE = '/dummy/db/file'
    DB_PATH = '/dummy/db/path'
    LOCAL_ROOT_DIR = '/dummy/local/root/dir'
    LOCAL_TMP_DIR = '/dummy/local/temp/dir'
    LOCAL_PROJ_DIR = '/dummy/local/proj/dir'
    DEFAULT_PLATFORMS_CONF = ''
    DEFAULT_JOBS_CONF = ''