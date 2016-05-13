from unittest import TestCase
from autosubmit.config.config_common import AutosubmitConfig
from autosubmit.config.parser_factory import ConfigParserFactory
from mock import Mock
from mock import patch
from mock import mock_open
import os
import sys
from datetime import datetime

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

    def test_get_project_dir(self):
        parser_mock = Mock(spec=SafeConfigParser)
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
        parser_mock = Mock(spec=SafeConfigParser)
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

    def test_check_json(self):
        # arrange
        valid_json = '[it_is_a_sample", "true]'
        invalid_json = '{[[dummy]random}'

        # act
        should_be_true = AutosubmitConfig.check_json('random_key', valid_json)
        should_be_false = AutosubmitConfig.check_json('random_key', invalid_json)

        # assert
        self.assertTrue(should_be_true)
        self.assertFalse(should_be_false)

    def test_check_is_int(self):
        # arrange
        section = 'any-section'
        option = 'any-option'

        parser_mock = Mock(spec=SafeConfigParser)
        parser_mock.has_option = Mock(side_effect=[False, True, True, False])
        parser_mock.get = Mock(side_effect=['123', 'dummy'])

        # act
        should_be_true = AutosubmitConfig.check_is_int(parser_mock, section, option, False)
        should_be_true2 = AutosubmitConfig.check_is_int(parser_mock, section, option, False)
        should_be_false = AutosubmitConfig.check_is_int(parser_mock, section, option, False)
        should_be_false2 = AutosubmitConfig.check_is_int(parser_mock, section, option, True)

        # assert
        self.assertTrue(should_be_true)
        self.assertTrue(should_be_true2)
        self.assertFalse(should_be_false)
        self.assertFalse(should_be_false2)

    def test_check_is_boolean(self):
        # arrange
        section = 'any-section'
        option = 'any-option'

        parser_mock = Mock(spec=SafeConfigParser)
        parser_mock.has_option = Mock(side_effect=[False, True, True, False])
        parser_mock.get = Mock(side_effect=['True', 'dummy'])

        # act
        should_be_true = AutosubmitConfig.check_is_boolean(parser_mock, section, option, False)
        should_be_true2 = AutosubmitConfig.check_is_boolean(parser_mock, section, option, False)
        should_be_false = AutosubmitConfig.check_is_boolean(parser_mock, section, option, False)
        should_be_false2 = AutosubmitConfig.check_is_boolean(parser_mock, section, option, True)

        # assert
        self.assertTrue(should_be_true)
        self.assertTrue(should_be_true2)
        self.assertFalse(should_be_false)
        self.assertFalse(should_be_false2)

    def test_check_regex(self):
        # arrange
        section = 'any-section'
        option = 'any-option'

        parser_mock = Mock(spec=SafeConfigParser)
        parser_mock.has_option = Mock(side_effect=[False, False, True, True, True, True, False, True, True, True, True])
        parser_mock.get = Mock(side_effect=['dummy-value', '999999', 'dummy-value', 'dummy-value', '999999'])

        # act
        # TODO: unexpected logic?
        should_be_false = AutosubmitConfig.check_regex(parser_mock, section, option, False, 'dummy-regex')
        should_be_true = AutosubmitConfig.check_regex(parser_mock, section, option, False, '[0-9]')
        should_be_false2 = AutosubmitConfig.check_regex(parser_mock, section, option, False, 'dummy-regex')
        should_be_true2 = AutosubmitConfig.check_regex(parser_mock, section, option, False, '[0-9]*')

        should_be_false3 = AutosubmitConfig.check_regex(parser_mock, section, option, True, 'dummy-regex')
        should_be_false4 = AutosubmitConfig.check_regex(parser_mock, section, option, True, 'dummy-regex')
        should_be_true3 = AutosubmitConfig.check_regex(parser_mock, section, option, True, '[0-9]*')

        # assert
        self.assertFalse(should_be_false)
        self.assertFalse(should_be_false2)
        self.assertFalse(should_be_false3)
        self.assertFalse(should_be_false4)

        self.assertTrue(should_be_true)
        self.assertTrue(should_be_true2)
        self.assertTrue(should_be_true3)

    def test_check_is_choice(self):
        # arrange
        section = 'any-section'
        option = 'any-option'
        choices = ['dummy-choice1', 'dummy-choice2']

        parser_mock = Mock(spec=SafeConfigParser)
        parser_mock.has_option = Mock(side_effect=[False, True, True, False])
        parser_mock.get = Mock(side_effect=[choices[1], 'not-a-choice'])

        # act
        should_be_true = AutosubmitConfig.check_is_choice(parser_mock, section, option, False, choices)
        should_be_true2 = AutosubmitConfig.check_is_choice(parser_mock, section, option, False, choices)
        should_be_false = AutosubmitConfig.check_is_choice(parser_mock, section, option, False, choices)
        should_be_false2 = AutosubmitConfig.check_is_choice(parser_mock, section, option, True, choices)

        # assert
        self.assertTrue(should_be_true)
        self.assertTrue(should_be_true2)
        self.assertFalse(should_be_false)
        self.assertFalse(should_be_false2)

    def test_get_bool_option(self):
        # arrange
        section = 'any-section'
        option = 'any-option'

        parser_mock = Mock(spec=SafeConfigParser)
        parser_mock.has_option = Mock(side_effect=[True, True, False, False])
        parser_mock.get = Mock(side_effect=['false', 'true'])

        # act
        should_be_false = AutosubmitConfig.get_bool_option(parser_mock, section, option, True)
        should_be_true = AutosubmitConfig.get_bool_option(parser_mock, section, option, False)

        should_be_false2 = AutosubmitConfig.get_bool_option(parser_mock, section, option, False)
        should_be_true2 = AutosubmitConfig.get_bool_option(parser_mock, section, option, True)

        # assert
        self.assertTrue(should_be_true)
        self.assertTrue(should_be_true2)

        self.assertFalse(should_be_false)
        self.assertFalse(should_be_false2)

    def test_get_startdates_list(self):
        # arrange
        parser_mock = Mock(spec=SafeConfigParser)
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

    def test_get_project_destination(self):
        # arrange
        parser_mock = Mock(spec=SafeConfigParser)
        parser_mock.get = Mock(side_effect=['/dummy/path',
                                            None, 'local', '/dummy/local/local-path',
                                            None, 'svn', 'svn', '/dummy/svn/svn-path',
                                            None, 'git', 'git', 'git', '/dummy/git/git-path.git'])

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()

        # act
        returned_project_destination = config.get_project_destination()
        returned_project_destination_local = config.get_project_destination()
        returned_project_destination_svn = config.get_project_destination()
        returned_project_destination_git = config.get_project_destination()

        # assert
        self.assertEquals('/dummy/path', returned_project_destination)
        self.assertEquals('local-path', returned_project_destination_local)
        self.assertEquals('svn-path', returned_project_destination_svn)
        self.assertEquals('git-path', returned_project_destination_git)

    def test_check_project(self):
        # arrange
        parser_mock = Mock(spec=SafeConfigParser)
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

    def test_get_some_properties(self):
        # arrange
        properties = {'RETRIALS': '111', 'SAFETYSLEEPTIME': '222', 'MAXWAITINGJOBS': '333',
                        'TOTALJOBS': '444', 'FILE_PROJECT_CONF': '/dummy/path', 'FILE_JOBS_CONF': '/dummy/object',
                        'PROJECT_BRANCH': 'dummy/branch', 'PROJECT_COMMIT': 'dummy/commit',
                        'PROJECT_REVISION': 'dummy/revision', 'NUMCHUNKS': '999', 'CHUNKSIZEUNIT': '9999',
                        'MEMBERS': 'MEMBER1 MEMBER2', 'RERUN': 'dummy/rerun', 'CHUNKLIST': 'dummy/chunklist',
                        'HPCARCH': 'dummy/hpcarch'}

        # TODO: Improve making properties as a dict of dicts (for section)
        def get_option(section, option):
            return properties[option]

        parser_mock = Mock(spec=SafeConfigParser)
        parser_mock.has = Mock(return_value=True)
        parser_mock.get = Mock(side_effect=get_option)

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()

        # act
        returned_retrials = config.get_retrials()
        returned_safetysleeptime = config.get_safetysleeptime()
        returned_max_jobs = config.get_max_waiting_jobs()
        returned_total_jobs = config.get_total_jobs()
        returned_file_project = config.get_file_project_conf()
        returned_file_jobs = config.get_file_jobs_conf()
        returned_branch = config.get_git_project_branch()
        returned_commit = config.get_git_project_commit()
        returned_revision = config.get_svn_project_revision()
        returned_num_chunks = config.get_num_chunks()
        returned_chunk_size_unit = config.get_chunk_size_unit()
        returned_member_list = config.get_member_list()
        returned_rerun = config.get_rerun()
        returned_chunk_list = config.get_chunk_list()
        returned_platform = config.get_platform()

        # assert
        self.assertEquals(int(properties['RETRIALS']), returned_retrials)
        self.assertEquals(int(properties['SAFETYSLEEPTIME']), returned_safetysleeptime)
        self.assertEquals(int(properties['MAXWAITINGJOBS']), returned_max_jobs)
        self.assertEquals(int(properties['TOTALJOBS']), returned_total_jobs)
        self.assertEquals(properties['FILE_PROJECT_CONF'], returned_file_project)
        self.assertEquals(properties['FILE_JOBS_CONF'], returned_file_jobs)
        self.assertEquals(properties['PROJECT_BRANCH'], returned_branch)
        self.assertEquals(properties['PROJECT_COMMIT'], returned_commit)
        self.assertEquals(properties['PROJECT_REVISION'], returned_revision)
        self.assertEquals(int(properties['NUMCHUNKS']), returned_num_chunks)
        self.assertEquals(properties['CHUNKSIZEUNIT'], returned_chunk_size_unit)
        self.assertEquals(properties['MEMBERS'].split(' '), returned_member_list)
        self.assertEquals(properties['RERUN'], returned_rerun)
        self.assertEquals(properties['CHUNKLIST'], returned_chunk_list)
        self.assertEquals(properties['HPCARCH'], returned_platform)

    def test_load_parameters(self):
        # arrange
        parser_mock = Mock(spec=SafeConfigParser)
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
        parser_mock = Mock(spec=SafeConfigParser)

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

    def test_check_autosubmit_conf(self):
        # arrange

        parser_mock = Mock(spec=SafeConfigParser)
        parser_mock.read = Mock()
        parser_mock.has = Mock(return_value=True)

        parser_mock.get = Mock(side_effect=[1111, 2222, 3333, 4444, 'True', 'True', 'example@test.org',
                                            1111, 2222, 3333, 'no-int', 'True', 'True', 'example@test.org'])

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()

        # act
        should_be_true = config._check_autosubmit_conf()
        should_be_false = config._check_autosubmit_conf()

        # arrange
        self.assertTrue(should_be_true)
        self.assertFalse(should_be_false)

    # TODO: Test other CVS cases
    def test_check_expdef_conf(self):
        # arrange
        parser_mock = Mock(spec=SafeConfigParser)
        parser_mock.read = Mock()
        parser_mock.has = Mock(return_value=True)

        parser_mock.get = Mock(side_effect=['year', 111, 222, 'standard', 'True', 'git', 'git',
                                            'year', 111, 'not-a-number', 'standard', 'True', 'none', 'none'])

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()

        # act
        should_be_true = config._check_expdef_conf()
        should_be_false = config._check_expdef_conf()

        # assert
        self.assertTrue(should_be_true)
        self.assertFalse(should_be_false)

    # TODO: Test specific cases
    def test_check_jobs_conf(self):
        # arrange
        parser_mock = Mock(spec=SafeConfigParser)
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
        should_be_true = config._check_jobs_conf()

        # assert
        self.assertTrue(should_be_true)

    # TODO: Test specific cases
    def test_check_platforms_conf(self):
        # arrange
        parser_mock = Mock(spec=SafeConfigParser)
        parser_mock.sections = Mock(side_effect=[[], [], ['dummy-section1'], ['dummy-section1', 'dummy-section2']])
        parser_mock.has = Mock(return_value=True)

        parser_mock.get = Mock(side_effect=['not-ps', 'true', 'false', 111, 222,
                                            'not-ps', 'true', 'false', 111, 222])

        factory_mock = Mock(spec=ConfigParserFactory)
        factory_mock.create_parser = Mock(return_value=parser_mock)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, factory_mock)
        config.reload()

        # act
        should_be_true = config._check_platforms_conf()

        # assert
        self.assertTrue(should_be_true)

    def test_check_conf_files(self):
        # arrange
        truth_mock = Mock(return_value=True)

        config = AutosubmitConfig(self.any_expid, FakeBasicConfig, ConfigParserFactory())
        config.reload()
        config._check_autosubmit_conf = truth_mock
        config._check_platforms_conf = truth_mock
        config._check_jobs_conf = truth_mock
        config._check_expdef_conf = truth_mock

        config2 = AutosubmitConfig(self.any_expid, FakeBasicConfig, ConfigParserFactory())
        config2.reload()
        config2._check_autosubmit_conf = truth_mock
        config2._check_platforms_conf = truth_mock
        config2._check_jobs_conf = truth_mock
        config2._check_expdef_conf = Mock(return_value=False)

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
