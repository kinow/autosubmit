#!/usr/bin/env python

from xml.dom.minidom import parseString
from hpcqueue import HPCQueue
from dir_config import LOCAL_ROOT_DIR
from time import sleep

class EcQueue(HPCQueue):
	def __init__(self, expid):
		self._host = "mn"
		self._scratch = "/scratch/ms"
		self._project = "spesiccf"
		self._user = "c1s"
		self._expid = expid
		self._remote_log_dir = self._scratch + "/" + self._project + "/" + self._user + "/" + self._expid + "/LOG_" + self._expid
		self._cancel_cmd = "eceaccess-job-delete"
		self._checkjob_cmd = "ecaccess-job-list"
		self._submit_cmd = "ecaccess-job-submit -queueName " + self._host + " " + LOCAL_ROOT_DIR + "/" + self._expid + "/tmp/"
		#self._submit_cmd = "ecaccess-job-submit -queueName c1a -distant " + self._remote_log_dir + "/"
		self._status_cmd = "ecaccess-job-get"
		self._put_cmd = "ecaccess-file-put"
		self._get_cmd = "ecaccess-file-get"
		self._mkdir_cmd = "ecaccess-file-mkdir " + self._host + ":" + self._scratch + "/" + self._project + "/" + self._user + "/" + self._expid + "; " + "ecaccess-file-mkdir " + self._host + ":" + self._remote_log_dir
		#self._mkdir_cmd = "ecaccess-file-mkdir " + self._expid + "; " + "ecaccess-file-mkdir " + self._remote_log_dir
		self._job_status = dict()
		self._job_status['COMPLETED'] = ['DONE']
		self._job_status['RUNNING'] = ['EXEC']
		self._job_status['QUEUING'] = ['INIT', 'RETR', 'STDBY', 'WAIT']
		self._job_status['FAILED'] = ['STOP']
		self._pathdir = "\$HOME/LOG_" + self._expid
	
	def update_cmds(self):
		self._remote_log_dir = self._scratch + "/" + self._project + "/" + self._user + "/" + self._expid + "/LOG_" + self._expid
		self._cancel_cmd = "eceaccess-job-delete"
		self._checkjob_cmd = "ecaccess-job-list"
		self._submit_cmd = "ecaccess-job-submit -queueName " + self._host + " " + LOCAL_ROOT_DIR + "/" + self._expid + "/tmp/"
		self._status_cmd = "ecaccess-job-get"
		self._put_cmd = "ecaccess-file-put"
		self._get_cmd = "ecaccess-file-get"
		self._mkdir_cmd = "ecaccess-file-mkdir " + self._host + ":" + self._scratch + "/" + self._project + "/" + self._user + "/" + self._expid + "; " + "ecaccess-file-mkdir " + self._host + ":" + self._remote_log_dir

	def get_submit_cmd(self):
		return self._submit_cmd

	def get_remote_log_dir(self):
		return self._remote_log_dir

	def get_mkdir_cmd(self):
		return self._mkdir_cmd

	def parse_job_output(self, output):
		job_state = output.split('\n')[6].split()[1]
		return job_state

	def get_submitted_job_id(self, output):
		return output

	def jobs_in_queue(self, output):
		print output
		return output.split()

def main():
	q = EcQueue()
	q.check_job(3431854)
	j = q.submit_job("/cfu/autosubmit/e000/templates/e000.sim")
	sleep(10)
	print q.check_job(j)
	q.cancel_job(j)
	
		
if __name__ == "__main__":
	main()
