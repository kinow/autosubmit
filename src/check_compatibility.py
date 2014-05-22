#!/usr/bin/env python
from dir_config import DB_DIR
from sys import exit, argv
from os import path

compatibility_table = [("2.2","1.0"),("2.3","1.1"),("2.4","1.2")]

def print_compatibility():
	print "COMPTAIBILITY TABLE"
	print "-------------------"
	print "{0:<{col1}}|{1:<{col2}}".format("Autosubmit","Template",col1=10,col2=10)
	for i in compatibility_table:
		print "{0:<{col1}}|{1:<{col2}}".format(i[0],i[1],col1=10,col2=10)

def check_compatibility(autosubmit_version_filename, template_version_filename):

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

	if(len(argv) != 2):
		print "Missing expid."
		exit(1)

	autosubmit_version_filename = "../VERSION"
	template_version_filename = DB_DIR + argv[1] + "/git/templates/VERSION"

	if check_compatibility(autosubmit_version_filename, template_version_filename):
		print "Compatibility check PASSED!"
	else:
		print "Compatibility check FAILED!"
		print_compatibility()
		print "WARNING: running after FAILED compatibility check is at your own risk!!!"
