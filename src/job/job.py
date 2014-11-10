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


import os
import re
from job_common import Status
from job_common import Type
from job_common import Template
from job_common import ArHeader
from job_common import BscHeader
from job_common import EcHeader
from job_common import HtHeader
from job_common import ItHeader
from job_common import MnHeader
from job_common import PsHeader
from job_common import StatisticsSnippet
import chunk_date_lib
from dir_config import LOCAL_ROOT_DIR
from dir_config import LOCAL_TMP_DIR
from dir_config import LOCAL_GIT_DIR

class Job:
	"""Class to handle all the tasks with Jobs at HPC.
	   A job is created by default with a name, a jobid, a status and a type.
	   It can have children and parents. The inheritance reflects the dependency between jobs.
	   If Job2 must wait until Job1 is completed then Job2 is a child of Job1. Inversely Job1 is a parent of Job2 """
  
	def __init__(self, name, id, status, jobtype):
		self._name = name
		self._long_name = name
		n = name.split('_')
		##workaround limit 15 characters limit for variables in headers (i.e. job name in hector and archer PBS pro header)
		if (len(n)==5):
			self._short_name = n[1][:6] + "_" + n[2][2:] + "_" + n[3] + n[4][:1]
		elif (len(n)==4):
			self._short_name = n[1][:6] + "_" + n[2][2:] + "_" + n[3][:1]
		elif (len(n)==2): 
			## this is wrong... if n[1] is larger than 15?
			self._short_name = n[1]
		else:
			self._short_name = n[0][:15]
		self._id = id
		self._status = status
		self._type = jobtype
		self._parents = list()
		self._children = list()
		self._fail_count = 0
		self._expid = n[0]
		self._complete = True
		self._parameters = dict()
		self._tmp_path = LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_TMP_DIR + "/"
	
	def delete(self):
		del self._name
		del self._long_name
		del self._short_name 
		del self._id
		del self._status
		del self._type
		del self._parents
		del self._children
		del self._fail_count
		del self._expid
		del self._complete
		del self._parameters
		del self._tmp_path
		del self

 	
	def print_job(self):
		print 'NAME: %s' % self._name 
		print 'JOBID: %s' % self._id 
		print 'STATUS: %s' % self._status
		print 'TYPE: %s' % self._type
		print 'PARENTS: %s' % [ p._name for p in self._parents ]
		print 'CHILDREN: %s' % [ c._name for c in self._children ]
		print 'FAIL_COUNT: %s' % self._fail_count
		print 'EXPID: %s' % self._expid 
 
 
	def get_name(self):
		"""Returns the job name"""
		return self._name

	def get_long_name(self):
		"""Returns the job long name"""
		## name is returned instead of long_name. Just to ensure backwards compatibility with experiments that does not have long_name attribute.
		if hasattr(self, '_long_name'):
			return self._long_name
		else:
			return self._name

	def get_short_name(self):
		"""Returns the job short name"""
		return self._short_name
 
	def get_id(self):
		"""Returns the job id"""
		return self._id
 
	def get_status(self):
		"""Returns the job status"""
		return self._status
 
	def get_type(self):
		"""Returns the job type"""
		return self._type

	def get_expid(self):
		return self._expid
 
	def get_parents(self):
		"""Returns a list with job's parents"""
		return self._parents

	def get_children(self):
		"""Returns a list with job's childrens"""
		return self._children

	def log_job(self):
		job_logger.info("%s\t%s\t%s" % ("Job Name","Job Id","Job Status"))
		job_logger.info("%s\t\t%s\t%s" % (self.name,self.id,self.status))

	def get_all_children(self):
		"""Returns a list with job's childrens and all it's descendents"""
		job_list = list()
		for job in self._children:
			job_list.append(job)
			job_list += job.get_all_children()
		# convert the list into a Set to remove duplicates and the again to a list
		return list(set(job_list))

	def get_fail_count(self):
		"""Returns the number	of	failures"""
		return self._fail_count
 
	def	get_parameters(self):
		''' Return the parameters list'''
		return	self._parameters
	
	def	set_parameters(self, newparameters):
		''' Set the parameters list'''
		self._parameters = newparameters  

	def print_parameters(self):
		print self._parameters
	
	def set_name(self, newName):
		self._name = newName

	def set_short_name(self, newName):
		n = newName.split('_')
		if (len(n)==5):
			self._short_name = n[1][:6] + "_" + n[2][2:] + "_" + n[3] + n[4][:1]
		elif (len(n)==4):
			self._short_name = n[1][:6] + "_" + n[2][2:] + "_" + n[3][:1]
		elif (len(n)==2): 
			self._short_name = n[1]
		else:
			self._short_name = n[0][:15]
 
	def set_id(self, new_id):
		self._id = new_id
 
	def set_status(self, new_status):
		self._status = new_status
  
	def set_expid(self, new_expid):
		self._expid = new_expid

	def set_type(self, new_type):
		self._type = new_type

	def set_parents(self, new_parents):
		self._parents = new_parents
 
	def set_children(self, new_children):
		self._children = new_children
 
	def set_fail_count(self, new_fail_count):
		self._fail_count = new_fail_count
	
	def inc_fail_count(self):
		self._fail_count += 1
	
	def add_parent(self, new_parent):
		self._parents += [new_parent]
 
	def add_children(self, new_children):
		self._children += [new_children]

	def delete_parent(self, parent):
		# careful, it is only possible to remove one parent at a time 
		self._parents.remove(parent)
 
	def delete_child(self, child):
		# careful it is only possible to remove one child at a time
		self._children.remove(child)

	def has_children(self):
		return self._children.__len__() 

	def has_parents(self):
		return self._parents.__len__() 

	def compare_by_status(self, other):
		return cmp(self.get_status(), other.get_status())
	
	def compare_by_type(self, other):
		return cmp(self.get_type(), other.get_type())

	def compare_by_id(self, other):
		return cmp(self.get_id(), other.get_id())
	
	def compare_by_name(self, other):
		return cmp(self.get_name(), other.get_name())

	def check_end_time(self):
		logname = self._tmp_path + self._name + '_COMPLETED'
		if(os.path.exists(logname)):
			return open(logname).readline().split()[0]
		else: 
			return 0

	def check_queued_time(self):
		logname = self._tmp_path + self._name + '_COMPLETED'
		if(os.path.exists(logname)):
			return open(logname).readline().split()[1]
		else: 
			return 0

	def check_run_time(self):
		logname = self._tmp_path + self._name + '_COMPLETED'
		if(os.path.exists(logname)):
			return open(logname).readline().split()[2]
		else: 
			return 0

	def check_failed_times(self):
		logname = self._tmp_path + self._name + '_COMPLETED'
		if(os.path.exists(logname)):
			return open(logname).readline().split()[3]
		else: 
			return 0
	
	def check_fail_queued_time(self):
		logname = self._tmp_path + self._name + '_COMPLETED'
		if(os.path.exists(logname)):
			return open(logname).readline().split()[4]
		else: 
			return 0

	def check_fail_run_time(self):
		logname = self._tmp_path + self._name + '_COMPLETED'
		if(os.path.exists(logname)):
			return open(logname).readline().split()[5]
		else: 
			return 0

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
			#job_logger.info("Job is completed, we are now removing the dependency in his %s child/children:" % self.has_children())
			for child in self.get_children():
				#job_logger.debug("number of Parents:", child.has_parents())
				if child.get_parents().__contains__(self):
					child.delete_parent(self)
		else:
			#job_logger.info("The checking in check_completion tell us that job %s has failed" % self.name)
			self.set_status(Status.FAILED)

	def update_parameters(self):
		parameters = self._parameters
		splittedname = self.get_long_name().split('_')
		parameters['JOBNAME'] = self._name
		
		if (self._type == Type.TRANSFER):
			parameters['SDATE'] = splittedname[1]
			string_date = splittedname[1]
			parameters['MEMBER'] = splittedname[2]
		elif (self._type == Type.INITIALISATION or self._type == Type.SIMULATION or self._type == Type.POSTPROCESSING or self._type == Type.CLEANING):
			parameters['SDATE'] = splittedname[1]
			string_date = splittedname[1]
			parameters['MEMBER'] = splittedname[2]
			if (self._type == Type.INITIALISATION):
				parameters['CHUNK'] = '1'
				chunk = 1
			else:
				parameters['CHUNK'] = splittedname[3]
				chunk = int(splittedname[3])
			total_chunk = int(parameters['NUMCHUNKS'])
			chunk_length_in_month = int(parameters['CHUNKSIZE'])
			chunk_start_date = chunk_date_lib.chunk_start_date(string_date,chunk,chunk_length_in_month)
			chunk_end_date = chunk_date_lib.chunk_end_date(chunk_start_date,chunk_length_in_month)
			run_days = chunk_date_lib.running_days(chunk_start_date,chunk_end_date)
			prev_days = chunk_date_lib.previous_days(string_date,chunk_start_date)
			chunk_end_days = chunk_date_lib.previous_days(string_date,chunk_end_date)
			day_before = chunk_date_lib.previous_day(string_date)
			chunk_end_date_1 = chunk_date_lib.previous_day(chunk_end_date)
			parameters['DAY_BEFORE'] = day_before
			parameters['Chunk_START_DATE'] = chunk_start_date
			parameters['Chunk_END_DATE'] = chunk_end_date_1
			parameters['RUN_DAYS'] = str(run_days)
			parameters['Chunk_End_IN_DAYS'] = str(chunk_end_days)
			
			chunk_start_month = chunk_date_lib.chunk_start_month(chunk_start_date)
			chunk_start_year = chunk_date_lib.chunk_start_year(chunk_start_date)
			  
			parameters['Chunk_START_YEAR'] = str(chunk_start_year)
			parameters['Chunk_START_MONTH'] = str(chunk_start_month)
			if total_chunk == chunk:
				parameters['Chunk_LAST'] = 'TRUE'
			else:
				parameters['Chunk_LAST'] = 'FALSE'
		  
		if (self._type == Type.SIMULATION):
			parameters['PREV'] = str(prev_days)
			parameters['WALLCLOCK'] = parameters['WALLCLOCK_SIM'] 
			parameters['NUMPROC'] = parameters['NUMPROC_SIM']
			parameters['TASKTYPE'] = 'SIMULATION'
		elif (self._type == Type.POSTPROCESSING):
			starting_date_year = chunk_date_lib.chunk_start_year(string_date)
			starting_date_month = chunk_date_lib.chunk_start_month(string_date)
			parameters['Starting_DATE_YEAR'] = str(starting_date_year)
			parameters['Starting_DATE_MONTH'] = str(starting_date_month)
			parameters['WALLCLOCK'] = parameters['WALLCLOCK_POST'] 
			parameters['NUMPROC'] = parameters['NUMPROC_POST']
			parameters['TASKTYPE'] = 'POSTPROCESSING'
		elif (self._type == Type.CLEANING):
			parameters['WALLCLOCK'] = parameters['WALLCLOCK_CLEAN'] 
			parameters['NUMPROC'] = parameters['NUMPROC_CLEAN']
			parameters['TASKTYPE'] = 'CLEANING'
		elif (self._type == Type.INITIALISATION):
			parameters['WALLCLOCK'] = parameters['WALLCLOCK_INI'] 
			parameters['NUMPROC'] = parameters['NUMPROC_INI']
			parameters['TASKTYPE'] = 'INITIALISATION'
		elif (self._type == Type.LOCALSETUP):
			parameters['TASKTYPE'] = 'LOCAL SETUP'
		elif (self._type == Type.REMOTESETUP):
			parameters['TASKTYPE'] = 'REMOTE SETUP'
			parameters['WALLCLOCK'] = parameters['WALLCLOCK_SETUP'] 
			parameters['NUMPROC'] = parameters['NUMPROC_SETUP']
		elif (self._type == Type.TRANSFER):
			parameters['TASKTYPE'] = 'TRANSFER'
		else: 
			print "Unknown Job Type"
		 
		parameters['FAIL_COUNT'] = str(self._fail_count)
		parameters['EXPID'] = parameters['EXPID'].upper()
		
		self._parameters = parameters 

		return parameters

	def update_content(self):
		localHeader = PsHeader

		if (self._parameters['HPCARCH'] == "bsc"):
			remoteHeader = BscHeader
		elif (self._parameters['HPCARCH'] == "ithaca"):
			remoteHeader = ItHeader
		elif (self._parameters['HPCARCH'] == "hector"):
			remoteHeader = HtHeader
		elif (self._parameters['HPCARCH'] == "archer"):
			remoteHeader = ArHeader
		elif (self._parameters['HPCARCH'] == "lindgren"):
			remoteHeader = LgHeader
		elif (self._parameters['HPCARCH'] == "ecmwf"):
			remoteHeader = EcHeader
		elif (self._parameters['HPCARCH'] == "marenostrum3"):
			remoteHeader = MnHeader

		template = Template()

		if (self._parameters['GIT_PROJECT'].lower() == "true"):
			template.read_localsetup_file(LOCAL_ROOT_DIR + "/" + self._expid + "/"  + LOCAL_GIT_DIR + "/" + self._parameters['GIT_FILE_LOCALSETUP'])
			template.read_remotesetup_file(LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_GIT_DIR + "/" + self._parameters['GIT_FILE_REMOTESETUP'])
			template.read_initialisation_file(LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_GIT_DIR + "/" + self._parameters['GIT_FILE_INI'])
			template.read_simulation_file(LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_GIT_DIR + "/" + self._parameters['GIT_FILE_SIM'])
			template.read_postprocessing_file(LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_GIT_DIR + "/" + self._parameters['GIT_FILE_POST'])
			template.read_cleaning_file(LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_GIT_DIR + "/" + self._parameters['GIT_FILE_CLEAN'])
			template.read_transfer_file(LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_GIT_DIR + "/" + self._parameters['GIT_FILE_TRANS'])

		if (self._type == Type.SIMULATION):
			items = [remoteHeader.HEADER_SIM]
			items.append(StatisticsSnippet.AS_HEADER_REM)
			items.append(template.SIMULATION)
			items.append(StatisticsSnippet.AS_TAILER_REM)
		elif (self._type == Type.POSTPROCESSING):
			items = [remoteHeader.HEADER_POST]
			items.append(StatisticsSnippet.AS_HEADER_REM)
			items.append(template.POSTPROCESSING)
			items.append(StatisticsSnippet.AS_TAILER_REM)
		elif (self._type == Type.CLEANING):
			items = [remoteHeader.HEADER_CLEAN]
			items.append(StatisticsSnippet.AS_HEADER_REM)
			items.append(template.CLEANING)
			items.append(StatisticsSnippet.AS_TAILER_REM)
		elif (self._type == Type.INITIALISATION):
			items = [remoteHeader.HEADER_INI]
			items.append(StatisticsSnippet.AS_HEADER_REM)
			items.append(template.INITIALISATION)
			items.append(StatisticsSnippet.AS_TAILER_REM)
		elif (self._type == Type.WRAPPING):
			items = [remoteHeader.HEADER_WRAPPING]
			items.append(StatisticsSnippet.AS_HEADER_REM)
			items.append(template.WRAPPING)
			items.append(StatisticsSnippet.AS_TAILER_REM)
		elif (self._type == Type.LOCALSETUP):
			items = [localHeader.HEADER_LOCALSETUP]
			items.append(StatisticsSnippet.AS_HEADER_LOC)
			items.append(template.LOCALSETUP)
			items.append(StatisticsSnippet.AS_TAILER_LOC)
		elif (self._type == Type.REMOTESETUP):
			items = [remoteHeader.HEADER_REMOTESETUP]
			items.append(StatisticsSnippet.AS_HEADER_REM)
			items.append(template.REMOTESETUP)
			items.append(StatisticsSnippet.AS_TAILER_REM)
		elif (self._type == Type.TRANSFER):
			items = [localHeader.HEADER_LOCALTRANS]
			items.append(StatisticsSnippet.AS_HEADER_LOC)
			items.append(template.TRANSFER)
			items.append(StatisticsSnippet.AS_TAILER_LOC)
		else: 
			print "Unknown Job Type"

		templateContent = ''.join(items)
		return templateContent

	def	create_script(self):
		parameters = self.update_parameters()
		templateContent = self.update_content()
		#print "jobType: %s" % self._type
		#print templateContent
		
		for key,value in parameters.items():
			#print "%s:\t%s" % (key,parameters[key])
			templateContent = templateContent.replace("%"+key+"%",parameters[key])

		scriptname = self._name+'.cmd'
		file(self._tmp_path + scriptname, 'w').write(templateContent)

		return scriptname
	
	def	check_script(self):
		parameters = self.update_parameters()
		templateContent = self.update_content()

		variables = re.findall('%'+'(\w+)'+'%', templateContent)
		#variables += re.findall('%%'+'(.+?)'+'%%', templateContent)
		out = set(parameters).issuperset(set(variables))

		if not out:
			print "The following set of variables to be substituted in template script is not part of parameters set: "
			print set(variables)-set(parameters)
		else:
			self.create_script()

		return out


if __name__ == "__main__":
	mainJob = Job('uno','1',Status.READY,0)
	job1 = Job('uno','1',Status.READY,0)
	job2 = Job('dos','2',Status.READY,0)
	job3 = Job('tres','3',Status.READY,0)
	jobs = [job1,job2,job3]
	mainJob.set_parents(jobs)
	print mainJob.get_parents()
	#mainJob.set_children(jobs)
	job1.add_children(mainJob)
	job2.add_children(mainJob)
	job3.add_children(mainJob)
	print mainJob.get_all_children();
	print mainJob.get_children()
	job3.check_completion() 
	print "Number of Parents: ", mainJob.has_parents()
	print "number of children : ", mainJob.has_children()
	mainJob.print_job()
	mainJob.delete()
	#mainJob.print_job()
