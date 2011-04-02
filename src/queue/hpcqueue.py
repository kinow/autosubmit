#!/usr/bin/env python

from commands import getstatusoutput
from time import sleep
from job.job_common import Status
from sys import exit
from dir_config import LOCAL_ROOT_DIR

SLEEPING_TIME = 30

class HPCQueue:
	def cancel_job(self, job_id):
		print 'ssh ' + self._host + ' "' + self._cancel_cmd + ' ' + str(job_id) + '"'
		(status, output) = getstatusoutput('ssh '+self._host+' "'+self._cancel_cmd+' ' + str(job_id) + '"')
	
	def check_job(self, job_id, current_state):
		job_status = Status.UNKNOWN

		if type(job_id) is not int:
			# URi: logger
			print('check_job() The argument %s is not an integer.' % job_id)
			# URi: value ?
			return job_status 

		retry = 10;
		(status, output) = getstatusoutput('ssh ' + self._host + ' "' + self._checkjob_cmd + ' %s"' % str(job_id))
		print 'ssh '+self._host+' "'+self._checkjob_cmd+' %s"' % str(job_id)
		print status
		print output
		# retry infinitelly except if it was in the RUNNING state, because it can happen that we don't get a COMPLETE status from queue due to the 5 min lifetime
		while(status!=0 and retry>0):
			if(current_state == Status.RUNNING):
				retry -= 1
			print('Can not get job status, retrying in 10 sec\n');
			(status, output) = getstatusoutput('ssh ' + self._host + ' "' + self._checkjob_cmd + ' %s"' % str(job_id))
			print status
			print output
			# URi: logger
			sleep(10)

		if(status == 0):
			# URi: this command is specific of mn
			job_status = self.parse_job_output(output)
			# URi: define status list in HPC Queue Class
			if (job_status in self._job_status['COMPLETED'] or retry == 0):
				job_status = Status.COMPLETED
			elif (job_status in self._job_status['RUNNING']):
				job_status = Status.RUNNING
			elif (job_status in self._job_status['QUEUING']):
				job_status = Status.QUEUING
			elif (job_status in self._job_status['FAILED']):
				job_status = Status.FAILED
			else:
				job_status = Status.UNKNOWN
		else:
			####BOUOUOUOU	NOT	GOOD!
			job_status = Status.COMPLETED
		return job_status
	
	def	check_remote_log_dir(self):
		(status, output) = getstatusoutput('ssh '+self._host+' "mkdir -p ' + self._remote_log_dir + '"')
		print output
		if(status == 0):
			print '%s has been created on %s .' %(self._remote_log_dir, self._host)
		else:
			print 'Could not create the DIR on HPC' 
	
	def	send_script(self,job_script):
		(status, output) = getstatusoutput('scp ' + LOCAL_ROOT_DIR + "/" + self._expid + '/tmp/' + str(job_script) + ' ' + self._host + ':' + self._remote_log_dir + '/')
		if(status == 0):
   			print 'The script has been sent'
		else:	
			print 'The script has not been sent'
	
	def	get_completed_files(self,jobname):
		# wait five secons to check get file
		sleep(5)
		filename=jobname+'_COMPLETED'
		(status, output) = getstatusoutput('scp '+ self._host + ':' + self._remote_log_dir + '/'+filename + ' ' + LOCAL_ROOT_DIR + "/" + self._expid + '/tmp/')
		print 'scp '+ self._host + ':' +self._remote_log_dir + '/' + filename + ' ' + LOCAL_ROOT_DIR + "/" + self._expid + '/tmp/'
		if(status == 0):
			print 'The COMPLETED files have been transfered'
			return True
		else:	
			print 'Something did not work well when transferring the COMPLETED files'
			return False
	
	def submit_job(self, job_script):
		(status, output) = getstatusoutput('ssh ' + self._host + ' "' + self._submit_cmd +' ' + self._remote_log_dir + '/' + str(job_script) + '"')
		print 'ssh ' + self._host + ' "' + self._submit_cmd + ' ' + self._remote_log_dir + '/' + str(job_script)
		if(status == 0):
			job_id = self.get_submitted_job_id(output)
			print job_id
			return int(job_id)

	def normal_stop(self,	signum,	frame):
		sleep(SLEEPING_TIME)
		(status, output) = getstatusoutput('ssh ' + self._host + ' "' + self._status_cmd	+ ' "')
		for job_id in self.jobs_in_queue(output):
			self.cancel_job(job_id)
			
		exit(0)

	def smart_stop(self,	signum,	frame):
		sleep(SLEEPING_TIME)
		(status, output) = getstatusoutput('ssh ' + self._host + ' "' + self._status_cmd	+ ' "')
		print self.jobs_in_queue(output)
		while self.jobs_in_queue(output):
			print	self.jobs_in_queue(output)
			sleep(SLEEPING_TIME)
			(status, output) = getstatusoutput('ssh ' + self._host + ' "' + self._status_cmd	+ ' "')
		exit(0)
