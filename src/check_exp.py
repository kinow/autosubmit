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
from config_common import AutosubmitConfig

def check_templates(as_conf):
	"""Procedure to check autogeneration of templates given 
	Autosubmit configuration.
	Returns True if all variables are set.
	If the parameters are not correctly replaced, the function returns
	False and the check fails.

	:param as_conf: Autosubmit configuration object
	:type: AutosubmitConf
	:retruns: bool
	"""
	out = True

	parameters = as_conf.load_parameters()
	joblist = JobList(parameters['EXPID'])
	joblist.create(parameters['DATELIST'].split(' '),parameters['MEMBERS'].split(' '),int(parameters['CHUNKINI']),int(parameters['NUMCHUNKS']),parameters)
	out = joblist.check_scripts()
	
	return out



####################
# Main Program
####################
def main():

	parser = argparse.ArgumentParser(description='Check autosubmit and experiment configurations given a experiment identifier. Check templates creation with those configurations')
	parser.add_argument('-e', '--expid', required=True, nargs = 1)
	args = parser.parse_args()
	if args.expid is None:
		parser.error("Missing expid.")

	as_conf = AutosubmitConfig(args.expid[0])

	print "Checking experiment configuration..."
	if as_conf.check_parameters():
		print "Experiment configuration check PASSED!"
	else:
		print "Experiment configuration check FAILED!"
		print "WARNING: running after FAILED experiment configuration check is at your own risk!!!"

	print "Checking experiment templates..."
	if check_templates(as_conf):
		print "Experiment templates check PASSED!"
	else:	
		print "Experiment templates check FAILED!"
		print "WARNING: running after FAILED experiment templates check is at your own risk!!!"

if __name__ == "__main__":
	main()
