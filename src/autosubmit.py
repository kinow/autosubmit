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

import time, os, sys
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
import dir_config
from config_parser import config_parser, expdef_parser, archdef_parser
from job.job import Job
from job.job_common import Status, Type
from job.job_list import JobList
from job.job_list import RerunJobList
import cPickle as pickle
from dir_config import LOCAL_ROOT_DIR
from check_compatibility import check_compatibility, print_compatibility
from finalise_exp import clean_git, clean_plot, register_sha

"""This is the main code of autosubmit. All the stream of execution is handled here (submitting all the jobs properly and repeating its execution in case of failure)."""

####################
# Global Variables
####################

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='myauto'+sys.argv[1]+'.log',
                    filemode='w')
logger = logging.getLogger("AutoLog")

def log_long(message):
	print "[%s] %s" % (time.asctime(), message)
 
def log_short(message):
	d = time.localtime()
	date = "%04d-%02d-%02d %02d:%02d:%02d" % (d[0],d[1],d[2],d[3],d[4],d[5])
	print "[%s] %s" % (date,message)

####################
# Main Program
####################
if __name__ == "__main__":
 
	os.system('clear')
	if(len(sys.argv) != 2):
		print "Missing expid\n"
		sys.exit(1)

	autosubmit_version_filename = "../VERSION"
	template_version_filename = LOCAL_ROOT_DIR + "/" + sys.argv[1] + "/git/templates/VERSION"
	
	if not check_compatibility(autosubmit_version_filename, template_version_filename):
		print "Compatibility check FAILED!"
		print_compatibility()
		sys.exit(1)
	else:
		print "Compatibility check PASSED!"

	conf_parser = config_parser(LOCAL_ROOT_DIR + "/" +  sys.argv[1] + "/conf/" + "autosubmit_" + sys.argv[1] + ".conf")
	exp_parser_file = conf_parser.get('config', 'EXPDEFFILE')
	arch_parser_file = conf_parser.get('config', 'ARCHDEFFILE')
	exp_parser = expdef_parser(exp_parser_file)
	arch_parser = archdef_parser(arch_parser_file)

	alreadySubmitted = int(conf_parser.get('config','alreadysubmitted'))
	totalJobs = int(conf_parser.get('config','totaljobs'))
	expid = conf_parser.get('config','expid')
	templatename = exp_parser.get('experiment','TEMPLATE_NAME') 
	maxWaitingJobs = int(conf_parser.get('config','maxwaitingjobs'))
	if (conf_parser.has_option('config','maxtransferjobs')):
		maxTransferJobs = int(conf_parser.get('config','maxtransferjobs'))
	else:
		maxTransferJobs = 2
	safetysleeptime = int(conf_parser.get('config','safetysleeptime'))
	retrials = int(conf_parser.get('config','retrials'))
	hpcarch = exp_parser.get('experiment', 'HPCARCH')
	scratch_dir = arch_parser.get('archdef', 'SCRATCH_DIR')
	hpcproj = exp_parser.get('experiment', 'HPCPROJ')
	hpcuser = exp_parser.get('experiment', 'HPCUSER')
	if (exp_parser.has_option('experiment','RERUN')):
		rerun = exp_parser.get('experiment','RERUN').lower()
	else: 
		rerun = 'false'
	if (conf_parser.has_option('config','WRAP')):
		wrapping = conf_parser.get('config','WRAP').lower()
	else: 
		wrapping = 'false'
	if (wrapping == 'true'):
		wrapsize = int(conf_parser.get('config', 'wrapsize'))
		#logger.info("Wrap size: %s" % wrapsize)
	else:
		wrapsize = 1

	expdef = []
	incldef = []
	for section in exp_parser.sections():
		if (section.startswith('include')):
			items = [x for x in exp_parser.items(section) if x not in exp_parser.items('DEFAULT')]
			incldef += items
		else:
			expdef += exp_parser.items(section)

	arch_parser = archdef_parser(arch_parser_file)
	expdef += arch_parser.items('archdef')

	parameters = dict()

	for item in expdef:
		parameters[item[0]] = item[1]
	for item in incldef:
		parameters[item[0]] = file(item[1]).read()



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
	elif(hpcarch == "ecmwf-cca"):
	   remoteQueue = EcQueue(expid)
	   remoteQueue.set_host("cca")
	elif(hpcarch == "marenostrum3"):
	   remoteQueue = Mn3Queue(expid)
	   remoteQueue.set_host("mn-" + hpcproj)

	localQueue = PsQueue(expid)
	localQueue.set_host(platform.node())
	localQueue.set_scratch("/cfu/autosubmit")
	localQueue.set_project(expid)
	localQueue.set_user("tmp")
	localQueue.update_cmds()

	logger.debug("The Experiment name is: %s" % expid)
	logger.info("Jobs to submit: %s" % totalJobs)
	logger.info("Start with job number: %s" % alreadySubmitted)
	logger.info("Maximum waiting jobs in queues: %s" % maxWaitingJobs)
	logger.info("Maximum transfer jobs: %s" % maxTransferJobs)
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

	#Minguuuuuu caution
	wraplist = list()
	activejobswrap = 0
	waitingWraps = 0
	wrapid = 0

	# Main loop. Finishing when all jobs have been submitted
	while joblist.get_active() :
		active = len(joblist.get_running())
		waiting = len(joblist.get_submitted() + joblist.get_queuing())
		transfering = 0
		availableTransfers = maxTransferJobs-transfering

		if (activejobswrap > 0):
			logger.debug("We have active wraps")
			logger.debug("Waiting wraps in queues:\t%s" % waitingWraps)
			available = maxWaitingJobs+(waitingWraps*wrapsize)-waiting
			logger.debug("Number of slots available in queue: %s" % available)
		else:
			logger.debug("No active wraps")
			available = maxWaitingJobs-waiting
			logger.debug("Number of slots available in queue: %s" % available)
	
		# variables to be updated on the fly
		conf_parser = config_parser(LOCAL_ROOT_DIR + "/" +  sys.argv[1] + "/conf/" + "autosubmit_" + sys.argv[1] + ".conf")
		totalJobs = int(conf_parser.get('config','totaljobs'))
		logger.info("Jobs to submit: %s" % totalJobs)
		if (conf_parser.has_option('config','maxtransferjobs')):
			maxTransferJobs = int(conf_parser.get('config','maxtransferjobs'))
		logger.info("Maximum transfer jobs: %s" % maxTransferJobs)
		if (conf_parser.has_option('config','WRAP')):
			wrapping = conf_parser.get('config','WRAP').lower()
		else: 
			wrapping = 'false'
		if (wrapping == 'true'):
			wrapsize = int(conf_parser.get('config', 'wrapsize'))
		else:
			wrapsize = 1
		safetysleeptime = int(conf_parser.get('config','safetysleeptime'))
		logger.info("Sleep: %s" % safetysleeptime)
		retrials = int(conf_parser.get('config','retrials'))
		logger.info("Number of retrials: %s" % retrials)
		exp_parser = expdef_parser(exp_parser_file)
		arch_parser = archdef_parser(arch_parser_file)
		expdef = []
		incldef = []
		for section in exp_parser.sections():
			if (section.startswith('include')):
				items = [x for x in exp_parser.items(section) if x not in exp_parser.items('DEFAULT')]
				incldef += items
			else:
				expdef += exp_parser.items(section)

		arch_parser = archdef_parser(arch_parser_file)
		expdef += arch_parser.items('archdef')

		parameters = dict()

		for item in expdef:
			parameters[item[0]] = item[1]
		for item in incldef:
			parameters[item[0]] = file(item[1]).read()

		parameters['WRAPSIZE'] = wrapsize
		parameters['RETRIALS'] = retrials 
		parameters['NUMPROC'] = parameters['NUMPROC_SETUP']
   		joblist.update_parameters(parameters)

		# read FAIL_RETRIAL number if, blank at creation time put a given number
		# check availability of machine, if not next iteration after sleep time
		# check availability of jobs, if no new jobs submited and no jobs available, then stop
  
		#logger.info("Saving joblist")
		joblist.save()
  
		if conf_parser.get('config','verbose').lower()=='true':
			logger.info("ACTIVE jobs in queues:\t%s" % active)
			logger.info("WAITING jobs in queues:\t%s" % waiting)
			logger.info("WAITING wraps in queues:\t%s" % waitingWraps)

		if available <= 0:
			if  conf_parser.get('config','verbose').lower()=='true':
				logger.info("There's no ROOM for more jobs...")
		else:
			if  conf_parser.get('config','verbose').lower()=='true':
				logger.info("We can SAFELY submit %s jobs..." % available)
	  
	  	######################################
		# AUTOSUBMIT - ALREADY SUBMITTED JOBS
		######################################
		#get the list of jobs currently in the Queue
		#logger.debug("AUTOSUBMIT - CHECKING ALREADY SUBMITTED JOBS")
		jobinqueue = joblist.get_in_queue()
		transfering = len([job for job in jobinqueue if job.get_type() == Type.TRANSFER])
		availableTransfers = maxTransferJobs-transfering
		logger.info("Number of jobs in queue: %s" % str(len(jobinqueue)-(activejobswrap*wrapsize-activejobswrap))) 
		# Check queue aviailability		
		queueavail = queue.check_host()
		if not queueavail:
			logger.info("There is no queue available")
		else:
			for job in jobinqueue:
				job.print_job()
				print ("Active jobs wrap: %s" % str(activejobswrap))
				#print ("Number of jobs in queue: %s" % str(len(jobinqueue)-(activejobswrap*wrapsize-activejobswrap))) 
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
				exp_parser = expdef_parser(exp_parser_file)
				arch_parser = archdef_parser(arch_parser_file)
				expdef = []
				incldef = []
				for section in exp_parser.sections():
					if (section.startswith('include')):
						items = [x for x in exp_parser.items(section) if x not in exp_parser.items('DEFAULT')]
						incldef += items
					else:
						expdef += exp_parser.items(section)
				arch_parser = archdef_parser(arch_parser_file)
				expdef += arch_parser.items('archdef')
				parameters = dict()
				for item in expdef:
					parameters[item[0]] = item[1]
				for item in incldef:
					parameters[item[0]] = file(item[1]).read()
				parameters['WRAPSIZE'] = wrapsize
				parameters['RETRIALS'] = retrials 
				parameters['NUMPROC'] = parameters['NUMPROC_SETUP']
				joblist.update_parameters(parameters)

			#Uri add check if status UNKNOWN and exit if you want 
	   
			##after checking the jobs , no job should have the status "submitted"
			##Uri throw an exception if this happens (warning type no exit)

			for wrap in wraplist:
				queue = remoteQueue
				wrap.print_wrap()
				logger.info("Checking wrap status...")
				print("Checking wrap status...")
				time.sleep(safetysleeptime)
				queueavail = queue.check_host()
				if not queueavail:
					logger.info("There is no queue available")
				else:
					status = queue.check_job(wrap.get_id(), wrap.get_status())
					if(status == Status.QUEUING or status == Status.SUBMITTED):
						waitingWraps = 1
						logger.debug("WAITING wraps in queues set to:\t%s" % waitingWraps)
					elif(status == Status.COMPLETED):
						logger.debug("This wrap seems to have completed...checking")
						### Minguuu this does not seem to make sense... a retrial will never happen...
						queue.get_completed_files(wrap.get_name())
						wrap.check_completion()
						wraplist.remove(wrap)
						activejobswrap -= 1
						waitingWraps = 0
						logger.debug("WAITING wraps in queues set to:\t%s" % waitingWraps)
					else:
						#logger.info("There are %s active wraps" % len(wraplist))
						waitingWraps = 0
						wrap.set_status(status)
						logger.debug("WAITING wraps in queues set to:\t%s" % waitingWraps)

	   
   		joblist.update_parameters(parameters)
		joblist.update_list()

		##############################
		# AUTOSUBMIT - JOBS TO SUBMIT
		##############################
		## get the list of jobs READY
		#logger.debug("AUTOSUBMIT - CHECKING JOBS TO SUBMIT")
		activejobs = joblist.get_active()
		#logger.info("There are %s active jobs" % len(activejobs))
		wrappablejobs = joblist.get_wrappable(wrapsize) 
		#logger.info("There are %s wrappable jobs" % len(wrappablejobs))

		if (wrapping == 'true'):
			## get the possible wraps (list of special jobs, containing several scripts each one)
			wrapsavail = joblist.get_wraps(wrapsize,wrapid)
			if not wrapsavail:
				logger.info("There is no wrap available")
			elif (min(available, len(wrapsavail)) <= 0):
				logger.info("AVAILABLE: %s" % available)
			elif (min(available, len(wrapsavail)) > 0 and activejobswrap <= totalJobs): 
				for wrap in wrapsavail:
					wraplist.append(wrap)
					print wrap.get_name()
					wrappername = wrap.create_script("common")
					print wrappername
					queue = remoteQueue
					logger.info("Submitting wrap to parallel queue...")
					print("Submitting wrap to parallal queue...")
					queueavail = queue.check_host()
					if not queueavail:
						logger.info("There is no queue available")
					else:
						for jobwrapped in wrap.get_jobs():
							scriptname = jobwrapped.create_script(templatename)
							queue.send_script(scriptname)
							logger.info("Submitting job wrap to parallel queue...")
							print("Submitting job wrap to parallal queue...")
						queue.send_script(wrappername)
						wrap_id = queue.submit_job(wrappername)
						wrap.set_id(wrap_id)
						wrap.set_status(Status.SUBMITTED)
						activejobswrap += 1
						wrapid += 1
						waitingWraps = 1
						logger.debug("WAITING wraps in queues set to:\t%s" % waitingWraps)
			else:
				logger.debug("We cannot submit any of the AVAILABLE wraps: %s" % min(available,len(jobsavail)))
				
		
			## get the list of jobs READY, excluding the single jobs that are being wrapped. The create_script is the python wrapper and the WCT and number of porcessors is a sumatori of all single jobs for those particular wrapped jobs.
			## submitting a wrap means sending the python script + sending several single scripts + submitting the special job.
			jobsavail = joblist.get_available(wrapsize)
		else:
			## get the list of jobs READY
			jobsavail = joblist.get_ready()
			print "Transfering: %s" % transfering
			#print "########################"
			print "Available transfer slots : %s" % availableTransfers
			#print "########################"
			jobstransready = [job for job in jobsavail if job.get_type() == Type.TRANSFER]
			#print "jobs trans ready %s" % jobstransready
			jobsavail = [j for j in jobsavail if j not in jobstransready]
			#print "jobs avaial - jobstransready %s" % jobsavail
			jobsavail = jobsavail + jobstransready[0:availableTransfers]
			#print "jobs avail %s" % jobsavail

   		joblist.update_parameters(parameters)
		joblist.update_list()

		if not queueavail:
			logger.info("There is no queue available")
		elif (min(available, len(jobsavail)) <= 0):
			logger.info("There is no job READY or available")
			logger.info("Number of jobs ready: %s" % len(jobsavail))
			logger.info("AVAILABLE: %s" % available)
		elif (min(available, len(jobsavail)) > 0 and len(jobinqueue)-(activejobswrap*wrapsize-activejobswrap) <= totalJobs): 
			#logger.info("We are going to submit: %s" % min(available,len(jobsavail)))
			##should sort the jobsavail by priority Clean->post->sim>ini
			#s = sorted(jobsavail, key=lambda k:k.get_name().split('_')[1][:6])
			## probably useless to sort by year before sorting by type
			s = sorted(jobsavail, key=lambda k:k.get_long_name().split('_')[1][:6])

			list_of_jobs_avail = sorted(s, key=lambda k:k.get_type())
     
			for job in list_of_jobs_avail[0:min(available, len(jobsavail), totalJobs-len(jobinqueue)-(activejobswrap*wrapsize-activejobswrap))]:
				print job.get_name()
				scriptname = job.create_script(templatename) 
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
		
		#if (min(wrapsavailable, len(wrapsavail)) == 0):
			##logger.info("There is no wrap READY or available")
			##logger.info("Number of wraps ready: %s" % len(wrapsavail))
			##logger.info("Number of wraps available in queue: %s" % wrapsavailable)
		#elif (min(wrapsavailable, len(wrapsavail)) > 0 and len(wrapsinqueue) <= totalWraps): 
			##logger.info("We are going to submit wraps: %s" % min(wrapsavailable,len(wrapsavail)))
		else: 
			logger.info("We cannot submit any of the AVAILABLE jobs: %s" % min(available,len(jobsavail)))

		time.sleep(safetysleeptime)
	## finalise experiment
	if (len(joblist.get_completed()) == len(joblist)):
		print "Cleaning GIT directory..."
		clean_git(expid)
		print "Cleaning plot directory..."
		clean_plot(expid)
 
logger.info("Finished job submission")
