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

import collections
import time
import autosubmit.history.utils as HUtils
import autosubmit.history.database_managers.database_models as Models
from datetime import datetime, timedelta
from json import dumps, loads

class JobData(object):
    """
    Robust representation of a row in the job_data table of the experiment history database.
    """

    def __init__(self, _id, counter=1, job_name="None", created=None, modified=None, submit=0, start=0, finish=0, status="UNKNOWN", rowtype=0, ncpus=0, wallclock="00:00", qos="debug", energy=0, date="", section="", member="", chunk=0, last=1, platform="NA", job_id=0, extra_data="", nnodes=0, run_id=None, MaxRSS=0.0, AveRSS=0.0, out="", err="", rowstatus=Models.RowStatus.INITIAL):
      """
      """
      self._id = _id
      self.counter = counter
      self.job_name = job_name
      self.created = HUtils.get_current_datetime_if_none(created)
      self.modified = HUtils.get_current_datetime_if_none(modified)
      self._submit = int(submit)
      self._start = int(start)
      self._finish = int(finish)
      self.status = status
      self.rowtype = rowtype
      self.ncpus = ncpus
      self.wallclock = wallclock
      self.qos = qos if qos else "debug"
      self._energy = energy if energy else 0
      self.date = date if date else ""
      self.section = section if section else ""
      self.member = member if member else ""
      self.chunk = chunk if chunk else 0
      self.last = last
      self._platform = platform if platform and len(
          platform) > 0 else "NA"
      self.job_id = job_id if job_id else 0
      try:
          self.extra_data_parsed = loads(extra_data)
      except Exception as exp:
          self.extra_data_parsed = {} # Fail fast            
      self.extra_data = extra_data
      self.nnodes = nnodes
      self.run_id = run_id
      self.require_update = False
      # DB VERSION 15 attributes
      self.MaxRSS = MaxRSS
      self.AveRSS = AveRSS
      self.out = out
      self.err = err
      self.rowstatus = rowstatus

    @classmethod
    def from_model(cls, row):
      """ Build JobData from JobDataRow. """
      job_data = cls(row.id, 
                      row.counter,
                      row.job_name,
                      row.created,
                      row.modified,
                      row.submit,
                      row.start,
                      row.finish,
                      row.status,
                      row.rowtype,
                      row.ncpus,
                      row.wallclock,
                      row.qos,
                      row.energy,
                      row.date,
                      row.section,
                      row.member,
                      row.chunk,
                      row.last,
                      row.platform,
                      row.job_id,
                      row.extra_data,
                      row.nnodes,
                      row.run_id,
                      row.MaxRSS,
                      row.AveRSS,
                      row.out,
                      row.err,
                      row.rowstatus)
      return job_data


    @property
    def submit(self):
        """
        Returns the submit time timestamp as an integer.
        """
        return int(self._submit)

    @property
    def start(self):
        """
        Returns the start time timestamp as an integer.
        """
        return int(self._start)

    @property
    def finish(self):
        """
        Returns the finish time timestamp as an integer.
        """
        return int(self._finish)

    @property
    def platform(self):
        """
        Returns the name of the platform, "NA" if no platform is set.
        """
        return self._platform

    @property
    def energy(self):
        """
        Returns the energy spent value (JOULES) as an integer.
        """
        return self._energy

    @submit.setter
    def submit(self, submit):
        self._submit = int(submit)

    @start.setter
    def start(self, start):
        self._start = int(start)

    @finish.setter
    def finish(self, finish):
        self._finish = int(finish)

    @platform.setter
    def platform(self, platform):
        self._platform = platform if platform and len(platform) > 0 else "NA"

    @energy.setter
    def energy(self, energy):
        """
        Set the energy value. If it is different than the current energy value, a update flag will be activated.
        """
        if energy > 0:
            if (energy != self._energy):
                # print("Updating energy to {0} from {1}.".format(
                #    energy, self._energy))
                self.require_update = True
            self._energy = energy if energy else 0

    def delta_queue_time(self):
        """
        Returns queuing time as a timedelta object.
        """
        return str(timedelta(seconds=self.queuing_time()))

    def delta_running_time(self):
        """
        Returns running time as a timedelta object.
        """
        return str(timedelta(seconds=self.running_time()))

    def submit_datetime(self):
        """
        Return the submit time as a datetime object, None if submit time equal 0.
        """
        if self.submit > 0:
            return datetime.fromtimestamp(self.submit)
        return None

    def start_datetime(self):
        """
        Return the start time as a datetime object, None if start time equal 0.
        """
        if self.start > 0:
            return datetime.fromtimestamp(self.start)
        return None

    def finish_datetime(self):
        """
        Return the finish time as a datetime object, None if start time equal 0.
        """
        if self.finish > 0:
            return datetime.fromtimestamp(self.finish)
        return None

    def submit_datetime_str(self):
        """
        Returns the submit datetime as a string with format %Y-%m-%d-%H:%M:%S
        """
        o_datetime = self.submit_datetime()
        if o_datetime:
            return o_datetime.strftime(DATETIME_FORMAT)
        else:
            return None

    def start_datetime_str(self):
        """
        Returns the start datetime as a string with format %Y-%m-%d-%H:%M:%S
        """
        o_datetime = self.start_datetime()
        if o_datetime:
            return o_datetime.strftime(DATETIME_FORMAT)
        else:
            return None

    def finish_datetime_str(self):
        """
        Returns the finish datetime as a string with format %Y-%m-%d-%H:%M:%S
        """
        o_datetime = self.finish_datetime()
        if o_datetime:
            return o_datetime.strftime(DATETIME_FORMAT)
        else:
            return None

    def running_time(self):
        """
        Calculates and returns the running time of the job, in seconds.

        :return: Running time in seconds.   
        :rtype: int
        """
        if self.status in ["RUNNING", "COMPLETED", "FAILED"]:
            return HUtils.calculate_run_time_in_seconds(self.start, self.finish)                        
        return 0

    def queuing_time(self):
        """
        Calculates and returns the queuing time of the job, in seconds.

        :return: Queueing time in seconds.   
        :rtype: int
        """
        if self.status in ["SUBMITTED", "QUEUING", "RUNNING", "COMPLETED", "HELD", "PREPARED", "FAILED", "SKIPPED"]:
            return HUtils.calculate_queue_time_in_seconds(self.submit, self.start)            
        return 0

    def get_hdata(self):
        """
        Get the job data as an ordered dict into a JSON object.  
        :return: Job data as an ordered dict into a JSON object.  
        :rtype: JSON object.
        """
        hdata = collections.OrderedDict()
        hdata["name"] = self.job_name
        hdata["date"] = self.date
        hdata["section"] = self.section
        hdata["member"] = self.member
        hdata["chunk"] = self.chunk
        hdata["submit"] = self.submit_datetime_str()
        hdata["start"] = self.start_datetime_str()
        hdata["finish"] = self.finish_datetime_str()
        hdata["queue_time"] = self.delta_queue_time()
        hdata["run_time"] = self.delta_running_time()
        hdata["wallclock"] = self.wallclock
        hdata["ncpus"] = self.ncpus
        hdata["nnodes"] = self.nnodes
        hdata["energy"] = self.energy
        hdata["platform"] = self.platform
        hdata["MaxRSS"] = self.MaxRSS
        hdata["AveRSS"] = self.AveRSS
        return dumps(hdata)