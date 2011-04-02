#!/usr/bin/env python
import time, os, sys
import commands
import signal
import logging
from queue.itqueue import ItQueue
from queue.mnqueue import MnQueue
import dir_config
from job.job import Job
from job.job_common import Status
from job.job_list import JobList
import cPickle as pickle

####################
# Global Variables
####################

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='../tmp/myauto.log',
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
 

	conf_parser = config_parser(argv[1])
	alreadySubmitted = int(conf_parser.get('config','alreadysubmitted'))
	totalJobs = int(conf_parser.get('config','totaljobs'))
	myTemplate = conf_parser.get('config','jobtemplate')
	expid = conf_parser.get('config','expid')
	maxWaitingJobs = int(conf_parser.get('config','maxwaitingjobs'))
	safetysleeptime = int(conf_parser.get('config','safetysleeptime'))
	hpcarch = conf_parser.get('config', 'hpcarch')
	if(hpcarch== "marenostrum"):
	   queue = MnQueue(expid)
	elif(hpcarch == "ithaca"):
	   queue = ItQueue(expid)
	elif(hpcarch == "hector"):
	   queue = HtQueue(expid)

	logger.debug("My template name is: %s" % myTemplate)
	logger.debug("The Experiment name is: %s" % expid)
	logger.info("Jobs to submit: %s" % totalJobs)
	logger.info("Start with job number: %s" % alreadySubmitted)
	logger.info("Maximum waiting jobs in queues: %s" % maxWaitingJobs)
	logger.info("Sleep: %s" % safetysleeptime)
	logger.info("Starting job submission...")


	signal.signal(signal.SIGQUIT, queue.smart_stop)
	signal.signal(signal.SIGINT, queue.normal_stop)
 
	filename = LOCAL_ROOT_DIR + "/" + sys.argv[1] + '/pkl/job_list_'+ sys.argv[1] +'.pkl'

	#the experiment should be loaded as well
	if (os.path.exists(filename)):
		joblist = pickle.load(file(filename,'rw'))
		logger.info("Starting from joblist pickled in %s " % filename)
	else:
		logger.error("The pickle file %s necessary does not exist." % filename)
		sys.exit()

	logger.debug("Length of joblist: ",len(joblist))
	totaljobs = len(joblist)
	logger.info("Number of Jobs: "+str(totaljobs))# Main loop. Finishing when all jobs have been submitted

	template_rootname=expparser.get('common_parameters','TEMPLATE') 
	while joblist.get_active() :
		active = len(joblist.get_running())
		waiting = len(joblist.get_submitted() + joblist.get_queuing())
		available = maxWaitingJobs-waiting
  
		logger.info("Saving joblist")
		joblist.save()
  
		if parser.get('config','verbose').lower()=='true':
			logger.info("Active jobs in queues:\t%s" % active)
			logger.info("Waiting jobs in queues:\t%s" % waiting)

		if available == 0:
			if  parser.get('config','verbose').lower()=='true':
				logger.info("There's no room for more jobs...")
		else:
			if  parser.get('config','verbose').lower()=='true':
				logger.info("We can safely submit %s jobs..." % available)
	  
		#get the list of jobs currently in the Queue
		jobinqueue = joblist.get_in_queue()
		logger.info("number of jobs in queue :%s" % len(jobinqueue)) 
		for job in jobinqueue:
			job.print_job()
			status = queue.check_job(job.get_id(), job.get_status())

		if(status==Status.COMPLETED):
			logger.debug("this job seems to have completed...checking")
			queue.get_completed_files(job.get_name())
			job.check_completion()
		else:
			job.set_status(status)
		#Uri add check if status UNKNOWN and exit if you want 
   
		##after checking the jobs , no job should have the status "submitted"
		##Uri throw an exception if this happens (warning type no exit)
   
		joblist.update_list()
		activejobs = joblist.get_active()
		logger.info("There are %s active jobs" % len(activejobs))

		## get the list of jobs READY
		jobsavail=joblist.get_ready()
		if (min(available, len(jobsavail)) == 0):
			logger.info("There is no job READY or available")
			logger.info("Number of job ready: ",len(jobsavail))
			logger.info("Number of jobs available in queue:", available)
		elif (min(available,len(jobsavail)) > 0): 
			logger.info("We are going to submit: ", min(available,len(jobsavail)))
			##should sort the jobsavail by priority Clean->post->sim>ini
			list_of_jobs_avail = sorted(jobsavail, key=lambda k:k.get_type())
     
			for job in list_of_jobs_avail[0:min(available,len(jobsavail))]:
				print job.get_name()
				scriptname = job.create_script(template_rootname) 
				print scriptname
				queue.send_script(scriptname)
				job_id = queue.submit_job(scriptname)
				job.set_id(job_id)
##set status to "submitted"
				job.set_status(Status.SUBMITTED)
				if parser.get('config','clean').lower()=='true':
					os.system("rm %s" % scriptname)

		time.sleep(safetysleeptime)
 
logger.info("Finished job submission")
 
