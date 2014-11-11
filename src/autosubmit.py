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

import argparse
import time, os, sys
import cPickle as pickle
import commands
import signal
import logging
import platform
from queue.itqueue import ItQueue
from queue.mnqueue import MnQueue
from queue.lgqueue import LgQueue
from queue.elqueue import ElQueue
from queue.psqueue import PsQueue
from queue.ecqueue import EcQueue
from queue.mn3queue import Mn3Queue
from queue.htqueue import HtQueue
from queue.arqueue import ArQueue
from job.job import Job
from job.job_common import Status
from job.job_common import Type
from job.job_list import JobList
from job.job_list import RerunJobList
from config_parser import config_parser
from config_parser import expdef_parser
from config_parser import pltdef_parser
from config_parser import moddef_parser
from dir_config import LOCAL_ROOT_DIR
from dir_config import LOCAL_GIT_DIR
from check_compatibility import check_compatibility, print_compatibility
from finalise_exp import clean_git, clean_plot, register_sha

"""This is the main code of autosubmit. All the stream of execution is handled here (submitting all the jobs properly and repeating its execution in case of failure)."""

def log_long(message):
	print "[%s] %s" % (time.asctime(), message)
 
def log_short(message):
	d = time.localtime()
	date = "%04d-%02d-%02d %02d:%02d:%02d" % (d[0],d[1],d[2],d[3],d[4],d[5])
	print "[%s] %s" % (date,message)

def check_parameters(conf_parser_file):
	conf_parser = config_parser(conf_parser_file)
	exp_parser_file = conf_parser.get('config', 'EXPDEFFILE')
	exp_parser = expdef_parser(exp_parser_file)

	expdef = []
	incldef = []
	for section in exp_parser.sections():
		if (section.startswith('include')):
			items = [x for x in exp_parser.items(section) if x not in exp_parser.items('DEFAULT')]
			incldef += items
		else:
			expdef += exp_parser.items(section)

	parameters = dict()
	for item in expdef:
		parameters[item[0]] = item[1]
	for item in incldef:
		parameters[item[0]] = file(item[1]).read()

	git_project = exp_parser.get('experiment','GIT_PROJECT').lower()
	if (git_project == "true"):
		# Check additional parameters changes
		print "Checking additional parameters..."
		parameters.append(check_additonal_parameters(conf_parser_file))

	return parameters

def check_additional_parameters(conf_parser_file):
	conf_parser = config_parser(conf_parser_file)
	exp_parser_file = conf_parser.get('config', 'EXPDEFFILE')
	exp_parser = expdef_parser(exp_parser_file)

	pltdef = []
	moddef = []
	plt_parser_file = exp_parser.get('git', 'GIT_FILE_PLATFORM_CONF')
	plt_parser = pltdef_parser(LOCAL_ROOT_DIR + "/" + args.expid[0] + "/" + LOCAL_GIT_DIR + "/" + plt_parser_file)
	mod_parser_file = exp_parser.get('git', 'GIT_FILE_MODEL_CONF')
	mod_parser = moddef_parser(LOCAL_ROOT_DIR + "/" + args.expid[0] + "/" + LOCAL_GIT_DIR + "/" + mod_parser_file)

	for section in plt_parser.sections():
		pltdef += plt_parser.items(section)
	for section in mod_parser.sections():
		moddef += mod_parser.items(section)
	
	parameters = dict()
	for item in pltdef:
		parameters[item[0]] = item[1]
	for item in moddef:
		parameters[item[0]] = item[1]

	return parameters


