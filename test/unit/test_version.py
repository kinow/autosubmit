import subprocess
from pathlib import Path
from unittest import TestCase

import sys

from autosubmit.autosubmit import Autosubmit


class TestAutosubmit(TestCase):

    def testAutosubmitVersion(self):
        bin_path = Path(__file__, '../../../bin/autosubmit').resolve()
        exit_code, out = subprocess.getstatusoutput(' '.join([sys.executable, str(bin_path), '-v']))
        self.assertEqual(0, exit_code)
        self.assertEqual(Autosubmit.autosubmit_version, out.strip())

    def testAutosubmitVersionBroken(self):
        bin_path = Path(__file__, '../../../bin/autosubmit').resolve()
        exit_code, _ = subprocess.getstatusoutput(' '.join([sys.executable, str(bin_path), '-abcdefg']))
        self.assertEqual(1, exit_code)
