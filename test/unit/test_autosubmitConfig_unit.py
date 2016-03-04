from unittest import TestCase
from unittest import skip
from autosubmit.config.config_common import AutosubmitConfig
from autosubmit.config.parser_factory import ConfigParserFactory
from mock import Mock
from mock import patch
from mock import mock_open
import os

try:
    # noinspection PyCompatibility
    from configparser import SafeConfigParser
except ImportError:
    # noinspection PyCompatibility
    from ConfigParser import SafeConfigParser

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

        parser_mock = Mock(spec=SafeConfigParser)
        parser_mock.read = Mock()

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        # act
        returned_parser = AutosubmitConfig.get_parser(factory_mock, file_path)

        # assert
        self.assertTrue(isinstance(returned_parser, SafeConfigParser))
        factory_mock.create_parser.assert_called_with()
        parser_mock.read.assert_called_with(file_path)

    def test_get_option(self):
        # arrange
        section = 'any-section'
        option = 'any-option'
        default = 'dummy-default'
        option_value = 'dummy-value'

        parser_mock = self._create_parser_mock(True, option_value)

        # act
        returned_option = AutosubmitConfig.get_option(parser_mock, section, option, default)

        # assert
        parser_mock.has_option.assert_called_once_with(section, option)
        self.assertTrue(isinstance(returned_option, str))
        self.assertNotEqual(default, returned_option)
        self.assertEqual(option_value, returned_option)

    def test_get_option_case_default(self):
        # arrange
        section = 'any-section'
        option = 'any-option'
        default = 'dummy-default'

        parser_mock = self._create_parser_mock(False)

        # act
        returned_option = AutosubmitConfig.get_option(parser_mock, section, option, default)

        # assert
        parser_mock.has_option.assert_called_once_with(section, option)
        self.assertTrue(isinstance(returned_option, str))
        self.assertEqual(default, returned_option)

    def test_experiment_file(self):
        self.assertEqual(self.config.experiment_file,
                         os.path.join(FakeBasicConfig.LOCAL_ROOT_DIR, self.any_expid, "conf",
                                             "expdef_" + self.any_expid + ".conf"))

    def test_platforms_parser(self):
        self.assertTrue(isinstance(self.config.platforms_parser, SafeConfigParser))

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

    @skip("pending refactor")
    def test_get_project_dir(self):
        self.assertEqual(self.config.get_project_dir(),
                         os.path.join(FakeBasicConfig.LOCAL_ROOT_DIR, self.any_expid, FakeBasicConfig.LOCAL_PROJ_DIR,
                                     self.config.get_project_destination()))

    def test_get_wallclock(self):
        # arrange
        expected_value = '00:05'
        config, parser_mock = self._arrange_config(expected_value)
        # act
        returned_value = config.get_wallclock(self.section)
        # assert
        self._assert_get_option(parser_mock, 'WALLCLOCK', expected_value, returned_value, str)

    def test_get_processors(self):
        # arrange
        expected_value = 99999
        config, parser_mock = self._arrange_config(expected_value)
        # act
        returned_value = config.get_processors(self.section)
        # assert
        self._assert_get_option(parser_mock, 'PROCESSORS', expected_value, returned_value, int)

    def test_get_threads(self):
        # arrange
        expected_value = 99999
        config, parser_mock = self._arrange_config(expected_value)
        # act
        returned_value = config.get_threads(self.section)
        # assert
        self._assert_get_option(parser_mock, 'THREADS', expected_value, returned_value, int)

    def test_get_tasks(self):
        # arrange
        expected_value = 99999
        config, parser_mock = self._arrange_config(expected_value)
        # act
        returned_value = config.get_tasks(self.section)
        # assert
        self._assert_get_option(parser_mock, 'TASKS', expected_value, returned_value, int)

    def test_get_memory(self):
        # arrange
        expected_value = 99999
        config, parser_mock = self._arrange_config(expected_value)
        # act
        returned_value = config.get_memory(self.section)
        # assert
        self._assert_get_option(parser_mock, 'MEMORY', expected_value, returned_value, int)

    def test_check_exists_case_true(self):
        # arrange
        parser_mock = self._create_parser_mock(True)
        # act
        exists = AutosubmitConfig.check_exists(parser_mock, self.section, self.option)
        # assert
        parser_mock.has_option.assert_called_once_with(self.section, self.option)
        self.assertTrue(exists)

    def test_check_exists_case_false(self):
        # arrange
        parser_mock = self._create_parser_mock(False)
        # act
        exists = AutosubmitConfig.check_exists(parser_mock, self.section, self.option)
        # assert
        parser_mock.has_option.assert_called_once_with(self.section, self.option)
        self.assertFalse(exists)

    def test_that_reload_must_load_parsers(self):
        # arrange
        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, ConfigParserFactory())
        parsers = ['_conf_parser', '_platforms_parser', 'jobs_parser', '_exp_parser', '_proj_parser']

        # pre-act assertions
        for parser in parsers:
            self.assertFalse(hasattr(config, parser))

        # act
        config.reload()

        # assert
        # TODO: could be improved asserting that the methods are called
        for parser in parsers:
            self.assertTrue(hasattr(config, parser))
            self.assertTrue(isinstance(getattr(config, parser), SafeConfigParser))

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

    #############################
    ## Helper functions & classes

    def _assert_get_option(self, parser_mock, option, expected_value, returned_value, expected_type):
        self.assertTrue(isinstance(returned_value, expected_type))
        self.assertEqual(expected_value, returned_value)
        parser_mock.has_option.assert_called_once_with(self.section, option)

    def _arrange_config(self, option_value):
        # arrange
        parser_mock = Mock(spec=SafeConfigParser)
        parser_mock.has_option = Mock(return_value=True)
        parser_mock.get = Mock(return_value=option_value)
        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)
        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()
        return config, parser_mock

    def _create_parser_mock(self, has_option, returned_option=None):
        parser_mock = Mock(spec=SafeConfigParser)
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