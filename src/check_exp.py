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
from dir_config import LOCAL_ROOT_DIR
from config_parser import config_parser, expdef_parser, archdef_parser
import argparse
from os import path


def print_parameters(title, parameters):
	"""Prints the parameters table in a tabular mode"""
	print title
	print "----------------------"
	print "{0:<{col1}}| {1:<{col2}}".format("-- Parameter --","-- Value --",col1=15,col2=15)
	for i in parameters:
		print "{0:<{col1}}| {1:<{col2}}".format(i[0],i[1],col1=15,col2=15)
	print ""

def check_experiment(autosubmit_def_filename):
	"""Function to read configuration files of Experiment, Platform and Autosubmit.
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
	arch_parser_file = conf_parser.get('config', 'ARCHDEFFILE')
	
	exp_parser = expdef_parser(exp_parser_file)
	arch_parser = archdef_parser(arch_parser_file)


	for section in conf_parser.sections():
		if ("" in [item[1] for item in conf_parser.items(section)]):
			result = False
			print_parameters("AUTOSUBMIT PARAMETERS - " + section, conf_parser.items(section))
	for section in exp_parser.sections():
		if ("" in [item[1] for item in exp_parser.items(section)]):
			result = False
			print_parameters("EXPERIMENT PARAMETERS - " + section, exp_parser.items(section))
	for section in arch_parser.sections():
		if ("" in [item[1] for item in arch_parser.items(section)]):
			result = False
			print_parameters("PLATFORM PARAMETERS - " + section, arch_parser.items(section))


	#if result:
	#	print "Experiment configuration check PASSED!"
	#else:
	#	print "Experiment configuration check FAILED! ..."

	return result


####################
# Main Program
####################
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Check autosubmit, experiment and platform configurations given a experiment identifier')
	parser.add_argument('-e', '--expid', required=True, nargs = 1)
	args = parser.parse_args()
	if args.expid is None:
		parser.error("Missing expid.")

	autosubmit_def_filename = LOCAL_ROOT_DIR + "/" + args.expid[0] + "/conf/" + "autosubmit_" + args.expid[0] + ".conf"

	if check_experiment(autosubmit_def_filename):
		print "Experiment configuration check PASSED!"
	else:
		print "Experiment configuration check FAILED!"
		print "WARNING: running after FAILED experiment configuration check is at your own risk!!!"
