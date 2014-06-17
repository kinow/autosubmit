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


import os
import datetime
from job_common import Status
from job_common import Type
from dir_config import LOCAL_ROOT_DIR
#LOCAL_ROOT_DIR = "/tmp"

class Wrap:
	"""Class to handle bundled tasks with Jobs at HPC.
	   A wrap is created by default with a name, a wrapid, a status and an expid. """
  
	def __init__(self, name, id, status, expid):
		self._name = name
		self._long_name = name
		self._short_name = name[:15]
		self._id = id
		self._status = status
		self._type = Type.WRAPPING
		self._fail_count = 0
		self._expid = expid
		self._jobs = list()
		self._complete = True
		self._parameters = dict()
		self._tmp_path = LOCAL_ROOT_DIR + "/" + self._expid + "/tmp/"
		self._template_path = LOCAL_ROOT_DIR + "/" + self._expid + "/git/templates/"
	
	def delete(self):
		del self._name
		del self._long_name
		del self._short_name 
		del self._id
		del self._status
		del self._type
		del self._fail_count
		del self._expid
		del self._jobs
		del self._complete
		del self._parameters
		del self._tmp_path
		del self

 	
	def print_wrap(self):
		print 'WRAPNAME: %s' % self._name 
		print 'WRAPID: %s' % self._id 
		print 'STATUS: %s' % self._status
		print 'TYPE: %s' % self._type
		print 'JOBS: %s' % [ j._name for j in self._jobs ]
		print 'FAIL_COUNT: %s' % self._fail_count
		print 'EXPID: %s' % self._expid 
 
 
	def get_name(self):
		"""Returns the wrap name"""
		return self._name

	def get_long_name(self):
		"""Returns the wrap long name"""
		## name is returned instead of long_name. Just to ensure backwards compatibility with experiments that does not have long_name attribute.
		if hasattr(self, '_long_name'):
			return self._long_name
		else:
			return self._name

	def get_short_name(self):
		"""Returns the wrap short name"""
		return self._short_name
 
	def get_id(self):
		"""Returns the wrap id"""
		return self._id
 
	def get_status(self):
		"""Returns the wrap status"""
		return self._status
 
	def get_type(self):
		"""Returns the wrap type"""
		return self._type

	def get_expid(self):
		return self._expid
 
	def log_wrap(self):
		job_logger.info("%s\t%s\t%s" % ("Wrap Name","Wrap Id","Wrap Status"))
		job_logger.info("%s\t\t%s\t%s" % (self.name,self.id,self.status))

	def get_fail_count(self):
		"""Returns the number of failures"""
		return self._fail_count
 
	def	get_parameters(self):
		''' Return the parameters list'''
		return	self._parameters
	
	def	set_parameters(self, newparameters):
		''' Set the parameters list'''
		self._parameters = newparameters  

	def print_parameters(self):
		print self._parameters

	def	get_jobs(self):
		''' Return the jobs list'''
		return	self._jobs
	
	def	get_jobnames(self):
		''' Return the list of job names'''
		jobnames = ""
		for job in self._jobs:
			jobnames += job.get_name() + " "
		return	jobnames
	
	def	set_jobs(self, newjobs):
		''' Set the jobs list'''
		self._jobs = newjobs  

	def print_jobs(self):
		print self._jobs
	
	def set_name(self, newName):
		self._name = newName

	def set_short_name(self, newName):
		self._short_name = newName[:15]
 
	def set_id(self, new_id):
		for job in self._jobs:
			job.set_id(new_id)
		self._id = new_id
 
	def set_status(self, new_status):
		for job in self._jobs:
			job.set_status(new_status)
		self._status = new_status
  
	def set_expid(self, new_expid):
		self._expid = new_expid

	def set_fail_count(self, new_fail_count):
		self._fail_count = new_fail_count
	
	def inc_fail_count(self):
		self._fail_count += 1
	
	def add_job(self, new_job):
		self._jobs += [new_job]
 
	def delete_job(self, job):
		# careful, it is only possible to remove one job at a time 
		self._jobs.remove(job)
 
	def has_jobs(self):
		return self._jobs.__len__() 

	def compare_by_status(self, other):
		return cmp(self.get_status(), other.get_status())
	
	def compare_by_id(self, other):
		return cmp(self.get_id(), other.get_id())
	
	def compare_by_name(self, other):
		return cmp(self.get_name(), other.get_name())

	def check_completion(self):
		''' Check the presence of *COMPLETED file and touch a Checked or failed file '''
		logname = self._tmp_path + self._name + '_COMPLETED'
		if(os.path.exists(logname)):
			self._complete=True
			os.system('touch ' + self._tmp_path + self._name + 'Checked')
			self._status = Status.COMPLETED
		else:
			os.system('touch ' + self._tmp_path + self._name + 'Failed')
			self._status = Status.FAILED
   
	def remove_dependencies(self):
		'''If Complete remove the dependency '''
		if (self._complete):
			self.set_status(Status.COMPLETED)
		else:
			#job_logger.info("The checking in check_completion tell us that job %s has failed" % self.name)
			self.set_status(Status.FAILED)

	def	create_script(self, templatename):
		parameters = self._parameters

		scriptname = self._name+'.cmd'
		parameters['JOBNAME'] = self._name
		print "jobType: %s" %str(self._type)
		mytemplate = self._template_path + templatename + '/' + templatename + '.wrapper'
		##update parameters
		r = datetime.datetime.strptime("00:00", "%H:%M")
		d1 = datetime.datetime.strptime(parameters['WALLCLOCK_SIM'], "%H:%M")
		dt1 = datetime.timedelta(hours=d1.hour,minutes=d1.minute)
		parameters['WALLCLOCK'] =  (r + dt1 * self.has_jobs()).strftime("%H:%M")
		parameters['NUMPROC'] = parameters['NUMPROC_SIM']
		#parameters['WALLCLOCK'] = '00:10'
		#parameters['NUMPROC'] = '10'
		parameters['TASKTYPE'] = 'WRAPPER'
		parameters['HEADER'] = parameters['HEADER_WRP']
		print "My Template: %s" % mytemplate
		templateContent = file(mytemplate).read()
		parameters['FAIL_COUNT'] = str(self._fail_count)
		parameters['TEMPLATE_NAME'] = parameters['TEMPLATE_NAME'].upper()
		#parameters['JOBS'] = str(self.has_jobs())
		parameters['JOBS'] = str(self.get_jobnames())
		print "Number of Jobs: ", self.has_jobs()

		# first value to be replaced is header as it contains inside other values between %% to be replaced later
		templateContent = templateContent.replace("%HEADER%",parameters['HEADER'])
		for key,value in parameters.items():
			if not key.startswith('HEADER') and key in templateContent:
				print "%s:\t%s" % (key,parameters[key])
				templateContent = templateContent.replace("%"+key+"%",parameters[key])

		self._parameters = parameters 
		file(self._tmp_path + scriptname, 'w').write(templateContent)
		return scriptname

if __name__ == "__main__":
	mainWrap = Wrap('uno','1',Status.READY,'w000')
	job1 = Job('uno','1',Status.READY,0)
	job2 = Job('dos','2',Status.READY,0)
	job3 = Job('tres','3',Status.READY,0)
	jobs = [job1,job2,job3]
	mainWrap.set_jobs(jobs)
	print mainWrap.get_jobs()
	job3.check_completion() 
	print "Number of Jobs: ", mainWrap.has_jobs()
	mainWrap.print_wrap()
	mainWrap.delete()
