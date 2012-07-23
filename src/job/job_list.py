#!/usr/bin/env python

from job_common import Status
from job_common import Type
from job import Job
import os
import pickle
from sys import	exit, setrecursionlimit
from dir_config import LOCAL_ROOT_DIR
from shutil import move
from time import localtime, strftime
import json

class JobList:
	
	def __init__(self, expid):
		self._pkl_path = LOCAL_ROOT_DIR + "/" + expid + "/pkl/"
		self._update_file = "updated_list_" + expid + ".txt"
		self._failed_file = "failed_job_list_" + expid + ".pkl"
		self._job_list_file = "job_list_" + expid + ".pkl"
		self._job_list = list()
		self._expid = expid
		self._stat_val = Status()

	def create(self, date_list, member_list, starting_chunk, num_chunks, parameters):
		print "Creating job list\n"
		for date in date_list:
			print date
			for member in member_list:
				print member
				for	chunk in range(starting_chunk, starting_chunk + num_chunks):
					rootjob_name = self._expid + "_" + str(date) + "_" + str(member) + "_" + str(chunk) + "_"
					post_job = Job(rootjob_name + "post", 0, Status.WAITING, Type.POSTPROCESSING)
					clean_job = Job(rootjob_name + "clean", 0, Status.WAITING, Type.CLEANING)
					if	(starting_chunk	== chunk and chunk != 1):
						sim_job = Job(rootjob_name + "sim", 0, Status.READY, Type.SIMULATION)
					else:
						sim_job = Job(rootjob_name + "sim", 0, Status.WAITING, Type.SIMULATION)
						
					# set dependency of postprocessing jobs
					post_job.set_parents([sim_job.get_name()])
					post_job.set_children([clean_job.get_name()])
					# set parents of clean job
					clean_job.set_parents([post_job.get_name()])
					# set first child of simulation job
					sim_job.set_children([post_job.get_name()])
					
					# set status of first chunk to READY
					if (chunk > 1):
						parentjob_name = self._expid + "_" + str(date) + "_" + str(member) + "_" + str(chunk-1) + "_" + "sim"
						sim_job.set_parents([parentjob_name])
						if (chunk > 2):
							parentjob_name = self._expid + "_" + str(date) + "_" + str(member) + "_" + str(chunk-2) + "_" + "clean"
							sim_job.add_parent(parentjob_name)
					if (chunk == 1):
						init_job = Job(rootjob_name + "init", 0, Status.READY, Type.INITIALISATION)
						init_job.set_children([sim_job.get_name()])
						init_job.set_parents([])
						sim_job.set_parents([init_job.get_name()])
						self._job_list += [init_job]
					if (chunk < starting_chunk + num_chunks	- 1):
						childjob_name = self._expid + "_" + str(date) + "_" + str(member) + "_" + str(chunk+1) + "_" + "sim"
						sim_job.add_children(childjob_name)
					if (chunk < starting_chunk + num_chunks - 2):
						childjob_name = self._expid+ "_" + str(date) + "_" + str(member) + "_" + str(chunk+2) + "_" + "sim"
						clean_job.set_children([childjob_name])

					self._job_list += [sim_job, post_job, clean_job]

		self.update_genealogy()
		for job in self._job_list:
			job.set_parameters(parameters)


	def	__len__(self):
		return	self._job_list.__len__()

	def	get_job_list(self):
		return	self._job_list
			
	def get_completed(self):
		"""Returns a list of completed jobs"""
		return [job for job in self._job_list if job.get_status() == Status.COMPLETED]

	def get_submitted(self):
		"""Returns a list of submitted jobs"""
		return [job for job in self._job_list if job.get_status() == Status.SUBMITTED]

	def get_running(self):
		"""Returns a list of jobs running"""
		return [job for job in self._job_list if job.get_status() == Status.RUNNING]

	def get_queuing(self):
		"""Returns a list of jobs queuing"""
		return [job for job in self._job_list if job.get_status() == Status.QUEUING]

	def get_failed(self):
		"""Returns a list of failed jobs"""
		return [job for job in self._job_list if job.get_status() == Status.FAILED]

	def get_ready(self):
		"""Returns a list of jobs ready"""
		return [job for job in self._job_list if job.get_status() == Status.READY]

	def get_waiting(self):
		"""Returns a list of jobs waiting"""
		return [job for job in self._job_list if job.get_status() == Status.WAITING]

	def get_unknown(self):
		"""Returns a list of jobs unknown"""
		return [job for job in self._job_list if job.get_status() == Status.UNKNOWN]

	def get_in_queue(self):
		"""Returns a list of jobs in the queue (Submitted, Running, Queuing)"""
		return self.get_submitted() + self.get_running() + self.get_queuing()

	def get_not_in_queue(self):
		"""Returns a list of jobs NOT in the queue (Ready, Waiting)"""
		return self.get_ready() + self.get_waiting()

	def get_finished(self):
		"""Returns a list of jobs finished (Completed, Failed)"""
		return self.get_completed() + self.get_failed()

	def get_active(self):
		"""Returns a list of active jobs (In queue, Ready)"""
		return self.get_in_queue() + self.get_ready() + self.get_unknown()
	
	def get_job_by_name(self, name):
		"""Returns the job that its name matches name"""
		for job in self._job_list:
			if job.get_name() == name:
				return job
		print "We could not find that job %s in the list!!!!" % name
	
	def sort_by_name(self):
		return sorted(self._job_list, key=lambda k:k.get_name())
	
	def sort_by_id(self):
		return sorted(self._job_list, key=lambda k:k.get_id())

	def sort_by_type(self):
		return sorted(self._job_list, key=lambda k:k.get_type())
	
	def sort_by_status(self):
		return sorted(self._job_list, key=lambda k:k.get_status())
	
	def load_file(self, filename):
		if(os.path.exists(filename)):
			return pickle.load(file(filename, 'r'))
		else:
			# URi: print ERROR
			return list()
		 
	def load(self):
		print "Loading JobList: " + self._pkl_path + self._job_list_file
		return	load_file(self,self._pkl_path + self._job_list_file)
		
	def load_updated(self):
		print "Loading updated list: " + self._pkl_path + self._update_file
		return self.load_file(self._pkl_path + self._update_file)

	def load_failed(self):
		print "Loading failed list: " + self._pkl_path + self._failed_file
		return self.load_file(self._pkl_path + self._failed_file)

	def save_failed(self, failed_list):
		# URi: should we check that the path exists?
		print "Saving failed list: " + self._pkl_path + self._failed_file
		pickle.dump(failed_list, file(self._pkl_path + self._failed_file, 'w'))
	
	def save(self):
		# URi: should we check that the path exists?
		setrecursionlimit(50000)
		print "Saving JobList: " + self._pkl_path + self._job_list_file
		pickle.dump(self, file(self._pkl_path + self._job_list_file, 'w'))
	
	def update_from_file(self, store_change=True):
		if(os.path.exists(self._pkl_path + self._update_file)):
			for line in open (self._pkl_path + self._update_file):
				if(self.get_job_by_name(line.split()[0])):
					self.get_job_by_name(line.split()[0]).set_status(self._stat_val.retval(line.split()[1]))
					self.get_job_by_name(line.split()[0]).set_fail_count(0)
			now = localtime()
			output_date = strftime("%Y%m%d_%H%M", now) 
			if(store_change):
				move(self._pkl_path + self._update_file, self._pkl_path + self._update_file + "_" + output_date)

	def update_list(self):
		# load updated file list
		self.update_from_file()
		
		# reset jobs that has failed less than 4 times
		for job in self.get_failed():
			job.inc_fail_count()
			if job.get_fail_count() < 4:
				job.set_status(Status.READY)
		
		# if waiting jobs has all parents completed change its State to READY
		for job in self.get_waiting():
			tmp = [parent for parent in job.get_parents() if parent.get_status() == Status.COMPLETED]
			#for parent in job.get_parents():				
				#if parent.get_status() != Status.COMPLETED:
				#	break
			if len(tmp) == len(job.get_parents()):
				job.set_status(Status.READY)
		self.save()
			
	def update_genealogy(self):
		"""When we have created the joblist, parents and child list just contain the names. Update the genealogy replacing job names by the corresponding job object"""
		for job in self._job_list:
			if job.has_children():
				# get the list of childrens (names)
				child_list = job.get_children()
				# remove the list of names
				job.set_children([])
				# for each child find the corresponding job
				for child in child_list:
					if isinstance(child, str):
						job_object = self.get_job_by_name(child)
						job.add_children(job_object)
					else:
						job.add_children(child)

			if job.has_parents():
				# get the list of childrens (names)
				parent_list = job.get_parents()
				# remove the list of names
				job.set_parents([])
				# for each child find the corresponding job
				for parent in parent_list:
					if isinstance(parent, str):
						job_object = self.get_job_by_name(parent)
						job.add_parent(job_object)
					else:
						job.add_parent(parent)
						
	def check_genealogy(self):
		"""When we have updated the joblist, parents and child list must be consistent"""
		pass

