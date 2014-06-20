#!/usr/bin/env python
"""Functions for handling comptaibility check of Autosbumit version and template project version"""
from dir_config import LOCAL_ROOT_DIR, COMPATIBILITY_TABLE 
import argparse
from os import path


def print_compatibility():
	"""Prints the compatibility table in a tabular mode"""
	compatibility_table = [tuple(l.split()) for l in file(LOCAL_ROOT_DIR + "/" + COMPATIBILITY_TABLE).readlines()]
	print "COMPTAIBILITY TABLE"
	print "-------------------"
	print "{0:<{col1}}|{1:<{col2}}".format("Autosubmit","Template",col1=10,col2=10)
	for i in compatibility_table:
		print "{0:<{col1}}|{1:<{col2}}".format(i[0],i[1],col1=10,col2=10)

def check_compatibility(autosubmit_version_filename, template_version_filename):
	"""Function to read version strings from VERSION files of Autosubmit and Templates.
	Returns True if exists a matching row with both strings in the compatibility table.
	If the parameters do not exist, the function returns False and the check fails.
	
	:param autosubmit_version_filename: path to the Autosubmit VERSION file
	:type: str
	:param template_version_filename: path to the Templates VERSION file
	:type: str
	:retruns: bool
	"""

	compatibility_table = [tuple(l.split()) for l in file(LOCAL_ROOT_DIR + "/" + COMPATIBILITY_TABLE).readlines()]
	result = False

	if (path.exists(autosubmit_version_filename)):
		autosubmit_version = file(autosubmit_version_filename).readline().split('\n')[0]
		#autosubmit_version_info = tuple([ int(num) for num in autosubmit_version.split('.')])
		print "Using Autosubmit: %s" % autosubmit_version
		if (path.exists(template_version_filename)):
			template_version = file(template_version_filename).readline().split('\n')[0]
			print "Using template: %s" % template_version
			result = tuple([autosubmit_version,template_version]) in compatibility_table
		else:
			print "The VERSION file %s necessary does not exist." % template_version_filename
			print "Compatibility check FAILED! while loading template VERSION file..."
	else:
		print "The VERSION file %s necessary does not exist." % autosubmit_version_filename
		print "Compatibility check FAILED! while loading Autosubmit VERSION file..."

	return result


####################
# Main Program
####################
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Check autosubmit and templates compatibility given a experiment identifier')
	parser.add_argument('-e', '--expid', required=True, nargs = 1)
	args = parser.parse_args()
	if args.expid is None:
		parser.error("Missing expid.")

	autosubmit_version_filename = "../VERSION"
	template_version_filename = LOCAL_ROOT_DIR + "/" + args.expid[0] + "/git/templates/VERSION"

	if check_compatibility(autosubmit_version_filename, template_version_filename):
		print "Compatibility check PASSED!"
	else:
		print "Compatibility check FAILED!"
		print_compatibility()
		print "WARNING: running after FAILED compatibility check is at your own risk!!!"
