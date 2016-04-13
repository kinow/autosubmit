from unittest import TestCase

from mock import Mock

from autosubmit.config.parser_factory import ConfigParserFactory
from autosubmit.job.job_list import DicJobs
from autosubmit.job.job_list import JobList


class TestDicJobs(TestCase):
    def setUp(self):
        self.experiment_id = 'random-id'
        self.job_list = JobList(self.experiment_id, FakeBasicConfig, ConfigParserFactory())
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
        self.dictionary.read_section(section, priority)

        # assert
        self.dictionary._create_jobs_once.assert_called_once_with(section, priority)
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
        self.dictionary.read_section(section, priority)

        # assert
        self.dictionary._create_jobs_once.assert_not_called()
        self.dictionary._create_jobs_startdate.assert_called_once_with(section, priority, frequency)
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
        self.dictionary.read_section(section, priority)

        # assert
        self.dictionary._create_jobs_once.assert_not_called()
        self.dictionary._create_jobs_startdate.assert_not_called()
        self.dictionary._create_jobs_member.assert_called_once_with(section, priority, frequency)
        self.dictionary._create_jobs_chunk.assert_not_called()

    def test_read_section_running_chunk_create_jobs_chunk(self):
        # arrange
        section = 'fake-section'
        priority = 999
        frequency = 123
        self.parser_mock.has_option = Mock(return_value=True)
        self.parser_mock.get = Mock(return_value='chunk')
        self.dictionary.get_option = Mock(return_value=frequency)
        self.dictionary._create_jobs_once = Mock()
        self.dictionary._create_jobs_startdate = Mock()
        self.dictionary._create_jobs_member = Mock()
        self.dictionary._create_jobs_chunk = Mock()

        # act
        self.dictionary.read_section(section, priority)

        # assert
        self.dictionary._create_jobs_once.assert_not_called()
        self.dictionary._create_jobs_startdate.assert_not_called()
        self.dictionary._create_jobs_member.assert_not_called()
        self.dictionary._create_jobs_chunk.assert_called_once_with(section, priority, frequency)

    def test_dic_create_right_jobs_by_startdate(self):
        # arrange
        section = 'fake-section'
        priority = 999
        frequency = 1
        self.dictionary._create_job = Mock(return_value='created_job')

        # act
        self.dictionary._create_jobs_startdate(section, priority, frequency)

        # assert
        self.assertEquals(len(self.dictionary._dic[section]), len(self.date_list))

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
