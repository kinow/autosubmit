#!/usr/bin/env python

# Copyright 2014 Climate Forecasting Unit, IC3

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
import platform

class ElQueue(HPCQueue):
	def __init__(self, expid):
		self._host = "ellen"
		self._scratch = "/cfu/scratch"
		self._project = "a"
		self._user = "asifsami"
		self._expid = expid
		#Ps-->self._remote_log_dir = "/cfu/autosubmit" + "/" + self._expid + "/tmp/LOG_" + self._expid
		self._remote_log_dir = self._scratch + "/" + self._project + "/" + self._user + "/" + self._expid + "/LOG_" + self._expid
		#Ps-->self._remote_common_dir = "/cfu/autosubmit/common"
		self._remote_common_dir = "/cfs/klemming/nobackup/a/asifsami/common/autosubmit"
		self._cancel_cmd = "ssh " + self._host + " kill -SIGINT"
		self._checkjob_cmd = "ssh " + self._host + " " + self._remote_common_dir + "/" + "pscall.sh"
		self._checkhost_cmd = "ssh " + self._host + " echo 1"
		self._submit_cmd = "ssh " + self._host + " " + self._remote_common_dir + "/" + "shcall.sh " + self._remote_log_dir + " "
		self._put_cmd = "scp"
		self._get_cmd = "scp"
		self._mkdir_cmd = "ssh " + self._host + " mkdir -p " + self._remote_log_dir
		self._job_status = dict()
		self._job_status['COMPLETED'] = ['1']
		self._job_status['RUNNING'] = ['0']
		self._job_status['QUEUING'] = ['qw', 'hqw', 'hRwq']
		self._job_status['FAILED'] = ['Eqw', 'Ehqw', 'EhRqw']
		self._pathdir = "\$HOME/LOG_" + self._expid
	
	def update_cmds(self):
		#self._remote_log_dir = "/cfu/autosubmit" + "/" + self._expid + "/tmp/LOG_" + self._expid
		self._remote_log_dir = self._scratch + "/" + self._project + "/" + self._user + "/" + self._expid + "/LOG_" + self._expid
		#self._remote_common_dir = "/cfu/autosubmit/common"
		self._remote_common_dir = "/cfs/klemming/nobackup/a/asifsami/common/autosubmit"
		self._status_cmd = "ssh " + self._host + " bjobs -w -X"
		self._cancel_cmd = "ssh " + self._host + " kill -SIGINT"
		self._checkjob_cmd = "ssh " + self._host + " " + self._remote_common_dir + "/" + "pscall.sh"
		self._checkhost_cmd = "ssh " + self._host + " echo 1"
		self._submit_cmd = "ssh " + self._host + " " + self._remote_common_dir + "/" + "shcall.sh " + self._remote_log_dir + " "
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
		return output

	def get_submitted_job_id(self, output):
		return output

	def jobs_in_queue(self, output):
		dom = parseString(output)
		jobs_xml = dom.getElementsByTagName("JB_job_number")
		return [int(element.firstChild.nodeValue) for element in jobs_xml ]
	
		
def main():
	q = ElQueue()
	q.check_job(1688)
	j = q.submit_job("/cfu/autosubmit/l002/templates/l002.sim")
	sleep(10)
	print q.check_job(j)
	q.cancel_job(j)

if __name__ == "__main__":
	main()
