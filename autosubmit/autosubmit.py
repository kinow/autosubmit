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

from __future__ import print_function

"""
Main module for autosubmit. Only contains an interface class to all functionality implemented on autosubmit
"""

try:
    # noinspection PyCompatibility
    from configparser import SafeConfigParser
except ImportError:
    # noinspection PyCompatibility
    from ConfigParser import SafeConfigParser

import argparse
import subprocess
import json
import tarfile
import time
import pickle
import os
import sys
import shutil
import re
import random
import signal
import datetime
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
from database.db_common import get_autosubmit_version
from monitor.monitor import Monitor
from date.chunk_date_lib import date2str


# noinspection PyUnusedLocal
def signal_handler(signal_received, frame):
    Log.info('Autosubmit will interrupt at the next safe ocasion')
    Autosubmit.exit = True


class Autosubmit:
    """
    Interface class for autosubmit.
    """

    # Get the version number from the relevant file. If not, from autosubmit package
    scriptdir = os.path.abspath(os.path.dirname(__file__))

    if not os.path.exists(os.path.join(scriptdir, 'VERSION')):
        scriptdir = os.path.join(scriptdir, os.path.pardir)

    version_path = os.path.join(scriptdir, 'VERSION')
    readme_path = os.path.join(scriptdir, 'README')
    changes_path = os.path.join(scriptdir, 'CHANGES')
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
        try:
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
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument('-f', '--force', action='store_true', help='deletes experiment without confirmation')

            # Monitor
            subparser = subparsers.add_parser('monitor', description="plots specified experiment")
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument('-o', '--output', choices=('pdf', 'png', 'ps', 'svg'), default='pdf',
                                   help='chooses type of output for generated plot')

            # Stats
            subparser = subparsers.add_parser('stats', description="plots statistics for specified experiment")
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument('-o', '--output', choices=('pdf', 'png', 'ps', 'svg'), default='pdf',
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
            subparser.add_argument('-all', action="store_true", default=False,
                                   help='Get completed files to synchronize pkl')
            subparser.add_argument('-s', '--save', action="store_true", default=False, help='Save changes to disk')

            # Check
            subparser = subparsers.add_parser('check', description="check configuration for specified experiment")
            subparser.add_argument('expid', help='experiment identifier')

            # Create
            subparser = subparsers.add_parser('create', description="create specified experiment joblist")
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument('-np', '--noplot', action='store_true', default=False, help='omit plot')

            # Configure
            subparser = subparsers.add_parser('configure', description="configure database and path for autosubmit. It "
                                                                       "can be done at machine, user or local level "
                                                                       "(by default at machine level)")
            subparser.add_argument('-db', '--databasepath', default=None, help='path to database. If not supplied, '
                                                                               'it will prompt for it')
            subparser.add_argument('-dbf', '--databasefilename', default=None, help='database filename')
            subparser.add_argument('-lr', '--localrootpath', default=None, help='path to store experiments. If not '
                                                                                'supplied, it will prompt for it')
            subparser.add_argument('-pc', '--platformsconfpath', default=None,
                                   help='path to platforms.conf file to use by default. If not supplied, it will not'
                                   ' prompt for it')
            subparser.add_argument('-jc', '--jobsconfpath', default=None, help='path to jobs.conf file to use by '
                                                                               'default. If not supplied, it will not '
                                                                               'prompt for it')
            group = subparser.add_mutually_exclusive_group()
            group.add_argument('--all', action="store_true", help='configure for all users')
            group.add_argument('--local', action="store_true", help='configure only for using Autosubmit from '
                                                                    'this path')

            # Install
            subparsers.add_parser('install', description='install database for autosubmit on the configured folder')

            # Set stattus
            subparser = subparsers.add_parser('setstatus', description="sets job status for an experiment")
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument('-s', '--save', action="store_true", default=False, help='Save changes to disk')
            subparser.add_argument('-t', '--status_final',
                                   choices=('READY', 'COMPLETED', 'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN',
                                            'QUEUING', 'RUNNING'),
                                   required=True,
                                   help='Supply the target status')
            group = subparser.add_mutually_exclusive_group(required=True)
            group.add_argument('-fl', '--list', type=str,
                               help='Supply the list of job names to be changed. Default = "Any". '
                                    'LIST = "b037_20101101_fc3_21_sim b037_20111101_fc4_26_sim"')
            group.add_argument('-fc', '--filter_chunks', type=str,
                               help='Supply the list of chunks to change the status. Default = "Any". '
                                    'LIST = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]"')
            group.add_argument('-fs', '--filter_status', type=str,
                               choices=('Any', 'READY', 'COMPLETED', 'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN'),
                               help='Select the original status to filter the list of jobs')
            group.add_argument('-ft', '--filter_type', type=str,
                               help='Select the job type to filter the list of jobs')

            # Test
            subparser = subparsers.add_parser('test', description='test experiment')
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument('-c', '--chunks', required=True, help='chunks to run')
            subparser.add_argument('-m', '--member', help='member to run')
            subparser.add_argument('-s', '--stardate', help='stardate to run')
            subparser.add_argument('-H', '--HPC', help='HPC to run experiment on it')
            subparser.add_argument('-b', '--branch', help='branch of git to run (or revision from subversion)')

            # Refresh
            subparser = subparsers.add_parser('refresh', description='refresh project directory for an experiment')
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument('-mc', '--model_conf', default=False, action='store_true',
                                   help='overwrite model conf file')

            # Archive
            subparser = subparsers.add_parser('archive', description='archives an experiment')
            subparser.add_argument('expid', help='experiment identifier')

            # Unarchive
            subparser = subparsers.add_parser('unarchive', description='unarchives an experiment')
            subparser.add_argument('expid', help='experiment identifier')

            # Readme
            subparsers.add_parser('readme', description='show readme')

            # Changelog
            subparsers.add_parser('changelog', description='show changelog')

            args = parser.parse_args()

            Log.set_console_level(args.logconsole)
            Log.set_file_level(args.logfile)

            if args.command == 'run':
                return Autosubmit.run_experiment(args.expid)
            elif args.command == 'expid':
                return Autosubmit.expid(args.HPC, args.description, args.copy, args.dummy) != ''
            elif args.command == 'delete':
                return Autosubmit.delete(args.expid, args.force)
            elif args.command == 'monitor':
                return Autosubmit.monitor(args.expid, args.output)
            elif args.command == 'stats':
                return Autosubmit.statistics(args.expid, args.output)
            elif args.command == 'clean':
                return Autosubmit.clean(args.expid, args.project, args.plot, args.stats)
            elif args.command == 'recovery':
                return Autosubmit.recovery(args.expid, args.save, args.all)
            elif args.command == 'check':
                return Autosubmit.check(args.expid)
            elif args.command == 'create':
                return Autosubmit.create(args.expid, args.noplot)
            elif args.command == 'configure':
                return Autosubmit.configure(args.databasepath, args.databasefilename, args.localrootpath,
                                            args.platformsconfpath, args.jobsconfpath, args.all, args.local)
            elif args.command == 'install':
                return Autosubmit.install()
            elif args.command == 'setstatus':
                return Autosubmit.set_status(args.expid, args.save, args.status_final, args.list,
                                             args.filter_chunks, args.filter_status, args.filter_type)
            elif args.command == 'test':
                return Autosubmit.test(args.expid, args.chunks, args.member, args.stardate, args.HPC, args.branch)
            elif args.command == 'refresh':
                return Autosubmit.refresh(args.expid, args.model_conf)
            elif args.command == 'archive':
                return Autosubmit.archive(args.expid)
            elif args.command == 'unarchive':
                return Autosubmit.unarchive(args.expid)
            elif args.command == 'readme':
                if os.path.isfile(Autosubmit.readme_path):
                    with open(Autosubmit.readme_path) as f:
                        print(f.read())
                        return True
                return False
            elif args.command == 'changelog':
                if os.path.isfile(Autosubmit.changes_path):
                    with open(Autosubmit.changes_path) as f:
                        print(f.read())
                        return True
                return False
        except Exception as e:
            from traceback import format_exc
            Log.critical('Unhandled exception on Autosubmit: {0}\n{1}', e, format_exc(10))

            return False

    @staticmethod
    def _delete_expid(expid_delete):
        """
        Removes an experiment from path and database

        :type expid_delete: str
        :param expid_delete: identifier of the experiment to delete
        """
        if not os.path.exists(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid_delete)):
            Log.info("Experiment directory does not exist.")
        else:
            Log.info("Removing experiment directory...")
            try:
                shutil.rmtree(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid_delete))
            except OSError as e:
                Log.warning('Can not delete experiment folder: {0}', e)
                return False
        Log.info("Deleting experiment from database...")
        ret = delete_experiment(expid_delete)
        if ret:
            Log.result("Experiment {0} deleted".format(expid_delete))
        return ret

    @staticmethod
    def expid(hpc, description, copy_id='', dummy=False, test=False):
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
        :param test: if true, creates an experiment for testing
        :return: experiment identifier. If method fails, returns ''.
        :rtype: str
        """
        BasicConfig.read()

        log_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, 'ASlogs', 'expid.log'.format(os.getuid()))
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
            exp_id = new_experiment(description, Autosubmit.autosubmit_version)
            if exp_id == '':
                return ''
            try:
                os.mkdir(os.path.join(BasicConfig.LOCAL_ROOT_DIR, exp_id))

                os.mkdir(os.path.join(BasicConfig.LOCAL_ROOT_DIR, exp_id, 'conf'))
                Log.info("Copying config files...")
                # autosubmit config and experiment copyed from AS.
                files = resource_listdir('autosubmit.config', 'files')
                for filename in files:
                    if resource_exists('autosubmit.config', 'files/' + filename):
                        index = filename.index('.')
                        new_filename = filename[:index] + "_" + exp_id + filename[index:]

                        if filename == 'platforms.conf' and BasicConfig.DEFAULT_PLATFORMS_CONF != '':
                            content = open(os.path.join(BasicConfig.DEFAULT_PLATFORMS_CONF, filename)).read()
                        elif filename == 'jobs.conf' and BasicConfig.DEFAULT_JOBS_CONF != '':
                            content = open(os.path.join(BasicConfig.DEFAULT_JOBS_CONF, filename)).read()
                        else:
                            content = resource_string('autosubmit.config', 'files/' + filename)

                        conf_new_filename = os.path.join(BasicConfig.LOCAL_ROOT_DIR, exp_id, "conf", new_filename)
                        Log.debug(conf_new_filename)
                        open(conf_new_filename, 'w').write(content)
                Autosubmit._prepare_conf_files(exp_id, hpc, Autosubmit.autosubmit_version, dummy)
            except (OSError, IOError) as e:
                Log.error("Can not create experiment: {0}\nCleaning...".format(e))
                Autosubmit._delete_expid(exp_id)
                return ''
        else:
            try:
                if os.path.exists(os.path.join(BasicConfig.LOCAL_ROOT_DIR, copy_id)):
                    exp_id = copy_experiment(copy_id, description, Autosubmit.autosubmit_version, test)
                    if exp_id == '':
                        return ''
                    dir_exp_id = os.path.join(BasicConfig.LOCAL_ROOT_DIR, exp_id)
                    os.mkdir(dir_exp_id)
                    os.mkdir(dir_exp_id + '/conf')
                    Log.info("Copying previous experiment config directories")
                    conf_copy_id = os.path.join(BasicConfig.LOCAL_ROOT_DIR, copy_id, "conf")
                    files = os.listdir(conf_copy_id)
                    for filename in files:
                        if os.path.isfile(os.path.join(conf_copy_id, filename)):
                            new_filename = filename.replace(copy_id, exp_id)
                            content = open(os.path.join(conf_copy_id, filename), 'r').read()
                            open(os.path.join(dir_exp_id, "conf", new_filename), 'w').write(content)
                    Autosubmit._prepare_conf_files(exp_id, hpc, Autosubmit.autosubmit_version, dummy)
                else:
                    Log.critical("The previous experiment directory does not exist")
                    return ''
            except (OSError, IOError) as e:
                Log.error("Can not create experiment: {0}\nCleaning...".format(e))
                Autosubmit._delete_expid(exp_id)
                return ''

        Log.debug("Creating temporal directory...")
        exp_id_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, exp_id)
        os.mkdir(os.path.join(exp_id_path, "tmp"))

        Log.debug("Creating pkl directory...")
        os.mkdir(os.path.join(exp_id_path, "pkl"))

        Log.debug("Creating plot directory...")
        os.mkdir(os.path.join(exp_id_path, "plot"))
        os.chmod(os.path.join(exp_id_path, "plot"), 0o775)
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
        log_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, "ASlogs", 'delete.log'.format(os.getuid()))
        try:
            Log.set_file(log_path)
        except IOError as e:
            Log.error("Can not create log file in path {0}: {1}".format(log_path, e.message))

        if os.path.exists(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)):
            if force or Autosubmit._user_yes_no_query("Do you want to delete " + expid + " ?"):
                return Autosubmit._delete_expid(expid)
            else:
                Log.info("Quitting...")
                return False
        else:
            Log.error("The experiment does not exist")
            return True

    @staticmethod
    def _load_parameters(as_conf, joblist, platforms):
        # Load parameters
        Log.debug("Loading parameters...")
        parameters = as_conf.load_parameters()
        for platform_name in platforms:
            platform = platforms[platform_name]
            parameters['{0}_ARCH'.format(platform.name)] = platform.name
            parameters['{0}_HOST'.format(platform.name)] = platform.get_host()
            parameters['{0}_USER'.format(platform.name)] = platform.user
            parameters['{0}_PROJ'.format(platform.name)] = platform.project
            parameters['{0}_BUDG'.format(platform.name)] = platform.budget
            parameters['{0}_TYPE'.format(platform.name)] = platform.type
            parameters['{0}_VERSION'.format(platform.name)] = platform.version
            parameters['{0}_SCRATCH_DIR'.format(platform.name)] = platform.scratch
            parameters['{0}_ROOTDIR'.format(platform.name)] = platform.root_dir

        platform = platforms[as_conf.get_platform()]
        parameters['HPCARCH'] = platform.name
        parameters['HPCHOST'] = platform.get_host()
        parameters['HPCUSER'] = platform.user
        parameters['HPCPROJ'] = platform.project
        parameters['HPCBUDG'] = platform.budget
        parameters['HPCTYPE'] = platform.type
        parameters['HPCVERSION'] = platform.version
        parameters['SCRATCH_DIR'] = platform.scratch
        parameters['HPCROOTDIR'] = platform.root_dir
        Log.debug("Updating parameters...")
        joblist.update_parameters(parameters)

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

        Autosubmit.exit = False
        signal.signal(signal.SIGINT, signal_handler)

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

        safetysleeptime = as_conf.get_safetysleeptime()
        retrials = as_conf.get_retrials()

        platforms = as_conf.read_platforms_conf()
        if platforms is None:
            return False

        Log.debug("The Experiment name is: {0}", expid)
        Log.debug("Sleep: {0}", safetysleeptime)
        Log.debug("Retrials: {0}", retrials)
        Log.info("Starting job submission...")

        # for platforms in platforms:
        #     signal.signal(signal.SIGQUIT, platforms[platforms].smart_stop)
        #     signal.signal(signal.SIGINT, platforms[platforms].normal_stop)

        filename = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, 'pkl', 'job_list_' + expid + '.pkl')
        Log.debug(filename)

        # the experiment should be loaded as well
        if os.path.exists(filename):
            joblist = pickle.load(open(filename, 'rw'))
            Log.debug("Starting from joblist pickled in {0}", filename)
        else:
            Log.error("The necessary pickle file {0} does not exist.", filename)
            return False

        Log.debug("Length of joblist: {0}", len(joblist))

        Autosubmit._load_parameters(as_conf, joblist, platforms)

        # check the job list script creation
        Log.debug("Checking experiment templates...")

        platforms_to_test = set()
        for job in joblist.get_job_list():
            if job.platform_name is None:
                job.platform_name = hpcarch
            # noinspection PyTypeChecker
            job.set_platform(platforms[job.platform_name])
            # noinspection PyTypeChecker
            platforms_to_test.add(platforms[job.platform_name])

        joblist.check_scripts(as_conf)

        # check the availability of the Queues
        for platform in platforms_to_test:
            platform.connect()
            platform.check_remote_log_dir()

        #########################
        # AUTOSUBMIT - MAIN LOOP
        #########################
        # Main loop. Finishing when all jobs have been submitted
        while joblist.get_active():
            if Autosubmit.exit:
                Log.info('Interrupted by user.')
                return 0
            # reload parameters changes
            Log.debug("Reloading parameters...")
            as_conf.reload()
            Autosubmit._load_parameters(as_conf, joblist, platforms)

            # variables to be updated on the fly
            total_jobs = len(joblist.get_job_list())
            Log.info("\n\n{0} of {1} jobs remaining ({2})".format(total_jobs - len(joblist.get_completed()), total_jobs,
                                                                  strftime("%H:%M")))
            safetysleeptime = as_conf.get_safetysleeptime()
            Log.debug("Sleep: {0}", safetysleeptime)
            retrials = as_conf.get_retrials()
            Log.debug("Number of retrials: {0}", retrials)

            # Flag to write the pickle only if something has changed
            save_pkl = False

            ######################################
            # AUTOSUBMIT - ALREADY SUBMITTED JOBS
            ######################################
            for platform in platforms_to_test:

                jobinqueue = joblist.get_in_queue(platform)
                if len(jobinqueue) == 0:
                    continue

                Log.info("\nJobs in {0} queue: {1}", platform.name, str(len(jobinqueue)))

                if not platform.check_host():
                    Log.debug("{0} is not available", platform.name)
                    continue

                for job in jobinqueue:
                    job.print_job()
                    status = platform.check_job(job.id)
                    if job.status != status:
                        save_pkl = True
                    if status == Status.COMPLETED:
                        Log.debug("This job seems to have completed...checking")
                        platform.get_completed_files(job.name)
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
                    elif job.status is Status.UNKNOWN:
                        Log.debug("Job {0} in UNKNOWN status. Checking completed files", job.name)
                        platform.get_completed_files(job.name)
                        job.check_completion(Status.UNKNOWN)
                    elif job.status is Status.SUBMITTED:
                        # after checking the jobs , no job should have the status "submitted"
                        Log.warning('Job {0} in SUBMITTED status after checking.', job.name)

            ##############################
            # AUTOSUBMIT - JOBS TO SUBMIT
            ##############################
            # get the list of jobs READY
            joblist.update_list()
            for platform in platforms_to_test:

                jobsavail = joblist.get_ready(platform)
                if len(jobsavail) == 0:
                    continue

                Log.info("\nJobs ready for {1}: {0}", len(jobsavail), platform.name)

                if not platform.check_host():
                    Log.debug("{0} is not available", platform.name)
                    continue

                max_jobs = platform.total_jobs
                max_waiting_jobs = platform.max_waiting_jobs
                waiting = len(joblist.get_submitted(platform) + joblist.get_queuing(platform))
                jobinqueue = joblist.get_in_queue(platform)
                available = min(max_waiting_jobs - waiting, max_jobs - len(jobinqueue))

                if min(available, len(jobsavail)) == 0:
                    Log.debug("Number of jobs ready: {0}", len(jobsavail))
                    Log.debug("Number of jobs available: {0}", available)
                elif min(available, len(jobsavail)) > 0:
                    Log.info("Jobs to submit: {0}", min(available, len(jobsavail)))
                    # should sort the jobsavail by priority Clean->post->sim>ini
                    # s = sorted(jobsavail, key=lambda k:k.name.split('_')[1][:6])
                    # probably useless to sort by year before sor1ting by type
                    s = sorted(jobsavail, key=lambda k: k.long_name.split('_')[1][:6])

                    list_of_jobs_avail = sorted(s, key=lambda k: k.priority, reverse=True)

                    for job in list_of_jobs_avail[0:min(available, len(jobsavail), max_jobs - len(jobinqueue))]:
                        Log.debug(job.name)
                        job.update_parameters(as_conf, joblist.parameters)
                        scriptname = job.create_script(as_conf)
                        Log.debug(scriptname)

                        platform.send_script(scriptname)
                        job.id = platform.submit_job(scriptname)
                        if job.id is None:
                            continue
                        # set status to "submitted"
                        job.status = Status.SUBMITTED
                        save_pkl = True
                        Log.info("{0} submitted", job.name)

            if save_pkl:
                joblist.save()
            if Autosubmit.exit:
                Log.info('Interrupted by user.')
                return 0
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
        filename = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, 'pkl', root_name + '_' + expid + '.pkl')
        Log.info("Getting job list...")
        Log.debug("JobList: {0}".format(filename))
        jobs = pickle.load(open(filename, 'r'))
        if not isinstance(jobs, type([])):
            jobs = jobs.get_job_list()

        monitor_exp = Monitor()
        monitor_exp.generate_output(expid, jobs, file_format)
        return True

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
        filename = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, 'pkl', root_name + '_' + expid + '.pkl')
        jobs = pickle.load(open(filename, 'r'))
        # if not isinstance(jobs, type([])):
        #     jobs = [job for job in jobs.get_finished() if job.type == Type.SIMULATION]

        if len(jobs.get_job_list()) > 0:
            Log.info("Plotting stats...")
            monitor_exp = Monitor()
            monitor_exp.generate_output_stats(expid, jobs.get_job_list(), file_format)
            Log.result("Stats plot ready")
        else:
            Log.info("There are no COMPLETED jobs...")
        return True

    @staticmethod
    def clean(expid, project, plot, stats, create_log_file=True):
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
        if create_log_file:
            Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                      'clean_exp.log'))
        if project:
            autosubmit_config = AutosubmitConfig(expid)
            if not autosubmit_config.check_conf_files():
                Log.critical('Can not clean project with invalid configuration')
                return False

            project_type = autosubmit_config.get_project_type()
            if project_type == "git":
                autosubmit_config.check_proj()
                Log.info("Registering commit SHA...")
                autosubmit_config.set_git_project_commit(autosubmit_config)
                autosubmit_git = AutosubmitGit(expid[0])
                Log.info("Cleaning GIT directory...")
                if not autosubmit_git.clean_git(autosubmit_config):
                    return False
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
        return True

    @staticmethod
    def recovery(expid, save, all_jobs):
        """
        TODO

        :param expid: identifier of the experiment to recover
        :type expid: str
        :param save: If true, recovery saves changes to joblist
        :type save: bool
        :param all_jobs: if True, it tries to get completed files for all jobs, not only active.
        :type all_jobs: bool
        """
        root_name = 'job_list'
        BasicConfig.read()

        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_TMP_DIR,
                                  'recovery.log'))

        Log.info('Recovering experiment {0}'.format(expid))

        path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl", root_name + "_" + expid + ".pkl")
        job_list = pickle.load(open(path, 'r'))

        as_conf = AutosubmitConfig(expid)
        if not as_conf.check_conf_files():
            Log.critical('Can not recover with invalid configuration')
            return False

        hpcarch = as_conf.get_platform()

        platforms = as_conf.read_platforms_conf()
        if platforms is None:
            return False
        for platform in platforms:
            platforms[platform].connect()
        if all_jobs:
            jobs_to_recover = job_list.get_job_list()
        else:
            jobs_to_recover = job_list.get_active()

        Log.info("Looking for COMPLETED files")
        for job in jobs_to_recover:
            if job.platform_name is None:
                job.platform_name = hpcarch
            # noinspection PyTypeChecker
            job.set_platform(platforms[job.platform_name])

            if job.get_platform().get_completed_files(job.name, 0, True):
                job.status = Status.COMPLETED
                Log.info("CHANGED job '{0}' status to COMPLETED".format(job.name))
            elif job.status != Status.SUSPENDED:
                job.status = Status.WAITING
                job.fail_count = 0
                Log.info("CHANGED job '{0}' status to WAITING".format(job.name))

        Log.info("Updating joblist")
        sys.setrecursionlimit(50000)
        job_list.update_list(False)
        job_list.update_from_file(False)

        if save:
            job_list.save()
        else:
            Log.warning('Changes NOT saved to the jobList. Use -s option to save')

        Log.result("Recovery finalized")
        monitor_exp = Monitor()
        monitor_exp.generate_output(expid, job_list.get_job_list())
        return True

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
        if not as_conf.check_conf_files():
            return False
        project_type = as_conf.get_project_type()
        if project_type != "none":
            if not as_conf.check_proj():
                return False

        platforms = as_conf.read_platforms_conf()
        if platforms is None:
            return False

        filename = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, 'pkl', 'job_list_' + expid + '.pkl')
        # the experiment should be loaded as well
        if os.path.exists(filename):
            joblist = pickle.load(open(filename, 'rw'))
            Log.debug("Starting from joblist pickled in {0}", filename)
        else:
            Log.error("The necessary pickle file {0} does not exist. Can not check templates!", filename)
            return False

        Autosubmit._load_parameters(as_conf, joblist, platforms)

        hpcarch = as_conf.get_platform()
        for job in joblist.get_job_list():
            if job.platform_name is None:
                job.platform_name = hpcarch
            # noinspection PyTypeChecker
            job.set_platform(platforms[job.platform_name])
            job.update_parameters(as_conf, joblist.parameters)

        return joblist.check_scripts(as_conf)

    @staticmethod
    def configure(database_path, database_filename, local_root_path, platforms_conf_path, jobs_conf_path,
                  machine, local):
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
        :param platforms_conf_path: path to platforms conf file to be used as model for new experiments
        :type platforms_conf_path: str
        :param jobs_conf_path: path to jobs conf file to be used as model for new experiments
        :type jobs_conf_path: str
        :param machine: True if this configuration has to be stored for all the machine users
        :type machine: bool
        :param local: True if this configuration has to be stored in the local path
        :type local: bool
        """
        home_path = os.path.expanduser('~')
        while database_path is None:
            database_path = input("Introduce Database path: ")
        database_path = database_path.replace('~', home_path)
        if not os.path.exists(database_path):
            Log.error("Database path does not exist.")
            return False

        while local_root_path is None:
            local_root_path = input("Introduce Local Root path: ")
        local_root_path = local_root_path.replace('~', home_path)
        if not os.path.exists(local_root_path):
            Log.error("Local Root path does not exist.")
            return False

        if platforms_conf_path is not None:
            platforms_conf_path = platforms_conf_path.replace('~', home_path)
            if not os.path.exists(platforms_conf_path):
                Log.error("platforms.conf path does not exist.")
                return False
        if jobs_conf_path is not None:
            jobs_conf_path = jobs_conf_path.replace('~', home_path)
            if not os.path.exists(jobs_conf_path):
                Log.error("jobs.conf path does not exist.")
                return False

        if machine:
            path = '/etc'
        elif local:
            path = '.'
        else:
            path = home_path
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
            if jobs_conf_path is not None or platforms_conf_path is not None:
                parser.add_section('conf')
                if jobs_conf_path is not None:
                    parser.set('conf', 'jobs', jobs_conf_path)
                if platforms_conf_path is not None:
                    parser.set('conf', 'platforms', platforms_conf_path)

            parser.write(config_file)
            config_file.close()
            Log.result("Configuration file written successfully")
        except (IOError, OSError) as e:
            Log.critical("Can not write config file: {0}".format(e.message))
            return False
        return True

    @staticmethod
    def install():
        """
        Creates a new database instance for autosubmit at the configured path

        """
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, "ASlogs", 'install.log'))
        if not os.path.exists(BasicConfig.DB_PATH):
            Log.info("Creating autosubmit database...")
            qry = resource_string('autosubmit.database', 'data/autosubmit.sql')
            if not create_db(qry):
                Log.critical("Can not write database file")
                return False
            Log.result("Autosubmit database created successfully")
        else:
            Log.error("Database already exists.")
            return False
        return True

    @staticmethod
    def refresh(expid, model_conf):
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
        Autosubmit._create_model_conf(as_conf, model_conf)
        return True

    @staticmethod
    def archive(expid):
        """
        Archives an experiment: call clean (if experiment is of version 3 or later), compress folder
        to tar.gz and moves to year's folder

        :param expid: experiment identifier
        :type expid: str
        """
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, "ASlogs", 'archive{0}.log'.format(expid)))
        exp_folder = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)

        # Cleaning to reduce file size.
        version = get_autosubmit_version(expid)
        if version is not None and version.startswith('3') and not Autosubmit.clean(expid, True, True, True, False):
            Log.critical("Can not archive project. Clean not successful")
            return False

        # Getting year of last completed. If not, year of expid folder
        year = None
        tmp_folder = os.path.join(exp_folder, BasicConfig.LOCAL_TMP_DIR)
        if os.path.isdir(tmp_folder):
            for filename in os.listdir(tmp_folder):
                if filename.endswith("COMPLETED"):
                    file_year = time.localtime(os.path.getmtime(os.path.join(tmp_folder, filename))).tm_year
                    if year is None or year < file_year:
                        year = file_year

        if year is None:
            year = time.localtime(os.path.getmtime(exp_folder)).tm_year
        Log.info("Archiving in year {0}", year)

        # Creating tar file
        Log.info("Creating tar file ... ")
        try:
            year_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, str(year))
            if not os.path.exists(year_path):
                os.mkdir(year_path)
            with tarfile.open(os.path.join(year_path, '{0}.tar.gz'.format(expid)), "w:gz") as tar:
                tar.add(exp_folder, arcname='')
                tar.close()
        except Exception as e:
            Log.critical("Can not write tar file: {0}".format(e))
            return False

        Log.info("Tar file created!")

        try:
            shutil.rmtree(exp_folder)
        except Exception as e:
            Log.critical("Can not remove experiments folder: {0}".format(e))
            Autosubmit.unarchive(expid)
            return False

        Log.result("Experiment archived succesfully")
        return True

    @staticmethod
    def unarchive(expid):
        """
        Unarchives an experiment: uncompress folder from tar.gz and moves to experiments root folder

        :param expid: experiment identifier
        :type expid: str
        """
        BasicConfig.read()
        Log.set_file(os.path.join(BasicConfig.LOCAL_ROOT_DIR, "ASlogs", 'unarchive{0}.log'.format(expid)))
        exp_folder = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)

        if os.path.exists(exp_folder):
            Log.error("Experiment {0} is not archived", expid)
            return False

        # Searching by year. We will store it on database
        year = datetime.datetime.today().year
        archive_path = None
        while year > 2000:
            archive_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, str(year), '{0}.tar.gz'.format(expid))
            if os.path.exists(archive_path):
                break
            year -= 1

        if year == 2000:
            Log.critical("Experiment can not be located on archive")
            return False
        Log.info("Experiment located in {0} archive", year)

        # Creating tar file
        Log.info("Unpacking tar file ... ")
        try:
            os.mkdir(exp_folder)
            with tarfile.open(os.path.join(archive_path), "r:gz") as tar:
                tar.extractall(exp_folder)
                tar.close()
        except Exception as e:
            os.rmdir(exp_folder)
            Log.critical("Can not extract tar file: {0}".format(e))
            return False

        Log.info("Unpacking finished.")

        try:
            os.remove(archive_path)
        except Exception as e:
            Log.error("Can not remove archived file folder: {0}".format(e))
            return False

        Log.result("Experiment {0} unarchived succesfully", expid)
        return True

    @staticmethod
    def _create_model_conf(as_conf, force):
        destiny = as_conf.project_file
        if os.path.exists(destiny):
            if force:
                os.remove(destiny)
            else:
                return
        if as_conf.get_project_type() != 'none' and as_conf.get_file_project_conf():
            shutil.copyfile(os.path.join(as_conf.get_project_dir(), as_conf.get_file_project_conf()), destiny)

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
        Autosubmit._create_model_conf(as_conf, False)

        if project_type != "none":
            # Check project configuration
            as_conf.check_proj()

        # Load parameters
        Log.info("Loading parameters...")
        parameters = as_conf.load_parameters()

        date_list = as_conf.get_date_list()
        if len(date_list) != len(set(date_list)):
            Log.error('There are repeated start dates!')
            return False
        num_chunks = as_conf.get_num_chunks()
        member_list = as_conf.get_member_list()
        if len(member_list) != len(set(member_list)):
            Log.error('There are repeated member names!')
            return False
        rerun = as_conf.get_rerun()

        Log.info("\nCreating joblist...")
        job_list = JobList(expid)

        date_format = ''
        if as_conf.get_chunk_size_unit() is 'hour':
            date_format = 'H'
        for date in date_list:
            if date.hour > 1:
                date_format = 'H'
            if date.minute > 1:
                date_format = 'M'
        job_list.create(date_list, member_list, num_chunks, parameters, date_format)
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
        return True

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
        project_destination = as_conf.get_project_destination()
        if project_type == "git":
            return AutosubmitGit.clone_repository(as_conf, force)
        elif project_type == "svn":
            svn_project_url = as_conf.get_svn_project_url()
            svn_project_revision = as_conf.get_svn_project_revision()
            project_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_PROJ_DIR)
            if os.path.exists(project_path):
                Log.info("Using project folder: {0}", project_path)
                if not force:
                    Log.debug("The project folder exists. SKIPPING...")
                    return True
            else:
                Log.debug("The project folder {0} has been created.", project_path)
            shutil.rmtree(project_path)
            Log.info("Checking out revision {0} into {1}", svn_project_revision + " " + svn_project_url, project_path)
            try:
                output = subprocess.check_output("cd " + project_path + "; svn checkout -r " + svn_project_revision +
                                                 " " + svn_project_url + " " + project_destination, shell=True)
            except subprocess.CalledProcessError:
                Log.error("Can not check out revision {0} into {1}", svn_project_revision + " " + svn_project_url,
                          project_path)
                shutil.rmtree(project_path)
                return False
            Log.debug("{0}" % output)

        elif project_type == "local":
            local_project_path = as_conf.get_local_project_path()
            project_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_PROJ_DIR)
            local_destination = os.path.join(project_path, project_destination)
            if os.path.exists(project_path):
                Log.info("Using project folder: {0}", project_path)
                if not force:
                    Log.debug("The project folder exists. SKIPPING...")
                    return True
                else:
                    shutil.rmtree(project_path)

            os.mkdir(project_path)
            os.mkdir(local_destination)
            Log.debug("The project folder {0} has been created.", project_path)

            Log.info("Copying {0} into {1}", local_project_path, project_path)

            try:
                output = subprocess.check_output("cp -R " + local_project_path + "/* " + local_destination, shell=True)
            except subprocess.CalledProcessError:
                Log.error("Can not copy {0} into {1}. Exiting...", local_project_path, project_path)
                shutil.rmtree(project_path)
                return False
            Log.debug("{0}", output)
        return True

    @staticmethod
    def change_status(final, final_status, job):
        job.status = final_status
        Log.info("CHANGED: job: " + job.name + " status to: " + final)

    @staticmethod
    def set_status(expid, save, final, lst, filter_chunks, filter_status, filter_section):
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
        job_list = pickle.load(open(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, 'pkl', root_name + "_" + expid +
                                    ".pkl"), 'r'))

        final_status = Autosubmit._get_status(final)
        if filter_chunks:
            fc = filter_chunks
            Log.debug(fc)

            if fc == 'Any':
                for job in job_list.get_job_list():
                    Autosubmit.change_status(final, final_status, job)
            else:
                # noinspection PyTypeChecker
                data = json.loads(Autosubmit._create_json(fc))
                for datejson in data['sds']:
                    date = datejson['sd']
                    jobs_date = filter(lambda j: date2str(j.date) == date, job_list.get_job_list())

                    for job in filter(lambda j: j.member is None, jobs_date):
                            Autosubmit.change_status(final, final_status, job)

                    for memberjson in datejson['ms']:
                        member = memberjson['m']
                        jobs_member = filter(lambda j: j.member == member, jobs_date)

                        for job in filter(lambda j: j.chunk is None, jobs_member):
                            Autosubmit.change_status(final, final_status, job)

                        for chunkjson in memberjson['cs']:
                            chunk = int(chunkjson)
                            for job in filter(lambda j: j.chunk == chunk, jobs_member):
                                Autosubmit.change_status(final, final_status, job)

        if filter_status:
            Log.debug("Filtering jobs with status {0}", filter_status)
            if filter_status == 'Any':
                for job in job_list.get_job_list():
                    Autosubmit.change_status(final, final_status, job)
            else:
                fs = Autosubmit._get_status(filter_status)
                for job in filter(lambda j: j.status == fs, job_list.get_job_list()):
                    Autosubmit.change_status(final, final_status, job)

        if filter_section:
            ft = filter_section
            Log.debug(ft)

            if ft == 'Any':
                for job in job_list.get_job_list():
                    Autosubmit.change_status(final, final_status, job)
            else:
                for job in job_list.get_job_list():
                    if job.section == ft:
                        Autosubmit.change_status(final, final_status, job)

        if lst:
            jobs = lst.split()

            if jobs == 'Any':
                for job in job_list.get_job_list():
                    Autosubmit.change_status(final, final_status, job)
            else:
                for job in job_list.get_job_list():
                    if job.name in jobs:
                        Autosubmit.change_status(final, final_status, job)

        sys.setrecursionlimit(50000)

        if save:
            job_list.update_list()
            path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl", root_name + "_" + expid + ".pkl")
            pickle.dump(job_list, open(path, 'w'))
            Log.info("Saving JobList: {0}", path)
        else:
            job_list.update_list(False)
            Log.warning("Changes NOT saved to the JobList!!!!:  use -s option to save")

        monitor_exp = Monitor()
        monitor_exp.generate_output(expid, job_list.get_job_list())
        return True

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
                return strtobool(input().lower())
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
        as_conf.set_platform(hpc)
        as_conf.set_safetysleeptime(10)

        if dummy:
            content = open(as_conf.experiment_file).read()

            # Experiment
            content = content.replace(re.search('^DATELIST =.*', content, re.MULTILINE).group(0),
                                      "DATELIST = 20000101")
            content = content.replace(re.search('^MEMBERS =.*', content, re.MULTILINE).group(0),
                                      "MEMBERS = fc0")
            content = content.replace(re.search('^CHUNKSIZE =.*', content, re.MULTILINE).group(0),
                                      "CHUNKSIZE = 4")
            content = content.replace(re.search('^NUMCHUNKS =.*', content, re.MULTILINE).group(0),
                                      "NUMCHUNKS = 1")
            content = content.replace(re.search('^PROJECT_TYPE =.*', content, re.MULTILINE).group(0),
                                      "PROJECT_TYPE = none")

            open(as_conf.experiment_file, 'w').write(content)

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
        elif s == 'RUNNING':
            return Status.RUNNING
        elif s == 'QUEUING':
            return Status.QUEUING
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
        Method to conduct a test for a given experiment. It creates a new experiment for a given experiment with a
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
        testid = Autosubmit.expid('test', 'test experiment for {0}'.format(expid), expid, False, True)
        if testid == '':
            return False

        as_conf = AutosubmitConfig(testid)
        exp_parser = as_conf.get_parser(as_conf.experiment_file)
        if AutosubmitConfig.get_bool_option(exp_parser, 'rerun', "RERUN", True):
            Log.error('Can not test a RERUN experiment')
            Autosubmit.delete(testid, True)
            return False

        content = open(as_conf.experiment_file).read()
        if hpc is None:
            platforms_parser = as_conf.get_parser(as_conf.platforms_file)
            test_platforms = list()
            for section in platforms_parser.sections():
                if AutosubmitConfig.get_option(platforms_parser, section, 'TEST_SUITE', 'false').lower() == 'true':
                    test_platforms.append(section)
            if len(test_platforms) == 0:
                Log.critical('No test HPC defined')
                return False
            hpc = random.choice(test_platforms)
        if member is None:
            member = random.choice(exp_parser.get('experiment', 'MEMBERS').split(' '))
        if stardate is None:
            stardate = random.choice(exp_parser.get('experiment', 'DATELIST').split(' '))
        # Experiment
        content = content.replace(re.search('DATELIST =.*', content).group(0),
                                  "DATELIST = " + stardate)
        content = content.replace(re.search('MEMBERS =.*', content).group(0),
                                  "MEMBERS = " + member)
        # noinspection PyTypeChecker
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

        open(as_conf.experiment_file, 'w').write(content)

        Autosubmit.create(testid, False)
        if not Autosubmit.run_experiment(testid):
            return False
        return Autosubmit.delete(testid, True)
