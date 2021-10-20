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
import utils as HUtils

class Logging():
  def __init__(self, expid):
    self.expid = expid        
  
  def log(self, main_msg, traceback_msg=""):
    try:
      log_path = self.get_default_log_path(self.expid)
      HUtils.get_current_datetime()
      if not os.path.exists(log_path):
        HUtils.create_file_with_full_permissions(log_path)
      with open(log_path, "a") as exp_log:
        exp_log.write(self.build_message(main_msg, traceback_msg))
    except Exception as exp:
      print(exp)
      print("Logging failed. Please report it to the developers.")  
    
  def build_message(self, main_msg, traceback_msg):
    return "{0} :: {1} :: {2}\n".format(HUtils.get_current_datetime(), main_msg, traceback_msg)

  def get_default_log_path(self, expid):
    return os.path.join("/esarchive","autosubmit", "as_metadata", "logs","{}_log.txt".format(expid))