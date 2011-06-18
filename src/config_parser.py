#!/usr/bin/env python

from ConfigParser import SafeConfigParser
import sys
import os.path

invalid_values = False

def check_values(value, valid_values):
	global invalid_values

	if(value.lower() not in valid_values): 
		print "Invalid value: " + value
		invalid_values = True

def config_parser(filename):
	hpcarch = ['bsc', 'ithaca']
	runmode = ['local', 'remote']
	loglevel = ['debug', 'info', 'warning', 'error', 'critical']
	
	#option that must be in config file and has no default value
	mandatory_opt = ['expid']
	
	# default value in case this options does not exist on config file
	default = ({'MAXWAITINGJOBS' : '50', 'TOTALJOBS': '1000', 'ALREADYSUBMITTED': '0', 'JOBTEMPLATE': 'jobtemplate.cmd', 'VERBOSE': 'true', 'DEBUG': 'false', 'RUNMODE': 'remote', 'AUTOFILEDIR': 'AUTOSUB_WORKING_COPY/tmp'})

	# check file existance
	if(not os.path.isfile(filename)):
		print "File does not exist: " + filename
		sys.exit()

	# load default values
	parser = SafeConfigParser(default)
	#ccpLoadDefaults(parser)
	parser.read(filename)

	# check which options of the mandatory one are not in config file
	missing = list(set(mandatory_opt).difference(parser.options('config')))
	if(missing):
		print "Missing options"
		print missing
		sys.exit()
	
	check_values(parser.get('config', 'hpcarch'), hpcarch)
	check_values(parser.get('config', 'runmode'), runmode)
	check_values(parser.get('config', 'loglevel'), loglevel)

	print parser.items('config')
	if(invalid_values):
		print "\nInvalid config file"
		sys.exit()
	else:
		print "\nConfig file OK"
	return parser


def expdef_parser(filename):
	# default value in case this options does not exist on config file
	default = ({'EXPID' : 'dumi', 'TYPE': '1', 'STATUS': '0', 'LONGNAME': 'Just a test'})

	# check file existance
	if(not os.path.isfile(filename)):
		print "File does not exist"
		sys.exit()

	# load default values
	parser = SafeConfigParser(default)
	parser.optionxform = str
	parser.read(filename)
	return parser

def archdef_parser(filename):

	# check file existance
	if(not os.path.isfile(filename)):
		print "File does not exist"
		sys.exit()

	# load default values
	parser = SafeConfigParser()
	parser.optionxform = str
	parser.read(filename)
	print parser.items('archdef')
	return parser

if __name__ == "__main__":
	if(len(sys.argv) != 2):
		print "Error missing config file"
	else:
		autosubmit_conf_parser(sys.argv[1])
