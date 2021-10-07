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
import slurm_parser as SlurmParser
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

  
  def write_submit_time(self, job_name, submit=0, status="UNKNOWN", ncpus=0, wallclock="00:00", qos="debug", date="", member="", section="", chunk=0, platform="NA", job_id=0, wrapper_queue=None, wrapper_code=None):
    try:
      next_counter = self._get_next_counter_by_job_name(job_name)
      job_data_dc = JobData(_id=0, 
                    counter=next_counter, 
                    job_name=job_name, 
                    submit=submit, 
                    status=status, 
                    rowtype=self._get_defined_rowtype(wrapper_code), 
                    ncpus=ncpus, 
                    wallclock=wallclock, 
                    qos=self._get_defined_queue_name(wrapper_queue, wrapper_code, qos),                    
                    date=date,
                    member=member,
                    section=section,
                    chunk=chunk,                    
                    platform=platform,
                    job_id=job_id)
      return self._register_submitted_job_data_dc(job_data_dc)
    except Exception as exp:
      self._log.log(str(exp), traceback.format_exc())
      return None
  
  def write_start_time(self, job_name, start=0, status="UNKWOWN", ncpus=0, wallclock="00:00", qos="debug", date="", member="", section="", chunk=0, platform="NA", job_id=0, wrapper_queue=None, wrapper_code=None):
    try:
      job_data_dc_last = self.get_job_data_dc_unique_latest_by_job_name(job_name)
      if not job_data_dc_last:
        job_data_dc_last = self.write_submit_time(job_name=job_name, status=status, ncpus=ncpus, wallclock=wallclock, qos=qos, date=date, member=member, section=section, chunk=chunk, platform=platform, job_id=job_id, wrapper_queue=wrapper_queue, wrapper_code=wrapper_code)
        self._log.log("write_start_time {0} start not found.".format(job_name))
      job_data_dc_last.start = start
      job_data_dc_last.qos = self._get_defined_queue_name(wrapper_queue, wrapper_code, qos)
      job_data_dc_last.status = status
      job_data_dc_last.rowtype = self._get_defined_rowtype(wrapper_code)
      job_data_dc_last.job_id = job_id
      return self.update_job_data_dc_by_id(job_data_dc_last)
    except Exception as exp:
      self._log.log(str(exp), traceback.format_exc())
      return None
  
  def write_finish_time(self, job_name, finish=0, status="UNKNOWN", ncpus=0, wallclock="00:00", qos="debug", date="", member="", section="", chunk=0, platform="NA", job_id=0, platform_object=None, packed=False, parent_id_list=None, no_slurm=True, out_file_path=None, out_file=None, err_file=None, wrapper_queue=None, wrapper_code=None):
    try:
      job_data_dc_last = self.get_job_data_dc_unique_latest_by_job_name(job_name)
      if not job_data_dc_last:
        job_data_dc_last = self.write_submit_time(job_name=job_name, status=status, ncpus=ncpus, wallclock=wallclock, qos=qos, date=date, member=member, section=section, chunk=chunk, platform=platform, job_id=job_id, wrapper_queue=wrapper_queue, wrapper_code=wrapper_code)
        self._log.log("write_finish_time {0} submit not found.".format(job_name))
      # writing finish
        
    except Exception as exp:
      self._log.log(str(exp), traceback.format_exc())
      return None

  def _register_submitted_job_data_dc(self, job_data_dc):
    self._set_current_job_data_rows_last_to_zero(job_data_dc.job_name)
    self.manager.insert_job_data(job_data_dc)
    return self.get_job_data_dc_unique_latest_by_job_name(job_data_dc.job_name)

  def get_job_data_dc_unique_latest_by_job_name(self, job_name):
    job_data_row_last = self.manager.get_job_data_last_by_name(job_name)
    if len(job_data_row_last) > 0:
      return JobData.from_model(job_data_row_last[0])
    return None

  def update_job_data_dc_by_id(self, job_data_dc):
    self.manager.update_job_data_by_id(job_data_dc)
    return self.get_job_data_dc_unique_latest_by_job_name(job_data_dc.job_name)

  def _set_current_job_data_rows_last_to_zero(self, job_name):
    """ Sets the column last = 0 for all job_rows by job_name and last = 1. """
    job_data_row_last = self.manager.get_job_data_last_by_name(job_name)
    job_data_dc_list = [JobData.from_model(row) for row in job_data_row_last]
    for job_data_dc in job_data_dc_list:          
      job_data_dc.last = 0
      self.manager.update_job_data_by_id(job_data_dc)

  def _get_next_counter_by_job_name(self, job_name):
    job_data_dc = self.get_job_data_dc_unique_latest_by_job_name(job_name)
    max_counter = self.manager.get_job_data_max_counter()
    if job_data_dc:      
      return max(max_counter, job_data_dc.counter)
    else:
      return max_counter
  
  def _get_defined_rowtype(self, code):  
    if code:
        return code
    else:
        return RowType.NORMAL
  
  def _get_defined_queue_name(self, wrapper_queue, wrapper_code, qos):
    if wrapper_code and wrapper_code > 2 and wrapper_queue is not None:
      return wrapper_queue
    return qos 