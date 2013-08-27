#!/usr/bin/env python
import dir_config
from sys import exit, argv
from job.job import Job
from job.job_common import Status
from job.job_list import JobList
from job.job_list import RerunJobList
from config_parser import config_parser, expdef_parser, archdef_parser, incldef_parser
from monitor import GenerateOutput
from os import path
import cPickle as pickle
from dir_config import LOCAL_ROOT_DIR
import json
from pyparsing import nestedExpr

def get_members(out):
		count = 0
		data = []
		for element in out:
			if (count%2 == 0):
				ms = {'m': out[count], 'cs': get_chunks(out[count+1])}
				data.append(ms)
				count = count + 1
			else:
				count = count + 1

		return data

def get_chunks(out):
	count = 0
	data = []
	for element in out:
		if (element.find("-") != -1):
			numbers = element.split("-")
			for count in range(int(numbers[0]), int(numbers[1])+1):
				data.append(str(count))
		else:
			data.append(element)

	return data

def create_json(text):
	count = 0
	data = []
	#text = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 16651101 [ fc0 [1-30 31 32] ] ]"
	
	out = nestedExpr('[',']').parseString(text).asList()

	for element in out[0]:
		if (count%2 == 0):
			sd = {'sd': out[0][count], 'ms': get_members(out[0][count+1])}
			data.append(sd)
			count = count + 1
		else:
			count = count + 1

	sds = {'sds': data}
	result = json.dumps(sds)
	return result


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
	incl_parser_file = conf_parser.get('config', 'INCLDEFFILE')

	expdef = []
	exp_parser = expdef_parser(exp_parser_file)
	for section in exp_parser.sections():
		expdef += exp_parser.items(section)

	arch_parser = archdef_parser(arch_parser_file)
	expdef += arch_parser.items('archdef')

	incldef = []
	incl_parser = incldef_parser(incl_parser_file)
	incldef += incl_parser.items('incldef')
	incldef = incldef[1:]

	parameters = dict()

	for item in expdef:
		parameters[item[0]] = item[1]
	
	for item in incldef:
		parameters[item[0]] = file(item[1]).read()


	date_list = exp_parser.get('experiment','DATELIST').split(' ')
	starting_chunk = int(exp_parser.get('experiment','CHUNKINI'))
	num_chunks = int(exp_parser.get('experiment','NUMCHUNKS'))
	member_list = exp_parser.get('experiment','MEMBERS').split(' ')
	#if (('RERUN','TRUE') in expdef or ('RERUN','FALSE') in expdef):
	if (exp_parser.has_option('experiment','RERUN')):
		rerun = exp_parser.get('experiment','RERUN').lower()
	else:
		rerun = 'false'

	if (rerun == 'false'):
		job_list = JobList(expid)
		job_list.create(date_list, member_list, starting_chunk, num_chunks, parameters)
	elif (rerun == 'true'):
		job_list = RerunJobList(expid)
		chunk_list = create_json(exp_parser.get('experiment','CHUNKLIST'))
		job_list.create(chunk_list, starting_chunk, num_chunks, parameters)


	job_list.save()
	GenerateOutput(expid, job_list.get_job_list(), 'pdf')
