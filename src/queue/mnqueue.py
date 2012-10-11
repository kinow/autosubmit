#!/usr/bin/env python

from xml.dom.minidom import parseString
from hpcqueue import HPCQueue
from time import sleep

class MnQueue(HPCQueue):
	def __init__(self, expid):
		self._host = "mn"
		self._expid = expid
		self._hpcuser = "\$USER"
		self._remote_log_dir = "/gpfs/scratch/ecm86/\$USER/" + self._expid + "/LOG_" + self._expid
		self._cancel_cmd = "ssh " + self._host + " mncancel"
		self._checkjob_cmd = "ssh " + self._host + " checkjob --xml"
		self._submit_cmd = "ssh " + self._host + " mnsubmit -initialdir " + self._remote_log_dir + " " + self._remote_log_dir + "/" 
		self._status_cmd = "ssh " + self._host + " mnq --xml"
		self._put_cmd = "scp"
		self._get_cmd = "scp"
		self._mkdir_cmd = "ssh " + self._host + " mkdir -p " + self._remote_log_dir
		self._job_status = dict()
		self._job_status['COMPLETED'] = ['Completed']
		self._job_status['RUNNING'] = ['Running']
		self._job_status['QUEUING'] = ['Pending', 'Idle', 'Blocked']
		self._job_status['FAILED'] = ['Failed', 'Node_fail', 'Timeout', 'Removed']

	def get_submit_cmd(self):
		self._submit_cmd = "ssh " + self._host + " mnsubmit -initialdir " + self._remote_log_dir + " " + self._remote_log_dir + "/" 
		return self._submit_cmd

	def get_remote_log_dir(self):
		self._remote_log_dir = "/gpfs/scratch/ecm86/\$USER/" + self._expid + "/LOG_" + self._expid
		return slef._remote_log_dir

	def get_mkdir_cmd(self):
		self._mkdir_cmd = "ssh " + self._host + " mkdir -p " + self._remote_log_dir
		return self._mkdir_cmd
	
	def parse_job_output(self, output):
		dom = parseString(output)
		job_xml = dom.getElementsByTagName("job")
		job_state = job_xml[0].getAttribute('State')
		return job_state

	def get_submitted_job_id(self, output):
		return output.split(' ')[3]
	
	def jobs_in_queue(self,	output):
		dom = parseString(output)
		job_list = dom.getElementsByTagName("job")
		return [ int(job.getAttribute('JobID')) for job in job_list ]
