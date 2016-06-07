import os
from unittest import TestCase


class TestSetup(TestCase):
    def test_setup_check_works(self):
        exit_code = os.system('python ../setup.py check')
        self.assertEquals(0, exit_code)
