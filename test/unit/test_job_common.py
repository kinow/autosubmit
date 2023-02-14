from unittest import TestCase

from autosubmit.job.job_common import Status


class TestJobCommon(TestCase):
    """
        This test is intended to prevent wrong changes on the Status class definition
    """

    def test_value_to_key_has_the_same_values_as_status_constants(self):
        self.assertEqual('SUSPENDED', Status.VALUE_TO_KEY[Status.SUSPENDED])
        self.assertEqual('UNKNOWN', Status.VALUE_TO_KEY[Status.UNKNOWN])
        self.assertEqual('FAILED', Status.VALUE_TO_KEY[Status.FAILED])
        self.assertEqual('WAITING', Status.VALUE_TO_KEY[Status.WAITING])
        self.assertEqual('READY', Status.VALUE_TO_KEY[Status.READY])
        self.assertEqual('SUBMITTED', Status.VALUE_TO_KEY[Status.SUBMITTED])
        self.assertEqual('HELD', Status.VALUE_TO_KEY[Status.HELD])
        self.assertEqual('QUEUING', Status.VALUE_TO_KEY[Status.QUEUING])
        self.assertEqual('RUNNING', Status.VALUE_TO_KEY[Status.RUNNING])
        self.assertEqual('COMPLETED', Status.VALUE_TO_KEY[Status.COMPLETED])
