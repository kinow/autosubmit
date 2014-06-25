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

"""Functions for finalise experiment. 
Cleaning space on LOCAL_ROOT_DIR/git directory.
Cleaning space on LOCAL_ROOT_DIR/plot directory.
Use these functions for finalised experiments."""
from dir_config import LOCAL_ROOT_DIR
import argparse
from os import path, listdir, chdir, remove
import shutil
from sys import exit
from commands import getstatusoutput
from register_exp import register_sha


def clean_git(expid):
	"""Function to clean space on LOCAL_ROOT_DIR/git directory."""

	dirs = listdir(LOCAL_ROOT_DIR + "/" + expid + "/git/")
	if (dirs):
		print "Registering SHA..."
		register_sha(expid,True)

		print "Checking git directories status..."
		for dirname in dirs:
			print dirname
			if path.isdir(LOCAL_ROOT_DIR + "/" + expid + "/git/" + dirname):
				if path.isdir(LOCAL_ROOT_DIR + "/" + expid + "/git/" + dirname + "/.git"):
					(status, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/" + dirname + "; " + "git diff-index HEAD --")
					if (status == 0):
						if (output):
							print "Changes not commited detected... SKIPPING!"
							print "WARNING: commit needed..."
							exit(1)
						else:
							(status, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/" + dirname + "; " + "git log --branches --not --remotes")
							if (output):
								print "Changes not pushed detected... SKIPPING!"
								print "WARNING: synchronization needed..."
								exit(1)
							else: 
								print "Ready to clean..."
								print "Cloning: 'git clone --bare " + dirname + " " + dirname +".git' ..."
								(status, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/" + "; " + "git clone --bare " + dirname + " " + dirname + ".git")
								print "Removing: " + dirname
								shutil.rmtree(LOCAL_ROOT_DIR + "/" + expid + "/git/" + dirname);
								print dirname + " directory clean!"
								print "WARNING: further runs will require 'git clone " + dirname + ".git " + dirname +"' ..."
					else:
						print "Failed to retrieve git info..." 
						exit(1)
				else:
					print "Not a git repository... SKIPPING!"
			else:
				print "Not a directory... SKIPPING!"
	return


def clean_plot(expid):
	"""Function to clean space on LOCAL_ROOT_DIR/plot directory."""
	
	search_dir = LOCAL_ROOT_DIR + "/" + expid + "/plot/"
	chdir(search_dir)
	files = filter(path.isfile, listdir(search_dir))
	files = [path.join(search_dir, f) for f in files]
	files.sort(key=lambda x: path.getmtime(x))
	remain = files[-2:]
	filelist = [ f for f in files if f not in remain ]
	for f in filelist:
		remove(f)
	print "Plot directory clean! last two plots remanining there."
	return


	

####################
# Main Program
####################
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Clean experiment git and plot directories, given an experiment identifier')
	parser.add_argument('-e', '--expid', required=True, nargs = 1)
	parser.add_argument('-g', '--git', action="store_true", default=False, help='Clean git')
	parser.add_argument('-p', '--plot', action="store_true", default=False, help='Clean plot, only 2 last will remain')
	args = parser.parse_args()
	if args.expid is None:
		parser.error("Missing expid.")
	
	if args.git:
		print "Cleaning GIT directory..."
		clean_git(args.expid[0])
	
	if args.plot:
		print "Cleaning plot directory..."
		clean_plot(args.expid[0])

