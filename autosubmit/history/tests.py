#!/usr/bin/python

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
import traceback
from experiment_history import ExperimentHistory
from logging import Logging

class TestExperimentHistory(unittest.TestCase):
  # @classmethod
  # def setUpClass(cls):    
  #   cls.exp = ExperimentHistory("tt00") # example database
  def setUp(self):
    pass

  def test_db_exists(self):
    exp_history = ExperimentHistory("tt00")
    self.assertTrue(exp_history.my_database_exists() == True)
    exp_history = ExperimentHistory("tt99")
    self.assertTrue(exp_history.my_database_exists() == False)
  
  def test_is_header_ready(self):
    exp_history = ExperimentHistory("tt00")
    self.assertTrue(exp_history.is_header_ready() == True)

  def test_get_all_job_data(self):
    pass

class TestLogging(unittest.TestCase):

  def setUp(self):
    message = "No Message"
    try:
      raise Exception("Setup test exception")
    except:
      message = traceback.format_exc()
    self.log = Logging("tt00")
    self.exp_message = "Exception message"
    self.trace_message = message

  def test_build_message(self):
    message = self.log.build_message(self.exp_message, self.trace_message)
    print(message)
    self.assertIsNotNone(message)
    self.assertTrue(len(message) > 0)

  def test_log(self):    
    self.log.log(self.exp_message, self.trace_message)
    


if __name__ == '__main__':
  unittest.main()