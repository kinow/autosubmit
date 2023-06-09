from unittest import TestCase

import os
import inspect
from copy import deepcopy
from mock import Mock,MagicMock, mock_open , call
from mock import patch

from autosubmit.job.job_packages import JobPackageSimple, JobPackageVertical
from autosubmit.job.job import Job
from autosubmit.job.job_common import Status

import shutil
import tempfile

from unittest import TestCase
from mock import MagicMock
from autosubmit.job.job_packager import JobPackager
from autosubmit.job.job_list import JobList
from autosubmit.job.job_dict import DicJobs
from autosubmit.job.job_utils import Dependency
from autosubmitconfigparser.config.yamlparser import YAMLParserFactory
from autosubmit.job.job_list_persistence import JobListPersistenceDb
from random import randrange
from collections import OrderedDict
from autosubmitconfigparser.config.configcommon import AutosubmitConfig
class FakeBasicConfig:
    def __init__(self):
        pass
    def props(self):
        pr = {}
        for name in dir(self):
            value = getattr(self, name)
            if not name.startswith('__') and not inspect.ismethod(value) and not inspect.isfunction(value):
                pr[name] = value
        return pr
    DB_DIR = '/dummy/db/dir'
    DB_FILE = '/dummy/db/file'
    DB_PATH = '/dummy/db/path'
    LOCAL_ROOT_DIR = '/dummy/local/root/dir'
    LOCAL_TMP_DIR = '/dummy/local/temp/dir'
    LOCAL_PROJ_DIR = '/dummy/local/proj/dir'
    DEFAULT_PLATFORMS_CONF = ''
    DEFAULT_JOBS_CONF = ''

