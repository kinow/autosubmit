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

import sys
import re
from os import path
from ConfigParser import SafeConfigParser

invalid_values = False

def check_values(key, value, valid_values):
	global invalid_values

	if(value.lower() not in valid_values): 
		print "Invalid value %s: %s" %(key, value)
		invalid_values = True

def check_regex(key, value, regex):
	global invalid_values

	prog = re.compile(regex)

	if(not prog.match(value.lower())):
		print "Invalid value %s: %s" %(key,value)
		invalid_values = True

def config_parser(filename):
	runmode = ['local', 'remote']
	loglevel = ['debug', 'info', 'warning', 'error', 'critical']
	alreadysubmitted = "\s*\d+\s*$" 
		
	# check file existance
	if(not path.isfile(filename)):
		print "File does not exist: " + filename
		sys.exit()

	# load values
	parser = SafeConfigParser()
	parser.optionxform = str
	parser.read(filename)
	
	check_values('RUNMODE', parser.get('config', 'RUNMODE'), runmode)
	check_values('LOGLEVEL', parser.get('config', 'LOGLEVEL'), loglevel)
	check_regex('ALREADYSUBMITTED', parser.get('config', 'ALREADYSUBMITTED'), alreadysubmitted)

	if(invalid_values):
		print "\nInvalid Autosubmit config file"
		sys.exit()
	else:
		print "\nAutosubmit config file OK"

	return parser


def expdef_parser(filename):
	hpcarch = ['bsc', 'ithaca', 'lindgren', 'ecmwf', 'marenostrum3', 'hector', 'archer']
	startdate = "(\s*[0-9]{4}[0-9]{2}[0-9]{2}\s*)+$"
	chunkini = "\s*\d+\s*$"
	numchunks = "\s*\d+\s*$"
	members = "(\s*fc\d+\s*)+$"
	rerun = "\s*(true|false)\s*$"
	
	#option that must be in config file and has no default value
	mandatory_opt = ['EXPID']

	# check file existance
	if(not path.isfile(filename)):
		print "File does not exist"
		sys.exit()

	# load values
	parser = SafeConfigParser()
	parser.optionxform = str
	parser.read(filename)

	# check which options of the mandatory one are not in config file
	missing = list(set(mandatory_opt).difference(parser.options('experiment')))
	if(missing):
		print "Missing options"
		print missing
		sys.exit()
	
	check_values('HPCARCH', parser.get('experiment', 'HPCARCH'), hpcarch)
	check_regex('DATELIST', parser.get('experiment', 'DATELIST'), startdate)
	check_regex('MEMBERS', parser.get('experiment', 'MEMBERS'), members)
	check_regex('CHUNKINI', parser.get('experiment', 'CHUNKINI'), chunkini)
	check_regex('NUMCHUNKS', parser.get('experiment', 'NUMCHUNKS'), numchunks)
	check_regex('RERUN', parser.get('experiment', 'RERUN'), rerun)

	if(invalid_values):
		print "\nInvalid experiment config file"
		sys.exit()
	else:
		print "\nExperiment config file OK"

	return parser

def archdef_parser(filename):

	# check file existance
	if(not path.isfile(filename)):
		print "File does not exist"
		sys.exit()

	# load values
	parser = SafeConfigParser()
	parser.optionxform = str
	parser.read(filename)


	if(invalid_values):
		print "\nInvalid platform config file"
		sys.exit()
	else:
		print "\nPlatform config file OK"

	return parser

if __name__ == "__main__":
	if(len(sys.argv) != 2):
		print "Error missing config file"
	else:
		autosubmit_conf_parser(sys.argv[1])
