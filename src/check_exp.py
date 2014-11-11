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

"""Functions for handling experiment parameters check"""
import argparse
from os import path
from job.job_common import Status
from job.job_common import Type
from job.job import Job
from job.job_list import JobList
from dir_config import LOCAL_ROOT_DIR
from dir_config import LOCAL_GIT_DIR
from config_parser import config_parser
from config_parser import expdef_parser
from config_parser import pltdef_parser
from config_parser import moddef_parser


def print_parameters(title, parameters):
	"""Prints the parameters table in a tabular mode"""
	print title
	print "----------------------"
	print "{0:<{col1}}| {1:<{col2}}".format("-- Parameter --","-- Value --",col1=15,col2=15)
	for i in parameters:
		print "{0:<{col1}}| {1:<{col2}}".format(i[0],i[1],col1=15,col2=15)
	print ""

def load_parameters(conf_parser_file):
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

	return parameters


def check_templates(autosubmit_def_filename):
	"""Procedure to check autogeneration of templates given 
	Experiment, Platform and Autosubmit configuration files.
	Returns True if all variables are set.
	If the parameters are not correctly replaced, the function returns
	False and the check fails.

	:param autosubmit_def_filename: path to the Autosubmit configuration file
	:type: str
	:retruns: bool
	"""
	out = True

	parameters = load_parameters(autosubmit_def_filename)
	joblist = JobList(parameters['EXPID'])
	joblist.create(parameters['DATELIST'].split(' '),parameters['MEMBERS'].split(' '),int(parameters['CHUNKINI']),int(parameters['NUMCHUNKS']),parameters)
	out = joblist.check_scripts()
	
	return out




def check_parameters(autosubmit_def_filename):
	"""Function to read configuration files of Experiment and Autosubmit.
	Returns True if all variables are set.
	If the parameters do not exist, the function returns False and the check fails.
	
	:param autosubmit_def_filename: path to the Autosubmit configuration file
	:type: str
	:retruns: bool
	"""

	result = True
	if (path.exists(autosubmit_def_filename)):
		conf_parser = config_parser(autosubmit_def_filename)
		print "Using config file: %s" % autosubmit_def_filename
	else:
		print "The config file %s necessary does not exist." % autosubmit_def_filename
		exit(1)

	exp_parser_file = conf_parser.get('config', 'EXPDEFFILE')
	exp_parser = expdef_parser(exp_parser_file)
	plt_parser_file = exp_parser.get('git', 'GIT_FILE_PLATFORM_CONF')
	plt_parser = pltdef_parser(LOCAL_ROOT_DIR + "/" + args.expid[0] + "/" + LOCAL_GIT_DIR + "/" + plt_parser_file)
	mod_parser_file = exp_parser.get('git', 'GIT_FILE_MODEL_CONF')
	mod_parser = moddef_parser(LOCAL_ROOT_DIR + "/" + args.expid[0] + "/" + LOCAL_GIT_DIR + "/" + mod_parser_file)

	for section in conf_parser.sections():
		if ("" in [item[1] for item in conf_parser.items(section)]):
			result = False
			print_parameters("AUTOSUBMIT PARAMETERS - " + section, conf_parser.items(section))
	for section in exp_parser.sections():
		if ("" in [item[1] for item in exp_parser.items(section)]):
			result = False
			print_parameters("EXPERIMENT PARAMETERS - " + section, exp_parser.items(section))
	for section in plt_parser.sections():
		if ("" in [item[1] for item in plt_parser.items(section)]):
			result = False
			print_parameters("PLATFORM PARAMETERS - " + section, plt_parser.items(section))
	for section in mod_parser.sections():
		if ("" in [item[1] for item in mod_parser.items(section)]):
			result = False
			print_parameters("MODEL PARAMETERS - " + section, mod_parser.items(section))

	return result


####################
# Main Program
####################
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Check autosubmit and experiment configurations given a experiment identifier. Check templates creation with those configurations')
	parser.add_argument('-e', '--expid', required=True, nargs = 1)
	args = parser.parse_args()
	if args.expid is None:
		parser.error("Missing expid.")

	autosubmit_def_filename = LOCAL_ROOT_DIR + "/" + args.expid[0] + "/conf/" + "autosubmit_" + args.expid[0] + ".conf"

	print "Checking experiment configuration..."
	if check_parameters(autosubmit_def_filename):
		print "Experiment configuration check PASSED!"
	else:
		print "Experiment configuration check FAILED!"
		print "WARNING: running after FAILED experiment configuration check is at your own risk!!!"

	print "Checking experiment templates..."
	if check_templates(autosubmit_def_filename):
		print "Experiment templates check PASSED!"
	else:	
		print "Experiment templates check FAILED!"
		print "WARNING: running after FAILED experiment templates check is at your own risk!!!"


