#!/usr/bin/env python

# Copyright 2014 Climatic Forecasting Unit, IC3

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


from xml.dom.minidom import parseString
from hpcqueue import HPCQueue
from time import sleep

class ArQueue(HPCQueue):
	def __init__(self, expid):
		self._host = "archer"
		self._scratch = "/work/pr1u1011"
		self._project = "pr1u1011"
		self._user = "pr1e1002"
		self._expid = expid
		self._remote_log_dir = self._scratch + "/" + self._project + "/" + self._user + "/" + self._expid + "/LOG_" + self._expid
		self._cancel_cmd = "ssh " + self._host + " qdel"
		self._checkjob_cmd = "ssh " + self._host + " /work/pr1u1011/pr1u1011/pr1e1001/common/autosubmit/qstatjob.sh"
		self._checkhost_cmd = "ssh " + self._host + " echo 1"
		self._submit_cmd = "ssh " + self._host + " \"cd " + self._remote_log_dir + "; qsub \" "
		self._status_cmd = "ssh " + self._host + " qsub -u \$USER | tail -n +6|cut -d' ' -f10"
		self._put_cmd = "scp"
		self._get_cmd = "scp"
		self._mkdir_cmd = "ssh " + self._host + " mkdir -p " + self._remote_log_dir
		self._job_status = dict()
		self._job_status['COMPLETED'] = ['F', 'E', 'c']
		self._job_status['RUNNING'] = ['R']
		self._job_status['QUEUING'] = ['Q', 'H', 'S', 'T', 'W', 'U', 'M']
		self._job_status['FAILED'] = ['Failed', 'Node_fail', 'Timeout']
		self._pathdir = "\$HOME/LOG_" + self._expid
	
	def update_cmds(self):
		self._remote_log_dir = self._scratch + "/" + self._project + "/" + self._user + "/" + self._expid + "/LOG_" + self._expid
		self._cancel_cmd = "ssh " + self._host + " qdel"
		self._checkjob_cmd = "ssh " + self._host + " /work/pr1u1011/pr1u1011/shared/common/autosubmit/qstatjob.sh"
		self._checkhost_cmd = "ssh " + self._host  + " echo 1"
		self._submit_cmd = "ssh " + self._host + " \"cd " + self._remote_log_dir + "; qsub \" "
		self._status_cmd = "ssh " + self._host + " qsub -u \$USER | tail -n +6|cut -d' ' -f10"
		self._put_cmd = "scp"
		self._get_cmd = "scp"
		self._mkdir_cmd = "ssh " + self._host + " mkdir -p " + self._remote_log_dir
	
	def get_checkhost_cmd(self):
		return self._checkhost_cmd
	
	def get_submit_cmd(self):
		return self._submit_cmd

	def get_remote_log_dir(self):
		return self._remote_log_dir

	def get_mkdir_cmd(self):
		return self._mkdir_cmd

	def parse_job_output(self, output):
		#job_state = output.split('\n')[2].split()[4]
		#return job_state
		return output

	def get_submitted_job_id(self, output):
		return output.split('.')[0]

	def jobs_in_queue(self, output):
		print output
		return output.split()


def main():
	q = ArQueue()
	q.check_job(1688)
	j = q.submit_job("/cfu/autosubmit/a002/templates/a002.sim")
	sleep(10)
	print q.check_job(j)
	q.cancel_job(j)
	
		
if __name__ == "__main__":
	main()
