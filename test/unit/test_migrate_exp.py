from unittest import TestCase
from mock import Mock, patch
from autosubmit.experiment.experiment_common import migrate_experiment
import os
import pwd


class TestMigrateExp(TestCase):
    def setUp(self):
        #self.user_from = "old-user"
        self.user_from = "dmanuben"
        #self.user_to = "new-user"
        self.user_to = "dmanuben"

#    def testFoo(self):
#        self.failUnless(False)

    @patch('autosubmit.experiment.experiment_common.os')
    def test_migrate_experiment(self, mock_os):
        current_user_id = "old-user"
        user_id, group_id = migrate_experiment("any path", self.user_to)

        to_uid = pwd.getpwnam(self.user_to).pw_uid
        mock_os.chown.assert_called_with("any path", to_uid, group_id)
        #self.assertEquals("new_user", user_id)

#    @patch('autosubmit.experiment.experiment_common.db_common')
#    def test_create_new_experiment(self, db_common_mock):
#        current_experiment_id = "empty"
#        self._build_db_mock(current_experiment_id, db_common_mock)
#        experiment_id = new_experiment(self.description, self.version)
#        self.assertEquals("a000", experiment_id)
 
#
#    @staticmethod
#    def _build_db_mock(current_experiment_id, mock_db_common):
#        mock_db_common.last_name_used = Mock(return_value=current_experiment_id)
#        mock_db_common.check_experiment_exists = Mock(return_value=False)
