from unittest import TestCase
from autosubmit.config.basicConfig import BasicConfig


class TestBasicConfig(TestCase):

    def test__update_config(self):
        BasicConfig._update_config()

    def test_read(self):
        BasicConfig.read()
