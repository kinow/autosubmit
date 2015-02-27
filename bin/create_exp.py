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


"""This is the code to create the job list. It reads the experiment configuration files and creates the parameter
structure and writes it in a .pkl file"""
import os
import sys
from log import Log

scriptdir = os.path.abspath(os.path.dirname(sys.argv[0]))
assert sys.path[0] == scriptdir
sys.path[0] = os.path.normpath(os.path.join(scriptdir, os.pardir))
import argparse
import json
from commands import getstatusoutput
from pyparsing import nestedExpr
from pkg_resources import require
from autosubmit.job.job_list import JobList
from autosubmit.job.job_list import RerunJobList
from autosubmit.config.config_common import AutosubmitConfig
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.monitor.monitor import Monitor


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
    parser = argparse.ArgumentParser(description='Create pickle given an experiment identifier')
    parser.add_argument('-v', '--version', action='version', version=autosubmit_version)
    parser.add_argument('-e', '--expid', required=True, nargs=1)
    args = parser.parse_args()
    if args.expid is None:
        parser.error("Missing expid.")
    Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, args.expid[0], BasicConfig.LOCAL_TMP_DIR,
                              'create_exp.log'))
    as_conf = AutosubmitConfig(args.expid[0])
    as_conf.check_conf()
    
    expid = as_conf.get_expid()
    project_type = as_conf.get_project_type()

    if project_type == "git":
        git_project_origin = as_conf.get_git_project_origin()
        git_project_branch = as_conf.get_git_project_branch()
        project_path = BasicConfig.LOCAL_ROOT_DIR + "/" + args.expid[0] + "/" + BasicConfig.LOCAL_PROJ_DIR
        if os.path.exists(project_path):
            Log.debug("The project folder exists. SKIPPING...")
            Log.info("Using project folder: %s" % project_path)
        else:
            os.mkdir(project_path)
            Log.debug("The project folder %s has been created." % project_path)
            Log.info("Cloning %s into %s" % (git_project_branch + " " + git_project_origin, project_path))
            (status, output) = getstatusoutput("cd " + project_path + "; git clone -b " + git_project_branch +
                                               " " + git_project_origin)
            if status:
                os.rmdir(project_path)
                Log.error("Can not clone %s into %s" % (git_project_branch + " " + git_project_origin, project_path))
                exit(1)

            Log.debug("%s" % output)
            git_project_name = output[output.find("'")+1:output.find("...")-1]
            (status, output) = getstatusoutput("cd " + project_path + "/" + git_project_name +
                                               "; git submodule update --remote --init")
            if status:
                os.rmdir(project_path)
                Log.error("Can not clone %s into %s" % (git_project_branch + " " + git_project_origin, project_path))
                exit(1)
            Log.debug("%s" % output)

            (status, output) = getstatusoutput("cd " + project_path + "/" + git_project_name +
                                               "; git submodule foreach -q 'branch=\"$(git config "
                                               "-f $toplevel/.gitmodules submodule.$name.branch)\"; "
                                               "git checkout $branch'")
            if status:
                os.rmdir(project_path)
                Log.error("Can not clone %s into %s" % (git_project_branch + " " + git_project_origin, project_path))
                exit(1)
            Log.debug("%s" % output)

    elif project_type == "svn":
        svn_project_url = as_conf.get_svn_project_url()
        svn_project_revision = as_conf.get_svn_project_revision()
        project_path = BasicConfig.LOCAL_ROOT_DIR + "/" + args.expid[0] + "/" + BasicConfig.LOCAL_PROJ_DIR
        if os.path.exists(project_path):
            Log.debug("The project folder exists. SKIPPING...")
            Log.info("Using project folder: %s" % project_path)
        else:
            os.mkdir(project_path)
            Log.debug("The project folder %s has been created." % project_path)
            Log.info("Checking out revision %s into %s" % (svn_project_revision + " " + svn_project_url, project_path))
            (status, output) = getstatusoutput("cd " + project_path + "; svn checkout -r " + svn_project_revision +
                                               " " + svn_project_url)
            if status:
                os.rmdir(project_path)
                Log.error("Can not check out revision %s into %s" % (svn_project_revision + " " + svn_project_url,
                                                                     project_path))
                exit(1)
            Log.debug("%s" % output)
    
    elif project_type == "local":
        local_project_path = as_conf.get_local_project_path()
        project_path = BasicConfig.LOCAL_ROOT_DIR + "/" + args.expid[0] + "/" + BasicConfig.LOCAL_PROJ_DIR
        if os.path.exists(project_path):
            Log.debug("The project folder exists. SKIPPING...")
            Log.info("Using project folder: %s" % project_path)
        else:
            os.mkdir(project_path)
            Log.debug("The project folder %s has been created." % project_path)
            Log.info("Copying %s into %s" % (local_project_path, project_path))
            (status, output) = getstatusoutput("cp -R " + local_project_path + " " + project_path)
            if status:
                os.rmdir(project_path)
                Log.error("Can not copy %s into %s. Exiting..." % (local_project_path, project_path))
                exit(1)
            Log.debug("%s" % output)
    
    if project_type != "none":
        # Check project configuration
        as_conf.check_proj()

    # Load parameters
    Log.info("Loading parameters...")
    parameters = as_conf.load_parameters()

    date_list = as_conf.get_date_list()
    starting_chunk = as_conf.get_starting_chunk()
    num_chunks = as_conf.get_num_chunks()
    member_list = as_conf.get_member_list()
    rerun = as_conf.get_rerun()

    if rerun == "false":
        job_list = JobList(expid)
        job_list.create(date_list, member_list, starting_chunk, num_chunks, parameters)
    else:
        job_list = RerunJobList(expid)
        chunk_list = create_json(as_conf.get_chunk_list())
        job_list.create(chunk_list, starting_chunk, num_chunks, parameters)

    platform = as_conf.get_platform()
    if platform == 'hector' or platform == 'archer':
        job_list.update_shortened_names()

    job_list.save()

    monitor_exp = Monitor()
    monitor_exp.generate_output(expid, job_list.get_job_list(), 'pdf')
    Log.user_warning("Remember to MODIFY the MODEL config files!")


if __name__ == "__main__":
    main()
