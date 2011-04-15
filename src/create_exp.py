#!/usr/bin/env python
import dir_config
from sys import exit, argv
from job.job import Job
from job.job_common import Status
from job.job_list import JobList
from config_parser import config_parser, expdef_parser, archdef_parser
from monitor import CreateTreeList
from os import path
import cPickle as pickle


####################
# Main Program
####################
if __name__ == "__main__":

	if(len(argv) != 2):
		print "Missing config file or expid."
		exit(1)

	if (path.exists(argv[1])):
		conf_parser = config_parser(argv[1])
		#joblist = pickle.load(file(argv[2], 'rw'))
		print "Using config file: %s" % argv[1]
	else:
		print "The config file %s necessary does not exist." % argv[1]
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
	CreateTreeList(expid, job_list.get_job_list())
