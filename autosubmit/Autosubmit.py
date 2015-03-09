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
from ConfigParser import SafeConfigParser
import argparse
from commands import getstatusoutput
import json
import time
import cPickle
import signal
import platform
import os
import sys
import shutil
import re
from pkg_resources import require, resource_listdir, resource_exists, resource_string
from time import strftime
from distutils.util import strtobool

from pyparsing import nestedExpr

from autosubmit.config.basicConfig import BasicConfig
from autosubmit.config.config_common import AutosubmitConfig
from autosubmit.job.job_common import Status
from autosubmit.git.git_common import AutosubmitGit
from autosubmit.job.job_list import JobList
from autosubmit.config.log import Log
from autosubmit.queue.psqueue import PsQueue
from autosubmit.queue.mn3queue import Mn3Queue
from autosubmit.queue.lgqueue import LgQueue
from autosubmit.queue.elqueue import ElQueue
from autosubmit.queue.arqueue import ArQueue
from autosubmit.queue.htqueue import HtQueue
from autosubmit.queue.itqueue import ItQueue
from autosubmit.queue.ecqueue import EcQueue
from autosubmit.queue.mnqueue import MnQueue
from autosubmit.database.db_common import create_db
from autosubmit.database.db_common import new_experiment
from autosubmit.database.db_common import copy_experiment
from autosubmit.database.db_common import delete_experiment
from autosubmit.monitor.monitor import Monitor


