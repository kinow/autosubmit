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

import os
import sys
import shutil
import re
import argparse
from distutils.util import strtobool
from commands import getstatusoutput
from pkg_resources import require
from pkg_resources import resource_string
from pkg_resources import resource_exists
from pkg_resources import resource_listdir
from autosubmit.database.db_common import new_experiment
from autosubmit.database.db_common import copy_experiment
from autosubmit.database.db_common import delete_experiment
from autosubmit.config.dir_config import LOCAL_ROOT_DIR

def user_yes_no_query(question):
	sys.stdout.write('%s [y/n]\n' % question)
	while True:
		try:
			return strtobool(raw_input().lower())
		except ValueError:
			sys.stdout.write('Please respond with \'y\' or \'n\'.\n')

#############################
# Conf files
#############################
def prepare_conf_files(content, exp_id, hpc, autosubmit_version):
	if re.search('EXPID =.*', content):
		content = content.replace(re.search('EXPID =.*', content).group(0), "EXPID = " + exp_id)
	if re.search('HPCARCH =.*', content):
		content = content.replace(re.search('HPCARCH =.*', content).group(0), "HPCARCH = " + hpc)
	if re.search('AUTOSUBMIT_VERSION =.*', content):
		content = content.replace(re.search('AUTOSUBMIT_VERSION =.*', content).group(0), "AUTOSUBMIT_VERSION = " + autosubmit_version)
	if re.search('AUTOSUBMIT_LOCAL_ROOT =.*', content):
		content = content.replace(re.search('AUTOSUBMIT_LOCAL_ROOT =.*', content).group(0), "AUTOSUBMIT_LOCAL_ROOT = " + LOCAL_ROOT_DIR)

	if re.search('SAFETYSLEEPTIME =.*', content):
		if hpc == "bsc":
			content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 10")
		elif hpc == "hector":
			content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 300")
		elif hpc == "ithaca":
			content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 10")
		elif hpc == "lindgren":
			content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 300")
		elif hpc == "ecmwf":
			content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 300")
		elif hpc == "marenostrum3": 
			content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 300")
		elif hpc == "archer": 
			content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 300")

	if re.search('SCRATCH_DIR =.*', content):
		if hpc == "bsc":
			content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /gpfs/scratch/ecm86")
		elif hpc == "hector":
			content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /work/pr1u1011")
		elif hpc == "ithaca":
			content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /scratch")
		elif hpc == "lindgren":
			content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /cfs/scratch")
		elif hpc == "ecmwf":
			content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /scratch/ms")
		elif hpc == "marenostrum3": 
			content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /gpfs/scratch")
		elif hpc == "archer": 
			content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /work/pr1u1011")


	return content

####################
# Main Program
####################
def main():
	##obtain version for autosubmit being used in expid.py step
	#autosubmit_version = file(os.path.join(package_dir, 'VERSION'),'r').read()
	#autosubmit_version = resource_string('autosubmit', 'VERSION')
	autosubmit_version = require("autosubmit")[0].version

	parser = argparse.ArgumentParser()
	group1 = parser.add_mutually_exclusive_group(required = True)
	group1.add_argument('--new', '-n', action = "store_true")
	group1.add_argument('--copy', '-y', type = str)
	group1.add_argument('--delete', '-D', type = str)
	group2 = parser.add_argument_group('experiment arguments')
	group2.add_argument('--HPC', '-H', choices = ('bsc', 'hector', 'ithaca', 'lindgren', 'ecmwf', 'marenostrum3', 'archer'))
	group2.add_argument('--description', '-d', type = str)

	args = parser.parse_args()
	if args.new is None and args.copy is None and args.delete is None:
		parser.error("Missing method either New or Copy or Delete.")
	if args.new:
		if args.description is None:
			parser.error("Missing experiment description.")
		if args.HPC is None:
			parser.error("Missing HPC.");

		exp_id = new_experiment(args.HPC, args.description)
		os.mkdir(LOCAL_ROOT_DIR + "/" + exp_id)
		
		os.mkdir(LOCAL_ROOT_DIR + "/" + exp_id + '/conf')
		print "Copying config files..."
		##autosubmit config and architecture copyed from AS.
		files = resource_listdir('autosubmit.config', 'files')
		for filename in files:
			if resource_exists('autosubmit.config', 'files/' + filename):
				index = filename.index('.')
				new_filename = filename[:index] + "_" + exp_id + filename[index:]
				content = resource_string('autosubmit.config', 'files/' + filename)
				content = prepare_conf_files(content, exp_id, args.HPC, autosubmit_version)
				print LOCAL_ROOT_DIR + "/" + exp_id + "/conf/" + new_filename
				file(LOCAL_ROOT_DIR + "/" + exp_id + "/conf/" + new_filename, 'w').write(content)

		content = file(LOCAL_ROOT_DIR + "/" + exp_id + "/conf/expdef_" + exp_id + ".conf").read()
		file(LOCAL_ROOT_DIR + "/" + exp_id + "/conf/expdef_" + exp_id + ".conf", 'w').write(content)

	elif args.copy:
		if args.description is None:
			parser.error("Missing experiment description.")
		if args.HPC is None:
			parser.error("Missing HPC.");

		if os.path.exists(LOCAL_ROOT_DIR + "/" + args.copy):
			exp_id = copy_experiment(args.copy, args.HPC, args.description)
			os.mkdir(LOCAL_ROOT_DIR + "/" + exp_id)
			os.mkdir(LOCAL_ROOT_DIR + "/" + exp_id + '/conf')
			print "Copying previous experiment config directories"
			files = os.listdir(LOCAL_ROOT_DIR + "/" + args.copy + "/conf")
			for filename in files:
				if os.path.isfile(LOCAL_ROOT_DIR + "/" + args.copy + "/conf/" + filename):
					new_filename = filename.replace(args.copy, exp_id)
					content = file(LOCAL_ROOT_DIR + "/" + args.copy + "/conf/" + filename, 'r').read()
					content = prepare_conf_files(content, exp_id, args.HPC, autosubmit_version)
					file(LOCAL_ROOT_DIR + "/" + exp_id + "/conf/" + new_filename, 'w').write(content)
		else:
			print "The previous experiment directory does not exist"
			sys.exit(1)
	
	elif args.delete:
		if os.path.exists(LOCAL_ROOT_DIR + "/" + args.delete):
			if user_yes_no_query("Do you want to delete " + args.delete + " ?"):
				print "Removing experiment directory..."
				shutil.rmtree(LOCAL_ROOT_DIR + "/" + args.delete)
				print "Deleting experiment from database..."
				delete_experiment(args.delete)
			else:
				print "Quitting..."
				sys.exit(1)
		else:
			print "The experiment does not exist"
			sys.exit(1)
	
	print "Creating temporal directory..."
	os.mkdir(LOCAL_ROOT_DIR + "/" +exp_id+"/"+"tmp")
	print "Creating pkl directory..."
	os.mkdir(LOCAL_ROOT_DIR + "/" +exp_id+"/"+"pkl")
	print "Creating plot directory..."
	os.mkdir(LOCAL_ROOT_DIR + "/" +exp_id+"/"+"plot")
	os.chmod(LOCAL_ROOT_DIR + "/" +exp_id+"/"+"plot",0o775)
	print "Remember to MODIFY the config files!"

if __name__ == "__main__":
	main()
