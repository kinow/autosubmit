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
import pickle
from pkg_resources import require
from autosubmit.job.job_common import Type
from autosubmit.config.basicConfig import BasicConfig
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

    parser = argparse.ArgumentParser(description='Plot statistics graph')
    parser.add_argument('-v', '--version', action='version', version=autosubmit_version)
    parser.add_argument('-e', '--expid', required=True, nargs=1)
    parser.add_argument('-j', '--joblist', required=True, nargs=1)
    parser.add_argument('-o', '--output', required=True, nargs=1, choices=('pdf', 'png', 'ps'), default='pdf')

    args = parser.parse_args()
    Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, args.expid[0], BasicConfig.LOCAL_TMP_DIR,
                              'statistics.log'))
    expid = args.expid[0]
    root_name = args.joblist[0]
    output = args.output[0]

    filename = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + '/pkl/' + root_name + '_' + expid + '.pkl'
    jobs = pickle.load(file(filename, 'r'))
    if not isinstance(jobs, type([])):
        jobs = [job for job in jobs.get_finished() if job.type == Type.SIMULATION]

    if len(jobs) > 0:
        monitor_exp = Monitor()
        monitor_exp.generate_output_stats(expid, jobs, output)
    else:
        Log.info("There are no COMPLETED jobs...")


if __name__ == "__main__":
    main()
