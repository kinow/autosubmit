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


from commands import getstatusoutput
from time import sleep
from job.job_common import Status
from sys import exit
from dir_config import LOCAL_ROOT_DIR

SLEEPING_TIME = 30

class HPCQueue:
	def cancel_job(self, job_id):
		print self._cancel_cmd + ' ' + str(job_id)
		(status, output) = getstatusoutput(self._cancel_cmd+' ' + str(job_id))
	
	def check_job(self, job_id, current_state):
		job_status = Status.UNKNOWN

		if type(job_id) is not int:
			# URi: logger
			print('check_job() The argument %s is not an integer.' % job_id)
			# URi: value ?
			return job_status 

		retry = 10;
		(status, output) = getstatusoutput(self._checkjob_cmd + ' %s' % str(job_id))
		print self._checkjob_cmd + ' %s' % str(job_id)
		print status
		print output
		# retry infinitelly except if it was in the RUNNING state, because it can happen that we don't get a COMPLETE status from queue due to the 5 min lifetime
		while(status!=0 and retry>0):
			#if(current_state == Status.RUNNING):
			retry -= 1
			print('Can not get job status, retrying in 10 sec\n');
			(status, output) = getstatusoutput(self._checkjob_cmd + ' %s' % str(job_id))
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
	
	def check_host(self):
		(status, output) = getstatusoutput(self.get_checkhost_cmd())
		if(status == 0):
			print 'The host ' + self._host + ' is up'
			return True
		else:
			print 'The host ' + self._host + ' is down'
			return False
	
	def	check_remote_log_dir(self):
		(status, output) = getstatusoutput(self.get_mkdir_cmd())
		print self._mkdir_cmd
		print output
		if(status == 0):
			print '%s has been created on %s .' %(self._remote_log_dir, self._host)
		else:
			print 'Could not create the DIR on HPC' 
	
	def	send_script(self,job_script):
		(status, output) = getstatusoutput(self._put_cmd + ' ' + LOCAL_ROOT_DIR + "/" + self._expid + '/tmp/' + str(job_script) + ' ' + self._host + ':' + self._remote_log_dir + "/" + str(job_script))
		print self._put_cmd + ' ' + LOCAL_ROOT_DIR + "/" + self._expid + '/tmp/' + str(job_script) + ' ' + self._host + ':' + self._remote_log_dir + "/" + str(job_script)
		if(status == 0):
   			print 'The script has been sent'
		else:	
			print 'The script has not been sent'
	
	def	get_completed_files(self,jobname):
		# wait five secons to check get file
		sleep(5)
		filename=jobname+'_COMPLETED'
		(status, output) = getstatusoutput(self._get_cmd + ' '+ self._host + ':' + self._remote_log_dir + '/' + filename + ' ' + LOCAL_ROOT_DIR + "/" + self._expid + '/tmp/' + filename)
		print self._get_cmd + ' '+ self._host + ':' +self._remote_log_dir + '/' + filename + ' ' + LOCAL_ROOT_DIR + "/" + self._expid + '/tmp/' + filename
		if(status == 0):
			print 'The COMPLETED files have been transfered'
			return True
		else:	
			print 'Something did not work well when transferring the COMPLETED files'
			return False
	
	def submit_job(self, job_script):
		(status, output) = getstatusoutput(self._submit_cmd + str(job_script))
		print self._submit_cmd + str(job_script)
		if(status == 0):
			job_id = self.get_submitted_job_id(output)
			print job_id
			return int(job_id)

	def normal_stop(self,	signum,	frame):
		sleep(SLEEPING_TIME)
		(status, output) = getstatusoutput(self._checkjob_cmd + ' ')
		for job_id in self.jobs_in_queue(output):
			self.cancel_job(job_id)
			
		exit(0)

	def smart_stop(self,	signum,	frame):
		sleep(SLEEPING_TIME)
		(status, output) = getstatusoutput(self._checkjob_cmd + ' ')
		print self.jobs_in_queue(output)
		while self.jobs_in_queue(output):
			print	self.jobs_in_queue(output)
			sleep(SLEEPING_TIME)
			(status, output) = getstatusoutput(self._checkjob_cmd + ' ')
		exit(0)
	
	def set_host(self, new_host):
		self._host = new_host
	
	def set_scratch(self, new_scratch):
		self._scratch = new_scratch
		
	def set_project(self, new_project):
		self._project = new_project

	def set_user(self, new_user):
		self._user = new_user

	def set_remote_log_dir(self, new_remote_log_dir):
		self._remote_log_dir = new_remote_log_dir