####################
# Main Program
####################
def main():
 
	os.system('clear')
	parser = argparse.ArgumentParser(description='Launch Autosubmit given an experiment identifier')
	parser.add_argument('-e', '--expid', required=True, nargs = 1)
	args = parser.parse_args()
	if args.expid is None:
		parser.error("Missing expid.")

	logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s',
    	                datefmt='%a, %d %b %Y %H:%M:%S',
            	        filename=os.path.join(os.path.dirname(__file__), os.pardir, 'my_autosubmit_' + args.expid[0] + '.log'),
                	    filemode='w')
	
	logger = logging.getLogger("AutoLog")


	conf_parser_file = LOCAL_ROOT_DIR + "/" +  args.expid[0] + "/conf/" + "autosubmit_" + args.expid[0] + ".conf"
	conf_parser = config_parser(conf_parser_file)
	exp_parser_file = conf_parser.get('config', 'EXPDEFFILE')
	exp_parser = expdef_parser(exp_parser_file)

	alreadySubmitted = int(conf_parser.get('config','ALREADYSUBMITTED'))
	totalJobs = int(conf_parser.get('config','TOTALJOBS'))
	expid = exp_parser.get('experiment','EXPID')
	maxWaitingJobs = int(conf_parser.get('config','MAXWAITINGJOBS'))
	safetysleeptime = int(conf_parser.get('config','SAFETYSLEEPTIME'))
	retrials = int(conf_parser.get('config','RETRIALS'))
	hpcarch = exp_parser.get('experiment', 'HPCARCH')
	scratch_dir = exp_parser.get('experiment', 'SCRATCH_DIR')
	hpcproj = exp_parser.get('experiment', 'HPCPROJ')
	hpcuser = exp_parser.get('experiment', 'HPCUSER')
	if (exp_parser.has_option('experiment','RERUN')):
		rerun = exp_parser.get('experiment','RERUN').lower()
	else: 
		rerun = 'false'
	
	# Check parameters changes	
	print "Checking parameters..."
	parameters = check_parameters(conf_parser_file)	

	if(hpcarch == "bsc"):
	   remoteQueue = MnQueue(expid)
	   remoteQueue.set_host("bsc")
	elif(hpcarch == "ithaca"):
	   remoteQueue = ItQueue(expid)
	   remoteQueue.set_host("ithaca")
	elif(hpcarch == "hector"):
	   remoteQueue = HtQueue(expid)
	   remoteQueue.set_host("ht-" + hpcproj)
	elif(hpcarch == "archer"):
	   remoteQueue = ArQueue(expid)
	   remoteQueue.set_host("ar-" + hpcproj)
	## in lindgren arch must set-up both serial and parallel queues
	elif(hpcarch == "lindgren"):
	   serialQueue = ElQueue(expid)
	   serialQueue.set_host("ellen") 
	   parallelQueue = LgQueue(expid)
	   parallelQueue.set_host("lindgren") 
	elif(hpcarch == "ecmwf"):
	   remoteQueue = EcQueue(expid)
	   remoteQueue.set_host("c2a")
	elif(hpcarch == "marenostrum3"):
	   remoteQueue = Mn3Queue(expid)
	   remoteQueue.set_host("mn-" + hpcproj)

	localQueue = PsQueue(expid)
	localQueue.set_host(platform.node())
	localQueue.set_scratch(LOCAL_ROOT_DIR)
	localQueue.set_project(expid)
	localQueue.set_user("tmp")
	localQueue.update_cmds()

	logger.debug("The Experiment name is: %s" % expid)
	logger.info("Jobs to submit: %s" % totalJobs)
	logger.info("Start with job number: %s" % alreadySubmitted)
	logger.info("Maximum waiting jobs in queues: %s" % maxWaitingJobs)
	logger.info("Sleep: %s" % safetysleeptime)
	logger.info("Retrials: %s" % retrials)
	logger.info("Starting job submission...")


	## in lindgren arch must signal both serial and parallel queues
	if(hpcarch == "lindgren"):
		signal.signal(signal.SIGQUIT, serialQueue.smart_stop)
		signal.signal(signal.SIGINT, serialQueue.normal_stop)
		signal.signal(signal.SIGQUIT, parallelQueue.smart_stop)
		signal.signal(signal.SIGINT, parallelQueue.normal_stop)
		serialQueue.set_scratch(scratch_dir)
		serialQueue.set_project(hpcproj)
		serialQueue.set_user(hpcuser)
		serialQueue.update_cmds()
		parallelQueue.set_scratch(scratch_dir)
		parallelQueue.set_project(hpcproj)
		parallelQueue.set_user(hpcuser)
		parallelQueue.update_cmds() 
	else:
		signal.signal(signal.SIGQUIT, remoteQueue.smart_stop)
		signal.signal(signal.SIGINT, remoteQueue.normal_stop)
		remoteQueue.set_scratch(scratch_dir)
		remoteQueue.set_project(hpcproj)
		remoteQueue.set_user(hpcuser)
		remoteQueue.update_cmds()

	signal.signal(signal.SIGQUIT, localQueue.smart_stop)
	signal.signal(signal.SIGINT, localQueue.normal_stop)
 
	if(rerun == 'false'):
		filename = LOCAL_ROOT_DIR + "/" + expid + '/pkl/job_list_'+ expid +'.pkl'
	elif(rerun == 'true'):
		filename = LOCAL_ROOT_DIR + "/" + expid + '/pkl/rerun_job_list_'+ expid +'.pkl'
	print filename

	#the experiment should be loaded as well
	if (os.path.exists(filename)):
		joblist = pickle.load(file(filename,'rw'))
		logger.info("Starting from joblist pickled in %s " % filename)
	else:
		logger.error("The pickle file %s necessary does not exist." % filename)
		sys.exit()

	logger.debug("Length of joblist: %s" % len(joblist))

	# Check parameters changes	
	print "Checking parameters..."
	parameters = check_parameters(conf_parser_file)	
	print "Updating parameters..."
	joblist.update_parameters(parameters)
	#check the job list script creation
	print "Checking experiment templates..."
	if (joblist.check_scripts()):
		logger.info("Experiment templates check PASSED!")
	else:
		logger.error("Experiment templates check FAILED!")
		print "Experiment templates check FAILED!"
		sys.exit()

	
	#check the availability of the Queues
	localQueue.check_remote_log_dir()
	## in lindgren arch must check both serial and parallel queues
	if(hpcarch == "lindgren"):
		serialQueue.check_remote_log_dir()
		parallelQueue.check_remote_log_dir()
	else:
		remoteQueue.check_remote_log_dir()

	#first job goes to the local Queue
	queue = localQueue

	#########################
	# AUTOSUBMIT - MAIN LOOP
	#########################
	# Main loop. Finishing when all jobs have been submitted
	while joblist.get_active() :
		active = len(joblist.get_running())
		waiting = len(joblist.get_submitted() + joblist.get_queuing())
		available = maxWaitingJobs-waiting
	
		# variables to be updated on the fly
		conf_parser = config_parser(LOCAL_ROOT_DIR + "/" +  args.expid[0] + "/conf/" + "autosubmit_" + args.expid[0] + ".conf")
		totalJobs = int(conf_parser.get('config','TOTALJOBS'))
		logger.info("Jobs to submit: %s" % totalJobs)
		safetysleeptime = int(conf_parser.get('config','SAFETYSLEEPTIME'))
		logger.info("Sleep: %s" % safetysleeptime)
		retrials = int(conf_parser.get('config','RETRIALS'))
		logger.info("Number of retrials: %s" % retrials)

		# Check parameters changes	
		print "Checking parameters..."
		parameters = check_parameters(conf_parser_file)	
		joblist.update_parameters(parameters)

		# read FAIL_RETRIAL number if, blank at creation time put a given number
		# check availability of machine, if not next iteration after sleep time
		# check availability of jobs, if no new jobs submited and no jobs available, then stop
  
  		# ??? why
		logger.info("Saving joblist")
		joblist.save()
  
		logger.info("Active jobs in queues:\t%s" % active)
		logger.info("Waiting jobs in queues:\t%s" % waiting)

		if available == 0:
			logger.info("There's no room for more jobs...")
		else:
			logger.info("We can safely submit %s jobs..." % available)
	  
		######################################
		# AUTOSUBMIT - ALREADY SUBMITTED JOBS
		######################################
		#get the list of jobs currently in the Queue
		jobinqueue = joblist.get_in_queue()
		logger.info("Number of jobs in queue: %s" % str(len(jobinqueue))) 

		# Check queue aviailability		
		queueavail = queue.check_host()
		if not queueavail:
			logger.info("There is no queue available")
		else:
			for job in jobinqueue:
				job.print_job()
				print ("Number of jobs in queue: %s" % str(len(jobinqueue))) 
				## in lindgren arch must select serial or parallel queue acording to the job type
				if(hpcarch == "lindgren" and job.get_type() == Type.SIMULATION):
					queue = parallelQueue
				elif(hpcarch == "lindgren" and (job.get_type() == Type.INITIALISATION or job.get_type() == Type.CLEANING or job.get_type() == Type.POSTPROCESSING)):
					queue = serialQueue
				elif(job.get_type() == Type.LOCALSETUP or job.get_type() == Type.TRANSFER):
					queue = localQueue
				else:
					queue = remoteQueue
				# Check queue aviailability		
				queueavail = queue.check_host()
				if not queueavail:
					logger.info("There is no queue available")
				else:
					status = queue.check_job(job.get_id(), job.get_status())
					if(status == Status.COMPLETED):
						logger.debug("This job seems to have completed...checking")
						queue.get_completed_files(job.get_name())
						job.check_completion()
					else:
						job.set_status(status)
			
				# Check parameters changes	
				print "Checking parameters..."
				parameters = check_parameters(conf_parser_file)	
				joblist.update_parameters(parameters)

			#Uri add check if status UNKNOWN and exit if you want 
			##after checking the jobs , no job should have the status "submitted"
			##Uri throw an exception if this happens (warning type no exit)
	   
		# explain it !!
		joblist.update_list()
		
		##############################
		# AUTOSUBMIT - JOBS TO SUBMIT
		##############################
		## get the list of jobs READY
		jobsavail = joblist.get_ready()

		# Check queue aviailability		
		queueavail = queue.check_host()
		if not queueavail:
			logger.info("There is no queue available")
		elif (min(available, len(jobsavail)) == 0):
			logger.info("There is no job READY or available")
			logger.info("Number of jobs ready: %s" % len(jobsavail))
			logger.info("Number of jobs available in queue: %s" % available)
		elif (min(available, len(jobsavail)) > 0 and len(jobinqueue) <= totalJobs): 
			logger.info("We are going to submit: %s" % min(available,len(jobsavail)))
			##should sort the jobsavail by priority Clean->post->sim>ini
			#s = sorted(jobsavail, key=lambda k:k.get_name().split('_')[1][:6])
			## probably useless to sort by year before sorting by type
			s = sorted(jobsavail, key=lambda k:k.get_long_name().split('_')[1][:6])

			list_of_jobs_avail = sorted(s, key=lambda k:k.get_type())
     
			for job in list_of_jobs_avail[0:min(available, len(jobsavail), totalJobs-len(jobinqueue))]:
				print job.get_name()
				scriptname = job.create_script() 
				print scriptname
				## in lindgren arch must select serial or parallel queue acording to the job type
				if(hpcarch == "lindgren" and job.get_type() == Type.SIMULATION):
					queue = parallelQueue
					logger.info("Submitting to parallel queue...")
					print("Submitting to parallel queue...")
				elif(hpcarch == "lindgren" and (job.get_type() == Type.REMOTESETUP or job.get_type() == Type.INITIALISATION or job.get_type() == Type.CLEANING or job.get_type() == Type.POSTPROCESSING)):
					queue = serialQueue
					logger.info("Submitting to serial queue...")
					print("Submitting to serial queue...")
				elif(job.get_type() == Type.LOCALSETUP or job.get_type() == Type.TRANSFER):
					queue = localQueue
					logger.info("Submitting to local queue...")
					print("Submitting to local queue...")
				else:
					queue = remoteQueue
					logger.info("Submitting to remote queue...")
					print("Submitting to remote queue...")
				# Check queue aviailability		
				queueavail = queue.check_host()
				if not queueavail:
					logger.info("There is no queue available")
				else:
					queue.send_script(scriptname)
					job_id = queue.submit_job(scriptname)
					job.set_id(job_id)
					##set status to "submitted"
					job.set_status(Status.SUBMITTED)

				# Check parameters changes	
				print "Checking parameters..."
				parameters = check_parameters(conf_parser_file)	
				joblist.update_parameters(parameters)
		
		time.sleep(safetysleeptime)
	## finalise experiment
	if (len(joblist.get_completed()) == len(joblist)):
		#print "Cleaning GIT directory..."
		#clean_git(expid)
		print "Cleaning plot directory..."
		clean_plot(expid)
 
 	logger.info("Finished job submission")

if __name__ == "__main__":
	main()
