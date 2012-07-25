#!/usr/bin/env python

from dir_config import LOCAL_ROOT_DIR
import pickle
from job.job_list import JobList
from job.job_list import RerunJobList
from job.job_common import Status
import argparse
from monitor import GenerateOutput
from queue.mnqueue import MnQueue
from queue.itqueue import ItQueue
from queue.lgqueue import LgQueue
from queue.psqueue import PsQueue
from sys import setrecursionlimit

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Autosubmit recovery')
	parser.add_argument('-e', '--expid', type=str, nargs=1, required=True, help='Experiment ID')
	parser.add_argument('-j', '--joblist', type=str, nargs=1, required=True, help='Job list')
	parser.add_argument('-g', '--get', action="store_true", default=False, help='Get completed files to synchronize pkl')
	parser.add_argument('-s', '--save', action="store_true", default=False, help='Save changes to disk')
	args = parser.parse_args()

	expid = args.expid[0]
	root_name = args.joblist[0]
	save = args.save
	get = args.get

	print expid
	l1 = pickle.load(file(LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl", 'r'))

	if(args.get):
		sc = expid[0]
		if sc == 'b':
			queue = MnQueue(expid)
		elif sc == 'i':
			queue = ItQueue(expid)
		elif sc == 'l':
			## in lindgren arch must set-up both serial and parallel queues
			serialQueue = PsQueue(expid)
			parallelQueue = LgQueue(expid)

		for job in l1.get_active():
			## in lindgren arch must select serial or parallel queue acording to the job type
			if (sc == 'l' and job.get_type() == Type.SIMULATION):
				queue = parallelQueue
			elif(sc == 'l' and (job.get_type() == Type.INITIALISATION or job.get_type() == Type.CLEANING or job.get_type() == Type.POSTPROCESSING)):
				queue = serialQueue
			if queue.get_completed_files(job.get_name()):
				job.set_status(Status.COMPLETED)
				print "CHANGED: job: " + job.get_name() + " status to: COMPLETED"
			else:
				job.set_status(Status.READY)
				job.set_fail_count(0)
				print "CHANGED: job: " + job.get_name() + " status to: READY"

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
