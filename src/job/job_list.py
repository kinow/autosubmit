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
import pickle
from time import localtime, strftime
from sys import	setrecursionlimit
from shutil import move
import json
from job_common import Status
from job_common import Type
from job import Job
from dir_config import LOCAL_ROOT_DIR

class JobList:
	
	def __init__(self, expid):
		self._pkl_path = LOCAL_ROOT_DIR + "/" + expid + "/pkl/"
		self._update_file = "updated_list_" + expid + ".txt"
		self._failed_file = "failed_job_list_" + expid + ".pkl"
		self._job_list_file = "job_list_" + expid + ".pkl"
		self._job_list = list()
		self._expid = expid
		self._stat_val = Status()
		self._parameters = []

	def create(self, date_list, member_list, starting_chunk, num_chunks, parameters):
		self._parameters = parameters
		localsetupjob_name = self._expid + "_" 
		localsetup_job = Job(localsetupjob_name + "localsetup", 0, Status.READY, Type.LOCALSETUP)
		localsetup_job.set_parents([])
		remotesetupjob_name = self._expid + "_" 
		remotesetup_job = Job(remotesetupjob_name + "remotesetup", 0, Status.WAITING, Type.REMOTESETUP)
		remotesetup_job.set_parents([localsetup_job.get_name()])
		localsetup_job.add_children(remotesetup_job.get_name())

		print "Creating job list\n"
		for date in date_list:
			print date
			for member in member_list:
				print member
				transjob_name = self._expid + "_" + str(date) + "_" + str(member) + "_" 
				trans_job = Job(transjob_name + "trans", 0, Status.WAITING, Type.TRANSFER)
				for	chunk in range(starting_chunk, starting_chunk + num_chunks):
					rootjob_name = self._expid + "_" + str(date) + "_" + str(member) + "_" + str(chunk) + "_"
					inijob_name = self._expid + "_" + str(date) + "_" + str(member) + "_" 
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
						ini_job = Job(inijob_name + "ini", 0, Status.WAITING, Type.INITIALISATION)
						ini_job.set_children([sim_job.get_name()])
						ini_job.set_parents([remotesetup_job.get_name()])
						remotesetup_job.add_children(ini_job.get_name())
						sim_job.set_parents([ini_job.get_name()])
						self._job_list += [ini_job]
					if (chunk < starting_chunk + num_chunks	- 1):
						childjob_name = self._expid + "_" + str(date) + "_" + str(member) + "_" + str(chunk+1) + "_" + "sim"
						sim_job.add_children(childjob_name)
					if (chunk < starting_chunk + num_chunks - 2):
						childjob_name = self._expid+ "_" + str(date) + "_" + str(member) + "_" + str(chunk+2) + "_" + "sim"
						clean_job.set_children([childjob_name])
					if (chunk == num_chunks or chunk == num_chunks-1):
						trans_job.set_parents([clean_job.get_name()])
						clean_job.add_children(trans_job.get_name())

					self._job_list += [sim_job, post_job, clean_job]
				
				self._job_list += [trans_job]

		self._job_list += [localsetup_job,remotesetup_job]

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

	def update_parameters(self, parameters):
		self._parameters = parameters
		for job in self._job_list:
			job.set_parameters(parameters)

	def update_list(self, store_change=True):
		# load updated file list
		self.update_from_file(store_change)
		
		# reset jobs that has failed less than 10 times
		if (self._parameters.has_key('RETRIALS')):
			retrials = int(self._parameters['RETRIALS'])
		else:
			retrials = 4
		print "Retrials: "
		print retrials

		for job in self.get_failed():
			job.inc_fail_count()
			if job.get_fail_count() < retrials:
				job.set_status(Status.READY)
		
		# if waiting jobs has all parents completed change its State to READY
		for job in self.get_waiting():
			tmp = [parent for parent in job.get_parents() if parent.get_status() == Status.COMPLETED]
			#for parent in job.get_parents():				
				#if parent.get_status() != Status.COMPLETED:
				#	break
			if len(tmp) == len(job.get_parents()):
				job.set_status(Status.READY)
		if(store_change):
			self.save()
			
	def update_shortened_names(self):
		"""In some cases the scheduler only can operate with names shorter than 15 characters. Update the job list replacing job names by the corresponding shortened job name"""
		for job in self._job_list:
			job.set_name(job.get_short_name())

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

	def check_scripts(self):
		"""When we have created the scripts, all parameters should have been substituted. %PARAMETER% handlers not allowed"""
		out = True
		for job in self._job_list:
			if not job.check_script():
				out = False
				print "WARNING: Invalid parameter substitution in %s!!!" % job.get_name()

		return out

