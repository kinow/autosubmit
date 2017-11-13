from unittest import TestCase
from mock import Mock
from autosubmit.job.job_packager import JobPackager
from autosubmit.job.job_packages import JobPackageVertical
from autosubmit.job.job import Job
from autosubmit.job.job_list import JobList
from bscearth.utils.config_parser import ConfigParserFactory
from autosubmit.job.job_list_persistence import JobListPersistenceDb
from autosubmit.job.job_common import Status
from random import randrange

class TestWrappers(TestCase):

    def setUp(self):
        self.experiment_id = 'random-id'
        self.platform = Mock()
        self.job_list = JobList(self.experiment_id, FakeBasicConfig, ConfigParserFactory(),
                                JobListPersistenceDb('.', '.'))

    def test_returned_packages(self):
        '''
            [s2]
            RUNNING = chunk
            DEPENDENCIES = s1 s2-1

            [s3]
            RUNNING = chunk
            DEPENDENCIES = s2

            [s4]
            RUNNING = chunk
            DEPENDENCIES = s3

        '''
        d1_m1_s1 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_s1', '00:50')
        d1_m2_s1 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_s1', '00:50')

        d1_m1_1_s2 = self._createDummyJob(Status.READY, 'expid_d1_m1_1_s2', '00:10')
        d1_m1_1_s2.add_parent(d1_m1_s1)

        d1_m1_2_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s2', '00:10')
        d1_m1_2_s2.add_parent(d1_m1_1_s2)

        d1_m1_3_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s2', '00:10')
        d1_m1_3_s2.add_parent(d1_m1_2_s2)

        d1_m1_4_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s2', '00:10')
        d1_m1_4_s2.add_parent(d1_m1_3_s2)

        d1_m2_1_s2 = self._createDummyJob(Status.READY, 'expid_d1_m2_1_s2', '00:10')
        d1_m2_1_s2.add_parent(d1_m2_s1)

        d1_m2_2_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s2', '00:10')
        d1_m2_2_s2.add_parent(d1_m2_1_s2)

        d1_m2_3_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s2', '00:10')
        d1_m2_3_s2.add_parent(d1_m2_2_s2)

        d1_m2_4_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s2', '00:10')
        d1_m2_4_s2.add_parent(d1_m2_3_s2)

        d1_m1_1_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_1_s3', '00:20')
        d1_m1_1_s3.add_parent(d1_m1_1_s2)

        d1_m1_2_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s3', '00:20')
        d1_m1_2_s3.add_parent(d1_m1_2_s2)

        d1_m1_3_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s3', '00:20')
        d1_m1_3_s3.add_parent(d1_m1_3_s2)

        d1_m1_4_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s3', '00:20')
        d1_m1_4_s3.add_parent(d1_m1_4_s2)

        d1_m2_1_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s3', '00:20')
        d1_m2_1_s3.add_parent(d1_m2_1_s2)

        d1_m2_2_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s3', '00:20')
        d1_m2_2_s3.add_parent(d1_m2_2_s2)

        d1_m2_3_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s3', '00:20')
        d1_m2_3_s3.add_parent(d1_m2_3_s2)

        d1_m2_4_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s3', '00:20')
        d1_m2_4_s3.add_parent(d1_m2_4_s2)

        d1_m1_1_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_1_s4', '00:30')
        d1_m1_1_s4.add_parent(d1_m1_1_s3)

        d1_m1_2_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s4', '00:30')
        d1_m1_2_s4.add_parent(d1_m1_2_s3)

        d1_m1_3_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s4', '00:30')
        d1_m1_3_s4.add_parent(d1_m1_3_s3)

        d1_m1_4_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s4', '00:30')
        d1_m1_4_s4.add_parent(d1_m1_4_s3)

        d1_m2_1_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s4', '00:30')
        d1_m2_1_s4.add_parent(d1_m2_1_s3)

        d1_m2_2_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s4', '00:30')
        d1_m2_2_s4.add_parent(d1_m2_2_s3)

        d1_m2_3_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s4', '00:30')
        d1_m2_3_s4.add_parent(d1_m2_3_s3)

        d1_m2_4_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s4', '00:30')
        d1_m2_4_s4.add_parent(d1_m2_4_s3)

        self.job_list._job_list = [d1_m1_s1, d1_m2_s1, d1_m1_1_s2, d1_m1_2_s2,
                                   d1_m1_3_s2, d1_m1_4_s2, d1_m2_1_s2, d1_m2_2_s2,
                                   d1_m2_3_s2, d1_m2_4_s2, d1_m1_1_s3, d1_m1_2_s3,
                                   d1_m1_3_s3, d1_m1_4_s3, d1_m2_1_s3, d1_m2_2_s3,
                                   d1_m2_3_s3, d1_m2_4_s3, d1_m1_1_s4, d1_m1_2_s4,
                                   d1_m1_3_s4, d1_m1_4_s4, d1_m2_1_s4, d1_m2_2_s4,
                                   d1_m2_3_s4, d1_m2_4_s4]

        self.job_list._ordered_jobs_by_date_member["d1"] = dict()
        self.job_list._ordered_jobs_by_date_member["d1"]["m1"] = [d1_m1_1_s2, d1_m1_1_s3, d1_m1_2_s2, d1_m1_2_s3, d1_m1_3_s2,
                                                                  d1_m1_3_s3, d1_m1_4_s2, d1_m1_4_s3]

        self.job_list._ordered_jobs_by_date_member["d1"]["m2"] = [d1_m2_1_s2, d1_m2_1_s3, d1_m2_2_s2, d1_m2_2_s3, d1_m2_3_s2,
                                                                  d1_m2_3_s3, d1_m2_4_s2, d1_m2_4_s3]

        wrapper_expression = "s2 s3"
        max_jobs = 18
        max_wrapped_jobs = 18
        max_wallclock = '10:00'

        section_list = [d1_m1_1_s2, d1_m2_1_s2]

        returned_packages = JobPackager._build_vertical_packages(self.job_list.get_ordered_jobs_by_date_member(), wrapper_expression, section_list, max_jobs, max_wallclock, max_wrapped_jobs)

        package_m1_s2_s3 = [d1_m1_1_s2, d1_m1_1_s3, d1_m1_2_s2, d1_m1_2_s3, d1_m1_3_s2, d1_m1_3_s3, d1_m1_4_s2,
                            d1_m1_4_s3]
        package_m2_s2_s3 = [d1_m2_1_s2, d1_m2_1_s3, d1_m2_2_s2, d1_m2_2_s3, d1_m2_3_s2, d1_m2_3_s3, d1_m2_4_s2,
                            d1_m2_4_s3]

        packages = [JobPackageVertical(package_m1_s2_s3), JobPackageVertical(package_m2_s2_s3)]

        returned_packages = returned_packages[0]
        for i in range(0, len(returned_packages)):
            self.assertListEqual(returned_packages[i]._jobs, packages[i]._jobs)

    def test_returned_packages_parent_running(self):
        '''
            [s2]
            RUNNING = chunk
            DEPENDENCIES = s1 s2-1

            [s3]
            RUNNING = chunk
            DEPENDENCIES = s2

            [s4]
            RUNNING = chunk
            DEPENDENCIES = s3

        '''
        d1_m1_s1 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_s1', '00:50')
        d1_m2_s1 = self._createDummyJob(Status.RUNNING, 'expid_d1_m1_s1', '00:50')

        d1_m1_1_s2 = self._createDummyJob(Status.READY, 'expid_d1_m1_1_s2', '00:10')
        d1_m1_1_s2.add_parent(d1_m1_s1)

        d1_m1_2_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s2', '00:10')
        d1_m1_2_s2.add_parent(d1_m1_1_s2)

        d1_m1_3_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s2', '00:10')
        d1_m1_3_s2.add_parent(d1_m1_2_s2)

        d1_m1_4_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s2', '00:10')
        d1_m1_4_s2.add_parent(d1_m1_3_s2)

        d1_m2_1_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s2', '00:10')
        d1_m2_1_s2.add_parent(d1_m2_s1)

        d1_m2_2_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s2', '00:10')
        d1_m2_2_s2.add_parent(d1_m2_1_s2)

        d1_m2_3_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s2', '00:10')
        d1_m2_3_s2.add_parent(d1_m2_2_s2)

        d1_m2_4_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s2', '00:10')
        d1_m2_4_s2.add_parent(d1_m2_3_s2)

        d1_m1_1_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_1_s3', '00:20')
        d1_m1_1_s3.add_parent(d1_m1_1_s2)

        d1_m1_2_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s3', '00:20')
        d1_m1_2_s3.add_parent(d1_m1_2_s2)

        d1_m1_3_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s3', '00:20')
        d1_m1_3_s3.add_parent(d1_m1_3_s2)

        d1_m1_4_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s3', '00:20')
        d1_m1_4_s3.add_parent(d1_m1_4_s2)

        d1_m2_1_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s3', '00:20')
        d1_m2_1_s3.add_parent(d1_m2_1_s2)

        d1_m2_2_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s3', '00:20')
        d1_m2_2_s3.add_parent(d1_m2_2_s2)

        d1_m2_3_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s3', '00:20')
        d1_m2_3_s3.add_parent(d1_m2_3_s2)

        d1_m2_4_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s3', '00:20')
        d1_m2_4_s3.add_parent(d1_m2_4_s2)

        d1_m1_1_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_1_s4', '00:30')
        d1_m1_1_s4.add_parent(d1_m1_1_s3)

        d1_m1_2_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s4', '00:30')
        d1_m1_2_s4.add_parent(d1_m1_2_s3)

        d1_m1_3_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s4', '00:30')
        d1_m1_3_s4.add_parent(d1_m1_3_s3)

        d1_m1_4_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s4', '00:30')
        d1_m1_4_s4.add_parent(d1_m1_4_s3)

        d1_m2_1_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s4', '00:30')
        d1_m2_1_s4.add_parent(d1_m2_1_s3)

        d1_m2_2_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s4', '00:30')
        d1_m2_2_s4.add_parent(d1_m2_2_s3)

        d1_m2_3_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s4', '00:30')
        d1_m2_3_s4.add_parent(d1_m2_3_s3)

        d1_m2_4_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s4', '00:30')
        d1_m2_4_s4.add_parent(d1_m2_4_s3)

        self.job_list._job_list = [d1_m1_s1, d1_m2_s1, d1_m1_1_s2, d1_m1_2_s2,
                                   d1_m1_3_s2, d1_m1_4_s2, d1_m2_1_s2, d1_m2_2_s2,
                                   d1_m2_3_s2, d1_m2_4_s2, d1_m1_1_s3, d1_m1_2_s3,
                                   d1_m1_3_s3, d1_m1_4_s3, d1_m2_1_s3, d1_m2_2_s3,
                                   d1_m2_3_s3, d1_m2_4_s3, d1_m1_1_s4, d1_m1_2_s4,
                                   d1_m1_3_s4, d1_m1_4_s4, d1_m2_1_s4, d1_m2_2_s4,
                                   d1_m2_3_s4, d1_m2_4_s4]

        self.job_list._ordered_jobs_by_date_member["d1"] = dict()
        self.job_list._ordered_jobs_by_date_member["d1"]["m1"] = [d1_m1_1_s2, d1_m1_1_s3, d1_m1_2_s2, d1_m1_2_s3, d1_m1_3_s2,
                                                                  d1_m1_3_s3, d1_m1_4_s2, d1_m1_4_s3]

        self.job_list._ordered_jobs_by_date_member["d1"]["m2"] = [d1_m2_1_s2, d1_m2_1_s3, d1_m2_2_s2, d1_m2_2_s3, d1_m2_3_s2,
                                                                  d1_m2_3_s3, d1_m2_4_s2, d1_m2_4_s3]

        wrapper_expression = "s2 s3"
        max_jobs = 18
        max_wrapped_jobs = 18
        max_wallclock = '10:00'

        section_list = [d1_m1_1_s2]

        returned_packages = JobPackager._build_vertical_packages(self.job_list.get_ordered_jobs_by_date_member(), wrapper_expression, section_list, max_jobs, max_wallclock, max_wrapped_jobs)

        package_m1_s2_s3 = [d1_m1_1_s2, d1_m1_1_s3, d1_m1_2_s2, d1_m1_2_s3, d1_m1_3_s2, d1_m1_3_s3, d1_m1_4_s2,
                            d1_m1_4_s3]

        packages = [JobPackageVertical(package_m1_s2_s3)]

        returned_packages = returned_packages[0]
        for i in range(0, len(returned_packages)):
            self.assertListEqual(returned_packages[i]._jobs, packages[i]._jobs)

    def test_returned_packages_parent_failed(self):
        '''
        [s2]
        RUNNING = chunk
        DEPENDENCIES = s1 s2-1

        [s3]
        RUNNING = chunk
        DEPENDENCIES = s2

        [s4]
        RUNNING = chunk
        DEPENDENCIES = s3
        '''
        d1_m1_s1 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_s1', '00:50')
        d1_m2_s1 = self._createDummyJob(Status.FAILED, 'expid_d1_m1_s1', '00:50')

        d1_m1_1_s2 = self._createDummyJob(Status.READY, 'expid_d1_m1_1_s2', '00:10')
        d1_m1_1_s2.add_parent(d1_m1_s1)

        d1_m1_2_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s2', '00:10')
        d1_m1_2_s2.add_parent(d1_m1_1_s2)

        d1_m1_3_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s2', '00:10')
        d1_m1_3_s2.add_parent(d1_m1_2_s2)

        d1_m1_4_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s2', '00:10')
        d1_m1_4_s2.add_parent(d1_m1_3_s2)

        d1_m2_1_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s2', '00:10')
        d1_m2_1_s2.add_parent(d1_m2_s1)

        d1_m2_2_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s2', '00:10')
        d1_m2_2_s2.add_parent(d1_m2_1_s2)

        d1_m2_3_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s2', '00:10')
        d1_m2_3_s2.add_parent(d1_m2_2_s2)

        d1_m2_4_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s2', '00:10')
        d1_m2_4_s2.add_parent(d1_m2_3_s2)

        d1_m1_1_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_1_s3', '00:20')
        d1_m1_1_s3.add_parent(d1_m1_1_s2)

        d1_m1_2_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s3', '00:20')
        d1_m1_2_s3.add_parent(d1_m1_2_s2)

        d1_m1_3_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s3', '00:20')
        d1_m1_3_s3.add_parent(d1_m1_3_s2)

        d1_m1_4_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s3', '00:20')
        d1_m1_4_s3.add_parent(d1_m1_4_s2)

        d1_m2_1_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s3', '00:20')
        d1_m2_1_s3.add_parent(d1_m2_1_s2)

        d1_m2_2_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s3', '00:20')
        d1_m2_2_s3.add_parent(d1_m2_2_s2)

        d1_m2_3_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s3', '00:20')
        d1_m2_3_s3.add_parent(d1_m2_3_s2)

        d1_m2_4_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s3', '00:20')
        d1_m2_4_s3.add_parent(d1_m2_4_s2)

        d1_m1_1_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_1_s4', '00:30')
        d1_m1_1_s4.add_parent(d1_m1_1_s3)

        d1_m1_2_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s4', '00:30')
        d1_m1_2_s4.add_parent(d1_m1_2_s3)

        d1_m1_3_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s4', '00:30')
        d1_m1_3_s4.add_parent(d1_m1_3_s3)

        d1_m1_4_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s4', '00:30')
        d1_m1_4_s4.add_parent(d1_m1_4_s3)

        d1_m2_1_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s4', '00:30')
        d1_m2_1_s4.add_parent(d1_m2_1_s3)

        d1_m2_2_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s4', '00:30')
        d1_m2_2_s4.add_parent(d1_m2_2_s3)

        d1_m2_3_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s4', '00:30')
        d1_m2_3_s4.add_parent(d1_m2_3_s3)

        d1_m2_4_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s4', '00:30')
        d1_m2_4_s4.add_parent(d1_m2_4_s3)

        self.job_list._job_list = [d1_m1_s1, d1_m2_s1, d1_m1_1_s2, d1_m1_2_s2,
                                   d1_m1_3_s2, d1_m1_4_s2, d1_m2_1_s2, d1_m2_2_s2,
                                   d1_m2_3_s2, d1_m2_4_s2, d1_m1_1_s3, d1_m1_2_s3,
                                   d1_m1_3_s3, d1_m1_4_s3, d1_m2_1_s3, d1_m2_2_s3,
                                   d1_m2_3_s3, d1_m2_4_s3, d1_m1_1_s4, d1_m1_2_s4,
                                   d1_m1_3_s4, d1_m1_4_s4, d1_m2_1_s4, d1_m2_2_s4,
                                   d1_m2_3_s4, d1_m2_4_s4]

        self.job_list._ordered_jobs_by_date_member["d1"] = dict()
        self.job_list._ordered_jobs_by_date_member["d1"]["m1"] = [d1_m1_1_s2, d1_m1_1_s3, d1_m1_2_s2, d1_m1_2_s3, d1_m1_3_s2,
                                                                  d1_m1_3_s3, d1_m1_4_s2, d1_m1_4_s3]

        self.job_list._ordered_jobs_by_date_member["d1"]["m2"] = [d1_m2_1_s2, d1_m2_1_s3, d1_m2_2_s2, d1_m2_2_s3, d1_m2_3_s2,
                                                                  d1_m2_3_s3, d1_m2_4_s2, d1_m2_4_s3]

        wrapper_expression = "s2 s3"
        max_wrapped_jobs = 18
        max_jobs = 18
        max_wallclock = '10:00'

        section_list = [d1_m1_1_s2]

        returned_packages = JobPackager._build_vertical_packages(self.job_list.get_ordered_jobs_by_date_member(), wrapper_expression, section_list,
                                                                 max_jobs, max_wallclock, max_wrapped_jobs)

        package_m1_s2_s3 = [d1_m1_1_s2, d1_m1_1_s3, d1_m1_2_s2, d1_m1_2_s3, d1_m1_3_s2, d1_m1_3_s3, d1_m1_4_s2,
                            d1_m1_4_s3]

        packages = [JobPackageVertical(package_m1_s2_s3)]
        returned_packages = returned_packages[0]
        for i in range(0, len(returned_packages)):
            self.assertListEqual(returned_packages[i]._jobs, packages[i]._jobs)

    def test_returned_packages_max_jobs(self):
        '''
            [s2]
            RUNNING = chunk
            DEPENDENCIES = s1 s2-1

            [s3]
            RUNNING = chunk
            DEPENDENCIES = s2

            [s4]
            RUNNING = chunk
            DEPENDENCIES = s3
        '''
        d1_m1_s1 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_s1', '00:50')
        d1_m2_s1 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_s1', '00:50')

        d1_m1_1_s2 = self._createDummyJob(Status.READY, 'expid_d1_m1_1_s2', '00:10')
        d1_m1_1_s2.add_parent(d1_m1_s1)

        d1_m1_2_s2 = self._createDummyJob(Status.READY, 'expid_d1_m1_2_s2', '00:10')
        d1_m1_2_s2.add_parent(d1_m1_1_s2)

        d1_m1_3_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s2', '00:10')
        d1_m1_3_s2.add_parent(d1_m1_2_s2)

        d1_m1_4_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s2', '00:10')
        d1_m1_4_s2.add_parent(d1_m1_3_s2)

        d1_m2_1_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s2', '00:10')
        d1_m2_1_s2.add_parent(d1_m2_s1)

        d1_m2_2_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s2', '00:10')
        d1_m2_2_s2.add_parent(d1_m2_1_s2)

        d1_m2_3_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s2', '00:10')
        d1_m2_3_s2.add_parent(d1_m2_2_s2)

        d1_m2_4_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s2', '00:10')
        d1_m2_4_s2.add_parent(d1_m2_3_s2)

        d1_m1_1_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_1_s3', '00:20')
        d1_m1_1_s3.add_parent(d1_m1_1_s2)

        d1_m1_2_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s3', '00:20')
        d1_m1_2_s3.add_parent(d1_m1_2_s2)

        d1_m1_3_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s3', '00:20')
        d1_m1_3_s3.add_parent(d1_m1_3_s2)

        d1_m1_4_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s3', '00:20')
        d1_m1_4_s3.add_parent(d1_m1_4_s2)

        d1_m2_1_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s3', '00:20')
        d1_m2_1_s3.add_parent(d1_m2_1_s2)

        d1_m2_2_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s3', '00:20')
        d1_m2_2_s3.add_parent(d1_m2_2_s2)

        d1_m2_3_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s3', '00:20')
        d1_m2_3_s3.add_parent(d1_m2_3_s2)

        d1_m2_4_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s3', '00:20')
        d1_m2_4_s3.add_parent(d1_m2_4_s2)

        d1_m1_1_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_1_s4', '00:30')
        d1_m1_1_s4.add_parent(d1_m1_1_s3)

        d1_m1_2_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s4', '00:30')
        d1_m1_2_s4.add_parent(d1_m1_2_s3)

        d1_m1_3_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s4', '00:30')
        d1_m1_3_s4.add_parent(d1_m1_3_s3)

        d1_m1_4_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s4', '00:30')
        d1_m1_4_s4.add_parent(d1_m1_4_s3)

        d1_m2_1_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s4', '00:30')
        d1_m2_1_s4.add_parent(d1_m2_1_s3)

        d1_m2_2_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s4', '00:30')
        d1_m2_2_s4.add_parent(d1_m2_2_s3)

        d1_m2_3_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s4', '00:30')
        d1_m2_3_s4.add_parent(d1_m2_3_s3)

        d1_m2_4_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s4', '00:30')
        d1_m2_4_s4.add_parent(d1_m2_4_s3)

        self.job_list._job_list = [d1_m1_s1, d1_m2_s1, d1_m1_1_s2, d1_m1_2_s2,
                                   d1_m1_3_s2, d1_m1_4_s2, d1_m2_1_s2, d1_m2_2_s2,
                                   d1_m2_3_s2, d1_m2_4_s2, d1_m1_1_s3, d1_m1_2_s3,
                                   d1_m1_3_s3, d1_m1_4_s3, d1_m2_1_s3, d1_m2_2_s3,
                                   d1_m2_3_s3, d1_m2_4_s3, d1_m1_1_s4, d1_m1_2_s4,
                                   d1_m1_3_s4, d1_m1_4_s4, d1_m2_1_s4, d1_m2_2_s4,
                                   d1_m2_3_s4, d1_m2_4_s4]

        self.job_list._ordered_jobs_by_date_member["d1"] = dict()
        self.job_list._ordered_jobs_by_date_member["d1"]["m1"] = [d1_m1_1_s2, d1_m1_1_s3, d1_m1_2_s2, d1_m1_2_s3, d1_m1_3_s2,
                                                                  d1_m1_3_s3, d1_m1_4_s2, d1_m1_4_s3]

        self.job_list._ordered_jobs_by_date_member["d1"]["m2"] = [d1_m2_1_s2, d1_m2_1_s3, d1_m2_2_s2, d1_m2_2_s3, d1_m2_3_s2,
                                                                  d1_m2_3_s3, d1_m2_4_s2, d1_m2_4_s3]

        wrapper_expression = "s2 s3"
        max_jobs = 10
        max_wrapped_jobs = 10
        max_wallclock = '10:00'

        section_list = [d1_m1_1_s2, d1_m2_1_s2]

        returned_packages = JobPackager._build_vertical_packages(self.job_list.get_ordered_jobs_by_date_member(),
                                                                 wrapper_expression, section_list,
                                                                 max_jobs, max_wallclock, max_wrapped_jobs)

        package_m1_s2_s3 = [d1_m1_1_s2, d1_m1_1_s3, d1_m1_2_s2, d1_m1_2_s3, d1_m1_3_s2, d1_m1_3_s3, d1_m1_4_s2,
                            d1_m1_4_s3]
        package_m2_s2_s3 = [d1_m2_1_s2, d1_m2_1_s3]

        packages = [JobPackageVertical(package_m1_s2_s3), JobPackageVertical(package_m2_s2_s3)]

        returned_packages = returned_packages[0]
        for i in range(0, len(returned_packages)):
            self.assertListEqual(returned_packages[i]._jobs, packages[i]._jobs)

    def test_returned_packages_max_wallclock(self):
        '''
            [s2]
            RUNNING = chunk
            DEPENDENCIES = s1 s2-1

            [s3]
            RUNNING = chunk
            DEPENDENCIES = s2

            [s4]
            RUNNING = chunk
            DEPENDENCIES = s3
        '''
        d1_m1_s1 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_s1', '00:50')
        d1_m2_s1 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_s1', '00:50')

        d1_m1_1_s2 = self._createDummyJob(Status.READY, 'expid_d1_m1_1_s2', '00:10')
        d1_m1_1_s2.add_parent(d1_m1_s1)

        d1_m1_2_s2 = self._createDummyJob(Status.READY, 'expid_d1_m1_2_s2', '00:10')
        d1_m1_2_s2.add_parent(d1_m1_1_s2)

        d1_m1_3_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s2', '00:10')
        d1_m1_3_s2.add_parent(d1_m1_2_s2)

        d1_m1_4_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s2', '00:10')
        d1_m1_4_s2.add_parent(d1_m1_3_s2)

        d1_m2_1_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s2', '00:10')
        d1_m2_1_s2.add_parent(d1_m2_s1)

        d1_m2_2_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s2', '00:10')
        d1_m2_2_s2.add_parent(d1_m2_1_s2)

        d1_m2_3_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s2', '00:10')
        d1_m2_3_s2.add_parent(d1_m2_2_s2)

        d1_m2_4_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s2', '00:10')
        d1_m2_4_s2.add_parent(d1_m2_3_s2)

        d1_m1_1_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_1_s3', '00:20')
        d1_m1_1_s3.add_parent(d1_m1_1_s2)

        d1_m1_2_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s3', '00:20')
        d1_m1_2_s3.add_parent(d1_m1_2_s2)

        d1_m1_3_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s3', '00:20')
        d1_m1_3_s3.add_parent(d1_m1_3_s2)

        d1_m1_4_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s3', '00:20')
        d1_m1_4_s3.add_parent(d1_m1_4_s2)

        d1_m2_1_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s3', '00:20')
        d1_m2_1_s3.add_parent(d1_m2_1_s2)

        d1_m2_2_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s3', '00:20')
        d1_m2_2_s3.add_parent(d1_m2_2_s2)

        d1_m2_3_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s3', '00:20')
        d1_m2_3_s3.add_parent(d1_m2_3_s2)

        d1_m2_4_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s3', '00:20')
        d1_m2_4_s3.add_parent(d1_m2_4_s2)

        d1_m1_1_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_1_s4', '00:30')
        d1_m1_1_s4.add_parent(d1_m1_1_s3)

        d1_m1_2_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s4', '00:30')
        d1_m1_2_s4.add_parent(d1_m1_2_s3)

        d1_m1_3_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s4', '00:30')
        d1_m1_3_s4.add_parent(d1_m1_3_s3)

        d1_m1_4_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s4', '00:30')
        d1_m1_4_s4.add_parent(d1_m1_4_s3)

        d1_m2_1_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s4', '00:30')
        d1_m2_1_s4.add_parent(d1_m2_1_s3)

        d1_m2_2_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s4', '00:30')
        d1_m2_2_s4.add_parent(d1_m2_2_s3)

        d1_m2_3_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s4', '00:30')
        d1_m2_3_s4.add_parent(d1_m2_3_s3)

        d1_m2_4_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s4', '00:30')
        d1_m2_4_s4.add_parent(d1_m2_4_s3)

        self.job_list._job_list = [d1_m1_s1, d1_m2_s1, d1_m1_1_s2, d1_m1_2_s2,
                                   d1_m1_3_s2, d1_m1_4_s2, d1_m2_1_s2, d1_m2_2_s2,
                                   d1_m2_3_s2, d1_m2_4_s2, d1_m1_1_s3, d1_m1_2_s3,
                                   d1_m1_3_s3, d1_m1_4_s3, d1_m2_1_s3, d1_m2_2_s3,
                                   d1_m2_3_s3, d1_m2_4_s3, d1_m1_1_s4, d1_m1_2_s4,
                                   d1_m1_3_s4, d1_m1_4_s4, d1_m2_1_s4, d1_m2_2_s4,
                                   d1_m2_3_s4, d1_m2_4_s4]

        self.job_list._ordered_jobs_by_date_member["d1"] = dict()
        self.job_list._ordered_jobs_by_date_member["d1"]["m1"] = [d1_m1_1_s2, d1_m1_1_s3, d1_m1_2_s2, d1_m1_2_s3, d1_m1_3_s2,
                                                                  d1_m1_3_s3, d1_m1_4_s2, d1_m1_4_s3]

        self.job_list._ordered_jobs_by_date_member["d1"]["m2"] = [d1_m2_1_s2, d1_m2_1_s3, d1_m2_2_s2, d1_m2_2_s3, d1_m2_3_s2,
                                                                  d1_m2_3_s3, d1_m2_4_s2, d1_m2_4_s3]

        wrapper_expression = "s2 s3"
        max_jobs = 18
        max_wrapped_jobs = 18
        max_wallclock = '01:00'

        section_list = [d1_m1_1_s2, d1_m2_1_s2]

        returned_packages = JobPackager._build_vertical_packages(self.job_list.get_ordered_jobs_by_date_member(),
                                                                 wrapper_expression, section_list,
                                                                 max_jobs, max_wallclock, max_wrapped_jobs)

        package_m1_s2_s3 = [d1_m1_1_s2, d1_m1_1_s3, d1_m1_2_s2, d1_m1_2_s3]
        package_m2_s2_s3 = [d1_m2_1_s2, d1_m2_1_s3, d1_m2_2_s2, d1_m2_2_s3]

        packages = [JobPackageVertical(package_m1_s2_s3), JobPackageVertical(package_m2_s2_s3)]

        returned_packages = returned_packages[0]
        for i in range(0, len(returned_packages)):
            self.assertListEqual(returned_packages[i]._jobs, packages[i]._jobs)

    def test_returned_packages_first_chunks_completed(self):
        '''
            [s2]
            RUNNING = chunk
            DEPENDENCIES = s1 s2-1

            [s3]
            RUNNING = chunk
            DEPENDENCIES = s2

            [s4]
            RUNNING = chunk
            DEPENDENCIES = s3

        '''
        d1_m1_s1 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_s1', '00:50')
        d1_m2_s1 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_s1', '00:50')

        d1_m1_1_s2 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_1_s2', '00:10')
        d1_m1_1_s2.add_parent(d1_m1_s1)

        d1_m1_2_s2 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_2_s2', '00:10')
        d1_m1_2_s2.add_parent(d1_m1_1_s2)

        d1_m1_3_s2 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_3_s2', '00:10')
        d1_m1_3_s2.add_parent(d1_m1_2_s2)

        d1_m1_4_s2 = self._createDummyJob(Status.READY, 'expid_d1_m1_4_s2', '00:10')
        d1_m1_4_s2.add_parent(d1_m1_3_s2)

        d1_m2_1_s2 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m2_1_s2', '00:10')
        d1_m2_1_s2.add_parent(d1_m2_s1)

        d1_m2_2_s2 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m2_2_s2', '00:10')
        d1_m2_2_s2.add_parent(d1_m2_1_s2)

        d1_m2_3_s2 = self._createDummyJob(Status.READY, 'expid_d1_m2_3_s2', '00:10')
        d1_m2_3_s2.add_parent(d1_m2_2_s2)

        d1_m2_4_s2 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s2', '00:10')
        d1_m2_4_s2.add_parent(d1_m2_3_s2)

        d1_m1_1_s3 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m1_1_s3', '00:20')
        d1_m1_1_s3.add_parent(d1_m1_1_s2)

        d1_m1_2_s3 = self._createDummyJob(Status.READY, 'expid_d1_m1_2_s3', '00:20')
        d1_m1_2_s3.add_parent(d1_m1_2_s2)

        d1_m1_3_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s3', '00:20')
        d1_m1_3_s3.add_parent(d1_m1_3_s2)

        d1_m1_4_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s3', '00:20')
        d1_m1_4_s3.add_parent(d1_m1_4_s2)

        d1_m2_1_s3 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m2_1_s3', '00:20')
        d1_m2_1_s3.add_parent(d1_m2_1_s2)

        d1_m2_2_s3 = self._createDummyJob(Status.COMPLETED, 'expid_d1_m2_2_s3', '00:20')
        d1_m2_2_s3.add_parent(d1_m2_2_s2)

        d1_m2_3_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s3', '00:20')
        d1_m2_3_s3.add_parent(d1_m2_3_s2)

        d1_m2_4_s3 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s3', '00:20')
        d1_m2_4_s3.add_parent(d1_m2_4_s2)

        d1_m1_1_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_1_s4', '00:30')
        d1_m1_1_s4.add_parent(d1_m1_1_s3)

        d1_m1_2_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_2_s4', '00:30')
        d1_m1_2_s4.add_parent(d1_m1_2_s3)

        d1_m1_3_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_3_s4', '00:30')
        d1_m1_3_s4.add_parent(d1_m1_3_s3)

        d1_m1_4_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m1_4_s4', '00:30')
        d1_m1_4_s4.add_parent(d1_m1_4_s3)

        d1_m2_1_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_1_s4', '00:30')
        d1_m2_1_s4.add_parent(d1_m2_1_s3)

        d1_m2_2_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_2_s4', '00:30')
        d1_m2_2_s4.add_parent(d1_m2_2_s3)

        d1_m2_3_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_3_s4', '00:30')
        d1_m2_3_s4.add_parent(d1_m2_3_s3)

        d1_m2_4_s4 = self._createDummyJob(Status.WAITING, 'expid_d1_m2_4_s4', '00:30')
        d1_m2_4_s4.add_parent(d1_m2_4_s3)

        self.job_list._job_list = [d1_m1_s1, d1_m2_s1, d1_m1_1_s2, d1_m1_2_s2,
                                   d1_m1_3_s2, d1_m1_4_s2, d1_m2_1_s2, d1_m2_2_s2,
                                   d1_m2_3_s2, d1_m2_4_s2, d1_m1_1_s3, d1_m1_2_s3,
                                   d1_m1_3_s3, d1_m1_4_s3, d1_m2_1_s3, d1_m2_2_s3,
                                   d1_m2_3_s3, d1_m2_4_s3, d1_m1_1_s4, d1_m1_2_s4,
                                   d1_m1_3_s4, d1_m1_4_s4, d1_m2_1_s4, d1_m2_2_s4,
                                   d1_m2_3_s4, d1_m2_4_s4]

        self.job_list._ordered_jobs_by_date_member["d1"] = dict()
        self.job_list._ordered_jobs_by_date_member["d1"]["m1"] = [d1_m1_1_s2, d1_m1_1_s3, d1_m1_2_s2, d1_m1_2_s3, d1_m1_3_s2,
                                                                  d1_m1_3_s3, d1_m1_4_s2, d1_m1_4_s3]

        self.job_list._ordered_jobs_by_date_member["d1"]["m2"] = [d1_m2_1_s2, d1_m2_1_s3, d1_m2_2_s2, d1_m2_2_s3, d1_m2_3_s2,
                                                                  d1_m2_3_s3, d1_m2_4_s2, d1_m2_4_s3]

        wrapper_expression = "s2 s3"
        max_wrapped_jobs = 18
        max_jobs = 18
        max_wallclock = '10:00'

        section_list = [d1_m1_2_s3, d1_m1_4_s2, d1_m2_3_s2]

        returned_packages = JobPackager._build_vertical_packages(self.job_list.get_ordered_jobs_by_date_member(),
                                                                 wrapper_expression, section_list,
                                                                 max_jobs, max_wallclock, max_wrapped_jobs)

        package_m1_s2_s3 = [d1_m1_2_s3, d1_m1_3_s3, d1_m1_4_s2, d1_m1_4_s3]
        package_m2_s2_s3 = [d1_m2_3_s2, d1_m2_3_s3, d1_m2_4_s2, d1_m2_4_s3]

        packages = [JobPackageVertical(package_m1_s2_s3), JobPackageVertical(package_m2_s2_s3)]

        returned_packages = returned_packages[0]
        for i in range(0, len(returned_packages)):
            self.assertListEqual(returned_packages[i]._jobs, packages[i]._jobs)

    #def test_parent_failed
    #def test_invalid_wrapper_expression(self):

    def _createDummyJob(self, status, name, total_wallclock):
        job_id = randrange(1, 999)
        job = Job(name, job_id, status, 0)
        job.type = randrange(0, 2)
        job.packed = False
        job.wallclock = total_wallclock
        job.platform = self.platform

        name_split = name.split('_')
        job.date = name_split[1]
        job.member = name_split[2]
        if len(name_split) == 5:
            job.chunk = name_split[3]
            job.section = name_split[4]
        else:
            job.section = name_split[3]
        return job

class FakeBasicConfig:
    def __init__(self):
        pass

    DB_DIR = '/dummy/db/dir'
    DB_FILE = '/dummy/db/file'
    DB_PATH = '/dummy/db/path'
    LOCAL_ROOT_DIR = '/dummy/local/root/dir'
    LOCAL_TMP_DIR = '/dummy/local/temp/dir'
    LOCAL_PROJ_DIR = '/dummy/local/proj/dir'
    DEFAULT_PLATFORMS_CONF = ''
    DEFAULT_JOBS_CONF = ''