class Autosubmit:
    # Get the version number from the relevant file. If not, from autosubmit package
    scriptdir = os.path.abspath(os.path.dirname(sys.argv[0]))
    version_path = os.path.join(scriptdir, '..', 'VERSION')
    if os.path.isfile(version_path):
        with open(version_path) as f:
            autosubmit_version = f.read().strip()
    else:
        autosubmit_version = require("autosubmit")[0].version

    @staticmethod
    def parse_args():
        BasicConfig.read()

        parser = argparse.ArgumentParser(description='Main executable for autosubmit. ')
        parser.add_argument('-v', '--version', action='version', version=Autosubmit.autosubmit_version,
                            help="return Autosubmit's version number and exit")
        parser.add_argument('-lf', '--logfile', choices=('EVERYTHING', 'DEBUG', 'INFO', 'RESULT', 'USER_WARNING',
                                                         'WARNING', 'ERROR', 'CRITICAL', 'NO_LOG'),
                            default='INFO', type=str,
                            help="set log to file level.")
        parser.add_argument('-lc', '--logconsole', choices=('EVERYTHING', 'DEBUG', 'INFO', 'RESULT', 'USER_WARNING',
                                                            'WARNING', 'ERROR', 'CRITICAL', 'NO_LOG'),
                            default='INFO', type=str,
                            help="set log file level")

        subparsers = parser.add_subparsers(dest='command')

        # Run
        subparser = subparsers.add_parser('run', description="run specified experiment")
        subparser.add_argument('-e', '--expid', required=True, help='experiment identifier')

        # Expid
        subparser = subparsers.add_parser('expid', description="Creates a new experiment")
        group = subparser.add_mutually_exclusive_group()
        group.add_argument('-y', '--copy', help='makes a copy of the specified experiment')
        group.add_argument('-dm', '--dummy', action='store_true',
                           help='creates a new experiment with default values, usually for testing')

        subparser.add_argument('-H', '--HPC', required=True,
                               choices=('bsc', 'hector', 'ithaca', 'lindgren', 'ecmwf', 'ecmwf-cca',
                                        'marenostrum3', 'archer'),
                               help='Specifies the HPC to use for the experiment')
        subparser.add_argument('-d', '--description', type=str, required=True,
                               help='A description for the experiment to store in the database.')

        # Delete
        subparser = subparsers.add_parser('delete', description="delete specified experiment")
        subparser.add_argument('-e', '--expid', required=True, help='experiment identifier')
        subparser.add_argument('-f', '--force', action='store_true', help='delete experiment without confirmation')

        # Monitor
        subparser = subparsers.add_parser('monitor', description="plots specified experiment")
        subparser.add_argument('-e', '--expid', required=True, help='experiment identifier')
        subparser.add_argument('-j', '--joblist', required=True, help='joblist to print')
        subparser.add_argument('-o', '--output', required=True, choices=('pdf', 'png', 'ps'), default='pdf',
                               help='type of output for generated plot')

        # Stats
        subparser = subparsers.add_parser('stats', description="plots statistics for specified experiment")
        subparser.add_argument('-e', '--expid', required=True, help='experiment identifier')
        subparser.add_argument('-j', '--joblist', required=True, help='joblist to print')
        subparser.add_argument('-o', '--output', required=True, choices=('pdf', 'png', 'ps'), default='pdf',
                               help='type of output for generated plot')

        # Clean
        subparser = subparsers.add_parser('clean', description="clean specified experiment")
        subparser.add_argument('-e', '--expid', required=True, help='experiment identifier')
        subparser.add_argument('-pr', '--project', action="store_true", help='clean project')
        subparser.add_argument('-p', '--plot', action="store_true",
                               help='clean plot, only 2 last will remain')

        # Recovery
        subparser = subparsers.add_parser('recovery', description="recover specified experiment")
        subparser.add_argument('-e', '--expid', type=str, required=True, help='experiment identifier')
        subparser.add_argument('-j', '--joblist', type=str, required=True, help='Job list')
        subparser.add_argument('-g', '--get', action="store_true", default=False,
                               help='Get completed files to synchronize pkl')
        subparser.add_argument('-s', '--save', action="store_true", default=False, help='Save changes to disk')

        # Check
        subparser = subparsers.add_parser('check', description="check configuration for specified experiment")
        subparser.add_argument('-e', '--expid', required=True, help='experiment identifier')

        # Create
        subparser = subparsers.add_parser('create', description="create specified experiment joblist")
        subparser.add_argument('-e', '--expid', required=True, help='experiment identifier')
        subparser.add_argument('-np', '--noplot', action='store_true', default=False, help='omit plot')

        # Configure
        subparser = subparsers.add_parser('configure', description="configure database and path for autosubmit. It "
                                                                   "can be done at machine, user or local level (by "
                                                                   "default at machine level)")
        subparser.add_argument('-db', '--databasepath', default=None, help='path to database. If not supplied, '
                                                                           'it will be prompt for it')
        subparser.add_argument('-lr', '--localrootpath', default=None, help='path to store experiments. If not '
                                                                            'supplied, it will be prompt for it')
        group = subparser.add_mutually_exclusive_group()
        group.add_argument('-u', '--user', action="store_true", help='configure only for this user')
        group.add_argument('-l', '--local', action="store_true", help='configure only for using Autosubmit from this '
                                                                      'path')

        # Install
        subparser = subparsers.add_parser('install', description='install database and scripts needed for autosubmit')
        subparser.add_argument('-db', '--database', action="store_true", help='install the database in the '
                                                                              'previously configured path')

        # Change_pkl
        subparser = subparsers.add_parser('change_pkl', description="change job status for an experiment")
        subparser.add_argument('-e', '--expid', type=str, required=True, help='experiment identifier')
        subparser.add_argument('-j', '--joblist', type=str, required=True, help='Job list')
        subparser.add_argument('-s', '--save', action="store_true", default=False, help='Save changes to disk')
        subparser.add_argument('-t', '--status_final',
                               choices=('READY', 'COMPLETED', 'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN'),
                               required=True,
                               help='Supply the target status')
        group1 = subparser.add_mutually_exclusive_group(required=True)
        group1.add_argument('-l', '--list', type=str,
                            help='Alternative 1: Supply the list of job names to be changed. Default = "Any". '
                                 'LIST = "b037_20101101_fc3_21_sim b037_20111101_fc4_26_sim"')
        group1.add_argument('-f', '--filter', action="store_true",
                            help='Alternative 2: Supply a filter for the job list. See help of filter arguments: '
                                 'chunk filter, status filter or type filter')
        group2 = subparser.add_mutually_exclusive_group(required=False)
        group2.add_argument('-fc', '--filter_chunks', type=str,
                            help='Supply the list of chunks to change the status. Default = "Any". '
                                 'LIST = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]"')
        group2.add_argument('-fs', '--filter_status', type=str,
                            choices=('Any', 'READY', 'COMPLETED', 'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN'),
                            help='Select the original status to filter the list of jobs')
        group2.add_argument('-ft', '--filter_type', type=str,
                            help='Select the job type to filter the list of jobs')

        args = parser.parse_args()

        Log.set_console_level(args.logconsole)
        Log.set_file_level(args.logfile)

        if args.command == 'run':
            Autosubmit.run_experiment(args.expid)
        elif args.command == 'expid':
            Autosubmit.expid(args.HPC, args.description, args.copy, args.dummy)
        elif args.command == 'delete':
            Autosubmit.delete(args.expid, args.force)
        elif args.command == 'monitor':
            Autosubmit.monitor(args.expid, args.joblist, args.output)
        elif args.command == 'stats':
            Autosubmit.statistics(args.expid, args.joblist, args.output)
        elif args.command == 'clean':
            Autosubmit.clean(args.expid, args.project, args.plot)
        elif args.command == 'recovery':
            Autosubmit.recovery(args.expid, args.joblist, args.save, args.get)
        elif args.command == 'check':
            Autosubmit.check(args.expid)
        elif args.command == 'create':
            Autosubmit.create(args.expid, args.noplot)
        elif args.command == 'configure':
            Autosubmit.configure(args.databasepath, args.localrootpath, args.user, args.local)
        elif args.command == 'install':
            Autosubmit.install(args.database)
        elif args.command == 'change_pkl':
            Autosubmit.change_pkl(args.expid, args.joblist, args.save, args.status_final, args.list, args.filter,
                                  args.filter_chunks, args.filter_status, args.filter_section)

    @staticmethod
    def delete_expid(expid_delete):
        Log.info("Removing experiment directory...")
        try:
            shutil.rmtree(BasicConfig.LOCAL_ROOT_DIR + "/" + expid_delete)
        except OSError:
            pass
        Log.info("Deleting experiment from database...")
        delete_experiment(expid_delete)
        Log.result("Experiment {0} deleted".format(expid_delete))

    @staticmethod
    def expid(hpc, description, copy, dummy):
        BasicConfig.read()

        log_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, 'expid{0}.log'.format(os.getuid()))
        try:
            Log.set_file(log_path)
        except IOError as e:
            Log.error("Can not create log file in path {0}: {1}".format(log_path, e.message))
        exp_id = None
        if description is None:
            Log.error("Missing experiment description.")
            exit(2)
        if hpc is None:
            Log.error("Missing HPC.")
            exit(1)
        if not copy:
            exp_id = new_experiment(hpc, description)
            try:
                os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id)

                os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + '/conf')
                Log.info("Copying config files...")
                # autosubmit config and experiment copyed from AS.
                files = resource_listdir('autosubmit.config', 'files')
                for filename in files:
                    if resource_exists('autosubmit.config', 'files/' + filename):
                        index = filename.index('.')
                        new_filename = filename[:index] + "_" + exp_id + filename[index:]
                        content = resource_string('autosubmit.config', 'files/' + filename)
                        Log.debug(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/conf/" + new_filename)
                        file(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/conf/" + new_filename, 'w').write(content)
                Autosubmit._prepare_conf_files(exp_id, hpc, Autosubmit.autosubmit_version, dummy)
            except (OSError, IOError) as e:
                Log.error("Can not create experiment: {0}\nCleaning...".format(e.message))
                Autosubmit.delete_expid(exp_id)
                exit(1)
        else:
            try:
                if os.path.exists(BasicConfig.LOCAL_ROOT_DIR + "/" + copy):
                    exp_id = copy_experiment(copy, hpc, description)
                    os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id)
                    os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + '/conf')
                    Log.info("Copying previous experiment config directories")
                    files = os.listdir(BasicConfig.LOCAL_ROOT_DIR + "/" + copy + "/conf")
                    for filename in files:
                        if os.path.isfile(BasicConfig.LOCAL_ROOT_DIR + "/" + copy + "/conf/" + filename):
                            new_filename = filename.replace(copy, exp_id)
                            content = file(BasicConfig.LOCAL_ROOT_DIR + "/" + copy + "/conf/" + filename, 'r').read()
                            file(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/conf/" + new_filename,
                                 'w').write(content)
                    Autosubmit._prepare_conf_files(exp_id, hpc, Autosubmit.autosubmit_version, dummy)
                else:
                    Log.critical("The previous experiment directory does not exist")
                    sys.exit(1)
            except (OSError, IOError) as e:
                Log.error("Can not create experiment: {0}\nCleaning...".format(e.message))
                Autosubmit.delete_expid(exp_id)
                exit(1)

        Log.debug("Creating temporal directory...")
        os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/" + "tmp")

        Log.debug("Creating pkl directory...")
        os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/" + "pkl")

        Log.debug("Creating plot directory...")
        os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/" + "plot")
        os.chmod(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/" + "plot", 0o775)
        Log.result("Experiment registered successfully")
        Log.user_warning("Remember to MODIFY the config files!")

    @staticmethod
    def delete(expid, force):
        if os.path.exists(BasicConfig.LOCAL_ROOT_DIR + "/" + expid):
            if force or Autosubmit._user_yes_no_query("Do you want to delete " + expid + " ?"):
                Autosubmit.delete_expid(expid)
            else:
                Log.info("Quitting...")
                sys.exit(1)
        else:
            Log.error("The experiment does not exist")
            sys.exit(1)

    @staticmethod
    def run_experiment(expid):
        """This is the main script of autosubmit. All the stream of execution is handled here
        (submitting all the jobs properly and repeating its execution in case of failure)."""
        if expid is None:
            Log.critical("Missing expid.")
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                  'autosubmit.log'))
        os.system('clear')

        as_conf = AutosubmitConfig(expid)
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

        for job in joblist.get_job_list():
            if job.queue_name == 'LOCAL':
                job.queue = local_queue
            else:
                job.queue = remote_queue
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

            for job in jobinqueue:

                job.print_job()
                Log.debug("Number of jobs in queue: %s" % str(len(jobinqueue)))
                # Check queue availability
                queueavail = job.queue.check_host()
                if not queueavail:
                    Log.debug("There is no queue available")
                else:
                    status = job.queue.check_job(job.id)
                    if status == Status.COMPLETED:
                        Log.debug("This job seems to have completed...checking")
                        job.queue.get_completed_files(job.name)
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

            if min(available, len(jobsavail)) == 0:
                Log.debug("There is no job READY or available")
                Log.debug("Number of jobs ready: %s" % len(jobsavail))
                Log.debug("Number of jobs available in queue: %s" % available)
            elif min(available, len(jobsavail)) > 0 and len(jobinqueue) <= max_jobs:
                Log.info("\nStarting to submit %s job(s)" % min(available, len(jobsavail)))
                # should sort the jobsavail by priority Clean->post->sim>ini
                # s = sorted(jobsavail, key=lambda k:k.name.split('_')[1][:6])
                # probably useless to sort by year before sorting by type
                s = sorted(jobsavail, key=lambda k: k.long_name.split('_')[1][:6])

                list_of_jobs_avail = sorted(s, key=lambda k: k.priority, reverse=True)

                for job in list_of_jobs_avail[0:min(available, len(jobsavail), max_jobs - len(jobinqueue))]:
                    Log.debug(job.name)
                    scriptname = job.create_script(as_conf)
                    Log.debug(scriptname)
                    # in lindgren arch must select serial or parallel queue acording to the job type
                    if job.queue_name == 'LOCAL':
                        Log.info("Submitting %s to local queue...", job.name)
                        job.queue = local_queue
                    else:
                        Log.info("Submitting %s to remote queue...", job.name)
                        job.queue = remote_queue

                    # Check queue availability
                    queueavail = job.queue.check_host()
                    if not queueavail:
                        Log.debug("There is no queue available")
                    else:
                        job.queue.send_script(scriptname)
                        job.id = job.queue.submit_job(scriptname)
                        # set status to "submitted"
                        job.status = Status.SUBMITTED
                    Log.info("%s submitted\n", job.name)

            time.sleep(safetysleeptime)

    @staticmethod
    def monitor(expid, root_name, output):
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR, 'monitor.log'))
        filename = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + '/pkl/' + root_name + '_' + expid + '.pkl'
        Log.info("Getting job list...")
        jobs = cPickle.load(file(filename, 'r'))
        if not isinstance(jobs, type([])):
            jobs = jobs.get_job_list()

        Log.info("Plotting...")
        monitor_exp = Monitor()
        monitor_exp.generate_output(expid, jobs, output)
        Log.result("Plot ready")

    @staticmethod
    def statistics(expid, root_name, output):
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                  'statistics.log'))
        Log.info("Loading jobs...")
        filename = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + '/pkl/' + root_name + '_' + expid + '.pkl'
        jobs = cPickle.load(file(filename, 'r'))
        # if not isinstance(jobs, type([])):
        #     jobs = [job for job in jobs.get_finished() if job.type == Type.SIMULATION]

        if len(jobs.get_job_list()) > 0:
            Log.info("Plotting stats...")
            monitor_exp = Monitor()
            monitor_exp.generate_output_stats(expid, jobs.get_job_list(), output)
            Log.result("Stats plot ready")
        else:
            Log.info("There are no COMPLETED jobs...")

    @staticmethod
    def clean(expid, project, plot):
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                  'finalise_exp.log'))
        if project:
            autosubmit_config = AutosubmitConfig(expid)
            autosubmit_config.check_conf()
            project_type = autosubmit_config.get_project_type()
            if project_type == "git":
                autosubmit_config.check_proj()
                Log.info("Registering commit SHA...")
                autosubmit_config.set_git_project_commit()
                autosubmit_git = AutosubmitGit(expid[0])
                Log.info("Cleaning GIT directory...")
                autosubmit_git.clean_git()
            else:
                Log.info("No project to clean...\n")
        if plot:
            Log.info("Cleaning plot directory...")
            monitor_autosubmit = Monitor()
            monitor_autosubmit.clean_plot(expid)

    @staticmethod
    def recovery(expid, root_name, save, get):
        BasicConfig.read()

        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                  'recovery.log'))

        Log.info('Recovering experiment {0}'.format(expid))
        l1 = cPickle.load(file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, 'pkl', root_name + "_" + expid + ".pkl"),
                               'r'))

        as_conf = AutosubmitConfig(expid)
        as_conf.check_conf()

        hpcarch = as_conf.get_platform()
        scratch_dir = as_conf.get_scratch_dir()
        hpcproj = as_conf.get_hpcproj()
        hpcuser = as_conf.get_hpcuser()

        if get:
            remote_queue = None

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
            elif hpcarch == 'ecmwf-cca':
                remote_queue = EcQueue(expid)
                remote_queue.set_scratch(scratch_dir)
                remote_queue.set_project(hpcproj)
                remote_queue.set_user(hpcuser)
                remote_queue.set_host("cca")
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
                if job.queue_name == 'LOCAL':
                    job.queue = local_queue
                else:
                    job.queue = remote_queue
                if job.queue.get_completed_files(job.name):
                    job.status = Status.COMPLETED
                    Log.info("CHANGED job '{0}' status to COMPLETED".format(job.name))
                elif job.status != Status.SUSPENDED:
                    job.status = Status.READY
                    job.set_fail_count(0)
                    Log.info("CHANGED job '{0}' status to READY".format(job.name))

            sys.setrecursionlimit(50000)
            l1.update_list()
            cPickle.dump(l1, file(BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl",
                                  'w'))

        if save:
            l1.update_from_file()
        else:
            l1.update_from_file(False)

        if save:
            sys.setrecursionlimit(50000)
            cPickle.dump(l1, file(BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid +
                                  ".pkl", 'w'))
        Log.result("Recovery finalized")
        monitor_exp = Monitor()
        monitor_exp.generate_output(expid, l1.get_job_list())

    @staticmethod
    def check(expid):
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR, 'check_exp.log'))
        as_conf = AutosubmitConfig(expid)
        as_conf.check_conf()
        project_type = as_conf.get_project_type()
        if project_type != "none":
            as_conf.check_proj()

        # print "Checking experiment configuration..."
        # if as_conf.check_parameters():
        #     print "Experiment configuration check PASSED!"
        # else:
        #     print "Experiment configuration check FAILED!"
        #     print "WARNING: running after FAILED experiment configuration check is at your own risk!!!"

        Log.info("Checking experiment templates...")
        if Autosubmit._check_templates(as_conf):
            Log.result("Experiment templates check PASSED!")
        else:
            Log.critical("Experiment templates check FAILED!")
            Log.warning("Running after FAILED experiment templates check is at your own risk!!!")

    @staticmethod
    def configure(database_path, local_root_path,  user, local):
        home_path = os.path.expanduser('~')
        while database_path is None:
            database_path = raw_input("Introduce Database path: ")
        database_path = database_path.replace('~', home_path)
        if not os.path.exists(database_path):
            Log.error("Database path does not exist.")
            exit(1)

        while local_root_path is None:
            local_root_path = raw_input("Introduce Local Root path: ")
        local_root_path = local_root_path.replace('~', home_path)
        if not os.path.exists(local_root_path):
            Log.error("Local Root path does not exist.")
            exit(1)

        if user:
            path = home_path
        elif local:
            path = '.'
        else:
            path = '/etc'
        path = os.path.join(path, '.autosubmitrc')

        config_file = open(path, 'w')
        Log.info("Writing configuration file...")
        try:
            parser = SafeConfigParser()
            parser.add_section('database')
            parser.set('database', 'path', database_path)
            parser.add_section('local')
            parser.set('local', 'path', local_root_path)
            parser.write(config_file)
            config_file.close()
            Log.result("Configuration file written successfully")
        except (IOError, OSError) as e:
            Log.critical("Can not write config file: {0}".format(e.message))

    @staticmethod
    def install(database):
        BasicConfig.read()

        if database:
            if not os.path.exists(BasicConfig.DB_PATH):
                Log.info("Creating autosubmit database...")
                try:
                    qry = resource_string('autosubmit.database', 'data/autosubmit.sql')
                    create_db(qry)
                    Log.result("Autosubmit database creatd successfully")
                except Exception as e:
                    Log.critical("Can not write database file: {0}".format(e.message))
            else:
                Log.error("Database already exists.")
                exit(1)

    @staticmethod
    def create(expid, noplot):
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                  'create_exp.log'))
        as_conf = AutosubmitConfig(expid)
        as_conf.check_conf()

        expid = as_conf.get_expid()
        project_type = as_conf.get_project_type()

        if project_type == "git":
            git_project_origin = as_conf.get_git_project_origin()
            git_project_branch = as_conf.get_git_project_branch()
            project_path = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/" + BasicConfig.LOCAL_PROJ_DIR
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
                    Log.error("Can not clone %s into %s" % (git_project_branch + " " + git_project_origin,
                                                            project_path))
                    exit(1)

                Log.debug("%s" % output)
                git_project_name = output[output.find("'")+1:output.find("...")-1]
                (status, output) = getstatusoutput("cd " + project_path + "/" + git_project_name +
                                                   "; git submodule update --remote --init")
                if status:
                    os.rmdir(project_path)
                    Log.error("Can not clone %s into %s" % (git_project_branch + " " + git_project_origin,
                                                            project_path))
                    exit(1)
                Log.debug("%s" % output)

                (status, output) = getstatusoutput("cd " + project_path + "/" + git_project_name +
                                                   "; git submodule foreach -q 'branch=\"$(git config "
                                                   "-f $toplevel/.gitmodules submodule.$name.branch)\"; "
                                                   "git checkout $branch'")
                if status:
                    os.rmdir(project_path)
                    Log.error("Can not clone %s into %s" % (git_project_branch + " " + git_project_origin,
                                                            project_path))
                    exit(1)
                Log.debug("%s" % output)

        elif project_type == "svn":
            svn_project_url = as_conf.get_svn_project_url()
            svn_project_revision = as_conf.get_svn_project_revision()
            project_path = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/" + BasicConfig.LOCAL_PROJ_DIR
            if os.path.exists(project_path):
                Log.debug("The project folder exists. SKIPPING...")
                Log.info("Using project folder: %s" % project_path)
            else:
                os.mkdir(project_path)
                Log.debug("The project folder %s has been created." % project_path)
                Log.info("Checking out revision %s into %s" % (svn_project_revision + " " + svn_project_url,
                                                               project_path))
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
            project_path = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/" + BasicConfig.LOCAL_PROJ_DIR
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
        if len(date_list) != len(set(date_list)):
            Log.error('There are repeated start dates!')
            exit(1)
        starting_chunk = as_conf.get_starting_chunk()
        num_chunks = as_conf.get_num_chunks()
        member_list = as_conf.get_member_list()
        if len(date_list) != len(set(date_list)):
            Log.error('There are repeated member names!')
            exit(1)
        rerun = as_conf.get_rerun()

        Log.info("\nCreating joblist...")
        job_list = JobList(expid)
        job_list.create(date_list, member_list, starting_chunk, num_chunks, parameters)
        if rerun == "true":
            chunk_list = Autosubmit._create_json(as_conf.get_chunk_list())
            job_list.rerun(chunk_list)

        pltfrm = as_conf.get_platform()
        if pltfrm == 'hector' or pltfrm == 'archer':
            job_list.update_shortened_names()

        Log.info("\nSaving joblist...")
        job_list.save()
        if not noplot:
            Log.info("\nPloting joblist...")
            monitor_exp = Monitor()
            monitor_exp.generate_output(expid, job_list.get_job_list(), 'pdf')

        Log.result("\nJob list created succesfully")
        Log.user_warning("Remember to MODIFY the MODEL config files!")

    @staticmethod
    def change_pkl(expid, root_name, save, final, lst, flt,
                   filter_chunks, filter_status, filter_section):
        BasicConfig.read()

        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                  'change_pkl.log'))
        Log.debug('Exp ID: %', expid)
        l1 = cPickle.load(file(BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid +
                               ".pkl", 'r'))

        if flt:
            if filter_chunks:
                fc = filter_chunks
                Log.debug(fc)

                if fc == 'Any':
                    for job in l1.get_job_list():
                        job.status = Autosubmit._get_status(final)
                        Log.info("CHANGED: job: " + job.name + " status to: " + final)
                else:
                    data = json.loads(Autosubmit._create_json(fc))
                    # change localsetup and remotesetup
                    # [...]
                    for date in data['sds']:
                        for member in date['ms']:
                            jobname_ini = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_ini"
                            job = l1.get_job_by_name(jobname_ini)
                            job.status = Autosubmit._get_status(final)
                            Log.info("CHANGED: job: " + job.name + " status to: " + final)
                            # change also trans
                            jobname_trans = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_trans"
                            job = l1.get_job_by_name(jobname_trans)
                            job.status = Autosubmit._get_status(final)
                            Log.info("CHANGED: job: " + job.name + " status to: " + final)
                            # [...]
                            for chunk in member['cs']:
                                jobname_sim = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(
                                    chunk) + "_sim"
                                jobname_post = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(
                                    chunk) + "_post"
                                jobname_clean = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(
                                    chunk) + "_clean"
                                job = l1.get_job_by_name(jobname_sim)
                                job.status = Autosubmit._get_status(final)
                                Log.info("CHANGED: job: " + job.name + " status to: " + final)
                                job = l1.get_job_by_name(jobname_post)
                                job.status = Autosubmit._get_status(final)
                                Log.info("CHANGED: job: " + job.name + " status to: " + final)
                                job = l1.get_job_by_name(jobname_clean)
                                job.status = Autosubmit._get_status(final)
                                Log.info("CHANGED: job: " + job.name + " status to: " + final)

            if filter_status:
                fs = filter_status
                Log.debug(fs)

                if fs == 'Any':
                    for job in l1.get_job_list():
                        job.status = Autosubmit._get_status(final)
                        Log.info("CHANGED: job: " + job.name + " status to: " + final)
                else:
                    for job in l1.get_job_list():
                        if job.status == Autosubmit._get_status(fs):
                            job.status = Autosubmit._get_status(final)
                            Log.info("CHANGED: job: " + job.name + " status to: " + final)

            if filter_section:
                ft = filter_section
                Log.debug(ft)

                if ft == 'Any':
                    for job in l1.get_job_list():
                        job.status = Autosubmit._get_status(final)
                        Log.info("CHANGED: job: " + job.name + " status to: " + final)
                else:
                    for job in l1.get_job_list():
                        if job.section == ft:
                            job.status = Autosubmit._get_status(final)
                            Log.info("CHANGED: job: " + job.name + " status to: " + final)

        if lst:
            jobs = lst.split()

            if jobs == 'Any':
                for job in l1.get_job_list():
                    job.status = Autosubmit._get_status(final)
                    Log.info("CHANGED: job: " + job.name + " status to: " + final)
            else:
                for job in l1.get_job_list():
                    if job.name in jobs:
                        job.status = Autosubmit._get_status(final)
                        Log.info("CHANGED: job: " + job.name + " status to: " + final)

        sys.setrecursionlimit(50000)

        if save:
            l1.update_list()
            cPickle.dump(l1, file(BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl",
                                  'w'))
            Log.info("Saving JobList: " + BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid +
                     ".pkl")
        else:
            l1.update_list(False)
            Log.warning("Changes NOT saved to the JobList!!!!:  use -s option to save")

        monitor_exp = Monitor()

        monitor_exp.generate_output(expid, l1.get_job_list())

    @staticmethod
    def _user_yes_no_query(question):
        sys.stdout.write('%s [y/n]\n' % question)
        while True:
            try:
                return strtobool(raw_input().lower())
            except ValueError:
                sys.stdout.write('Please respond with \'y\' or \'n\'.\n')

    @staticmethod
    def _prepare_conf_files(exp_id, hpc, autosubmit_version, dummy):
        as_conf = AutosubmitConfig(exp_id)
        as_conf.set_version(autosubmit_version)
        as_conf.set_expid(exp_id)
        as_conf.set_local_root()
        as_conf.set_platform(hpc)
        as_conf.set_scratch_dir(hpc)
        as_conf.set_safetysleeptime(hpc)

        if dummy:
            content = file(as_conf.experiment_file).read()

            # Experiment
            content = content.replace(re.search('DATELIST =.*', content).group(0),
                                      "DATELIST = 20000101")
            content = content.replace(re.search('MEMBERS =.*', content).group(0),
                                      "MEMBERS = fc0")
            content = content.replace(re.search('CHUNKSIZE =.*', content).group(0),
                                      "CHUNKSIZE = 4")
            content = content.replace(re.search('NUMCHUNKS =.*', content).group(0),
                                      "NUMCHUNKS = 1")
            content = content.replace(re.search('PROJECT_TYPE =.*', content).group(0),
                                      "PROJECT_TYPE = none")

            # # Wallclocks
            # content = content.replace(re.search('WALLCLOCK_SETUP =.*', content).group(0),
            #                           "WALLCLOCK_SETUP = 00:01")
            # content = content.replace(re.search('WALLCLOCK_INI =.*', content).group(0),
            #                           "WALLCLOCK_INI = 00:01")
            # content = content.replace(re.search('WALLCLOCK_SIM =.*', content).group(0),
            #                           "WALLCLOCK_SIM = 00:01")
            # content = content.replace(re.search('WALLCLOCK_POST =.*', content).group(0),
            #                           "WALLCLOCK_POST = 00:01")
            # content = content.replace(re.search('WALLCLOCK_CLEAN =.*', content).group(0),
            #                           "WALLCLOCK_CLEAN = 00:01")
            #
            # # Processors
            # content = content.replace(re.search('NUMPROC_SETUP =.*', content).group(0),
            #                           "NUMPROC_SETUP = 1")
            # content = content.replace(re.search('NUMPROC_INI =.*', content).group(0),
            #                           "NUMPROC_INI = 1")
            # content = content.replace(re.search('NUMPROC_SIM =.*', content).group(0),
            #                           "NUMPROC_SIM = 1")
            # content = content.replace(re.search('NUMTHREAD_SIM =.*', content).group(0),
            #                           "NUMTHREAD_SIM = 1")
            # content = content.replace(re.search('NUMTASK_SIM =.*', content).group(0),
            #                           "NUMTASK_SIM = 1")
            # content = content.replace(re.search('NUMPROC_POST =.*', content).group(0),
            #                           "NUMPROC_POST = 1")
            # content = content.replace(re.search('NUMPROC_CLEAN =.*', content).group(0),
            #                           "NUMPROC_CLEAN = 1")
            #
            # content = content.replace(re.search('PROJECT_TYPE =.*', content).group(0),
            #                           "PROJECT_TYPE = none")

            file(as_conf.experiment_file, 'w').write(content)

    @staticmethod
    def _check_templates(as_conf):
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
        out = joblist.check_scripts(as_conf)
        return out

    @staticmethod
    def _get_status(s):
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

    @staticmethod
    def _get_members(out):
        count = 0
        data = []
        # noinspection PyUnusedLocal
        for element in out:
            if count % 2 == 0:
                ms = {'m': out[count], 'cs': Autosubmit._get_chunks(out[count + 1])}
                data.append(ms)
                count += 1
            else:
                count += 1

        return data

    @staticmethod
    def _get_chunks(out):
        data = []
        for element in out:
            if element.find("-") != -1:
                numbers = element.split("-")
                for count in range(int(numbers[0]), int(numbers[1]) + 1):
                    data.append(str(count))
            else:
                data.append(element)

        return data

    @staticmethod
    def _create_json(text):
        count = 0
        data = []
        # text = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 16651101 [ fc0 [1-30 31 32] ] ]"

        out = nestedExpr('[', ']').parseString(text).asList()

        # noinspection PyUnusedLocal
        for element in out[0]:
            if count % 2 == 0:
                sd = {'sd': out[0][count], 'ms': Autosubmit._get_members(out[0][count + 1])}
                data.append(sd)
                count += 1
            else:
                count += 1

        sds = {'sds': data}
        result = json.dumps(sds)
        return result

