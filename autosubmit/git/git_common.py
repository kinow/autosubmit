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

from os import path
from os import listdir
from shutil import rmtree
from commands import getstatusoutput

from autosubmit.config.dir_config import LOCAL_ROOT_DIR
from autosubmit.config.dir_config import LOCAL_GIT_DIR


class AutosubmitGit:
    """Class to handle experiment git repository"""

    def __init__(self, expid):
        self._expid = expid

    def clean_git(self):
        """Function to clean space on LOCAL_ROOT_DIR/git directory."""
        dirs = listdir(LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_GIT_DIR)
        if dirs:
            print "Checking git directories status..."
            for dirname in dirs:
                print dirname
                if path.isdir(LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_GIT_DIR + "/" + dirname):
                    if path.isdir(LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_GIT_DIR + "/" + dirname + "/.git"):
                        (status, output) = getstatusoutput(
                            "cd " + LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_GIT_DIR + "/" + dirname + "; " +
                            "git diff-index HEAD --")
                        if status == 0:
                            if output:
                                print "Changes not commited detected... SKIPPING!"
                                print "WARNING: commit needed..."
                                exit(1)
                            else:
                                (status, output) = getstatusoutput(
                                    "cd " + LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_GIT_DIR + "/" + dirname +
                                    "; " + "git log --branches --not --remotes")
                                if output:
                                    print "Changes not pushed detected... SKIPPING!"
                                    print "WARNING: synchronization needed..."
                                    exit(1)
                                else:
                                    print "Ready to clean..."
                                    print "Cloning: 'git clone --bare " + dirname + " " + dirname + ".git' ..."
                                    # noinspection PyUnusedLocal
                                    (status, output) = getstatusoutput(
                                        "cd " + LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_GIT_DIR + "/" + "; " +
                                        "git clone --bare " + dirname + " " + dirname + ".git")
                                    print "Removing: " + dirname
                                    rmtree(LOCAL_ROOT_DIR + "/" + self._expid + "/" + LOCAL_GIT_DIR + "/" + dirname)
                                    print dirname + " directory clean!"
                                    print ("WARNING: further runs will require 'git clone " + dirname + ".git " +
                                           dirname + "' ...")
                        else:
                            print "Failed to retrieve git info..."
                            exit(1)
                    else:
                        print "Not a git repository... SKIPPING!"
                else:
                    print "Not a directory... SKIPPING!"
        return
