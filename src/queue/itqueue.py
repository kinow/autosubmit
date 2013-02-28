#!/usr/bin/env python

from xml.dom.minidom import parseString
from hpcqueue import HPCQueue
from time import sleep

class ItQueue(HPCQueue):
	def __init__(self, expid):
		self._host = "ithaca"
		self._scratch = "/scratch"
		self._project = "cfu"
		self._user = "masif"
		self._expid = expid
		self._remote_log_dir = self._scratch + "/" + self._project + "/" + self._user + "/" + self._expid + "/LOG_" + self._expid
		self._cancel_cmd = "ssh " + self._host + " qdel"
		self._checkjob_cmd = "ssh " + self._host + " qstatjob.sh"
		self._submit_cmd = "ssh " + self._host + " qsub -wd " + self._remote_log_dir + " " + self._remote_log_dir + "/"
		self._put_cmd = "scp"
		self._get_cmd = "scp"
		self._mkdir_cmd = "ssh " + self._host + " mkdir -p " + self._remote_log_dir
		self._job_status = dict()
		self._job_status['COMPLETED'] = ['c']
		self._job_status['RUNNING'] = ['r', 't', 'Rr', 'Rt']
		self._job_status['QUEUING'] = ['qw', 'hqw', 'hRwq', 'Rs', 'Rts', 'RS', 'RtS', 'RT', 'RtT']
		self._job_status['FAILED'] = ['Eqw', 'Ehqw', 'EhRqw', 's', 'ts', 'S', 'tS', 'T', 'tT', 'dr', 'dt', 'dRr', 'dRt', 'ds', 'dS', 'dT', 'dRs', 'dRS', 'dRT']
		self._pathdir = "\$HOME/LOG_" + self._expid
	
	def update_cmds(self):
		self._remote_log_dir = self._scratch + "/" + self._project + "/" + self._user + "/" + self._expid + "/LOG_" + self._expid
		self._cancel_cmd = "ssh " + self._host + " qdel"
		self._checkjob_cmd = "ssh " + self._host + " qstatjob.sh"
		self._submit_cmd = "ssh " + self._host + " qsub -wd " + self._remote_log_dir + " " + self._remote_log_dir + "/" 
		self._put_cmd = "scp"
		self._get_cmd = "scp"
		self._mkdir_cmd = "ssh " + self._host + " mkdir -p " + self._remote_log_dir

	def get_mkdir_cmd(self):
		return self._mkdir_cmd
	
	def get_submit_cmd(self):
		return self._submit_cmd

	def get_remote_log_dir(self):
		return self._remote_log_dir
	
	def parse_job_output(self, output):
		return output

	def get_submitted_job_id(self, output):
		return output.split(' ')[2]

	def jobs_in_queue(self, output):
		dom = parseString(output)
		jobs_xml = dom.getElementsByTagName("JB_job_number")
		return [int(element.firstChild.nodeValue) for element in jobs_xml ]

		
if __name__ == "__main__":
	q = ItQueue()
	q.check_job(1688)
	j = q.submit_job("/home/cfu/omula/test/run_t159l62_orca1.ksh")
	sleep(10)
	print q.check_job(j)
	q.cancel_job(j)
