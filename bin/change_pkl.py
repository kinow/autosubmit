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

"""Script for handling job status changes"""
import sys
import os

scriptdir = os.path.abspath(os.path.dirname(sys.argv[0]))
assert sys.path[0] == scriptdir
sys.path[0] = os.path.normpath(os.path.join(scriptdir, os.pardir))
import pickle
import argparse
import json
from pyparsing import nestedExpr
from pkg_resources import require
from autosubmit.job.job_common import Status
from autosubmit.job.job_common import Type
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.monitor.monitor import Monitor


def get_status(s):
    if s == 'READY':
        return Status.READY
    elif s == 'COMPLETED':
        return Status.COMPLETED
    elif s == 'WAITING':
        return Status.WAITING
    elif s == 'SUSPENDED':
        return Status.SUSPENDED
    elif s == 'FAILED':
        return Status.FAILED
    elif s == 'UNKNOWN':
        return Status.UNKNOWN


def get_type(t):
    if t == 'LOCALSETUP':
        return Type.LOCALSETUP
    elif t == 'REMOTESETUP':
        return Type.REMOTESETUP
    elif t == 'INITIALISATION':
        return Type.INITIALISATION
    elif t == 'SIMULATION':
        return Type.SIMULATION
    elif t == 'POSTPROCESSING':
        return Type.POSTPROCESSING
    elif t == 'CLEANING':
        return Type.CLEANING
    elif t == 'LOCALTRANSFER':
        return Type.TRANSFER


def get_members(out):
    count = 0
    data = []
    # noinspection PyUnusedLocal
    for element in out:
        if count % 2 == 0:
            ms = {'m': out[count], 'cs': get_chunks(out[count + 1])}
            data.append(ms)
            count += 1
        else:
            count += 1

    return data


def get_chunks(out):
    data = []
    for element in out:
        if element.find("-") != -1:
            numbers = element.split("-")
            for count in range(int(numbers[0]), int(numbers[1]) + 1):
                data.append(str(count))
        else:
            data.append(element)

    return data


