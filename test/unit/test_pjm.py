from unittest import TestCase
from unittest.mock import Mock,MagicMock, patch
from autosubmitconfigparser.config.configcommon import AutosubmitConfig
from autosubmitconfigparser.config.yamlparser import YAMLParserFactory
from autosubmit.autosubmit import Autosubmit
import autosubmit.platforms.pjmplatform

from pathlib import Path
from autosubmit.platforms.platform import Platform
from autosubmit.platforms.pjmplatform import PJMPlatform
import autosubmit.platforms.headers.pjm_header
from tempfile import TemporaryDirectory
from datetime import datetime
from autosubmit.job.job import Job, Status

class FakeBasicConfig:
    DB_DIR = '/dummy/db/dir'
    DB_FILE = '/dummy/db/file'
    DB_PATH = '/dummy/db/path'
    LOCAL_ROOT_DIR = '/dummy/local/root/dir'
    LOCAL_TMP_DIR = '/dummy/local/temp/dir'
    LOCAL_PROJ_DIR = '/dummy/local/proj/dir'
    LOCAL_ASLOG_DIR = '/dummy/local/aslog/dir'
    DEFAULT_PLATFORMS_CONF = ''
    DEFAULT_JOBS_CONF = ''
    @staticmethod
    def read():
        return
