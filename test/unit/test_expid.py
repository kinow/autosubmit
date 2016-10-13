from unittest import TestCase
from mock import Mock
from autosubmit.autosubmit import new_experiment
import autosubmit.database.db_common as db_common


class TestExpid(TestCase):
    def setUp(self):
        self.description = "for testing"
        self.version = "test-version"

    def test_create_new_experiment(self):
        # arrange
        current_experiment_id = "a006"
        db_common.last_name_used = Mock(return_value=current_experiment_id)
        db_common.check_experiment_exists = Mock(return_value=False)
        db_common._set_experiment = Mock(return_value=True)
        # act
        experiment_id = new_experiment(self.description, self.version)
        # assert
        self.assertEquals("a007", experiment_id)