#!/usr/bin/env python

# Copyright 2015-2020 Earth Sciences Department, BSC-CNS
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
import sqlite3
import os
import traceback
import textwrap
import autosubmit.history.utils as HUtils
import database_models as Models
from abc import ABCMeta, abstractmethod
from database_manager import DatabaseManager, DEFAULT_JOBDATA_DIR
from datetime import datetime

CURRENT_DB_VERSION = 16
DB_EXPERIMENT_HEADER_SCHEMA_CHANGES = 14
DB_VERSION_SCHEMA_CHANGES = 12
DEFAULT_DB_VERSION = 10
DEFAULT_MAX_COUNTER = 0

class ExperimentHistoryDbManager(DatabaseManager):
  """ Manages actions directly on the database.  
  """
  def __init__(self, expid, jobdata_dir_path=DEFAULT_JOBDATA_DIR):
    """ Requires expid and jobdata_dir_path. """
    super(ExperimentHistoryDbManager, self).__init__(expid, jobdata_dir_path=jobdata_dir_path)
    self.db_version = DEFAULT_DB_VERSION # type : int
    self._set_schema_changes()
    self._set_table_queries()    
    self.historicaldb_file_path = os.path.join(self.JOBDATA_DIR, "job_data_{0}.db".format(self.expid)) # type : str
    
  def _set_table_queries(self):
    """ Sets basic table queries. """
    self.create_table_header_query = textwrap.dedent(
      '''CREATE TABLE 
      IF NOT EXISTS experiment_run (
      run_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
      created TEXT NOT NULL,
      modified TEXT NOT NULL,
      start INTEGER NOT NULL,
      finish INTEGER,
      chunk_unit TEXT NOT NULL,
      chunk_size INTEGER NOT NULL,
      completed INTEGER NOT NULL,
      total INTEGER NOT NULL,
      failed INTEGER NOT NULL,
      queuing INTEGER NOT NULL,
      running INTEGER NOT NULL,
      submitted INTEGER NOT NULL,
      suspended INTEGER NOT NULL DEFAULT 0,
      metadata TEXT
      );
      ''')
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
      MaxRSS REAL NOT NULL DEFAULT 0.0,
      AveRSS REAL NOT NULL DEFAULT 0.0,
      out TEXT NOT NULL,
      err TEXT NOT NULL,
      rowstatus INTEGER NOT NULL DEFAULT 0,
      UNIQUE(counter,job_name)
      );
      ''')
    self.create_index_query = textwrap.dedent(''' 
      CREATE INDEX IF NOT EXISTS ID_JOB_NAME ON job_data(job_name);
      ''')

  def _set_schema_changes(self):
    # type : () -> None
    """ Creates the list of schema changes"""
    self.version_schema_changes = [
      "ALTER TABLE job_data ADD COLUMN nnodes INTEGER NOT NULL DEFAULT 0",
      "ALTER TABLE job_data ADD COLUMN run_id INTEGER"      
    ]
    # Version 15
    self.version_schema_changes.extend([
      "ALTER TABLE job_data ADD COLUMN MaxRSS REAL NOT NULL DEFAULT 0.0",
      "ALTER TABLE job_data ADD COLUMN AveRSS REAL NOT NULL DEFAULT 0.0",
      "ALTER TABLE job_data ADD COLUMN out TEXT NOT NULL DEFAULT ''",
      "ALTER TABLE job_data ADD COLUMN err TEXT NOT NULL DEFAULT ''",
      "ALTER TABLE job_data ADD COLUMN rowstatus INTEGER NOT NULL DEFAULT 0",
      "ALTER TABLE experiment_run ADD COLUMN suspended INTEGER NOT NULL DEFAULT 0",
      "ALTER TABLE experiment_run ADD COLUMN metadata TEXT"
    ])  
    # Version 16
    self.version_schema_changes.extend([
      "ALTER TABLE experiment_run ADD COLUMN modified TEXT"
    ])
  
  def create_historical_database(self):
    """ Creates the historical database with the latest changes. """
    self.execute_statement_on_dbfile(self.historicaldb_file_path, self.create_table_header_query)
    self.execute_statement_on_dbfile(self.historicaldb_file_path, self.create_table_query)
    self.execute_statement_on_dbfile(self.historicaldb_file_path, self.create_index_query)
    self._set_historical_pragma_version(CURRENT_DB_VERSION)
    self.db_version = CURRENT_DB_VERSION
  
  def update_historical_database(self):
    """ Updates the historical database with the latest changes IF necessary. """
    if self._get_pragma_version() == CURRENT_DB_VERSION:
      self.execute_many_statements_on_dbfile(self.historicaldb_file_path, self.version_schema_changes)
      self.execute_statement_on_dbfile(self.historicaldb_file_path, self.create_index_query)
      self.execute_statement_on_dbfile(self.historicaldb_file_path, self.create_table_header_query)
      self._set_historical_pragma_version(CURRENT_DB_VERSION)
      self.db_version = CURRENT_DB_VERSION

  def get_experiment_run_with_max_id(self):
    """ Get Models.ExperimentRunRow for the maximum id run. """
    statement = self.get_built_select_statement("experiment_run", "run_id > 0 ORDER BY run_id DESC LIMIT 0, 1")
    max_experiment_run = self.get_from_statement(self.historicaldb_file_path, statement)
    if len(max_experiment_run) <= 0:
      raise Exception("Error on experiment run retrieval")
    return Models.ExperimentRunRow(*max_experiment_run[0])

  def get_job_data_all(self):
    """ Gets List of Models.JobDataRow from database. """
    statement = self.get_built_select_statement("job_data")
    job_data_rows = self.get_from_statement(self.historicaldb_file_path, statement)
    return [Models.JobDataRow(*row) for row in job_data_rows]

  def update_many_job_data_change_status(self, changes):
    # type : (List[Tuple]) -> None
    """ 
    Update many job_data rows in bulk. Requires a changes list of argument tuples. 
    Only updates finish, modified, status, and rowstatus by id.
    """
    statement = ''' UPDATE job_data SET finish=?, modified=?, status=?, rowstatus=? WHERE id=? '''
    self.execute_many_statement_with_arguments_on_dbfile(self.historicaldb_file_path, statement, changes)

  def update_job_data_by_id(self, job_data):
    """
    Update job_data table with data class JobData.  
    Update finish, modified, job_id, status, energy, extra_data, nnodes, ncpus, rowstatus, out, err by id.
    """
    statement = ''' UPDATE job_data SET last=?, submit=?, start=?, finish=?, modified=?, job_id=?, status=?, energy=?, extra_data=?, nnodes=?, ncpus=?, rowstatus=?, out=?, err=? WHERE id=? '''
    arguments = (job_data.last, job_data.submit, job_data.start, job_data.finish, HUtils.get_current_datetime(), job_data.job_id, job_data.status, job_data.energy, job_data.extra_data, job_data.nnodes, job_data.ncpus, job_data.rowstatus, job_data.out, job_data.err, job_data._id)
    self.execute_statement_with_arguments_on_dbfile(self.historicaldb_file_path, statement, arguments)


  def update_experiment_run(self, experiment_run):
    """ 
    Update experiment_run table with data class ExperimentRun.  
    Updates by run_id (finish, chunk_unit, chunk_size, completed, total, failed, queuing, running, submitted, suspended) 
    """
    statement = ''' UPDATE experiment_run SET finish=?, chunk_unit=?, chunk_size=?, completed=?, total=?, failed=?, queuing=?, running=?, submitted=?, suspended=?, modified=? WHERE run_id=? '''
    arguments = (experiment_run.finish, experiment_run.chunk_unit, experiment_run.chunk_size, experiment_run.completed, experiment_run.total, experiment_run.failed, experiment_run.queuing, experiment_run.running, experiment_run.submitted, experiment_run.suspended, HUtils.get_current_datetime(), experiment_run.run_id)
    self.execute_statement_with_arguments_on_dbfile(self.historicaldb_file_path, statement, arguments)

  def insert_job_data(self, job_data):
    # type : (JobData) -> int
    """ Insert data class JobData into database """
    statement = ''' INSERT INTO job_data(counter, job_name, created, modified, submit, start, finish, status, rowtype, ncpus, wallclock, qos, energy, date, section, member, chunk, last, platform, job_id, extra_data, nnodes, run_id, MaxRSS, AveRSS, out, err, rowstatus) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
    arguments = (job_data.counter, job_data.job_name, HUtils.get_current_datetime(), HUtils.get_current_datetime(), job_data.submit, job_data.start, job_data.finish, job_data.status, job_data.rowtype, job_data.ncpus, job_data.wallclock, job_data.qos, job_data.energy, job_data.date, job_data.section, job_data.member, job_data.chunk, job_data.last, job_data.platform, job_data.job_id, job_data.extra_data, job_data.nnodes, job_data.run_id, job_data.MaxRSS, job_data.AveRSS, job_data.out, job_data.err, job_data.rowstatus)    
    return self.insert_statement_with_arguments(self.historicaldb_file_path, statement, arguments)

  def insert_experiment_run(self, experiment_run):
    """ Insert data class ExperimentRun into database """
    statement = ''' INSERT INTO experiment_run(created, modified, start, finish, chunk_unit, chunk_size, completed, total, failed, queuing, running, submitted, suspended, metadata) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
    arguments = (HUtils.get_current_datetime(), HUtils.get_current_datetime(), experiment_run.start, experiment_run.finish, experiment_run.chunk_unit, experiment_run.chunk_size, experiment_run.completed,
    experiment_run.total, experiment_run.failed, experiment_run.queuing, experiment_run.running, experiment_run.submitted, experiment_run.suspended, experiment_run.metadata)
    return self.insert_statement_with_arguments(self.historicaldb_file_path, statement, arguments)

  def get_job_data_last_by_run_id_and_finished(self, run_id):
    """ Get List of Models.JobDataRow for last=1, finished > 0 and run_id   """
    statement = self.get_built_select_statement("job_data", "run_id=? and last=1 and finish > 0 and rowtype >= 2 ORDER BY id")
    arguments = (run_id,)
    job_data_rows = self.get_from_statement_with_arguments(self.historicaldb_file_path, statement, arguments)
    return [Models.JobDataRow(*row) for row in job_data_rows]

  def get_job_data_last_by_run_id(self, run_id):
    """ Get List of Models.JobDataRow for last=1 and run_id """
    statement = self.get_built_select_statement("job_data", "run_id=? and last=1 and rowtype >= 2 ORDER BY id")    
    arguments = (run_id,)
    job_data_rows = self.get_from_statement_with_arguments(self.historicaldb_file_path, statement, arguments)
    return [Models.JobDataRow(*row) for row in job_data_rows]

  def get_job_data_by_name(self, job_name):
    """ Get List of Models.JobDataRow for job_name """
    statement = self.get_built_select_statement("job_data", "job_name=? ORDER BY counter DESC")
    arguments = (job_name,)
    job_data_rows = self.get_from_statement_with_arguments(self.historicaldb_file_path, statement, arguments)
    return [Models.JobDataRow(*row) for row in job_data_rows]

  def get_job_data_last_by_name(self, job_name):
    """ Get List of Models.JobDataRow for job_name and last=1 """
    statement = self.get_built_select_statement("job_data", "last=1 and job_name=? ORDER BY counter DESC")
    arguments = (job_name,)
    job_data_rows_last = self.get_from_statement_with_arguments(self.historicaldb_file_path, statement, arguments)
    return [Models.JobDataRow(*row) for row in job_data_rows_last]

  def get_job_data_max_counter(self):
    statement = "SELECT MAX(counter) as maxcounter FROM job_data"
    counter_result = self.get_from_statement(self.historicaldb_file_path, statement)
    if len(counter_result) <= 0:
      return DEFAULT_MAX_COUNTER
    else:      
      max_counter = Models.MaxCounterRow(*counter_result[0]).maxcounter
      return max_counter if max_counter else DEFAULT_MAX_COUNTER

  def delete_job_data(self, _id):
    """ Deletes row in job_data by id. Useful for testing. """
    statement = ''' DELETE FROM job_data WHERE id=? '''
    arguments = (_id, )
    self.execute_statement_with_arguments_on_dbfile(self.historicaldb_file_path, statement, arguments)
  
  def delete_experiment_run(self, run_id):
    """ Deletes row in experiment_run by run_id. Useful for testing. """
    statement = ''' DELETE FROM experiment_run where run_id=? '''
    arguments = (run_id,)
    self.execute_statement_with_arguments_on_dbfile(self.historicaldb_file_path, statement, arguments)

  def _set_historical_pragma_version(self, version=10):
    """ Sets the pragma version. """
    statement = "pragma user_version={v:d};".format(v=version)
    self.execute_statement_on_dbfile(self.historicaldb_file_path, statement)

  def _get_pragma_version(self):
    """ Gets current pragma version as int. """
    statement = "pragma user_version;"
    pragma_result = self.get_from_statement(self.historicaldb_file_path, statement)
    if len(pragma_result) <= 0:
      raise Exception("Error while getting the pragma version. This might be a signal of a deeper problem. Review previous errors.")    
    return Models.PragmaVersion(*pragma_result[0]).version
