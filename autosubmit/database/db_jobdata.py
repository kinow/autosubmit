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

import os
import sys
import string
import time
import pickle
import textwrap
import traceback
import sqlite3
import copy
import collections
from datetime import datetime
from json import dumps
#from networkx import DiGraph
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.job.job_common import Status
from autosubmit.job.job_package_persistence import JobPackagePersistence
from bscearth.utils.date import date2str, parse_date, previous_day, chunk_end_date, chunk_start_date, Log, subs_dates


CURRENT_DB_VERSION = 12  # Used to be 10
# Defining RowType standard


class RowType:
    NORMAL = 2
    #PACKED = 2


_debug = True
JobItem = collections.namedtuple('JobItem', ['id', 'counter', 'job_name', 'created', 'modified', 'submit', 'start', 'finish',
                                             'status', 'rowtype', 'ncpus', 'wallclock', 'qos', 'energy', 'date', 'section', 'member', 'chunk', 'last', 'platform', 'job_id', 'extra_data', 'nnodes', 'run_id'])

ExperimentRunItem = collections.namedtuple('ExperimentRunItem', [
                                           'run_id', 'created', 'start', 'finish', 'chunk_unit', 'chunk_size', 'completed', 'total', 'failed', 'queuing', 'running', 'submitted'])

ExperimentRow = collections.namedtuple(
    'ExperimentRow', ['exp_id', 'expid', 'status', 'seconds'])


class ExperimentRun():

    def __init__(self, run_id, created=None, start=0, finish=0, chunk_unit="NA", chunk_size=0, completed=0, total=0, failed=0, queuing=0, running=0, submitted=0):
        self.run_id = run_id
        self.created = created if created else datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
        self.start = start
        self.finish = finish
        self.chunk_unit = chunk_unit
        self.chunk_size = chunk_size
        self.submitted = submitted
        self.queuing = queuing
        self.running = running
        self.completed = completed
        self.failed = failed
        self.total = total

    def _increase_counter(self, status):
        if status == Status.FAILED:
            self.failed += 1
        elif status == Status.SUBMITTED:
            self.submitted += 1
        elif status == Status.QUEUING:
            self.queuing += 1
        elif status == Status.RUNNING:
            self.running += 1
        elif status == Status.COMPLETED:
            self.completed += 1 if self.completed < self.total else 0
        else:
            pass

    def _decrease_counter(self, status):
        if status == Status.FAILED:
            self.failed -= 1 if self.failed > 0 else 0
        elif status == Status.SUBMITTED:
            self.submitted -= 1 if self.submitted > 0 else 0
        elif status == Status.QUEUING:
            self.queuing -= 1 if self.queuing > 0 else 0
        elif status == Status.RUNNING:
            self.running -= 1 if self.running > 0 else 0
        elif status == Status.COMPLETED:
            self.completed -= 1 if self.completed > 0 else 0
        else:
            pass

    def update_counters(self, prev_status, status):
        if prev_status != status:
            self._increase_counter(status)
            self._decrease_counter(prev_status)


class JobData():
    """Job Data object
    """

    def __init__(self, _id, counter=1, job_name="None", created=None, modified=None, submit=0, start=0, finish=0, status="UNKNOWN", rowtype=0, ncpus=0, wallclock="00:00", qos="debug", energy=0, date="", section="", member="", chunk=0, last=1, platform="NA", job_id=0, extra_data=dict(), nnodes=0, run_id=None):
        """[summary]

        Args:
            _id (int): Internal Id
            counter (int, optional): [description]. Defaults to 1.
            job_name (str, optional): [description]. Defaults to "None".
            created (datetime, optional): [description]. Defaults to None.
            modified (datetime, optional): [description]. Defaults to None.
            submit (int, optional): [description]. Defaults to 0.
            start (int, optional): [description]. Defaults to 0.
            finish (int, optional): [description]. Defaults to 0.
            status (str, optional): [description]. Defaults to "UNKNOWN".
            rowtype (int, optional): [description]. Defaults to 1.
            ncpus (int, optional): [description]. Defaults to 0.
            wallclock (str, optional): [description]. Defaults to "00:00".
            qos (str, optional): [description]. Defaults to "debug".
            energy (int, optional): [description]. Defaults to 0.
            date (str, optional): [description]. Defaults to "".
            section (str, optional): [description]. Defaults to "".
            member (str, optional): [description]. Defaults to "".
            chunk (int, optional): [description]. Defaults to 0.
            last (int, optional): [description]. Defaults to 1.
            platform (str, optional): [description]. Defaults to "NA".
            job_id (int, optional): [description]. Defaults to 0.
        """
        self._id = _id
        self.counter = counter
        self.job_name = job_name
        self.created = created if created else datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
        self.modified = modified if modified else datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
        self._submit = int(submit)
        self._start = int(start)
        self._finish = int(finish)
        self.status = status
        self.rowtype = rowtype
        self.ncpus = ncpus
        self.wallclock = wallclock
        self.qos = qos if qos else "debug"
        self._energy = energy if energy else 0
        self.date = date if date else ""
        self.section = section if section else ""
        self.member = member if member else ""
        self.chunk = chunk if chunk else 0
        self.last = last
        self._platform = platform if platform and len(
            platform) > 0 else "NA"
        self.job_id = job_id if job_id else 0
        self.extra_data = dumps(extra_data)
        self.nnodes = nnodes
        self.run_id = run_id

    @property
    def submit(self):
        return int(self._submit)

    @property
    def start(self):
        return int(self._start)

    @property
    def finish(self):
        return int(self._finish)

    @property
    def platform(self):
        return self._platform

    @property
    def energy(self):
        return self._energy

    @submit.setter
    def submit(self, submit):
        self._submit = int(submit)

    @start.setter
    def start(self, start):
        self._start = int(start)

    @finish.setter
    def finish(self, finish):
        self._finish = int(finish)

    @platform.setter
    def platform(self, platform):
        self._platform = platform if platform and len(platform) > 0 else "NA"

    @energy.setter
    def energy(self, energy):
        self._energy = energy if energy else 0


