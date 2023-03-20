from unittest import TestCase
from log.log import AutosubmitError, AutosubmitCritical


"""Tests for the log module."""

class TestLog(TestCase):

    def setUp(self):
        ...

    def test_autosubmit_error(self):
        ae = AutosubmitError()
        assert 'Unhandled Error' == ae.message
        assert 6000 == ae.code
        assert None is ae.trace
        assert 'Unhandled Error' == ae.error_message
        assert ' ' == str(ae)

    def test_autosubmit_error_error_message(self):
        ae = AutosubmitError(trace='ERROR!')
        assert 'ERROR! Unhandled Error' == ae.error_message

    def test_autosubmit_critical(self):
        ac = AutosubmitCritical()
        assert 'Unhandled Error' == ac.message
        assert 7000 == ac.code
        assert None is ac.trace
        assert ' ' == str(ac)

