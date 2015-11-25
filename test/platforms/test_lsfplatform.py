import textwrap
import os
import shutil
import tempfile
from unittest import TestCase
from autosubmit.platforms.lsfplatform import LsfPlatform


class PlatformsTests(TestCase):
    def setUp(self):
        # have to create the cmd file in the tmp folder before testing
        self.platform = LsfPlatform('a000')
        self.platform.set_host("mn-bsc32")
        self.platform.set_scratch("/gpfs/scratch")
        self.platform.set_project("bsc32")
        self.platform.set_user("bsc32704")
        self.platform.update_cmds()
        self.tmpdir = tempfile.mkdtemp()
        self.scriptname = 'test.cmd'
        self.scriptpath = os.path.join(self.tmpdir, self.scriptname)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def write_script(self):
        script_content = textwrap.dedent("""\
                    #!/bin/sh
                    ###############################################################################
                    #                   TEST
                    ###############################################################################
                    #
                    #BSUB -J test
                    #BSUB -oo /gpfs/scratch/bsc32/bsc32704/a000/LOG_a000/test_%J.out
                    #BSUB -eo /gpfs/scratch/bsc32/bsc32704/a000/LOG_a000/test_%J.err
                    #BSUB -W 00:01
                    #BSUB -n 1
                    #
                    ###############################################################################
                    echo "test"
                    """)
        open(self.scriptpath, 'w').write(script_content)

    def test_connect(self):
        self.assertTrue(self.platform.connect())

    def test_remote_log_dir(self):
        self.platform.connect()
        self.assertTrue(self.platform.check_remote_log_dir())

    def test_send_file(self):
        self.platform.connect()
        self.write_script()
        self.assertTrue(self.platform.send_file(self.scriptpath,
                                                os.path.join(self.platform.get_remote_log_dir(), self.scriptname)))

    def test_submit_job(self):
        self.platform.connect()
        job_id = self.platform.submit_job(self.scriptname)
        self.assertNotEqual(job_id, 0)


    #def test_send_script(self):
    #    self.platform.connect()
    #    self.assertTrue(self.platform.send_script(self.scriptname))
