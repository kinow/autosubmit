#!/usr/bin/env python

from xml.dom.minidom import parseString
from hpcqueue import HPCQueue
from time import sleep
from commands import getstatusoutput

class MnQueue(HPCQueue):
	def __init__(self, expid):
		self._host = "mn"
		self._cancel_cmd = "mncancel"
		self._checkjob_cmd = "checkjob --xml"
		self._submit_cmd = "mnsubmit"
		self._status_cmd = "mnq --xml"
		self._job_status = dict()
		self._job_status['COMPLETED'] = ['Completed']
		self._job_status['RUNNING'] = ['Running']
		self._job_status['QUEUING'] = ['Pending', 'Idle', 'Blocked']
		self._job_status['FAILED'] = ['Failed', 'Node_fail', 'Timeout']
		self._expid = expid
		self._remote_log_dir = "/gpfs/scratch/ecm86/\$USER/" + expid + "/LOG_" + expid
		#(status, user) = getstatusoutput('ssh '+self._host+' "whoami"')
		#if(status == 0):
			#self._remote_log_dir = "/gpfs/scratch/ecm86/" + user + "/" + expid
		#else:
			#self._remote_log_dir  = "\$HOME/LOG_"+expid
		self.check_remote_log_dir()
	
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
