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

"""This is the main script of autosubmit. All the stream of execution is handled here
(submitting all the jobs properly and repeating its execution in case of failure)."""
import os
import sys

scriptdir = os.path.abspath(os.path.dirname(sys.argv[0]))
assert sys.path[0] == scriptdir
sys.path[0] = os.path.normpath(os.path.join(scriptdir, os.pardir))
import argparse
import time
import cPickle
import signal
import platform

from pkg_resources import require
from queue.itqueue import ItQueue
from queue.mnqueue import MnQueue
from queue.lgqueue import LgQueue
from queue.elqueue import ElQueue
from queue.psqueue import PsQueue
from queue.ecqueue import EcQueue
from queue.mn3queue import Mn3Queue
from queue.htqueue import HtQueue
from queue.arqueue import ArQueue
from job.job_common import Status
from job.job_common import Type
from config.config_common import AutosubmitConfig
from config.basicConfig import BasicConfig
from log import Log
from time import strftime


####################
# Main Program
####################
def main():
    # Get the version number from the relevant file. If not, from autosubmit package
    version_path = os.path.join(scriptdir, '..', 'VERSION')
    if os.path.isfile(version_path):
        with open(version_path) as f:
            autosubmit_version = f.read().strip()
    else:
        autosubmit_version = require("autosubmit")[0].version
    BasicConfig.read()
    parser = argparse.ArgumentParser(description='Launch Autosubmit given an experiment identifier')
    # parser.add_argument('action')
    parser.add_argument('-v', '--version', action='version', version=autosubmit_version)
    parser.add_argument('-e', '--expid', nargs=1)
    args = parser.parse_args()

    # if args.action is None or args.action.lower() == 'run':
    # pass
    # elif args.action.lower() == 'expid':
    # os.system("expid -H ithaca -n")

    if args.expid is None:
        parser.error("Missing expid.")

    os.system('clear')
    Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, args.expid[0], BasicConfig.LOCAL_TMP_DIR,
                              'autosubmit.log'))

    as_conf = AutosubmitConfig(args.expid[0])
    as_conf.check_conf()

    project_type = as_conf.get_project_type()
    if project_type != "none":
        # Check proj configuration
        as_conf.check_proj()

    expid = as_conf.get_expid()
    hpcarch = as_conf.get_platform()
    scratch_dir = as_conf.get_scratch_dir()
    hpcproj = as_conf.get_hpcproj()
    hpcuser = as_conf.get_hpcuser()
    max_jobs = as_conf.get_total_jobs()
    max_waiting_jobs = as_conf.get_max_waiting_jobs()
    safetysleeptime = as_conf.get_safetysleeptime()
    retrials = as_conf.get_retrials()
    rerun = as_conf.get_rerun()

    remote_queue = None
    serial_queue = None
    parallel_queue = None

    if hpcarch == "bsc":
        remote_queue = MnQueue(expid)
        remote_queue.set_host("bsc")
    elif hpcarch == "ithaca":
        remote_queue = ItQueue(expid)
        remote_queue.set_host("ithaca")
    elif hpcarch == "hector":
        remote_queue = HtQueue(expid)
        remote_queue.set_host("ht-" + hpcproj)
    elif hpcarch == "archer":
        remote_queue = ArQueue(expid)
        remote_queue.set_host("ar-" + hpcproj)
    # in lindgren arch must set-up both serial and parallel queues
    elif hpcarch == "lindgren":
        serial_queue = ElQueue(expid)
        serial_queue.set_host("ellen")
        parallel_queue = LgQueue(expid)
        parallel_queue.set_host("lindgren")
    elif hpcarch == "ecmwf":
        remote_queue = EcQueue(expid)
        remote_queue.set_host("c2a")
    elif hpcarch == "ecmwf-cca":
        remote_queue = EcQueue(expid)
        remote_queue.set_host("cca")
    elif hpcarch == "marenostrum3":
        remote_queue = Mn3Queue(expid)
        remote_queue.set_host("mn-" + hpcproj)

    local_queue = PsQueue(expid)
    local_queue.set_host(platform.node())
    local_queue.set_scratch(BasicConfig.LOCAL_ROOT_DIR)
    local_queue.set_project(expid)
    local_queue.set_user(BasicConfig.LOCAL_TMP_DIR)
    local_queue.update_cmds()

    Log.debug("The Experiment name is: %s" % expid)
    Log.debug("Total jobs to submit: %s" % max_jobs)
    Log.debug("Maximum waiting jobs in queues: %s" % max_waiting_jobs)
    Log.debug("Sleep: %s" % safetysleeptime)
    Log.debug("Retrials: %s" % retrials)
    Log.info("Starting job submission...")

    # If remoto_queue is None (now only in lindgren) arch must signal both serial and parallel queues
    if remote_queue is None:
        signal.signal(signal.SIGQUIT, serial_queue.smart_stop)
        signal.signal(signal.SIGINT, serial_queue.normal_stop)
        signal.signal(signal.SIGQUIT, parallel_queue.smart_stop)
        signal.signal(signal.SIGINT, parallel_queue.normal_stop)
        serial_queue.set_scratch(scratch_dir)
        serial_queue.set_project(hpcproj)
        serial_queue.set_user(hpcuser)
        serial_queue.update_cmds()
        parallel_queue.set_scratch(scratch_dir)
        parallel_queue.set_project(hpcproj)
        parallel_queue.set_user(hpcuser)
        parallel_queue.update_cmds()
    else:
        signal.signal(signal.SIGQUIT, remote_queue.smart_stop)
        signal.signal(signal.SIGINT, remote_queue.normal_stop)
        remote_queue.set_scratch(scratch_dir)
        remote_queue.set_project(hpcproj)
        remote_queue.set_user(hpcuser)
        remote_queue.update_cmds()

    signal.signal(signal.SIGQUIT, local_queue.smart_stop)
    signal.signal(signal.SIGINT, local_queue.normal_stop)

    if rerun == 'false':
        filename = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + '/pkl/job_list_' + expid + '.pkl'
    else:
        filename = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + '/pkl/rerun_job_list_' + expid + '.pkl'
    Log.debug(filename)

    # the experiment should be loaded as well
    if os.path.exists(filename):
        joblist = cPickle.load(file(filename, 'rw'))
        Log.debug("Starting from joblist pickled in %s " % filename)
    else:
        Log.error("The pickle file %s necessary does not exist." % filename)
        sys.exit()

    Log.debug("Length of joblist: %s" % len(joblist))

    # Load parameters
    Log.debug("Loading parameters...")
    parameters = as_conf.load_parameters()
    Log.debug("Updating parameters...")
    joblist.update_parameters(parameters)
    # check the job list script creation
    Log.debug("Checking experiment templates...")
    if joblist.check_scripts(as_conf):
        Log.result("Experiment templates check PASSED!")
    else:
        Log.error("Experiment templates check FAILED!")
        sys.exit()

    # check the availability of the Queues
    local_queue.check_remote_log_dir()
    # in lindgren arch must check both serial and parallel queues
    if remote_queue is None:
        serial_queue.check_remote_log_dir()
        parallel_queue.check_remote_log_dir()
    else:
        remote_queue.check_remote_log_dir()

    # first job goes to the local Queue
    queue = local_queue

    #########################
    # AUTOSUBMIT - MAIN LOOP
    #########################
    # Main loop. Finishing when all jobs have been submitted
    while joblist.get_active():
        active = len(joblist.get_running())
        waiting = len(joblist.get_submitted() + joblist.get_queuing())
        available = max_waiting_jobs - waiting

        # reload parameters changes
        Log.debug("Reloading parameters...")
        as_conf.reload()
        parameters = as_conf.load_parameters()
        joblist.update_parameters(parameters)

        # variables to be updated on the fly
        max_jobs = as_conf.get_total_jobs()
        Log.debug("Total jobs: {0}".format(max_jobs))
        total_jobs = len(joblist.get_job_list())
        Log.info("\n{0} of {1} jobs remaining ({2})".format(total_jobs-len(joblist.get_completed()), total_jobs,
                                                             strftime("%H:%M")))
        safetysleeptime = as_conf.get_safetysleeptime()
        Log.debug("Sleep: %s" % safetysleeptime)
        retrials = as_conf.get_retrials()
        Log.debug("Number of retrials: %s" % retrials)

        # read FAIL_RETRIAL number if, blank at creation time put a given number
        # check availability of machine, if not next iteration after sleep time
        # check availability of jobs, if no new jobs submited and no jobs available, then stop

        # ??? why
        joblist.save()

        Log.info("Active jobs in queues:\t%s" % active)
        Log.info("Waiting jobs in queues:\t%s" % waiting)

        if available == 0:
            Log.debug("There's no room for more jobs...")
        else:
            Log.debug("We can safely submit %s jobs..." % available)

        ######################################
        # AUTOSUBMIT - ALREADY SUBMITTED JOBS
        ######################################
        # get the list of jobs currently in the Queue
        jobinqueue = joblist.get_in_queue()
        Log.info("Number of jobs in queue: %s" % str(len(jobinqueue)))

        # Check queue availability
        queueavail = queue.check_host()
        if not queueavail:
            Log.info("There is no queue available")
        else:
            for job in jobinqueue:

                job.print_job()
                Log.debug("Number of jobs in queue: %s" % str(len(jobinqueue)))
                # in lindgren arch must select serial or parallel queue acording to the job type
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
                # Check queue availability
                queueavail = queue.check_host()
                if not queueavail:
                    Log.debug("There is no queue available")
                else:
                    status = queue.check_job(job.id)
                    if status == Status.COMPLETED:
                        Log.debug("This job seems to have completed...checking")
                        queue.get_completed_files(job.name)
                        job.check_completion()
                    else:
                        job.status = status
                    if job.status is Status.QUEUING:
                        Log.info("Job %s is QUEUING", job.name)
                    elif job.status is Status.RUNNING:
                        Log.info("Job %s is RUNNING", job.name)
                    elif job.status is Status.COMPLETED:
                        Log.result("Job %s is COMPLETED", job.name)
                    elif job.status is Status.FAILED:
                        Log.user_warning("Job %s is FAILED", job.name)
                        # Uri add check if status UNKNOWN and exit if you want
                        # after checking the jobs , no job should have the status "submitted"
                        # Uri throw an exception if this happens (warning type no exit)

        # explain it !!
        joblist.update_list()

        ##############################
        # AUTOSUBMIT - JOBS TO SUBMIT
        ##############################
        # get the list of jobs READY
        jobsavail = joblist.get_ready()

        # Check queue availability
        queueavail = queue.check_host()
        if not queueavail:
            Log.debug("There is no queue available")
        elif min(available, len(jobsavail)) == 0:
            Log.debug("There is no job READY or available")
            Log.debug("Number of jobs ready: %s" % len(jobsavail))
            Log.debug("Number of jobs available in queue: %s" % available)
        elif min(available, len(jobsavail)) > 0 and len(jobinqueue) <= max_jobs:
            Log.info("\nStarting to submit %s job(s)" % min(available, len(jobsavail)))
            # should sort the jobsavail by priority Clean->post->sim>ini
            # s = sorted(jobsavail, key=lambda k:k.name.split('_')[1][:6])
            # probably useless to sort by year before sorting by type
            s = sorted(jobsavail, key=lambda k: k.long_name.split('_')[1][:6])

            list_of_jobs_avail = sorted(s, key=lambda k: k.type)

            for job in list_of_jobs_avail[0:min(available, len(jobsavail), max_jobs - len(jobinqueue))]:
                Log.debug(job.name)
                scriptname = job.create_script(as_conf)
                Log.debug(scriptname)
                # in lindgren arch must select serial or parallel queue acording to the job type
                if remote_queue is None and job.type == Type.SIMULATION:
                    queue = parallel_queue
                    Log.info("Submitting %s to parallel queue...", job.name)
                elif (remote_queue is None and (job.type == Type.REMOTESETUP or
                                                job.type == Type.INITIALISATION or
                                                job.type == Type.CLEANING or
                                                job.type == Type.POSTPROCESSING)):
                    queue = serial_queue
                    Log.info("Submitting %s to serial queue...", job.name)
                elif job.type == Type.LOCALSETUP or job.type == Type.TRANSFER:
                    queue = local_queue
                    Log.info("Submitting %s to local queue...", job.name)
                else:
                    queue = remote_queue
                    Log.info("Submitting %s to remote queue...", job.name)
                # Check queue availability
                queueavail = queue.check_host()
                if not queueavail:
                    Log.debug("There is no queue available")
                else:
                    queue.send_script(scriptname)
                    job.id = queue.submit_job(scriptname)
                    # set status to "submitted"
                    job.status = Status.SUBMITTED
                Log.info("%s submited\n", job.name)

        time.sleep(safetysleeptime)


if __name__ == "__main__":
    main()
