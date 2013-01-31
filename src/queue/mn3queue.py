#!/usr/bin/env python

from xml.dom.minidom import parseString
from hpcqueue import HPCQueue
from time import sleep

class Mn3Queue(HPCQueue):
	def __init__(self, expid):
		self._host = "mn"
		self._expid = expid
		self._remote_log_dir = "/gpfs/scratch/ecm86/\$USER/" + self._expid + "/LOG_" + self._expid
		self._cancel_cmd = "ssh " + self._host + " bkill"
		self._checkjob_cmd = "ssh " + self._host + " bjobs"
		self._submit_cmd = "ssh " + self._host + " /gpfs/projects/ecm86/common/autosubmit/bsub.sh " + self._remote_log_dir + "/" 
		self._status_cmd = "ssh " + self._host + " bjobs -w -X"
		self._put_cmd = "scp"
		self._get_cmd = "scp"
		self._mkdir_cmd = "ssh " + self._host + " mkdir -p " + self._remote_log_dir
		self._job_status = dict()
		#        RUN        SSUSP       USUSP      UNKNOWN    PEND FWD_PEND
		self._job_status['COMPLETED'] = ['DONE']
		self._job_status['RUNNING'] = ['RUN']
		self._job_status['QUEUING'] = ['PEND', 'FW_PEND']
		self._job_status['FAILED'] = ['SSUSP', 'USUSP', 'EXIT']

	def get_submit_cmd(self):
		self._submit_cmd = "ssh " + self._host + " /gpfs/projects/ecm86/common/autosubmit/bsub.sh " + self._remote_log_dir + "/" 
		return self._submit_cmd

	def get_remote_log_dir(self):
		self._remote_log_dir = "/gpfs/scratch/ecm86/\$USER/" + self._expid + "/LOG_" + self._expid
		return self._remote_log_dir

	def get_mkdir_cmd(self):
		self._mkdir_cmd = "ssh " + self._host + " mkdir -p " + self._remote_log_dir
		return self._mkdir_cmd
	
	def parse_job_output(self, output):
		job_state = output.split('\n')[1].split()[2]
		return job_state

	def get_submitted_job_id(self, output):
		return output.split('<')[1].split('>')[0]
	
	def jobs_in_queue(self,	output):
		return zip(*[ line.split() for line in output.split('\n') ])[0][1:]