class FailedJobList:
	
	def __init__(self, expid):
		self._pkl_path = LOCAL_ROOT_DIR + "/" + expid + "/pkl/"
		self._update_file = "updated_list_" + expid + ".txt"
		self._failed_file = "failed_job_list_" + expid + ".pkl"
		self._job_list_file = "failed_job_list_" + expid + ".pkl"
		self._job_list = list()
		self._expid = expid
		self._stat_val = Status()

	def create(self, chunk_list, parameters):
		print "Creating job list\n"
		data = json.loads(chunk_list)
		print data
		for date in data['sds']:
			print date['sd']
			for member in date['ms']:
				print member['m']
				starting_chunk = int(member['cs'][0])
				if (len(member['cs']) > 1):
					last_chunk = int(member['cs'][len(member['cs'])-1])
				else:
					last_chunk = starting_chunk
				for	chunk in member['cs']:
					print chunk
					chunk = int(chunk)
					rootjob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(chunk) + "_"
					post_job = Job(rootjob_name + "post", 0, Status.WAITING, Type.POSTPROCESSING)
					clean_job = Job(rootjob_name + "clean", 0, Status.WAITING, Type.CLEANING)
					sim_job = Job(rootjob_name + "sim", 0, Status.WAITING, Type.SIMULATION)
						
					# set dependency of postprocessing jobs
					post_job.set_parents([sim_job.get_name()])
					post_job.set_children([clean_job.get_name()])
					# set parents of clean job
					clean_job.set_parents([post_job.get_name()])
					# set first child of simulation job
					sim_job.set_children([post_job.get_name()])
					
					# set status of first chunk to READY
					if (chunk > starting_chunk):
						prev_chunk = member['cs'][member['cs'].index(str(chunk))-1]
						parentjob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(prev_chunk) + "_" + "clean"
						sim_job.set_parents([parentjob_name])
					if (chunk == starting_chunk):
						init_job = Job(rootjob_name + "init", 0, Status.READY, Type.INITIALISATION)
						init_job.set_children([sim_job.get_name()])
						init_job.set_parents([])
						sim_job.set_parents([init_job.get_name()])
						self._job_list += [init_job]
					if (chunk < last_chunk): ####REVISAR <--- ###
						next_chunk = member['cs'][member['cs'].index(str(chunk))+1]
						childjob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(next_chunk) + "_" + "sim"
						clean_job.add_children(childjob_name)

					self._job_list += [sim_job, post_job, clean_job]

		self.update_genealogy()
		for job in self._job_list:
			job.set_parameters(parameters)


	def	__len__(self):
		return	self._job_list.__len__()

	def	get_job_list(self):
		return	self._job_list
			
	def get_completed(self):
		"""Returns a list of completed jobs"""
		return [job for job in self._job_list if job.get_status() == Status.COMPLETED]

	def get_submitted(self):
		"""Returns a list of submitted jobs"""
		return [job for job in self._job_list if job.get_status() == Status.SUBMITTED]

	def get_running(self):
		"""Returns a list of jobs running"""
		return [job for job in self._job_list if job.get_status() == Status.RUNNING]

	def get_queuing(self):
		"""Returns a list of jobs queuing"""
		return [job for job in self._job_list if job.get_status() == Status.QUEUING]

	def get_failed(self):
		"""Returns a list of failed jobs"""
		return [job for job in self._job_list if job.get_status() == Status.FAILED]

	def get_ready(self):
		"""Returns a list of jobs ready"""
		return [job for job in self._job_list if job.get_status() == Status.READY]

	def get_waiting(self):
		"""Returns a list of jobs waiting"""
		return [job for job in self._job_list if job.get_status() == Status.WAITING]

	def get_unknown(self):
		"""Returns a list of jobs unknown"""
		return [job for job in self._job_list if job.get_status() == Status.UNKNOWN]

	def get_in_queue(self):
		"""Returns a list of jobs in the queue (Submitted, Running, Queuing)"""
		return self.get_submitted() + self.get_running() + self.get_queuing()

	def get_not_in_queue(self):
		"""Returns a list of jobs NOT in the queue (Ready, Waiting)"""
		return self.get_ready() + self.get_waiting()

	def get_finished(self):
		"""Returns a list of jobs finished (Completed, Failed)"""
		return self.get_completed() + self.get_failed()

	def get_active(self):
		"""Returns a list of active jobs (In queue, Ready)"""
		return self.get_in_queue() + self.get_ready() + self.get_unknown()
	
	def get_job_by_name(self, name):
		"""Returns the job that its name matches name"""
		for job in self._job_list:
			if job.get_name() == name:
				return job
		print "We could not find that job %s in the list!!!!" % name
	
	def sort_by_name(self):
		return sorted(self._job_list, key=lambda k:k.get_name())
	
	def sort_by_id(self):
		return sorted(self._job_list, key=lambda k:k.get_id())

	def sort_by_type(self):
		return sorted(self._job_list, key=lambda k:k.get_type())
	
	def sort_by_status(self):
		return sorted(self._job_list, key=lambda k:k.get_status())
	
	def load_file(self, filename):
		if(os.path.exists(filename)):
			return pickle.load(file(filename, 'r'))
		else:
			# URi: print ERROR
			return list()
		 
	def load(self):
		print "Loading JobList: " + self._pkl_path + self._job_list_file
		return	load_file(self,self._pkl_path + self._job_list_file)
		
	def load_updated(self):
		print "Loading updated list: " + self._pkl_path + self._update_file
		return self.load_file(self._pkl_path + self._update_file)

	def load_failed(self):
		print "Loading failed list: " + self._pkl_path + self._failed_file
		return self.load_file(self._pkl_path + self._failed_file)

	def save_failed(self, failed_list):
		# URi: should we check that the path exists?
		print "Saving failed list: " + self._pkl_path + self._failed_file
		pickle.dump(failed_list, file(self._pkl_path + self._failed_file, 'w'))
	
	def save(self):
		# URi: should we check that the path exists?
		setrecursionlimit(50000)
		print "Saving JobList: " + self._pkl_path + self._job_list_file
		pickle.dump(self, file(self._pkl_path + self._job_list_file, 'w'))
	
	def update_from_file(self, store_change=True):
		if(os.path.exists(self._pkl_path + self._update_file)):
			for line in open (self._pkl_path + self._update_file):
				if(self.get_job_by_name(line.split()[0])):
					self.get_job_by_name(line.split()[0]).set_status(self._stat_val.retval(line.split()[1]))
					self.get_job_by_name(line.split()[0]).set_fail_count(0)
			now = localtime()
			output_date = strftime("%Y%m%d_%H%M", now) 
			if(store_change):
				move(self._pkl_path + self._update_file, self._pkl_path + self._update_file + "_" + output_date)

	def update_list(self):
		# load updated file list
		self.update_from_file()
		
		# reset jobs that has failed less than 4 times
		for job in self.get_failed():
			job.inc_fail_count()
			if job.get_fail_count() < 4:
				job.set_status(Status.READY)
		
		# if waiting jobs has all parents completed change its State to READY
		for job in self.get_waiting():
			tmp = [parent for parent in job.get_parents() if parent.get_status() == Status.COMPLETED]
			#for parent in job.get_parents():				
				#if parent.get_status() != Status.COMPLETED:
				#	break
			if len(tmp) == len(job.get_parents()):
				job.set_status(Status.READY)
		self.save()
			
	def update_genealogy(self):
		"""When we have created the joblist, parents and child list just contain the names. Update the genealogy replacing job names by the corresponding job object"""
		for job in self._job_list:
			if job.has_children():
				# get the list of childrens (names)
				child_list = job.get_children()
				# remove the list of names
				job.set_children([])
				# for each child find the corresponding job
				for child in child_list:
					if isinstance(child, str):
						job_object = self.get_job_by_name(child)
						job.add_children(job_object)
					else:
						job.add_children(child)

			if job.has_parents():
				# get the list of childrens (names)
				parent_list = job.get_parents()
				# remove the list of names
				job.set_parents([])
				# for each child find the corresponding job
				for parent in parent_list:
					if isinstance(parent, str):
						job_object = self.get_job_by_name(parent)
						job.add_parent(job_object)
					else:
						job.add_parent(parent)
						
	def check_genealogy(self):
		"""When we have updated the joblist, parents and child list must be consistent"""
		pass