def create_json(text):
    count = 0
    data = []
    # text = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 16651101 [ fc0 [1-30 31 32] ] ]"

    out = nestedExpr('[', ']').parseString(text).asList()

    # noinspection PyUnusedLocal
    for element in out[0]:
        if count % 2 == 0:
            sd = {'sd': out[0][count], 'ms': get_members(out[0][count + 1])}
            data.append(sd)
            count += 1
        else:
            count += 1

    sds = {'sds': data}
    result = json.dumps(sds)
    return result


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

    parser = argparse.ArgumentParser(description='Autosubmit change pickle')
    parser.add_argument('-v', '--version', action='version', version=autosubmit_version)
    parser.add_argument('-e', '--expid', type=str, nargs=1, required=True, help='Experiment ID')
    parser.add_argument('-j', '--joblist', type=str, nargs=1, required=True, help='Job list')
    parser.add_argument('-s', '--save', action="store_true", default=False, help='Save changes to disk')
    parser.add_argument('-t', '--status_final',
                        choices=('READY', 'COMPLETED', 'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN'), required=True,
                        help='Supply the target status')
    group1 = parser.add_mutually_exclusive_group(required=True)
    group1.add_argument('-l', '--list', type=str,
                        help='Alternative 1: Supply the list of job names to be changed. Default = "Any". '
                             'LIST = "b037_20101101_fc3_21_sim b037_20111101_fc4_26_sim"')
    group1.add_argument('-f', '--filter', action="store_true",
                        help='Alternative 2: Supply a filter for the job list. See help of filter arguments: '
                             'chunk filter, status filter or type filter')
    group2 = parser.add_mutually_exclusive_group(required=False)
    group2.add_argument('-fc', '--filter_chunks', type=str,
                        help='Supply the list of chunks to change the status. Default = "Any". '
                             'LIST = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]"')
    group2.add_argument('-fs', '--filter_status', type=str,
                        choices=('Any', 'READY', 'COMPLETED', 'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN'),
                        help='Select the original status to filter the list of jobs')
    group2.add_argument('-ft', '--filter_type', type=str, choices=('Any', 'LOCALSETUP', 'REMOTESETUP', 'INITIALISATION',
                                                                   'SIMULATION', 'POSTPROCESSING', 'CLEANING',
                                                                   'LOCALTRANSFER'),
                        help='Select the job type to filter the list of jobs')
    args = parser.parse_args()

    expid = args.expid[0]
    root_name = args.joblist[0]
    save = args.save
    final = args.status_final

    print expid
    l1 = pickle.load(file(BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl", 'r'))

    if args.filter:
        if args.filter_chunks:
            fc = args.filter_chunks
            print fc

            if fc == 'Any':
                for job in l1.get_job_list():
                    job.status = get_status(final)
                    print "CHANGED: job: " + job.name + " status to: " + final
            else:
                data = json.loads(create_json(fc))
                # change localsetup and remotesetup
                # [...]
                for date in data['sds']:
                    for member in date['ms']:
                        jobname_ini = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_ini"
                        job = l1.get_job_by_name(jobname_ini)
                        job.status = get_status(final)
                        print "CHANGED: job: " + job.name + " status to: " + final
                        # change also trans
                        jobname_trans = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_trans"
                        job = l1.get_job_by_name(jobname_trans)
                        job.status = get_status(final)
                        print "CHANGED: job: " + job.name + " status to: " + final
                        # [...]
                        for chunk in member['cs']:
                            jobname_sim = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(
                                chunk) + "_sim"
                            jobname_post = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(
                                chunk) + "_post"
                            jobname_clean = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(
                                chunk) + "_clean"
                            job = l1.get_job_by_name(jobname_sim)
                            job.status = get_status(final)
                            print "CHANGED: job: " + job.name + " status to: " + final
                            job = l1.get_job_by_name(jobname_post)
                            job.status = get_status(final)
                            print "CHANGED: job: " + job.name + " status to: " + final
                            job = l1.get_job_by_name(jobname_clean)
                            job.status = get_status(final)
                            print "CHANGED: job: " + job.name + " status to: " + final

        if args.filter_status:
            fs = args.filter_status
            print fs

            if fs == 'Any':
                for job in l1.get_job_list():
                    job.status = get_status(final)
                    print "CHANGED: job: " + job.name + " status to: " + final
            else:
                for job in l1.get_job_list():
                    if job.status == get_status(fs):
                        job.status = get_status(final)
                        print "CHANGED: job: " + job.name + " status to: " + final

        if args.filter_type:
            ft = args.filter_type
            print ft

            if ft == 'Any':
                for job in l1.get_job_list():
                    job.status = get_status(final)
                    print "CHANGED: job: " + job.name + " status to: " + final
            else:
                for job in l1.get_job_list():
                    if job.type == get_type(ft):
                        job.status = get_status(final)
                        print "CHANGED: job: " + job.name + " status to: " + final

    if args.list:
        jobs = args.list.split()

        if jobs == 'Any':
            for job in l1.get_job_list():
                job.status = get_status(final)
                print "CHANGED: job: " + job.name + " status to: " + final
        else:
            for job in l1.get_job_list():
                if job.name in jobs:
                    job.status = get_status(final)
                    print "CHANGED: job: " + job.name + " status to: " + final

    sys.setrecursionlimit(50000)

    if save:
        l1.update_list()
        pickle.dump(l1, file(BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl",
                             'w'))
        print "Saving JobList: " + BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl"
    else:
        l1.update_list(False)
        print "Changes NOT saved to the JobList!!!!:  use -s option to save"

    monitor_exp = Monitor()

    monitor_exp.generate_output(expid, l1.get_job_list())


if __name__ == '__main__':
    main()
