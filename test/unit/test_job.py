import datetime
import inspect
import os
import sys
import tempfile
from pathlib import Path
# compatibility with both versions (2 & 3)
from sys import version_info
from textwrap import dedent
from unittest import TestCase

from autosubmitconfigparser.config.configcommon import AutosubmitConfig
from autosubmitconfigparser.config.configcommon import BasicConfig, YAMLParserFactory
from mock import Mock, MagicMock
from mock import patch

from autosubmit.autosubmit import Autosubmit
from autosubmit.job.job import Job
from autosubmit.job.job_common import Status
from autosubmit.job.job_list import JobList
from autosubmit.platforms.platform import Platform

if version_info.major == 2:
    import builtins as builtins
else:
    import builtins


class TestJob(TestCase):
    def setUp(self):
        self.experiment_id = 'random-id'
        self.job_name = 'random-name'
        self.job_id = 999
        self.job_priority = 0
        self.as_conf = Mock()
        self.as_conf.experiment_data = dict()
        self.as_conf.experiment_data["JOBS"] = dict()
        self.as_conf.jobs_data = self.as_conf.experiment_data["JOBS"]
        self.as_conf.experiment_data["PLATFORMS"] = dict()
        self.job = Job(self.job_name, self.job_id, Status.WAITING, self.job_priority)
        self.job.processors = 2
        self.as_conf.load_project_parameters = Mock(return_value=dict())


    def test_when_the_job_has_more_than_one_processor_returns_the_parallel_platform(self):
        platform = Platform(self.experiment_id, 'parallel-platform', FakeBasicConfig().props())
        platform.serial_platform = 'serial-platform'

        self.job._platform = platform
        self.job.processors = 999

        returned_platform = self.job.platform

        self.assertEqual(platform, returned_platform)

    def test_when_the_job_has_only_one_processor_returns_the_serial_platform(self):
        platform = Platform(self.experiment_id, 'parallel-platform', FakeBasicConfig().props())
        platform.serial_platform = 'serial-platform'

        self.job._platform = platform
        self.job.processors = 1

        returned_platform = self.job.platform

        self.assertEqual('serial-platform', returned_platform)

    def test_set_platform(self):
        dummy_platform = Platform('whatever', 'rand-name', FakeBasicConfig().props())
        self.assertNotEqual(dummy_platform, self.job.platform)

        self.job.platform = dummy_platform

        self.assertEqual(dummy_platform, self.job.platform)

    def test_when_the_job_has_a_queue_returns_that_queue(self):
        dummy_queue = 'whatever'
        self.job._queue = dummy_queue

        returned_queue = self.job.queue

        self.assertEqual(dummy_queue, returned_queue)

    def test_when_the_job_has_not_a_queue_and_some_processors_returns_the_queue_of_the_platform(self):
        dummy_queue = 'whatever-parallel'
        dummy_platform = Platform('whatever', 'rand-name', FakeBasicConfig().props())
        dummy_platform.queue = dummy_queue
        self.job.platform = dummy_platform

        self.assertIsNone(self.job._queue)

        returned_queue = self.job.queue

        self.assertIsNotNone(returned_queue)
        self.assertEqual(dummy_queue, returned_queue)

    def test_when_the_job_has_not_a_queue_and_one_processor_returns_the_queue_of_the_serial_platform(self):
        serial_queue = 'whatever-serial'
        parallel_queue = 'whatever-parallel'

        dummy_serial_platform = Platform('whatever', 'serial', FakeBasicConfig().props())
        dummy_serial_platform.serial_queue = serial_queue

        dummy_platform = Platform('whatever', 'parallel', FakeBasicConfig().props())
        dummy_platform.serial_platform = dummy_serial_platform
        dummy_platform.queue = parallel_queue
        dummy_platform.processors_per_node = "1"
        #dummy_platform.hyperthreading = "false"

        self.job._platform = dummy_platform
        self.job.processors = '1'

        self.assertIsNone(self.job._queue)

        returned_queue = self.job.queue

        self.assertIsNotNone(returned_queue)
        self.assertEqual(serial_queue, returned_queue)
        self.assertNotEqual(parallel_queue, returned_queue)

    def test_set_queue(self):
        dummy_queue = 'whatever'
        self.assertNotEqual(dummy_queue, self.job._queue)

        self.job.queue = dummy_queue

        self.assertEqual(dummy_queue, self.job.queue)

    def test_that_the_increment_fails_count_only_adds_one(self):
        initial_fail_count = self.job.fail_count
        self.job.inc_fail_count()
        incremented_fail_count = self.job.fail_count

        self.assertEqual(initial_fail_count + 1, incremented_fail_count)

    def test_parents_and_children_management(self):
        random_job1 = Job('dummy-name', 111, Status.WAITING, 0)
        random_job2 = Job('dummy-name2', 222, Status.WAITING, 0)
        random_job3 = Job('dummy-name3', 333, Status.WAITING, 0)

        self.job.add_parent(random_job1,
                            random_job2,
                            random_job3)

        # assert added
        self.assertEqual(3, len(self.job.parents))
        self.assertEqual(1, len(random_job1.children))
        self.assertEqual(1, len(random_job2.children))
        self.assertEqual(1, len(random_job3.children))

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
        self.assertEqual(2, len(self.job.parents))

        random_job1.delete_child(self.job)
        self.assertEqual(0, len(random_job1.children))

    def test_create_script(self):
        # arrange
        self.job.parameters = dict()
        self.job.parameters['NUMPROC'] = 999
        self.job.parameters['NUMTHREADS'] = 777
        self.job.parameters['NUMTASK'] = 666

        self.job._tmp_path = '/dummy/tmp/path'
        self.job.additional_files = '/dummy/tmp/path_additional_file'

        update_content_mock = Mock(return_value=('some-content: %NUMPROC%, %NUMTHREADS%, %NUMTASK% %% %%',['some-content: %NUMPROC%, %NUMTHREADS%, %NUMTASK% %% %%']))
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
        update_content_mock.assert_called_with(config)
        # TODO add assert for additional files
        open_mock.assert_called_with(os.path.join(self.job._tmp_path, self.job.name + '.cmd'), 'wb')
        # Expected values: %% -> %, %KEY% -> KEY.VALUE without %
        write_mock.write.assert_called_with(b'some-content: 999, 777, 666 % %')
        chmod_mock.assert_called_with(os.path.join(self.job._tmp_path, self.job.name + '.cmd'), 0o755)

    def test_that_check_script_returns_false_when_there_is_an_unbound_template_variable(self):
        # arrange
        update_content_mock = Mock(return_value=('some-content: %UNBOUND%','some-content: %UNBOUND%'))
        self.job.update_content = update_content_mock
        #template_content = update_content_mock
        update_parameters_mock = Mock(return_value=self.job.parameters)
        self.job.update_parameters = update_parameters_mock

        config = Mock(spec=AutosubmitConfig)
        config.get_project_dir = Mock(return_value='/project/dir')

        # act
        checked = self.job.check_script(config, self.job.parameters)

        # assert
        update_parameters_mock.assert_called_with(config, self.job.parameters)
        update_content_mock.assert_called_with(config)
        self.assertFalse(checked)

    def test_check_script(self):
        # arrange
        self.job.parameters = dict()
        self.job.parameters['NUMPROC'] = 999
        self.job.parameters['NUMTHREADS'] = 777
        self.job.parameters['NUMTASK'] = 666
        self.job.parameters['RESERVATION'] = "random-string"
        update_content_mock = Mock(return_value=('some-content: %NUMPROC%, %NUMTHREADS%, %NUMTASK%', 'some-content: %NUMPROC%, %NUMTHREADS%, %NUMTASK%'))

        #todo
        self.job.update_content = update_content_mock

        update_parameters_mock = Mock(return_value=self.job.parameters)
        self.job.update_parameters = update_parameters_mock

        config = Mock(spec=AutosubmitConfig)
        config.get_project_dir = Mock(return_value='/project/dir')

        # act
        checked = self.job.check_script(config, self.job.parameters)

        # assert
        update_parameters_mock.assert_called_with(config, self.job.parameters)
        update_content_mock.assert_called_with(config)
        self.assertTrue(checked)

    @patch('autosubmitconfigparser.config.basicconfig.BasicConfig')
    def test_hetjob(self, mocked_global_basic_config: Mock):
        """
        Test job platforms with a platform. Builds job and platform using YAML data, without mocks.
        :param mocked_global_basic_config:
        :return:
        """
        expid = "zzyy"
        with tempfile.TemporaryDirectory() as temp_dir:
            BasicConfig.LOCAL_ROOT_DIR = str(temp_dir)
            Path(temp_dir, expid).mkdir()
            for path in [f'{expid}/tmp', f'{expid}/tmp/ASLOGS', f'{expid}/tmp/ASLOGS_{expid}', f'{expid}/proj',
                         f'{expid}/conf']:
                Path(temp_dir, path).mkdir()
            with open(Path(temp_dir, f'{expid}/conf/experiment_data.yml'), 'w+') as experiment_data:
                experiment_data.write(dedent(f'''\
                            CONFIG:
                              RETRIALS: 0 
                            DEFAULT:
                              EXPID: {expid}
                              HPCARCH: test
                            PLATFORMS:
                              test:
                                TYPE: slurm
                                HOST: localhost
                                PROJECT: abc
                                QUEUE: debug
                                USER: me
                                SCRATCH_DIR: /anything/
                                ADD_PROJECT_TO_HOST: False
                                MAX_WALLCLOCK: '00:55'
                                TEMP_DIR: ''
                                
                            '''))
                experiment_data.flush()
            # For could be added here to cover more configurations options
            with open(Path(temp_dir, f'{expid}/conf/hetjob.yml'), 'w+') as hetjob:
                hetjob.write(dedent(f'''\
                            JOBS:
                                HETJOB_A:
                                    FILE: a
                                    PLATFORM: test
                                    RUNNING: once
                                    WALLCLOCK: '00:30'
                                    MEMORY: 
                                        - 0
                                        - 0
                                    NODES:
                                        - 3
                                        - 1
                                    TASKS:
                                        - 32
                                        - 32 
                                    THREADS:
                                        - 4
                                        - 4
                                    CUSTOM_DIRECTIVES: 
                                        - ['#SBATCH --export=ALL', '#SBATCH --distribution=block:cyclic', '#SBATCH --exclusive']
                                        - ['#SBATCH --export=ALL', '#SBATCH --distribution=block:cyclic:fcyclic', '#SBATCH --exclusive']
                '''))

            mocked_basic_config = Mock(spec=BasicConfig)
            mocked_basic_config.LOCAL_ROOT_DIR = str(temp_dir)
            mocked_global_basic_config.LOCAL_ROOT_DIR.return_value = str(temp_dir)

            config = AutosubmitConfig(expid, basic_config=mocked_basic_config, parser_factory=YAMLParserFactory())
            config.reload(True)
            parameters = config.load_parameters()
            job_list_obj = JobList(expid, mocked_basic_config, YAMLParserFactory(),
                                   Autosubmit._get_job_list_persistence(expid, config), config)
            job_list_obj.generate(
                date_list=[],
                member_list=[],
                num_chunks=1,
                chunk_ini=1,
                parameters=parameters,
                date_format='M',
                default_retrials=config.get_retrials(),
                default_job_type=config.get_default_job_type(),
                wrapper_type=config.get_wrapper_type(),
                wrapper_jobs={},
                notransitive=True,
                update_structure=True,
                run_only_members=config.get_member_list(run_only=True),
                jobs_data=config.experiment_data,
                as_conf=config
            )
            job_list = job_list_obj.get_job_list()
            self.assertEqual(1, len(job_list))

            submitter = Autosubmit._get_submitter(config)
            submitter.load_platforms(config)

            hpcarch = config.get_platform()
            for job in job_list:
                if job.platform_name == "" or job.platform_name is None:
                    job.platform_name = hpcarch
                job.platform = submitter.platforms[job.platform_name]

            job = job_list[0]

            # This is the final header
            parameters = job.update_parameters(config, parameters)
            template_content, additional_templates = job.update_content(config)

            # Asserts the script is valid. There shouldn't be variables in the script that aren't in the parameters.
            checked = job.check_script(config, parameters)
            self.assertTrue(checked)

    @patch('autosubmitconfigparser.config.basicconfig.BasicConfig')
    def test_job_parameters(self, mocked_global_basic_config: Mock):
        """Test job platforms with a platform. Builds job and platform using YAML data, without mocks.

        Actually one mock, but that's for something in the AutosubmitConfigParser that can
        be modified to remove the need of that mock.
        """

        expid = 'zzyy'

        for reservation in [None, '', '  ', 'some-string', 'a', '123', 'True']:
            reservation_string = '' if not reservation else f'RESERVATION: "{reservation}"'
            with tempfile.TemporaryDirectory() as temp_dir:
                BasicConfig.LOCAL_ROOT_DIR = str(temp_dir)
                Path(temp_dir, expid).mkdir()
                # FIXME: Not sure why but the submitted and Slurm were using the $expid/tmp/ASLOGS folder?
                for path in [f'{expid}/tmp', f'{expid}/tmp/ASLOGS', f'{expid}/tmp/ASLOGS_{expid}', f'{expid}/proj',
                             f'{expid}/conf']:
                    Path(temp_dir, path).mkdir()
                with open(Path(temp_dir, f'{expid}/conf/minimal.yml'), 'w+') as minimal:
                    minimal.write(dedent(f'''\
                    CONFIG:
                      RETRIALS: 0 
                    DEFAULT:
                      EXPID: {expid}
                      HPCARCH: test
                    JOBS:
                      A:
                        FILE: a
                        PLATFORM: test
                        RUNNING: once
                        {reservation_string}
                    PLATFORMS:
                      test:
                        TYPE: slurm
                        HOST: localhost
                        PROJECT: abc
                        QUEUE: debug
                        USER: me
                        SCRATCH_DIR: /anything/
                        ADD_PROJECT_TO_HOST: False
                        MAX_WALLCLOCK: '00:55'
                        TEMP_DIR: ''
                    '''))
                    minimal.flush()

                mocked_basic_config = Mock(spec=BasicConfig)
                mocked_basic_config.LOCAL_ROOT_DIR = str(temp_dir)
                mocked_global_basic_config.LOCAL_ROOT_DIR.return_value = str(temp_dir)

                config = AutosubmitConfig(expid, basic_config=mocked_basic_config, parser_factory=YAMLParserFactory())
                config.reload(True)
                parameters = config.load_parameters()

                job_list_obj = JobList(expid, mocked_basic_config, YAMLParserFactory(),
                                       Autosubmit._get_job_list_persistence(expid, config), config)
                job_list_obj.generate(
                    date_list=[],
                    member_list=[],
                    num_chunks=1,
                    chunk_ini=1,
                    parameters=parameters,
                    date_format='M',
                    default_retrials=config.get_retrials(),
                    default_job_type=config.get_default_job_type(),
                    wrapper_type=config.get_wrapper_type(),
                    wrapper_jobs={},
                    notransitive=True,
                    update_structure=True,
                    run_only_members=config.get_member_list(run_only=True),
                    jobs_data=config.experiment_data,
                    as_conf=config
                )
                job_list = job_list_obj.get_job_list()
                self.assertEqual(1, len(job_list))

                submitter = Autosubmit._get_submitter(config)
                submitter.load_platforms(config)

                hpcarch = config.get_platform()
                for job in job_list:
                    if job.platform_name == "" or job.platform_name is None:
                        job.platform_name = hpcarch
                    job.platform = submitter.platforms[job.platform_name]

                job = job_list[0]

                # Asserts the script is valid.
                checked = job.check_script(config, parameters)
                self.assertTrue(checked)

                # Asserts the configuration value is propagated as-is to the job parameters.
                # Finally, asserts the header created is correct.
                if not reservation:
                    self.assertTrue('JOBS.A.RESERVATION' not in job.parameters)

                    template_content, additional_templates = job.update_content(config)
                    self.assertFalse(additional_templates)

                    self.assertFalse(f'#SBATCH --reservation' in template_content)
                else:
                    self.assertEqual(reservation, job.parameters['JOBS.A.RESERVATION'])

                    template_content, additional_templates = job.update_content(config)
                    self.assertFalse(additional_templates)
                    self.assertTrue(f'#SBATCH --reservation={reservation}' in template_content)

    def test_exists_completed_file_then_sets_status_to_completed(self):
        # arrange
        exists_mock = Mock(return_value=True)
        sys.modules['os'].path.exists = exists_mock

        # act
        self.job.check_completion()

        # assert
        exists_mock.assert_called_once_with(os.path.join(self.job._tmp_path, self.job.name + '_COMPLETED'))
        self.assertEqual(Status.COMPLETED, self.job.status)

    def test_completed_file_not_exists_then_sets_status_to_failed(self):
        # arrange
        exists_mock = Mock(return_value=False)
        sys.modules['os'].path.exists = exists_mock

        # act
        self.job.check_completion()

        # assert
        exists_mock.assert_called_once_with(os.path.join(self.job._tmp_path, self.job.name + '_COMPLETED'))
        self.assertEqual(Status.FAILED, self.job.status)

    def test_total_processors(self):
        for test in [
            {
                'processors': '',
                'nodes': 0,
                'expected': 1
            },
            {
                'processors': '',
                'nodes': 10,
                'expected': ''
            },
            {
                'processors': '42',
                'nodes': 2,
                'expected': 42
            },
            {
                'processors': '1:9',
                'nodes': 0,
                'expected': 10
            }
        ]:
            self.job.processors = test['processors']
            self.job.nodes = test['nodes']
            self.assertEqual(self.job.total_processors, test['expected'])

    def test_job_script_checking_contains_the_right_default_variables(self):
        # This test (and feature) was implemented in order to avoid
        # false positives on the checking process with auto-ecearth3
        # Arrange
        section = "RANDOM-SECTION"
        self.job.section = section
        self.job.parameters['ROOTDIR'] = "none"
        self.job.parameters['PROJECT_TYPE'] = "none"
        processors = 80
        threads = 1
        tasks = 16
        memory = 80
        wallclock = "00:30"
        self.as_conf.get_member_list = Mock(return_value = [])
        custom_directives = '["whatever"]'
        options = {
            'PROCESSORS': processors,
            'THREADS': threads,
            'TASKS': tasks,
            'MEMORY': memory,
            'WALLCLOCK': wallclock,
            'CUSTOM_DIRECTIVES': custom_directives,
            'SCRATCH_FREE_SPACE': 0,
        }
        self.as_conf.jobs_data[section] = options

        dummy_serial_platform = MagicMock()
        dummy_serial_platform.name = 'serial'
        dummy_platform = MagicMock()
        dummy_platform.serial_platform = dummy_serial_platform
        dummy_platform.name = 'dummy_platform'

        self.as_conf.substitute_dynamic_variables = MagicMock()
        default = {'d': '%d%', 'd_': '%d_%', 'Y': '%Y%', 'Y_': '%Y_%',
                                              'M': '%M%', 'M_': '%M_%', 'm': '%m%', 'm_': '%m_%'}
        self.as_conf.substitute_dynamic_variables.return_value = default
        dummy_platform.custom_directives = '["whatever"]'
        self.as_conf.dynamic_variables = {}
        self.as_conf.parameters = MagicMock()
        self.as_conf.return_value = {}
        self.as_conf.normalize_parameters_keys = MagicMock()
        self.as_conf.normalize_parameters_keys.return_value = default
        self.job._platform = dummy_platform
        self.as_conf.platforms_data = { "dummy_platform":{ "whatever":"dummy_value", "whatever2":"dummy_value2"} }

        parameters = {}
        # Act
        parameters = self.job.update_parameters(self.as_conf, parameters)
        # Assert
        self.assertTrue('CURRENT_WHATEVER' in parameters)
        self.assertTrue('CURRENT_WHATEVER2' in parameters)

        self.assertEqual('dummy_value', parameters['CURRENT_WHATEVER'])
        self.assertEqual('dummy_value2', parameters['CURRENT_WHATEVER2'])
        self.assertTrue('d' in parameters)
        self.assertTrue('d_' in parameters)
        self.assertTrue('Y' in parameters)
        self.assertTrue('Y_' in parameters)
        self.assertEqual('%d%', parameters['d'])
        self.assertEqual('%d_%', parameters['d_'])
        self.assertEqual('%Y%', parameters['Y'])
        self.assertEqual('%Y_%', parameters['Y_'])

    def test_sdate(self):
        """Test that the property getter for ``sdate`` works as expected."""
        for test in [
            [None, None, ''],
            [datetime.datetime(1975, 5, 25, 22, 0, 0, 0, datetime.timezone.utc), 'H', '1975052522'],
            [datetime.datetime(1975, 5, 25, 22, 30, 0, 0, datetime.timezone.utc), 'M', '197505252230'],
            [datetime.datetime(1975, 5, 25, 22, 30, 0, 0, datetime.timezone.utc), 'S', '19750525223000'],
            [datetime.datetime(1975, 5, 25, 22, 30, 0, 0, datetime.timezone.utc), None, '19750525']
        ]:
            self.job.date = test[0]
            self.job.date_format = test[1]
            self.assertEquals(test[2], self.job.sdate)

class FakeBasicConfig:
    def __init__(self):
        pass
    def props(self):
        pr = {}
        for name in dir(self):
            value = getattr(self, name)
            if not name.startswith('__') and not inspect.ismethod(value) and not inspect.isfunction(value):
                pr[name] = value
        return pr
    #convert this to dict
    DB_DIR = '/dummy/db/dir'
    DB_FILE = '/dummy/db/file'
    DB_PATH = '/dummy/db/path'
    LOCAL_ROOT_DIR = '/dummy/local/root/dir'
    LOCAL_TMP_DIR = '/dummy/local/temp/dir'
    LOCAL_PROJ_DIR = '/dummy/local/proj/dir'
    DEFAULT_PLATFORMS_CONF = ''
    DEFAULT_JOBS_CONF = ''




