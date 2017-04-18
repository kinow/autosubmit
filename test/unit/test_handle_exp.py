from unittest import TestCase
from mock import Mock, patch


class TestHandleExp(TestCase):
    def setUp(self):
        self.user_from = "old-user"
        self.user_to = "new-user"

    def testFoo(self):
        self.failUnless(False)

#    @patch('autosubmit.autosubmit.handle')
#    def test_handle_experiment(self, db_common_mock):
#        current_user_id = "old-user"
#        self._build_db_mock(current_experiment_id, db_common_mock)
#        user_id = handle_experiment(self.user_from, self.user_to)
#        self.assertEquals("new_user", user_id)
#
#    @staticmethod
#    def _build_db_mock(current_experiment_id, mock_db_common):
#        mock_db_common.last_name_used = Mock(return_value=current_experiment_id)
#        mock_db_common.check_experiment_exists = Mock(return_value=False)
