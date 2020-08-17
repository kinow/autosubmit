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
from bscearth.utils.date import date2str, parse_date, previous_day, chunk_end_date, chunk_start_date, Log, subs_dates


CURRENT_DB_VERSION = 10
_debug = True
JobItem = collections.namedtuple('JobItem', ['id', 'counter', 'job_name', 'created', 'modified', 'submit', 'start', 'finish',
                                             'status', 'rowtype', 'ncpus', 'wallclock', 'qos', 'energy', 'date', 'section', 'member', 'chunk', 'last', 'platform', 'job_id', 'extra_data'])

ExperimentRow = collections.namedtuple(
    'ExperimentRow', ['exp_id', 'expid', 'status', 'seconds'])


class JobData():
    """Job Data object
    """

    def __init__(self, _id, counter=1, job_name="None", created=None, modified=None, submit=0, start=0, finish=0, status="UNKNOWN", rowtype=1, ncpus=0, wallclock="00:00", qos="debug", energy=0, date="", section="", member="", chunk=0, last=1, platform="NA", job_id=0, extra_data=dict()):
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

    def create_table(self):
        """ create a table from the create_table_sql statement
        :param conn: Connection object
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        try:
            if self.conn:
                c = self.conn.cursor()
                c.execute(self.create_table_query)
            else:
                raise IOError("Not a valid connection")
        except IOError as exp:
            Log.warning(exp)
            return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.warning("Error on create table : " + str(type(e).__name__))
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
            Log.warning(exp)
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
            print(traceback.format_exc())
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
            Log.warning("Error on Insert : " + str(type(e).__name__))

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
            Log.warning("Error while trying to update " +
                        str(expid) + " in experiment_status.")
            Log.warning(traceback.format_exc())
            Log.warning("Error on Update: " + str(type(e).__name__))
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
        self.folder_path = BasicConfig.JOBDATA_DIR
        self.database_path = os.path.join(
            self.folder_path, "job_data_" + str(expid) + ".db")
        #self.conn = None
        self.jobdata_list = JobDataList(self.expid)
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
            UNIQUE(counter,job_name)
            );
            ''')
        if not os.path.exists(self.database_path):
            open(self.database_path, "w")
            self.conn = self.create_connection(self.database_path)
            self.create_table()
            if self._set_pragma_version(CURRENT_DB_VERSION):
                Log.info("Database version set.")
        else:
            self.conn = self.create_connection(self.database_path)

    def write_submit_time(self, job_name, submit=0, status="UNKNOWN", ncpus=0, wallclock="00:00", qos="debug", date="", member="", section="", chunk=0, platform="NA", job_id=0):
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
        #print("Saving write submit " + job_name)
        try:
            job_data = self.get_job_data(job_name)
            current_counter = 1
            max_counter = self._get_maxcounter_jobdata()
            #submit = parse_date(submit) if submit > 0 else 0
            #print("submit job data " + str(job_data))
            if job_data and len(job_data) > 0:
                # print("job data has 1 element")
                # max_counter = self._get_maxcounter_jobdata()
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
                0, current_counter, job_name, None, None, submit, 0, 0, status, 1, ncpus, wallclock, qos, 0, date, member, section, chunk, 1, platform, job_id))
            # print(rowid)
            if rowid:
                return True
            else:
                return None
        except Exception as exp:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.warning(str(exp))
            return None

        # if rowid > 0:
        #     print("Successfully inserted")

    def write_start_time(self, job_name, start=0, status="UNKWNONW", ncpus=0, wallclock="00:00", qos="debug", date="", member="", section="", chunk=0, platform="NA", job_id=0):
        """Writes start time into the database

        Args:
            job_name (str): Name of Job
            start (int, optional): Start time. Defaults to 0.
            status (str, optional): Status of job. Defaults to "UNKWNONW".
            ncpus (int, optional): Number of cpis. Defaults to 0.
            wallclock (str, optional): Wallclock value. Defaults to "00:00".
            qos (str, optional): Name of QoS. Defaults to "debug".
            date (str, optional): Date from config. Defaults to "".
            member (str, optional): Member from config. Defaults to "".
            section (str, optional): [description]. Defaults to "".
            chunk (int, optional): [description]. Defaults to 0.
            platform (str, optional): [description]. Defaults to "NA".
            job_id (int, optional): [description]. Defaults to 0.

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
                job_name, start, status, ncpus, wallclock, qos, date, member, section, chunk, platform, job_id)
            if submit_inserted:
                # print("retro start")
                self.write_start_time(job_name, start, status,
                                      ncpus, wallclock, qos, date, member, section, chunk, platform, job_id)
                return True
            else:
                return None
        except Exception as exp:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.warning(str(exp))
            return None

    def write_finish_time(self, job_name, finish=0, status="UNKNOWN", ncpus=0, wallclock="00:00", qos="debug", date="", member="", section="", chunk=0, platform="NA", job_id=0, platform_object=None):
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
            energy = 0
            submit_time = start_time = finish_time = 0
            extra_data = dict()
            # Updating existing row
            if job_data_last:
                job_data_last = job_data_last[0]
                # if job_data_last.finish == 0:
                # Call Slurm here, update times.
                if platform_object:
                    # print("There is platform object")
                    try:
                        if type(platform_object) is not str:
                            if platform_object.type == "slurm":
                                #print("Checking Slurm for " + str(job_name))
                                submit_time, start_time, finish_time, energy, extra_data = platform_object.check_job_energy(
                                    job_id)
                    except Exception as exp:
                        Log.info(traceback.format_exc())
                        Log.warning(str(exp))
                        energy = 0
                job_data_last.finish = int(
                    finish_time) if finish_time > 0 else int(finish)
                job_data_last.status = status
                job_data_last.job_id = job_id
                job_data_last.energy = energy
                job_data_last.extra_data = dumps(extra_data)
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
                job_name, finish, status, ncpus, wallclock, qos, date, member, section, chunk, platform, job_id)
            write_inserted = self.write_start_time(job_name, finish, status, ncpus,
                                                   wallclock, qos, date, member, section, chunk, platform, job_id)
            # print(submit_inserted)
            # print(write_inserted)
            if submit_inserted and write_inserted:
                #print("retro finish")
                self.write_finish_time(
                    job_name, finish, status, ncpus, wallclock, qos, date, member, section, chunk, platform, job_id, platform_object)
            else:
                return None
        except Exception as exp:
            if _debug == True:
                Log.info(traceback.format_exc())
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
                                                          job_item.rowtype, job_item.ncpus, job_item.wallclock, job_item.qos, job_item.energy, job_item.date, job_item.section, job_item.member, job_item.chunk, job_item.last, job_item.platform, job_item.job_id, job_item.extra_data))

            else:
                raise Exception("Job data folder not found :" +
                                str(self.jobdata_path))
        except Exception as exp:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.warning(str(exp))
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
                    # _id, _counter, _job_name, _created, _modified, _submit, _start, _finish, _status, _rowtype, _ncpus, _wallclock, _qos, _energy, _date, _section, _member, _chunk, _last, _platform = item
                    job_item = JobItem(*item)
                    job_data.append(JobData(job_item.id, job_item.counter, job_item.job_name, job_item.created, job_item.modified, job_item.submit, job_item.start, job_item.finish, job_item.status,
                                            job_item.rowtype, job_item.ncpus, job_item.wallclock, job_item.qos, job_item.energy, job_item.date, job_item.section, job_item.member, job_item.chunk, job_item.last, job_item.platform, job_item.job_id, job_item.extra_data))
                    # job_data.append(JobData(_id, _counter, _job_name, _created, _modified,
                    #                         _submit, _start, _finish, _status, _rowtype, _ncpus, _wallclock, _qos, _energy, _date, _section, _member, _chunk, _last, _platform))
                return job_data
            else:
                raise Exception("Job data folder not found :" +
                                str(self.jobdata_path))
        except Exception as exp:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.warning(str(exp))
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
                        # _id, _counter, _job_name, _created, _modified, _submit, _start, _finish, _status, _rowtype, _ncpus, _wallclock, _qos, _energy, _date, _section, _member, _chunk, _last, _platform = current_job_last
                        # return JobData(_id, _counter, _job_name, _created, _modified,
                        #                _submit, _start, _finish, _status, _rowtype, _ncpus, _wallclock, _qos, _energy, _date, _section, _member, _chunk, _last, _platform)
                        jobdata.append(JobData(job_item.id, job_item.counter, job_item.job_name, job_item.created, job_item.modified, job_item.submit, job_item.start, job_item.finish, job_item.status,
                                               job_item.rowtype, job_item.ncpus, job_item.wallclock, job_item.qos, job_item.energy, job_item.date, job_item.section, job_item.member, job_item.chunk, job_item.last, job_item.platform, job_item.job_id, job_item.extra_data))
                    return jobdata
                else:
                    return None
            else:
                raise Exception("Job data folder not found :" +
                                str(self.jobdata_path))
        except Exception as exp:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.warning(str(exp))
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
            Log.warning("Error on Insert : " + str(type(e).__name__))
            return None

    def _update_start_job_data(self, jobdata):
        """Update start time of job data row

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
            Log.warning("Error on Insert : " + str(type(e).__name__))
            return None

    def _update_finish_job_data_plus(self, jobdata):
        """Updates the finish job data, also updates submit, start times.

        Args:
            jobdata (JobData): JobData object

        Returns:
            int/None: lastrowid if success, None if error
        """
        try:
            if self.conn:
                sql = ''' UPDATE job_data SET submit=?, start=?, finish=?, modified=?, job_id=?, status=?, energy=?, extra_data=? WHERE id=? '''
                cur = self.conn.cursor()
                cur.execute(sql, (jobdata.submit, jobdata.start, jobdata.finish, jobdata.modified, jobdata.job_id,
                                  jobdata.status, jobdata.energy, jobdata.extra_data, jobdata._id))
                self.conn.commit()
                return cur.lastrowid
            return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.warning("Error on Update : " + str(type(e).__name__))
            return None

    def _update_finish_job_data(self, jobdata):
        """Update register with id. Updates finish, modified, status.

        Args:
            jobdata ([type]): [description]

        Returns:
            [type]: None if error, lastrowid if success
        """
        try:
            if self.conn:
                # print("Updating finish time")
                sql = ''' UPDATE job_data SET finish=?, modified=?, job_id=?, status=?, energy=?, extra_data=? WHERE id=? '''
                cur = self.conn.cursor()
                cur.execute(sql, (jobdata.finish, jobdata.modified, jobdata.job_id,
                                  jobdata.status, jobdata.energy, jobdata.extra_data, jobdata._id))
                self.conn.commit()
                return cur.lastrowid
            return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.warning("Error on Update : " + str(type(e).__name__))
            return None

    def _insert_job_data(self, jobdata):
        """[summary]

        Args:
            jobdata ([type]): JobData object

        Returns:
            [type]: None if error, lastrowid if correct
        """
        try:
            if self.conn:
                #print("preparing to insert")
                sql = ''' INSERT INTO job_data(counter, job_name, created, modified, submit, start, finish, status, rowtype, ncpus, wallclock, qos, energy, date, section, member, chunk, last, platform, job_id, extra_data) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
                tuplerow = (jobdata.counter, jobdata.job_name, jobdata.created, jobdata.modified, jobdata.submit, jobdata.start,
                            jobdata.finish, jobdata.status, jobdata.rowtype, jobdata.ncpus, jobdata.wallclock, jobdata.qos, jobdata.energy, jobdata.date, jobdata.section, jobdata.member, jobdata.chunk, jobdata.last, jobdata.platform, jobdata.job_id, jobdata.extra_data)
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
            Log.warning("Error on Insert : " + str(type(e).__name__) +
                        "\t " + str(jobdata.job_name) + "\t" + str(jobdata.counter))
            return None

    def _get__all_job_data(self):
        """
        Get all registers from job_data.\n
        :return: row content: exp_id, name, status, seconds_diff  
        :rtype: 4-tuple (int, str, str, int)
        """
        try:
            #conn = create_connection(path)
            if self.conn:
                self.conn.text_factory = str
                cur = self.conn.cursor()
                cur.execute(
                    "SELECT id, counter, job_name, created, modified, submit, start, finish, status, rowtype, ncpus, wallclock, qos, energy, date, section, member, chunk, last, platform, job_id, extra_data FROM job_data")
                rows = cur.fetchall()
                return rows
            else:
                return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
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
                    "SELECT id, counter, job_name, created, modified, submit, start, finish, status, rowtype, ncpus, wallclock, qos, energy, date, section, member, chunk, last, platform, job_id, extra_data FROM job_data WHERE job_name=? ORDER BY counter DESC", (job_name,))
                rows = cur.fetchall()
                # print(rows)
                return rows
            else:
                return None
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
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
                    "SELECT id, counter, job_name, created, modified, submit, start, finish, status, rowtype, ncpus, wallclock, qos, energy, date, section, member, chunk, last, platform, job_id, extra_data FROM job_data WHERE last=1 and job_name=? ORDER BY counter DESC", (job_name,))
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
            Log.warning("Error on Select : " + str(type(e).__name__))
            return None

    def _set_pragma_version(self, version=2):
        """Sets current version of the schema

        Args:
            version (int, optional): Current Version. Defaults to 1.

        Returns:
            Boolean/None: True if success, None if error
        """
        try:
            if self.conn:
                self.conn.text_factory = str
                cur = self.conn.cursor()
                cur.execute("pragma user_version={v:d}".format(v=version))
                self.conn.commit()
                return True
        except sqlite3.Error as e:
            if _debug == True:
                Log.info(traceback.format_exc())
            Log.warning("Error on version : " + str(type(e).__name__))
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
            Log.warning("Error on Select Max : " + str(type(e).__name__))
            return None
