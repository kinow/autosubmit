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

import unittest
import time
import random
from experiment_history_db_manager import ExperimentHistoryDatabaseManager
from autosubmit.history.data_classes.experiment_run import ExperimentRun
from autosubmit.history.data_classes.job_data import JobData
EXPID = "tt00"

class TestExperimentHistoryDatabaseManager(unittest.TestCase):

  def setUp(self):
    self.experiment_database = ExperimentHistoryDatabaseManager(EXPID)

  def tearDown(self):
    pass

  def test_get_max_id(self):        
    max_item = self.experiment_database.get_experiment_run_with_max_id()  
    self.assertTrue(len(max_item) > 0)
    self.assertTrue(max_item.run_id >= 18) # Max is 18

  def test_pragma(self):
    self.assertTrue(self.experiment_database._get_pragma_version() == 16)
  
  def test_get_job_data(self):
    job_data = self.experiment_database.get_job_data_last_by_name("a29z_20000101_fc0_1_SIM")
    self.assertTrue(len(job_data) > 0)
    self.assertTrue(job_data[0].last == 1)
    self.assertTrue(job_data[0].job_name == "a29z_20000101_fc0_1_SIM")

    job_data = self.experiment_database.get_job_data_by_name("a29z_20000101_fc0_1_SIM")
    self.assertTrue(job_data[0].job_name == "a29z_20000101_fc0_1_SIM")

    job_data = self.experiment_database.get_job_data_last_by_run_id(18) # Latest
    self.assertTrue(len(job_data) > 0)

    job_data = self.experiment_database.get_job_data_last_by_run_id_and_finished(18) 
    self.assertTrue(len(job_data) > 0)

    job_data = self.experiment_database.get_job_data_all()
    self.assertTrue(len(job_data) > 0)
  
  def test_insert_and_delete_experiment_run(self):
    new_run = ExperimentRun(19)
    new_id = self.experiment_database.insert_experiment_run(new_run)
    self.assertIsNotNone(new_id)
    last_experiment_run = self.experiment_database.get_experiment_run_with_max_id()
    self.assertTrue(new_id == last_experiment_run.run_id)
    self.experiment_database.delete_experiment_run(new_id)
    last_experiment_run = self.experiment_database.get_experiment_run_with_max_id()
    self.assertTrue(new_id != last_experiment_run.run_id)
  
  def test_insert_and_delete_job_data(self):
    max_run_id = self.experiment_database.get_experiment_run_with_max_id().run_id
    new_job_data_name = "test_001_name_{0}".format(int(time.time()))
    new_job_data = JobData(_id=1, job_name=new_job_data_name, run_id=max_run_id)
    new_job_data_id = self.experiment_database.insert_job_data(new_job_data)
    self.assertIsNotNone(new_job_data_id)
    self.experiment_database.delete_job_data(new_job_data_id)
    job_data = self.experiment_database.get_job_data_by_name(new_job_data_name)
    self.assertTrue(len(job_data) == 0)


  def test_update_experiment_run(self):
    last_experiment_run = self.experiment_database.get_experiment_run_with_max_id() # 18
    experiment_run_data_class = ExperimentRun.from_model(last_experiment_run)
    backup_run = ExperimentRun.from_model(last_experiment_run)
    experiment_run_data_class.chunk_unit = "unouno"
    experiment_run_data_class.running = random.randint(1, 100)
    experiment_run_data_class.queuing = random.randint(1, 100)
    experiment_run_data_class.suspended = random.randint(1, 100)
    self.experiment_database.update_experiment_run(experiment_run_data_class)
    last_experiment_run = self.experiment_database.get_experiment_run_with_max_id() # 18
    self.assertTrue(last_experiment_run.chunk_unit == experiment_run_data_class.chunk_unit)
    self.assertTrue(last_experiment_run.running == experiment_run_data_class.running)
    self.assertTrue(last_experiment_run.queuing == experiment_run_data_class.queuing)
    self.assertTrue(last_experiment_run.suspended == experiment_run_data_class.suspended)
    self.experiment_database.update_experiment_run(backup_run)

  def test_job_data_from_model(self):
    job_data_rows = self.experiment_database.get_job_data_last_by_name("a29z_20000101_fc0_1_SIM")
    job_data_row_first = job_data_rows[0]
    job_data_data_class = JobData.from_model(job_data_row_first)
    print(job_data_data_class.extra_data_parsed)
    self.assertTrue(job_data_row_first.job_name == job_data_data_class.job_name)

if __name__ == '__main__':
  unittest.main()