class RerunJobList(JobList):
	
	def __init__(self, expid):
		self._pkl_path = LOCAL_ROOT_DIR + "/" + expid + "/pkl/"
		self._update_file = "updated_list_" + expid + ".txt"
		self._failed_file = "failed_job_list_" + expid + ".pkl"
		self._job_list_file = "rerun_job_list_" + expid + ".pkl"
		self._job_list = list()
		self._expid = expid
		self._stat_val = Status()
		self._parameters = []

	def create(self, chunk_list, starting_chunk, num_chunks, parameters):
		print "Creating job list\n"
		data = json.loads(chunk_list)
		print data
		self._parameters = parameters

		localsetupjob_name = self._expid + "_" 
		localsetup_job = Job(localsetupjob_name + "localsetup", 0, Status.READY, Type.LOCALSETUP)
		localsetup_job.set_parents([])
		remotesetupjob_name = self._expid + "_" 
		remotesetup_job = Job(remotesetupjob_name + "remotesetup", 0, Status.WAITING, Type.REMOTESETUP)
		remotesetup_job.set_parents([localsetup_job.get_name()])
		localsetup_job.add_children(remotesetup_job.get_name())



		for date in data['sds']:
			print date['sd']
			for member in date['ms']:
				print member['m']
				print member['cs']
				
				first_chunk = int(member['cs'][0])
				
				if (len(member['cs']) > 1):
					second_chunk = int(member['cs'][1]) 
					last_chunk = int(member['cs'][len(member['cs'])-1])
					second_last_chunk = int(member['cs'][len(member['cs'])-2]) 
				else:
					last_chunk = first_chunk
				
				inijob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" 
				ini_job = Job(inijob_name + "ini", 0, Status.WAITING, Type.INITIALISATION)
				ini_job.set_parents([remotesetup_job.get_name()])

				transjob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" 
				trans_job = Job(transjob_name + "trans", 0, Status.WAITING, Type.TRANSFER)
				#ini_job.set_parents([])
				
				remotesetup_job.add_children(ini_job.get_name())
				self._job_list += [ini_job]
				self._job_list += [trans_job]

				for	chunk in member['cs']:
					chunk = int(chunk)
					rootjob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(chunk) + "_"
					post_job = Job(rootjob_name + "post", 0, Status.WAITING, Type.POSTPROCESSING)
					clean_job = Job(rootjob_name + "clean", 0, Status.WAITING, Type.CLEANING)
					sim_job = Job(rootjob_name + "sim", 0, Status.WAITING, Type.SIMULATION)
					# set dependency of postprocessing jobs
					sim_job.set_children([post_job.get_name()])
					post_job.set_parents([sim_job.get_name()])
					post_job.set_children([clean_job.get_name()])
					clean_job.set_parents([post_job.get_name()])
					trans_job.set_parents([clean_job.get_name()])

					# Link parents:
					# if chunk is 1 then not needed to add the previous clean job
					if (chunk == 1):
						ini_job.set_children([sim_job.get_name()])
						sim_job.set_parents([ini_job.get_name()])
						self._job_list += [sim_job, post_job, clean_job]
					elif (chunk == first_chunk):
						prev_new_job_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(chunk-1) + "_" + "clean"
						prev_new_clean_job = Job(prev_new_job_name, 0, Status.WAITING, Type.CLEANING)
						ini_job.set_children([prev_new_clean_job.get_name()])
						sim_job.set_parents([prev_new_clean_job.get_name()])
						prev_new_clean_job.set_parents([ini_job.get_name()])
						prev_new_clean_job.set_children([sim_job.get_name()])
						self._job_list += [prev_new_clean_job, sim_job, post_job, clean_job]
					else:
						if (chunk > first_chunk):
							prev_chunk = int(member['cs'][member['cs'].index(str(chunk))-1])
							if (chunk > second_chunk):
								prev_prev_chunk = int(member['cs'][member['cs'].index(str(chunk))-2])
							# in case reruning no consecutive chunk we need to create the previous clean job in the basis of chunk-1
							if (prev_chunk != chunk-1):
								prev_new_job_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(chunk-1) + "_" + "clean"
								prev_new_clean_job = Job(prev_new_job_name, 0, Status.WAITING, Type.CLEANING)
								sim_job.set_parents([prev_new_clean_job.get_name()])
								# Link parent and child for new clean job:
								prev_clean_job_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(prev_chunk) + "_" + "clean"
								prev_new_clean_job.set_parents([prev_clean_job_name])
								prev_new_clean_job.set_children([sim_job.get_name()])
								# Add those to the list
								self._job_list += [prev_new_clean_job, sim_job, post_job, clean_job]
							# otherwise we should link backwards to the immediate before clean job
							else:
								prev_sim_job_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(prev_chunk) + "_" + "sim"
								sim_job.set_parents([prev_sim_job_name])
								if (chunk > second_chunk):
									prev_clean_job_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(prev_prev_chunk) + "_" + "clean"
									sim_job.add_parent(prev_clean_job_name)
								# Add those to the list
								self._job_list += [sim_job, post_job, clean_job]
					#Link child:								
					if (chunk < last_chunk):
						next_chunk = int(member['cs'][member['cs'].index(str(chunk))+1])
						if (chunk < second_last_chunk):
							next_next_chunk = int(member['cs'][member['cs'].index(str(chunk))+2])
						else:
							clean_job.add_children(trans_job.get_name())
						# in case reruning no consecutive chunks we need to link next_chunk-1 clean job
						if (next_chunk != chunk+1):
							childjob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(next_chunk-1) + "_" + "clean"
							clean_job.add_children(childjob_name)
						# otherwise we should link with next chunk sim job
						else:
							childjob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(next_chunk) + "_" + "sim"
							sim_job.add_children(childjob_name)
							if (chunk < second_last_chunk):
								childjob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(next_next_chunk) + "_" + "sim"
								clean_job.add_children(childjob_name)
					else:
						clean_job.add_children(trans_job.get_name())


											
						
				#if (member['cs'] == []):
				#	clean_job = ini_job
				#if (last_chunk != num_chunks):
				#	finaljob_name = self._expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(num_chunks) + "_" + "clean"
				#	final_job = Job(finaljob_name , 0, Status.WAITING, Type.CLEANING)
				#	final_job.set_parents([clean_job.get_name()])
				#	clean_job.add_children(finaljob_name)
				#	self._job_list += [final_job]
		
		self._job_list += [localsetup_job,remotesetup_job]

		self.update_genealogy()
		for job in self._job_list:
			job.set_parameters(parameters)

