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

"""Script for handling experiment statistics plots"""
import os
import sys
from log import Log

scriptdir = os.path.abspath(os.path.dirname(sys.argv[0]))
assert sys.path[0] == scriptdir
sys.path[0] = os.path.normpath(os.path.join(scriptdir, os.pardir))
import argparse
from pkg_resources import require
from ConfigParser import SafeConfigParser

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

    parser = argparse.ArgumentParser(description='Plot statistics graph')
    parser.add_argument('-v', '--version', action='version', version=autosubmit_version)
    parser.add_argument('-db', '--databasepath', nargs=1, default=None)
    parser.add_argument('-lr', '--localrootpath', nargs=1, default=None)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-u', '--user', action="store_true")
    group.add_argument('-l', '--local', action="store_true")

    args = parser.parse_args()
    home_path = os.path.expanduser('~')
    while args.databasepath is None:
        args.databasepath = raw_input("Introduce Database path: ")
    args.databasepath = args.databasepath.replace('~', home_path)
    if not os.path.exists(args.databasepath):
        Log.error("Database path does not exist.")
        exit(1)

    while args.localrootpath is None:
        args.localrootpath = raw_input("Introduce Local Root path: ")
    args.localrootpath = args.localrootpath.replace('~', home_path)
    if not os.path.exists(args.localrootpath):
        Log.error("Local Root path does not exist.")
        exit(1)

    if args.user:
        path = home_path
    elif args.local:
        path = '.'
    else:
        path = '/etc'
    path = os.path.join(path, '.autosubmitrc')

    config_file = open(path, 'w')

    Log.info("Writing configuration file...")
    parser = SafeConfigParser()
    parser.add_section('database')
    parser.set('database', 'path', args.databasepath)
    parser.add_section('local')
    parser.set('local', 'path', args.localrootpath)
    parser.write(config_file)
    config_file.close()
    Log.info("Configuration file written successfully")

if __name__ == "__main__":
    main()
