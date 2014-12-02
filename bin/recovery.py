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

"""Script for handling experiment recovery after crash or job failure"""
import os
import sys
scriptdir = os.path.abspath(os.path.dirname(sys.argv[0]))
assert sys.path[0] == scriptdir
sys.path[0] = os.path.normpath(os.path.join(scriptdir, os.pardir))
import argparse
import platform
import pickle
from pkg_resources import require
from autosubmit.queue.mnqueue import MnQueue
from autosubmit.queue.itqueue import ItQueue
from autosubmit.queue.lgqueue import LgQueue
from autosubmit.queue.elqueue import ElQueue
from autosubmit.queue.psqueue import PsQueue
from autosubmit.queue.ecqueue import EcQueue
from autosubmit.queue.mn3queue import Mn3Queue
from autosubmit.queue.htqueue import HtQueue
from autosubmit.queue.arqueue import ArQueue
from autosubmit.job.job_list import JobList
from autosubmit.job.job_list import RerunJobList
from autosubmit.job.job_common import Status
from autosubmit.job.job_common import Type
from autosubmit.config.dir_config import LOCAL_ROOT_DIR
from autosubmit.config.dir_config import LOCAL_TMP_DIR
from autosubmit.config.config_common import AutosubmitConfig
from autosubmit.monitor.monitor import Monitor

####################
# Main Program
####################
def main():
	autosubmit_version = require("autosubmit")[0].version

	parser = argparse.ArgumentParser(description='Autosubmit recovery')
	parser.add_argument('-v', '--version', action='version', version=autosubmit_version)
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

	as_conf = AutosubmitConfig(expid)
	as_conf.check_conf()
	
	hpcarch = as_conf.get_platform()
	scratch_dir = as_conf.get_scratch_dir()
	hpcproj = as_conf.get_hpcproj()
	hpcuser = as_conf.get_hpcuser()
	
	if(args.get):
		if hpcarch == 'bsc':
			remoteQueue = MnQueue(expid)
			remoteQueue.set_scratch(scratch_dir)
			remoteQueue.set_project(hpcproj)
			remoteQueue.set_user(hpcuser)
			remoteQueue.set_host("bsc")
			remoteQueue.update_cmds()
		elif hpcarch == 'ithaca':
			remoteQueue = ItQueue(expid)
			remoteQueue.set_scratch(scratch_dir)
			remoteQueue.set_project(hpcproj)
			remoteQueue.set_user(hpcuser)
			remoteQueue.set_host("ithaca")
			remoteQueue.update_cmds()
		elif hpcarch == 'lindgren':
			## in lindgren arch must set-up both serial and parallel queues
			serialQueue = ElQueue(expid)
			serialQueue.set_scratch(scratch_dir)
			serialQueue.set_project(hpcproj)
			serialQueue.set_user(hpcuser)
			serialQueue.set_host("lindgren")
			serialQueue.update_cmds()
			parallelQueue = LgQueue(expid)
			parallelQueue.set_scratch(scratch_dir)
			parallelQueue.set_project(hpcproj)
			parallelQueue.set_user(hpcuser)
			parallelQueue.set_host("ellen")
			parallelQueue.update_cmds()
		elif hpcarch == 'ecmwf':
			remoteQueue = EcQueue(expid)
			remoteQueue.set_scratch(scratch_dir)
			remoteQueue.set_project(hpcproj)
			remoteQueue.set_user(hpcuser)
			remoteQueue.set_host("c2a")
			remoteQueue.update_cmds()
		elif hpcarch == 'marenostrum3':
			remoteQueue = Mn3Queue(expid)
			remoteQueue.set_scratch(scratch_dir)
			remoteQueue.set_project(hpcproj)
			remoteQueue.set_user(hpcuser)
			remoteQueue.set_host("mn-" + hpcproj)
			remoteQueue.update_cmds()
		elif hpcarch == 'hector':
			remoteQueue = HtQueue(expid)
			remoteQueue.set_scratch(scratch_dir)
			remoteQueue.set_project(hpcproj)
			remoteQueue.set_user(hpcuser)
			remoteQueue.set_host("ht-" + hpcproj)
			remoteQueue.update_cmds()
		elif hpcarch == 'archer':
			remoteQueue = ArQueue(expid)
			remoteQueue.set_scratch(scratch_dir)
			remoteQueue.set_project(hpcproj)
			remoteQueue.set_user(hpcuser)
			remoteQueue.set_host("ar-" + hpcproj)
			remoteQueue.update_cmds()
		
		localQueue = PsQueue(expid)
		localQueue.set_host(platform.node())
		localQueue.set_scratch(LOCAL_ROOT_DIR)
		localQueue.set_project(expid)
		localQueue.set_user(LOCAL_TMP_DIR)
		localQueue.update_cmds()


		for job in l1.get_active():
			## in lindgren arch must select serial or parallel queue acording to the job type
			if (hpcarch == 'lindgren' and job.get_type() == Type.SIMULATION):
				queue = parallelQueue
			elif(hpcarch == 'lindgren' and (job.get_type() == Type.INITIALISATION or job.get_type() == Type.CLEANING or job.get_type() == Type.POSTPROCESSING)):
				queue = serialQueue
			elif(job.get_type() == Type.LOCALSETUP or job.get_type() == Type.TRANSFER):
				queue = localQueue
			else:
				queue = remoteQueue
			if queue.get_completed_files(job.get_name()):
				job.set_status(Status.COMPLETED)
				print "CHANGED: job: " + job.get_name() + " status to: COMPLETED"
			elif(job.get_status() != Status.SUSPENDED):
				job.set_status(Status.READY)
				job.set_fail_count(0)
				print "CHANGED: job: " + job.get_name() + " status to: READY"

		sys.setrecursionlimit(50000)
		l1.update_list()
		pickle.dump(l1, file(LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl", 'w'))



	if(save):
		l1.update_from_file()
	else:
		l1.update_from_file(False)

	if(save):
		sys.setrecursionlimit(50000)
		pickle.dump(l1, file(LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl", 'w'))

	monitor_exp = Monitor()
	monitor_exp.GenerateOutput(expid, l1.get_job_list())

if __name__ == '__main__':
	main()
