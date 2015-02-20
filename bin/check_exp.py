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

"""Functions for handling experiment parameters check"""
import os
import sys

scriptdir = os.path.abspath(os.path.dirname(sys.argv[0]))
assert sys.path[0] == scriptdir
sys.path[0] = os.path.normpath(os.path.join(scriptdir, os.pardir))
import argparse
from pkg_resources import require
from autosubmit.job.job_list import JobList
from autosubmit.config.config_common import AutosubmitConfig


def check_templates(as_conf):
    """Procedure to check autogeneration of templates given
    Autosubmit configuration.
    Returns True if all variables are set.
    If the parameters are not correctly replaced, the function returns
    False and the check fails.

    :param as_conf: Autosubmit configuration object
    :type: AutosubmitConf
    :retruns: bool
    """
    parameters = as_conf.load_parameters()
    joblist = JobList(parameters['EXPID'])
    joblist.create(parameters['DATELIST'].split(' '), parameters['MEMBERS'].split(' '), int(parameters['CHUNKINI']),
                   int(parameters['NUMCHUNKS']), parameters)
    out = joblist.check_scripts()

    return out


####################
# Main Program
####################
def main():
    autosubmit_version = require("autosubmit")[0].version

    parser = argparse.ArgumentParser(
        description='Check autosubmit and experiment configurations given a experiment identifier. '
                    'Check templates creation with those configurations')
    parser.add_argument('-v', '--version', action='version', version=autosubmit_version)
    parser.add_argument('-e', '--expid', required=True, nargs=1)
    args = parser.parse_args()
    if args.expid is None:
        parser.error("Missing expid.")

    as_conf = AutosubmitConfig(args.expid[0])
    as_conf.check_conf()
    git_project = as_conf.get_git_project()
    if git_project == "true":
        as_conf.check_git()

    print "Checking experiment configuration..."
    if as_conf.check_parameters():
        print "Experiment configuration check PASSED!"
    else:
        print "Experiment configuration check FAILED!"
        print "WARNING: running after FAILED experiment configuration check is at your own risk!!!"

    print "Checking experiment templates..."
    if check_templates(as_conf):
        print "Experiment templates check PASSED!"
    else:
        print "Experiment templates check FAILED!"
        print "WARNING: running after FAILED experiment templates check is at your own risk!!!"


if __name__ == "__main__":
    main()
