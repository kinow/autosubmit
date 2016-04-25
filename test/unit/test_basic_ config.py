from unittest import TestCase

import os
from mock import Mock
from mock import patch

from autosubmit.config.basicConfig import BasicConfig

'''
    This class has a static private (__named) method which is impossible to be tested.
    IMHO this kind of static private methods are not a good practise in terms of testing.

    Read about this on the below article:
    http://googletesting.blogspot.com.es/2008/12/static-methods-are-death-to-testability.html
'''


class TestBasicConfig(TestCase):
    def test_update_config_set_the_right_db_path(self):
        # arrange
        BasicConfig.DB_PATH = 'fake-path'
        # act
        BasicConfig._update_config()
        # assert
        self.assertEquals(os.path.join(BasicConfig.DB_DIR, BasicConfig.DB_FILE), BasicConfig.DB_PATH)

    def test_read_makes_the_right_method_calls(self):
        # arrange
        with patch('autosubmit.config.basicConfig.BasicConfig._update_config', Mock()):
            # act
            BasicConfig.read()
            # assert
            BasicConfig._update_config.assert_called_once_with()
