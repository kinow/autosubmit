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
from database_managers.experiment_history_db_manager import ExperimentHistoryDatabaseManager

class ExperimentHistory():
  def __init__(self, expid):
    self.expid = expid
    self.manager = ExperimentHistoryDatabaseManager(self.expid)
  
  def get_all_job_data_row(self):
    return self.manager.get_job_data_all()

# if __name__ == "__main__":
#   exp = ExperimentHistory("tt00")
#   for job_data_row in exp.get_all_job_data_row():
#     print(job_data_row)