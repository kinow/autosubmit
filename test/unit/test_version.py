import subprocess
from pathlib import Path
from unittest import TestCase

import sys

from autosubmit.autosubmit import Autosubmit


class TestAutosubmit(TestCase):

    def testAutosubmitVersion(self):
        bin_path = Path(__file__, '../../../bin/autosubmit').resolve()
        out = subprocess.getoutput(' '.join([sys.executable, str(bin_path), '-v']))
        self.assertEquals(Autosubmit.autosubmit_version, out.strip())

    def testAutosubmitVersionBroken(self):
        bin_path = Path(__file__, '../../../bin/autosubmit').resolve()
        exit_code, _ = subprocess.getstatusoutput(' '.join([sys.executable, str(bin_path), '-abcdefg']))
        self.assertEquals(1, exit_code)
