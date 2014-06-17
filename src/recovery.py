#!/usr/bin/env python

# Copyright 2014 Climatic Forecasting Unit, IC3

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
from queue.mnqueue import MnQueue
from queue.itqueue import ItQueue
from queue.lgqueue import LgQueue
from queue.elqueue import ElQueue
from queue.psqueue import PsQueue
from queue.ecqueue import EcQueue
from queue.mn3queue import Mn3Queue
from queue.htqueue import HtQueue
from queue.arqueue import ArQueue
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

	conf_parser = config_parser(LOCAL_ROOT_DIR + "/" +  expid + "/conf/" + "autosubmit_" + expid + ".conf")
	exp_parser_file = conf_parser.get('config', 'EXPDEFFILE')
	arch_parser_file = conf_parser.get('config', 'ARCHDEFFILE')
	exp_parser = expdef_parser(exp_parser_file)
	arch_parser = archdef_parser(arch_parser_file)

	scratch_dir = arch_parser.get('archdef', 'SCRATCH_DIR')
	hpcproj = exp_parser.get('experiment', 'HPCPROJ')
	hpcuser = exp_parser.get('experiment', 'HPCUSER')
	
	if(args.get):
		sc = expid[0]
		if sc == 'b':
			remoteQueue = MnQueue(expid)
			remoteQueue.set_scratch(scratch_dir)
			remoteQueue.set_project(hpcproj)
			remoteQueue.set_user(hpcuser)
			remoteQueue.update_cmds()
		elif sc == 'i':
			remoteQueue = ItQueue(expid)
			remoteQueue.set_scratch(scratch_dir)
			remoteQueue.set_project(hpcproj)
			remoteQueue.set_user(hpcuser)
			remoteQueue.update_cmds()
		elif sc == 'l':
			## in lindgren arch must set-up both serial and parallel queues
			serialQueue = ElQueue(expid)
			serialQueue.set_scratch(scratch_dir)
			serialQueue.set_project(hpcproj)
			serialQueue.set_user(hpcuser)
			serialQueue.update_cmds()
			parallelQueue = LgQueue(expid)
			parallelQueue.set_scratch(scratch_dir)
			parallelQueue.set_project(hpcproj)
			parallelQueue.set_user(hpcuser)
			parallelQueue.update_cmds()
		elif sc == 'e':
			remoteQueue = EcQueue(expid)
			remoteQueue.set_scratch(scratch_dir)
			remoteQueue.set_project(hpcproj)
			remoteQueue.set_user(hpcuser)
			remoteQueue.update_cmds()
		elif sc == 'm':
			remoteQueue = Mn3Queue(expid)
			remoteQueue.set_scratch(scratch_dir)
			remoteQueue.set_project(hpcproj)
			remoteQueue.set_user(hpcuser)
			remoteQueue.update_cmds()
		elif sc == 'h':
			remoteQueue = HtQueue(expid)
			remoteQueue.set_scratch(scratch_dir)
			remoteQueue.set_project(hpcproj)
			remoteQueue.set_user(hpcuser)
			remoteQueue.update_cmds()
		elif sc == 'a':
			remoteQueue = ArQueue(expid)
			remoteQueue.set_scratch(scratch_dir)
			remoteQueue.set_project(hpcproj)
			remoteQueue.set_user(hpcuser)
			remoteQueue.update_cmds()
		
		localQueue = PsQueue(expid)
		localQueue.set_host(platform.node())
		localQueue.set_scratch("/cfu/autosubmit")
		localQueue.set_project(expid)
		localQueue.set_user("tmp")
		localQueue.update_cmds()


		for job in l1.get_active():
			## in lindgren arch must select serial or parallel queue acording to the job type
			if (sc == 'l' and job.get_type() == Type.SIMULATION):
				queue = parallelQueue
			elif(sc == 'l' and (job.get_type() == Type.INITIALISATION or job.get_type() == Type.CLEANING or job.get_type() == Type.POSTPROCESSING)):
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
