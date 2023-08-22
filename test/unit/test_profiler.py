from unittest import TestCase, mock
from autosubmit.profiler.profiler import Profiler
from log.log import AutosubmitCritical


class TestProfiler(TestCase):
    def setUp(self):
        self.profiler = Profiler("a000")

    # Black box techniques for status machine based software
    #
    #   O---->__init__------> start
    #                           |
    #                           |
    #                         stop ----> report --->0

    # Transition coverage
    def test_transitions(self):
        # __init__ -> start
        self.profiler.start()

        # start -> stop
        self.profiler.stop()

    def test_transitions_fail_cases(self):
        # __init__ -> stop
        self.assertRaises(AutosubmitCritical, self.profiler.stop)

        # start -> start
        self.profiler.start()
        self.assertRaises(AutosubmitCritical, self.profiler.start)

        # stop -> stop
        self.profiler.stop()
        self.assertRaises(AutosubmitCritical, self.profiler.stop)

    # White box tests
    @mock.patch("os.access")
    def test_writing_permission_check_fails(self, mock_response):
        mock_response.return_value = False

        self.profiler.start()
        self.assertRaises(AutosubmitCritical, self.profiler.stop)

    def test_memory_profiling_loop(self):
        self.profiler.start()
        bytearray(1024*1024)
        self.profiler.stop()
