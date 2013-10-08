#!/usr/bin/env python
import os
from job_common import Status
from job_common import Type
from sets import Set
import chunk_date_lib
from dir_config import LOCAL_ROOT_DIR

class Job:
	"""Class to handle all the tasks with Jobs at HPC.
	   A job is created by default with a name, a jobid, a status and a type.
	   It can have children and parents. The inheritance reflects the dependency between jobs.
	   If Job2 must wait until Job1 is completed then Job2 is a child of Job1. Inversely Job1 is a parent of Job2 """
  
	def __init__(self, name, id, status, jobtype):
		self._name = name
		self._long_name = name
		n = name.split('_')
		##workaround limit 15 characters limit for variables in headers (i.e. job name in hector PBS pro header)
		if (len(n)==5):
			self._short_name = n[1][:6] + "_" + n[2][2:] + "_" + n[3] + n[4][:1]
		elif (len(n)==4):
			self._short_name = n[1][:6] + "_" + n[2][2:] + "_" + n[3][:1]
		elif (len(n)==2): 
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
		self._tmp_path = LOCAL_ROOT_DIR + "/" + self._expid + "/tmp/"
		self._template_path = LOCAL_ROOT_DIR + "/" + self._expid + "/templates/"
	
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
		return list(Set(job_list))

	def get_fail_count(self):
		"""Returns the number	of	failures"""
		return self._fail_count
 
	def	get_parameters(self):
		''' Return the parameters list'''
		return	self._parameters
	
	def	set_parameters(self, newparameters):
		''' Set the parameters list'''
		self._parameters = newparameters  
	
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

	def	create_script(self, templatename):
		parameters = self._parameters

		templatename = self._template_path + templatename
		splittedname = self.get_long_name().split('_')
		scriptname = self._name+'.cmd'
		parameters['JOBNAME'] = self._name
		
		if (self._type == Type.TRANSFER):
			parameters['SDATE'] = splittedname[1]
			string_date = splittedname[1]
			parameters['MEMBER'] = splittedname[2]
		elif (self._type == Type.SIMULATION or self._type == Type.INITIALISATION or self._type == Type.POSTPROCESSING or self._type == Type.CLEANING):
			parameters['SDATE'] = splittedname[1]
			string_date = splittedname[1]
			parameters['MEMBER'] = splittedname[2]
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
			print "jobType: %s" %str(self._type)
			mytemplate = templatename + '.sim'
			##update parameters
			parameters['PREV'] = str(prev_days)
			parameters['WALLCLOCK'] = parameters['WALLCLOCK_SIM'] 
			parameters['NUMPROC'] = parameters['NUMPROC_SIM']
			parameters['TASKTYPE'] = 'SIMULATION'
			parameters['HEADER'] = parameters['HEADER_SIM']
		elif (self._type == Type.POSTPROCESSING):
			print "jobType: %s " % str(self._type)
			mytemplate = templatename + '.post'
			##update parameters
			starting_date_year = chunk_date_lib.chunk_start_year(string_date)
			starting_date_month = chunk_date_lib.chunk_start_month(string_date)
			parameters['Starting_DATE_YEAR'] = str(starting_date_year)
			parameters['Starting_DATE_MONTH'] = str(starting_date_month)
			parameters['WALLCLOCK'] = parameters['WALLCLOCK_POST'] 
			parameters['NUMPROC'] = parameters['NUMPROC_POST']
			parameters['TASKTYPE'] = 'POSTPROCESSING'
			parameters['HEADER'] = parameters['HEADER_POST']
		elif (self._type == Type.CLEANING):
			print "jobType: %s" % str(self._type)
			##update parameters
			mytemplate = templatename + '.clean'
			parameters['WALLCLOCK'] = parameters['WALLCLOCK_CLEAN'] 
			parameters['NUMPROC'] = parameters['NUMPROC_CLEAN']
			parameters['TASKTYPE'] = 'CLEANING'
			parameters['HEADER'] = parameters['HEADER_CLEAN']
		elif (self._type == Type.INITIALISATION):
			print "jobType: %s" % self._type
			##update parameters
			mytemplate = templatename + '.ini'
			parameters['WALLCLOCK'] = parameters['WALLCLOCK_INI'] 
			parameters['NUMPROC'] = parameters['NUMPROC_INI']
			parameters['TASKTYPE'] = 'INITIALISATION'
			parameters['HEADER'] = parameters['HEADER_INI']
		elif (self._type == Type.LOCALSETUP):
			print "jobType: %s" % self._type
			##update parameters
			mytemplate = templatename + '.localsetup'
			parameters['TASKTYPE'] = 'LOCAL SETUP'
			parameters['HEADER'] = parameters['HEADER_LOCALSETUP']
		elif (self._type == Type.REMOTESETUP):
			print "jobType: %s" % self._type
			##update parameters
			mytemplate = templatename + '.remotesetup'
			parameters['WALLCLOCK'] = parameters['WALLCLOCK_SETUP'] 
			parameters['NUMPROC'] = parameters['NUMPROC_SETUP']
			parameters['TASKTYPE'] = 'REMOTE SETUP'
			parameters['HEADER'] = parameters['HEADER_REMOTESETUP']
		elif (self._type == Type.TRANSFER):
			print "jobType: %s" % self._type
			##update parameters
			mytemplate = templatename + '.localtrans'
			parameters['TASKTYPE'] = 'TRANSFER'
			parameters['HEADER'] = parameters['HEADER_LOCALTRANS']
		else: 
			print "Unknown Job Type"
		 
		print "My Template: %s" % mytemplate
		#templateContent = file(hpcarch).read()
		templateContent = file(mytemplate).read()
		#parameters['MODEL'] = str(templatename).upper()
		parameters['TASKTYPE'] = str(self._type)
		parameters['FAIL_COUNT'] = str(self._fail_count)
		# first value to be replaced is header as it contains inside other values between %% to be replaced later
		templateContent = templateContent.replace("%HEADER%",parameters['HEADER'])
		params = dict()
		for key,value in parameters.items():
			if value != 'HEADER':
				params[key] = value

		# use params dictionary to do not replace twice the header
		for key in params.keys():
			if key in templateContent:
				print "%s:\t%s" % (key,params[key])
				templateContent = templateContent.replace("%"+key+"%",params[key])
		
		self.parameters = parameters 
		file(self._tmp_path + scriptname, 'w').write(templateContent)
		return scriptname

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
