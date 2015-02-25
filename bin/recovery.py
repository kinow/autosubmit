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

"""Script for handling experiment recovery after crash or job failure"""
import os
import sys
from log import Log

scriptdir = os.path.abspath(os.path.dirname(sys.argv[0]))
assert sys.path[0] == scriptdir
sys.path[0] = os.path.normpath(os.path.join(scriptdir, os.pardir))
import argparse
import platform
import pickle
from pkg_resources import require
from autosubmit.queue.mnqueue import MnQueue
from autosubmit.queue.itqueue import ItQueue
from autosubmit.queue.lgqueue import LgQueue
from autosubmit.queue.elqueue import ElQueue
from autosubmit.queue.psqueue import PsQueue
from autosubmit.queue.ecqueue import EcQueue
from autosubmit.queue.mn3queue import Mn3Queue
from autosubmit.queue.htqueue import HtQueue
from autosubmit.queue.arqueue import ArQueue
from autosubmit.job.job_common import Status
from autosubmit.job.job_common import Type
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.config.config_common import AutosubmitConfig
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

    parser = argparse.ArgumentParser(description='Autosubmit recovery')
    parser.add_argument('-v', '--version', action='version', version=autosubmit_version)
    parser.add_argument('-e', '--expid', type=str, nargs=1, required=True, help='Experiment ID')
    parser.add_argument('-j', '--joblist', type=str, nargs=1, required=True, help='Job list')
    parser.add_argument('-g', '--get', action="store_true", default=False,
                        help='Get completed files to synchronize pkl')
    parser.add_argument('-s', '--save', action="store_true", default=False, help='Save changes to disk')
    args = parser.parse_args()
    Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, args.expid[0], BasicConfig.LOCAL_TMP_DIR, 'log',
                              'recovery.log'))
    expid = args.expid[0]
    root_name = args.joblist[0]
    save = args.save
    get = args.get

    Log.debug(expid)
    l1 = pickle.load(file(BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl", 'r'))

    as_conf = AutosubmitConfig(expid)
    as_conf.check_conf()

    hpcarch = as_conf.get_platform()
    scratch_dir = as_conf.get_scratch_dir()
    hpcproj = as_conf.get_hpcproj()
    hpcuser = as_conf.get_hpcuser()

    if get:
        remote_queue = None
        serial_queue = None
        parallel_queue = None

        if hpcarch == 'bsc':
            remote_queue = MnQueue(expid)
            remote_queue.set_scratch(scratch_dir)
            remote_queue.set_project(hpcproj)
            remote_queue.set_user(hpcuser)
            remote_queue.set_host("bsc")
            remote_queue.update_cmds()
        elif hpcarch == 'ithaca':
            remote_queue = ItQueue(expid)
            remote_queue.set_scratch(scratch_dir)
            remote_queue.set_project(hpcproj)
            remote_queue.set_user(hpcuser)
            remote_queue.set_host("ithaca")
            remote_queue.update_cmds()
        elif hpcarch == 'lindgren':
            # in lindgren arch must set-up both serial and parallel queues
            serial_queue = ElQueue(expid)
            serial_queue.set_scratch(scratch_dir)
            serial_queue.set_project(hpcproj)
            serial_queue.set_user(hpcuser)
            serial_queue.set_host("lindgren")
            serial_queue.update_cmds()
            parallel_queue = LgQueue(expid)
            parallel_queue.set_scratch(scratch_dir)
            parallel_queue.set_project(hpcproj)
            parallel_queue.set_user(hpcuser)
            parallel_queue.set_host("ellen")
            parallel_queue.update_cmds()
        elif hpcarch == 'ecmwf':
            remote_queue = EcQueue(expid)
            remote_queue.set_scratch(scratch_dir)
            remote_queue.set_project(hpcproj)
            remote_queue.set_user(hpcuser)
            remote_queue.set_host("c2a")
            remote_queue.update_cmds()
        elif hpcarch == 'marenostrum3':
            remote_queue = Mn3Queue(expid)
            remote_queue.set_scratch(scratch_dir)
            remote_queue.set_project(hpcproj)
            remote_queue.set_user(hpcuser)
            remote_queue.set_host("mn-" + hpcproj)
            remote_queue.update_cmds()
        elif hpcarch == 'hector':
            remote_queue = HtQueue(expid)
            remote_queue.set_scratch(scratch_dir)
            remote_queue.set_project(hpcproj)
            remote_queue.set_user(hpcuser)
            remote_queue.set_host("ht-" + hpcproj)
            remote_queue.update_cmds()
        elif hpcarch == 'archer':
            remote_queue = ArQueue(expid)
            remote_queue.set_scratch(scratch_dir)
            remote_queue.set_project(hpcproj)
            remote_queue.set_user(hpcuser)
            remote_queue.set_host("ar-" + hpcproj)
            remote_queue.update_cmds()

        local_queue = PsQueue(expid)
        local_queue.set_host(platform.node())
        local_queue.set_scratch(BasicConfig.LOCAL_ROOT_DIR)
        local_queue.set_project(expid)
        local_queue.set_user(BasicConfig.LOCAL_TMP_DIR)
        local_queue.update_cmds()

        for job in l1.get_active():
            # If remote queue is none (now only in lindgren) arch must select serial or parallel queue
            # acording to the job type
            if remote_queue is None and job.type == Type.SIMULATION:
                queue = parallel_queue
            elif (remote_queue is None and (job.type == Type.INITIALISATION or
                                            job.type == Type.CLEANING or
                                            job.type == Type.POSTPROCESSING)):
                queue = serial_queue
            elif job.type == Type.LOCALSETUP or job.type == Type.TRANSFER:
                queue = local_queue
            else:
                queue = remote_queue
            if queue.get_completed_files(job.name):
                job.status = Status.COMPLETED
                Log.info("CHANGED: job: " + job.name + " status to: COMPLETED")
            elif job.status != Status.SUSPENDED:
                job.status = Status.READY
                job.set_fail_count(0)
                Log.info("CHANGED: job: " + job.name + " status to: READY")

        sys.setrecursionlimit(50000)
        l1.update_list()
        pickle.dump(l1, file(BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl",
                             'w'))

    if save:
        l1.update_from_file()
    else:
        l1.update_from_file(False)

    if save:
        sys.setrecursionlimit(50000)
        pickle.dump(l1, file(BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl",
                             'w'))

    monitor_exp = Monitor()
    monitor_exp.generate_output(expid, l1.get_job_list())


if __name__ == '__main__':
    main()
