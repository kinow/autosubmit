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

from autosubmit.config.basicConfig import BasicConfig
from autosubmit.config.log import Log


class AutosubmitGit:
    """
    Class to handle experiment git repository

    :param expid: experiment identifier
    :type expid: str
    """

    def __init__(self, expid):
        self._expid = expid

    def clean_git(self):
        """
        Function to clean space on BasicConfig.LOCAL_ROOT_DIR/git directory.
        """
        dirs = listdir(BasicConfig.LOCAL_ROOT_DIR + "/" + self._expid + "/" + BasicConfig.LOCAL_PROJ_DIR)
        if dirs:
            Log.debug("Checking git directories status...")
            for dirname in dirs:
                Log.debug("Directory: " + dirname)
                if path.isdir(BasicConfig.LOCAL_ROOT_DIR + "/" + self._expid + "/" + BasicConfig.LOCAL_PROJ_DIR +
                              "/" + dirname):
                    if path.isdir(BasicConfig.LOCAL_ROOT_DIR + "/" + self._expid + "/" + BasicConfig.LOCAL_PROJ_DIR +
                                  "/" + dirname + "/.git"):
                        (status, output) = getstatusoutput("cd " + BasicConfig.LOCAL_ROOT_DIR + "/" + self._expid +
                                                           "/" + BasicConfig.LOCAL_PROJ_DIR + "/" + dirname + "; " +
                                                           "git diff-index HEAD --")
                        if status == 0:
                            if output:
                                Log.info("Changes not commited detected... SKIPPING!")
                                Log.user_warning("Commit needed!")
                                exit(1)
                            else:
                                (status, output) = getstatusoutput("cd " + BasicConfig.LOCAL_ROOT_DIR + "/" +
                                                                   self._expid + "/" + BasicConfig.LOCAL_PROJ_DIR +
                                                                   "/" + dirname + "; " +
                                                                   "git log --branches --not --remotes")
                                if output:
                                    Log.info("Changes not pushed detected... SKIPPING!")
                                    Log.user_warning("Synchronization needed!")
                                    exit(1)
                                else:
                                    Log.debug("Ready to clean...")
                                    Log.debug("Cloning: 'git clone --bare " + dirname + " " + dirname + ".git' ...")
                                    # noinspection PyUnusedLocal
                                    (status, output) = getstatusoutput("cd " + BasicConfig.LOCAL_ROOT_DIR + "/" +
                                                                       self._expid + "/" + BasicConfig.LOCAL_PROJ_DIR +
                                                                       "/" + "; " + "git clone --bare " + dirname +
                                                                       " " + dirname + ".git")
                                    Log.debug("Removing: " + dirname)
                                    rmtree(BasicConfig.LOCAL_ROOT_DIR + "/" + self._expid + "/" +
                                           BasicConfig.LOCAL_PROJ_DIR + "/" + dirname)
                                    Log.debug(dirname + " directory clean!")
                                    Log.user_warning("Further runs will require 'git clone {0}.git {0} '...", dirname)
                        else:
                            Log.error("Failed to retrieve git info...")
                            exit(1)
                    else:
                        Log.debug("Not a git repository... SKIPPING!")
                else:
                    Log.debug("Not a directory... SKIPPING!")
        return
