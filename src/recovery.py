#!/usr/bin/env python

from dir_config import LOCAL_ROOT_DIR
import pickle
from job.job_list import JobList
from job.job_common import Status
import argparse
from monitor import GenerateOutput

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Autosubmit recovery')
	parser.add_argument('-e', '--expid', type=str, nargs=1, required=True, help='Experiment ID')
	parser.add_argument('-s', '--save', action="store_true", default=False )
	args = parser.parse_args()

	expid = args.expid[0]
	save = args.save
	print expid
	l1 = pickle.load(file(LOCAL_ROOT_DIR + "/" + expid + "/" + "/pkl/job_list_" + expid + ".pkl", 'r'))
	l1.update_from_file()
	GenerateOutput(expid, l1.get_job_list())

	if(save):
		pickle.dump(l1, file(LOCAL_ROOT_DIR + "/" + expid + "/" + "/pkl/job_list_" + expid + ".pkl", 'w'))
