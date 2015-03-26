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

"""
Main module for autosubmit. Only contains an interface class to all functionality implemented on autosubmit
"""

from ConfigParser import SafeConfigParser
import argparse
from commands import getstatusoutput
import json
import time
import cPickle
import os
import sys
import shutil
import re
import random
from pkg_resources import require, resource_listdir, resource_exists, resource_string
from time import strftime
from distutils.util import strtobool

from pyparsing import nestedExpr

sys.path.insert(0, os.path.abspath('.'))

from config.basicConfig import BasicConfig
from config.config_common import AutosubmitConfig
from job.job_common import Status
from git.git_common import AutosubmitGit
from job.job_list import JobList
from config.log import Log
from database.db_common import create_db
from database.db_common import new_experiment
from database.db_common import copy_experiment
from database.db_common import delete_experiment
from monitor.monitor import Monitor


class Autosubmit:
    """
    Interface class for autosubmit.
    """
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
        """
        Parse arguments given to an executable and start execution of command given
        """
        BasicConfig.read()

        parser = argparse.ArgumentParser(description='Main executable for autosubmit. ')
        parser.add_argument('-v', '--version', action='version', version=Autosubmit.autosubmit_version,
                            help="returns autosubmit's version number and exit")
        parser.add_argument('-lf', '--logfile', choices=('EVERYTHING', 'DEBUG', 'INFO', 'RESULT', 'USER_WARNING',
                                                         'WARNING', 'ERROR', 'CRITICAL', 'NO_LOG'),
                            default='DEBUG', type=str,
                            help="sets file's log level.")
        parser.add_argument('-lc', '--logconsole', choices=('EVERYTHING', 'DEBUG', 'INFO', 'RESULT', 'USER_WARNING',
                                                            'WARNING', 'ERROR', 'CRITICAL', 'NO_LOG'),
                            default='INFO', type=str,
                            help="sets console's log level")

        subparsers = parser.add_subparsers(dest='command')

        # Run
        subparser = subparsers.add_parser('run', description="runs specified experiment")
        subparser.add_argument('expid', help='experiment identifier')

        # Expid
        subparser = subparsers.add_parser('expid', description="Creates a new experiment")
        group = subparser.add_mutually_exclusive_group()
        group.add_argument('-y', '--copy', help='makes a copy of the specified experiment')
        group.add_argument('-dm', '--dummy', action='store_true',
                           help='creates a new experiment with default values, usually for testing')

        subparser.add_argument('-H', '--HPC', required=True,
                               help='specifies the HPC to use for the experiment')
        subparser.add_argument('-d', '--description', type=str, required=True,
                               help='sets a description for the experiment to store in the database.')

        # Delete
        subparser = subparsers.add_parser('delete', description="delete specified experiment")
        subparser.add_argument('expid',  help='experiment identifier')
        subparser.add_argument('-f', '--force', action='store_true', help='deletes experiment without confirmation')

        # Monitor
        subparser = subparsers.add_parser('monitor', description="plots specified experiment")
        subparser.add_argument('expid', help='experiment identifier')
        subparser.add_argument('-o', '--output', choices=('pdf', 'png', 'ps'), default='pdf',
                               help='chooses type of output for generated plot')

        # Stats
        subparser = subparsers.add_parser('stats', description="plots statistics for specified experiment")
        subparser.add_argument('expid', help='experiment identifier')
        subparser.add_argument('-o', '--output', choices=('pdf', 'png', 'ps'), default='pdf',
                               help='type of output for generated plot')

        # Clean
        subparser = subparsers.add_parser('clean', description="clean specified experiment")
        subparser.add_argument('expid', help='experiment identifier')
        subparser.add_argument('-pr', '--project', action="store_true", help='clean project')
        subparser.add_argument('-p', '--plot', action="store_true",
                               help='clean plot, only 2 last will remain')
        subparser.add_argument('-s', '--stats', action="store_true",
                               help='clean stats, only last will remain')

        # Recovery
        subparser = subparsers.add_parser('recovery', description="recover specified experiment")
        subparser.add_argument('expid', type=str, help='experiment identifier')
        subparser.add_argument('-g', '--get', action="store_true", default=False,
                               help='Get completed files to synchronize pkl')
        subparser.add_argument('-s', '--save', action="store_true", default=False, help='Save changes to disk')

        # Check
        subparser = subparsers.add_parser('check', description="check configuration for specified experiment")
        subparser.add_argument('expid',  help='experiment identifier')

        # Create
        subparser = subparsers.add_parser('create', description="create specified experiment joblist")
        subparser.add_argument('expid',  help='experiment identifier')
        subparser.add_argument('-np', '--noplot', action='store_true', default=False, help='omit plot')

        # Configure
        subparser = subparsers.add_parser('configure', description="configure database and path for autosubmit. It "
                                                                   "can be done at machine, user or local level (by "
                                                                   "default at machine level)")
        subparser.add_argument('-db', '--databasepath', default=None, help='path to database. If not supplied, '
                                                                           'it will prompt for it')
        subparser.add_argument('-dbf', '--databasefilename', default=None, help='database filename')
        subparser.add_argument('-lr', '--localrootpath', default=None, help='path to store experiments. If not '
                                                                            'supplied, it will prompt for it')
        subparser.add_argument('-qc', '--queuesconfpath', default=None, help='path to queues.conf file to use by '
                                                                             'default. If not supplied, it will not '
                                                                             'prompt for it')
        subparser.add_argument('-jc', '--jobsconfpath', default=None, help='path to jobs.conf file to use by '
                                                                           'default. If not supplied, it will not '
                                                                           'prompt for it')
        group = subparser.add_mutually_exclusive_group()
        group.add_argument('-u', '--user', action="store_true", help='configure only for this user')
        group.add_argument('-l', '--local', action="store_true", help='configure only for using Autosubmit from this '
                                                                      'path')

        # Install
        subparsers.add_parser('install', description='install database for autosubmit on the configured folder')

        # Change_pkl
        subparser = subparsers.add_parser('change_pkl', description="change job status for an experiment")
        subparser.add_argument('expid',  help='experiment identifier')
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

        # Test
        subparser = subparsers.add_parser('test', description='test experiment')
        subparser.add_argument('expid',  help='experiment identifier')
        subparser.add_argument('-c', '--chunks', required=True, help='chunks to run')
        subparser.add_argument('-m', '--member', help='member to run')
        subparser.add_argument('-s', '--stardate', help='stardate to run')
        subparser.add_argument('-H', '--HPC', help='HPC to run experiment on it')
        subparser.add_argument('-b', '--branch', help='branch of git to run (or revision from subversion)')

        # Refresh
        subparser = subparsers.add_parser('refresh', description='refresh project directory for an experiment')
        subparser.add_argument('expid',  help='experiment identifier')

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
            Autosubmit.monitor(args.expid, args.output)
        elif args.command == 'stats':
            Autosubmit.statistics(args.expid, args.output)
        elif args.command == 'clean':
            Autosubmit.clean(args.expid, args.project, args.plot, args.stats)
        elif args.command == 'recovery':
            Autosubmit.recovery(args.expid, args.save, args.get)
        elif args.command == 'check':
            Autosubmit.check(args.expid)
        elif args.command == 'create':
            Autosubmit.create(args.expid, args.noplot)
        elif args.command == 'configure':
            Autosubmit.configure(args.databasepath, args.databasefilename, args.localrootpath, args.queuesconfpath,
                                 args.jobsconfpath, args.user, args.local)
        elif args.command == 'install':
            Autosubmit.install()
        elif args.command == 'change_pkl':
            Autosubmit.change_pkl(args.expid, args.save, args.status_final, args.list, args.filter,
                                  args.filter_chunks, args.filter_status, args.filter_section)
        elif args.command == 'test':
            Autosubmit.test(args.expid, args.chunks, args.member, args.stardate, args.HPC, args.branch)
        elif args.command == 'refresh':
            Autosubmit.refresh(args.expid)

    @staticmethod
    def _delete_expid(expid_delete):
        """
        Removes an experiment from path and database

        :type expid_delete: str
        :param expid_delete: identifier of the experiment to delete
        """
        Log.info("Removing experiment directory...")
        try:
            shutil.rmtree(BasicConfig.LOCAL_ROOT_DIR + "/" + expid_delete)
        except OSError:
            pass
        Log.info("Deleting experiment from database...")
        ret = delete_experiment(expid_delete)
        if ret:
            Log.result("Experiment {0} deleted".format(expid_delete))
        return ret

    @staticmethod
    def expid(hpc, description, copy_id='', dummy=False):
        """
        Creates a new experiment for given HPC

        :type hpc: str
        :type description: str
        :type copy_id: str
        :type dummy: bool
        :param hpc: name of the main HPC for the experiment
        :param description: short experiment's description.
        :param copy_id: experiment identifier of experiment to copy
        :param dummy: if true, writes a default dummy configuration for testing
        :return: experiment identifier. If method fails, returns ''.
        :rtype: str
        """
        BasicConfig.read()

        log_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, 'expid.log'.format(os.getuid()))
        try:
            Log.set_file(log_path)
        except IOError as e:
            Log.error("Can not create log file in path {0}: {1}".format(log_path, e.message))
        exp_id = None
        if description is None:
            Log.error("Missing experiment description.")
            return ''
        if hpc is None:
            Log.error("Missing HPC.")
            return ''
        if not copy_id:
            exp_id = new_experiment(hpc, description)
            try:
                os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id)

                os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + '/conf')
                Log.info("Copying config files...")
                # autosubmit config and experiment copyed from AS.
                files = resource_listdir('config', 'files')
                for filename in files:
                    if resource_exists('config', 'files/' + filename):
                        index = filename.index('.')
                        new_filename = filename[:index] + "_" + exp_id + filename[index:]

                        if filename == 'queues.conf' and BasicConfig.DEFAULT_QUEUES_CONF != '':
                            content = file(os.path.join(BasicConfig.DEFAULT_QUEUES_CONF, filename)).read()
                        elif filename == 'jobs.conf' and BasicConfig.DEFAULT_JOBS_CONF != '':
                            content = file(os.path.join(BasicConfig.DEFAULT_JOBS_CONF, filename)).read()
                        else:
                            content = resource_string('config', 'files/' + filename)

                        Log.debug(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/conf/" + new_filename)
                        file(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/conf/" + new_filename, 'w').write(content)
                Autosubmit._prepare_conf_files(exp_id, hpc, Autosubmit.autosubmit_version, dummy)
            except (OSError, IOError) as e:
                Log.error("Can not create experiment: {0}\nCleaning...".format(e.message))
                Autosubmit._delete_expid(exp_id)
                return ''
        else:
            try:
                if os.path.exists(BasicConfig.LOCAL_ROOT_DIR + "/" + copy_id):
                    exp_id = copy_experiment(copy_id, hpc, description)
                    os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id)
                    os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + '/conf')
                    Log.info("Copying previous experiment config directories")
                    files = os.listdir(BasicConfig.LOCAL_ROOT_DIR + "/" + copy_id + "/conf")
                    for filename in files:
                        if os.path.isfile(BasicConfig.LOCAL_ROOT_DIR + "/" + copy_id + "/conf/" + filename):
                            new_filename = filename.replace(copy_id, exp_id)
                            content = file(BasicConfig.LOCAL_ROOT_DIR + "/" + copy_id + "/conf/" + filename, 'r').read()
                            file(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/conf/" + new_filename,
                                 'w').write(content)
                    Autosubmit._prepare_conf_files(exp_id, hpc, Autosubmit.autosubmit_version, dummy)
                else:
                    Log.critical("The previous experiment directory does not exist")
                    sys.exit(1)
            except (OSError, IOError) as e:
                Log.error("Can not create experiment: {0}\nCleaning...".format(e))
                Autosubmit._delete_expid(exp_id)
                return ''

        Log.debug("Creating temporal directory...")
        os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/" + "tmp")

        Log.debug("Creating pkl directory...")
        os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/" + "pkl")

        Log.debug("Creating plot directory...")
        os.mkdir(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/" + "plot")
        os.chmod(BasicConfig.LOCAL_ROOT_DIR + "/" + exp_id + "/" + "plot", 0o775)
        Log.result("Experiment registered successfully")
        Log.user_warning("Remember to MODIFY the config files!")
        return exp_id

    @staticmethod
    def delete(expid, force):
        """
        Deletes and experiment from database and experiment's folder

        :type force: bool
        :type expid: str
        :param expid: identifier of the experiment to delete
        :param force: if True, does not ask for confrmation

        :returns: True if succesful, False if not
        :rtype: bool
        """
        if os.path.exists(BasicConfig.LOCAL_ROOT_DIR + "/" + expid):
            if force or Autosubmit._user_yes_no_query("Do you want to delete " + expid + " ?"):
                return Autosubmit._delete_expid(expid)
            else:
                Log.info("Quitting...")
                return False
        else:
            Log.error("The experiment does not exist")
            return True

    @staticmethod
    def run_experiment(expid):
        """
        Runs and experiment (submitting all the jobs properly and repeating its execution in case of failure).

        :type expid: str
        :param expid: identifier of experiment to be run
        :return: True if run to the end, False otherwise
        :rtype: bool
        """
        if expid is None:
            Log.critical("Missing expid.")
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                  'run.log'))
        os.system('clear')

        as_conf = AutosubmitConfig(expid)
        if not as_conf.check_conf_files():
            Log.critical('Can not run with invalid configuration')
            return False

        project_type = as_conf.get_project_type()
        if project_type != "none":
            # Check proj configuration
            as_conf.check_proj()

        expid = as_conf.get_expid()
        hpcarch = as_conf.get_platform()
        max_jobs = as_conf.get_total_jobs()
        max_waiting_jobs = as_conf.get_max_waiting_jobs()
        safetysleeptime = as_conf.get_safetysleeptime()
        retrials = as_conf.get_retrials()

        queues = as_conf.read_queues_conf()

        Log.debug("The Experiment name is: {0}", expid)
        Log.debug("Total jobs to submit: {0}", max_jobs)
        Log.debug("Maximum waiting jobs in queues: {0}", max_waiting_jobs)
        Log.debug("Sleep: {0}", safetysleeptime)
        Log.debug("Retrials: {0}", retrials)
        Log.info("Starting job submission...")

        # for queue in queues:
        #     signal.signal(signal.SIGQUIT, queues[queue].smart_stop)
        #     signal.signal(signal.SIGINT, queues[queue].normal_stop)

        # if rerun == 'false':
        filename = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + '/pkl/job_list_' + expid + '.pkl'
        # else:
        #     filename = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + '/pkl/rerun_job_list_' + expid + '.pkl'
        Log.debug(filename)

        # the experiment should be loaded as well
        if os.path.exists(filename):
            joblist = cPickle.load(file(filename, 'rw'))
            Log.debug("Starting from joblist pickled in {0}", filename)
        else:
            Log.error("The necessary pickle file {0} does not exist.", filename)
            sys.exit()

        Log.debug("Length of joblist: {0}", len(joblist))

        # Load parameters
        Log.debug("Loading parameters...")
        parameters = as_conf.load_parameters()
        Log.debug("Updating parameters...")
        joblist.update_parameters(parameters)
        # check the job list script creation
        Log.debug("Checking experiment templates...")

        queues_to_test = set()
        for job in joblist.get_job_list():
            if job.queue_name is None:
                job.queue_name = hpcarch
            job.set_queue(queues[job.queue_name])
            queues_to_test.add(queues[job.queue_name])

        if joblist.check_scripts(as_conf):
            Log.result("Experiment templates check PASSED!")
        else:
            Log.warning("Experiment templates check FAILED!")

        # check the availability of the Queues
        for queue in queues_to_test:
            queue.connect()
            queue.check_remote_log_dir()

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
            Log.debug("Sleep: {0}", safetysleeptime)
            retrials = as_conf.get_retrials()
            Log.debug("Number of retrials: {0}", retrials)

            # read FAIL_RETRIAL number if, blank at creation time put a given number
            # check availability of machine, if not next iteration after sleep time
            # check availability of jobs, if no new jobs submited and no jobs available, then stop

            # ??? why
            joblist.save()

            Log.info("Active jobs in queues:\t{0}", active)
            Log.info("Waiting jobs in queues:\t{0}", waiting)

            if available == 0:
                Log.debug("There's no room for more jobs...")
            else:
                Log.debug("We can safely submit {0} jobs...", available)

            ######################################
            # AUTOSUBMIT - ALREADY SUBMITTED JOBS
            ######################################
            # get the list of jobs currently in the Queue
            jobinqueue = joblist.get_in_queue()
            Log.info("Number of jobs in queue: {0}", str(len(jobinqueue)))

            for job in jobinqueue:

                job.print_job()
                Log.debug("Number of jobs in queue: {0}", str(len(jobinqueue)))
                # Check queue availability
                job_queue = job.get_queue()
                queueavail = job_queue.check_host()
                if not queueavail:
                    Log.debug("There is no queue available")
                else:
                    status = job_queue.check_job(job.id)
                    if status == Status.COMPLETED:
                        Log.debug("This job seems to have completed...checking")
                        job_queue.get_completed_files(job.name)
                        job.check_completion()
                    else:
                        job.status = status
                    if job.status is Status.QUEUING:
                        Log.info("Job {0} is QUEUING", job.name)
                    elif job.status is Status.RUNNING:
                        Log.info("Job {0} is RUNNING", job.name)
                    elif job.status is Status.COMPLETED:
                        Log.result("Job {0} is COMPLETED", job.name)
                    elif job.status is Status.FAILED:
                        Log.user_warning("Job {0} is FAILED", job.name)
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
                Log.debug("Number of jobs ready: {0}", len(jobsavail))
                Log.debug("Number of jobs available in queue: {0}", available)
            elif min(available, len(jobsavail)) > 0 and len(jobinqueue) <= max_jobs:
                Log.info("\nStarting to submit {0} job(s)", min(available, len(jobsavail)))
                # should sort the jobsavail by priority Clean->post->sim>ini
                # s = sorted(jobsavail, key=lambda k:k.name.split('_')[1][:6])
                # probably useless to sort by year before sorting by type
                s = sorted(jobsavail, key=lambda k: k.long_name.split('_')[1][:6])

                list_of_jobs_avail = sorted(s, key=lambda k: k.priority, reverse=True)

                for job in list_of_jobs_avail[0:min(available, len(jobsavail), max_jobs - len(jobinqueue))]:
                    Log.debug(job.name)
                    scriptname = job.create_script(as_conf)
                    Log.debug(scriptname)

                    job_queue = job.get_queue()
                    queueavail = job_queue.check_host()
                    if not queueavail:
                        Log.warning("Queue {0} is not available".format(job_queue.name))
                    else:
                        job_queue.send_script(scriptname)
                        job.id = job_queue.submit_job(scriptname)
                        if job.id is None:
                            continue
                        # set status to "submitted"
                        job.status = Status.SUBMITTED
                        Log.info("{0} submitted\n", job.name)

            time.sleep(safetysleeptime)

        Log.info("No more jobs to run.")
        if len(joblist.get_failed()) > 0:
            Log.info("Some jobs have failed and reached maximun retrials")
            return False
        else:
            Log.result("Run successful")
            return True

    @staticmethod
    def monitor(expid, file_format):
        """
        Plots workflow graph for a given experiment with status of each job coded by node color.
        Plot is created in experiment's plot folder with name <expid>_<date>_<time>.<file_format>

        :type file_format: str
        :type expid: str
        :param expid: identifier of the experiment to plot
        :param file_format: plot's file format. It can be pdf, png or ps
        """
        root_name = 'job_list'
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR, 'monitor.log'))
        filename = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + '/pkl/' + root_name + '_' + expid + '.pkl'
        Log.info("Getting job list...")
        Log.debug("JobList: {0}".format(filename))
        jobs = cPickle.load(file(filename, 'r'))
        if not isinstance(jobs, type([])):
            jobs = jobs.get_job_list()

        Log.info("Plotting...")
        monitor_exp = Monitor()
        monitor_exp.generate_output(expid, jobs, file_format)
        Log.result("Plot ready")

    @staticmethod
    def statistics(expid, file_format):
        """
        Plots statistics graph for a given experiment.
        Plot is created in experiment's plot folder with name <expid>_<date>_<time>.<file_format>

        :type file_format: str
        :type expid: str
        :param expid: identifier of the experiment to plot
        :param file_format: plot's file format. It can be pdf, png or ps
        """
        root_name = 'job_list'
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
            monitor_exp.generate_output_stats(expid, jobs.get_job_list(), file_format)
            Log.result("Stats plot ready")
        else:
            Log.info("There are no COMPLETED jobs...")

    @staticmethod
    def clean(expid, project, plot, stats):
        """
        Clean experiment's directory to save storage space.
        It removes project directory and outdated plots or stats.

        :type plot: bool
        :type project: bool
        :type expid: str
        :type stats: bool
        :param expid: identifier of experiment to clean
        :param project: set True to delete project directory
        :param plot: set True to delete outdated plots
        :param stats: set True to delete outdated stats
        """
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                  'finalise_exp.log'))
        if project:
            autosubmit_config = AutosubmitConfig(expid)
            if not autosubmit_config.check_conf_files():
                Log.critical('Can not clean project with invalid configuration')
                return False

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
            Log.info("Cleaning plots...")
            monitor_autosubmit = Monitor()
            monitor_autosubmit.clean_plot(expid)
        if stats:
            Log.info("Cleaning stats directory...")
            monitor_autosubmit = Monitor()
            monitor_autosubmit.clean_stats(expid)

    @staticmethod
    def recovery(expid, save, get):
        """
        TODO

        :param expid: identifier of the experiment to recover
        :type expid: str
        :param save: If true, recovery saves changes to joblist
        :type save: bool
        :param get: if True, it tries to get completed files for active jobs. If file is found, it sets state to
                    COMPLETED. If not, it sets state to READY and fail count to 0, unless previous state was SUSPENDED
        :type get: bool
        """
        root_name = 'job_list'
        BasicConfig.read()

        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                  'recovery.log'))

        Log.info('Recovering experiment {0}'.format(expid))
        job_list = cPickle.load(file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, 'pkl',
                                                  root_name + "_" + expid + ".pkl"), 'r'))

        as_conf = AutosubmitConfig(expid)
        if not as_conf.check_conf_files():
            Log.critical('Can not recover with invalid configuration')
            return False

        hpcarch = as_conf.get_platform()

        if get:
            queues = as_conf.read_queues_conf()

            for job in job_list.get_active():
                if job.queue_name is None:
                    job.queue_name = hpcarch
                job.set_queue(queues[job.queue_name])

                if job.get_queue().get_completed_files(job.name):
                    job.status = Status.COMPLETED
                    Log.info("CHANGED job '{0}' status to COMPLETED".format(job.name))
                elif job.status != Status.SUSPENDED:
                    job.status = Status.READY
                    job.set_fail_count(0)
                    Log.info("CHANGED job '{0}' status to READY".format(job.name))

            sys.setrecursionlimit(50000)
            job_list.update_list()
            cPickle.dump(job_list, file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl",
                                                     root_name + "_" + expid + ".pkl", 'w')))

        if save:
            job_list.update_from_file()
        else:
            job_list.update_from_file(False)

        if save:
            sys.setrecursionlimit(50000)
            cPickle.dump(job_list, file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl",
                                                     root_name + "_" + expid + ".pkl", 'w')))
        Log.result("Recovery finalized")
        monitor_exp = Monitor()
        monitor_exp.generate_output(expid, job_list.get_job_list())

    @staticmethod
    def check(expid):
        """
        Checks experiment configuration and warns about any detected error or inconsistency.

        :param expid: experiment identifier:
        :type expid: str
        """
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR, 'check_exp.log'))
        as_conf = AutosubmitConfig(expid)
        as_conf.check_conf_files()
        project_type = as_conf.get_project_type()
        if project_type != "none":
            as_conf.check_proj()

        # print "Checking experiment configuration..."
        # if as_conf.check_parameters():
        #     print "Experiment configuration check PASSED!"
        # else:
        #     print "Experiment configuration check FAILED!"
        #     print "WARNING: running after FAILED experiment configuration check is at your own risk!!!"

        # Log.info("Checking experiment templates...")
        # if Autosubmit._check_templates(as_conf):
        #     Log.result("Experiment templates check PASSED!")
        # else:
        #     Log.critical("Experiment templates check FAILED!")
        #     Log.warning("Running after FAILED experiment templates check is at your own risk!!!")

    @staticmethod
    def configure(database_path, database_filename, local_root_path, queues_conf_path, jobs_conf_path,  user, local):
        """
        Configure several paths for autosubmit: database, local root and others. Can be configured at system,
        user or local levels. Local level configuration precedes user level and user level precedes system
        configuration.

        :param database_path: path to autosubmit database
        :type database_path: str
        :param database_path: path to autosubmit database
        :type database_path: str
        :param local_root_path: path to autosubmit's experiments' directory
        :type local_root_path: str
        :param queues_conf_path: path to queues conf file to be used as model for new experiments
        :type queues_conf_path: str
        :param jobs_conf_path: path to jobs conf file to be used as model for new experiments
        :type jobs_conf_path: str
        :param user: True if this configuration has to be stored by user
        :type user: bool
        :param local: True if this configuration has to be stored in the local path
        :type local: bool
        """
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

        if queues_conf_path is not None:
            queues_conf_path = queues_conf_path.replace('~', home_path)
            if not os.path.exists(queues_conf_path):
                Log.error("queues.conf path does not exist.")
                exit(1)
        if jobs_conf_path is not None:
            jobs_conf_path = jobs_conf_path.replace('~', home_path)
            if not os.path.exists(jobs_conf_path):
                Log.error("jobs.conf path does not exist.")
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
            if database_filename is not None:
                parser.set('database', 'filename', database_filename)
            parser.add_section('local')
            parser.set('local', 'path', local_root_path)
            if jobs_conf_path is not None or queues_conf_path is not None:
                parser.add_section('conf')
                if jobs_conf_path is not None:
                    parser.set('conf', 'jobs', jobs_conf_path)
                if queues_conf_path is not None:
                    parser.set('conf', 'queues', queues_conf_path)

            parser.write(config_file)
            config_file.close()
            Log.result("Configuration file written successfully")
        except (IOError, OSError) as e:
            Log.critical("Can not write config file: {0}".format(e.message))

    @staticmethod
    def install():
        """
        Creates a new database instance for autosubmit at the configured path
        """
        BasicConfig.read()
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
    def refresh(expid):
        """
        Refresh project folder for given experiment

        :param expid: experiment identifier
        :type expid: str
        """
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                  'refresh.log'))
        as_conf = AutosubmitConfig(expid)
        if not as_conf.check_conf_files():
            Log.critical('Can not copy with invalid configuration')
            return False
        project_type = as_conf.get_project_type()
        if Autosubmit._copy_code(as_conf, expid, project_type, True):
            Log.result("Project folder updated")

    @staticmethod
    def create(expid, noplot):
        """
        Creates job list for given experiment. Configuration files must be valid before realizaing this process.

        :param expid: experiment identifier
        :type expid: str
        :param noplot: if True, method omits final ploting of joblist. Only needed on large experiments when plotting
                       time can be much larger than creation time.
        :type noplot: bool
        :return: True if succesful, False if not
        :rtype: bool
        """
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                  'create_exp.log'))
        as_conf = AutosubmitConfig(expid)
        if not as_conf.check_conf_files():
            Log.critical('Can not create with invalid configuration')
            return False

        project_type = as_conf.get_project_type()

        if not Autosubmit._copy_code(as_conf, expid, project_type, False):
            return False

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
        else:
            job_list.remove_rerun_only_jobs()

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
    def _copy_code(as_conf, expid, project_type, force):
        """
        Method to copy code from experiment repository to project directory.

        :param as_conf: experiment configuration class
        :type as_conf: AutosubmitConfig
        :param expid: experiment identifier
        :type expid: str
        :param project_type: project type (git, svn, local)
        :type project_type: str
        :param force: if True, overwrites current data
        :return: True if succesful, False if not
        :rtype: bool
        """
        if project_type == "git":
            git_project_origin = as_conf.get_git_project_origin()
            git_project_branch = as_conf.get_git_project_branch()
            project_path = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/" + BasicConfig.LOCAL_PROJ_DIR
            if os.path.exists(project_path):
                Log.info("Using project folder: {0}", project_path)
                if not force:
                    Log.debug("The project folder exists. SKIPPING...")
                    return True
                else:
                    shutil.rmtree(project_path)
            os.mkdir(project_path)
            Log.debug("The project folder {0} has been created.", project_path)

            Log.info("Cloning {0} into {1}", git_project_branch + " " + git_project_origin, project_path)
            (status, output) = getstatusoutput("cd " + project_path + "; git clone --recursive -b "
                                               + git_project_branch + " " + git_project_origin)
            if status:
                Log.error("Can not clone {0} into {1}", git_project_branch + " " + git_project_origin, project_path)
                shutil.rmtree(project_path)
                return False

            Log.debug("{0}", output)

        elif project_type == "svn":
            svn_project_url = as_conf.get_svn_project_url()
            svn_project_revision = as_conf.get_svn_project_revision()
            project_path = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/" + BasicConfig.LOCAL_PROJ_DIR
            if os.path.exists(project_path):
                Log.info("Using project folder: {0}", project_path)
                if not force:
                    Log.debug("The project folder exists. SKIPPING...")
                    return True
            else:
                Log.debug("The project folder {0} has been created.", project_path)
            shutil.rmtree(project_path)
            Log.info("Checking out revision {0} into {1}", svn_project_revision + " " + svn_project_url, project_path)
            (status, output) = getstatusoutput("cd " + project_path + "; svn checkout -r " + svn_project_revision +
                                               " " + svn_project_url)
            if status:
                Log.error("Can not check out revision {0} into {1}", svn_project_revision + " " + svn_project_url,
                          project_path)
                shutil.rmtree(project_path)
                return False
            Log.debug("{0}" % output)

        elif project_type == "local":
            local_project_path = as_conf.get_local_project_path()
            project_path = BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/" + BasicConfig.LOCAL_PROJ_DIR
            if os.path.exists(project_path):
                Log.info("Using project folder: {0}", project_path)
                if not force:
                    Log.debug("The project folder exists. SKIPPING...")
                    return True
                else:
                    shutil.rmtree(project_path)
            os.mkdir(project_path)
            Log.debug("The project folder {0} has been created.", project_path)

            Log.info("Copying {0} into {1}", local_project_path, project_path)
            (status, output) = getstatusoutput("cp -R " + local_project_path + " " + project_path)
            if status:
                Log.error("Can not copy {0} into {1}. Exiting...", local_project_path, project_path)
                shutil.rmtree(project_path)
                return False
            Log.debug("{0}", output)
        return True

    @staticmethod
    def change_pkl(expid, save, final, lst, flt,
                   filter_chunks, filter_status, filter_section):
        """
        TODO

        :param expid: experiment identifier
        :type expid: str
        :param save:
        :type save: bool
        :param final:
        :type final: str
        :param lst:
        :type lst: str
        :param flt:
        :type flt: bool
        :param filter_chunks:
        :type filter_chunks: str
        :param filter_status:
        :type filter_status: str
        :param filter_section:
        :type filter_section: str
        """
        root_name = 'job_list'
        BasicConfig.read()

        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                  'change_pkl.log'))
        Log.debug('Exp ID: {0}', expid)
        job_list = cPickle.load(file(BasicConfig.LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid +
                                     ".pkl", 'r'))

        final_status = Autosubmit._get_status(final)
        if flt:
            if filter_chunks:
                fc = filter_chunks
                Log.debug(fc)

                if fc == 'Any':
                    for job in job_list.get_job_list():
                        job.status = final_status
                        Log.info("CHANGED: job: " + job.name + " status to: " + final)
                else:
                    data = json.loads(Autosubmit._create_json(fc))
                    # change localsetup and remotesetup
                    # [...]
                    for date in data['sds']:
                        for member in date['ms']:
                            jobname_ini = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_ini"
                            job = job_list.get_job_by_name(jobname_ini)
                            job.status = final_status
                            Log.info("CHANGED: job: " + job.name + " status to: " + final)
                            # change also trans
                            jobname_trans = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_trans"
                            job = job_list.get_job_by_name(jobname_trans)
                            job.status = final_status
                            Log.info("CHANGED: job: " + job.name + " status to: " + final)
                            # [...]
                            for chunk in member['cs']:
                                jobname_sim = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(
                                    chunk) + "_sim"
                                jobname_post = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(
                                    chunk) + "_post"
                                jobname_clean = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(
                                    chunk) + "_clean"
                                job = job_list.get_job_by_name(jobname_sim)
                                job.status = final_status
                                Log.info("CHANGED: job: " + job.name + " status to: " + final)
                                job = job_list.get_job_by_name(jobname_post)
                                job.status = final_status
                                Log.info("CHANGED: job: " + job.name + " status to: " + final)
                                job = job_list.get_job_by_name(jobname_clean)
                                job.status = final_status
                                Log.info("CHANGED: job: " + job.name + " status to: " + final)

            if filter_status:
                Log.debug("Filtering jobs with status {0}", filter_status)
                if filter_status == 'Any':
                    for job in job_list.get_job_list():
                        job.status = final_status
                        Log.info("CHANGED: job: " + job.name + " status to: " + final)
                else:
                    fs = Autosubmit._get_status(filter_status)

                    for job in job_list.get_job_list():
                        if job.status == fs:
                            job.status = final_status
                            Log.info("CHANGED: job: " + job.name + " status to: " + final)

            if filter_section:
                ft = filter_section
                Log.debug(ft)

                if ft == 'Any':
                    for job in job_list.get_job_list():
                        job.status = final_status
                        Log.info("CHANGED: job: " + job.name + " status to: " + final)
                else:
                    for job in job_list.get_job_list():
                        if job.section == ft:
                            job.status = final_status
                            Log.info("CHANGED: job: " + job.name + " status to: " + final)

        if lst:
            jobs = lst.split()

            if jobs == 'Any':
                for job in job_list.get_job_list():
                    job.status = final_status
                    Log.info("CHANGED: job: " + job.name + " status to: " + final)
            else:
                for job in job_list.get_job_list():
                    if job.name in jobs:
                        job.status = final_status
                        Log.info("CHANGED: job: " + job.name + " status to: " + final)

        sys.setrecursionlimit(50000)

        if save:
            job_list.update_list()
            path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl", root_name + "_" + expid + ".pkl")
            cPickle.dump(job_list, file(path, 'w'))
            Log.info("Saving JobList: {0}", path)
        else:
            job_list.update_list(False)
            Log.warning("Changes NOT saved to the JobList!!!!:  use -s option to save")

        monitor_exp = Monitor()
        monitor_exp.generate_output(expid, job_list.get_job_list())

    @staticmethod
    def _user_yes_no_query(question):
        """
        Utility function to ask user a yes/no question

        :param question: question to ask
        :type question: str
        :return: True if answer is yes, False if it is no
        :rtype: bool
        """
        sys.stdout.write('{0} [y/n]\n'.format(question))
        while True:
            try:
                return strtobool(raw_input().lower())
            except ValueError:
                sys.stdout.write('Please respond with \'y\' or \'n\'.\n')

    @staticmethod
    def _prepare_conf_files(exp_id, hpc, autosubmit_version, dummy):
        """
        Changes default configuration files to match new experminet values

        :param exp_id: experiment identifier
        :type exp_id: str
        :param hpc: hpc to use
        :type hpc: str
        :param autosubmit_version: current autosubmit's version
        :type autosubmit_version: str
        :param dummy: if True, creates a dummy experiment adding some dafault values
        :type dummy: bool
        """
        as_conf = AutosubmitConfig(exp_id)
        as_conf.set_version(autosubmit_version)
        as_conf.set_expid(exp_id)
        as_conf.set_local_root()
        as_conf.set_platform(hpc)
        as_conf.set_safetysleeptime(10)

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
        """
        Convert job status from str to Status

        :param s: status string
        :type s: str
        :return: status instance
        :rtype: Status
        """
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
        """
        Function to get a list of members from json

        :param out: json member definition
        :type out: str
        :return: list of members
        :rtype: list
        """
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
        """
        Function to get a list of chunks from json

        :param out: json member definition
        :type out: str
        :return: list of chunks
        :rtype: list
        """
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
        """
        Function to parse rerun specification from json format

        :param text: text to parse
        :type text: list
        :return: parsed output
        """
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

    @staticmethod
    def test(expid, chunks, member=None, stardate=None, hpc=None, branch=None):
        """
        Method to conduct a test for a given experiment. It creates a new experiment for a given experiment qith a
        given number of chunks with a random start date and a random member to be run on a random HPC.


        :param expid: experiment identifier
        :type expid: str
        :param chunks: number of chunks to be run by the experiment
        :type chunks: int
        :param member: member to be used by the test. If None, it uses a random one from which are defined on
                       the experiment.
        :type member: str
        :param stardate: start date to be used by the test. If None, it uses a random one from which are defined on
                         the experiment.
        :type stardate: str
        :param hpc: HPC to be used by the test. If None, it uses a random one from which are defined on
                    the experiment.
        :type hpc: str
        :param branch: branch or revision to be used by the test. If None, it uses configured branch.
        :type branch: str
        :return: True if test was succesful, False otherwise
        :rtype: bool
        """
        testid = Autosubmit.expid('test', 'test experiment for {0}'.format(expid), expid, False)
        if testid == '':
            return False

        as_conf = AutosubmitConfig(testid)
        exp_parser = as_conf.get_parser(as_conf.experiment_file)

        content = file(as_conf.experiment_file).read()
        if hpc is None:
            queues_parser = as_conf.get_parser(as_conf.queues_file)
            test_queues = list()
            for section in queues_parser.sections():
                if AutosubmitConfig.get_option(queues_parser, section, 'TEST_SUITE', 'false').lower() == 'true':
                    test_queues.append(section)
            if len(test_queues) == 0:
                Log.critical('No test HPC defined')
                return False
            hpc = random.choice(test_queues)
        if member is None:
            member = random.choice(exp_parser.get('experiment', 'MEMBERS').split(' '))
        if stardate is None:
            stardate = random.choice(exp_parser.get('experiment', 'DATELIST').split(' '))
        # Experiment
        content = content.replace(re.search('DATELIST =.*', content).group(0),
                                  "DATELIST = " + stardate)
        content = content.replace(re.search('MEMBERS =.*', content).group(0),
                                  "MEMBERS = " + member)
        content = content.replace(re.search('NUMCHUNKS =.*', content).group(0),
                                  "NUMCHUNKS = " + chunks)
        content = content.replace(re.search('HPCARCH =.*', content).group(0),
                                  "HPCARCH = " + hpc)
        content = content.replace(re.search('EXPID =.*', content).group(0),
                                  "EXPID = " + testid)
        if branch is not None:
            content = content.replace(re.search('PROJECT_BRANCH =.*', content).group(0),
                                      "PROJECT_BRANCH = " + branch)
            content = content.replace(re.search('PROJECT_REVISION =.*', content).group(0),
                                      "PROJECT_REVISION = " + branch)

        file(as_conf.experiment_file, 'w').write(content)

        Autosubmit.create(testid, False)
        if not Autosubmit.run_experiment(testid):
            exit(1)
        Autosubmit.delete(testid, True)

