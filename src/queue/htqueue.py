#!/usr/bin/env python

from xml.dom.minidom import parseString
from hpcqueue import HPCQueue
from time import sleep

class HtQueue(HPCQueue):
	def __init__(self, expid):
		self._host = "hecktor"
		self._scratch = "/work/pr1u1011"
		self._project = "pr1u1011"
		self._user = "pr1e1002"
		self._expid = expid
		self._remote_log_dir = self._scratch + "/" + self._project + "/" + self._user + "/" + self._expid + "/LOG_" + self._expid
		self._cancel_cmd = "ssh " + self._host + " qdel"
		self._checkjob_cmd = "ssh " + self._host + " qstat"
		self._checkhost_cmd = "ssh " + self._host + " echo 1"
		self._submit_cmd = "ssh " + self._host + " qsub -v PBS_O_WORKDIR=" + self._remote_log_dir + " " + self._remote_log_dir + "/"
		self._status_cmd = "ssh " + self._host + " qsub -u \$USER | tail -n +6|cut -d' ' -f10"
		self._put_cmd = "scp"
		self._get_cmd = "scp"
		self._mkdir_cmd = "ssh " + self._host + " mkdir -p " + self._remote_log_dir
		self._job_status = dict()
		self._job_status['COMPLETED'] = ['F', 'E']
		self._job_status['RUNNING'] = ['R']
		self._job_status['QUEUING'] = ['Q', 'H', 'S', 'T', 'W', 'U', 'M']
		self._job_status['FAILED'] = ['Failed', 'Node_fail', 'Timeout']
		self._pathdir = "\$HOME/LOG_" + self._expid
	
	def update_cmds(self):
		self._remote_log_dir = self._scratch + "/" + self._project + "/" + self._user + "/" + self._expid + "/LOG_" + self._expid
		self._cancel_cmd = "ssh " + self._host + " qdel"
		self._checkjob_cmd = "ssh " + self._host + " qstat"
		self._checkhost_cmd = "ssh " + self._host  + " echo 1"
		self._submit_cmd = "ssh " + self._host + " qsub -v PBS_O_WORKDIR=" + self._remote_log_dir + " " + self._remote_log_dir + "/"
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
		job_state = output.split('\n')[2].split()[4]
		return job_state

	def get_submitted_job_id(self, output):
		return output.split('.')[0]

	def jobs_in_queue(self, output):
		print output
		return output.split()


def main():
	q = HtQueue()
	q.check_job(1688)
	j = q.submit_job("/cfu/autosubmit/h002/templates/h002.sim")
	sleep(10)
	print q.check_job(j)
	q.cancel_job(j)
	
		
if __name__ == "__main__":
	main()
