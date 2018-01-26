from unittest import TestCase
from mock import Mock
from autosubmit.job.job_list import JobList
from bscearth.utils.config_parser import ConfigParserFactory
from autosubmit.job.job_list_persistence import JobListPersistenceDb
from autosubmit.job.job_common import Status
from random import randrange
from autosubmit.job.job import Job
from mock import patch

from autosubmit.job.job_grouping import JobGrouping

class TestJobGrouping(TestCase):

    def setUp(self):
        self.experiment_id = 'random-id'
        self.job_list = JobList(self.experiment_id, FakeBasicConfig, ConfigParserFactory(),
                                JobListPersistenceDb('.', '.'))
        self.parser_mock = Mock(spec='SafeConfigParser')

        # Basic workflow with SETUP, INI, SIM, POST, CLEAN
        self._createDummyJob('expid_SETUP', Status.READY)

        for date in ['d1', 'd2']:
            for member in ['m1', 'm2']:
                job = self._createDummyJob('expid_' + date + '_' + member + '_' + 'INI', Status.WAITING, date, member)
                self.job_list.get_job_list().append(job)

        sections = ['SIM', 'POST', 'CLEAN']
        for section in sections:
            for date in ['d1', 'd2']:
                for member in ['m1', 'm2']:
                    for chunk in [1, 2]:
                        job = self._createDummyJob('expid_' + date + '_' + member + '_' + str(chunk) + '_' + section, Status.WAITING, date, member, chunk)
                        self.job_list.get_job_list().append(job)

    def test_group_by_date(self):
        groups_dict = dict()

        groups_dict['status'] = {'d1' : Status.WAITING, 'd2' : Status.WAITING}
        groups_dict['jobs'] = {
                                'expid_d1_m1_INI' : ['d1'], 'expid_d1_m2_INI' : ['d1'], 'expid_d2_m1_INI' : ['d2'], 'expid_d2_m2_INI' : ['d2'],

                               'expid_d1_m1_1_SIM': ['d1'], 'expid_d1_m1_2_SIM': ['d1'], 'expid_d1_m2_1_SIM': ['d1'], 'expid_d1_m2_2_SIM': ['d1'],
                               'expid_d2_m1_1_SIM': ['d2'], 'expid_d2_m1_2_SIM': ['d2'], 'expid_d2_m2_1_SIM': ['d2'], 'expid_d2_m2_2_SIM': ['d2'],

                               'expid_d1_m1_1_POST': ['d1'], 'expid_d1_m1_2_POST': ['d1'], 'expid_d1_m2_1_POST': ['d1'], 'expid_d1_m2_2_POST': ['d1'],
                               'expid_d2_m1_1_POST': ['d2'], 'expid_d2_m1_2_POST': ['d2'], 'expid_d2_m2_1_POST': ['d2'], 'expid_d2_m2_2_POST': ['d2'],

                               'expid_d1_m1_1_CLEAN': ['d1'], 'expid_d1_m1_2_CLEAN': ['d1'], 'expid_d1_m2_1_CLEAN': ['d1'],  'expid_d1_m2_2_CLEAN': ['d1'],
                               'expid_d2_m1_1_CLEAN': ['d2'], 'expid_d2_m1_2_CLEAN': ['d2'], 'expid_d2_m2_1_CLEAN': ['d2'], 'expid_d2_m2_2_CLEAN': ['d2']
                               }
        
        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        side_effect = []
        for job in reversed(self.job_list.get_job_list()):
            if job.date is not None:
                side_effect.append(job.date)

        with patch('autosubmit.job.job_grouping.date2str', side_effect=side_effect):
            job_grouping = JobGrouping('date', self.job_list.get_job_list(), self.job_list)
            self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def test_group_by_member(self):
        groups_dict = dict()

        groups_dict['status'] = {'d1_m1': Status.WAITING, 'd1_m2': Status.WAITING, 'd2_m1': Status.WAITING, 'd2_m2' : Status.WAITING}
        groups_dict['jobs'] = {
            'expid_d1_m1_INI': ['d1_m1'], 'expid_d1_m2_INI': ['d1_m2'], 'expid_d2_m1_INI': ['d2_m1'], 'expid_d2_m2_INI': ['d2_m2'],

            'expid_d1_m1_1_SIM': ['d1_m1'], 'expid_d1_m1_2_SIM': ['d1_m1'], 'expid_d1_m2_1_SIM': ['d1_m2'],
            'expid_d1_m2_2_SIM': ['d1_m2'],
            'expid_d2_m1_1_SIM': ['d2_m1'], 'expid_d2_m1_2_SIM': ['d2_m1'], 'expid_d2_m2_1_SIM': ['d2_m2'],
            'expid_d2_m2_2_SIM': ['d2_m2'],

            'expid_d1_m1_1_POST': ['d1_m1'], 'expid_d1_m1_2_POST': ['d1_m1'], 'expid_d1_m2_1_POST': ['d1_m2'],
            'expid_d1_m2_2_POST': ['d1_m2'],
            'expid_d2_m1_1_POST': ['d2_m1'], 'expid_d2_m1_2_POST': ['d2_m1'], 'expid_d2_m2_1_POST': ['d2_m2'],
            'expid_d2_m2_2_POST': ['d2_m2'],

            'expid_d1_m1_1_CLEAN': ['d1_m1'], 'expid_d1_m1_2_CLEAN': ['d1_m1'], 'expid_d1_m2_1_CLEAN': ['d1_m2'],
            'expid_d1_m2_2_CLEAN': ['d1_m2'],
            'expid_d2_m1_1_CLEAN': ['d2_m1'], 'expid_d2_m1_2_CLEAN': ['d2_m1'], 'expid_d2_m2_1_CLEAN': ['d2_m2'],
            'expid_d2_m2_2_CLEAN': ['d2_m2']
        }

        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        side_effect = []
        for job in reversed(self.job_list.get_job_list()):
            if job.member is not None:
                side_effect.append(job.date)

        with patch('autosubmit.job.job_grouping.date2str', side_effect=side_effect):
            job_grouping = JobGrouping('member', self.job_list.get_job_list(), self.job_list)
            self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def test_group_by_chunk(self):
        groups_dict = dict()

        groups_dict['status'] = {'d1_m1_1': Status.WAITING, 'd1_m1_2': Status.WAITING,
                                 'd1_m2_1': Status.WAITING, 'd1_m2_2': Status.WAITING,
                                 'd2_m1_1': Status.WAITING, 'd2_m1_2': Status.WAITING,
                                 'd2_m2_1': Status.WAITING, 'd2_m2_2': Status.WAITING}
        groups_dict['jobs'] = {
            'expid_d1_m1_1_SIM': ['d1_m1_1'], 'expid_d1_m1_2_SIM': ['d1_m1_2'], 'expid_d1_m2_1_SIM': ['d1_m2_1'],
            'expid_d1_m2_2_SIM': ['d1_m2_2'],
            'expid_d2_m1_1_SIM': ['d2_m1_1'], 'expid_d2_m1_2_SIM': ['d2_m1_2'], 'expid_d2_m2_1_SIM': ['d2_m2_1'],
            'expid_d2_m2_2_SIM': ['d2_m2_2'],

            'expid_d1_m1_1_POST': ['d1_m1_1'], 'expid_d1_m1_2_POST': ['d1_m1_2'], 'expid_d1_m2_1_POST': ['d1_m2_1'],
            'expid_d1_m2_2_POST': ['d1_m2_2'],
            'expid_d2_m1_1_POST': ['d2_m1_1'], 'expid_d2_m1_2_POST': ['d2_m1_2'], 'expid_d2_m2_1_POST': ['d2_m2_1'],
            'expid_d2_m2_2_POST': ['d2_m2_2'],

            'expid_d1_m1_1_CLEAN': ['d1_m1_1'], 'expid_d1_m1_2_CLEAN': ['d1_m1_2'], 'expid_d1_m2_1_CLEAN': ['d1_m2_1'],
            'expid_d1_m2_2_CLEAN': ['d1_m2_2'],
            'expid_d2_m1_1_CLEAN': ['d2_m1_1'], 'expid_d2_m1_2_CLEAN': ['d2_m1_2'], 'expid_d2_m2_1_CLEAN': ['d2_m2_1'],
            'expid_d2_m2_2_CLEAN': ['d2_m2_2']
        }

        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        side_effect = []
        for job in reversed(self.job_list.get_job_list()):
            if job.chunk is not None:
                side_effect.append(job.date)

        with patch('autosubmit.job.job_grouping.date2str', side_effect=side_effect):
            job_grouping = JobGrouping('chunk', self.job_list.get_job_list(), self.job_list)
            self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def test_group_by_split(self):
        for date in ['d1', 'd2']:
            for member in ['m1', 'm2']:
                for chunk in [1, 2]:
                    for split in [1, 2]:
                        job = self._createDummyJob('expid_' + date + '_' + member + '_' + str(chunk) + '_' + str(split) + '_CMORATM',
                                                   Status.WAITING, date, member, chunk, split)
                        self.job_list.get_job_list().append(job)

        groups_dict = dict()

        groups_dict['status'] = {
            'expid_d1_m1_1_CMORATM': Status.WAITING,
            'expid_d1_m1_2_CMORATM': Status.WAITING,
            'expid_d1_m2_1_CMORATM': Status.WAITING,
            'expid_d1_m2_2_CMORATM': Status.WAITING,
            'expid_d2_m1_1_CMORATM': Status.WAITING,
            'expid_d2_m1_2_CMORATM': Status.WAITING,
            'expid_d2_m2_1_CMORATM': Status.WAITING,
            'expid_d2_m2_2_CMORATM': Status.WAITING,
        }
        
        groups_dict['jobs'] =  {
            'expid_d1_m1_1_1_CMORATM' : ['expid_d1_m1_1_CMORATM'],
            'expid_d1_m1_1_2_CMORATM' : ['expid_d1_m1_1_CMORATM'],
            'expid_d1_m1_2_1_CMORATM' : ['expid_d1_m1_2_CMORATM'],
            'expid_d1_m1_2_2_CMORATM' : ['expid_d1_m1_2_CMORATM'],
            'expid_d1_m2_1_1_CMORATM': ['expid_d1_m2_1_CMORATM'],
            'expid_d1_m2_1_2_CMORATM': ['expid_d1_m2_1_CMORATM'],
            'expid_d1_m2_2_1_CMORATM': ['expid_d1_m2_2_CMORATM'],
            'expid_d1_m2_2_2_CMORATM': ['expid_d1_m2_2_CMORATM'],
            'expid_d2_m1_1_1_CMORATM': ['expid_d2_m1_1_CMORATM'],
            'expid_d2_m1_1_2_CMORATM': ['expid_d2_m1_1_CMORATM'],
            'expid_d2_m1_2_1_CMORATM': ['expid_d2_m1_2_CMORATM'],
            'expid_d2_m1_2_2_CMORATM': ['expid_d2_m1_2_CMORATM'],
            'expid_d2_m2_1_1_CMORATM': ['expid_d2_m2_1_CMORATM'],
            'expid_d2_m2_1_2_CMORATM': ['expid_d2_m2_1_CMORATM'],
            'expid_d2_m2_2_1_CMORATM': ['expid_d2_m2_2_CMORATM'],
            'expid_d2_m2_2_2_CMORATM': ['expid_d2_m2_2_CMORATM']
        }

        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        job_grouping = JobGrouping('split', self.job_list.get_job_list(), self.job_list)
        self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def test_automatic_grouping_all(self):
        groups_dict = dict()

        groups_dict['status'] = {'d1': Status.WAITING, 'd2': Status.WAITING}
        groups_dict['jobs'] = {
            'expid_d1_m1_INI': ['d1'], 'expid_d1_m2_INI': ['d1'], 'expid_d2_m1_INI': ['d2'], 'expid_d2_m2_INI': ['d2'],

            'expid_d1_m1_1_SIM': ['d1'], 'expid_d1_m1_2_SIM': ['d1'], 'expid_d1_m2_1_SIM': ['d1'],
            'expid_d1_m2_2_SIM': ['d1'],
            'expid_d2_m1_1_SIM': ['d2'], 'expid_d2_m1_2_SIM': ['d2'], 'expid_d2_m2_1_SIM': ['d2'],
            'expid_d2_m2_2_SIM': ['d2'],

            'expid_d1_m1_1_POST': ['d1'], 'expid_d1_m1_2_POST': ['d1'], 'expid_d1_m2_1_POST': ['d1'],
            'expid_d1_m2_2_POST': ['d1'],
            'expid_d2_m1_1_POST': ['d2'], 'expid_d2_m1_2_POST': ['d2'], 'expid_d2_m2_1_POST': ['d2'],
            'expid_d2_m2_2_POST': ['d2'],

            'expid_d1_m1_1_CLEAN': ['d1'], 'expid_d1_m1_2_CLEAN': ['d1'], 'expid_d1_m2_1_CLEAN': ['d1'],
            'expid_d1_m2_2_CLEAN': ['d1'],
            'expid_d2_m1_1_CLEAN': ['d2'], 'expid_d2_m1_2_CLEAN': ['d2'], 'expid_d2_m2_1_CLEAN': ['d2'],
            'expid_d2_m2_2_CLEAN': ['d2']
        }

        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        side_effect = []
        for job in reversed(self.job_list.get_job_list()):
            if job.date is not None:
                side_effect.append(job.date)

        with patch('autosubmit.job.job_grouping.date2str', side_effect=side_effect):
            job_grouping = JobGrouping('automatic', self.job_list.get_job_list(), self.job_list)
            self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def test_automatic_grouping_not_ini(self):
        self.job_list.get_job_by_name('expid_d1_m1_INI').status = Status.READY
        self.job_list.get_job_by_name('expid_d1_m2_INI').status = Status.READY
        self.job_list.get_job_by_name('expid_d2_m1_INI').status = Status.READY
        self.job_list.get_job_by_name('expid_d2_m2_INI').status = Status.READY

        groups_dict = dict()

        groups_dict['status'] = {'d1': Status.WAITING, 'd2': Status.WAITING}
        groups_dict['jobs'] = {
            'expid_d1_m1_1_SIM': ['d1'], 'expid_d1_m1_2_SIM': ['d1'], 'expid_d1_m2_1_SIM': ['d1'],
            'expid_d1_m2_2_SIM': ['d1'],
            'expid_d2_m1_1_SIM': ['d2'], 'expid_d2_m1_2_SIM': ['d2'], 'expid_d2_m2_1_SIM': ['d2'],
            'expid_d2_m2_2_SIM': ['d2'],

            'expid_d1_m1_1_POST': ['d1'], 'expid_d1_m1_2_POST': ['d1'], 'expid_d1_m2_1_POST': ['d1'],
            'expid_d1_m2_2_POST': ['d1'],
            'expid_d2_m1_1_POST': ['d2'], 'expid_d2_m1_2_POST': ['d2'], 'expid_d2_m2_1_POST': ['d2'],
            'expid_d2_m2_2_POST': ['d2'],

            'expid_d1_m1_1_CLEAN': ['d1'], 'expid_d1_m1_2_CLEAN': ['d1'], 'expid_d1_m2_1_CLEAN': ['d1'],
            'expid_d1_m2_2_CLEAN': ['d1'],
            'expid_d2_m1_1_CLEAN': ['d2'], 'expid_d2_m1_2_CLEAN': ['d2'], 'expid_d2_m2_1_CLEAN': ['d2'],
            'expid_d2_m2_2_CLEAN': ['d2']
        }

        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        side_effect = []
        for job in reversed(self.job_list.get_job_list()):
            if job.date is not None:
                side_effect.append(job.date)

        with patch('autosubmit.job.job_grouping.date2str', side_effect=side_effect):
            job_grouping = JobGrouping('automatic', self.job_list.get_job_list(), self.job_list)
            self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def test_automatic_grouping_splits(self,):
        for date in ['d1', 'd2']:
            for member in ['m1', 'm2']:
                for chunk in [1, 2]:
                    for split in [1, 2]:
                        job = self._createDummyJob(
                            'expid_' + date + '_' + member + '_' + str(chunk) + '_' + str(split) + '_CMORATM',
                            Status.WAITING, date, member, chunk, split)
                        self.job_list.get_job_list().append(job)

        groups_dict = dict()

        groups_dict['status'] = {'d1': Status.WAITING, 'd2': Status.WAITING}
        groups_dict['jobs'] = {
            'expid_d1_m1_INI': ['d1'], 'expid_d1_m2_INI': ['d1'], 'expid_d2_m1_INI': ['d2'], 'expid_d2_m2_INI': ['d2'],

            'expid_d1_m1_1_SIM': ['d1'], 'expid_d1_m1_2_SIM': ['d1'], 'expid_d1_m2_1_SIM': ['d1'],
            'expid_d1_m2_2_SIM': ['d1'],
            'expid_d2_m1_1_SIM': ['d2'], 'expid_d2_m1_2_SIM': ['d2'], 'expid_d2_m2_1_SIM': ['d2'],
            'expid_d2_m2_2_SIM': ['d2'],

            'expid_d1_m1_1_POST': ['d1'], 'expid_d1_m1_2_POST': ['d1'], 'expid_d1_m2_1_POST': ['d1'],
            'expid_d1_m2_2_POST': ['d1'],
            'expid_d2_m1_1_POST': ['d2'], 'expid_d2_m1_2_POST': ['d2'], 'expid_d2_m2_1_POST': ['d2'],
            'expid_d2_m2_2_POST': ['d2'],

            'expid_d1_m1_1_CLEAN': ['d1'], 'expid_d1_m1_2_CLEAN': ['d1'], 'expid_d1_m2_1_CLEAN': ['d1'],
            'expid_d1_m2_2_CLEAN': ['d1'],
            'expid_d2_m1_1_CLEAN': ['d2'], 'expid_d2_m1_2_CLEAN': ['d2'], 'expid_d2_m2_1_CLEAN': ['d2'],
            'expid_d2_m2_2_CLEAN': ['d2'],

            'expid_d1_m1_1_1_CMORATM': ['d1'],
            'expid_d1_m1_1_2_CMORATM': ['d1'],
            'expid_d1_m1_2_1_CMORATM': ['d1'],
            'expid_d1_m1_2_2_CMORATM': ['d1'],
            'expid_d1_m2_1_1_CMORATM': ['d1'],
            'expid_d1_m2_1_2_CMORATM': ['d1'],
            'expid_d1_m2_2_1_CMORATM': ['d1'],
            'expid_d1_m2_2_2_CMORATM': ['d1'],
            'expid_d2_m1_1_1_CMORATM': ['d2'],
            'expid_d2_m1_1_2_CMORATM': ['d2'],
            'expid_d2_m1_2_1_CMORATM': ['d2'],
            'expid_d2_m1_2_2_CMORATM': ['d2'],
            'expid_d2_m2_1_1_CMORATM': ['d2'],
            'expid_d2_m2_1_2_CMORATM': ['d2'],
            'expid_d2_m2_2_1_CMORATM': ['d2'],
            'expid_d2_m2_2_2_CMORATM': ['d2']
        }

        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        side_effect = []
        for job in reversed(self.job_list.get_job_list()):
            if job.date is not None:
                side_effect.append(job.date)

        with patch('autosubmit.job.job_grouping.date2str', side_effect=side_effect):
            job_grouping = JobGrouping('automatic', self.job_list.get_job_list(), self.job_list)
            self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def test_automatic_grouping_different_status_member(self):
        self.job_list.get_job_by_name('expid_d1_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m2_INI').status = Status.COMPLETED

        self.job_list.get_job_by_name('expid_d1_m1_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_2_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_2_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_CLEAN').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_2_CLEAN').status = Status.COMPLETED

        self.job_list.get_job_by_name('expid_d1_m2_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_CLEAN').status = Status.RUNNING

        self.job_list.get_job_by_name('expid_d1_m2_2_SIM').status = Status.READY

        groups_dict = dict()

        groups_dict['status'] = {'d1_m1': Status.COMPLETED, 'd2': Status.WAITING}
        groups_dict['jobs'] = {
            'expid_d1_m1_INI' : ['d1_m1'],

            'expid_d1_m1_1_SIM': ['d1_m1'], 'expid_d1_m1_2_SIM': ['d1_m1'],
            'expid_d2_m1_1_SIM': ['d2'], 'expid_d2_m1_2_SIM': ['d2'], 'expid_d2_m2_1_SIM': ['d2'],
            'expid_d2_m2_2_SIM': ['d2'],

            'expid_d1_m1_1_POST': ['d1_m1'], 'expid_d1_m1_2_POST': ['d1_m1'],
            'expid_d2_m1_1_POST': ['d2'], 'expid_d2_m1_2_POST': ['d2'], 'expid_d2_m2_1_POST': ['d2'],
            'expid_d2_m2_2_POST': ['d2'],

            'expid_d1_m1_1_CLEAN': ['d1_m1'], 'expid_d1_m1_2_CLEAN': ['d1_m1'],
            'expid_d2_m1_1_CLEAN': ['d2'], 'expid_d2_m1_2_CLEAN': ['d2'], 'expid_d2_m2_1_CLEAN': ['d2'],
            'expid_d2_m2_2_CLEAN': ['d2']
        }

        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        side_effect = []
        for job in reversed(self.job_list.get_job_list()):
            if job.date is not None:
                side_effect.append(job.date)

        with patch('autosubmit.job.job_grouping.date2str', side_effect=side_effect):
            job_grouping = JobGrouping('automatic', self.job_list.get_job_list(), self.job_list)
            self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def test_automatic_grouping_different_status_chunk(self):
        self.job_list.get_job_by_name('expid_d1_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m2_INI').status = Status.COMPLETED

        self.job_list.get_job_by_name('expid_d1_m1_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_CLEAN').status = Status.COMPLETED

        self.job_list.get_job_by_name('expid_d1_m1_2_SIM').status = Status.READY

        self.job_list.get_job_by_name('expid_d1_m2_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_CLEAN').status = Status.RUNNING

        self.job_list.get_job_by_name('expid_d1_m2_2_SIM').status = Status.READY

        groups_dict = dict()

        groups_dict['status'] = {'d1_m1_1': Status.COMPLETED, 'd2': Status.WAITING}
        groups_dict['jobs'] = {
            'expid_d1_m1_1_SIM': ['d1_m1_1'],
            'expid_d2_m1_1_SIM': ['d2'], 'expid_d2_m1_2_SIM': ['d2'], 'expid_d2_m2_1_SIM': ['d2'],
            'expid_d2_m2_2_SIM': ['d2'],

            'expid_d1_m1_1_POST': ['d1_m1_1'],
            'expid_d2_m1_1_POST': ['d2'], 'expid_d2_m1_2_POST': ['d2'], 'expid_d2_m2_1_POST': ['d2'],
            'expid_d2_m2_2_POST': ['d2'],

            'expid_d1_m1_1_CLEAN': ['d1_m1_1'],
            'expid_d2_m1_1_CLEAN': ['d2'], 'expid_d2_m1_2_CLEAN': ['d2'], 'expid_d2_m2_1_CLEAN': ['d2'],
            'expid_d2_m2_2_CLEAN': ['d2']
        }

        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        side_effect = []
        for job in reversed(self.job_list.get_job_list()):
            if job.date is not None:
                side_effect.append(job.date)

        with patch('autosubmit.job.job_grouping.date2str', side_effect=side_effect):
            job_grouping = JobGrouping('automatic', self.job_list.get_job_list(), self.job_list)
            self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def test_group_by_member_expand_running(self):
        self.job_list.get_job_by_name('expid_d1_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m2_INI').status = Status.COMPLETED

        self.job_list.get_job_by_name('expid_d1_m1_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_CLEAN').status = Status.COMPLETED

        self.job_list.get_job_by_name('expid_d1_m1_2_SIM').status = Status.READY

        self.job_list.get_job_by_name('expid_d1_m2_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_CLEAN').status = Status.RUNNING

        self.job_list.get_job_by_name('expid_d1_m2_2_SIM').status = Status.READY

        groups_dict = dict()

        groups_dict['status'] = {'d1_m1': Status.READY, 'd2_m1': Status.WAITING,
                                 'd2_m2': Status.WAITING}
        groups_dict['jobs'] = {
            'expid_d1_m1_INI': ['d1_m1'], 'expid_d2_m1_INI': ['d2_m1'],
            'expid_d2_m2_INI': ['d2_m2'],

            'expid_d1_m1_1_SIM': ['d1_m1'], 'expid_d1_m1_2_SIM': ['d1_m1'],
            'expid_d2_m1_1_SIM': ['d2_m1'], 'expid_d2_m1_2_SIM': ['d2_m1'], 'expid_d2_m2_1_SIM': ['d2_m2'],
            'expid_d2_m2_2_SIM': ['d2_m2'],

            'expid_d1_m1_1_POST': ['d1_m1'], 'expid_d1_m1_2_POST': ['d1_m1'],
            'expid_d2_m1_1_POST': ['d2_m1'], 'expid_d2_m1_2_POST': ['d2_m1'], 'expid_d2_m2_1_POST': ['d2_m2'],
            'expid_d2_m2_2_POST': ['d2_m2'],

            'expid_d1_m1_1_CLEAN': ['d1_m1'], 'expid_d1_m1_2_CLEAN': ['d1_m1'],
            'expid_d2_m1_1_CLEAN': ['d2_m1'], 'expid_d2_m1_2_CLEAN': ['d2_m1'], 'expid_d2_m2_1_CLEAN': ['d2_m2'],
            'expid_d2_m2_2_CLEAN': ['d2_m2']
        }

        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        side_effect = []
        for job in reversed(self.job_list.get_job_list()):
            if job.member is not None:
                side_effect.append(job.date)

        with patch('autosubmit.job.job_grouping.date2str', side_effect=side_effect):
            job_grouping = JobGrouping('member', self.job_list.get_job_list(), self.job_list, expanded_status=[Status.RUNNING])
            self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def test_group_by_chunk_expand_failed_running(self):
        self.job_list.get_job_by_name('expid_d1_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m2_INI').status = Status.COMPLETED

        self.job_list.get_job_by_name('expid_d1_m1_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_CLEAN').status = Status.FAILED

        self.job_list.get_job_by_name('expid_d1_m1_2_SIM').status = Status.READY

        self.job_list.get_job_by_name('expid_d1_m2_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_CLEAN').status = Status.RUNNING

        self.job_list.get_job_by_name('expid_d1_m2_2_SIM').status = Status.READY

        groups_dict = dict()

        groups_dict['status'] = {'d1_m1_2': Status.READY, 'd1_m2_2': Status.READY,
                                 'd2_m1_1': Status.WAITING, 'd2_m1_2': Status.WAITING,
                                 'd2_m2_1': Status.WAITING, 'd2_m2_2': Status.WAITING}
        groups_dict['jobs'] = {
            'expid_d1_m1_2_SIM': ['d1_m1_2'],
            'expid_d1_m2_2_SIM': ['d1_m2_2'],
            'expid_d2_m1_1_SIM': ['d2_m1_1'], 'expid_d2_m1_2_SIM': ['d2_m1_2'], 'expid_d2_m2_1_SIM': ['d2_m2_1'],
            'expid_d2_m2_2_SIM': ['d2_m2_2'],

            'expid_d1_m1_2_POST': ['d1_m1_2'],
            'expid_d1_m2_2_POST': ['d1_m2_2'],
            'expid_d2_m1_1_POST': ['d2_m1_1'], 'expid_d2_m1_2_POST': ['d2_m1_2'], 'expid_d2_m2_1_POST': ['d2_m2_1'],
            'expid_d2_m2_2_POST': ['d2_m2_2'],

            'expid_d1_m1_2_CLEAN': ['d1_m1_2'],
            'expid_d1_m2_2_CLEAN': ['d1_m2_2'],
            'expid_d2_m1_1_CLEAN': ['d2_m1_1'], 'expid_d2_m1_2_CLEAN': ['d2_m1_2'], 'expid_d2_m2_1_CLEAN': ['d2_m2_1'],
            'expid_d2_m2_2_CLEAN': ['d2_m2_2']
        }

        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        side_effect = []
        for job in reversed(self.job_list.get_job_list()):
            if job.chunk is not None:
                side_effect.append(job.date)

        with patch('autosubmit.job.job_grouping.date2str', side_effect=side_effect):
            job_grouping = JobGrouping('chunk', self.job_list.get_job_list(), self.job_list, expanded_status=[Status.RUNNING, Status.FAILED])
            self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def test_group_by_member_expand(self):
        self.job_list.get_job_by_name('expid_d1_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m2_INI').status = Status.COMPLETED

        self.job_list.get_job_by_name('expid_d1_m1_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_CLEAN').status = Status.COMPLETED

        self.job_list.get_job_by_name('expid_d1_m1_2_SIM').status = Status.READY

        self.job_list.get_job_by_name('expid_d1_m2_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_CLEAN').status = Status.RUNNING

        self.job_list.get_job_by_name('expid_d1_m2_2_SIM').status = Status.READY

        groups_dict = dict()

        groups_dict['status'] = {'d1_m1': Status.READY}
        groups_dict['jobs'] = {
            'expid_d1_m1_INI': ['d1_m1'],

            'expid_d1_m1_1_SIM': ['d1_m1'], 'expid_d1_m1_2_SIM': ['d1_m1'],

            'expid_d1_m1_1_POST': ['d1_m1'], 'expid_d1_m1_2_POST': ['d1_m1'],

            'expid_d1_m1_1_CLEAN': ['d1_m1'], 'expid_d1_m1_2_CLEAN': ['d1_m1'],
        }

        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        side_effect = ['d1', 'd2']
        for job in reversed(self.job_list.get_job_list()):
            if job.member is not None:
                side_effect.append(job.date)

        with patch('autosubmit.job.job_grouping.date2str', side_effect=side_effect):
            job_grouping = JobGrouping('member', self.job_list.get_job_list(), self.job_list,
                                   expand_list="[ d1 [m2] d2 [m1 m2] ]")
            self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def test_group_by_member_expand_and_running(self, *patches):
        self.job_list.get_job_by_name('expid_d1_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m2_INI').status = Status.COMPLETED

        self.job_list.get_job_by_name('expid_d1_m1_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_CLEAN').status = Status.COMPLETED

        self.job_list.get_job_by_name('expid_d1_m1_2_SIM').status = Status.READY

        self.job_list.get_job_by_name('expid_d1_m2_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_CLEAN').status = Status.RUNNING

        self.job_list.get_job_by_name('expid_d1_m2_2_SIM').status = Status.READY

        self.job_list.get_job_by_name('expid_d2_m1_1_SIM').status = Status.RUNNING

        groups_dict = dict()

        groups_dict['status'] = {'d1_m1': Status.READY}
        groups_dict['jobs'] = {
            'expid_d1_m1_INI': ['d1_m1'],

            'expid_d1_m1_1_SIM': ['d1_m1'], 'expid_d1_m1_2_SIM': ['d1_m1'],

            'expid_d1_m1_1_POST': ['d1_m1'], 'expid_d1_m1_2_POST': ['d1_m1'],

            'expid_d1_m1_1_CLEAN': ['d1_m1'], 'expid_d1_m1_2_CLEAN': ['d1_m1'],
        }

        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        side_effect = ['d1', 'd2']
        for job in reversed(self.job_list.get_job_list()):
            if job.member is not None:
                side_effect.append(job.date)

        with patch('autosubmit.job.job_grouping.date2str', side_effect=side_effect):
            job_grouping = JobGrouping('member', self.job_list.get_job_list(), self.job_list,
                                   expand_list="[ d1 [m2] d2 [m2] ]", expanded_status=[Status.RUNNING])
            self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def test_group_by_chunk_expand(self, *patches):
        self.job_list.get_job_by_name('expid_d1_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m1_INI').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d2_m2_INI').status = Status.COMPLETED

        self.job_list.get_job_by_name('expid_d1_m1_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m1_1_CLEAN').status = Status.FAILED

        self.job_list.get_job_by_name('expid_d1_m1_2_SIM').status = Status.READY

        self.job_list.get_job_by_name('expid_d1_m2_1_SIM').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_POST').status = Status.COMPLETED
        self.job_list.get_job_by_name('expid_d1_m2_1_CLEAN').status = Status.RUNNING

        groups_dict = dict()

        groups_dict['status'] = {'d1_m1_1': Status.FAILED, 'd1_m1_2': Status.READY, 'd1_m2_1': Status.RUNNING, 'd2_m2_2': Status.WAITING}
        groups_dict['jobs'] = {
            'expid_d1_m1_1_SIM': ['d1_m1_1'], 'expid_d1_m1_2_SIM': ['d1_m1_2'], 'expid_d1_m2_1_SIM': ['d1_m2_1'],
            'expid_d2_m2_2_SIM': ['d2_m2_2'],

            'expid_d1_m1_1_POST': ['d1_m1_1'], 'expid_d1_m1_2_POST': ['d1_m1_2'], 'expid_d1_m2_1_POST': ['d1_m2_1'],
            'expid_d2_m2_2_POST': ['d2_m2_2'],

            'expid_d1_m1_1_CLEAN': ['d1_m1_1'], 'expid_d1_m1_2_CLEAN': ['d1_m1_2'], 'expid_d1_m2_1_CLEAN': ['d1_m2_1'],
            'expid_d2_m2_2_CLEAN': ['d2_m2_2']
        }

        self.job_list.get_date_list = Mock(return_value=['d1', 'd2'])
        self.job_list.get_member_list = Mock(return_value=['m1', 'm2'])
        self.job_list.get_chunk_list = Mock(return_value=[1, 2])
        self.job_list.get_date_format = Mock(return_value='')

        side_effect = ['d1', 'd2']
        for job in reversed(self.job_list.get_job_list()):
            if job.chunk is not None:
                side_effect.append(job.date)

        with patch('autosubmit.job.job_grouping.date2str', side_effect=side_effect):
            job_grouping = JobGrouping('chunk', self.job_list.get_job_list(), self.job_list,
                                   expand_list="[ d1 [m2 [2] ] d2 [m1 [1 2] m2 [1] ] ]")
            self.assertDictEqual(job_grouping.group_jobs(), groups_dict)

    def _createDummyJob(self, name, status, date=None, member=None, chunk=None, split=None):
        job_id = randrange(1, 999)
        job = Job(name, job_id, status, 0)
        job.type = randrange(0, 2)

        job.date = date
        job.member = member
        job.chunk = chunk
        job.split = split

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



