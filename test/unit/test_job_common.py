from unittest import TestCase

from autosubmit.job.job_common import Status


class TestJobCommon(TestCase):
    """
        This test is intended to prevent wrong changes on the Status classs definition
    """

    def test_value_to_key_has_the_same_values_as_status_constants(self):
        self.assertEquals('SUSPENDED', Status.VALUE_TO_KEY[Status.SUSPENDED])
        self.assertEquals('UNKNOWN', Status.VALUE_TO_KEY[Status.UNKNOWN])
        self.assertEquals('FAILED', Status.VALUE_TO_KEY[Status.FAILED])
        self.assertEquals('WAITING', Status.VALUE_TO_KEY[Status.WAITING])
        self.assertEquals('READY', Status.VALUE_TO_KEY[Status.READY])
        self.assertEquals('SUBMITTED', Status.VALUE_TO_KEY[Status.SUBMITTED])
        self.assertEquals('QUEUING', Status.VALUE_TO_KEY[Status.QUEUING])
        self.assertEquals('RUNNING', Status.VALUE_TO_KEY[Status.RUNNING])
        self.assertEquals('COMPLETED', Status.VALUE_TO_KEY[Status.COMPLETED])
