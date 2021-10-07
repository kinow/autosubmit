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
import traceback
from database_managers.experiment_history_db_manager import ExperimentHistoryDbManager, DEFAULT_JOBDATA_DIR
from database_managers.database_models import RowType
from data_classes.job_data import JobData
from logging import Logging

class ExperimentHistory():
  def __init__(self, expid, jobdata_dir_path=DEFAULT_JOBDATA_DIR):
    self.expid = expid
    self._log = Logging(expid)
    try:
      self.manager = ExperimentHistoryDbManager(self.expid, jobdata_dir_path=jobdata_dir_path)
      if os.path.exists(self.manager.historicaldb_file_path):
        self.manager.update_historical_database()
      else:
        self.manager.create_historical_database()
    except Exception as exp:
      self._log.log(str(exp), traceback.format_exc())
      self.manager = None

  
  def write_submit_time(self, job_name, submit=0, status="UNKNOWN", ncpus=0, wallclock="00:00", qos="debug", date="", member="", section="", chunk=0, platform="NA", job_id=0, packed=False, wrapper_queue=None, wrapper_code=None):
    try:
      next_counter = self._get_current_max_counter_by_job_name(job_name)
      job_data_dc = JobData(0, next_counter, job_name, None, None, submit, 0, 0, status, self.determine_rowtype(wrapper_code), ncpus, wallclock, queu)
    except Exception as exp:
      self._log.log(str(exp), traceback.format_exc())
  
  def _get_next_counter_by_job_name(self, job_name):
    job_data_row = self.manager.get_job_data_last_by_name(job_name)
    max_counter = self.manager.get_job_data_max_counter()
    if len(job_data_row) > 0:
      job_max_counter = max(job.counter for job in job_data_row)
      return max(max_counter, job_max_counter)
    else:
      return max_counter
  
  def determine_rowtype(self, code):  
    if code:
        return code
    else:
        return RowType.NORMAL
  
  def get_defined_queue_name(self, wrapper_queue, wrapper_code, qos):
    if wrapper_code and wrapper_code > 2 and wrapper_queue is not None:
      return wrapper_queue
    return qos 