import tempfile
from unittest import TestCase
from mock import Mock, patch
from autosubmit.autosubmit import Autosubmit
from autosubmit.experiment.experiment_common import new_experiment
from textwrap import dedent
from pathlib import Path
from autosubmitconfigparser.config.basicconfig import BasicConfig


class TestExpid(TestCase):
    def setUp(self):
        self.description = "for testing"
        self.version = "test-version"

    @patch('autosubmit.experiment.experiment_common.db_common')
    def test_create_new_experiment(self, db_common_mock):
        current_experiment_id = "empty"
        self._build_db_mock(current_experiment_id, db_common_mock)
        experiment_id = new_experiment(self.description, self.version)
        self.assertEqual("a000", experiment_id)

    @patch('autosubmit.experiment.experiment_common.db_common')
    def test_create_new_test_experiment(self, db_common_mock):
        current_experiment_id = "empty"
        self._build_db_mock(current_experiment_id, db_common_mock)
        experiment_id = new_experiment(self.description, self.version, True)
        self.assertEqual("t000", experiment_id)

    @patch('autosubmit.experiment.experiment_common.db_common')
    def test_create_new_operational_experiment(self, db_common_mock):
        current_experiment_id = "empty"
        self._build_db_mock(current_experiment_id, db_common_mock)
        experiment_id = new_experiment(self.description, self.version, False, True)
        self.assertEqual("o000", experiment_id)

    @patch('autosubmit.experiment.experiment_common.db_common')
    def test_create_new_experiment_with_previous_one(self, db_common_mock):
        current_experiment_id = "a007"
        self._build_db_mock(current_experiment_id, db_common_mock)
        experiment_id = new_experiment(self.description, self.version)
        self.assertEqual("a007", experiment_id)

    @patch('autosubmit.experiment.experiment_common.db_common')
    def test_create_new_test_experiment_with_previous_one(self, db_common_mock):
        current_experiment_id = "t0ac"
        self._build_db_mock(current_experiment_id, db_common_mock)
        experiment_id = new_experiment(self.description, self.version, True)
        self.assertEqual("t0ac", experiment_id)

    @patch('autosubmit.experiment.experiment_common.db_common')
    def test_create_new_operational_experiment_with_previous_one(self, db_common_mock):
        current_experiment_id = "o113"
        self._build_db_mock(current_experiment_id, db_common_mock)
        experiment_id = new_experiment(self.description, self.version, False, True)
        self.assertEqual("o113", experiment_id)

    @staticmethod
    def _build_db_mock(current_experiment_id, mock_db_common):
        mock_db_common.last_name_used = Mock(return_value=current_experiment_id)
        mock_db_common.check_experiment_exists = Mock(return_value=False)

    @patch('autosubmit.autosubmit.resource_listdir')
    @patch('autosubmit.autosubmit.resource_filename')
    def test_autosubmit_generate_config(self, resource_filename_mock, resource_listdir_mock):
        expid = 'ff99'
        original_local_root_dir = BasicConfig.LOCAL_ROOT_DIR

        with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w') as source_yaml, tempfile.TemporaryDirectory() as temp_dir:
            # Our processed and commented YAML output file must be written here
            Path(temp_dir, expid, 'conf').mkdir(parents=True)
            BasicConfig.LOCAL_ROOT_DIR = temp_dir

            source_yaml.write(
dedent('''JOB:
  JOBNAME: SIM
  PLATFORM: local
CONFIG:
  TEST: The answer?
  ROOT: No'''))
            source_yaml.flush()
            resource_listdir_mock.return_value = [Path(source_yaml.name).name]
            resource_filename_mock.return_value = source_yaml.name

            parameters = {
                'JOB': {
                    'JOBNAME': 'sim'
                },
                'CONFIG': {
                    'CONFIG.TEST': '42'
                }
            }
            Autosubmit.generate_as_config(exp_id=expid, parameters=parameters)

            source_text = Path(source_yaml.name).read_text()
            source_name = Path(source_yaml.name)
            output_text = Path(temp_dir, expid, 'conf', f'{source_name.stem}_{expid}.yml').read_text()

            self.assertNotEquals(source_text, output_text)
            self.assertFalse('# sim' in source_text)
            self.assertTrue('# sim' in output_text)
            self.assertFalse('# 42' in source_text)
            self.assertTrue('# 42' in output_text)

        # Reset the local root dir.
        BasicConfig.LOCAL_ROOT_DIR = original_local_root_dir
