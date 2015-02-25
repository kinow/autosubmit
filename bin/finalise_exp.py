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
import os
import sys
from config.basicConfig import BasicConfig
from log import Log

scriptdir = os.path.abspath(os.path.dirname(sys.argv[0]))
assert sys.path[0] == scriptdir
sys.path[0] = os.path.normpath(os.path.join(scriptdir, os.pardir))
import argparse
from pkg_resources import require
from autosubmit.config.config_common import AutosubmitConfig
from autosubmit.git.git_common import AutosubmitGit
from autosubmit.monitor.monitor import Monitor


####################
# Main Program
####################
def main():
    version_path = os.path.join(scriptdir, '..', 'VERSION')
    if os.path.isfile(version_path):
        with open(version_path) as f:
            autosubmit_version = f.read().strip()
    else:
        autosubmit_version = require("autosubmit")[0].version
    BasicConfig.read()

    parser = argparse.ArgumentParser(
        description='Clean experiment git and plot directories, given an experiment identifier')
    parser.add_argument('-v', '--version', action='version', version=autosubmit_version)
    parser.add_argument('-e', '--expid', required=True, nargs=1)
    parser.add_argument('-pr', '--project', action="store_true", default=False, help='Clean project')
    parser.add_argument('-p', '--plot', action="store_true", default=False, help='Clean plot, only 2 last will remain')
    args = parser.parse_args()
    if args.expid is None:
        parser.error("Missing expid.")
    Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, args.expid[0], BasicConfig.LOCAL_TMP_DIR, 'log',
                              'finalise_exp.log'))
    if args.project:
        autosubmit_config = AutosubmitConfig(args.expid[0])
        autosubmit_config.check_conf()
        project_type = autosubmit_config.get_project_type()
        if project_type == "git":
            autosubmit_config.check_proj()
            Log.info("Registering commit SHA...")
            autosubmit_config.set_git_project_commit()
            autosubmit_git = AutosubmitGit(args.expid[0])
            Log.info("Cleaning GIT directory...")
            autosubmit_git.clean_git()
        else:
            Log.info("No project to clean...")

    if args.plot:
        Log.info("Cleaning plot directory...")
        monitor_autosubmit = Monitor()
        monitor_autosubmit.clean_plot(args.expid[0])


if __name__ == "__main__":
    main()
