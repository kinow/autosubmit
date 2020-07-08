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
from datetime import datetime
from networkx import DiGraph
from autosubmit.config.basicConfig import BasicConfig


class JobData():
    """Job Data object
    """

    def __init__(self, _id, counter=1, job_name="None", created=None, modified=None, submit=0, start=0, finish=0, status="UNKNOWN", rowtype=1, ncpus=0, wallclock="00:00", qos="debug", energy=0, date="", section="", member="", chunk=0, last=1):
        """[summary]

        Args:
            _id ([type]): [description]
            counter (int, optional): [description]. Defaults to 1.
            job_name (str, optional): [description]. Defaults to "None".
            created ([type], optional): [description]. Defaults to None.
            modified ([type], optional): [description]. Defaults to None.
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
        self.energy = energy
        self.date = date if date else ""
        self.section = section if section else ""
        self.member = member if member else ""
        self.chunk = chunk if chunk else 0
        self.last = last

    @property
    def submit(self):
        return int(self._submit)

    @property
    def start(self):
        return int(self._start)

    @property
    def finish(self):
        return int(self._finish)

    @submit.setter
    def submit(self, submit):
        self._submit = int(submit)

    @start.setter
    def start(self, start):
        self._start = int(start)

    @finish.setter
    def finish(self, finish):
        self._finish = int(finish)


class JobDataList():
    def __init__(self, expid):
        self.jobdata_list = list()
        self.expid = expid

    def add_jobdata(self, jobdata):
        self.jobdata_list.append(jobdata)

    def size(self):
        return len(self.jobdata_list)


class JobDataStructure():
    def __init__(self, expid):
        BasicConfig.read()
        self.expid = expid
        self.folder_path = BasicConfig.JOBDATA_DIR
        self.database_path = os.path.join(
            self.folder_path, "job_data_" + str(expid) + ".db")
        self.conn = None
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
            UNIQUE(counter,job_name)
            );''')
        if not os.path.exists(self.database_path):
            open(self.database_path, "w")
            self.conn = self.create_connection(self.database_path)
            self.create_table()
        else:
            self.conn = self.create_connection(self.database_path)

    def write_submit_time(self, job_name, submit=0, status="UNKNOWN", ncpus=0, wallclock="00:00", qos="debug", date="", member="", section="", chunk=0):
        """Write submit always generates a new record

        Args:
            job_name ([type]): [description]
            submit (int, optional): [description]. Defaults to 0.
            status (str, optional): [description]. Defaults to "UNKNOWN".
            ncpus (int, optional): [description]. Defaults to 0.
            wallclock (str, optional): [description]. Defaults to "00:00".
            qos (str, optional): [description]. Defaults to "debug".
        """
        #print("Saving write submit " + job_name)
        try:
            job_data = self.get_job_data(job_name)
            current_counter = max_counter = 1
            #submit = parse_date(submit) if submit > 0 else 0
            #print("submit job data " + str(job_data))
            if job_data and len(job_data) > 0:
                #print("job data has 1 element")
                max_counter = self._get_maxcounter_jobdata()
                job_max_counter = max(job.counter for job in job_data)
                current_last = [
                    job for job in job_data if job.counter == job_max_counter]

                # Deactivate current last for this job
                current_last[0].modified = datetime.today().strftime(
                    '%Y-%m-%d-%H:%M:%S')
                up_id = self._deactivate_current_last(current_last[0])
                # Finding current counter
                current_counter = (
                    job_max_counter + 1) if job_max_counter >= max_counter else max_counter + 1

            # Insert new last
            #print("Inserting new job data")
            rowid = self._insert_job_data(JobData(
                0, current_counter, job_name, None, None, submit, 0, 0, status, 1, ncpus, wallclock, qos, 0, date, member, section, chunk, 1))
            return True
        except Exception as exp:
            print(traceback.format_exc())
            print(exp)
            return None

        # if rowid > 0:
        #     print("Successfully inserted")

    def write_start_time(self, job_name, start=0, status="UNKWNONW", ncpus=0, wallclock="00:00", qos="debug", date="", member="", section="", chunk=0):
        """[summary]

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

        Returns:
            [type]: [description]
        """
        try:
            job_data_last = self.get_job_data_last(job_name)
            # Updating existing row
            if job_data_last:
                if job_data_last.start == 0:
                    job_data_last.start = start
                    job_data_last.modified = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
                    rowid = self._update_start_job_data(job_data_last)
                    return rowid
            # It is necessary to create a new row
            submit_inserted = self.write_submit_time(
                job_name, start, status, ncpus, wallclock, qos, date, member, section, chunk)
            if submit_inserted:
                self.write_start_time(job_name, start, status,
                                      ncpus, wallclock, qos, date, member, section, chunk)
            else:
                return None
        except Exception as exp:
            print(traceback.format_exc())
            print(exp)
            return None

    def write_finish_time(self, job_name, finish=0, status="UNKNOWN", ncpus=0, wallclock="00:00", qos="debug", date="", member="", section="", chunk=0):
        """Write finish time in database. If possible, calls Slurm to retrieve energy.

        Args:
            job_name ([type]): [description]
            finish (int, optional): [description]. Defaults to 0.
            status (str, optional): [description]. Defaults to "UNKNOWN".
            ncpus (int, optional): [description]. Defaults to 0.
            wallclock (str, optional): [description]. Defaults to "00:00".
            qos (str, optional): [description]. Defaults to "debug".
            date (str, optional): [description]. Defaults to "".
            member (str, optional): [description]. Defaults to "".
            section (str, optional): [description]. Defaults to "".
            chunk (int, optional): [description]. Defaults to 0.

        Returns:
            [type]: [description]
        """
        try:
            job_data_last = self.get_job_data_last(job_name)
            # Updating existing row
            if job_data_last:
                if job_data_last.finish == 0:
                    # Call Slurm here, update times.
                    job_data_last.finish = finish
                    job_data_last.status = status
                    job_data_last.modified = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
                    rowid = self._update_finish_job_data(job_data_last)
                    return True
            # It is necessary to create a new row
            submit_inserted = self.write_submit_time(
                job_name, finish, status, ncpus, wallclock, qos, date, member, section, chunk)
            write_inserted = self.write_start_time(job_name, finish, status, ncpus,
                                                   wallclock, qos, date, member, section, chunk)
            if submit_inserted and write_inserted:
                self.write_finish_time(
                    job_name, finish, status, ncpus, wallclock, qos, date, member, section, chunk)
            else:
                return None
        except Exception as exp:
            print(traceback.format_exc())
            print(exp)
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
                    _id, _counter, _job_name, _created, _modified, _submit, _start, _finish, _status, _rowtype, _ncpus, _wallclock, _qos, _energy, _date, _section, _member, _chunk, _last = item
                    self.jobdata_list.add_jobdata(JobData(_id, _counter, _job_name, _created, _modified,
                                                          _submit, _start, _finish, _status, _rowtype, _ncpus, _wallclock, _qos, _energy, _date, _section, _member, _chunk, _last))

            else:
                raise Exception("Job data folder not found :" +
                                str(self.jobdata_path))
        except Exception as exp:
            print(traceback.format_exc())
            print(exp)

    def get_job_data(self, job_name):
        try:
            job_data = list()
            if os.path.exists(self.folder_path):
                current_job = self._get_job_data(job_name)
                for item in current_job:
                    _id, _counter, _job_name, _created, _modified, _submit, _start, _finish, _status, _rowtype, _ncpus, _wallclock, _qos, _energy, _date, _section, _member, _chunk, _last = item
                    job_data.append(JobData(_id, _counter, _job_name, _created, _modified,
                                            _submit, _start, _finish, _status, _rowtype, _ncpus, _wallclock, _qos, _energy, _date, _section, _member, _chunk, _last))
                return job_data
            else:
                raise Exception("Job data folder not found :" +
                                str(self.jobdata_path))
        except Exception as exp:
            print(traceback.format_exc())
            print(exp)
            return None

    def get_job_data_last(self, job_name):
        """[summary]

        Args:
            job_name ([type]): [description]

        Raises:
            Exception: [description]

        Returns:
            [type]: [description]
        """
        try:
            if os.path.exists(self.folder_path):
                current_job_last = self._get_job_data_last(job_name)
                if current_job_last:
                    _id, _counter, _job_name, _created, _modified, _submit, _start, _finish, _status, _rowtype, _ncpus, _wallclock, _qos, _energy, _date, _section, _member, _chunk, _last = current_job_last
                    return JobData(_id, _counter, _job_name, _created, _modified,
                                   _submit, _start, _finish, _status, _rowtype, _ncpus, _wallclock, _qos, _energy, _date, _section, _member, _chunk, _last)
                else:
                    return None
            else:
                raise Exception("Job data folder not found :" +
                                str(self.jobdata_path))
        except Exception as exp:
            print(traceback.format_exc())
            print(exp)
            return None

    def _deactivate_current_last(self, jobdata):
        try:
            sql = ''' UPDATE job_data SET last=0, modified = ? WHERE id = ?'''
            tuplerow = (jobdata.modified, jobdata._id)
            cur = self.conn.cursor()
            cur.execute(sql, tuplerow)
            self.conn.commit()
            return cur.lastrowid
        except Exception as exp:
            print(traceback.format_exc())
            print("Error on Update : " + str(type(e).__name__))
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
            sql = ''' UPDATE job_data SET start=?, modified=? WHERE id=? '''
            cur = self.conn.cursor()
            cur.execute(sql, (int(jobdata.start),
                              jobdata.modified, jobdata._id))
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            print(traceback.format_exc())
            print("Error on Insert : " + str(type(e).__name__))
            return None

    def _update_finish_job_data(self, jobdata):
        try:
            sql = ''' UPDATE job_data SET finish=?, modified=?, status=? WHERE id=? '''
            cur = self.conn.cursor()
            cur.execute(sql, (jobdata.finish, jobdata.modified,
                              jobdata.status, jobdata._id))
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            print(traceback.format_exc())
            print("Error on Insert : " + str(type(e).__name__))
            return None

    def _insert_job_data(self, jobdata):
        """[summary]
        """
        try:
            if self.conn:
                #print("preparing to insert")
                sql = ''' INSERT INTO job_data(counter, job_name, created, modified, submit, start, finish, status, rowtype, ncpus, wallclock, qos, energy, date, section, member, chunk, last) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
                tuplerow = (jobdata.counter, jobdata.job_name, jobdata.created, jobdata.modified, jobdata.submit, jobdata.start,
                            jobdata.finish, jobdata.status, jobdata.rowtype, jobdata.ncpus, jobdata.wallclock, jobdata.qos, jobdata.energy, jobdata.date, jobdata.section, jobdata.member, jobdata.chunk, jobdata.last)
                cur = self.conn.cursor()
                #print("pre insert")
                cur.execute(sql, tuplerow)
                self.conn.commit()
                #print("Inserted " + str(jobdata.job_name))
                return cur.lastrowid
            else:
                print("Not a valid connection.")
                return None
        except sqlite3.Error as e:
            print(traceback.format_exc())
            print("Error on Insert : " + str(type(e).__name__))
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
                    "SELECT id, counter, job_name, created, modified, submit, start, finish, status, rowtype, ncpus, wallclock, qos, energy, date, section, member, chunk, last FROM job_data")
                rows = cur.fetchall()
                return rows
            else:
                raise Exception("Not a valid connection")
        except Exception as exp:
            print(traceback.format_exc())
            return list()

    def _get_job_data(self, job_name):
        """[summary]
        """
        try:
            if self.conn:
                self.conn.text_factory = str
                cur = self.conn.cursor()
                cur.execute(
                    "SELECT id, counter, job_name, created, modified, submit, start, finish, status, rowtype, ncpus, wallclock, qos, energy, date, section, member, chunk, last FROM job_data WHERE job_name=?", (job_name,))
                rows = cur.fetchall()
                # print(rows)
                return rows
            else:
                raise Exception("Not a valid connection")
        except Exception as exp:
            print(traceback.format_exc())
            return None

    def _get_job_data_last(self, job_name):
        try:
            if self.conn:
                self.conn.text_factory = str
                cur = self.conn.cursor()
                cur.execute(
                    "SELECT id, counter, job_name, created, modified, submit, start, finish, status, rowtype, ncpus, wallclock, qos, energy, date, section, member, chunk, last FROM job_data WHERE last=1 and job_name=?", (job_name,))
                rows = cur.fetchall()
                if rows and len(rows) > 0:
                    return rows[0]
                else:
                    return None
            else:
                raise Exception("Not a valid connection")
        except Exception as exp:
            print(traceback.format_exc())
            return None

    def _get_maxcounter_jobdata(self):
        """[summary]

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
                    return int(result)
                else:
                    return None
        except Exception as exp:
            print(traceback.format_exc())
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
                raise Exception("Not a valid connection")
        except Exception as e:
            print(e)

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