class JobDataList():
    """Object that stores the list of jobs to be handled.
    """

    def __init__(self, expid):
        self.jobdata_list = list()
        self.expid = expid

    def add_jobdata(self, jobdata):
        self.jobdata_list.append(jobdata)

    def size(self):
        return len(self.jobdata_list)


class MainDataBase():
    def __init__(self, expid):
        self.expid = expid
        self.conn = None
        self.conn_ec = None
        self.create_table_query = None
        self.create_table_header_query = None
        self.version_schema_changes = []

    def create_connection(self, db_file):
        """ 
        Create a database connection to the SQLite database specified by db_file.  
        :param db_file: database file name  
        :return: Connection object or None
        """
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except:
            return None

    def create_table(self, statement):
        """ create a table from the create_table_sql statement
        :param conn: Connection object
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        try:
            if self.conn:
                c = self.conn.cursor()
                c.execute(statement)
                self.conn.commit()
            else:
                raise IOError("Not a valid connection")
        except IOError as exp:
            Log.warning(exp)
            return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(str(type(e).__name__))
            Log.warning("Error on create table . create_table")
            return None

    def create_index(self):
        """ Creates index from statement defined in child class
        """
        try:
            if self.conn:
                c = self.conn.cursor()
                c.execute(self.create_index_query)
                self.conn.commit()
            else:
                raise IOError("Not a valid connection")
        except IOError as exp:
            Log.warning(exp)
            return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(str(type(e).__name__))
            Log.warning("Error on create index . create_index")
            return None

    def update_table_schema(self):
        """[summary]
        """
        try:
            if self.conn:
                c = self.conn.cursor()
                for item in self.version_schema_changes:
                    try:
                        c.execute(item)
                    except sqlite3.Error as e:
                        if _debug == True:
                            Log.info(str(type(e).__name__))
                        Log.debug(str(type(e).__name__))
                        Log.warning(
                            "Error on updating table schema statement. It is safe to ignore this message.")
                        pass
                self.conn.commit()
            else:
                raise IOError("Not a valid connection")
        except IOError as exp:
            Log.warning(exp)
            return None
        except Exception as exp:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(str(exp))
            Log.warning(
                "Error on updating table schema . update_table_schema.")
            return None


class ExperimentStatus(MainDataBase):
    def __init__(self, expid):
        MainDataBase.__init__(self, expid)
        BasicConfig.read()
        self.DB_FILE_AS_TIMES = os.path.join(
            BasicConfig.LOCAL_ROOT_DIR, "as_times.db")
        self.DB_FILE_ECEARTH = os.path.join(
            BasicConfig.LOCAL_ROOT_DIR, "ecearth.db")
        self.PKL_FILE_PATH = os.path.join(
            BasicConfig.LOCAL_ROOT_DIR, expid, "pkl", "job_list_" + str(self.expid) + ".pkl")
        self.create_table_query = textwrap.dedent(
            '''CREATE TABLE
        IF NOT EXISTS experiment_status (
        exp_id integer PRIMARY KEY,
        name text NOT NULL,
        status text NOT NULL,
        seconds_diff integer NOT NULL,
        modified text NOT NULL,
        FOREIGN KEY (exp_id) REFERENCES experiment (id)
        );''')

        if not os.path.exists(self.DB_FILE_AS_TIMES):
            open(self.DB_FILE_AS_TIMES, "w")
            self.conn = self.create_connection(self.DB_FILE_AS_TIMES)
            self.create_table()
        else:
            self.conn = self.create_connection(self.DB_FILE_AS_TIMES)

        if os.path.exists(self.DB_FILE_ECEARTH):
            self.conn_ec = self.create_connection(self.DB_FILE_ECEARTH)

        self.current_table = self.prepare_status_db()
        self.current_row = next(
            (exp for exp in self.current_table if exp.expid == self.expid), None) if len(self.current_table) > 0 else None

    def print_current_table(self):
        for experiment in self.current_table:
            #experiment = ExperimentRow(k, *v)
            print(experiment.expid)
            print(experiment.exp_id)
            print(experiment.status)
            print(experiment.seconds)
            print("\n")
        if self.current_row:
            print("Current Row:\n\t" + self.current_row.expid + "\n\t" +
                  str(self.current_row.exp_id) + "\n\t" + self.current_row.status)

    def prepare_status_db(self):
        """
        Returns the contents of the status table in an ordered way 
        :return: Map from experiment name to (Id of experiment, Status, Seconds)  
        :rtype: Dictionary Key: String, Value: Integer, String, Integer
        """
        #self.conn = self.create_connection(self.DB_FILE_AS_TIMES)

        #drop_table_query = ''' DROP TABLE experiment_status '''
        # create_table(conn, drop_table_query)
        # self.create_table()
        current_table = self._get_exp_status()
        result = list()
        # print(current_table)
        # print(type(current_table))
        if current_table:
            for item in current_table:
                #exp_id, expid, status, seconds = item
                result.append(ExperimentRow(*item))
        return result

    def _get_id_db(self):
        """
        Get exp_id of the experiment (different than the experiment name).  
        :param conn: ecearth.db connection  
        :type conn: sqlite3 connection  
        :param expid: Experiment name  
        :type expid: String  
        :return: Id of the experiment  
        :rtype: Integer or None
        """
        try:
            if self.conn_ec:
                cur = self.conn_ec.cursor()
                cur.execute(
                    "SELECT id FROM experiment WHERE name=?", (self.expid,))
                row = cur.fetchone()
                return int(row[0])
            return None
        except Exception as exp:
            Log.debug("From _get_id_db: {0}".format(str(exp)))
            Log.warning(
                "Autosubmit couldn't retrieve experiment database information. _get_id_db")
            return None

    def _get_exp_status(self):
        """
        Get all registers from experiment_status.\n
        :return: row content: exp_id, name, status, seconds_diff  
        :rtype: 4-tuple (int, str, str, int)
        """
        try:
            if self.conn:
                #conn = create_connection(DB_FILE_AS_TIMES)
                self.conn.text_factory = str
                cur = self.conn.cursor()
                cur.execute(
                    "SELECT exp_id, name, status, seconds_diff FROM experiment_status")
                rows = cur.fetchall()
                return rows
            return None
        except Exception as exp:
            Log.debug("From _get_exp_status: {0}".format(str(exp)))
            Log.warning(
                "Autosubmit couldn't retrieve experiment status database information. _get_exp_status")
            return None

    def test_running(self, time_condition=600):
        if (os.path.exists(self.PKL_FILE_PATH)):
            current_stat = os.stat(self.PKL_FILE_PATH)
            timest = int(current_stat.st_mtime)
            timesys = int(time.time())
            time_diff = int(timesys - timest)
            if (time_diff < time_condition):
                return True
            else:
                return False

    def update_running_status(self, status="RUNNING"):
        if self.current_row:
            # Row exists
            self._update_exp_status(status)
        else:
            # New Row
            self._create_exp_status()

    def _create_exp_status(self):
        """
        Create experiment status
        :param conn:
        :param details:
        :return:
        """
        try:
            if self.conn and self.conn_ec:
                exp_id = self._get_id_db()
                #conn = create_connection(DB_FILE_AS_TIMES)
                creation_date = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
                sql = ''' INSERT INTO experiment_status(exp_id, name, status, seconds_diff, modified) VALUES(?,?,?,?,?) '''
                # print(row_content)
                cur = self.conn.cursor()
                cur.execute(sql, (exp_id,
                                  self.expid, "RUNNING", 0, creation_date))
                # print(cur)
                self.conn.commit()
                return cur.lastrowid
        except sqlite3.Error as e:
            Log.debug("From _create_exp_status: {0}".format(
                str(type(e).__name__)))
            Log.warning(
                "Autosubmit couldn't insert information into status database. _create_exp_status")

    def _update_exp_status(self, status="RUNNING"):
        """
        Update existing experiment_status.  
        :param expid: Experiment name  
        :type expid: String  
        :param status: Experiment status  
        :type status: String  
        :param seconds_diff: Indicator of how long it has been active since the last time it was checked  
        :type seconds_diff: Integer  
        :return: Id of register  
        :rtype: Integer
        """
        try:
            if self.conn and self.current_row:
                # conn = create_connection(DB_FILE_AS_TIMES)
                modified_date = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
                sql = ''' UPDATE experiment_status SET status = ?, seconds_diff = ?, modified = ? WHERE name = ? '''
                cur = self.conn.cursor()
                cur.execute(sql, (status, 0, modified_date,
                                  self.current_row.expid))
                self.conn.commit()
                return cur.lastrowid
            return None
        except sqlite3.Error as e:
            Log.warning(
                "Error while trying to update {0} in experiment_status.".format(str(expid)))
            Log.debug("From _update_exp_status: {0}".format(
                traceback.format_exc()))
            # Log.warning("Error on Update: " + str(type(e).__name__))
            return None


class JobDataStructure(MainDataBase):

    def __init__(self, expid):
        """Initializes the object based on the unique identifier of the experiment.

        Args:
            expid (str): Experiment identifier
        """
        MainDataBase.__init__(self, expid)
        BasicConfig.read()
        #self.expid = expid
        self.basic_conf = BasicConfig
        self.expid = expid
        self.folder_path = BasicConfig.JOBDATA_DIR
        self.database_path = os.path.join(
            self.folder_path, "job_data_" + str(expid) + ".db")
        #self.conn = None
        self.jobdata_list = JobDataList(self.expid)
        self.version_schema_changes.append(
            "ALTER TABLE job_data ADD COLUMN nnodes INTEGER NOT NULL DEFAULT 0")
        self.version_schema_changes.append(
            "ALTER TABLE job_data ADD COLUMN run_id INTEGER")
        # We use rowtype to identify a packed job
        self.create_table_query = textwrap.dedent(
            '''CREATE TABLE
            IF NOT EXISTS job_data (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            counter INTEGER NOT NULL,
            job_name TEXT NOT NULL,
            created TEXT NOT NULL,
            modified TEXT NOT NULL,
            submit INTEGER NOT NULL,
            start INTEGER NOT NULL,
            finish INTEGER NOT NULL,
            status TEXT NOT NULL,
            rowtype INTEGER NOT NULL,
            ncpus INTEGER NOT NULL,
            wallclock TEXT NOT NULL,
            qos TEXT NOT NULL,
            energy INTEGER NOT NULL,
            date TEXT NOT NULL,
            section TEXT NOT NULL,
            member TEXT NOT NULL,
            chunk INTEGER NOT NULL,
            last INTEGER NOT NULL,
            platform TEXT NOT NULL,
            job_id INTEGER NOT NULL,
            extra_data TEXT NOT NULL,
            nnodes INTEGER NOT NULL DEFAULT 0,
            run_id INTEGER,
            UNIQUE(counter,job_name)
            );
            ''')

        # Creating the header table
        self.create_table_header_query = textwrap.dedent(
            '''CREATE TABLE 
            IF NOT EXISTS experiment_run (
            run_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            created TEXT NOT NULL,
            start INTEGER NOT NULL,
            finish INTEGER,
            chunk_unit TEXT NOT NULL,
            chunk_size INTEGER NOT NULL,
            completed INTEGER NOT NULL,
            total INTEGER NOT NULL,
            failed INTEGER NOT NULL,
            queuing INTEGER NOT NULL,
            running INTEGER NOT NULL,
            submitted INTEGER NOT NULL
            );
            ''')

        # Index creation is in a different statement
        self.create_index_query = textwrap.dedent(''' 
            CREATE INDEX IF NOT EXISTS ID_JOB_NAME ON job_data(job_name);
            ''')
        # print(self.database_path)
        if not os.path.exists(self.database_path):
            open(self.database_path, "w")
            self.conn = self.create_connection(self.database_path)
            self.create_table(self.create_table_header_query)
            self.create_table(self.create_table_query)
            self.create_index()
            if self._set_pragma_version(CURRENT_DB_VERSION):
                Log.info("Database version set.")
        else:
            self.conn = self.create_connection(self.database_path)
            db_version = self._select_pragma_version()
            if db_version != CURRENT_DB_VERSION:
                # Update to current version
                Log.info("Database schema needs update.")
                self.update_table_schema()
                self.create_index()
                self.create_table(self.create_table_header_query)
                if self._set_pragma_version(CURRENT_DB_VERSION):
                    Log.info("Database version set to {0}.".format(
                        CURRENT_DB_VERSION))
        self.current_run_id = self.get_current_run_id()

    def determine_rowtype(self, code):
        """
        Determines rowtype based on job information.

        :param packed: True if job belongs to wrapper, False otherwise
        :type packed: boolean
        :return: rowtype, 2 packed, 1 normal
        :rtype: int
        """
        if code:
            return code
        else:
            return RowType.NORMAL

    def get_current_run_id(self):
        current_run = self.get_max_id_experiment_run()
        if current_run:
            return current_run.run_id
        else:
            new_run = ExperimentRun(0)
            return self._insert_experiment_run(new_run)

    def process_status_changes(self, tracking_dictionary, job_list=None, chunk_unit="NA", chunk_size=0):
        current_run = self.get_max_id_experiment_run()
        if current_run:
            if tracking_dictionary is not None and bool(tracking_dictionary) == True:
                if job_list:
                    current_date_member_completed_count = sum(
                        1 for job in job_list if job.date is not None and job.member is not None and job.status == Status.COMPLETED)
                    if len(tracking_dictionary.keys()) >= int(current_date_member_completed_count * 0.9):
                        # If setstatus changes more than 90% of date-member completed jobs, it's a new run
                        # Must create a new experiment run
                        Log.result(
                            "Since a significant amount of jobs have changes status. Autosubmit will consider a new run of the same experiment.")
                        self.validate_current_run(
                            job_list, chunk_unit, chunk_size, True)
                        return None
                for name, (prev_status, status) in tracking_dictionary.items():
                    current_run.update_counters(prev_status, status)
                self._update_experiment_run(current_run)
        else:
            raise Exception("Empty header database")

    def validate_current_run(self, job_list, chunk_unit="NA", chunk_size=0, must_create=False):
        """[summary]

        :param job_list ([type]): [description]
        :param chunk_unit (str, optional): [description]. Defaults to "NA".
        :param chunk_size (int, optional): [description]. Defaults to 0.
        :param must_create (bool, optional): [description]. Defaults to False.

        :return: [description]
        """
        try:
            if not job_list:
                raise Exception(
                    "Autosubmit couldn't find the job_list. validate_current_run.")
            current_run = self.get_max_id_experiment_run()
            current_total = len(job_list)
            completed_count = sum(
                1 for job in job_list if job.status == Status.COMPLETED)
            failed_count = sum(
                1 for job in job_list if job.status == Status.FAILED)
            queue_count = sum(
                1 for job in job_list if job.status == Status.QUEUING)
            submit_count = sum(
                1 for job in job_list if job.status == Status.SUBMITTED)
            running_count = sum(
                1 for job in job_list if job.status == Status.RUNNING)

            if not current_run or must_create == True:
                new_run = ExperimentRun(0, None, 0, 0, chunk_unit, chunk_size, completed_count,
                                        current_total, failed_count, queue_count, running_count, submit_count)
                self.current_run_id = self._insert_experiment_run(new_run)
            else:
                if current_run.total != current_total:
                    new_run = ExperimentRun(0, None, 0, 0, chunk_unit, chunk_size, completed_count,
                                            current_total, failed_count, queue_count, running_count, submit_count)
                    self.current_run_id = self._insert_experiment_run(new_run)
                else:
                    current_run.completed = completed_count
                    current_run.failed = failed_count
                    current_run.queuing = queue_count
                    current_run.submitted = submit_count
                    current_run.running = running_count
                    self._update_experiment_run(current_run)
                    self.current_run_id = current_run.run_id
        except Exception as exp:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning(
                "Autosubmit couldn't insert a new experiment run register. validate_current_run {0}".format(str(exp)))
            return None

    def get_job_package_code(self, current_job_name):
        """
        Finds the package code and retrieves it. None if no package.

        :param BasicConfig: Basic configuration 
        :type BasicConfig: Configuration Object
        :param expid: Experiment Id
        :type expid: String
        :param current_job_name: Name of job
        :type current_jobs: string
        :return: package code, None if not found
        :rtype: int or None
        """
        packages = None
        try:
            packages = JobPackagePersistence(os.path.join(self.basic_conf.LOCAL_ROOT_DIR, self.expid, "pkl"),
                                             "job_packages_" + self.expid).load(wrapper=False)
        except Exception as ex:
            Log.debug(
                "Wrapper table not found, trying packages. JobDataStructure.retrieve_packages")
            packages = None
            try:
                packages = JobPackagePersistence(os.path.join(self.basic_conf.LOCAL_ROOT_DIR, self.expid, "pkl"),
                                                 "job_packages_" + self.expid).load(wrapper=True)
            except Exception as exp2:
                packages = None

        if (packages):
            try:
                for exp, package_name, job_name in packages:
                    if current_job_name == job_name:
                        code = int(package_name.split("_")[2])
                        return code
            except Exception as ex:
                Log.warning(
                    "Package parse error. JobDataStructure.retrieve_packages")
                Log.debug(traceback.format_exc())
                return None
        return None

    def write_submit_time(self, job_name, submit=0, status="UNKNOWN", ncpus=0, wallclock="00:00", qos="debug", date="", member="", section="", chunk=0, platform="NA", job_id=0, packed=False):
        """Writes submit time of job.

        Args:
            job_name ([type]): [description]
            submit (int, optional): [description]. Defaults to 0.
            status (str, optional): [description]. Defaults to "UNKNOWN".
            ncpus (int, optional): [description]. Defaults to 0.
            wallclock (str, optional): [description]. Defaults to "00:00".
            qos (str, optional): [description]. Defaults to "debug".
            date (str, optional): [description]. Defaults to "".
            member (str, optional): [description]. Defaults to "".
            section (str, optional): [description]. Defaults to "".
            chunk (int, optional): [description]. Defaults to 0.
            platform (str, optional): [description]. Defaults to "NA".
            job_id (int, optional): [description]. Defaults to 0.

        Returns:
            [type]: [description]
        """
        try:
            job_data = self.get_job_data(job_name)
            current_counter = 1
            max_counter = self._get_maxcounter_jobdata()
            if job_data and len(job_data) > 0:
                job_max_counter = max(job.counter for job in job_data)
                current_last = [
                    job for job in job_data if job.counter == job_max_counter]
                for current in current_last:
                    # Deactivate current last for this job
                    current.modified = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
                    up_id = self._deactivate_current_last(current)
                # Finding current counter
                current_counter = (
                    job_max_counter + 1) if job_max_counter >= max_counter else max_counter
            else:
                current_counter = max_counter
            # Insert new last
            rowid = self._insert_job_data(JobData(
                0, current_counter, job_name, None, None, submit, 0, 0, status, self.determine_rowtype(self.get_job_package_code(job_name)), ncpus, wallclock, qos, 0, date, member, section, chunk, 1, platform, job_id, dict(), 0, self.current_run_id))
            if rowid:
                return True
            else:
                return None
        except Exception as exp:
            Log.debug(traceback.format_exc())
            Log.warning(
                "Autosubmit couldn't write submit time.")
            return None

        # if rowid > 0:
        #     print("Successfully inserted")

    def write_start_time(self, job_name, start=0, status="UNKWNONW", ncpus=0, wallclock="00:00", qos="debug", date="", member="", section="", chunk=0, platform="NA", job_id=0, packed=False):
        """Writes start time into the database

        Args:
            job_name ([type]): [description]
            start (int, optional): [description]. Defaults to 0.
            status (str, optional): [description]. Defaults to "UNKWNONW".
            ncpus (int, optional): [description]. Defaults to 0.
            wallclock (str, optional): [description]. Defaults to "00:00".
            qos (str, optional): [description]. Defaults to "debug".
            date (str, optional): [description]. Defaults to "".
            member (str, optional): [description]. Defaults to "".
            section (str, optional): [description]. Defaults to "".
            chunk (int, optional): [description]. Defaults to 0.
            platform (str, optional): [description]. Defaults to "NA".
            job_id (int, optional): [description]. Defaults to 0.
            packed (bool, optional): [description]. Defaults to False.
            nnodes (int, optional): [description]. Defaults to 0.

        Returns:
            [type]: [description]
        """
        try:
            job_data_last = self.get_job_data_last(job_name)
            # Updating existing row
            if job_data_last:
                job_data_last = job_data_last[0]
                if job_data_last.start == 0:
                    job_data_last.start = start
                    job_data_last.status = status
                    job_data_last.job_id = job_id
                    job_data_last.modified = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
                    _updated = self._update_start_job_data(job_data_last)
                    return _updated
            # It is necessary to create a new row
            submit_inserted = self.write_submit_time(
                job_name, start, status, ncpus, wallclock, qos, date, member, section, chunk, platform, job_id, packed)
            if submit_inserted:
                # print("retro start")
                self.write_start_time(job_name, start, status,
                                      ncpus, wallclock, qos, date, member, section, chunk, platform, job_id, packed)
                return True
            else:
                return None
        except Exception as exp:
            Log.debug(traceback.format_exc())
            Log.warning(
                "Autosubmit couldn't write start time.")
            return None

    def write_finish_time(self, job_name, finish=0, status="UNKNOWN", ncpus=0, wallclock="00:00", qos="debug", date="", member="", section="", chunk=0, platform="NA", job_id=0, platform_object=None, packed=False, parent_id_list=[]):
        """Writes the finish time into the database

        Args:
            job_name (str): Name of Job.
            finish (int, optional): Finish time. Defaults to 0.
            status (str, optional): Current Status. Defaults to "UNKNOWN".
            ncpus (int, optional): Number of cpus. Defaults to 0.
            wallclock (str, optional): Wallclock value. Defaults to "00:00".
            qos (str, optional): Name of QoS. Defaults to "debug".
            date (str, optional): Date from config. Defaults to "".
            member (str, optional): Member from config. Defaults to "".
            section (str, optional): Section from config. Defaults to "".
            chunk (int, optional): Chunk from config. Defaults to 0.
            platform (str, optional): Name of platform of job. Defaults to "NA".
            job_id (int, optional): Id of job. Defaults to 0.
            platform_object (obj, optional): Platform object. Defaults to None.

        Returns:
            Boolean/None: True if success, None if exception.
        """
        try:
            # print("Writing finish time \t" + str(job_name) + "\t" + str(finish))
            job_data_last = self.get_job_data_last(job_name)
            # energy = 0
            submit_time = start_time = finish_time = number_nodes = number_cpus = energy = 0
            extra_data = dict()
            # Updating existing row
            if job_data_last:
                job_data_last = job_data_last[0]
                # Call Slurm here, update times.
                if platform_object:
                    # print("There is platform object")
                    try:
                        if type(platform_object) is not str:
                            if platform_object.type == "slurm":
                                # print("Checking Slurm for " + str(job_name))
                                submit_time, start_time, finish_time, energy, number_cpus, number_nodes, extra_data = platform_object.check_job_energy(
                                    job_id, packed)
                    except Exception as exp:
                        Log.info(traceback.format_exc())
                        Log.warning(str(exp))
                        #energy = 0
                try:
                    extra_data["parents"] = [int(item)
                                             for item in parent_id_list]
                except Exception as inner_exp:
                    Log.debug(
                        "Parent Id List couldn't be parsed to array of int. Using default values.")
                    extra_data["parents"] = parent_id_list
                    pass

                job_data_last.finish = finish_time if finish_time > 0 else int(
                    finish)
                job_data_last.status = status
                job_data_last.job_id = job_id
                job_data_last.energy = energy
                job_data_last.ncpus = number_cpus if number_cpus > 0 else job_data_last.ncpus
                job_data_last.nnodes = number_nodes if number_nodes > 0 else job_data_last.nnodes
                job_data_last.extra_data = dumps(
                    extra_data) if extra_data else "NA"
                job_data_last.modified = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
                if submit_time > 0 and start_time > 0:
                    job_data_last.submit = int(submit_time)
                    job_data_last.start = int(start_time)
                    rowid = self._update_finish_job_data_plus(job_data_last)
                else:
                    rowid = self._update_finish_job_data(job_data_last)
                return True
            # It is necessary to create a new row
            submit_inserted = self.write_submit_time(
                job_name, finish, status, ncpus, wallclock, qos, date, member, section, chunk, platform, job_id, packed)
            write_inserted = self.write_start_time(job_name, finish, status, ncpus,
                                                   wallclock, qos, date, member, section, chunk, platform, job_id, packed)
            # print(submit_inserted)
            # print(write_inserted)
            if submit_inserted and write_inserted:
                #print("retro finish")
                self.write_finish_time(
                    job_name, finish, status, ncpus, wallclock, qos, date, member, section, chunk, platform, job_id, platform_object, packed, number_nodes)
            else:
                return None
        except Exception as exp:
            Log.debug(traceback.format_exc())
            Log.warning("Autosubmit couldn't write finish time.")
            return None

    def retry_incompleted_data(self, list_jobs):
        """
        Retries retrieval of data that might be incompleted. 

        :param list_jobs: list of jobs in experiment
        :type list_jobs: list()

        :return: None (Modifies database)
        """
        try:
            pending_jobs = self.get_pending_data()
            if pending_jobs:
                for item in pending_jobs:
                    job_object = section = next(
                        (job for job in list_jobs if job.name == item), None)
                    if (job_object):
                        platform_object = job_object.platform
                        if type(platform_object) is not str:
                            if platform_object.type == "slurm":
                                # print("Checking Slurm for " + str(job_name))
                                Log.info("Attempting to complete information for {0}".format(
                                    job_object.name))
                                submit_time, start_time, finish_time, energy, extra_data = platform_object.check_job_energy(
                                    job_object.id, job_object.packed)
                                if submit_time > 0 and start_time > 0:
                                    job_data_last = self.get_job_data_last(
                                        job_object.name)[0]
                                    job_data_last.submit = int(submit_time)
                                    job_data_last.start = int(start_time)
                                    job_data_last.energy = energy
                                    job_data_last.extra_data = dumps(
                                        extra_data)
                                    job_data_last.modified = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
                                    rowid = self._update_finish_job_data_plus(
                                        job_data_last)
                                    Log.info("Historic data successfully retrieved and updated for: {0} {1}".format(
                                        job_object.name, rowid))
        except Exception as exp:
            print(traceback.format_exc())
            Log.warning(str(exp))
            return None

    def get_all_job_data(self):
        """[summary]

        Raises:
            Exception: [description]
        """
        try:
            if os.path.exists(self.folder_path):

                current_table = self._get_all_job_data()
                current_job_data = dict()
                for item in current_table:
                    # _id, _counter, _job_name, _created, _modified, _submit, _start, _finish, _status, _rowtype, _ncpus, _wallclock, _qos, _energy, _date, _section, _member, _chunk, _last, _platform = item
                    job_item = JobItem(*item)
                    self.jobdata_list.add_jobdata(JobData(job_item.id, job_item.counter, job_item.job_name, job_item.created, job_item.modified, job_item.submit, job_item.start, job_item.finish, job_item.status,
                                                          job_item.rowtype, job_item.ncpus, job_item.wallclock, job_item.qos, job_item.energy, job_item.date, job_item.section, job_item.member, job_item.chunk, job_item.last, job_item.platform, job_item.job_id, job_item.extra_data, job_item.nnodes, job_item.run_id))

            else:
                raise Exception("Job data folder not found :" +
                                str(self.jobdata_path))
        except Exception as exp:
            Log.debug(traceback.format_exc())
            Log.warning(
                "Autosubmit couldn't retrieve job data. get_all_job_data")
            return None

    def get_job_data(self, job_name):
        """Retrieves all the rows that have the same job_name

        Args:
            job_name (str): [description]

        Raises:
            Exception: If path to data folder does not exist

        Returns:
            [type]: None if error, list of jobs if successful
        """
        try:
            job_data = list()
            if os.path.exists(self.folder_path):
                current_job = self._get_job_data(job_name)
                for item in current_job:
                    job_item = JobItem(*item)
                    job_data.append(JobData(job_item.id, job_item.counter, job_item.job_name, job_item.created, job_item.modified, job_item.submit, job_item.start, job_item.finish, job_item.status,
                                            job_item.rowtype, job_item.ncpus, job_item.wallclock, job_item.qos, job_item.energy, job_item.date, job_item.section, job_item.member, job_item.chunk, job_item.last, job_item.platform, job_item.job_id, job_item.extra_data, job_item.nnodes, job_item.run_id))
                return job_data
            else:
                raise Exception("Job data folder not found :" +
                                str(self.jobdata_path))
        except Exception as exp:
            Log.debug(traceback.format_exc())
            Log.warning("Autosubmit couldn't retrieve job data. get_job_data")
            return None

    def get_pending_data(self):
        """[summary]
        """
        try:
            job_names_list = list()
            if os.path.exists(self.folder_path):
                current_pending = self._get_job_data_pending()
                if current_pending:
                    for item in current_pending:
                        job_id, job_name, job_rowtype = item
                        job_names_list.append(job_name)
                        # job_name_to_detail[job_name] = (job_id, job_rowtype)
                        # jobid_list.append(job_id)
                    return job_names_list
                else:
                    return None
        except Exception as exp:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning(
                "Autosubmit couldn't retrieve job data. get_job_data_last")
            return None

    def get_max_id_experiment_run(self):
        try:
            #expe = list()
            if os.path.exists(self.folder_path):
                current_experiment_run = self._get_max_id_experiment_run()
                if current_experiment_run:
                    exprun_item = ExperimentRunItem(*current_experiment_run)
                    return ExperimentRun(exprun_item.run_id, exprun_item.created, exprun_item.start, exprun_item.finish, exprun_item.chunk_unit, exprun_item.chunk_size, exprun_item.completed, exprun_item.total, exprun_item.failed, exprun_item.queuing, exprun_item.running, exprun_item.submitted)
                else:
                    return None
            else:
                raise Exception("Job data folder not found :" +
                                str(self.jobdata_path))
        except Exception as exp:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning(
                "Autosubmit couldn't retrieve experiment run header. get_max_id_experiment_run")
            return None

    def get_job_data_last(self, job_name):
        """ Returns latest jobdata row for a job_name. The current version.

        Args:
            job_name ([type]): [description]

        Raises:
            Exception: [description]

        Returns:
            [type]: None if error, JobData if success
        """
        try:
            jobdata = list()
            if os.path.exists(self.folder_path):
                current_job_last = self._get_job_data_last(job_name)
                if current_job_last:
                    for current in current_job_last:
                        job_item = JobItem(*current)
                        jobdata.append(JobData(job_item.id, job_item.counter, job_item.job_name, job_item.created, job_item.modified, job_item.submit, job_item.start, job_item.finish, job_item.status,
                                               job_item.rowtype, job_item.ncpus, job_item.wallclock, job_item.qos, job_item.energy, job_item.date, job_item.section, job_item.member, job_item.chunk, job_item.last, job_item.platform, job_item.job_id, job_item.extra_data, job_item.nnodes, job_item.run_id))
                    return jobdata
                else:
                    return None
            else:
                raise Exception("Job data folder not found :" +
                                str(self.jobdata_path))
        except Exception as exp:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning(
                "Autosubmit couldn't retrieve job data. get_job_data_last")
            return None

    def _deactivate_current_last(self, jobdata):
        """Sets last = 0 to row with id

        Args:
            jobdata ([type]): [description]

        Returns:
            [type]: [description]
        """
        try:
            if self.conn:
                sql = ''' UPDATE job_data SET last=0, modified = ? WHERE id = ?'''
                tuplerow = (jobdata.modified, jobdata._id)
                cur = self.conn.cursor()
                cur.execute(sql, tuplerow)
                self.conn.commit()
                return cur.lastrowid
            return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on Insert : " + str(type(e).__name__))
            return None

    def _update_start_job_data(self, jobdata):
        """Update job_data by id. Updates start, modified, job_id, status.

        Args:
            jobdata ([type]): [description]

        Returns:
            [type]: [description]
        """
        # current_time =
        try:
            if self.conn:
                sql = ''' UPDATE job_data SET start=?, modified=?, job_id=?, status=? WHERE id=? '''
                cur = self.conn.cursor()
                cur.execute(sql, (int(jobdata.start),
                                  jobdata.modified, jobdata.job_id, jobdata.status, jobdata._id))
                self.conn.commit()
                return True
            return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on Insert : " + str(type(e).__name__))
            return None

    def _update_finish_job_data_plus(self, jobdata):
        """Updates job_data by id. Updates submit, start, finish, modified, job_id, status, energy, extra_data, nnodes, ncpus

        Args:
            jobdata (JobData): JobData object

        Returns:
            int/None: lastrowid if success, None if error
        """
        try:
            if self.conn:
                sql = ''' UPDATE job_data SET submit=?, start=?, finish=?, modified=?, job_id=?, status=?, energy=?, extra_data=?, nnodes=?, ncpus=? WHERE id=? '''
                cur = self.conn.cursor()
                cur.execute(sql, (jobdata.submit, jobdata.start, jobdata.finish, jobdata.modified, jobdata.job_id,
                                  jobdata.status, jobdata.energy, jobdata.extra_data, jobdata.nnodes, jobdata.ncpus, jobdata._id))
                self.conn.commit()
                return cur.lastrowid
            return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on Update : " + str(type(e).__name__))
            return None

    def _update_finish_job_data(self, jobdata):
        """Update register by id. Updates finish, modified, job_id, status, energy, extra_data, nnodes, ncpus

        Args:
            jobdata ([type]): [description]

        Returns:
            [type]: None if error, lastrowid if success
        """
        try:
            if self.conn:
                # print("Updating finish time")
                sql = ''' UPDATE job_data SET finish=?, modified=?, job_id=?, status=?, energy=?, extra_data=?, nnodes=?, ncpus=? WHERE id=? '''
                cur = self.conn.cursor()
                cur.execute(sql, (jobdata.finish, jobdata.modified, jobdata.job_id,
                                  jobdata.status, jobdata.energy, jobdata.extra_data, jobdata.nnodes, jobdata.ncpus, jobdata._id))
                self.conn.commit()
                return cur.lastrowid
            return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on Update : " + str(type(e).__name__))
            return None

    def _update_experiment_run(self, experiment_run):
        """Updates experiment run row by run_id (finish, chunk_unit, chunk_size, completed, total, failed, queuing, running, submitted)

        :param experiment_run: Object representation of experiment run row 
        :type experiment_run: ExperimentRun object

        :return: None
        """
        try:
            if self.conn:
                sql = ''' UPDATE experiment_run SET finish=?, chunk_unit=?, chunk_size=?, completed=?, total=?, failed=?, queuing=?, running=?, submitted=? WHERE run_id=? '''
                cur = self.conn.cursor()
                cur.execute(sql, (experiment_run.finish, experiment_run.chunk_unit, experiment_run.chunk_size,
                                  experiment_run.completed, experiment_run.total, experiment_run.failed, experiment_run.queuing, experiment_run.running, experiment_run.submitted, experiment_run.run_id))
                self.conn.commit()
                return cur.lastrowid
            return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on update experiment_run : " +
                        str(type(e).__name__))
            return None

    def _insert_job_data(self, jobdata):
        """[summary]
        Inserts a new job_data register.
        :param jobdata: JobData object
        """
        try:
            if self.conn:
                #print("preparing to insert")
                sql = ''' INSERT INTO job_data(counter, job_name, created, modified, submit, start, finish, status, rowtype, ncpus, wallclock, qos, energy, date, section, member, chunk, last, platform, job_id, extra_data, nnodes, run_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
                tuplerow = (jobdata.counter, jobdata.job_name, jobdata.created, jobdata.modified, jobdata.submit, jobdata.start,
                            jobdata.finish, jobdata.status, jobdata.rowtype, jobdata.ncpus, jobdata.wallclock, jobdata.qos, jobdata.energy, jobdata.date, jobdata.section, jobdata.member, jobdata.chunk, jobdata.last, jobdata.platform, jobdata.job_id, jobdata.extra_data, jobdata.nnodes, jobdata.run_id)
                cur = self.conn.cursor()
                #print("pre insert")
                cur.execute(sql, tuplerow)
                self.conn.commit()
                #print("Inserted " + str(jobdata.job_name))
                return cur.lastrowid
            else:
                #print("Not a valid connection.")
                return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on Insert : " + str(type(e).__name__) +
                        "\t " + str(jobdata.job_name) + "\t" + str(jobdata.counter))
            return None

    def _insert_experiment_run(self, experiment_run):
        """[summary]
        Inserts a new experiment_run register.
        :param experiment_run: ExperimentRun object
        """
        try:
            if self.conn:
                #print("preparing to insert")
                sql = ''' INSERT INTO experiment_run(created,start,finish,chunk_unit,chunk_size,completed,total,failed,queuing,running,submitted) VALUES(?,?,?,?,?,?,?,?,?,?,?) '''
                tuplerow = (experiment_run.created, experiment_run.start, experiment_run.finish, experiment_run.chunk_unit, experiment_run.chunk_size, experiment_run.completed,
                            experiment_run.total, experiment_run.failed, experiment_run.queuing, experiment_run.running, experiment_run.submitted)
                cur = self.conn.cursor()
                cur.execute(sql, tuplerow)
                self.conn.commit()
                return cur.lastrowid
            else:
                return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on insert on experiment_run: {0}".format(
                str(type(e).__name__)))
            return None

    def _get__all_job_data(self):
        """
        Get all registers from job_data.\n
        :return: row content: 
        :rtype: 23-tuple 
        """
        try:
            #conn = create_connection(path)
            if self.conn:
                self.conn.text_factory = str
                cur = self.conn.cursor()
                cur.execute(
                    "SELECT id, counter, job_name, created, modified, submit, start, finish, status, rowtype, ncpus, wallclock, qos, energy, date, section, member, chunk, last, platform, job_id, extra_data, nnodes, run_id FROM job_data")
                rows = cur.fetchall()
                return rows
            else:
                return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on Select : " + str(type(e).__name__))
            return list()

    def _get_job_data(self, job_name):
        """[summary]

        Args:
            job_name ([type]): [description]

        Returns:
            [type]: None if error, list of tuple if found (list can be empty)
        """
        try:
            if self.conn:
                self.conn.text_factory = str
                cur = self.conn.cursor()
                cur.execute(
                    "SELECT id, counter, job_name, created, modified, submit, start, finish, status, rowtype, ncpus, wallclock, qos, energy, date, section, member, chunk, last, platform, job_id, extra_data, nnodes, run_id FROM job_data WHERE job_name=? ORDER BY counter DESC", (job_name,))
                rows = cur.fetchall()
                # print(rows)
                return rows
            else:
                return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on Select : " + str(type(e).__name__))
            return None

    def _get_job_data_last(self, job_name):
        """Returns the latest row for a job_name. The current version.

        Args:
            job_name ([type]): [description]

        Returns:
            [type]: [description]
        """
        try:
            if self.conn:
                self.conn.text_factory = str
                cur = self.conn.cursor()
                cur.execute(
                    "SELECT id, counter, job_name, created, modified, submit, start, finish, status, rowtype, ncpus, wallclock, qos, energy, date, section, member, chunk, last, platform, job_id, extra_data, nnodes, run_id FROM job_data WHERE last=1 and job_name=? ORDER BY counter DESC", (job_name,))
                rows = cur.fetchall()
                if rows and len(rows) > 0:
                    return rows
                else:
                    return None
            else:
                return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on Select : " + str(type(e).__name__))
            return None

    def _get_job_data_pending(self):
        """
        Gets the list of job_id, job_name of those jobs that have pending information.  
        This function is no longer used.
        """
        try:
            if self.conn:
                self.conn.text_factory = str
                cur = self.conn.cursor()
                cur.execute(
                    "SELECT job_id, job_name, rowtype FROM job_data WHERE last=1 and platform='marenostrum4' and energy <= 0 and (status = 'COMPLETED' or status = 'FAILED')")
                rows = cur.fetchall()
                if rows and len(rows) > 0:
                    return rows
                else:
                    return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on historic database retrieval.")
            return None

    def _set_pragma_version(self, version=2):
        """Sets current version of the schema

        :param version: Current Version. Defaults to 1. 
        :type version: (int, optional)
        :return: current version, None 
        :rtype: (int, None)
        """
        try:
            if self.conn:
                self.conn.text_factory = str
                cur = self.conn.cursor()
                # print("Setting version")
                cur.execute("pragma user_version={v:d};".format(v=version))
                self.conn.commit()
                return True
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on version : " + str(type(e).__name__))
            return None

    def _select_pragma_version(self):
        """[summary]
        """
        try:
            if self.conn:
                self.conn.text_factory = str
                cur = self.conn.cursor()
                cur.execute("pragma user_version;")
                rows = cur.fetchall()
                if len(rows) > 0:
                    # print(rows)
                    #print("Row " + str(rows[0]))
                    result, = rows[0]
                    # print(result)
                    return int(result) if result >= 0 else None
                else:
                    # Starting value
                    return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error while retrieving version: " +
                        str(type(e).__name__))
            return None

    def _get_maxcounter_jobdata(self):
        """Return the maxcounter of the experiment

        Returns:
            [type]: [description]
        """
        try:
            if self.conn:
                self.conn.text_factory = str
                cur = self.conn.cursor()
                cur.execute("SELECT MAX(counter) as maxcounter FROM job_data")
                rows = cur.fetchall()
                if len(rows) > 0:
                    #print("Row " + str(rows[0]))
                    result, = rows[0]
                    return int(result) if result else 1
                else:
                    # Starting value
                    return 1
            return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on Select Max : " + str(type(e).__name__))
            return None

    def _get_max_id_experiment_run(self):
        """Return the max id from experiment_run

        :return: max run_id, None
        :rtype: int, None
        """
        try:
            if self.conn:
                self.conn.text_factory = str
                cur = self.conn.cursor()
                cur.execute(
                    "SELECT run_id,created,start,finish,chunk_unit,chunk_size,completed,total,failed,queuing,running,submitted from experiment_run ORDER BY run_id DESC LIMIT 0, 1")
                rows = cur.fetchall()
                if len(rows) > 0:
                    return rows[0]
                else:
                    return None
            return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.debug(traceback.format_exc())
            Log.warning("Error on select max run_id : " +
                        str(type(e).__name__))
            return None
