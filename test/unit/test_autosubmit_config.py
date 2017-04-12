from unittest import TestCase
from autosubmit.config.config_common import AutosubmitConfig
from bscearth.utils.config_parser import ConfigParserFactory, ConfigParser
from mock import Mock
from mock import patch
from mock import mock_open
import os
import sys
from datetime import datetime

# compatibility with both versions (2 & 3)
from sys import version_info

if version_info.major == 2:
    import __builtin__ as builtins
else:
    import builtins


class TestAutosubmitConfig(TestCase):
    any_expid = 'a000'

    # dummy values for tests
    section = 'any-section'
    option = 'any-option'

    def setUp(self):
        self.config = AutosubmitConfig(self.any_expid, FakeBasicConfig, ConfigParserFactory())
        self.config.reload()

    def test_get_parser(self):
        # arrange
        file_path = 'dummy/file/path'

        parser_mock = Mock(spec=ConfigParser)
        parser_mock.read = Mock()

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        # act
        returned_parser = AutosubmitConfig.get_parser(factory_mock, file_path)

        # assert
        self.assertTrue(isinstance(returned_parser, ConfigParser))
        factory_mock.create_parser.assert_called_with()
        parser_mock.read.assert_called_with(file_path)

    def test_experiment_file(self):
        self.assertEqual(self.config.experiment_file,
                         os.path.join(FakeBasicConfig.LOCAL_ROOT_DIR, self.any_expid, "conf",
                                      "expdef_" + self.any_expid + ".conf"))

    def test_platforms_parser(self):
        self.assertTrue(isinstance(self.config.platforms_parser, ConfigParser))

    def test_platforms_file(self):
        self.assertEqual(self.config.platforms_file,
                         os.path.join(FakeBasicConfig.LOCAL_ROOT_DIR, self.any_expid, "conf",
                                      "platforms_" + self.any_expid + ".conf"))

    def test_project_file(self):
        self.assertEqual(self.config.project_file,
                         os.path.join(FakeBasicConfig.LOCAL_ROOT_DIR, self.any_expid, "conf",
                                      "proj_" + self.any_expid + ".conf"))

    def test_jobs_file(self):
        self.assertEqual(self.config.jobs_file,
                         os.path.join(FakeBasicConfig.LOCAL_ROOT_DIR, self.any_expid, "conf",
                                      "jobs_" + self.any_expid + ".conf"))

    def test_get_project_dir(self):
        parser_mock = Mock(spec=ConfigParser)
        parser_mock.get = Mock(side_effect=['/dummy/path'])

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()

        # act
        returned_project_dir = config.get_project_dir()

        # assert
        self.assertEquals(os.path.join(FakeBasicConfig.LOCAL_ROOT_DIR, self.any_expid, FakeBasicConfig.LOCAL_PROJ_DIR,
                                       '/dummy/path'), returned_project_dir)

    def test_get_wallclock(self):
        # arrange
        expected_value = '00:05'
        default_value = ''
        config, parser_mock = self._arrange_config(expected_value)
        # act
        returned_value = config.get_wallclock(self.section)
        # assert
        self._assert_get_option(parser_mock, 'WALLCLOCK', expected_value, returned_value, default_value, str)

    def test_get_processors(self):
        # arrange
        expected_value = '99999'
        default_value = 1
        config, parser_mock = self._arrange_config(expected_value)
        # act
        returned_value = config.get_processors(self.section)
        # assert
        self._assert_get_option(parser_mock, 'PROCESSORS', expected_value, returned_value, default_value, str)

    def test_get_threads(self):
        # arrange
        expected_value = '99999'
        default_value = 1
        config, parser_mock = self._arrange_config(expected_value)
        # act
        returned_value = config.get_threads(self.section)
        # assert
        self._assert_get_option(parser_mock, 'THREADS', expected_value, returned_value, default_value, str)

    def test_get_tasks(self):
        # arrange
        expected_value = '99999'
        default_value = 0
        config, parser_mock = self._arrange_config(expected_value)
        # act
        returned_value = config.get_tasks(self.section)
        # assert
        self._assert_get_option(parser_mock, 'TASKS', expected_value, returned_value, default_value, str)

    def test_get_memory(self):
        # arrange
        expected_value = '99999'
        default_value = ''
        config, parser_mock = self._arrange_config(expected_value)
        # act
        returned_value = config.get_memory(self.section)
        # assert
        self._assert_get_option(parser_mock, 'MEMORY', expected_value, returned_value, default_value, str)

    def test_that_reload_must_load_parsers(self):
        # arrange
        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, ConfigParserFactory())
        parsers = ['_conf_parser', '_platforms_parser', '_jobs_parser', '_exp_parser', '_proj_parser']

        # pre-act assertions
        for parser in parsers:
            self.assertTrue(hasattr(config, parser))
            self.assertIsNone(getattr(config, parser))

        # act
        config.reload()

        # assert
        # TODO: could be improved asserting that the methods are called
        for parser in parsers:
            self.assertTrue(hasattr(config, parser))
            self.assertTrue(isinstance(getattr(config, parser), ConfigParser))

    def test_set_expid(self):
        # arrange
        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, ConfigParserFactory())

        open_mock = mock_open(read_data="EXPID = dummy")
        with patch.object(builtins, "open", open_mock):
            # act
            config.set_expid('dummy-expid')

        # assert
        open_mock.assert_any_call(config.experiment_file, 'w')
        open_mock.assert_any_call(getattr(config, '_conf_parser_file'), 'w')

    def test_set_platform(self):
        # arrange
        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, ConfigParserFactory())

        open_mock = mock_open(read_data="HPCARCH = dummy")
        with patch.object(builtins, "open", open_mock):
            # act
            config.set_platform('dummy-platform')

        # assert
        open_mock.assert_any_call(config.experiment_file, 'w')

    def test_set_version(self):
        # arrange
        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, ConfigParserFactory())

        open_mock = mock_open(read_data='AUTOSUBMIT_VERSION = dummy')
        with patch.object(builtins, "open", open_mock):
            # act
            config.set_version('dummy-vesion')

        # assert
        open_mock.assert_any_call(getattr(config, '_conf_parser_file'), 'w')

    def test_set_safetysleeptime(self):
        # arrange
        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, ConfigParserFactory())

        open_mock = mock_open(read_data='SAFETYSLEEPTIME = dummy')
        with patch.object(builtins, "open", open_mock):
            # act
            config.set_safetysleeptime(999999)

        # assert
        open_mock.assert_any_call(getattr(config, '_conf_parser_file'), 'w')

    def test_load_project_parameters(self):
        # arrange
        parser_mock = Mock(spec=ConfigParser)
        parser_mock.sections = Mock(return_value=['DUMMY_SECTION_1', 'DUMMY_SECTION_2'])
        parser_mock.items = Mock(side_effect=[[['dummy_key1', 'dummy_value1'], ['dummy_key2', 'dummy_value2']],
                                              [['dummy_key3', 'dummy_value3'], ['dummy_key4', 'dummy_value4']]])

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()

        # act
        project_parameters = config.load_project_parameters()

        # assert
        parser_mock.items.assert_any_call('DUMMY_SECTION_1')
        parser_mock.items.assert_any_call('DUMMY_SECTION_2')
        self.assertEquals(4, len(project_parameters))
        for i in range(1, 4):
            self.assertEquals(project_parameters.get('dummy_key' + str(i)), 'dummy_value' + str(i))

    def test_get_startdates_list(self):
        # arrange
        parser_mock = Mock(spec=ConfigParser)
        # TODO: Check if these are all accepted formats
        parser_mock.get = Mock(return_value='1920 193005 19400909 1950[01 0303]')

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()

        # act
        returned_dates = config.get_date_list()

        # assert
        self.assertEquals(5, len(returned_dates))
        self.assertTrue(datetime(1920, 1, 1) in returned_dates)
        self.assertTrue(datetime(1930, 5, 1) in returned_dates)
        self.assertTrue(datetime(1940, 9, 9) in returned_dates)
        self.assertTrue(datetime(1950, 1, 1) in returned_dates)
        self.assertTrue(datetime(1950, 3, 3) in returned_dates)

    def test_check_project(self):
        # arrange
        parser_mock = Mock(spec=ConfigParser)
        parser_mock.read = Mock(side_effect=Exception)

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, ConfigParserFactory())
        config2 = AutosubmitConfig(self.any_expid, FakeBasicConfig, ConfigParserFactory())
        config3 = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)

        config._proj_parser_file = ''

        # act
        should_be_true = config.check_proj()
        should_be_true2 = config2.check_proj()
        should_be_false = config3.check_proj()

        # assert
        self.assertTrue(should_be_true)
        self.assertEquals(None, config._proj_parser)
        self.assertTrue(should_be_true2)
        self.assertFalse(should_be_false)

    def test_load_parameters(self):
        # arrange
        parser_mock = Mock(spec=ConfigParser)
        parser_mock.sections = Mock(side_effect=[['dummy-section1'], ['dummy-section2'], ['dummy-section3']])

        parser_mock.options = Mock(side_effect=[['dummy-option1', 'dummy-option2'],
                                                ['dummy-option3', 'dummy-option4']])

        parser_mock.get = Mock(return_value='dummy-value')

        parser_mock.items = Mock(return_value=[['dummy-key1', 'dummy-value1'],
                                               ['dummy-key2', 'dummy-value2']])

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()

        # act
        returned_parameters = config.load_parameters()

        # assert
        self.assertEquals(6, len(returned_parameters))
        self.assertTrue(returned_parameters.has_key('dummy-option1'))
        self.assertTrue(returned_parameters.has_key('dummy-option2'))
        self.assertTrue(returned_parameters.has_key('dummy-option3'))
        self.assertTrue(returned_parameters.has_key('dummy-option4'))
        self.assertTrue(returned_parameters.has_key('dummy-key1'))
        self.assertTrue(returned_parameters.has_key('dummy-key2'))

    def test_git_project_commit(self):
        # arrange
        # noinspection PyPep8Naming
        sys.modules['subprocess'].CalledProcessError = Exception
        sys.modules['subprocess'].check_output = Mock(side_effect=[Exception,
                                                                   'dummy/path/', Exception,
                                                                   'dummy/path/', 'dummy/sha/'])
        parser_mock = Mock(spec=ConfigParser)

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()

        # TODO: reorganize act & improve the assertions
        should_be_false = config.set_git_project_commit(config)
        should_be_false2 = config.set_git_project_commit(config)

        open_mock = mock_open(read_data='PROJECT_BRANCH = dummy \n PROJECT_COMMIT = dummy')
        with patch.object(builtins, "open", open_mock):
            # act
            should_be_true = config.set_git_project_commit(config)

            # assert
            self.assertTrue(should_be_true)

        self.assertFalse(should_be_false)
        self.assertFalse(should_be_false2)

    # TODO: Test specific cases
    def test_check_jobs_conf(self):
        # arrange
        parser_mock = Mock(spec=ConfigParser)
        parser_mock.sections = Mock(side_effect=[['dummy-section1', 'dummy-section2'],
                                                 ['dummy-platform1', 'dummy-platform2']])
        parser_mock.has = Mock(return_value=True)

        parser_mock.get = Mock(side_effect=['true', 'dummy-platform1', 'dependency-1 dependency-2',
                                            'dependency-1 dependency-2', 'once',
                                            'true', 'dummy-platform1', 'dependency-1 dependency-2',
                                            'dependency-1 dependency-2', 'once'])

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()

        # act
        should_be_true = config.check_jobs_conf()

        # assert
        self.assertTrue(should_be_true)

    # TODO: Test specific cases
    def test_check_platforms_conf(self):
        # arrange
        parser_mock = Mock(spec=ConfigParser)
        parser_mock.sections = Mock(side_effect=[[], [], ['dummy-section1'], ['dummy-section1', 'dummy-section2']])
        parser_mock.has = Mock(return_value=True)

        parser_mock.get = Mock(side_effect=['not-ps', 'true', 'false', 111, 222,
                                            'not-ps', 'true', 'false', 111, 222])

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()

        # act
        should_be_true = config.check_platforms_conf()

        # assert
        self.assertTrue(should_be_true)

    def test_check_conf_files(self):
        # arrange
        truth_mock = Mock(return_value=True)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, ConfigParserFactory())
        config.reload()
        config.check_autosubmit_conf = truth_mock
        config.check_platforms_conf = truth_mock
        config.check_jobs_conf = truth_mock
        config.check_expdef_conf = truth_mock

        config2 = AutosubmitConfig(self.any_expid, FakeBasicConfig, ConfigParserFactory())
        config2.reload()
        config2.check_autosubmit_conf = truth_mock
        config2.check_platforms_conf = truth_mock
        config2.check_jobs_conf = truth_mock
        config2.check_expdef_conf = Mock(return_value=False)

        # act
        should_be_true = config.check_conf_files()
        should_be_false = config2.check_conf_files()

        # assert
        self.assertTrue(should_be_true)
        self.assertFalse(should_be_false)
        self.assertEquals(7, truth_mock.call_count)

    def test_is_valid_mail_with_non_mail_address_returns_false(self):
        self.assertFalse(AutosubmitConfig.is_valid_mail_address('12345'))

    def test_is_valid_mail_with_mail_address_returns_true(self):
        self.assertTrue(AutosubmitConfig.is_valid_mail_address('example@example.org'))

    #############################
    ## Helper functions & classes

    def _assert_get_option(self, parser_mock, option, expected_value, returned_value, default_value, expected_type):
        self.assertTrue(isinstance(returned_value, expected_type))
        self.assertEqual(expected_value, returned_value)
        parser_mock.get_option.assert_called_once_with(self.section, option, default_value)

    def _arrange_config(self, option_value):
        # arrange
        parser_mock = Mock(spec=ConfigParser)
        parser_mock.has_option = Mock(return_value=True)
        parser_mock.get = Mock(return_value=option_value)
        parser_mock.get_option = Mock(return_value=option_value)
        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)
        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()
        return config, parser_mock

    def _create_parser_mock(self, has_option, returned_option=None):
        parser_mock = Mock(spec=ConfigParser)
        parser_mock.has_option = Mock(return_value=has_option)
        parser_mock.get = Mock(return_value=returned_option)
        return parser_mock


class FakeBasicConfig:
    DB_DIR = '/dummy/db/dir'
    DB_FILE = '/dummy/db/file'
    DB_PATH = '/dummy/db/path'
    LOCAL_ROOT_DIR = '/dummy/local/root/dir'
    LOCAL_TMP_DIR = '/dummy/local/temp/dir'
    LOCAL_PROJ_DIR = '/dummy/local/proj/dir'
    DEFAULT_PLATFORMS_CONF = ''
    DEFAULT_JOBS_CONF = ''
