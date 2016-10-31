from unittest import TestCase
from mock import Mock, patch
from autosubmit.experiment.experiment_common import new_experiment, next_experiment_id


class TestExpid(TestCase):
    def setUp(self):
        self.description = "for testing"
        self.version = "test-version"

    @patch('autosubmit.experiment.experiment_common.db_common')
    def test_create_new_experiment(self, db_common_mock):
        current_experiment_id = "empty"
        self._build_db_mock(current_experiment_id, db_common_mock)
        experiment_id = new_experiment(self.description, self.version)
        self.assertEquals("a000", experiment_id)

    @patch('autosubmit.experiment.experiment_common.db_common')
    def test_create_new_test_experiment(self, db_common_mock):
        current_experiment_id = "empty"
        self._build_db_mock(current_experiment_id, db_common_mock)
        experiment_id = new_experiment(self.description, self.version, True)
        self.assertEquals("t000", experiment_id)

    @patch('autosubmit.experiment.experiment_common.db_common')
    def test_create_new_operational_experiment(self, db_common_mock):
        current_experiment_id = "empty"
        self._build_db_mock(current_experiment_id, db_common_mock)
        experiment_id = new_experiment(self.description, self.version, False, True)
        self.assertEquals("o000", experiment_id)

    @patch('autosubmit.experiment.experiment_common.db_common')
    def test_create_new_experiment_with_previous_one(self, db_common_mock):
        current_experiment_id = "a006"
        self._build_db_mock(current_experiment_id, db_common_mock)
        experiment_id = new_experiment(self.description, self.version)
        self.assertEquals("a007", experiment_id)

    @patch('autosubmit.experiment.experiment_common.db_common')
    def test_create_new_test_experiment_with_previous_one(self, db_common_mock):
        current_experiment_id = "t0ab"
        self._build_db_mock(current_experiment_id, db_common_mock)
        experiment_id = new_experiment(self.description, self.version, True)
        self.assertEquals("t0ac", experiment_id)

    @patch('autosubmit.experiment.experiment_common.db_common')
    def test_create_new_operational_experiment_with_previous_one(self, db_common_mock):
        current_experiment_id = "o112"
        self._build_db_mock(current_experiment_id, db_common_mock)
        experiment_id = new_experiment(self.description, self.version, False, True)
        self.assertEquals("o113", experiment_id)

    @staticmethod
    def _build_db_mock(current_experiment_id, mock_db_common):
        mock_db_common.last_name_used = Mock(return_value=current_experiment_id)
        mock_db_common.check_experiment_exists = Mock(return_value=False)
