#!/usr/bin/env python
import dir_config
from sys import exit, argv
from job.job import Job
from job.job_common import Status
from job.job_list import JobList
from config_parser import config_parser, expdef_parser, archdef_parser
from monitor import GenerateOutput
from os import path
import cPickle as pickle
from dir_config import LOCAL_ROOT_DIR


####################
# Main Program
####################
if __name__ == "__main__":

	if(len(argv) != 2):
		print "Missing config file or expid."
		exit(1)

	filename = LOCAL_ROOT_DIR + "/" + argv[1] + "/conf/" + "autosubmit_" + argv[1] + ".conf"
	if (path.exists(filename)):
		conf_parser = config_parser(filename)
		print "Using config file: %s" % filename
	else:
		print "The config file %s necessary does not exist." % filename
		exit(1)


	expid = conf_parser.get('config', 'expid')

	exp_parser_file = conf_parser.get('config', 'EXPDEFFILE')
	arch_parser_file = conf_parser.get('config', 'ARCHDEFFILE')

	job_list = JobList(expid)

	exp_parser = expdef_parser(exp_parser_file)
	expdef = exp_parser.items('expdef')

	arch_parser = archdef_parser(arch_parser_file)
	expdef += arch_parser.items('archdef')

	parameters = dict()

	for item in expdef:
		parameters[item[0]] = item[1]

	date_list = exp_parser.get('expdef','DATELIST').split(' ')
	starting_chunk = int(exp_parser.get('expdef','CHUNKINI'))
	num_chunks = int(exp_parser.get('expdef','NUMCHUNKS'))
	member_list = exp_parser.get('expdef','MEMBERS').split(' ')

	job_list.create(date_list, member_list, starting_chunk, num_chunks, parameters)
	job_list.save()
	GenerateOutput(expid, job_list.get_job_list(), 'pdf')
