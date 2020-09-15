#!/usr/bin/env python

# Copyright 2017 Earth Sciences Department, BSC-CNS

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
from time import sleep
from time import mktime
from datetime import datetime
import traceback

from xml.dom.minidom import parseString

from autosubmit.platforms.paramiko_platform import ParamikoPlatform
from autosubmit.platforms.headers.slurm_header import SlurmHeader
from autosubmit.platforms.wrappers.wrapper_factory import SlurmWrapperFactory
from log.log import AutosubmitCritical,AutosubmitError,Log
class SlurmPlatform(ParamikoPlatform):
    """
    Class to manage jobs to host using SLURM scheduler

    :param expid: experiment's identifier
    :type expid: str
    """

    def __init__(self, expid, name, config):
        ParamikoPlatform.__init__(self, expid, name, config)
        self._header = SlurmHeader()
        self._wrapper = SlurmWrapperFactory(self)
        self.job_status = dict()
        self.job_status['COMPLETED'] = ['COMPLETED']
        self.job_status['RUNNING'] = ['RUNNING']
        self.job_status['QUEUING'] = ['PENDING', 'CONFIGURING', 'RESIZING']
        self.job_status['FAILED'] = ['FAILED', 'CANCELLED','CANCELLED+', 'NODE_FAIL', 'PREEMPTED', 'SUSPENDED', 'TIMEOUT','OUT_OF_MEMORY','OUT_OF_ME+','OUT_OF_ME']
        self._pathdir = "\$HOME/LOG_" + self.expid
        self._allow_arrays = False
        self._allow_wrappers = True
        self.update_cmds()
        self.config = config
        exp_id_path = os.path.join(config.LOCAL_ROOT_DIR, self.expid)
        tmp_path = os.path.join(exp_id_path, "tmp")
        self._submit_script_path = os.path.join(tmp_path , config.LOCAL_ASLOG_DIR,"submit_"+self.name+".sh")
        self._submit_script_file = open(self._submit_script_path, 'w').close()

    def open_submit_script(self):
        self._submit_script_file = open(self._submit_script_path, 'w').close()
        self._submit_script_file = open(self._submit_script_path, 'a')

    def get_submit_script(self):
        self._submit_script_file.close()
        os.chmod(self._submit_script_path, 0o750)
        return os.path.join(self.config.LOCAL_ASLOG_DIR,os.path.basename(self._submit_script_path))


    def submit_Script(self,hold=False):
        """
        Sends a Submit file Script, execute it  in the platform and retrieves the Jobs_ID of all jobs at once.

        :param job: job object
        :type job: autosubmit.job.job.Job
        :return: job id for  submitted jobs
        :rtype: list(str)
        """
        try:
            self.send_file(self.get_submit_script(),False)
            cmd = os.path.join(self.get_files_path(),os.path.basename(self._submit_script_path))
            self.send_command(cmd)
            jobs_id = self.get_submitted_job_id(self.get_ssh_output())
        except IOError as e:
            raise AutosubmitError("Submit script is not found, retry again in next AS iteration", 6008, e.message)
        except BaseException as e:
            raise AutosubmitError("Job couldn't be submitted, retry again in next AS iteration", 6008, e.message)

    def update_cmds(self):
        """
        Updates commands for platforms
        """
        self.root_dir = os.path.join(self.scratch, self.project, self.user, self.expid)
        self.remote_log_dir = os.path.join(self.root_dir, "LOG_" + self.expid)
        self.cancel_cmd = "scancel"
        self._checkhost_cmd = "echo 1"
        self._submit_cmd = 'sbatch -D {1} {1}/'.format(self.host, self.remote_log_dir)
        self._submit_hold_cmd = 'sbatch -H -D {1} {1}/'.format(self.host, self.remote_log_dir)

        self.put_cmd = "scp"
        self.get_cmd = "scp"
        self.mkdir_cmd = "mkdir -p " + self.remote_log_dir


    def get_checkhost_cmd(self):
        return self._checkhost_cmd

    def get_mkdir_cmd(self):
        return self.mkdir_cmd

    def get_remote_log_dir(self):
        return self.remote_log_dir

    def parse_job_output(self, output):
        return output.strip().split(' ')[0].strip()

    def parse_job_finish_data(self, output, packed):
        """Parses the context of the sacct query to SLURM for a single job.
        Only normal jobs return submit, start, finish, joules, ncpus, nnodes.

        When a wrapper has finished, capture finish time.

        :param output: The sacct output
        :type output: str
        :param job_id: Id in SLURM for the job
        :type job_id: int
        :param packed: true if job belongs to package
        :type packed: bool
        :return: submit, start, finish, joules, ncpus, nnodes, detailed_data
        :rtype: int, int, int, int, int, int, json object (str)
        """
        try:
            # Setting up: Storing detail for posterity
            detailed_data = dict()
            # No blank spaces after or before
            output = output.strip() if output else None
            lines = output.split("\n") if output else []
            is_end_of_wrapper = False
            extra_data = None
            # If there is output, list exists
            if len(lines) > 0:
                # Collecting information from all output
                for line in lines:
                    line = line.strip().split()
                    if len(line) > 0:
                        # Collecting detailed data
                        name = str(line[0])
                        if packed:
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
                            extra_data = {"energy": str(line[7] if len(line) > 7 else "NA"),
                                          "MaxRSS": str(line[8] if len(line) > 8 else "NA"),
                                          "AveRSS": str(line[9] if len(line) > 9 else "NA")}
                        # Detailed data will contain the important information from output
                        detailed_data[name] = extra_data
                submit = start = finish = joules = nnodes = ncpus = 0
                status = "UNKNOWN"
                # Take first line as source
                line = lines[0].strip().split()
                ncpus = int(line[2] if len(line) > 2 else 0)
                nnodes = int(line[3] if len(line) > 3 else 0)
                status = str(line[1])
                if packed == False:
                    # If it is not wrapper job, take first line as source
                    if status not in ["COMPLETED", "FAILED", "UNKNOWN"]:
                        # It not completed, then its error and send default data plus output
                        return (0, 0, 0, 0, ncpus, nnodes, detailed_data)
                else:
                    # Check if the wrapper has finished
                    if status in ["COMPLETED", "FAILED", "UNKNOWN"]:
                        # Wrapper has finished
                        is_end_of_wrapper = True
                if line:
                    try:
                        # Parse submit and start only for normal jobs (not packed)
                        submit = int(mktime(datetime.strptime(
                            line[4], "%Y-%m-%dT%H:%M:%S").timetuple())) if not packed else 0
                        start = int(mktime(datetime.strptime(
                            line[5], "%Y-%m-%dT%H:%M:%S").timetuple())) if not packed else 0
                        # Assuming the job has been COMPLETED
                        # If normal job or end of wrapper => Try to get the finish time from the first line of the output, else default to now.
                        finish = (int(mktime(datetime.strptime(
                            line[6], "%Y-%m-%dT%H:%M:%S").timetuple())) if len(line) > 6 and line[6] != "Unknown" else datetime.now().timestamp()) if not packed or is_end_of_wrapper == True else 0
                        # If normal job or end of wrapper => Try to get energy from first line
                        joules = (self.parse_output_number(
                            line[7]) if len(line) > 7 and len(line[7]) > 0 else 0) if not packed or is_end_of_wrapper == True else 0
                    except Exception as exp:
                        Log.info(
                            "Parsing mishandling.")
                        # joules = -1
                        pass

                detailed_data = detailed_data if not packed or is_end_of_wrapper == True else extra_data
                return (submit, start, finish, joules, ncpus, nnodes, detailed_data)

            return (0, 0, 0, 0, 0, 0, dict())
        except Exception as exp:
            Log.warning(
                "Autosubmit couldn't parse SLURM energy output. From parse_job_finish_data: {0}".format(str(exp)))
            return (0, 0, 0, 0, 0, 0, dict())

    def parse_output_number(self, string_number):
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
                multiplier = 1000000
                number = string_number[:-1]
            elif last_letter == "K" or last_letter == "M":
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

    def parse_Alljobs_output(self, output,job_id):
        try:
            status = [x.split()[1] for x in output.splitlines() if x.split()[0] == str(job_id)]
        except BaseException as e:
            return status
        if len(status) == 0:
            return status
        return status[0]



    def get_submitted_job_id(self, outputlines):
        try:
            if outputlines.find("failed") != -1:
                raise AutosubmitCritical("Submission failed. Command Failed", 7014)
            jobs_id = []
            for output in outputlines.splitlines():
                jobs_id.append(int(output.split(' ')[3]))
            return jobs_id
        except IndexError:
            raise AutosubmitCritical("Submission failed. There are issues on your config file",7014)
    def jobs_in_queue(self):
        dom = parseString('')
        jobs_xml = dom.getElementsByTagName("JB_job_number")
        return [int(element.firstChild.nodeValue) for element in jobs_xml]

    def get_submit_cmd(self, job_script, job, hold=False):
        if not hold:
            self._submit_script_file.write(self._submit_cmd + job_script + "\n")
        else:
            self._submit_script_file.write(self._submit_hold_cmd + job_script + "\n" )



    def get_checkjob_cmd(self, job_id):
        return 'sacct -n -X -j {1} -o "State"'.format(self.host, job_id)

    def get_checkAlljobs_cmd(self, jobs_id):
        return "sacct -n -X -j  {1} -o jobid,State".format(self.host, jobs_id)
    def get_queue_status_cmd(self, job_id):
        return 'squeue -j {0} -o %A,%R'.format(job_id)

    def get_job_energy_cmd(self, job_id):
        return 'sacct -n -j {0} -o JobId%25,State,NCPUS,NNodes,Submit,Start,End,ConsumedEnergy,MaxRSS%25,AveRSS%25'.format(job_id)

    def parse_queue_reason(self, output,job_id):
        reason =[x.split(',')[1] for x in output.splitlines() if x.split(',')[0] == str(job_id)]
        if len(reason) > 0:
            return reason[0]
        return reason


    @staticmethod
    def wrapper_header(filename, queue, project, wallclock, num_procs, dependency, directives, threads,method="asthreads"):
        if method =='srun':
            language = "#!/bin/bash"
            return \
                language + """
###############################################################################
#              {0}
###############################################################################
#
#SBATCH -J {0}
{1}
#SBATCH -A {2}
#SBATCH --output={0}.out
#SBATCH --error={0}.err
#SBATCH -t {3}:00
#SBATCH -n {4}
#SBATCH --cpus-per-task={7}
{5}
{6}
#
###############################################################################
                """.format(filename, queue, project, wallclock, num_procs, dependency,
                           '\n'.ljust(13).join(str(s) for s in directives), threads)
        else:
            language = "#!/usr/bin/env python"
            return \
            language+"""
###############################################################################
#              {0}
###############################################################################
#
#SBATCH -J {0}
{1}
#SBATCH -A {2}
#SBATCH --output={0}.out
#SBATCH --error={0}.err
#SBATCH -t {3}:00
#SBATCH --cpus-per-task={7}
#SBATCH -n {4}
{5}
{6}
#
###############################################################################
            """.format(filename, queue, project, wallclock, num_procs, dependency,
                   '\n'.ljust(13).join(str(s) for s in directives),threads)

    @staticmethod
    def allocated_nodes():
        return """os.system("scontrol show hostnames $SLURM_JOB_NODELIST > node_list")"""

    def check_file_exists(self,filename):
        file_exist = False
        sleeptime = 5
        retries = 0
        max_retries = 3
        while not file_exist and retries < max_retries:
            try:
                self._ftpChannel.stat(os.path.join(self.get_files_path(), filename))  # This return IOError if path doesn't exist
                file_exist = True
            except IOError:  # File doesn't exist, retry in sleeptime
                Log.debug("{2} File still no exists.. waiting {0}s for a new retry ( retries left: {1})", sleeptime,
                          max_retries - retries, os.path.join(self.get_files_path(),filename))
                sleep(sleeptime)
                sleeptime = sleeptime + 5
                retries = retries + 1
            except BaseException as e:  # Unrecoverable error
                Log.critical("Crashed while retrieving remote logs",6001,e.message)
                file_exist = False  # won't exist
                retries = 999  # no more retries

        return file_exist