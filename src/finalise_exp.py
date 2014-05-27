#!/usr/bin/env python
"""Functions for finalise experiment. 
Cleaning space on LOCAL_ROOT_DIR/git directory by using git clean.
Cleaning space on LOCAL_ROOT_DIR/plot directory.
Use these functions for finalised experiments."""
from dir_config import LOCAL_ROOT_DIR
import argparse
from os import path
from sys import exit
from commands import getstatusoutput


def clean_git():
	"""Function to clean space on LOCAL_ROOT_DIR/git directory."""
	#(status, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/git/templates/" + "; " + "git clean")


def clean_plot():
	"""Function to clean space on LOCAL_ROOT_DIR/plot directory."""
	

####################
# Main Program
####################
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Clean autosubmit finalised experiments directory given a experiment identifier')
	parser.add_argument('-e', '--expid', required=True, nargs = 1)
	args = parser.parse_args()
	if args.expid is None:
		parser.error("Missing expid.")
	
	#print "Cleaning GIT directory..."
	#clean_git(args.expid[0])
	#print "GIT directory clean! further runs will require checkout model and templates again"
	#print "Cleaning plot directory..."
	#clean_plot(args.expid[0])
	#print "Plot directory clean! last two plots remanining there."

