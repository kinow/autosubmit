#!/usr/bin/env python

import pickle
l1=pickle.load(file('../auxfiles/failed_job_list_dumi.pkl', 'r'))
l2=pickle.load(file('../auxfiles/job_list_dumi.pkl', 'r'))
from job.job_list import JobList
from queue.mnqueue import MnQueue as queue
from queue.mnqueue import MnQueue as MnQueue
from queue.hpcqueue import HPCQueue as HPCQueue
queue = MnQueue('dumi')
for x in l2.get_active():
	print x.get_name() + " " + str(x.get_status())
for x in l2.get_active():
	if queue.get_completed_files(x.get_name()):
		x.set_status(Status.COMPLETED)
	else:
		x.set_status(Status.READY)
l2.job_list += l1
for x in l2.get_failed():
	x.set_fail_count(0)
	x.set_status(Status.READY)
