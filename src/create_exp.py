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


import argparse
import shutil
import json
import cPickle as pickle
from commands import getstatusoutput
from pyparsing import nestedExpr
from os import path
from os import mkdir
from job.job import Job
from job.job_common import Status
from job.job_list import JobList
from job.job_list import RerunJobList
from config_parser import config_parser
from config_parser import expdef_parser
from config_parser import pltdef_parser
from config_parser import moddef_parser
from monitor import GenerateOutput
from dir_config import LOCAL_ROOT_DIR
from dir_config import LOCAL_GIT_DIR

"""This is the code to create the job list. It reads the experiment configuration files and creates the parameter structure and writes it in a .pkl file"""

def check_parameters(conf_parser_file):
	conf_parser = config_parser(conf_parser_file)
	exp_parser_file = conf_parser.get('config', 'EXPDEFFILE')
	exp_parser = expdef_parser(exp_parser_file)

	expdef = []
	incldef = []
	for section in exp_parser.sections():
		if (section.startswith('include')):
			items = [x for x in exp_parser.items(section) if x not in exp_parser.items('DEFAULT')]
			incldef += items
		else:
			expdef += exp_parser.items(section)

	parameters = dict()
	for item in expdef:
		parameters[item[0]] = item[1]
	for item in incldef:
		parameters[item[0]] = file(item[1]).read()

	git_project = exp_parser.get('experiment','GIT_PROJECT').lower()
	if (git_project == "true"):
		# Check additional parameters changes
		print "Checking additional parameters..."
		parameters.append(check_additonal_parameters(conf_parser_file))

	return parameters


def check_additional_parameters(conf_parser_file):
	conf_parser = config_parser(conf_parser_file)
	exp_parser_file = conf_parser.get('config', 'EXPDEFFILE')
	exp_parser = expdef_parser(exp_parser_file)

	pltdef = []
	moddef = []
	plt_parser_file = exp_parser.get('git', 'GIT_FILE_PLATFORM_CONF')
	plt_parser = pltdef_parser(LOCAL_ROOT_DIR + "/" + args.expid[0] + "/" + LOCAL_GIT_DIR + "/" + plt_parser_file)
	mod_parser_file = exp_parser.get('git', 'GIT_FILE_MODEL_CONF')
	mod_parser = moddef_parser(LOCAL_ROOT_DIR + "/" + args.expid[0] + "/" + LOCAL_GIT_DIR + "/" + mod_parser_file)

	for section in plt_parser.sections():
		pltdef += plt_parser.items(section)
	for section in mod_parser.sections():
		moddef += mod_parser.items(section)
	
	parameters = dict()
	for item in pltdef:
		parameters[item[0]] = item[1]
	for item in moddef:
		parameters[item[0]] = item[1]

	return parameters


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
def main():
	
	parser = argparse.ArgumentParser(description='Create pickle given an experiment identifier')
	parser.add_argument('-e', '--expid', required=True, nargs = 1)
	args = parser.parse_args()
	if args.expid is None:
		parser.error("Missing expid.")

	conf_parser_file = LOCAL_ROOT_DIR + "/" + args.expid[0] + "/conf/" + "autosubmit_" + args.expid[0] + ".conf"
	conf_parser = config_parser(conf_parser_file)
	exp_parser_file = conf_parser.get('config', 'EXPDEFFILE')
	exp_parser = expdef_parser(exp_parser_file)
	
	expid = conf_parser.get('config', 'EXPID')
	git_project = exp_parser.get('experiment','GIT_PROJECT').lower()

	print ""

	if (git_project == "true"):
		git_project_origin = exp_parser.get('git','GIT_PROJECT_ORIGIN').lower()
		git_project_branch = exp_parser.get('git','GIT_PROJECT_BRANCH').lower()
		git_project_path = LOCAL_ROOT_DIR + "/" + args.expid[0] + "/" + LOCAL_GIT_DIR
		if (path.exists(git_project_path)):
			print "The git folder exists. SKIPPING..."
			print "Using git folder: %s" % git_project_path
		else:
			mkdir(git_project_path)
			print "The git folder %s has been created." % git_project_path
			print "Cloning %s into %s" % (git_project_branch + " " + git_project_origin, git_project_path)
			(status, output) = getstatusoutput("cd " + git_project_path + "; git clone -b " + git_project_branch + " " + git_project_origin)
			print "%s" % output
			git_project_name = output[output.find("'")+1:output.find("...")-1] 
			(status, output) = getstatusoutput("cd " + git_project_path + "/" + git_project_name + "; git submodule update --remote --init")
			print "%s" % output
			(status, output) = getstatusoutput("cd " + git_project_path + "/" + git_project_name + "; git submodule foreach -q 'branch=\"$(git config -f $toplevel/.gitmodules submodule.$name.branch)\"; git checkout $branch'")
			print "%s" % output

	# Check parameters changes
	print "Checking parameters..."
	parameters = check_parameters(conf_parser_file)
			
	date_list = exp_parser.get('experiment','DATELIST').split(' ')
	starting_chunk = int(exp_parser.get('experiment','CHUNKINI'))
	num_chunks = int(exp_parser.get('experiment','NUMCHUNKS'))
	member_list = exp_parser.get('experiment','MEMBERS').split(' ')
	rerun = exp_parser.get('experiment','RERUN').lower()

	print ""

	if (rerun == "false"):
		job_list = JobList(expid)
		job_list.create(date_list, member_list, starting_chunk, num_chunks, parameters)
	elif (rerun == "true"):
		job_list = RerunJobList(expid)
		chunk_list = create_json(exp_parser.get('experiment','CHUNKLIST'))
		job_list.create(chunk_list, starting_chunk, num_chunks, parameters)

	platform = exp_parser.get('experiment', 'HPCARCH')
	if (platform == 'hector' or platform == 'archer'):
		job_list.update_shortened_names()

	job_list.save()
	GenerateOutput(expid, job_list.get_job_list(), 'pdf')


if __name__ == "__main__":
	main()
