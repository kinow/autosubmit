import unittest
from autosubmit.platforms.lsfplatform import LsfPlatform


class PlatformsTests(unittest.TestCase):
    def setUp(self):
        # have to create the cmd file in the tmp folder before testing
        self.platform = LsfPlatform('a000')
        self.platform.set_host("mn-bsc32")
        self.platform.set_scratch("/gpfs/scratch")
        self.platform.set_project("bsc32")
        self.platform.set_user("bsc32704")
        self.platform.update_cmds()
        self.scriptname = "test.cmd"

    def tearDown(self):
        pass

    def testMethod(self):
        self.assertTrue(self.platform.connect())
        self.assertTrue(self.platform.check_remote_log_dir())
        self.assertTrue(self.platform.send_script(self.scriptname))
        job_id = self.platform.submit_job(self.scriptname)
        print(job_id)
        self.assertNotEqual(job_id, 0)


if __name__ == '__main__':
    unittest.main()
