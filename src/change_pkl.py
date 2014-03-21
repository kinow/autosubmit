#!/usr/bin/env python

from dir_config import LOCAL_ROOT_DIR
import pickle
from job.job_list import JobList
from job.job_list import RerunJobList
from job.job_common import Status
from job.job_common import Type
import argparse
import platform
from config_parser import config_parser, expdef_parser, archdef_parser
from monitor import GenerateOutput
from sys import setrecursionlimit

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Autosubmit change pikcle')
	parser.add_argument('-e', '--expid', type=str, nargs=1, required=True, help='Experiment ID')
	parser.add_argument('-j', '--joblist', type=str, nargs=1, required=True, help='Job list')
	parser.add_argument('-s', '--save', action="store_true", default=False, help='Save changes to disk')
	parser.add_argument('-t', '--status_final', choices = ('READY', 'COMPLETED', 'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN'), required = True)
	group1 = parser.add_mutually_exclusive_group(required = True)
	group1.add_argument('-l', '--list', type = str)
	group1.add_argument('-f', '--filter', action="store_true")
	group2 = parser.add_argument_group('filter arguments')
	group2.add_argument('-fc', '--filter_chunks', type = str, default = 'Any', help = 'Supply the list of chunks to change the status. Default = Any. LIST = [ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]')#, required = True)
	group2.add_argument('-fs', '--filter_status', type = str, choices = ('Any', 'READY', 'COMPLETED', 'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN'), default = 'Any', help = 'Select the original status to filter the list of jobs')
	group2.add_argument('-ft', '--filter_type', type = str, choices = ('Any', 'LOCALSETUP', 'REMOTESETUP', 'INITIALISATION', 'SIMULATION', 'POSTPROCESSING', 'CLEANING', 'LOCALTRANSFER'), default = 'Any', help = 'Select the job type to filter the list of jobs')
	args = parser.parse_args()

	expid = args.expid[0]
	root_name = args.joblist[0]
	save = args.save

	print expid
	l1 = pickle.load(file(LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl", 'r'))

	
	if(args.list):

		for job in l1.get_job_list():
			job.set_status(Status.COMPLETED)
			print "CHANGED: job: " + job.get_name() + " status to: COMPLETED"

		setrecursionlimit(50000)
		l1.update_list()
		pickle.dump(l1, file(LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl", 'w'))



	if(save):
		l1.update_from_file()
	else:
		l1.update_from_file(False)

	if(save):
		setrecursionlimit(50000)
		pickle.dump(l1, file(LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl", 'w'))

	GenerateOutput(expid, l1.get_job_list())
