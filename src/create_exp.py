#!/usr/bin/env python
import dir_config
from sys import exit, argv
from job.job import Job
from job.job_common import Status
from job.job_list import JobList
from job.job_list import RerunJobList
from config_parser import config_parser, expdef_parser, archdef_parser
from monitor import GenerateOutput
from os import path
import cPickle as pickle
from dir_config import LOCAL_ROOT_DIR
import json
import re

def create_json(text):
	list_sd = []
	list_m = []
	list_ms = []
	list_cs = []
	data = []
	pattern_sd = "\d{8}"
	pattern_m = "fc\d"

	tmp = text

	for match in re.findall(pattern_sd, text):
		list_sd.append(match) 

	tmp = re.split(pattern_sd, text)
	for element in tmp:
		if element != "":
			for match in re.split(pattern_m, element):
				cs = match[match.find("[")+1:match.find("]")]
				if cs != "":
					list_cs.append(cs.replace(" ", "").split(","))
			print list_cs
			i = 0
			for match in re.findall(pattern_m, element):
				c = {'m': match, 'cs': list_cs[i] }
				list_m.append(c)
				i = i + 1

			list_ms.append(list_m)
			list_m = []
			list_cs = []
	
	i = 0
	for element in list_sd:
		sd = {'sd': element, 'ms': list_ms[i]}
		data.append(sd)
		i = i + 1
	
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

	expdef = []
	exp_parser = expdef_parser(exp_parser_file)
	for section in exp_parser.sections():
		expdef += exp_parser.items(section)

	arch_parser = archdef_parser(arch_parser_file)
	expdef += arch_parser.items('archdef')

	parameters = dict()

	for item in expdef:
		parameters[item[0]] = item[1]

	date_list = exp_parser.get('experiment','DATELIST').split(' ')
	starting_chunk = int(exp_parser.get('experiment','CHUNKINI'))
	num_chunks = int(exp_parser.get('experiment','NUMCHUNKS'))
	member_list = exp_parser.get('experiment','MEMBERS').split(' ')
	rerun = exp_parser.get('experiment','RERUN').lower()

	if (rerun == 'false'):
		job_list = JobList(expid)
		job_list.create(date_list, member_list, starting_chunk, num_chunks, parameters)
	elif (rerun == 'true'):
		job_list = RerunJobList(expid)
		chunk_list = create_json(exp_parser.get('experiment','CHUNKLIST'))
		job_list.create(chunk_list, starting_chunk, num_chunks, parameters)


	job_list.save()
	GenerateOutput(expid, job_list.get_job_list(), 'pdf')
