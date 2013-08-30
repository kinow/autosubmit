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
import sys, os
import shutil
import cPickle as pickle
from dir_config import DB_DIR
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

def create_templates(exp_id, template_name, HPC, header):

	dir = DB_DIR + exp_id + '/templates'
	if os.path.exists(dir):
		shutil.rmtree(dir)
	os.mkdir(dir)
	
	print exp_id
	print template_name
	print HPC
	print header

	print "Copying templates files..."
	# list all files in templates of type template_name
	print os.listdir(DB_DIR + exp_id + '/git/templates/' + template_name + "/")
	files = [f for f in os.listdir(DB_DIR + exp_id + '/git/templates/' + template_name + "/") if os.path.isfile(DB_DIR + exp_id + '/git/templates/' + template_name + "/" + f)]
	extensions = set( f[f.index('.'):] for f in files)
	extensions.discard('.conf')
	# merge header and body of template
	for ext in extensions:
		#content = header 
		content = file(DB_DIR + exp_id + "/git/templates/" + template_name + "/" + template_name + ext).read()
		file(DB_DIR + exp_id + "/templates/" + "template_" + exp_id + ext, 'w').write(content)

	# list all files in common templates
	print os.listdir(DB_DIR + exp_id + '/git/templates/common')
	files = [f for f in os.listdir(DB_DIR + exp_id + '/git/templates/common') if os.path.isfile(DB_DIR + exp_id + '/git/templates/common' + "/" + f)]
	extensions= set( f[f.index('.'):] for f in files)
	extensions.discard('.conf')
	# merge header and body of common template
	for ext in extensions:
		#content = header
		content = file(DB_DIR + exp_id + "/git/templates/common/" + "common" + ext).read()
		file(DB_DIR + exp_id + "/templates/" + "template_" + exp_id + ext, 'w').write(content)


####################
# Main Program
####################
if __name__ == "__main__":

	if(len(argv) != 2):
		print "Missing config file or expid."
		exit(1)

	filename = DB_DIR + argv[1] + "/conf/" + "autosubmit_" + argv[1] + ".conf"
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
	incldef = []
	exp_parser = expdef_parser(exp_parser_file)
	for section in exp_parser.sections():
		if (section.startswith('include')):
			items = [x for x in exp_parser.items(section) if x not in exp_parser.items('DEFAULT')]
			incldef += items
		else:
			expdef += exp_parser.items(section)

	arch_parser = archdef_parser(arch_parser_file)
	expdef += arch_parser.items('archdef')

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

	print "Creating templates..."
	create_templates(argv[1], exp_parser.get('DEFAULT','TEMPLATE_NAME'), exp_parser.get('DEFAULT','HPCARCH'), arch_parser.get('archdef','HEADER'))

	if (rerun == 'false'):
		job_list = JobList(expid)
		job_list.create(date_list, member_list, starting_chunk, num_chunks, parameters)
	elif (rerun == 'true'):
		job_list = RerunJobList(expid)
		chunk_list = create_json(exp_parser.get('experiment','CHUNKLIST'))
		job_list.create(chunk_list, starting_chunk, num_chunks, parameters)


	job_list.save()
	GenerateOutput(expid, job_list.get_job_list(), 'pdf')
