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
from config_common import AutosubmitConfig
from monitor import GenerateOutput
from dir_config import LOCAL_ROOT_DIR
from dir_config import LOCAL_GIT_DIR

"""This is the code to create the job list. It reads the experiment configuration files and creates the parameter structure and writes it in a .pkl file"""

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

	as_conf = AutosubmitConfig(args.expid[0])
	
	expid = as_conf.get_expid()
	git_project = as_conf.get_git_project()

	print ""

	if (git_project == "true"):
		git_project_origin = as_conf.get_git_project_origin()
		git_project_branch = as_conf.get_git_project_branch
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

	# Load parameters
	print "Loading parameters..."
	parameters = as_conf.load_parameters()
			
	date_list = as_conf.get_date_list()
	starting_chunk = as_conf.get_starting_chunk()
	num_chunks = as_conf.get_num_chunks()
	member_list = as_conf.get_member_list()
	rerun = as_conf.get_rerun()

	print ""

	if (rerun == "false"):
		job_list = JobList(expid)
		job_list.create(date_list, member_list, starting_chunk, num_chunks, parameters)
	elif (rerun == "true"):
		job_list = RerunJobList(expid)
		chunk_list = create_json(exp_parser.get('experiment','CHUNKLIST'))
		job_list.create(chunk_list, starting_chunk, num_chunks, parameters)

	platform = as_conf.get_platform()
	if (platform == 'hector' or platform == 'archer'):
		job_list.update_shortened_names()

	job_list.save()
	GenerateOutput(expid, job_list.get_job_list(), 'pdf')


if __name__ == "__main__":
	main()
