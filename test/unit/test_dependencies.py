from unittest.mock import Mock

import copy
import inspect
import mock
import tempfile
import unittest
from copy import deepcopy
from datetime import datetime

from autosubmit.job.job_dict import DicJobs
from autosubmit.job.job import Job
from autosubmit.job.job_common import Status
from autosubmit.job.job_list import JobList
from autosubmit.job.job_list_persistence import JobListPersistenceDb
from autosubmitconfigparser.config.yamlparser import YAMLParserFactory


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


class TestJobList(unittest.TestCase):
    def setUp(self):
        self.experiment_id = 'random-id'
        self.as_conf = mock.Mock()
        self.as_conf.experiment_data = dict()
        self.as_conf.experiment_data["JOBS"] = dict()
        self.as_conf.jobs_data = self.as_conf.experiment_data["JOBS"]
        self.as_conf.experiment_data["PLATFORMS"] = dict()
        self.temp_directory = tempfile.mkdtemp()
        self.JobList = JobList(self.experiment_id, FakeBasicConfig, YAMLParserFactory(),
                               JobListPersistenceDb(self.temp_directory, 'db'), self.as_conf)
        self.date_list = ["20020201", "20020202", "20020203", "20020204", "20020205", "20020206", "20020207",
                          "20020208", "20020209", "20020210"]
        self.member_list = ["fc1", "fc2", "fc3", "fc4", "fc5", "fc6", "fc7", "fc8", "fc9", "fc10"]
        self.chunk_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.split_list = [1, 2, 3, 4, 5]
        self.JobList._date_list = self.date_list
        self.JobList._member_list = self.member_list
        self.JobList._chunk_list = self.chunk_list
        self.JobList._split_list = self.split_list

        # Define common test case inputs here
        self.relationships_dates = {
            "DATES_FROM": {
                "20020201": {
                    "MEMBERS_FROM": {
                        "fc2": {
                            "DATES_TO": "[20020201:20020202]*,20020203",
                            "MEMBERS_TO": "fc2",
                            "CHUNKS_TO": "all"
                        }
                    },
                    "SPLITS_FROM": {
                        "ALL": {
                            "SPLITS_TO": "1"
                        }
                    }
                }
            }
        }
        self.relationships_dates_optional = deepcopy(self.relationships_dates)
        self.relationships_dates_optional["DATES_FROM"]["20020201"]["MEMBERS_FROM"] = {
            "fc2?": {"DATES_TO": "20020201", "MEMBERS_TO": "fc2", "CHUNKS_TO": "all", "SPLITS_TO": "5"}}
        self.relationships_dates_optional["DATES_FROM"]["20020201"]["SPLITS_FROM"] = {"ALL": {"SPLITS_TO": "1?"}}

        self.relationships_members = {
            "MEMBERS_FROM": {
                "fc2": {
                    "SPLITS_FROM": {
                        "ALL": {
                            "DATES_TO": "20020201",
                            "MEMBERS_TO": "fc2",
                            "CHUNKS_TO": "all",
                            "SPLITS_TO": "1"
                        }
                    }
                }
            }
        }
        self.relationships_chunks = {
            "CHUNKS_FROM": {
                "1": {
                    "DATES_TO": "20020201",
                    "MEMBERS_TO": "fc2",
                    "CHUNKS_TO": "all",
                    "SPLITS_TO": "1"
                }
            }
        }
        self.relationships_chunks2 = {
            "CHUNKS_FROM": {
                "1": {
                    "DATES_TO": "20020201",
                    "MEMBERS_TO": "fc2",
                    "CHUNKS_TO": "all",
                    "SPLITS_TO": "1"
                },
                "2": {
                    "SPLITS_FROM": {
                        "5": {
                            "SPLITS_TO": "2"
                        }
                    }
                }
            }
        }

        self.relationships_splits = {
            "SPLITS_FROM": {
                "1": {
                    "DATES_TO": "20020201",
                    "MEMBERS_TO": "fc2",
                    "CHUNKS_TO": "all",
                    "SPLITS_TO": "1"
                }
            }
        }

        self.relationships_general = {
            "DATES_TO": "20020201",
            "MEMBERS_TO": "fc2",
            "CHUNKS_TO": "all",
            "SPLITS_TO": "1"
        }
        self.relationships_general_1_to_1 = {
            "DATES_TO": "20020201",
            "MEMBERS_TO": "fc2",
            "CHUNKS_TO": "all",
            "SPLITS_TO": "1*,2*,3*,4*,5*"
        }
        # Create a mock Job object
        self.mock_job = Mock(wraps=Job)

        # Set the attributes on the mock object
        self.mock_job.name = "Job1"
        self.mock_job.job_id = 1
        self.mock_job.status = Status.READY
        self.mock_job.priority = 1
        self.mock_job.date = None
        self.mock_job.member = None
        self.mock_job.chunk = None
        self.mock_job.split = None

    def test_unify_to_filter(self):
        """Test the _unify_to_fitler function"""
        # :param unified_filter: Single dictionary with all filters_to
        # :param filter_to: Current dictionary that contains the filters_to
        # :param filter_type: "DATES_TO", "MEMBERS_TO", "CHUNKS_TO", "SPLITS_TO"
        # :return: unified_filter
        unified_filter = \
            {
                "DATES_TO": "20020201",
                "MEMBERS_TO": "fc2",
                "CHUNKS_TO": "all",
                "SPLITS_TO": "1"
            }
        filter_to = \
            {
                "DATES_TO": "20020205,[20020207:20020208]",
                "MEMBERS_TO": "fc2,fc3",
                "CHUNKS_TO": "all"
            }
        filter_type = "DATES_TO"
        result = self.JobList._unify_to_filter(unified_filter, filter_to, filter_type)
        expected_output = \
            {
                "DATES_TO": "20020201,20020205,20020207,20020208,",
                "MEMBERS_TO": "fc2",
                "CHUNKS_TO": "all",
                "SPLITS_TO": "1"
            }
        self.assertEqual(result, expected_output)

    def test_simple_dependency(self):
        result_d = self.JobList._check_dates({}, self.mock_job)
        result_m = self.JobList._check_members({}, self.mock_job)
        result_c = self.JobList._check_chunks({}, self.mock_job)
        result_s = self.JobList._check_splits({}, self.mock_job)
        self.assertEqual(result_d, {})
        self.assertEqual(result_m, {})
        self.assertEqual(result_c, {})
        self.assertEqual(result_s, {})

    def test_parse_filters_to_check(self):
        """Test the _parse_filters_to_check function"""
        result = self.JobList._parse_filters_to_check("20020201,20020202,20020203", self.date_list)
        expected_output = ["20020201", "20020202", "20020203"]
        self.assertEqual(result, expected_output)
        result = self.JobList._parse_filters_to_check("20020201,[20020203:20020205]", self.date_list)
        expected_output = ["20020201", "20020203", "20020204", "20020205"]
        self.assertEqual(result, expected_output)
        result = self.JobList._parse_filters_to_check("[20020201:20020203],[20020205:20020207]", self.date_list)
        expected_output = ["20020201", "20020202", "20020203", "20020205", "20020206", "20020207"]
        self.assertEqual(result, expected_output)
        result = self.JobList._parse_filters_to_check("20020201", self.date_list)
        expected_output = ["20020201"]
        self.assertEqual(result, expected_output)

    def test_parse_filter_to_check(self):
        # Call the function to get the result
        # Value can have the following formats:
        # a range: [0:], [:N], [0:N], [:-1], [0:N:M] ...
        # a value: N
        # a range with step: [0::M], [::2], [0::3], [::3] ...
        result = self.JobList._parse_filter_to_check("20020201", self.date_list)
        expected_output = ["20020201"]
        self.assertEqual(result, expected_output)
        result = self.JobList._parse_filter_to_check("[20020201:20020203]", self.date_list)
        expected_output = ["20020201", "20020202", "20020203"]
        self.assertEqual(result, expected_output)
        result = self.JobList._parse_filter_to_check("[20020201:20020203:2]", self.date_list)
        expected_output = ["20020201", "20020203"]
        self.assertEqual(result, expected_output)
        result = self.JobList._parse_filter_to_check("[20020202:]", self.date_list)
        expected_output = self.date_list[1:]
        self.assertEqual(result, expected_output)
        result = self.JobList._parse_filter_to_check("[:20020203]", self.date_list)
        expected_output = self.date_list[:3]
        self.assertEqual(result, expected_output)
        result = self.JobList._parse_filter_to_check("[::2]", self.date_list)
        expected_output = self.date_list[::2]
        self.assertEqual(result, expected_output)
        result = self.JobList._parse_filter_to_check("[20020203::]", self.date_list)
        expected_output = self.date_list[2:]
        self.assertEqual(result, expected_output)
        result = self.JobList._parse_filter_to_check("[:20020203:]", self.date_list)
        expected_output = self.date_list[:3]
        self.assertEqual(result, expected_output)
        # test with a member N:N
        result = self.JobList._parse_filter_to_check("[fc2:fc3]", self.member_list)
        expected_output = ["fc2", "fc3"]
        self.assertEqual(result, expected_output)
        # test with a chunk
        result = self.JobList._parse_filter_to_check("[1:2]", self.chunk_list, level_to_check="CHUNKS_FROM")
        expected_output = [1, 2]
        self.assertEqual(result, expected_output)
        # test with a split
        result = self.JobList._parse_filter_to_check("[1:2]", self.split_list, level_to_check="SPLITS_FROM")
        expected_output = [1, 2]
        self.assertEqual(result, expected_output)

    def test_check_dates(self):
        # Call the function to get the result
        self.mock_job.date = datetime.strptime("20020201", "%Y%m%d")
        self.mock_job.member = "fc2"
        self.mock_job.chunk = 1
        self.mock_job.split = 1
        result = self.JobList._check_dates(self.relationships_dates, self.mock_job)
        expected_output = {
            "DATES_TO": "20020201*,20020202*,20020203",
            "MEMBERS_TO": "fc2",
            "CHUNKS_TO": "all",
            "SPLITS_TO": "1"
        }
        self.assertEqual(result, expected_output)
        # failure
        self.mock_job.date = datetime.strptime("20020301", "%Y%m%d")
        result = self.JobList._check_dates(self.relationships_dates, self.mock_job)
        self.assertEqual(result, {})

    def test_check_members(self):
        # Call the function to get the result
        self.mock_job.date = datetime.strptime("20020201", "%Y%m%d")
        self.mock_job.member = "fc2"

        result = self.JobList._check_members(self.relationships_members, self.mock_job)
        expected_output = {
            "DATES_TO": "20020201",
            "MEMBERS_TO": "fc2",
            "CHUNKS_TO": "all",
            "SPLITS_TO": "1"
        }
        self.assertEqual(result, expected_output)
        self.mock_job.member = "fc3"
        result = self.JobList._check_members(self.relationships_members, self.mock_job)
        self.assertEqual(result, {})
        # FAILURE
        self.mock_job.member = "fc99"
        result = self.JobList._check_members(self.relationships_members, self.mock_job)
        self.assertEqual(result, {})

    def test_check_splits(self):
        # Call the function to get the result

        self.mock_job.split = 1
        result = self.JobList._check_splits(self.relationships_splits, self.mock_job)
        expected_output = {
            "DATES_TO": "20020201",
            "MEMBERS_TO": "fc2",
            "CHUNKS_TO": "all",
            "SPLITS_TO": "1"
        }
        self.assertEqual(result, expected_output)
        self.mock_job.split = 2
        result = self.JobList._check_splits(self.relationships_splits, self.mock_job)
        self.assertEqual(result, {})
        # failure
        self.mock_job.split = 99
        result = self.JobList._check_splits(self.relationships_splits, self.mock_job)
        self.assertEqual(result, {})

    def test_check_chunks(self):
        # Call the function to get the result

        self.mock_job.chunk = 1
        result = self.JobList._check_chunks(self.relationships_chunks, self.mock_job)
        expected_output = {
            "DATES_TO": "20020201",
            "MEMBERS_TO": "fc2",
            "CHUNKS_TO": "all",
            "SPLITS_TO": "1"
        }
        self.assertEqual(result, expected_output)
        self.mock_job.chunk = 2
        result = self.JobList._check_chunks(self.relationships_chunks, self.mock_job)
        self.assertEqual(result, {})
        # failure
        self.mock_job.chunk = 99
        result = self.JobList._check_chunks(self.relationships_chunks, self.mock_job)
        self.assertEqual(result, {})

    def test_check_general(self):
        # Call the function to get the result

        self.mock_job.date = datetime.strptime("20020201", "%Y%m%d")
        self.mock_job.member = "fc2"
        self.mock_job.chunk = 1
        self.mock_job.split = 1
        result = self.JobList._filter_current_job(self.mock_job, self.relationships_general)
        expected_output = {
            "DATES_TO": "20020201",
            "MEMBERS_TO": "fc2",
            "CHUNKS_TO": "all",
            "SPLITS_TO": "1"
        }
        self.assertEqual(result, expected_output)

    def test_check_relationship(self):
        relationships = {'MEMBERS_FROM': {
            'TestMember,   TestMember2,TestMember3   ': {'CHUNKS_TO': 'None', 'DATES_TO': 'None', 'FROM_STEP': None,
                                                         'MEMBERS_TO': 'None', 'STATUS': None}}}
        level_to_check = "MEMBERS_FROM"
        value_to_check = "TestMember"
        result = self.JobList._check_relationship(relationships, level_to_check, value_to_check)
        expected_output = [
            {'CHUNKS_TO': 'None', 'DATES_TO': 'None', 'FROM_STEP': None, 'MEMBERS_TO': 'None', 'STATUS': None}]
        self.assertEqual(result, expected_output)
        value_to_check = "TestMember2"
        result = self.JobList._check_relationship(relationships, level_to_check, value_to_check)
        expected_output = [
            {'CHUNKS_TO': 'None', 'DATES_TO': 'None', 'FROM_STEP': None, 'MEMBERS_TO': 'None', 'STATUS': None}]
        self.assertEqual(result, expected_output)
        value_to_check = "TestMember3"
        result = self.JobList._check_relationship(relationships, level_to_check, value_to_check)
        expected_output = [
            {'CHUNKS_TO': 'None', 'DATES_TO': 'None', 'FROM_STEP': None, 'MEMBERS_TO': 'None', 'STATUS': None}]
        self.assertEqual(result, expected_output)
        value_to_check = "TestMember   "
        result = self.JobList._check_relationship(relationships, level_to_check, value_to_check)
        expected_output = [
            {'CHUNKS_TO': 'None', 'DATES_TO': 'None', 'FROM_STEP': None, 'MEMBERS_TO': 'None', 'STATUS': None}]
        self.assertEqual(result, expected_output)
        value_to_check = "   TestMember"
        result = self.JobList._check_relationship(relationships, level_to_check, value_to_check)
        expected_output = [
            {'CHUNKS_TO': 'None', 'DATES_TO': 'None', 'FROM_STEP': None, 'MEMBERS_TO': 'None', 'STATUS': None}]
        self.assertEqual(result, expected_output)

    def test_add_special_conditions(self):
        # Method from job_list
        job = Job("child", 1, Status.READY, 1)
        job.section = "child_one"
        job.date = datetime.strptime("20200128", "%Y%m%d")
        job.member = "fc0"
        job.chunk = 1
        job.split = 1
        job.splits = 1
        job.max_checkpoint_step = 0
        special_conditions = {"STATUS": "RUNNING", "FROM_STEP": "2"}
        only_marked_status = False
        filters_to_apply = {"DATES_TO": "all", "MEMBERS_TO": "all", "CHUNKS_TO": "all", "SPLITS_TO": "all"}
        parent = Job("parent", 1, Status.READY, 1)
        parent.section = "parent_one"
        parent.date = datetime.strptime("20200128", "%Y%m%d")
        parent.member = "fc0"
        parent.chunk = 1
        parent.split = 1
        parent.splits = 1
        parent.max_checkpoint_step = 0
        job.status = Status.READY
        job_list = Mock(wraps=self.JobList)
        job_list._job_list = [job, parent]
        job_list.add_special_conditions(job, special_conditions, filters_to_apply, parent)
        # self.JobList.jobs_edges
        # job.edges = self.JobList.jobs_edges[job.name]
        # assert
        self.assertEqual(job.max_checkpoint_step, 2)
        value = job.edge_info.get("RUNNING", "").get("parent", ())
        self.assertEqual((value[0].name, value[1]), (parent.name, "2"))
        self.assertEqual(len(job.edge_info.get("RUNNING", "")), 1)

        self.assertEqual(str(job_list.jobs_edges.get("RUNNING", ())), str({job}))
        only_marked_status = False
        parent2 = Job("parent2", 1, Status.READY, 1)
        parent2.section = "parent_two"
        parent2.date = datetime.strptime("20200128", "%Y%m%d")
        parent2.member = "fc0"
        parent2.chunk = 1

        job_list.add_special_conditions(job, special_conditions, filters_to_apply, parent2)
        value = job.edge_info.get("RUNNING", "").get("parent2", ())
        self.assertEqual(len(job.edge_info.get("RUNNING", "")), 2)
        self.assertEqual((value[0].name, value[1]), (parent2.name, "2"))
        self.assertEqual(str(job_list.jobs_edges.get("RUNNING", ())), str({job}))
        job_list.add_special_conditions(job, special_conditions, filters_to_apply, parent2)
        self.assertEqual(len(job.edge_info.get("RUNNING", "")), 2)

if __name__ == '__main__':
    unittest.main()
