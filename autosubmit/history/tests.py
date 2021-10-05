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
from experiment_history import ExperimentHistory

class TestExperimentHistory(unittest.TestCase):
  # @classmethod
  # def setUpClass(cls):    
  #   cls.exp = ExperimentHistory("tt00") # example database
  def test_select_job_data_by_run_id(self):
    result = ExperimentHistory("tt00").manager.get_job_data_last_by_run_id(17)
    print(result)
    self.assertIsNotNone(result)
  
  def test_get_all_job_data(self):
    result = ExperimentHistory("tt00").get_all_job_data_row()
    print(result)
    self.assertTrue(result)

if __name__ == '__main__':
  unittest.main()