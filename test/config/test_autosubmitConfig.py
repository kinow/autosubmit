from unittest import TestCase
from autosubmit.config.config_common import AutosubmitConfig, BasicConfig
from config.parser_factory import ConfigParserFactory
import datetime


class TestAutosubmitConfig(TestCase):

    def setUp(self):
        BasicConfig.read()
        self.config = AutosubmitConfig('a000', BasicConfig, ConfigParserFactory())
        self.config.reload()

    def getFullPath(self, relativepath):
        return '/home/Earth/jvegas/debug/autosubmit/a000/' + relativepath

    def test_experiment_file(self):
        self.assertEqual(self.config.experiment_file, self.getFullPath('conf/expdef_a000.conf'))

    def test_platforms_file(self):
        self.assertEqual(self.config.platforms_file, self.getFullPath('conf/platforms_a000.conf'))

    def test_project_file(self):
        self.assertEqual(self.config.project_file, self.getFullPath('conf/proj_a000.conf'))

    def test_jobs_file(self):
        self.assertEqual(self.config.jobs_file, self.getFullPath('conf/jobs_a000.conf'))

    def test_get_project_dir(self):
        self.assertEqual(self.config.get_project_dir(), self.getFullPath(BasicConfig.LOCAL_PROJ_DIR + '/'))

    def test_get_wallclock(self):
        self.assertEqual(self.config.get_wallclock('INI'), '00:05')

    def test_get_processors(self):
        self.assertEqual(self.config.get_processors('INI'), 1)

    def test_get_threads(self):
        self.assertEqual(self.config.get_threads('INI'), 1)

    def test_get_tasks(self):
        self.assertEqual(self.config.get_tasks('INI'), 1)

    def test_check_conf_files(self):
        self.assertTrue(self.config.check_conf_files())

    def test__check_autosubmit_conf(self):
        self.assertTrue(self.config._check_autosubmit_conf())

    def test__check_platforms_conf(self):
        self.assertTrue(self.config._check_platforms_conf())

    def test__check_jobs_conf(self):
        self.assertTrue(self.config._check_jobs_conf())

    def test__check_expdef_conf(self):
        self.assertTrue(self.config._check_expdef_conf())

    def test_check_proj(self):
        self.assertTrue(self.config.check_proj())

    def test_reload(self):
        self.config.reload()

    def test_load_parameters(self):
        self.assertDictEqual(self.config.load_parameters(),
                             {'EXPID': 'a000', 'TOTALJOBS': '6', 'PROJECT_REVISION': '', 'RETRIALS': '4',
                              'HPCARCH': 'patata', 'AUTOSUBMIT_VERSION': '3.0.0rc1', 'CALENDAR': 'standard',
                              'CHUNKLIST': '', 'CHUNKSIZE': '4', 'CHUNKSIZEUNIT': 'month', 'DATELIST': '1960',
                              'FILE_PROJECT_CONF': '', 'MAXWAITINGJOBS': '3', 'MEMBERS': 'fc0 fc1',
                              'NUMCHUNKS': '5', 'PROJECT_BRANCH': '', 'PROJECT_COMMIT': '', 'PROJECT_DESTINATION': '',
                              'PROJECT_ORIGIN': '', 'PROJECT_PATH': '', 'PROJECT_TYPE': 'none', 'PROJECT_URL': '',
                              'RERUN': 'FALSE', 'SAFETYSLEEPTIME': '10'})

    def test_load_project_parameters(self):
        self.assertDictEqual(self.config.load_project_parameters(),
                             {})

    def test_print_parameters(self):
        self.config.print_parameters('title', self.config.load_parameters())

    def test_set_expid(self):
        self.config.set_expid('a000')

    def test_get_project_type(self):
        self.assertEqual(self.config.get_project_type(), 'none')

    def test_get_file_project_conf(self):
        self.assertEqual(self.config.get_file_project_conf(), '')

    def test_get_file_jobs_conf(self):
        self.assertEqual(self.config.get_file_jobs_conf(), '')

    def test_get_git_project_origin(self):
        self.assertEqual(self.config.get_git_project_origin(), '')

    def test_get_git_project_branch(self):
        self.assertEqual(self.config.get_git_project_branch(), '')

    def test_get_git_project_commit(self):
        self.assertEqual(self.config.get_git_project_commit(), '')

    def test_get_project_destination(self):
        self.assertEqual(self.config.get_git_project_commit(), '')

    def test_set_git_project_commit(self):
        self.assertEqual(self.config.get_git_project_commit(), '')

    def test_get_svn_project_url(self):
        self.assertEqual(self.config.get_svn_project_url(), '')

    def test_get_svn_project_revision(self):
        self.assertEqual(self.config.get_svn_project_revision(), '')

    def test_get_local_project_path(self):
        self.assertEqual(self.config.get_local_project_path(), '')

    def test_get_date_list(self):
        self.assertEqual(self.config.get_date_list(), [datetime.datetime(1960, 1, 1, 0, 0)])

    def test_get_num_chunks(self):
        self.assertEqual(self.config.get_num_chunks(), 5)

    def test_get_chunk_size_unit(self):
        self.assertEqual(self.config.get_chunk_size_unit(), 'month')

    def test_get_member_list(self):
        self.assertEqual(self.config.get_member_list(), ['fc0', 'fc1'])

    def test_get_rerun(self):
        self.assertEqual(self.config.get_rerun(), 'false')

    def test_get_chunk_list(self):
        self.assertEqual(self.config.get_chunk_list(), '')

    def test_get_platform(self):
        self.assertEqual(self.config.get_platform(), 'patata')

    def test_set_platform(self):
        self.config.set_platform('patata')

    def test_set_version(self):
        self.config.set_version('3.0.0rc1')

    def test_get_total_jobs(self):
        self.assertEqual(self.config.get_total_jobs(), 6)

    def test_get_max_waiting_jobs(self):
        self.assertEqual(self.config.get_max_waiting_jobs(), 3)

    def test_get_safetysleeptime(self):
        self.assertEqual(self.config.get_safetysleeptime(), 10)

    def test_set_safetysleeptime(self):
        self.config.set_safetysleeptime(10)

    def test_get_retrials(self):
        self.assertEqual(self.config.get_retrials(), 4)

    def test_get_parser(self):
        self.assertIsNotNone(self.config.get_parser(ConfigParserFactory(), self.config._exp_parser_file))

    def test_read_platforms_conf(self):
        self.assertEqual(self.config.get_local_project_path(), '')

    def test_get_option(self):
        self.assertEqual(AutosubmitConfig.get_option(self.config._exp_parser, 'git', 'PROJECT_ORIGIN', ''), '')
        self.assertEqual(AutosubmitConfig.get_option(self.config._exp_parser, 'git', 'PROJECT_ORIGIN', 'origin'),
                         '')
        self.assertEqual(AutosubmitConfig.get_option(self.config._exp_parser, 'DEFAULT', 'HPCARCH', ''),
                         'patata')
        self.assertEqual(AutosubmitConfig.get_option(self.config.jobs_parser, 'INI', 'PROCESSORS', 1),
                         1)
        self.assertEqual(AutosubmitConfig.get_option(self.config.jobs_parser, 'INI', 'PROCESSORS', 2),
                         2)

    def test_get_bool_option(self):
        self.assertFalse(AutosubmitConfig.get_bool_option(self.config._exp_parser, 'rerun', 'RERUN', True))

    def test_check_exists(self):
        self.assertFalse(AutosubmitConfig.check_exists(self.config.jobs_parser, 'INI', 'PROCESSORS'))
        self.assertTrue(AutosubmitConfig.check_exists(self.config._exp_parser, 'DEFAULT', 'HPCARCH'))

    def test_check_is_boolean(self):
        self.assertTrue(AutosubmitConfig.check_is_boolean(self.config._exp_parser, 'rerun', 'RERUN', True))
        self.assertFalse(AutosubmitConfig.check_is_boolean(self.config._exp_parser, 'DEFAULT', 'HPCARCH', True))
        self.assertFalse(AutosubmitConfig.check_is_boolean(self.config.jobs_parser, 'INI', 'PROCESSORS', True))
        self.assertTrue(AutosubmitConfig.check_is_boolean(self.config.jobs_parser, 'INI', 'PROCESSORS', False))

    def test_check_is_choice(self):
        self.assertTrue(AutosubmitConfig.check_is_choice(self.config._exp_parser, 'DEFAULT', 'HPCARCH', True,
                                                         ['patata']))
        self.assertTrue(AutosubmitConfig.check_is_choice(self.config.jobs_parser, 'INI', 'PROCESSORS', False,
                                                         ['patata']))
        self.assertFalse(AutosubmitConfig.check_is_choice(self.config.jobs_parser, 'INI', 'PROCESSORS', True,
                                                          ['patata']))

    def test_check_is_int(self):
        self.assertFalse(AutosubmitConfig.check_is_int(self.config.jobs_parser, 'INI', 'PROCESSORS', True))
        self.assertTrue(AutosubmitConfig.check_is_int(self.config.jobs_parser, 'SIM', 'PROCESSORS', True))

    # def test_check_regex(self):
    #     self.fail()
    #
    # def test_check_json(self):
    #     self.fail()