class TestPJM(TestCase):

    def setUp(self) -> None:
        self.exp_id = 'a000'
        self.as_conf = MagicMock()
        self.as_conf = AutosubmitConfig(self.exp_id, FakeBasicConfig, YAMLParserFactory())
        self.as_conf.experiment_data = dict()
        self.as_conf.experiment_data["DEFAULT"] = dict()
        self.as_conf.experiment_data["DEFAULT"]["HPCARCH"] = "ARM"
        yml_file = Path("files/fake-jobs.yml")
        yml_file.exists()
        factory = YAMLParserFactory()
        parser = factory.create_parser()
        parser.data = parser.load(yml_file)
        self.as_conf.experiment_data.update(parser.data)
        yml_file = Path("files/fake-platforms.yml")
        yml_file.exists()
        factory = YAMLParserFactory()
        parser = factory.create_parser()
        parser.data = parser.load(yml_file)
        self.as_conf.experiment_data.update(parser.data)
        self.setUp_pjm()


    @patch("builtins.open",MagicMock())
    def setUp_pjm(self):
        MagicMock().write = MagicMock()
        MagicMock().os.path.join = MagicMock()
        self.section = 'ARM'
        self.submitted_ok = "[INFO] PJM 0000 pjsub Job 167661 submitted."
        self.submitted_fail = "[ERR.] PJM 0057 pjsub node=32 is greater than the upper limit (24)."
        self.out= """JOB_ID     JOB_NAME   MD ST  USER     GROUP    START_DATE      ELAPSE_TIM ELAPSE_LIM            NODE_REQUIRE    VNODE  CORE V_MEM        V_POL E_POL RANK      LST EC  PC  SN PRI ACCEPT         RSC_GRP  REASON          
167687     test       NM ACC bsc32070 bsc32    03/08 11:41:07  0000:00:01 0000:01:00            1               -      -    -            -     -     bychip    ACC 0   0   0  127 03/08 11:41:04 small    -               
167688     test       NM RUN bsc32070 bsc32    (03/08 11:41)   0000:00:00 0000:01:00            1               -      -    -            -     -     bychip    RNO 0   0   0  127 03/08 11:41:05 small    -               
167689     test       NM RNO bsc32070 bsc32    (03/08 11:41)   0000:00:00 0000:01:00            1               -      -    -            -     -     bychip    RNE 0   0   0  127 03/08 11:41:05 small    -               
167690     test       NM RNA bsc32070 bsc32    (03/08 11:41)   0000:00:00 0000:01:00            1               -      -    -            -     -     bychip    RUN 0   0   0  127 03/08 11:41:06 small    -               
167691     test       NM RNP bsc32070 bsc32    (03/08 11:41)   0000:00:00 0000:01:00            1               -      -    -            -     -     bychip    RNA 0   0   0  127 03/08 11:41:06 small    -               
167692     test       NM HLD bsc32070 bsc32    (03/08 11:41)   0000:00:00 0000:01:00            1               -      -    -            -     -     bychip    RNP 0   0   0  127 03/08 11:41:06 small    -              """
        self.queued_jobs = ["167687","167690","167691","167692"]
        self.running_jobs = ["167688","167689"]
        self.out_h="""JOB_ID     JOB_NAME   MD ST  USER     GROUP    START_DATE      ELAPSE_TIM ELAPSE_LIM            NODE_REQUIRE    VNODE  CORE V_MEM        V_POL E_POL RANK      LST EC  PC  SN PRI ACCEPT         RSC_GRP  REASON          
167648     STDIN      NM EXT bsc32070 bsc32    03/06 12:14:00  0000:00:02 0001:00:00            1               -      -    -            -     -     bychip    RNO 0   0   0  127 03/06 12:13:57 def_grp  -               
167661     test       NM ERR bsc32070 bsc32    03/06 13:55:02  0000:00:02 0000:01:00            1               -      -    -            -     -     bychip    RNO 127 0   0  127 03/06 13:54:59 small    -               
167662     test       NM CCL bsc32070 bsc32    03/06 14:25:30  0000:00:02 0000:01:00            1               -      -    -            -     -     bychip    RNO 127 0   0  127 03/06 14:25:27 small    -               
167663     test       NM RJT bsc32070 bsc32    03/06 14:25:54  0000:00:04 0000:01:00            1               -      -    -            -     -     bychip    RNO 0   0   0  127 03/06 14:25:52 small    -               
167677     test       NM EXT bsc32070 bsc32    03/07 16:39:54  0000:00:04 0000:01:00            1               -      -    -            -     -     bychip    RNO 0   0   0  127 03/07 16:39:50 small    -               
167678     test       NM EXT bsc32070 bsc32    03/07 16:39:57  0000:00:04 0000:01:00            1               -      -    -            -     -     bychip    RNO 0   0   0  127 03/07 16:39:53 small    -               
167683     test       NM EXT bsc32070 bsc32    03/08 11:39:45  0000:00:04 0000:01:00            1               -      -    -            -     -     bychip    RNO 0   0   0  127 03/08 11:39:41 small    -               
167687     test       NM EXT bsc32070 bsc32    03/08 11:41:07  0000:00:04 0000:01:00            1               -      -    -            -     -     bychip    RNO 0   0   0  127 03/08 11:41:04 small    -               
167688     test       NM EXT bsc32070 bsc32    03/08 11:41:08  0000:00:04 0000:01:00            1               -      -    -            -     -     bychip    RNO 0   0   0  127 03/08 11:41:05 small    -               
167689     test       NM EXT bsc32070 bsc32    03/08 11:41:09  0000:00:04 0000:01:00            1               -      -    -            -     -     bychip    RNO 0   0   0  127 03/08 11:41:05 small    -               
167690     test       NM EXT bsc32070 bsc32    03/08 11:41:10  0000:00:04 0000:01:00            1               -      -    -            -     -     bychip    RNO 0   0   0  127 03/08 11:41:06 small    -               
167691     test       NM EXT bsc32070 bsc32    03/08 11:41:10  0000:00:04 0000:01:00            1               -      -    -            -     -     bychip    RNO 0   0   0  127 03/08 11:41:06 small    -               
167692     test       NM EXT bsc32070 bsc32    03/08 11:41:10  0000:00:04 0000:01:00            1               -      -    -            -     -     bychip    RNO 0   0   0  127 03/08 11:41:06 small    -     """

        self.completed_jobs = ["167677", "167678", "167683", "167687", "167688", "167689", "167690", "167691", "167692"]
        self.failed_jobs = ["167661", "167662", "167663"]
        self.submitter = Autosubmit._get_submitter(self.as_conf)
        self.submitter.load_platforms(self.as_conf)
        self.remote_platform = self.submitter.platforms[self.section]

    def test_parse_queue_reason(self):
        """Test parsing of queue reason."""
        output = self.remote_platform.parse_queue_reason(self.out_h, self.completed_jobs)
        self.assertEqual(output, "")



