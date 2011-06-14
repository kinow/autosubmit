#!/usr/bin/env python

from dir_config import LOCAL_ROOT_DIR
import pickle
from job.job_list import JobList
from job.job_common import Status
from queue.mnqueue import MnQueue as MnQueue
from queue.itqueue import ItQueue as ItQueue
from queue.hpcqueue import HPCQueue as HPCQueue
import argparse

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Autosubmit recovery')
	parser.add_argument('-e', '--expid', type=str, nargs=1, required=True, help='Experiment ID')
	parser.add_argument('--HPC', '-H', nargs = 1, choices = ('bsc', 'hector', 'ithaca'))
	args = parser.parse_args()

	expid = args.expid[0]
	hpcarch = args.HPC[0]
	print expid
	l1=pickle.load(file(LOCAL_ROOT_DIR + "/" + expid + "/" + "/pkl/failed_job_list_" + expid + ".pkl", 'r'))
	l2=pickle.load(file(LOCAL_ROOT_DIR + "/" + expid + "/" + "/pkl/job_list_" + expid + ".pkl", 'r'))

	if(hpcarch== "bsc"):
	   queue = MnQueue(expid)
	elif(hpcarch == "ithaca"):
	   queue = ItQueue(expid)
	elif(hpcarch == "hector"):
	   queue = HtQueue(expid)

	for x in l2.get_active():
		print x.get_name() + " " + str(x.get_status())
	for x in l2.get_active():
		if queue.get_completed_files(x.get_name()):
			x.set_status(Status.COMPLETED)
		else:
			x.set_status(Status.READY)
	l2._job_list += l1
	for x in l2.get_failed():
		x.set_fail_count(0)
		x.set_status(Status.READY)
	pickle.dump(l2, file(LOCAL_ROOT_DIR + "/" + expid + "/" + "/pkl/new_job_list_" + expid + ".pkl", 'w'))