class TestJobPackage(TestCase):

    def setUpWrappers(self,options):
        # reset
        self.as_conf = None
        self.job_package_wrapper = None
        self.experiment_id = 'random-id'
        self._wrapper_factory = MagicMock()

        self.config = FakeBasicConfig
        self.config.read = MagicMock()



        self.as_conf = AutosubmitConfig(self.experiment_id, self.config, YAMLParserFactory())
        self.as_conf.experiment_data = dict()
        self.as_conf.experiment_data["JOBS"] = dict()
        self.as_conf.experiment_data["PLATFORMS"] = dict()
        self.as_conf.experiment_data["WRAPPERS"] = dict()
        self.temp_directory = tempfile.mkdtemp()
        self.job_list = JobList(self.experiment_id, self.config, YAMLParserFactory(),
                                JobListPersistenceDb(self.temp_directory, 'db'), self.as_conf)
        self.parser_mock = MagicMock(spec='SafeConfigParser')

        self._platform.max_waiting_jobs = 100
        self._platform.total_jobs = 100
        self.as_conf.experiment_data["WRAPPERS"]["WRAPPERS"] = options
        self._wrapper_factory.as_conf = self.as_conf
        self.jobs[0].wallclock = "00:00"
        self.jobs[0].threads = "1"
        self.jobs[0].tasks = "1"
        self.jobs[0].exclusive = True
        self.jobs[0].queue = "debug"
        self.jobs[0].partition = "debug"
        self.jobs[0].custom_directives = "dummy_directives"
        self.jobs[0].processors = "9"
        self.jobs[0]._processors = "9"
        self.jobs[0].retrials = 0
        self.jobs[1].wallclock = "00:00"
        self.jobs[1].threads = ""
        self.jobs[1].tasks = ""
        self.jobs[1].exclusive = True
        self.jobs[1].queue = "debug2"
        self.jobs[1].partition = "debug2"
        self.jobs[1].custom_directives = "dummy_directives2"
        self.jobs[1].processors = "9"
        self.jobs[1]._processors = "9"


        self.wrapper_type = options.get('TYPE', 'vertical')
        self.wrapper_policy = options.get('POLICY', 'flexible')
        self.wrapper_method = options.get('METHOD', 'ASThread')
        self.jobs_in_wrapper = options.get('JOBS_IN_WRAPPER', 'None')
        self.extensible_wallclock = options.get('EXTEND_WALLCLOCK', 0)
        self.job_package_wrapper = JobPackageVertical(self.jobs,configuration=self.as_conf,wrapper_info=[self.wrapper_type,self.wrapper_policy,self.wrapper_method,self.jobs_in_wrapper,self.extensible_wallclock])
        self.job_list._ordered_jobs_by_date_member["WRAPPERS"] = dict()




    def setUp(self):
        self._platform = MagicMock()
        self._platform.queue = "debug"
        self._platform.partition = "debug"
        self._platform.serial_platform = self._platform
        self._platform.serial_queue = "debug-serial"
        self._platform.serial_partition = "debug-serial"
        self.jobs = [Job('dummy1', 0, Status.READY, 0),
                     Job('dummy2', 0, Status.READY, 0)]
        self.jobs[0]._platform = self.jobs[1]._platform = self._platform
        self.job_package = JobPackageSimple(self.jobs)
    def test_default_parameters(self):
        options = {
            'TYPE': "vertical",
            'JOBS_IN_WRAPPER': "None",
            'METHOD': "ASThread",
            'POLICY': "flexible",
            'EXTEND_WALLCLOCK': 0,
        }

        self.setUpWrappers(options)
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["TYPE"], "vertical")
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["JOBS_IN_WRAPPER"], "None")
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["METHOD"], "ASThread")
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["POLICY"], "flexible")
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["EXTEND_WALLCLOCK"], 0)

        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["EXCLUSIVE"], True)
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["INNER_RETRIALS"], 0)
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["QUEUE"], "debug")
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["PARTITION"], "debug")
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["THREADS"], "1")
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["TASKS"], "1")

        options_slurm = {
            'EXCLUSIVE': False,
            'QUEUE': "bsc32",
            'PARTITION': "bsc32",
            'THREADS': "30",
            'TASKS': "40",
            'INNER_RETRIALS': 30,
            'CUSTOM_DIRECTIVES': "['#SBATCH --mem=1000']"
        }
        self.setUpWrappers(options_slurm)
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["EXCLUSIVE"], False)
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["INNER_RETRIALS"], 30)
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["QUEUE"], "bsc32")
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["PARTITION"], "bsc32")
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["THREADS"], "30")
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["TASKS"], "40")
        self.assertEqual(self.as_conf.experiment_data["CURRENT_WRAPPER"]["CUSTOM_DIRECTIVES"], "['#SBATCH --mem=1000']")



    def test_job_package_default_init(self):
        with self.assertRaises(Exception):
            JobPackageSimple([])

    def test_job_package_different_platforms_init(self):
        self.jobs[0]._platform = MagicMock()
        self.jobs[1]._platform = MagicMock()
        with self.assertRaises(Exception):
            JobPackageSimple(self.jobs)

    def test_job_package_none_platforms_init(self):
        self.jobs[0]._platform = None
        self.jobs[1]._platform = None
        with self.assertRaises(Exception):
            JobPackageSimple(self.jobs)

    def test_job_package_length(self):
        self.assertEqual(2, len(self.job_package))

    def test_job_package_jobs_getter(self):
        self.assertEqual(self.jobs, self.job_package.jobs)

    def test_job_package_platform_getter(self):
        self.assertEqual(self.platform, self.job_package.platform)

    @patch("builtins.open",MagicMock())
    def test_job_package_submission(self):
        # arrange
        MagicMock().write = MagicMock()

        for job in self.jobs:
            job._tmp_path = MagicMock()
            job._get_paramiko_template = MagicMock("false","empty")

        self.job_package._create_scripts = MagicMock()
        self.job_package._send_files = MagicMock()
        self.job_package._do_submission = MagicMock()
        for job in self.jobs:
            job.update_parameters = MagicMock()
        # act
        self.job_package.submit('fake-config', 'fake-params')
        # assert
        for job in self.jobs:
            job.update_parameters.assert_called_once_with('fake-config', 'fake-params')
        self.job_package._create_scripts.is_called_once_with()
        self.job_package._send_files.is_called_once_with()
        self.job_package._do_submission.is_called_once_with()

    def test_wrapper_parameters(self):
        pass