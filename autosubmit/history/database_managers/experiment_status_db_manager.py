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

import os
import sqlite3
import traceback
import textwrap
import time
from database_manager import DatabaseManager
import autosubmit.history.utils as HUtils
import database_models as Models

class ExperimentStatusDbManager(DatabaseManager):
  """ Manages the actions on the status database """
  def __init__(self, expid):
      super(ExperimentStatusDbManager, self).__init__(expid)
      self._as_times_file_path = os.path.join(self._basic_configuration.LOCAL_ROOT_DIR, self.AS_TIMES_DB_NAME)
      self._ecearth_file_path = os.path.join(self._basic_configuration.LOCAL_ROOT_DIR, self.ECEARTH_DB_NAME)
      self._pkl_file_path = os.path.join(self._basic_configuration.LOCAL_ROOT_DIR, "pkl", "job_list_{0}.pkl".format(self.expid))
      self._validate_status_database()
      self.current_experiment_row = self._get_current_experiment_row(self.expid)
      self.current_experiment_status_row =self._get_current_experiment_status_row(self.current_experiment_row.id)

  def _validate_status_database(self):
      """ Creates experiment_status table if it does not exist """        
      create_table_query = textwrap.dedent(
          '''CREATE TABLE
              IF NOT EXISTS experiment_status (
              exp_id integer PRIMARY KEY,
              name text NOT NULL,
              status text NOT NULL,
              seconds_diff integer NOT NULL,
              modified text NOT NULL,
              FOREIGN KEY (exp_id) REFERENCES experiment (id)
          );'''
      )
      self.execute_statement_on_dbfile(self._as_times_file_path, create_table_query)
 
  def print_current_table(self):
      for experiment in self._get_experiment_status_content():
          print(experiment)
      if self.current_experiment_status_row:
          print("Current Row:\n\t" + self.current_experiment_status_row.name + "\n\t" +
                str(self.current_experiment_status_row.exp_id) + "\n\t" + self.current_experiment_status_row.status)

  def is_running(self, time_condition=600):
      # type : (int) -> bool
      """ True if experiment is running, False otherwise. """
      if (os.path.exists(self._pkl_file_path)):
          current_stat = os.stat(self._pkl_file_path)
          timest = int(current_stat.st_mtime)
          timesys = int(time.time())
          time_diff = int(timesys - timest)
          if (time_diff < time_condition):
              return True
          else:
              return False
      return False
  
  def set_experiment_as_running(self, status="RUNNING"):
    if self.current_experiment_status_row:
        # Row exists         
        self._update_exp_status(status)
    else:
        # New Row          
        self._create_exp_status()

  def _get_current_experiment_row(self, expid):
    # type : (str) -> Models.ExperimentRow
    """
    Get the experiment from ecearth.db by expid as Models.ExperimentRow.      
    """
    statement = self.get_built_select_statement("experiment", "name=?")
    current_rows = self.get_from_statement_with_arguments(self._ecearth_file_path, statement, (expid,))
    if len(current_rows) <= 0:      
      raise ValueError("Experiment {0} not found in {1}".format(expid, self._ecearth_file_path))
    return Models.ExperimentRow(*current_rows[0])

  def _get_experiment_status_content(self):
    # type : () -> List[Models.ExperimentStatusRow]
    """
    Get all registers from experiment_status as List of Models.ExperimentStatusRow.\n
    """
    statement = self.get_built_select_statement("experiment_status")
    current_rows = self.get_from_statement(self._as_times_file_path, statement)
    return [Models.ExperimentStatusRow(*row) for row in current_rows]

  def _get_current_experiment_status_row(self, exp_id):
    # type : (int) -> Models.ExperimentStatusRow
    """ Get Models.ExperimentStatusRow from as_times.db by exp_id (int)"""
    statement = self.get_built_select_statement("experiment_status", "exp_id=?")
    arguments = (exp_id,)
    current_rows = self.get_from_statement_with_arguments(self._as_times_file_path, statement, arguments)
    if len(current_rows) <= 0:
      return None
    return Models.ExperimentStatusRow(*current_rows[0])


  def _create_exp_status(self):
    # type : () -> None
    """
    Create experiment status        
    """
    statement = ''' INSERT INTO experiment_status(exp_id, name, status, seconds_diff, modified) VALUES(?,?,?,?,?) '''
    arguments = (self.current_experiment_row.id, self.expid, Models.RunningStatus.RUNNING, 0, HUtils.get_current_datetime())
    return self.insert_statement_with_arguments(self._as_times_file_path, statement, arguments)

  def _update_exp_status(self, status="RUNNING"):
    # type : (str) -> None
    """
    Update status, seconds_diff, modified in experiment_status.        
    """
    statement = ''' UPDATE experiment_status SET status = ?, seconds_diff = ?, modified = ? WHERE name = ? '''
    arguments = (status, 0, HUtils.get_current_datetime(), self.current_experiment_row.name)
    self.execute_statement_with_arguments_on_dbfile(self._as_times_file_path, statement, arguments)        


# if __name__ == "__main__":
#   exp = ExperimentStatusDbManager("a2h6")
#   exp.set_experiment_as_running()
#   exp.print_current_table()