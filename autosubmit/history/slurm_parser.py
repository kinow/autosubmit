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

from datetime import datetime
from time import mktime, time


def parse_job_finish_data(self, output, wrapped):
  """ 
  Slurm Command 'sacct -n --jobs {0} -o JobId%25,State,NCPUS,NNodes,Submit,Start,End,ConsumedEnergy,MaxRSS%25,AveRSS%25'
  Only not wrapped jobs return submit, start, finish, joules, ncpus, nnodes.

  :return: submit, start, finish, joules, ncpus, nnodes, detailed_data
  :rtype: int, int, int, int, int, int, json object (str)
  """
  try:
      # Setting up: Storing detail for posterity
      detailed_data = dict()
      steps = []
      # No blank spaces after or before
      output = output.strip() if output else None
      lines = output.split("\n") if output else []
      is_end_of_wrapper = False
      # If there is output, list exists
      if len(lines) > 0:
          # Collecting information from all output
          for line in lines:
              line = line.strip().split()
              if len(line) > 0:
                  # Collecting detailed data
                  name = str(line[0])
                  if wrapped:
                      # If it belongs to a wrapper
                      extra_data = {"ncpus": str(line[2] if len(line) > 2 else "NA"),
                                    "nnodes": str(line[3] if len(line) > 3 else "NA"),
                                    "submit": str(line[4] if len(line) > 4 else "NA"),
                                    "start": str(line[5] if len(line) > 5 else "NA"),
                                    "finish": str(line[6] if len(line) > 6 else "NA"),
                                    "energy": str(line[7] if len(line) > 7 else "NA"),
                                    "MaxRSS": str(line[8] if len(line) > 8 else "NA"),
                                    "AveRSS": str(line[9] if len(line) > 9 else "NA")}
                  else:
                      # Normal job
                      extra_data = {"submit": str(line[4] if len(line) > 4 else "NA"),
                                    "start": str(line[5] if len(line) > 5 else "NA"),
                                    "finish": str(line[6] if len(line) > 6 else "NA"),
                                    "energy": str(line[7] if len(line) > 7 else "NA"),
                                    "MaxRSS": str(line[8] if len(line) > 8 else "NA"),
                                    "AveRSS": str(line[9] if len(line) > 9 else "NA")}
                  # Detailed data will contain the important information from output
                  detailed_data[name] = extra_data
                  steps.append(name)
          submit = start = finish = energy = nnodes = ncpus = 0
          status = "UNKNOWN"
          # Take first line as source
          line = lines[0].strip().split()
          ncpus = int(line[2] if len(line) > 2 else 0)
          nnodes = int(line[3] if len(line) > 3 else 0)
          status = str(line[1])
          if wrapped == False:
              # If it is not wrapper job, take first line as source
              if status not in ["COMPLETED", "FAILED", "UNKNOWN"]:
                  # It not completed, then its error and send default data plus output
                  return (0, 0, 0, 0, ncpus, nnodes, detailed_data, False)
          else:
              # If it is a wrapped job
              # Check if the wrapper has finished
              if status in ["COMPLETED", "FAILED", "UNKNOWN"]:
                  # Wrapper has finished
                  is_end_of_wrapper = True
          # Continue with first line as source
          if line:
              try:
                  # Parse submit and start only for normal jobs (not wrapped)
                  submit = int(mktime(datetime.strptime(
                      line[4], "%Y-%m-%dT%H:%M:%S").timetuple())) if not wrapped else 0
                  start = int(mktime(datetime.strptime(
                      line[5], "%Y-%m-%dT%H:%M:%S").timetuple())) if not wrapped else 0
                  # Assuming the job has been COMPLETED
                  # If normal job or end of wrapper => Try to get the finish time from the first line of the output, else default to now.
                  finish = 0

                  if not wrapped:
                      # If normal job, take finish time from first line
                      finish = (int(mktime(datetime.strptime(line[6], "%Y-%m-%dT%H:%M:%S").timetuple(
                      ))) if len(line) > 6 and line[6] != "Unknown" else int(time()))
                      energy = parse_output_number(line[7]) if len(
                          line) > 7 and len(line[7]) > 0 else 0
                  else:
                      # If it is a wrapper job
                      # If end of wrapper, take data from first line
                      if is_end_of_wrapper == True:
                          finish = (int(mktime(datetime.strptime(line[6], "%Y-%m-%dT%H:%M:%S").timetuple(
                          ))) if len(line) > 6 and line[6] != "Unknown" else int(time()))
                          energy = parse_output_number(line[7]) if len(
                              line) > 7 and len(line[7]) > 0 else 0
                      else:
                          # If wrapped but not end of wrapper, try to get info from current data.
                          if "finish" in extra_data.keys() and extra_data["finish"] != "Unknown":
                              # finish data exists
                              finish = int(mktime(datetime.strptime(
                                  extra_data["finish"], "%Y-%m-%dT%H:%M:%S").timetuple()))
                          else:
                              # if finish date does not exist, query previous step.
                              if len(steps) >= 2 and detailed_data.__contains__(steps[-2]):
                                  new_extra_data = detailed_data[steps[-2]]
                                  if "finish" in new_extra_data.keys() and new_extra_data["finish"] != "Unknown":
                                      # This might result in an job finish < start, need to handle that in the caller function
                                      finish = int(mktime(datetime.strptime(
                                          new_extra_data["finish"], "%Y-%m-%dT%H:%M:%S").timetuple()))
                                  else:
                                      finish = int(time())
                              else:
                                  finish = int(time())
                          if "energy" in extra_data.keys() and extra_data["energy"] != "NA":
                              # energy exists
                              energy = parse_output_number(
                                  extra_data["energy"])
                          else:
                              # if energy does not exist, query previous step
                              if len(steps) >= 2 and detailed_data.__contains__(steps[-2]):
                                  new_extra_data = detailed_data[steps[-2]]
                                  if "energy" in new_extra_data.keys() and new_extra_data["energy"] != "NA":
                                      energy = parse_output_number(
                                          new_extra_data["energy"])
                                  else:
                                      energy = 0
                              else:
                                  energy = 0
              except Exception as exp:
                  pass

          detailed_data = detailed_data if not wrapped or is_end_of_wrapper == True else extra_data
          return (submit, start, finish, energy, ncpus, nnodes, detailed_data, is_end_of_wrapper)

      return (0, 0, 0, 0, 0, 0, dict(), False)
  except Exception as exp:
      return (0, 0, 0, 0, 0, 0, dict(), False)


def parse_output_number(string_number):
    """
    Parses number in format 1.0K 1.0M 1.0G

    :param string_number: String representation of number
    :type string_number: str
    :return: number in float format
    :rtype: float
    """
    number = 0.0
    if (string_number):
        last_letter = string_number.strip()[-1]
        multiplier = 1
        if last_letter == "G":
            multiplier = 1000000000
            number = string_number[:-1]
        elif last_letter == "M":
            multiplier = 1000000
            number = string_number[:-1]
        elif last_letter == "K":
            multiplier = 1000
            number = string_number[:-1]
        else:
            number = string_number
        try:
            number = float(number) * multiplier
        except Exception as exp:
            number = 0.0
            pass
    return number