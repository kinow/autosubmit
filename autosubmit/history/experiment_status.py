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

import traceback
from experiment_status_db_manager import ExperimentStatusDbManager
from log.log import Log

class ExperimentStatus():
  """ Represents the Experiment Status Mechanism that keeps track of currently active experiments """
  def __init__(self, expid):
    # type : (str) -> None
    self.expid = expid # type : str
    try:
      self._manager = ExperimentStatusDbManager(self.expid)
    except Exception as exp:
      Log.warning("Error while trying to update {0} in experiment_status.".format(str(self.expid)))
      Log.debug(traceback.format_exc())      
      Log.info(traceback.format_exc())
      self._manager = None
                            
  def set_running(self):
    # type : () -> None
    """ Set the status of the experiment in experiment_status of as_times.db as RUNNING. Creates the database, table and row if necessary."""
    if self._manager:
      self._manager.set_experiment_as_running()
    else:
      Log.info("It's not possible to set the experiment as RUNNING in this moment. If it is not automatically set as RUNNING in a few minutes, look for previous errors.")