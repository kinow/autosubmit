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

"""Functions for handling compatibility check of Autosbumit version and template project version"""
from dir_config import LOCAL_ROOT_DIR, COMPATIBILITY_TABLE 
import argparse
from os import path


def print_compatibility():
	"""Prints the compatibility table in a tabular mode"""
	compatibility_table = [tuple(l.split()) for l in file(LOCAL_ROOT_DIR + "/" + COMPATIBILITY_TABLE).readlines()]
	print "COMPATIBILITY TABLE"
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
def main():

	parser = argparse.ArgumentParser(description='Check autosubmit and templates compatibility given a experiment identifier')
	parser.add_argument('-e', '--expid', required=True, nargs = 1)
	args = parser.parse_args()
	if args.expid is None:
		parser.error("Missing expid.")

	autosubmit_version_filename = os.path.join(os.path.dirname(__file__), os.pardir, "VERSION")
	template_version_filename = LOCAL_ROOT_DIR + "/" + args.expid[0] + "/git/templates/VERSION"

	if check_compatibility(autosubmit_version_filename, template_version_filename):
		print "Compatibility check PASSED!"
	else:
		print "Compatibility check FAILED!"
		print_compatibility()
		print "WARNING: running after FAILED compatibility check is at your own risk!!!"

if __name__ == "__main__":
	main()
