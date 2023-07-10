import mock
import unittest
from copy import deepcopy
from datetime import datetime

from autosubmit.job.job import Job
from autosubmit.job.job_common import Status
from autosubmit.job.job_list import JobList


class TestJobList(unittest.TestCase):
    def setUp(self):
        self.date_list = ["20020201", "20020202", "20020203", "20020204", "20020205", "20020206", "20020207", "20020208", "20020209", "20020210"]
        self.member_list = ["fc1", "fc2", "fc3", "fc4", "fc5", "fc6", "fc7", "fc8", "fc9", "fc10"]
        self.chunk_list = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        self.split_list = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        # Define common test case inputs here
        self.relationships_dates = {
                "DATES_FROM": {
                    "20020201": {
                        "MEMBERS_FROM": {
                            "fc2": {
                                "DATES_TO": "20020201",
                                "MEMBERS_TO": "fc2",
                                "CHUNKS_TO": "ALL"
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
        self.relationships_dates_optional["DATES_FROM"]["20020201"]["MEMBERS_FROM"] = { "fc2?": { "DATES_TO": "20020201", "MEMBERS_TO": "fc2", "CHUNKS_TO": "ALL", "SPLITS_TO": "5" } }
        self.relationships_dates_optional["DATES_FROM"]["20020201"]["SPLITS_FROM"] = { "ALL": { "SPLITS_TO": "1?" } }

        self.relationships_members = {
                "MEMBERS_FROM": {
                    "fc2": {
                        "SPLITS_FROM": {
                            "ALL": {
                                "DATES_TO": "20020201",
                                "MEMBERS_TO": "fc2",
                                "CHUNKS_TO": "ALL",
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
                        "CHUNKS_TO": "ALL",
                        "SPLITS_TO": "1"
                    }
                }
            }
        self.relationships_chunks2 = {
                "CHUNKS_FROM": {
                    "1": {
                        "DATES_TO": "20020201",
                        "MEMBERS_TO": "fc2",
                        "CHUNKS_TO": "ALL",
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
                        "CHUNKS_TO": "ALL",
                        "SPLITS_TO": "1"
                    }
                }
            }

        self.relationships_general = {
                "DATES_TO": "20020201",
                "MEMBERS_TO": "fc2",
                "CHUNKS_TO": "ALL",
                "SPLITS_TO": "1"
            }
        # Create a mock Job object
        self.mock_job = mock.MagicMock(spec=Job)

        # Set the attributes on the mock object
        self.mock_job.name = "Job1"
        self.mock_job.job_id = 1
        self.mock_job.status = Status.READY
        self.mock_job.priority = 1
        self.mock_job.date = None
        self.mock_job.member = None
        self.mock_job.chunk = None
        self.mock_job.split = None

    def test_parse_checkpoint(self):
        data = "r2"
        correct = {"FROM_STEP": '2', "STATUS":Status.RUNNING}
        result = JobList._parse_checkpoint(data)
        self.assertEqual(result, correct)
        data = "r"
        correct = {"FROM_STEP": '1', "STATUS":Status.RUNNING}
        result = JobList._parse_checkpoint(data)
        self.assertEqual(result, correct)
        data = "f2"
        correct = {"FROM_STEP": '2', "STATUS":Status.FAILED}
        result = JobList._parse_checkpoint(data)
        self.assertEqual(result, correct)
        data = "f"
        correct = {"FROM_STEP": '1', "STATUS":Status.FAILED}
        result = JobList._parse_checkpoint(data)
        self.assertEqual(result, correct)
        data = "s"
        correct = {"FROM_STEP": None, "STATUS":Status.SUBMITTED}
        result = JobList._parse_checkpoint(data)
        self.assertEqual(result, correct)
        data = "s2"
        correct = {"FROM_STEP": None, "STATUS":Status.SUBMITTED}
        result = JobList._parse_checkpoint(data)
        self.assertEqual(result, correct)
        data = "q"
        correct = {"FROM_STEP": None, "STATUS":Status.QUEUING}
        result = JobList._parse_checkpoint(data)
        self.assertEqual(result, correct)
        data = "q2"
        correct = {"FROM_STEP": None, "STATUS":Status.QUEUING}
        result = JobList._parse_checkpoint(data)
        self.assertEqual(result, correct)


    def test_simple_dependency(self):
        result_d = JobList._check_dates({}, self.mock_job)
        result_m = JobList._check_members({}, self.mock_job)
        result_c = JobList._check_chunks({}, self.mock_job)
        result_s = JobList._check_splits({}, self.mock_job)
        self.assertEqual(result_d, {})
        self.assertEqual(result_m, {})
        self.assertEqual(result_c, {})
        self.assertEqual(result_s, {})
    def test_check_dates_optional(self):
        self.mock_job.date = datetime.strptime("20020201", "%Y%m%d")
        self.mock_job.member = "fc2"
        self.mock_job.chunk = 1
        self.mock_job.split = 1
        result = JobList._check_dates(self.relationships_dates_optional, self.mock_job)
        expected_output = {
                "DATES_TO": "20020201?",
                "MEMBERS_TO": "fc2?",
                "CHUNKS_TO": "ALL?",
                "SPLITS_TO": "1?"
            }
        self.assertEqual(result, expected_output)
    def test_parse_filters_to_check(self):
        result = JobList._parse_filters_to_check("20020201,20020202,20020203",self.date_list)
        expected_output = ["20020201","20020202","20020203"]
        self.assertEqual(result, expected_output)
        result = JobList._parse_filters_to_check("20020201,[20020203:20020205]",self.date_list)
        

    def test_parse_filter_to_check(self):
        # Call the function to get the result
        # Value can have the following formats:
        # a range: [0:], [:N], [0:N], [:-1], [0:N:M] ...
        # a value: N
        # a range with step: [0::M], [::2], [0::3], [::3] ...
        result = JobList._parse_filter_to_check("20020201",self.date_list)
        expected_output = ["20020201"]
        self.assertEqual(result, expected_output)
        result = JobList._parse_filter_to_check("[20020201:20020203]",self.date_list)
        expected_output = ["20020201","20020202","20020203"]
        self.assertEqual(result, expected_output)
        result = JobList._parse_filter_to_check("[20020201:20020203:2]",self.date_list)
        expected_output = ["20020201","20020203"]
        self.assertEqual(result, expected_output)
        result = JobList._parse_filter_to_check("[20020202:]",self.date_list)
        expected_output = self.date_list[1:]
        self.assertEqual(result, expected_output)
        result = JobList._parse_filter_to_check("[:20020203]",self.date_list)
        expected_output = self.date_list[:3]
        self.assertEqual(result, expected_output)
        result = JobList._parse_filter_to_check("[::2]",self.date_list)
        expected_output = self.date_list[::2]
        self.assertEqual(result, expected_output)
        result = JobList._parse_filter_to_check("[20020203::]",self.date_list)
        expected_output = self.date_list[2:]
        self.assertEqual(result, expected_output)
        result = JobList._parse_filter_to_check("[:20020203:]",self.date_list)
        expected_output = self.date_list[:3]
        self.assertEqual(result, expected_output)



    def test_check_dates(self):
        # Call the function to get the result
        self.mock_job.date = datetime.strptime("20020201", "%Y%m%d")
        self.mock_job.member = "fc2"
        self.mock_job.chunk = 1
        self.mock_job.split = 1
        result = JobList._check_dates(self.relationships_dates, self.mock_job)
        expected_output = {
                "DATES_TO": "20020201",
                "MEMBERS_TO": "fc2",
                "CHUNKS_TO": "ALL",
                "SPLITS_TO": "1"
            }
        self.assertEqual(result, expected_output)
        self.mock_job.date = datetime.strptime("20020202", "%Y%m%d")
        result = JobList._check_dates(self.relationships_dates, self.mock_job)
        self.assertEqual(result, {})
    def test_check_members(self):
        # Call the function to get the result
        self.mock_job.date = datetime.strptime("20020201", "%Y%m%d")
        self.mock_job.member = "fc2"

        result = JobList._check_members(self.relationships_members, self.mock_job)
        expected_output = {
                "DATES_TO": "20020201",
                "MEMBERS_TO": "fc2",
                "CHUNKS_TO": "ALL",
                "SPLITS_TO": "1"
            }
        self.assertEqual(result, expected_output)
        self.mock_job.member = "fc3"
        result = JobList._check_members(self.relationships_members, self.mock_job)
        self.assertEqual(result, {})

    def test_check_splits(self):
        # Call the function to get the result

        self.mock_job.split = 1
        result = JobList._check_splits(self.relationships_splits, self.mock_job)
        expected_output = {
                "DATES_TO": "20020201",
                "MEMBERS_TO": "fc2",
                "CHUNKS_TO": "ALL",
                "SPLITS_TO": "1"
            }
        self.assertEqual(result, expected_output)
        self.mock_job.split = 2
        result = JobList._check_splits(self.relationships_splits, self.mock_job)
        self.assertEqual(result, {})
    def test_check_chunks(self):
        # Call the function to get the result

        self.mock_job.chunk = 1
        result = JobList._check_chunks(self.relationships_chunks, self.mock_job)
        expected_output = {
                "DATES_TO": "20020201",
                "MEMBERS_TO": "fc2",
                "CHUNKS_TO": "ALL",
                "SPLITS_TO": "1"
            }
        self.assertEqual(result, expected_output)
        self.mock_job.chunk = 2
        result = JobList._check_chunks(self.relationships_chunks, self.mock_job)
        self.assertEqual(result, {})
        # test splits_from
        self.mock_job.split = 5
        result = JobList._check_chunks(self.relationships_chunks2, self.mock_job)
        expected_output2 = {
                "SPLITS_TO": "2"
            }
        self.assertEqual(result, expected_output2)
        self.mock_job.split = 1
        result = JobList._check_chunks(self.relationships_chunks2, self.mock_job)
        self.assertEqual(result, {})

    def test_check_general(self):
        # Call the function to get the result

        self.mock_job.date = datetime.strptime("20020201", "%Y%m%d")
        self.mock_job.member = "fc2"
        self.mock_job.chunk = 1
        self.mock_job.split = 1
        result = JobList._filter_current_job(self.mock_job,self.relationships_general)
        expected_output = {
                "DATES_TO": "20020201",
                "MEMBERS_TO": "fc2",
                "CHUNKS_TO": "ALL",
                "SPLITS_TO": "1"
            }
        self.assertEqual(result, expected_output)


    def test_valid_parent(self):
        # Call the function to get the result

        date_list = ["20020201"]
        member_list = ["fc1", "fc2", "fc3"]
        chunk_list = [1, 2, 3]
        is_a_natural_relation = False
        # Filter_to values
        filter_ = {
                "DATES_TO": "20020201",
                "MEMBERS_TO": "fc2",
                "CHUNKS_TO": "ALL",
                "SPLITS_TO": "1"
            }
        # PArent job values
        self.mock_job.date = datetime.strptime("20020201", "%Y%m%d")
        self.mock_job.member = "fc2"
        self.mock_job.chunk = 1
        self.mock_job.split = 1
        result = JobList._valid_parent(self.mock_job, date_list, member_list, chunk_list, is_a_natural_relation, filter_)
        # it returns a tuple, the first element is the result, the second is the optional flag
        self.assertEqual(result, (True,False))
        filter_ = {
                "DATES_TO": "20020201",
                "MEMBERS_TO": "fc2",
                "CHUNKS_TO": "ALL",
                "SPLITS_TO": "1?"
            }
        result = JobList._valid_parent(self.mock_job, date_list, member_list, chunk_list, is_a_natural_relation, filter_)
        self.assertEqual(result, (True,True))


if __name__ == '__main__':
    unittest.main()
