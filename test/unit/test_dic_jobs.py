from datetime import datetime
from unittest import TestCase

from mock import Mock
import math
from bscearth.utils.config_parser import ConfigParserFactory
from autosubmit.job.job_common import Status
from autosubmit.job.job_common import Type
from autosubmit.job.job_dict import DicJobs
from autosubmit.job.job_list import JobList
from autosubmit.job.job_list_persistence import JobListPersistenceDb


class TestDicJobs(TestCase):
    def setUp(self):
        self.experiment_id = 'random-id'
        self.job_list = JobList(self.experiment_id, FakeBasicConfig, ConfigParserFactory(),
                                JobListPersistenceDb('.', '.'))
        self.parser_mock = Mock(spec='SafeConfigParser')
        self.date_list = ['fake-date1', 'fake-date2']
        self.member_list = ['fake-member1', 'fake-member2']
        self.num_chunks = 99
        self.chunk_list = range(1, self.num_chunks + 1)
        self.date_format = 'H'
        self.default_retrials = 999
        self.dictionary = DicJobs(self.job_list, self.parser_mock, self.date_list, self.member_list, self.chunk_list,
                                  self.date_format, self.default_retrials)

    def test_read_section_running_once_create_jobs_once(self):
        # arrange
        section = 'fake-section'
        priority = 999
        self.parser_mock.has_option = Mock(return_value=True)
        self.parser_mock.get = Mock(return_value='once')
        self.dictionary.get_option = Mock(return_value=123)
        self.dictionary._create_jobs_once = Mock()
        self.dictionary._create_jobs_startdate = Mock()
        self.dictionary._create_jobs_member = Mock()
        self.dictionary._create_jobs_chunk = Mock()

        # act
        self.dictionary.read_section(section, priority, Type.BASH)

        # assert
        self.dictionary._create_jobs_once.assert_called_once_with(section, priority, Type.BASH, {})
        self.dictionary._create_jobs_startdate.assert_not_called()
        self.dictionary._create_jobs_member.assert_not_called()
        self.dictionary._create_jobs_chunk.assert_not_called()

    def test_read_section_running_date_create_jobs_startdate(self):
        # arrange
        section = 'fake-section'
        priority = 999
        frequency = 123
        self.parser_mock.has_option = Mock(return_value=True)
        self.parser_mock.get = Mock(return_value='date')
        self.dictionary.get_option = Mock(return_value=frequency)
        self.dictionary._create_jobs_once = Mock()
        self.dictionary._create_jobs_startdate = Mock()
        self.dictionary._create_jobs_member = Mock()
        self.dictionary._create_jobs_chunk = Mock()

        # act
        self.dictionary.read_section(section, priority, Type.BASH)

        # assert
        self.dictionary._create_jobs_once.assert_not_called()
        self.dictionary._create_jobs_startdate.assert_called_once_with(section, priority, frequency, Type.BASH, {})
        self.dictionary._create_jobs_member.assert_not_called()
        self.dictionary._create_jobs_chunk.assert_not_called()

    def test_read_section_running_member_create_jobs_member(self):
        # arrange
        section = 'fake-section'
        priority = 999
        frequency = 123
        self.parser_mock.has_option = Mock(return_value=True)
        self.parser_mock.get = Mock(return_value='member')
        self.dictionary.get_option = Mock(return_value=frequency)
        self.dictionary._create_jobs_once = Mock()
        self.dictionary._create_jobs_startdate = Mock()
        self.dictionary._create_jobs_member = Mock()
        self.dictionary._create_jobs_chunk = Mock()

        # act
        self.dictionary.read_section(section, priority, Type.BASH)

        # assert
        self.dictionary._create_jobs_once.assert_not_called()
        self.dictionary._create_jobs_startdate.assert_not_called()
        self.dictionary._create_jobs_member.assert_called_once_with(section, priority, frequency, Type.BASH, {})
        self.dictionary._create_jobs_chunk.assert_not_called()

    def test_read_section_running_chunk_create_jobs_chunk(self):
        # arrange
        section = 'fake-section'
        priority = 999
        frequency = 123
        synchronize = 'date'
        delay = -1
        splits = 0
        self.parser_mock.has_option = Mock(return_value=True)
        self.parser_mock.get = Mock(return_value='chunk')
        self.dictionary.get_option = Mock(side_effect=[frequency, synchronize, delay, splits])
        self.dictionary._create_jobs_once = Mock()
        self.dictionary._create_jobs_startdate = Mock()
        self.dictionary._create_jobs_member = Mock()
        self.dictionary._create_jobs_chunk = Mock()

        # act
        self.dictionary.read_section(section, priority, Type.BASH)

        # assert
        self.dictionary._create_jobs_once.assert_not_called()
        self.dictionary._create_jobs_startdate.assert_not_called()
        self.dictionary._create_jobs_member.assert_not_called()
        self.dictionary._create_jobs_chunk.assert_called_once_with(section, priority, frequency, Type.BASH, synchronize, delay, splits, {})

    def test_dic_creates_right_jobs_by_startdate(self):
        # arrange
        mock_section = Mock()
        mock_section.name = 'fake-section'
        priority = 999
        frequency = 1
        self.dictionary.build_job = Mock(return_value=mock_section)
        # act
        self.dictionary._create_jobs_startdate(mock_section.name, priority, frequency, Type.BASH)

        # assert
        self.assertEquals(len(self.date_list), self.dictionary.build_job.call_count)
        self.assertEquals(len(self.dictionary._dic[mock_section.name]), len(self.date_list))
        for date in self.date_list:
            self.assertEquals(self.dictionary._dic[mock_section.name][date], mock_section)

    def test_dic_creates_right_jobs_by_member(self):
        # arrange
        mock_section = Mock()
        mock_section.name = 'fake-section'
        priority = 999
        frequency = 1
        self.dictionary.build_job = Mock(return_value=mock_section)

        # act
        self.dictionary._create_jobs_member(mock_section.name, priority, frequency, Type.BASH)

        # assert
        self.assertEquals(len(self.date_list) * len(self.member_list), self.dictionary.build_job.call_count)
        self.assertEquals(len(self.dictionary._dic[mock_section.name]), len(self.date_list))
        for date in self.date_list:
            for member in self.member_list:
                self.assertEquals(self.dictionary._dic[mock_section.name][date][member], mock_section)

    def test_dic_creates_right_jobs_by_chunk(self):
        # arrange
        mock_section = Mock()
        mock_section.name = 'fake-section'
        priority = 999
        frequency = 1
        self.dictionary.build_job = Mock(return_value=mock_section)

        # act
        self.dictionary._create_jobs_chunk(mock_section.name, priority, frequency, Type.BASH)

        # assert
        self.assertEquals(len(self.date_list) * len(self.member_list) * len(self.chunk_list),
                          self.dictionary.build_job.call_count)
        self.assertEquals(len(self.dictionary._dic[mock_section.name]), len(self.date_list))
        for date in self.date_list:
            for member in self.member_list:
                for chunk in self.chunk_list:
                    self.assertEquals(self.dictionary._dic[mock_section.name][date][member][chunk], mock_section)

    def test_dic_creates_right_jobs_by_chunk_with_frequency_3(self):
        # arrange
        mock_section = Mock()
        mock_section.name = 'fake-section'
        priority = 999
        frequency = 3
        self.dictionary.build_job = Mock(return_value=mock_section)

        # act
        self.dictionary._create_jobs_chunk(mock_section.name, priority, frequency, Type.BASH)

        # assert
        self.assertEquals(len(self.date_list) * len(self.member_list) * (len(self.chunk_list) / frequency),
                          self.dictionary.build_job.call_count)
        self.assertEquals(len(self.dictionary._dic[mock_section.name]), len(self.date_list))

    def test_dic_creates_right_jobs_by_chunk_with_frequency_4(self):
        # arrange
        mock_section = Mock()
        mock_section.name = 'fake-section'
        priority = 999
        frequency = 4
        self.dictionary.build_job = Mock(return_value=mock_section)

        # act
        self.dictionary._create_jobs_chunk(mock_section.name, priority, frequency, Type.BASH)

        # assert
        # you have to multiply to the round upwards (ceil) of the next division
        self.assertEquals(
            len(self.date_list) * len(self.member_list) * math.ceil(len(self.chunk_list) / float(frequency)),
            self.dictionary.build_job.call_count)
        self.assertEquals(len(self.dictionary._dic[mock_section.name]), len(self.date_list))

    def test_dic_creates_right_jobs_by_chunk_with_date_synchronize(self):
        # arrange
        mock_section = Mock()
        mock_section.name = 'fake-section'
        priority = 999
        frequency = 1
        created_job = 'created_job'
        self.dictionary.build_job = Mock(return_value=mock_section)

        # act
        self.dictionary._create_jobs_chunk(mock_section.name, priority, frequency, Type.BASH, 'date')

        # assert
        self.assertEquals(len(self.chunk_list),
                          self.dictionary.build_job.call_count)
        self.assertEquals(len(self.dictionary._dic[mock_section.name]), len(self.date_list))
        for date in self.date_list:
            for member in self.member_list:
                for chunk in self.chunk_list:
                    self.assertEquals(self.dictionary._dic[mock_section.name][date][member][chunk], mock_section)

    def test_dic_creates_right_jobs_by_chunk_with_date_synchronize_and_frequency_4(self):
        # arrange
        mock_section = Mock()
        mock_section.name = 'fake-section'
        priority = 999
        frequency = 4
        self.dictionary.build_job = Mock(return_value=mock_section)

        # act
        self.dictionary._create_jobs_chunk(mock_section.name, priority, frequency, Type.BASH, 'date')

        # assert
        self.assertEquals(math.ceil(len(self.chunk_list) / float(frequency)),
                          self.dictionary.build_job.call_count)
        self.assertEquals(len(self.dictionary._dic[mock_section.name]), len(self.date_list))

    def test_dic_creates_right_jobs_by_chunk_with_member_synchronize(self):
        # arrange
        mock_section = Mock()
        mock_section.name = 'fake-section'
        priority = 999
        frequency = 1
        self.dictionary.build_job = Mock(return_value=mock_section)

        # act
        self.dictionary._create_jobs_chunk(mock_section.name, priority, frequency, Type.BASH, 'member')

        # assert
        self.assertEquals(len(self.date_list) * len(self.chunk_list),
                          self.dictionary.build_job.call_count)
        self.assertEquals(len(self.dictionary._dic[mock_section.name]), len(self.date_list))
        for date in self.date_list:
            for member in self.member_list:
                for chunk in self.chunk_list:
                    self.assertEquals(self.dictionary._dic[mock_section.name][date][member][chunk], mock_section)

    def test_dic_creates_right_jobs_by_chunk_with_member_synchronize_and_frequency_4(self):
        # arrange
        mock_section = Mock()
        mock_section.name = 'fake-section'
        priority = 999
        frequency = 4
        self.dictionary.build_job = Mock(return_value=mock_section)

        # act
        self.dictionary._create_jobs_chunk(mock_section.name, priority, frequency, Type.BASH, 'member')

        # assert
        self.assertEquals(len(self.date_list) * math.ceil(len(self.chunk_list) / float(frequency)),
                          self.dictionary.build_job.call_count)
        self.assertEquals(len(self.dictionary._dic[mock_section.name]), len(self.date_list))

    def test_create_job_creates_a_job_with_right_parameters(self):
        # arrange
        section = ''
        priority = 99
        date = datetime(2016, 1, 1)
        member = 'fc0'
        chunk = 'ch0'
        frequency = 123
        delay = -1
        platform_name = 'fake-platform'
        filename = 'fake-fike'
        queue = 'fake-queue'
        processors = '111'
        threads = '222'
        tasks = '333'
        memory = memory_per_task = 444
        wallclock = 555
        notify_on = 'COMPLETED FAILED'
        synchronize = None
        self.parser_mock.has_option = Mock(side_effect=[True, True, True, True, True, True, True, True, True, True, True,
                                                        True, True, True, True, False, True, False])
        self.parser_mock.get = Mock(side_effect=[frequency, delay, 'True', 'True', 'bash', platform_name, filename, queue,
                                                 'True', processors, threads, tasks, memory, memory_per_task,
                                                 wallclock, notify_on,synchronize])
        job_list_mock = Mock()
        job_list_mock.append = Mock()
        self.dictionary._jobs_list.get_job_list = Mock(return_value=job_list_mock)

        # act
        created_job = self.dictionary.build_job(section, priority, date, member, chunk, dict())

        # assert
        self.assertEquals('random-id_2016010100_fc0_ch0_', created_job.name)
        self.assertEquals(Status.WAITING, created_job.status)
        self.assertEquals(priority, created_job.priority)
        self.assertEquals(section, created_job.section)
        self.assertEquals(date, created_job.date)
        self.assertEquals(member, created_job.member)
        self.assertEquals(chunk, created_job.chunk)
        self.assertEquals(self.date_format, created_job.date_format)
        self.assertEquals(frequency, created_job.frequency)
        self.assertEquals(delay, created_job.delay)
        self.assertTrue(created_job.wait)
        self.assertTrue(created_job.rerun_only)
        self.assertEquals(Type.BASH, created_job.type)
        self.assertEquals(platform_name, created_job.platform_name)
        self.assertEquals(filename, created_job.file)
        self.assertEquals(queue, created_job.queue)
        self.assertTrue(created_job.check)
        self.assertEquals(processors, created_job.processors)
        self.assertEquals(threads, created_job.threads)
        self.assertEquals(tasks, created_job.tasks)
        self.assertEquals(memory, created_job.memory)
        self.assertEquals(wallclock, created_job.wallclock)
        self.assertIsNone(created_job.retrials)
        job_list_mock.append.assert_called_once_with(created_job)

    def test_get_option_returns_the_right_option_otherwise_the_default(self):
        # arrange
        section = 'any-section'
        option = 'any-option'
        default = 'any-default'

        self.parser_mock.has_option = Mock(side_effect=[True, False])
        self.parser_mock.get = Mock(return_value=option)

        # act
        returned_option = self.dictionary.get_option(section, option, default)
        returned_default = self.dictionary.get_option(section, option, default)

        # assert
        self.assertEquals(option, returned_option)
        self.assertEquals(default, returned_default)

    def test_get_member_returns_the_jobs_if_no_member(self):
        # arrange
        jobs = 'fake-jobs'
        dic = {'any-key': 'any-value'}

        # act
        returned_jobs = self.dictionary._get_member(jobs, dic, 'fake-member', None)  # expected jobs

        # arrange
        self.assertEquals(jobs, returned_jobs)

    def test_get_member_returns_the_jobs_with_the_member(self):
        # arrange
        jobs = ['fake-job']
        dic = {'fake-job2': 'any-value'}
        member = 'fake-job2'

        # act
        returned_jobs = self.dictionary._get_member(jobs, dic, member, None)

        # arrange
        self.assertEquals(['fake-job'] + ['any-value'], returned_jobs)  # expected jobs + member

    def test_get_member_returns_the_jobs_with_the_given_chunk_of_the_member(self):
        # arrange
        jobs = ['fake-job']
        dic = {'fake-job2': {'fake-job3': 'fake'}}
        member = 'fake-job2'

        # act
        returned_jobs = self.dictionary._get_member(jobs, dic, member, 'fake-job3')

        # arrange
        self.assertEquals(['fake-job'] + ['fake'], returned_jobs)  # expected jobs + chunk

    def test_get_member_returns_the_jobs_with_all_the_chunks_of_the_member(self):
        # arrange
        jobs = ['fake-job']
        dic = {'fake-job2': {5: 'fake5', 8: 'fake8', 9: 'fake9'}}
        member = 'fake-job2'

        # act
        returned_jobs = self.dictionary._get_member(jobs, dic, member, None)

        # arrange
        self.assertEquals(['fake-job'] + ['fake5', 'fake8', 'fake9'], returned_jobs)  # expected jobs + all chunks

    def test_get_date_returns_the_jobs_if_no_date(self):
        # arrange
        jobs = 'fake-jobs'
        dic = {'any-key': 'any-value'}

        # act
        returned_jobs = self.dictionary._get_date(jobs, dic, 'whatever', None, None)

        # arrange
        self.assertEquals('fake-jobs', returned_jobs)  # expected jobs

    def test_get_date_returns_the_jobs_with_the_date(self):
        # arrange
        jobs = ['fake-job']
        dic = {'fake-job2': 'any-value'}
        date = 'fake-job2'

        # act
        returned_jobs = self.dictionary._get_date(jobs, dic, date, None, None)

        # arrange
        self.assertEquals(['fake-job'] + ['any-value'], returned_jobs)  # expected jobs + date

    def test_get_date_returns_the_jobs_and_calls_get_member_once_with_the_given_member(self):
        # arrange
        jobs = ['fake-job']
        date_dic = {'fake-job3': 'fake'}
        dic = {'fake-job2': date_dic}
        date = 'fake-job2'
        member = 'fake-member'
        chunk = 'fake-chunk'
        self.dictionary._get_member = Mock()

        # act
        returned_jobs = self.dictionary._get_date(jobs, dic, date, member, chunk)

        # arrange
        self.assertEquals(['fake-job'], returned_jobs)
        self.dictionary._get_member.assert_called_once_with(jobs, date_dic, member, chunk)

    def test_get_date_returns_the_jobs_and_calls_get_member_for_all_its_members(self):
        # arrange
        jobs = ['fake-job']
        date_dic = {'fake-job3': 'fake'}
        dic = {'fake-job2': date_dic}
        date = 'fake-job2'
        chunk = 'fake-chunk'
        self.dictionary._get_member = Mock()

        # act
        returned_jobs = self.dictionary._get_date(jobs, dic, date, None, chunk)

        # arrange
        self.assertEquals(['fake-job'], returned_jobs)
        self.assertEquals(len(self.dictionary._member_list), self.dictionary._get_member.call_count)
        for member in self.dictionary._member_list:
            self.dictionary._get_member.assert_any_call(jobs, date_dic, member, chunk)

    def test_get_jobs_returns_the_job_of_the_section(self):
        # arrange
        section = 'fake-section'
        self.dictionary._dic = {'fake-section': 'fake-job'}

        # act
        returned_jobs = self.dictionary.get_jobs(section)

        # arrange
        self.assertEquals(['fake-job'], returned_jobs)

    def test_get_jobs_calls_get_date_with_given_date(self):
        # arrange
        section = 'fake-section'
        dic = {'fake-job3': 'fake'}
        date = 'fake-date'
        member = 'fake-member'
        chunk = 111
        self.dictionary._dic = {'fake-section': dic}
        self.dictionary._get_date = Mock()

        # act
        returned_jobs = self.dictionary.get_jobs(section, date, member, chunk)

        # arrange
        self.assertEquals(list(), returned_jobs)
        self.dictionary._get_date.assert_called_once_with(list(), dic, date, member, chunk)

    def test_get_jobs_calls_get_date_for_all_its_dates(self):
        # arrange
        section = 'fake-section'
        dic = {'fake-job3': 'fake'}
        member = 'fake-member'
        chunk = 111
        self.dictionary._dic = {'fake-section': dic}
        self.dictionary._get_date = Mock()

        # act
        returned_jobs = self.dictionary.get_jobs(section, member=member, chunk=chunk)

        # arrange
        self.assertEquals(list(), returned_jobs)
        self.assertEquals(len(self.dictionary._date_list), self.dictionary._get_date.call_count)
        for date in self.dictionary._date_list:
            self.dictionary._get_date.assert_any_call(list(), dic, date, member, chunk)

    def test_create_jobs_once_calls_create_job_and_assign_correctly_its_return_value(self):
        mock_section = Mock()
        mock_section.name = 'fake-section'
        priority = 999
        self.dictionary.build_job = Mock(return_value=mock_section)
        self.job_list.graph.add_node = Mock()

        self.dictionary._create_jobs_once(mock_section.name, priority, Type.BASH, dict())

        self.assertEquals(mock_section, self.dictionary._dic[mock_section.name])
        self.dictionary.build_job.assert_called_once_with(mock_section.name, priority, None, None, None, Type.BASH, {})
        self.job_list.graph.add_node.assert_called_once_with(mock_section.name)


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
