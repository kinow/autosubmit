#!/usr/bin/env python

# Copyright 2015 Earth Sciences Department, BSC-CNS

# This file is part of Autosubmit.

# Autosubmit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Autosubmit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Autosubmit.  If not, see <http://www.gnu.org/licenses/>.
import pickle
from sys import setrecursionlimit
from autosubmit.job.job import Job
import os


class JobListPersistence(object):
    def save(self, persistence_path, persistence_file, job_list):
        """
        Persists a job list

        :param job_list: JobList
        :param persistence_file: str
        :param persistence_path: str
        """
        raise NotImplementedError

    def load(self, persistence_path, persistence_file):
        """
        Loads a job list from persistence

        :param persistence_file: str
        :param persistence_path: str
        """
        raise NotImplementedError


class JobListPersistencePkl(JobListPersistence):

    EXT = '.pkl'

    def load(self, persistence_path, persistence_file):
        """
        Loads a job list from a pkl file

        :param persistence_file: str
        :param persistence_path: str
        """
        path = os.path.join(persistence_path, persistence_file + EXT)
        if os.path.exists(path):
            fd = open(path, 'r')
            return pickle.load(fd)
        else:
            Log.critical('File {0} does not exist'.format(filename))
            return list()

    def save(self, persistence_path, persistence_file, job_list):
        """
        Persists a job list in a pkl file

        :param job_list: JobList
        :param persistence_file: str
        :param persistence_path: str
        """
        path = os.path.join(persistence_path, persistence_file + EXT)
        fd = open(path, 'w')
        setrecursionlimit(50000)
        Log.debug("Saving JobList: " + path)
        pickle.dump(job_list, fd)
        Log.debug('Joblist saved')


class JobListPersistenceDb(JobListPersistence):

    VERSION = 1
    JOB_LIST_TABLE = 'job_list'

    def __init__(self, persistence_path, persistence_file):
        self.db_manager = DbManager(persistence_path, persistence_file, self.VERSION)

    def load(self, persistence_path, persistence_file):
        """
        Loads a job list from a database

        :param persistence_file: str
        :param persistence_path: str
        """
        job_list = list()
        rows = self.db_manager.select_all(self.JOB_LIST_TABLE)
        for row in rows:
            job_list.append(Job(row[0], row[1], row[2], row[3]))
        return job_list

    def save(self, persistence_path, persistence_file, job_list):
        """
        Persists a job list in a database

        :param job_list: JobList
        :param persistence_file: str
        :param persistence_path: str
        """
        self._reset_table()
        for job in job_list:
            self.db_manager.insert(self.JOB_LIST_TABLE, [job.name, job.id, job.status, job.priority])

    def _reset_table(self):
        """
        Drops and recreates the database
        """
        self.db_manager.drop_table(self.JOB_LIST_TABLE)
        self.db_manager.create_table(self.JOB_LIST_TABLE, ['name', 'id', 'status', 'priority'])
