#!/usr/bin/env python

# Copyright 2017 Earth Sciences Department, BSC-CNS

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
import threading

from job.job_packager import JobPackager
from job.job_exceptions import WrongTemplateException
from platforms.paramiko_submitter import ParamikoSubmitter
from notifications.notifier import Notifier
from notifications.mail_notifier import MailNotifier
from bscearth.utils.date import date2str
from monitor.monitor import Monitor
from database.db_common import get_autosubmit_version
from database.db_common import delete_experiment
from experiment.experiment_common import copy_experiment
from experiment.experiment_common import new_experiment
from database.db_common import create_db
from job.job_grouping import JobGrouping
from job.job_list_persistence import JobListPersistencePkl
from job.job_list_persistence import JobListPersistenceDb
from job.job_package_persistence import JobPackagePersistence
from job.job_packages import JobPackageThread
from job.job_list import JobList
from git.autosubmit_git import AutosubmitGit
from job.job_common import Status
from config.config_parser import ConfigParserFactory
from config.config_common import AutosubmitConfig
from config.basicConfig import BasicConfig
from distutils.util import strtobool
from log.log import Log, AutosubmitError,AutosubmitCritical

try:
    import dialog
except Exception:
    dialog = None
from time import sleep
import argparse
import subprocess
import json
import tarfile
import time
import copy
import os
import pwd
import sys
import shutil
import re
import random
import signal
import datetime
import portalocker
from pkg_resources import require, resource_listdir, resource_exists, resource_string
from collections import defaultdict
from pyparsing import nestedExpr

"""
Main module for autosubmit. Only contains an interface class to all functionality implemented on autosubmit
"""


sys.path.insert(0, os.path.abspath('.'))

# noinspection PyUnusedLocal
def signal_handler(signal_received, frame):
    """
    Used to handle interrupt signals, allowing autosubmit to clean before exit

    :param signal_received:
    :param frame:
    """
    Log.info('Autosubmit will interrupt at the next safe occasion')
    Autosubmit.exit = True

def signal_handler_create(signal_received, frame):
    """
    Used to handle KeyboardInterrumpt signals while the create method is being executed

    :param signal_received:
    :param frame:
    """
    raise AutosubmitCritical('Autosubmit has been closed in an unexpected way. Killed or control + c.',7010)

class Autosubmit:
    """
    Interface class for autosubmit.
    """
    sys.setrecursionlimit(500000)
    # Get the version number from the relevant file. If not, from autosubmit package
    script_dir = os.path.abspath(os.path.dirname(__file__))

    if not os.path.exists(os.path.join(script_dir, 'VERSION')):
        script_dir = os.path.join(script_dir, os.path.pardir)

    version_path = os.path.join(script_dir, 'VERSION')
    readme_path = os.path.join(script_dir, 'README')
    changes_path = os.path.join(script_dir, 'CHANGELOG')
    if os.path.isfile(version_path):
        with open(version_path) as f:
            autosubmit_version = f.read().strip()
    else:
        autosubmit_version = require("autosubmit")[0].version

    exit = False

    @staticmethod
    def parse_args():
        """
        Parse arguments given to an executable and start execution of command given
        """

        try:
            BasicConfig.read()
            parser = argparse.ArgumentParser(
                description='Main executable for autosubmit. ')

            parser.add_argument('-v', '--version', action='version', version=Autosubmit.autosubmit_version)
            parser.add_argument('-lf', '--logfile', choices=('NO_LOG','INFO','WARNING', 'DEBUG'),
                                default='WARNING', type=str,
                                help="sets file's log level.")
            parser.add_argument('-lc', '--logconsole', choices=('NO_LOG','INFO','WARNING', 'DEBUG'),
                                default='INFO', type=str,
                                help="sets console's log level")

            subparsers = parser.add_subparsers(dest='command')
            # Run
            subparser = subparsers.add_parser(
                'run', description="runs specified experiment")
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument('-nt', '--notransitive', action='store_true',
                                   default=False, help='Disable transitive reduction')
            subparser.add_argument('-v', '--update_version', action='store_true',
                                   default=False, help='Update experiment version')

            # Expid
            subparser = subparsers.add_parser(
                'expid', description="Creates a new experiment")
            group = subparser.add_mutually_exclusive_group()
            group.add_argument(
                '-y', '--copy', help='makes a copy of the specified experiment')
            group.add_argument('-dm', '--dummy', action='store_true',
                               help='creates a new experiment with default values, usually for testing')
            group.add_argument('-op', '--operational', action='store_true',
                               help='creates a new experiment with operational experiment id')
            subparser.add_argument('-H', '--HPC', required=True,
                                   help='specifies the HPC to use for the experiment')
            subparser.add_argument('-d', '--description', type=str, required=True,
                                   help='sets a description for the experiment to store in the database.')
            subparser.add_argument('-c', '--config', type=str, required=False,
                                   help='defines where are located the configuration files.')
            # Delete
            subparser = subparsers.add_parser(
                'delete', description="delete specified experiment")
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument(
                '-f', '--force', action='store_true', help='deletes experiment without confirmation')

            # Monitor
            subparser = subparsers.add_parser(
                'monitor', description="plots specified experiment")
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument('-o', '--output', choices=('pdf', 'png', 'ps', 'svg'),
                                   help='chooses type of output for generated plot')  # Default -o value comes from .conf
            subparser.add_argument('-group_by', choices=('date', 'member', 'chunk', 'split', 'automatic'), default=None,
                                   help='Groups the jobs automatically or by date, member, chunk or split')
            subparser.add_argument('-expand', type=str,
                                   help='Supply the list of dates/members/chunks to filter the list of jobs. Default = "Any". '
                                   'LIST = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]"')
            subparser.add_argument(
                '-expand_status', type=str, help='Select the stat uses to be expanded')
            subparser.add_argument('--hide_groups', action='store_true',
                                   default=False, help='Hides the groups from the plot')
            subparser.add_argument('-cw', '--check_wrapper', action='store_true',
                                   default=False, help='Generate possible wrapper in the current workflow')

            group2 = subparser.add_mutually_exclusive_group(required=False)

            group.add_argument('-fs', '--filter_status', type=str,
                               choices=('Any', 'READY', 'COMPLETED',
                                        'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN'),
                               help='Select the original status to filter the list of jobs')
            group = subparser.add_mutually_exclusive_group(required=False)
            group.add_argument('-fl', '--list', type=str,
                               help='Supply the list of job names to be filtered. Default = "Any". '
                                    'LIST = "b037_20101101_fc3_21_sim b037_20111101_fc4_26_sim"')
            group.add_argument('-fc', '--filter_chunks', type=str,
                               help='Supply the list of chunks to filter the list of jobs. Default = "Any". '
                                    'LIST = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]"')
            group.add_argument('-fs', '--filter_status', type=str,
                               choices=('Any', 'READY', 'COMPLETED',
                                        'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN'),
                               help='Select the original status to filter the list of jobs')
            group.add_argument('-ft', '--filter_type', type=str,
                               help='Select the job type to filter the list of jobs')
            subparser.add_argument('--hide', action='store_true', default=False,
                                   help='hides plot window')
            group2.add_argument('-txt', '--text', action='store_true', default=False,
                                help='Generates only txt status file')

            group2.add_argument('-txtlog', '--txt_logfiles', action='store_true', default=False,
                                help='Generates only txt status file(AS < 3.12b behaviour)')

            subparser.add_argument('-nt', '--notransitive', action='store_true',
                                   default=False, help='Disable transitive reduction')
            subparser.add_argument('-d', '--detail', action='store_true',
                                   default=False, help='Shows Job List view in terminal')

            # Stats
            subparser = subparsers.add_parser(
                'stats', description="plots statistics for specified experiment")
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument('-ft', '--filter_type', type=str, help='Select the job type to filter '
                                                                          'the list of jobs')
            subparser.add_argument('-fp', '--filter_period', type=int, help='Select the period to filter jobs '
                                                                            'from current time to the past '
                                                                            'in number of hours back')
            subparser.add_argument('-o', '--output', choices=('pdf', 'png', 'ps', 'svg'), default='pdf',
                                   help='type of output for generated plot')
            subparser.add_argument('--hide', action='store_true', default=False,
                                   help='hides plot window')
            subparser.add_argument('-nt', '--notransitive', action='store_true',
                                   default=False, help='Disable transitive reduction')

            # Clean
            subparser = subparsers.add_parser(
                'clean', description="clean specified experiment")
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument(
                '-pr', '--project', action="store_true", help='clean project')
            subparser.add_argument('-p', '--plot', action="store_true",
                                   help='clean plot, only 2 last will remain')
            subparser.add_argument('-s', '--stats', action="store_true",
                                   help='clean stats, only last will remain')

            # Recovery
            subparser = subparsers.add_parser(
                'recovery', description="recover specified experiment")
            subparser.add_argument(
                'expid', type=str, help='experiment identifier')
            subparser.add_argument(
                '-np', '--noplot', action='store_true', default=False, help='omit plot')
            subparser.add_argument('--all', action="store_true", default=False,
                                   help='Get completed files to synchronize pkl')
            subparser.add_argument(
                '-s', '--save', action="store_true", default=False, help='Save changes to disk')
            subparser.add_argument('--hide', action='store_true', default=False,
                                   help='hides plot window')
            subparser.add_argument('-group_by', choices=('date', 'member', 'chunk', 'split', 'automatic'), default=None,
                                   help='Groups the jobs automatically or by date, member, chunk or split')
            subparser.add_argument('-expand', type=str,
                                   help='Supply the list of dates/members/chunks to filter the list of jobs. Default = "Any". '
                                        'LIST = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]"')
            subparser.add_argument(
                '-expand_status', type=str, help='Select the statuses to be expanded')
            subparser.add_argument('-nt', '--notransitive', action='store_true',
                                   default=False, help='Disable transitive reduction')
            subparser.add_argument('-nl', '--no_recover_logs', action='store_true', default=False,
                                   help='Disable logs recovery')
            subparser.add_argument('-d', '--detail', action='store_true',
                                   default=False, help='Show Job List view in terminal')

            # Migrate
            subparser = subparsers.add_parser(
                'migrate', description="Migrate experiments from current user to another")
            subparser.add_argument('expid', help='experiment identifier')
            group = subparser.add_mutually_exclusive_group(required=True)
            group.add_argument('-o', '--offer', action="store_true",
                               default=False, help='Offer experiment')
            group.add_argument('-p', '--pickup', action="store_true",
                               default=False, help='Pick-up released experiment')

            # Inspect
            subparser = subparsers.add_parser(
                'inspect', description="Generate all .cmd files")
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument('-nt', '--notransitive', action='store_true',
                                   default=False, help='Disable transitive reduction')
            subparser.add_argument(
                '-f', '--force', action="store_true", help='Overwrite all cmd')
            subparser.add_argument('-cw', '--check_wrapper', action='store_true',
                                   default=False, help='Generate possible wrapper in the current workflow')

            group.add_argument('-fs', '--filter_status', type=str,
                               choices=('Any', 'READY', 'COMPLETED',
                                        'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN'),
                               help='Select the original status to filter the list of jobs')
            group = subparser.add_mutually_exclusive_group(required=False)
            group.add_argument('-fl', '--list', type=str,
                               help='Supply the list of job names to be filtered. Default = "Any". '
                                    'LIST = "b037_20101101_fc3_21_sim b037_20111101_fc4_26_sim"')
            group.add_argument('-fc', '--filter_chunks', type=str,
                               help='Supply the list of chunks to filter the list of jobs. Default = "Any". '
                                    'LIST = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]"')
            group.add_argument('-fs', '--filter_status', type=str,
                               choices=('Any', 'READY', 'COMPLETED',
                                        'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN'),
                               help='Select the original status to filter the list of jobs')
            group.add_argument('-ft', '--filter_type', type=str,
                               help='Select the job type to filter the list of jobs')

            # Check
            subparser = subparsers.add_parser(
                'check', description="check configuration for specified experiment")
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument('-nt', '--notransitive', action='store_true',
                                   default=False, help='Disable transitive reduction')
            # Describe
            subparser = subparsers.add_parser(
                'describe', description="Show details for specified experiment")
            subparser.add_argument('expid', help='experiment identifier')

            # Create
            subparser = subparsers.add_parser(
                'create', description="create specified experiment joblist")
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument(
                '-np', '--noplot', action='store_true', default=False, help='omit plot')
            subparser.add_argument('--hide', action='store_true', default=False,
                                   help='hides plot window')
            subparser.add_argument('-d', '--detail', action='store_true',
                                   default=False, help='Show Job List view in terminal')
            subparser.add_argument('-o', '--output', choices=('pdf', 'png', 'ps', 'svg'),
                                   help='chooses type of output for generated plot')  # Default -o value comes from .conf
            subparser.add_argument('-group_by', choices=('date', 'member', 'chunk', 'split', 'automatic'), default=None,
                                   help='Groups the jobs automatically or by date, member, chunk or split')
            subparser.add_argument('-expand', type=str,
                                   help='Supply the list of dates/members/chunks to filter the list of jobs. Default = "Any". '
                                        'LIST = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]"')
            subparser.add_argument(
                '-expand_status', type=str, help='Select the statuses to be expanded')
            subparser.add_argument('-nt', '--notransitive', action='store_true',
                                   default=False, help='Disable transitive reduction')
            subparser.add_argument('-cw', '--check_wrapper', action='store_true',
                                   default=False, help='Generate possible wrapper in the current workflow')

            # Configure
            subparser = subparsers.add_parser('configure', description="configure database and path for autosubmit. It "
                                                                       "can be done at machine, user or local level."
                                                                       "If no arguments specified configure will "
                                                                       "display dialog boxes (if installed)")
            subparser.add_argument(
                '--advanced', action="store_true", help="Open advanced configuration of autosubmit")
            subparser.add_argument('-db', '--databasepath', default=None, help='path to database. If not supplied, '
                                                                               'it will prompt for it')
            subparser.add_argument(
                '-dbf', '--databasefilename', default=None, help='database filename')
            subparser.add_argument('-lr', '--localrootpath', default=None, help='path to store experiments. If not '
                                                                                'supplied, it will prompt for it')
            subparser.add_argument('-pc', '--platformsconfpath', default=None, help='path to platforms.conf file to '
                                                                                    'use by default. Optional')
            subparser.add_argument('-jc', '--jobsconfpath', default=None, help='path to jobs.conf file to use by '
                                                                               'default. Optional')
            subparser.add_argument(
                '-sm', '--smtphostname', default=None, help='STMP server hostname. Optional')
            subparser.add_argument(
                '-mf', '--mailfrom', default=None, help='Notifications sender address. Optional')
            group = subparser.add_mutually_exclusive_group()
            group.add_argument('--all', action="store_true",
                               help='configure for all users')
            group.add_argument('--local', action="store_true", help='configure only for using Autosubmit from this '
                                                                    'path')

            # Install
            subparsers.add_parser(
                'install', description='install database for autosubmit on the configured folder')

            # Set status
            subparser = subparsers.add_parser(
                'setstatus', description="sets job status for an experiment")
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument(
                '-np', '--noplot', action='store_true', default=False, help='omit plot')
            subparser.add_argument(
                '-s', '--save', action="store_true", default=False, help='Save changes to disk')
            subparser.add_argument('-t', '--status_final',
                                   choices=('READY', 'COMPLETED', 'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN',
                                            'QUEUING', 'RUNNING', 'HELD'),
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
                               help='Select the status (one or more) to filter the list of jobs.'
                                    "Valid values = ['Any', 'READY', 'COMPLETED', 'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN']")
            group.add_argument('-ft', '--filter_type', type=str,
                               help='Select the job type to filter the list of jobs')
            group.add_argument('-ftc', '--filter_type_chunk', type=str,
                               help='Supply the list of chunks to change the status. Default = "Any". When the member name "all" is set, all the chunks \
                               selected from for that member will be updated for all the members. Example: all [1], will have as a result that the \
                                   chunks 1 for all the members will be updated. Follow the format: '
                                    '"[ 19601101 [ fc0 [1 2 3 4] Any [1] ] 19651101 [ fc0 [16-30] ] ],SIM,SIM2,SIM3"')

            subparser.add_argument('--hide', action='store_true', default=False,
                                   help='hides plot window')
            subparser.add_argument('-group_by', choices=('date', 'member', 'chunk', 'split', 'automatic'), default=None,
                                   help='Groups the jobs automatically or by date, member, chunk or split')
            subparser.add_argument('-expand', type=str,
                                   help='Supply the list of dates/members/chunks to filter the list of jobs. Default = "Any". '
                                        'LIST = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]"')
            subparser.add_argument(
                '-expand_status', type=str, help='Select the statuses to be expanded')
            subparser.add_argument('-nt', '--notransitive', action='store_true',
                                   default=False, help='Disable transitive reduction')
            subparser.add_argument('-cw', '--check_wrapper', action='store_true',
                                   default=False, help='Generate possible wrapper in the current workflow')
            subparser.add_argument('-d', '--detail', action='store_true',
                                   default=False, help='Generate detailed view of changes')

            # Test Case
            subparser = subparsers.add_parser(
                'testcase', description='create test case experiment')
            subparser.add_argument(
                '-y', '--copy', help='makes a copy of the specified experiment')
            subparser.add_argument(
                '-d', '--description', required=True, help='description of the test case')
            subparser.add_argument('-c', '--chunks', help='chunks to run')
            subparser.add_argument('-m', '--member', help='member to run')
            subparser.add_argument('-s', '--stardate', help='stardate to run')
            subparser.add_argument(
                '-H', '--HPC', required=True, help='HPC to run experiment on it')
            subparser.add_argument(
                '-b', '--branch', help='branch of git to run (or revision from subversion)')

            # Test
            subparser = subparsers.add_parser(
                'test', description='test experiment')
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument(
                '-c', '--chunks', required=True, help='chunks to run')
            subparser.add_argument('-m', '--member', help='member to run')
            subparser.add_argument('-s', '--stardate', help='stardate to run')
            subparser.add_argument(
                '-H', '--HPC', help='HPC to run experiment on it')
            subparser.add_argument(
                '-b', '--branch', help='branch of git to run (or revision from subversion)')

            # Refresh
            subparser = subparsers.add_parser(
                'refresh', description='refresh project directory for an experiment')
            subparser.add_argument('expid', help='experiment identifier')
            subparser.add_argument('-mc', '--model_conf', default=False, action='store_true',
                                   help='overwrite model conf file')
            subparser.add_argument('-jc', '--jobs_conf', default=False, action='store_true',
                                   help='overwrite jobs conf file')
            # Update Version
            subparser = subparsers.add_parser(
                'updateversion', description='refresh experiment version')
            subparser.add_argument('expid', help='experiment identifier')

            # Archive
            subparser = subparsers.add_parser(
                'archive', description='archives an experiment')
            subparser.add_argument('expid', help='experiment identifier')

            # Unarchive
            subparser = subparsers.add_parser(
                'unarchive', description='unarchives an experiment')
            subparser.add_argument('expid', help='experiment identifier')

            # Readme
            subparsers.add_parser('readme', description='show readme')

            # Changelog
            subparsers.add_parser('changelog', description='show changelog')
            args = parser.parse_args()

        except Exception as e:
            if type(e) is SystemExit:
                if e.message == 0: # Version keyword force an exception in parse arg due and os_exit(0) but the program is succesfully finished
                    print(Autosubmit.autosubmit_version)
                    os._exit(0)
            raise AutosubmitCritical("Incorrect arguments for this command",7011)


        expid = "None"
        if hasattr(args, 'expid'):
            expid = args.expid
        Autosubmit._init_logs(args.command,args.logconsole,args.logfile,expid)

        if args.command == 'run':
            return Autosubmit.run_experiment(args.expid, args.notransitive, args.update_version)
        elif args.command == 'expid':
            return Autosubmit.expid(args.HPC, args.description, args.copy, args.dummy, False,
                                    args.operational, args.config) != ''
        elif args.command == 'delete':
            return Autosubmit.delete(args.expid, args.force)
        elif args.command == 'monitor':
            return Autosubmit.monitor(args.expid, args.output, args.list, args.filter_chunks, args.filter_status,
                                      args.filter_type, args.hide, args.text, args.group_by, args.expand,
                                      args.expand_status, args.hide_groups, args.notransitive, args.check_wrapper, args.txt_logfiles, args.detail)
        elif args.command == 'stats':
            return Autosubmit.statistics(args.expid, args.filter_type, args.filter_period, args.output, args.hide,
                                         args.notransitive)
        elif args.command == 'clean':
            return Autosubmit.clean(args.expid, args.project, args.plot, args.stats)
        elif args.command == 'recovery':
            return Autosubmit.recovery(args.expid, args.noplot, args.save, args.all, args.hide, args.group_by,
                                       args.expand, args.expand_status, args.notransitive, args.no_recover_logs, args.detail)
        elif args.command == 'check':
            return Autosubmit.check(args.expid, args.notransitive)
        elif args.command == 'inspect':
            return Autosubmit.inspect(args.expid, args.list, args.filter_chunks, args.filter_status,
                                      args.filter_type, args.notransitive, args.force, args.check_wrapper)
        elif args.command == 'describe':
            return Autosubmit.describe(args.expid)
        elif args.command == 'migrate':
            return Autosubmit.migrate(args.expid, args.offer, args.pickup)
        elif args.command == 'create':
            return Autosubmit.create(args.expid, args.noplot, args.hide, args.output, args.group_by, args.expand,
                                     args.expand_status, args.notransitive, args.check_wrapper, args.detail)
        elif args.command == 'configure':
            if not args.advanced or (args.advanced and dialog is None):
                return Autosubmit.configure(args.advanced, args.databasepath, args.databasefilename,
                                            args.localrootpath, args.platformsconfpath, args.jobsconfpath,
                                            args.smtphostname, args.mailfrom, args.all, args.local)
            else:
                return Autosubmit.configure_dialog()
        elif args.command == 'install':
            return Autosubmit.install()
        elif args.command == 'setstatus':
            return Autosubmit.set_status(args.expid, args.noplot, args.save, args.status_final, args.list,
                                         args.filter_chunks, args.filter_status, args.filter_type, args.filter_type_chunk, args.hide,
                                         args.group_by, args.expand, args.expand_status, args.notransitive, args.check_wrapper, args.detail)
        elif args.command == 'testcase':
            return Autosubmit.testcase(args.copy, args.description, args.chunks, args.member, args.stardate,
                                       args.HPC, args.branch)
        elif args.command == 'test':
            return Autosubmit.test(args.expid, args.chunks, args.member, args.stardate, args.HPC, args.branch)
        elif args.command == 'refresh':
            return Autosubmit.refresh(args.expid, args.model_conf, args.jobs_conf)
        elif args.command == 'updateversion':
            return Autosubmit.update_version(args.expid)
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

    @staticmethod
    def _init_logs(command,console_level='INFO',log_level='DEBUG',expid='None'):
        Log.set_console_level(console_level)
        if expid != 'None':
            Autosubmit._check_ownership(expid)
            exp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)
            tmp_path = os.path.join(exp_path, BasicConfig.LOCAL_TMP_DIR)
            aslogs_path = os.path.join(tmp_path, BasicConfig.LOCAL_ASLOG_DIR)
            if not os.path.exists(exp_path) and "create" not in command:
                raise AutosubmitCritical("Experiment does not exist", 7012)
            if not os.path.exists(tmp_path):
                os.mkdir(tmp_path)
            if not os.path.exists(aslogs_path):
                os.mkdir(aslogs_path)

            Log.set_file(os.path.join(aslogs_path, command + '.log'), "out", log_level)
            Log.set_file(os.path.join(aslogs_path, command + '_err.log'), "err")
            Log.set_file(os.path.join(aslogs_path, 'jobs_status.log'), "status")
        else:
            Log.set_file(os.path.join(BasicConfig.GLOBAL_LOG_DIR, command + '.log'), "out", log_level)
            Log.set_file(os.path.join(BasicConfig.GLOBAL_LOG_DIR, command + '_err.log'), "err")

    @staticmethod
    def _check_ownership(expid):
        try:
            current_user_id = pwd.getpwuid(os.getuid())[0]
            current_owner_id = pwd.getpwuid(os.stat(os.path.join(
                BasicConfig.LOCAL_ROOT_DIR, expid)).st_uid).pw_name
            if current_user_id != current_owner_id:
                raise AutosubmitCritical("You don't own the experiment {0}.".format(expid),7012)
        except BaseException as e:
            raise AutosubmitCritical("User or owner does not exists",7012,e.message)


    @staticmethod
    def _delete_expid(expid_delete, force):
        """
        Removes an experiment from path and database
        If current user is eadmin and -f has been sent, it deletes regardless 
        of experiment owner

        :type expid_delete: str
        :param expid_delete: identifier of the experiment to delete
        :type force: boolean
        :param force: True if the force flag has been sent
        :return: True if succesfully deleted, False otherwise
        :rtype: boolean
        """
        # Read current user uid
        my_user = os.getuid()
        # Read eadmin user uid
        id_eadmin = os.popen('id -u eadmin').read().strip()
        if expid_delete == '' or expid_delete is None and not os.path.exists(os.path.join(BasicConfig.LOCAL_ROOT_DIR,
                                                                                          expid_delete)):
            Log.result("Experiment directory does not exist.")
        else:
            ret = False
            # Handling possible failure of retrieval of current owner data
            currentOwner_id = 0
            currentOwner = "empty"
            try:
                currentOwner = os.stat(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid_delete)).st_uid
                currentOwner_id = pwd.getpwuid(os.stat(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid_delete)).st_uid).pw_name
            except:
                pass
            finally:
                if currentOwner_id == 0:
                    Log.info("Current owner '{0}' of experiment {1} does not exist anymore.", currentOwner, expid_delete)

            # Deletion workflow continues as usual, a disjunction is included for the case when
            # force is sent, and user is eadmin
            if currentOwner_id == os.getlogin() or (force and my_user == id_eadmin):
                if (force and my_user == id_eadmin):
                    Log.info(
                        "Preparing deletion of experiment {0} from owner: {1}, as eadmin.", expid_delete, currentOwner)
                try:
                    Log.info("Removing experiment directory...")
                    shutil.rmtree(os.path.join(
                        BasicConfig.LOCAL_ROOT_DIR, expid_delete))
                except OSError as e:
                    raise AutosubmitCritical('Can not delete experiment folder: ',7012,e.message)
                Log.info("Deleting experiment from database...")
                ret = delete_experiment(expid_delete)
                if ret:
                    Log.result("Experiment {0} deleted".format(expid_delete))
            else:
                if currentOwner_id == 0:
                    raise AutosubmitCritical('Detected Eadmin user however, -f flag is not found.  {0} can not be deleted!'.format(expid_delete), 7012)
                else:
                    raise AutosubmitCritical('Current user is not the owner of the experiment. {0} can not be deleted!'.format(expid_delete), 7012)

    @staticmethod
    def expid(hpc, description, copy_id='', dummy=False, test=False, operational=False, root_folder=''):
        """
        Creates a new experiment for given HPC

        :param operational: if true, creates an operational experiment
        :type operational: bool
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
        exp_id = None
        if description is None or hpc is None:
            raise AutosubmitCritical("Check that the parameters are defined (-d and -H) ",7011)
        if not copy_id:
            exp_id = new_experiment(
                description, Autosubmit.autosubmit_version, test, operational)
            if exp_id == '':
                raise AutosubmitCritical("Couldn't create a new experiment",7011)
            try:
                os.mkdir(os.path.join(BasicConfig.LOCAL_ROOT_DIR, exp_id))
                os.mkdir(os.path.join(
                    BasicConfig.LOCAL_ROOT_DIR, exp_id, 'conf'))
                Log.info("Copying config files...")

                # autosubmit config and experiment copied from AS.
                files = resource_listdir('autosubmit.config', 'files')
                for filename in files:
                    if resource_exists('autosubmit.config', 'files/' + filename):
                        index = filename.index('.')
                        new_filename = filename[:index] + \
                            "_" + exp_id + filename[index:]

                        if filename == 'platforms.conf' and BasicConfig.DEFAULT_PLATFORMS_CONF != '':
                            content = open(os.path.join(
                                BasicConfig.DEFAULT_PLATFORMS_CONF, filename)).read()
                        elif filename == 'jobs.conf' and BasicConfig.DEFAULT_JOBS_CONF != '':
                            content = open(os.path.join(
                                BasicConfig.DEFAULT_JOBS_CONF, filename)).read()
                        else:
                            content = resource_string(
                                'autosubmit.config', 'files/' + filename)

                        # If autosubmitrc [conf] custom_platforms has been set and file exists, replace content
                        if filename.startswith("platforms") and os.path.isfile(BasicConfig.CUSTOM_PLATFORMS_PATH):
                            content = open(
                                BasicConfig.CUSTOM_PLATFORMS_PATH, 'r').read()

                        conf_new_filename = os.path.join(
                            BasicConfig.LOCAL_ROOT_DIR, exp_id, "conf", new_filename)
                        Log.debug(conf_new_filename)
                        open(conf_new_filename, 'w').write(content)
                Autosubmit._prepare_conf_files(
                    exp_id, hpc, Autosubmit.autosubmit_version, dummy)
            except (OSError, IOError) as e:
                Autosubmit._delete_expid(exp_id)
                raise AutosubmitCritical("Couldn't create a new experiment, permissions?", 7012, e.message)
        else:
            try:
                if root_folder == '' or root_folder is None:
                    root_folder = os.path.join(
                        BasicConfig.LOCAL_ROOT_DIR, copy_id)
                if os.path.exists(root_folder):
                    # List of allowed files from conf
                    conf_copy_filter_folder = []
                    conf_copy_filter = ["autosubmit_" + str(copy_id) + ".conf",
                                        "expdef_" + str(copy_id) + ".conf",
                                        "jobs_" + str(copy_id) + ".conf",
                                        "platforms_" + str(copy_id) + ".conf",
                                        "proj_" + str(copy_id) + ".conf"]
                    if root_folder != os.path.join(BasicConfig.LOCAL_ROOT_DIR, copy_id):
                        conf_copy_filter_folder = ["autosubmit.conf",
                                                   "expdef.conf",
                                                   "jobs.conf",
                                                   "platforms.conf",
                                                   "proj.conf"]
                        exp_id = new_experiment(
                            description, Autosubmit.autosubmit_version, test, operational)
                    else:
                        exp_id = copy_experiment(
                            copy_id, description, Autosubmit.autosubmit_version, test, operational)

                    if exp_id == '':
                        return ''
                    dir_exp_id = os.path.join(
                        BasicConfig.LOCAL_ROOT_DIR, exp_id)
                    os.mkdir(dir_exp_id)
                    os.mkdir(dir_exp_id + '/conf')
                    if root_folder == os.path.join(BasicConfig.LOCAL_ROOT_DIR, copy_id):
                        Log.info(
                            "Copying previous experiment config directories")
                        conf_copy_id = os.path.join(
                            BasicConfig.LOCAL_ROOT_DIR, copy_id, "conf")
                    else:
                        Log.info("Copying from folder: {0}", root_folder)
                        conf_copy_id = root_folder
                    files = os.listdir(conf_copy_id)
                    for filename in files:
                        # Allow only those files in the list
                        if filename in conf_copy_filter:
                            if os.path.isfile(os.path.join(conf_copy_id, filename)):
                                new_filename = filename.replace(
                                    copy_id, exp_id)
                                # Using readlines for replacement handling
                                content = open(os.path.join(
                                    conf_copy_id, filename), 'r').readlines()

                                # If autosubmitrc [conf] custom_platforms has been set and file exists, replace content
                                if filename.startswith("platforms") and os.path.isfile(BasicConfig.CUSTOM_PLATFORMS_PATH):
                                    content = open(
                                        BasicConfig.CUSTOM_PLATFORMS_PATH, 'r').readlines()
                                # Setting email notifications to false
                                if filename == str("autosubmit_" + str(copy_id) + ".conf"):
                                    content = ["NOTIFICATIONS = False\n" if line.startswith(
                                        ("NOTIFICATIONS =", "notifications =")) else line for line in content]
                                # Putting content together before writing
                                sep = ""
                                open(os.path.join(dir_exp_id, "conf",
                                                  new_filename), 'w').write(sep.join(content))
                        if filename in conf_copy_filter_folder:
                            if os.path.isfile(os.path.join(conf_copy_id, filename)):
                                new_filename = filename.split(
                                    ".")[0]+"_"+exp_id+".conf"
                                content = open(os.path.join(
                                    conf_copy_id, filename), 'r').read()
                                # If autosubmitrc [conf] custom_platforms has been set and file exists, replace content
                                if filename.startswith("platforms") and os.path.isfile(
                                        BasicConfig.CUSTOM_PLATFORMS_PATH):
                                    content = open(
                                        BasicConfig.CUSTOM_PLATFORMS_PATH, 'r').read()

                                open(os.path.join(dir_exp_id, "conf",
                                                  new_filename), 'w').write(content)

                    Autosubmit._prepare_conf_files(
                        exp_id, hpc, Autosubmit.autosubmit_version, dummy)
                    #####
                    autosubmit_config = AutosubmitConfig(
                        exp_id, BasicConfig, ConfigParserFactory())
                    autosubmit_config.check_conf_files(False)
                    project_type = autosubmit_config.get_project_type()
                    if project_type == "git":
                        autosubmit_git = AutosubmitGit(copy_id[0])
                        Log.info("checking model version...")
                        if not autosubmit_git.check_commit(autosubmit_config):
                            raise AutosubmitCritical("Uncommitted changes",7013)

                else:
                    raise AutosubmitCritical("The experiment directory doesn't exist",7012)
            except (OSError, IOError) as e:
                Autosubmit._delete_expid(exp_id, True)
                raise AutosubmitCritical("Can not create experiment", 7012,e.message)

        Log.debug("Creating temporal directory...")
        exp_id_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, exp_id)
        tmp_path = os.path.join(exp_id_path, "tmp")
        os.mkdir(tmp_path)
        os.chmod(tmp_path, 0o775)
        os.mkdir(os.path.join(tmp_path, BasicConfig.LOCAL_ASLOG_DIR))
        os.chmod(os.path.join(tmp_path, BasicConfig.LOCAL_ASLOG_DIR), 0o775)
        Log.debug("Creating temporal remote directory...")
        remote_tmp_path = os.path.join(tmp_path, "LOG_"+exp_id)
        os.mkdir(remote_tmp_path)
        os.chmod(remote_tmp_path, 0o755)

        Log.debug("Creating pkl directory...")
        os.mkdir(os.path.join(exp_id_path, "pkl"))

        Log.debug("Creating plot directory...")
        os.mkdir(os.path.join(exp_id_path, "plot"))
        os.chmod(os.path.join(exp_id_path, "plot"), 0o775)
        Log.result("Experiment registered successfully")
        Log.warning("Remember to MODIFY the config files!")
        try:
            Log.debug("Setting the right permissions...")
            os.chmod(os.path.join(exp_id_path, "conf"), 0o755)
            os.chmod(os.path.join(exp_id_path, "pkl"), 0o755)
            os.chmod(os.path.join(exp_id_path, "tmp"), 0o755)
            os.chmod(os.path.join(exp_id_path, "plot"), 0o775)
            os.chmod(os.path.join(exp_id_path, "conf/autosubmit_" +
                                  str(exp_id) + ".conf"), 0o755)
            os.chmod(os.path.join(exp_id_path, "conf/expdef_" +
                                  str(exp_id) + ".conf"), 0o755)
            os.chmod(os.path.join(exp_id_path, "conf/jobs_" +
                                  str(exp_id) + ".conf"), 0o755)
            os.chmod(os.path.join(exp_id_path, "conf/platforms_" +
                                  str(exp_id) + ".conf"), 0o755)
            os.chmod(os.path.join(exp_id_path, "conf/proj_" +
                                  str(exp_id) + ".conf"), 0o755)
        except:
            pass
        return exp_id

    @staticmethod
    def delete(expid, force):
        """
        Deletes and experiment from database and experiment's folder

        :type force: bool
        :type expid: str
        :param expid: identifier of the experiment to delete
        :param force: if True, does not ask for confirmation

        :returns: True if succesful, False if not
        :rtype: bool
        """

        if os.path.exists(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)):
            if force or Autosubmit._user_yes_no_query("Do you want to delete " + expid + " ?"):
                Log.debug('Enter Autosubmit._delete_expid {0}', expid)
                return Autosubmit._delete_expid(expid, force)
            else:
                raise AutosubmitCritical("Insufficient permissions",7012)
        else:
            raise AutosubmitCritical("Experiment does not exist", 7012)

    @staticmethod
    def _load_parameters(as_conf, job_list, platforms):
        """
        Add parameters from configuration files into platform objects, and into the job_list object.

        :param as_conf: Basic configuration handler.\n
        :type as_conf: AutosubmitConfig object\n
        :param job_list: Handles the list as a unique entity.\n
        :type job_list: JobList() object\n
        :param platforms: List of platforms related to the experiment.\n
        :type platforms: List() of Platform Objects. e.g EcPlatform(), SgePlatform().
        :return: Nothing, modifies input.
        """
        # Load parameters
        Log.debug("Loading parameters...")
        parameters = as_conf.load_parameters()
        for platform_name in platforms:
            platform = platforms[platform_name]
            # Call method from platform.py parent object
            platform.add_parameters(parameters)
        # Platform = from DEFAULT.HPCARCH, e.g. marenostrum4
        if as_conf.get_platform().lower() not in platforms.keys():
            raise AutosubmitCritical("Specified platform in expdef_.conf " + str(as_conf.get_platform(
            ).lower()) + " is not a valid platform defined in platforms_.conf.",7014)
        platform = platforms[as_conf.get_platform().lower()]
        platform.add_parameters(parameters, True)
        # Attach paramenters to JobList
        job_list.parameters = parameters
    @staticmethod
    def inspect(expid,  lst, filter_chunks, filter_status, filter_section, notransitive=False, force=False, check_wrapper=False):
        """
         Generates cmd files experiment.

         :type expid: str
         :param expid: identifier of experiment to be run
         :return: True if run to the end, False otherwise
         :rtype: bool
         """

        Autosubmit._check_ownership(expid)
        exp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)
        tmp_path = os.path.join(exp_path, BasicConfig.LOCAL_TMP_DIR)
        if os.path.exists(os.path.join(tmp_path, 'autosubmit.lock')):
            locked = True
        else:
            locked = False
        Log.info("Starting inspect command")
        os.system('clear')
        signal.signal(signal.SIGINT, signal_handler)
        as_conf = AutosubmitConfig(expid, BasicConfig, ConfigParserFactory())
        as_conf.check_conf_files(True)
        project_type = as_conf.get_project_type()
        safetysleeptime = as_conf.get_safetysleeptime()
        Log.debug("The Experiment name is: {0}", expid)
        Log.debug("Sleep: {0}", safetysleeptime)
        packages_persistence = JobPackagePersistence(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl"),
                                                     "job_packages_" + expid)
        os.chmod(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid,
                              "pkl", "job_packages_" + expid + ".db"), 0644)

        packages_persistence.reset_table(True)
        job_list_original = Autosubmit.load_job_list(
            expid, as_conf, notransitive=notransitive)
        job_list = copy.deepcopy(job_list_original)
        job_list.packages_dict = {}

        Log.debug("Length of the jobs list: {0}", len(job_list))

        # variables to be updated on the fly
        safetysleeptime = as_conf.get_safetysleeptime()
        Log.debug("Sleep: {0}", safetysleeptime)
        # Generate
        Log.info("Starting to generate cmd scripts")

        if not isinstance(job_list, type([])):
            jobs = []
            jobs_cw = []
            if check_wrapper and (not locked or (force and locked)):
                Log.info("Generating all cmd script adapted for wrappers")
                jobs = job_list.get_uncompleted()

                jobs_cw = job_list.get_completed()
            else:
                if (force and not locked) or (force and locked):
                    Log.info("Overwritting all cmd scripts")
                    jobs = job_list.get_job_list()
                elif locked:
                    Log.warning(
                        "There is a .lock file and not -f, generating only all unsubmitted cmd scripts")
                    jobs = job_list.get_unsubmitted()
                else:
                    Log.info("Generating cmd scripts only for selected jobs")
                    if filter_chunks:
                        fc = filter_chunks
                        Log.debug(fc)
                        if fc == 'Any':
                            jobs = job_list.get_job_list()
                        else:
                            # noinspection PyTypeChecker
                            data = json.loads(Autosubmit._create_json(fc))
                            for date_json in data['sds']:
                                date = date_json['sd']
                                jobs_date = filter(lambda j: date2str(
                                    j.date) == date, job_list.get_job_list())

                                for member_json in date_json['ms']:
                                    member = member_json['m']
                                    jobs_member = filter(
                                        lambda j: j.member == member, jobs_date)

                                    for chunk_json in member_json['cs']:
                                        chunk = int(chunk_json)
                                        jobs = jobs + \
                                            [job for job in filter(
                                                lambda j: j.chunk == chunk, jobs_member)]

                    elif filter_status:
                        Log.debug(
                            "Filtering jobs with status {0}", filter_status)
                        if filter_status == 'Any':
                            jobs = job_list.get_job_list()
                        else:
                            fs = Autosubmit._get_status(filter_status)
                            jobs = [job for job in filter(
                                lambda j: j.status == fs, job_list.get_job_list())]

                    elif filter_section:
                        ft = filter_section
                        Log.debug(ft)

                        if ft == 'Any':
                            jobs = job_list.get_job_list()
                        else:
                            for job in job_list.get_job_list():
                                if job.section == ft:
                                    jobs.append(job)
                    elif lst:
                        jobs_lst = lst.split()

                        if jobs == 'Any':
                            jobs = job_list.get_job_list()
                        else:
                            for job in job_list.get_job_list():
                                if job.name in jobs_lst:
                                    jobs.append(job)
                    else:
                        jobs = job_list.get_job_list()
        if isinstance(jobs, type([])):
            referenced_jobs_to_remove = set()
            for job in jobs:
                for child in job.children:
                    if child not in jobs:
                        referenced_jobs_to_remove.add(child)
                for parent in job.parents:
                    if parent not in jobs:
                        referenced_jobs_to_remove.add(parent)

            for job in jobs:
                job.status = Status.WAITING

            Autosubmit.generate_scripts_andor_wrappers(
                as_conf, job_list, jobs, packages_persistence, False)
        if len(jobs_cw) > 0:
            referenced_jobs_to_remove = set()
            for job in jobs_cw:
                for child in job.children:
                    if child not in jobs_cw:
                        referenced_jobs_to_remove.add(child)
                for parent in job.parents:
                    if parent not in jobs_cw:
                        referenced_jobs_to_remove.add(parent)

            for job in jobs_cw:
                job.status = Status.WAITING
            Autosubmit.generate_scripts_andor_wrappers(
                as_conf, job_list, jobs_cw, packages_persistence, False)

        Log.info("no more scripts to generate, now proceed to check them manually")
        time.sleep(safetysleeptime)
        return True

    @staticmethod
    def generate_scripts_andor_wrappers(as_conf, job_list, jobs_filtered, packages_persistence, only_wrappers=False):
        """
        :param as_conf: Class that handles basic configuration parameters of Autosubmit. \n
        :type as_conf: AutosubmitConfig() Object \n
        :param job_list: Representation of the jobs of the experiment, keeps the list of jobs inside. \n
        :type job_list: JobList() Object \n
        :param jobs_filtered: list of jobs that are relevant to the process. \n 
        :type jobs_filtered: List() of Job Objects \n
        :param packages_persistence: Object that handles local db persistence.  \n
        :type packages_persistence: JobPackagePersistence() Object \n
        :param only_wrappers: True when coming from Autosubmit.create(). False when coming from Autosubmit.inspect(), \n
        :type only_wrappers: Boolean \n
        :return: Nothing\n
        :rtype: \n
        """
        job_list._job_list = jobs_filtered
        job_list.update_list(as_conf, False)

        # Current choice is Paramiko Submitter
        submitter = Autosubmit._get_submitter(as_conf)
        # Load platforms saves a dictionary Key: Platform Name, Value: Corresponding Platform Object
        submitter.load_platforms(as_conf)
        # The value is retrieved from DEFAULT.HPCARCH
        hpcarch = as_conf.get_platform()
        Autosubmit._load_parameters(as_conf, job_list, submitter.platforms)
        platforms_to_test = set()
        for job in job_list.get_job_list():
            if job.platform_name is None:
                job.platform_name = hpcarch
            # Assign platform objects to each job
            # noinspection PyTypeChecker
            job.platform = submitter.platforms[job.platform_name.lower()]
            # Add object to set
            # noinspection PyTypeChecker
            platforms_to_test.add(job.platform)
        # case setstatus
        job_list.check_scripts(as_conf)
        job_list.update_list(as_conf, False)
        # Loading parameters again
        Autosubmit._load_parameters(as_conf, job_list, submitter.platforms)
        while job_list.get_active():
            Autosubmit.submit_ready_jobs(
                as_conf, job_list, platforms_to_test, packages_persistence, True, only_wrappers, hold=False)
            job_list.update_list(as_conf, False)

    @staticmethod
    def run_experiment(expid, notransitive=False, update_version=False):
        """
        Runs and experiment (submitting all the jobs properly and repeating its execution in case of failure).

        :type expid: str
        :param expid: identifier of experiment to be run
        :return: True if run to the end, False otherwise
        :rtype: bool
        """

        exp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)
        tmp_path = os.path.join(exp_path, BasicConfig.LOCAL_TMP_DIR)
        import platform
        host = platform.node()
        if BasicConfig.ALLOWED_HOSTS and host not in BasicConfig.ALLOWED_HOSTS:
            raise AutosubmitCritical("The current host is not allowed to run Autosubmit",7004)


        as_conf = AutosubmitConfig(expid, BasicConfig, ConfigParserFactory())
        as_conf.check_conf_files(True)
        Log.info("Autosubmit is running with {0}", Autosubmit.autosubmit_version)
        if update_version:
            if as_conf.get_version() != Autosubmit.autosubmit_version:
                Log.info("The {2} experiment {0} version is being updated to {1} for match autosubmit version",
                         as_conf.get_version(), Autosubmit.autosubmit_version, expid)
                as_conf.set_version(Autosubmit.autosubmit_version)
        else:
            if as_conf.get_version() is not None and as_conf.get_version() != Autosubmit.autosubmit_version:
                raise AutosubmitCritical("Current experiment uses ({0}) which is not the running Autosubmit version  \nPlease, update the experiment version if you wish to continue using AutoSubmit {1}\nYou can achieve this using the command autosubmit updateversion {2} \n"
                             "Or with the -v parameter: autosubmit run {2} -v ".format(as_conf.get_version(), Autosubmit.autosubmit_version, expid),7067)
        # checking if there is a lock file to avoid multiple running on the same expid
        try:
            with portalocker.Lock(os.path.join(tmp_path, 'autosubmit.lock'), timeout=1):
                Log.info("Preparing .lock file to avoid multiple instances with same experiment id")
                os.system('clear')
                signal.signal(signal.SIGINT, signal_handler)

                hpcarch = as_conf.get_platform()
                safetysleeptime = as_conf.get_safetysleeptime()
                retrials = as_conf.get_retrials()
                submitter = Autosubmit._get_submitter(as_conf)
                submitter.load_platforms(as_conf)
                Log.debug("The Experiment name is: {0}", expid)
                Log.debug("Sleep: {0}", safetysleeptime)
                Log.debug("Default retrials: {0}", retrials)
                Log.info("Starting job submission...")
                pkl_dir = os.path.join(
                    BasicConfig.LOCAL_ROOT_DIR, expid, 'pkl')
                try:
                    job_list = Autosubmit.load_job_list(expid, as_conf, notransitive=notransitive)
                except BaseException as e:
                    raise AutosubmitCritical("Corrupted job_list, backup couldn''t be restored",7040,e.message)


                Log.debug("Starting from job list restored from {0} files", pkl_dir)
                Log.debug("Length of the jobs list: {0}", len(job_list))
                Autosubmit._load_parameters(as_conf, job_list, submitter.platforms)
                # check the job list script creation
                Log.debug("Checking experiment templates...")
                platforms_to_test = set()
                for job in job_list.get_job_list():
                    if job.platform_name is None:
                        job.platform_name = hpcarch
                    # noinspection PyTypeChecker
                    job.platform = submitter.platforms[job.platform_name.lower(
                    )]
                    # noinspection PyTypeChecker
                    platforms_to_test.add(job.platform)
                job_list.check_scripts(as_conf)
                try:
                    packages_persistence = JobPackagePersistence(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl"),"job_packages_" + expid)
                except BaseException as e:
                    raise AutosubmitCritical("Corrupted job_packages, python 2.7 and sqlite doesn't allow to restore these packages",7040,e.message)
                if as_conf.get_wrapper_type() != 'none':
                    os.chmod(os.path.join(BasicConfig.LOCAL_ROOT_DIR,
                                          expid, "pkl", "job_packages_" + expid+".db"), 0644)
                    try:
                        packages = packages_persistence.load()
                    except BaseException as e:
                        raise AutosubmitCritical(
                            "Corrupted job_packages, python 2.7 and sqlite doesn't allow to restore these packages(will work on autosubmit4)",
                            7040, e.message)

                    for (exp_id, package_name, job_name) in packages:
                        if package_name not in job_list.packages_dict:
                            job_list.packages_dict[package_name] = []
                        job_list.packages_dict[package_name].append(
                            job_list.get_job_by_name(job_name))
                    for package_name, jobs in job_list.packages_dict.items():
                        from job.job import WrapperJob
                        wrapper_job = WrapperJob(package_name, jobs[0].id, Status.SUBMITTED, 0, jobs,
                                                 None,
                                                 None, jobs[0].platform, as_conf, jobs[0].hold)
                        job_list.job_package_map[jobs[0].id] = wrapper_job
                job_list.update_list(as_conf)

                job_list.save()
                Log.info("Autosubmit is running with v{0}", Autosubmit.autosubmit_version)
                #########################
                # AUTOSUBMIT - MAIN LOOP
                #########################
                # Main loop. Finishing when all jobs have been submitted
                main_loop_retrials = 120 # Hard limit of tries 120 tries at 1min sleep each try
                Autosubmit.restore_platforms(platforms_to_test) # establish the connection to all platforms
                save = True
                while job_list.get_active():
                    try:
                        if Autosubmit.exit:
                            return 0
                        # reload parameters changes
                        Log.debug("Reloading parameters...")
                        as_conf.reload()
                        Autosubmit._load_parameters(as_conf, job_list, submitter.platforms)
                        total_jobs = len(job_list.get_job_list())
                        Log.info("\n\n{0} of {1} jobs remaining ({2})".format(total_jobs - len(job_list.get_completed()),total_jobs,time.strftime("%H:%M")))
                        safetysleeptime = as_conf.get_safetysleeptime()
                        default_retrials = as_conf.get_retrials()
                        check_wrapper_jobs_sleeptime = as_conf.get_wrapper_check_time()
                        Log.debug("Sleep: {0}", safetysleeptime)
                        Log.debug("Number of retrials: {0}", default_retrials)
                        Log.debug('WRAPPER CHECK TIME = {0}'.format(check_wrapper_jobs_sleeptime))
                        if save: # previous iteration
                            job_list.backup_save()
                        save = False
                        slurm = []
                        for platform in platforms_to_test:
                            list_jobid = ""
                            completed_joblist = []
                            list_prevStatus = []
                            queuing_jobs = job_list.get_in_queue_grouped_id(
                                platform)
                            for job_id, job in queuing_jobs.items():
                                # Check Wrappers one-by-one
                                if job_list.job_package_map and job_id in job_list.job_package_map:
                                    Log.debug(
                                        'Checking wrapper job with id ' + str(job_id))
                                    wrapper_job = job_list.job_package_map[job_id]
                                    if as_conf.get_notifications() == 'true':
                                        for inner_job in wrapper_job.job_list:
                                            inner_job.prev_status = inner_job.status
                                    check_wrapper = True
                                    if wrapper_job.status == Status.RUNNING:
                                        check_wrapper = True if datetime.timedelta.total_seconds(datetime.datetime.now(
                                        ) - wrapper_job.checked_time) >= check_wrapper_jobs_sleeptime else False
                                    if check_wrapper:
                                        wrapper_job.checked_time = datetime.datetime.now()
                                        # This is where wrapper will be checked on the slurm platform, update takes place.
                                        platform.check_job(wrapper_job)
                                        try:
                                            if wrapper_job.status != wrapper_job.new_status:
                                                Log.info('Wrapper job ' + wrapper_job.name + ' changed from ' + str(Status.VALUE_TO_KEY[wrapper_job.status]) + ' to status ' + str(Status.VALUE_TO_KEY[wrapper_job.new_status]))
                                        except:
                                            raise AutosubmitCritical("Wrapper is in Unknown Status couldn't get wrapper parameters",7050)

                                        # New status will be saved and inner_jobs will be checked.
                                        wrapper_job.check_status(wrapper_job.new_status)
                                        # Erase from packages if the wrapper failed to be queued ( Hold Admin bug )
                                        if wrapper_job.status == Status.WAITING:
                                            for inner_job in wrapper_job.job_list:
                                                inner_job.packed = False
                                            job_list.job_package_map.pop(
                                                job_id, None)
                                            job_list.packages_dict.pop(
                                                job_id, None)
                                        save = True

                                    # Notifications e-mail
                                    if as_conf.get_notifications() == 'true':
                                        for inner_job in wrapper_job.job_list:
                                            if inner_job.prev_status != inner_job.status:
                                                if Status.VALUE_TO_KEY[inner_job.status] in inner_job.notify_on:
                                                    Notifier.notify_status_change(MailNotifier(BasicConfig), expid, inner_job.name,
                                                                                  Status.VALUE_TO_KEY[inner_job.prev_status],
                                                                                  Status.VALUE_TO_KEY[inner_job.status],
                                                                                  as_conf.get_mails_to())
                                else:  # Prepare jobs, if slurm check all active jobs at once.
                                    job = job[0]
                                    prev_status = job.status
                                    if job.status == Status.FAILED:
                                        continue
                                    # If exist key has been pressed and previous status was running, do not check
                                    if not (Autosubmit.exit is True and prev_status == Status.RUNNING):
                                        if platform.type == "slurm":  # List for add all jobs that will be checked
                                            # Do not check if Autosubmit exit is True and the previous status was running.
                                            # if not (Autosubmit.exit == True and prev_status == Status.RUNNING):
                                            list_jobid += str(job_id) + ','
                                            list_prevStatus.append(prev_status)
                                            completed_joblist.append(job)
                                        else:  # If they're not from slurm platform check one-by-one
                                            platform.check_job(job)
                                            if prev_status != job.update_status(as_conf.get_copy_remote_logs() == 'true'):
                                                if as_conf.get_notifications() == 'true':
                                                    if Status.VALUE_TO_KEY[job.status] in job.notify_on:
                                                        Notifier.notify_status_change(MailNotifier(BasicConfig), expid, job.name,
                                                                                      Status.VALUE_TO_KEY[prev_status],
                                                                                      Status.VALUE_TO_KEY[job.status],
                                                                                      as_conf.get_mails_to())
                                        save = True

                            if platform.type == "slurm" and list_jobid != "":
                                slurm.append(
                                    [platform, list_jobid, list_prevStatus, completed_joblist])
                        # END Normal jobs + wrappers
                        # CHECK ALL JOBS at once if they're from slurm ( wrappers non contempled)
                        for platform_jobs in slurm:
                            platform = platform_jobs[0]
                            jobs_to_check = platform_jobs[1]
                            platform.check_Alljobs(
                                platform_jobs[3], jobs_to_check, as_conf.get_copy_remote_logs())
                            for j_Indx in xrange(0, len(platform_jobs[3])):
                                prev_status = platform_jobs[2][j_Indx]
                                job = platform_jobs[3][j_Indx]
                                if prev_status != job.update_status(as_conf.get_copy_remote_logs() == 'true'):
                                    if as_conf.get_notifications() == 'true':
                                        if Status.VALUE_TO_KEY[job.status] in job.notify_on:
                                            Notifier.notify_status_change(MailNotifier(BasicConfig), expid, job.name,
                                                                          Status.VALUE_TO_KEY[prev_status],
                                                                          Status.VALUE_TO_KEY[job.status],
                                                                          as_conf.get_mails_to())
                                save = True
                        # End Check Current jobs
                        save2 = job_list.update_list(as_conf)
                        if save or save2:
                            job_list.save()
                        if len(job_list.get_ready()) > 0:
                            Autosubmit.submit_ready_jobs(as_conf, job_list, platforms_to_test, packages_persistence, hold=False)
                        if as_conf.get_remote_dependencies() and len(job_list.get_prepared()) > 0:
                            Autosubmit.submit_ready_jobs(as_conf, job_list, platforms_to_test, packages_persistence, hold=True)
                        save = job_list.update_list(as_conf)
                        if save:
                            job_list.save()
                        if Autosubmit.exit:
                            job_list.save()
                        time.sleep(safetysleeptime)
                    except AutosubmitError as e: #If an error is detected, restore all connections and job_list
                        Log.error("Trace: {0}", e.trace)
                        Log.error("{1} [eCode={0}]", e.code, e.message)
                        Log.info("Waiting 1 minute before continue")
                        sleep(60)
                        #Save job_list if not is a failed submitted job
                        if "submitted" not in e.message:
                            try:
                                save = job_list.update_list(as_conf)
                                if save:
                                    job_list.save()
                            except BaseException as e: #Restore from file
                                try:
                                    job_list = Autosubmit.load_job_list(expid, as_conf, notransitive=notransitive)
                                except BaseException as e:
                                    raise AutosubmitCritical("Corrupted job_list, backup couldn't be restored", 7040,
                                                             e.message)
                        else: # Restore from files
                            try:
                                job_list = Autosubmit.load_job_list(expid, as_conf, notransitive=notransitive)
                            except BaseException as e:
                                raise AutosubmitCritical("Corrupted job_list, backup couldn't be restored", 7040,
                                                         e.message)
                        if main_loop_retrials > 0: # Restore platforms and try again, to avoid endless loop with failed configuration, a hard limit is set.
                            main_loop_retrials = main_loop_retrials - 1
                            try:
                                Autosubmit.restore_platforms(platforms_to_test)
                            except BaseException:
                                raise AutosubmitCritical("Autosubmit couldn't recover the platforms",7050, e.message)
                        else:
                            raise AutosubmitCritical("Autosubmit Encounter too much errors during running time",7051,e.message)
                    except AutosubmitCritical as e: # Critical errors can't be recovered. Failed configuration or autosubmit error
                        raise AutosubmitCritical(e.message, e.code, e.trace)
                    except portalocker.AlreadyLocked:
                        message = "We have detected that there is another Autosubmit instance using the experiment\n. Stop other Autosubmit instances that are using the experiment or delete autosubmit.lock file located on tmp folder"
                        raise AutosubmitCritical(message, 7000)
                    except BaseException as e: # If this happens, there is a bug in the code or an exception not-well caught
                        raise
                #############################################################################3
                Log.result("No more jobs to run.")
                # Wait for all remaining threads of I/O, close remaining connections
                timeout = 0
                for platform in platforms_to_test:
                    platform.closeConnection()
                active_threads = True
                all_threads = threading.enumerate()
                while active_threads and timeout < 360:
                    active_threads = False
                    threads_active = 0
                    for thread in all_threads:
                        if "Thread-" in thread.name:
                            if thread.isAlive():
                                active_threads = True
                                threads_active = threads_active+1
                        sleep(10)
                if len(job_list.get_failed()) > 0:
                    Log.info("Some jobs have failed and reached maximum retrials")
                else:
                    Log.result("Run successful")
        except portalocker.AlreadyLocked:
            message = "We have detected that there is another Autosubmit instance using the experiment\n. Stop other Autosubmit instances that are using the experiment or delete autosubmit.lock file located on tmp folder"
            raise AutosubmitCritical(message,7000)
        except AutosubmitCritical as e:
            raise AutosubmitCritical(e.message, e.code, e.trace)
        except BaseException as e:
            raise

    @staticmethod
    def restore_platforms(platform_to_test):
        Log.result("Checking the connection to all platforms in use")
        for platform in platform_to_test:
            platform.test_connection()
            Log.result("[{1}] Connection successfull to host {0}",platform.host,platform.name)
    @staticmethod
    def submit_ready_jobs(as_conf, job_list, platforms_to_test, packages_persistence, inspect=False,
                          only_wrappers=False, hold=False):
        """
        Gets READY jobs and send them to the platforms if there is available space on the queues

        :param as_conf: autosubmit config object \n
        :type as_conf: AutosubmitConfig object  \n
        :param job_list: job list to check  \n
        :type job_list: JobList object  \n
        :param platforms_to_test: platforms used  \n
        :type platforms_to_test: set of Platform Objects, e.g. SgePlatform(), LsfPlatform().  \n
        :param packages_persistence: Handles database per experiment. \n
        :type packages_persistence: JobPackagePersistence object \n
        :param inspect: True if coming from generate_scripts_andor_wrappers(). \n
        :type inspect: Boolean \n
        :param only_wrappers: True if it comes from create -cw, False if it comes from inspect -cw. \n
        :type only_wrappers: Boolean \n
        :return: True if at least one job was submitted, False otherwise \n
        :rtype: Boolean
        """
        save = False
        for platform in platforms_to_test:
            if not hold:
                Log.debug("\nJobs ready for {1}: {0}", len(
                    job_list.get_ready(platform, hold=hold)), platform.name)
            else:
                Log.debug("\nJobs prepared for {1}: {0}", len(
                    job_list.get_prepared(platform)), platform.name)

            packages_to_submit = JobPackager(
                as_conf, platform, job_list, hold=hold).build_packages()

            if not inspect:
                platform.open_submit_script()
            valid_packages_to_submit = []
            for package in packages_to_submit:
                try:
                    # If called from inspect command or -cw
                    if only_wrappers or inspect:
                        if hasattr(package, "name"):
                            job_list.packages_dict[package.name] = package.jobs
                            from job.job import WrapperJob
                            wrapper_job = WrapperJob(package.name, package.jobs[0].id, Status.READY, 0,
                                                     package.jobs,
                                                     package._wallclock, package._num_processors,
                                                     package.platform, as_conf, hold)
                            job_list.job_package_map[package.jobs[0].id] = wrapper_job
                            packages_persistence.save(
                                package.name, package.jobs, package._expid, inspect)
                        for innerJob in package._jobs:
                            # Setting status to COMPLETED so it does not get stuck in the loop that calls this function
                            innerJob.status = Status.COMPLETED

                    # If called from RUN or inspect command
                    if not only_wrappers:
                        try:
                            package.submit( as_conf, job_list.parameters, inspect, hold=hold)
                            valid_packages_to_submit.append(package)
                        except (IOError, OSError):
                            continue
                        except AutosubmitError as e:
                            raise
                        if hasattr(package, "name"):
                            job_list.packages_dict[package.name] = package.jobs
                            from job.job import WrapperJob
                            wrapper_job = WrapperJob(package.name, package.jobs[0].id, Status.READY, 0,
                                                     package.jobs,
                                                     package._wallclock, package._num_processors,
                                                     package.platform, as_conf, hold)
                            job_list.job_package_map[package.jobs[0].id] = wrapper_job

                    if isinstance(package, JobPackageThread):
                        # If it is instance of JobPackageThread, then it is JobPackageVertical.
                        packages_persistence.save(
                            package.name, package.jobs, package._expid, inspect)
                except WrongTemplateException as e:
                    raise AutosubmitCritical("Invalid parameter substitution in {0} template".format(e.job_name),7014)
                except AutosubmitCritical as e:
                    raise AutosubmitCritical(e.message,e.code,e.trace)
                except AutosubmitError as e:
                    raise
                except Exception as e:
                    raise

            if platform.type == "slurm" and not inspect and not only_wrappers:
                try:
                    save = True
                    if len(valid_packages_to_submit) > 0:
                        jobs_id = platform.submit_Script(hold=hold)
                        if jobs_id is None:
                            raise BaseException(
                                "Exiting AS, AS is unable to get jobID this can be due a failure on the platform or a bad parameter on job.conf(check that queue parameter is valid for your current platform(CNS,BSC32,PRACE...)")
                        i = 0
                        for package in valid_packages_to_submit:
                            for job in package.jobs:
                                job.id = str(jobs_id[i])
                                job.status = Status.SUBMITTED
                                job.hold = hold
                                job.write_submit_time()
                            if hasattr(package, "name"):
                                job_list.packages_dict[package.name] = package.jobs
                                from job.job import WrapperJob
                                wrapper_job = WrapperJob(package.name, package.jobs[0].id, Status.SUBMITTED, 0,
                                                         package.jobs,
                                                         package._wallclock, package._num_processors,
                                                         package.platform, as_conf, hold)
                                job_list.job_package_map[package.jobs[0].id] = wrapper_job
                                if isinstance(package, JobPackageThread):
                                    # Saving only when it is a real multi job package
                                    packages_persistence.save(
                                        package.name, package.jobs, package._expid, inspect)
                            i += 1
                    save = True
                except WrongTemplateException as e:
                    Log.error(
                        "Invalid parameter substitution in {0} template", e.job_name)
                    raise
                except Exception:
                    Log.error("{0} submission failed", platform.name)
                    raise
        return save

    @staticmethod
    def monitor(expid, file_format, lst, filter_chunks, filter_status, filter_section, hide, txt_only=False,
                group_by=None, expand=list(), expand_status=list(), hide_groups=False, notransitive=False, check_wrapper=False, txt_logfiles=False, detail=False):
        """
        Plots workflow graph for a given experiment with status of each job coded by node color.
        Plot is created in experiment's plot folder with name <expid>_<date>_<time>.<file_format>

        :type file_format: str
        :type expid: str
        :param expid: identifier of the experiment to plot
        :param file_format: plot's file format. It can be pdf, png, ps or svg
        :param lst: list of jobs to change status
        :type lst: str
        :param filter_chunks: chunks to change status
        :type filter_chunks: str
        :param filter_status: current status of the jobs to change status
        :type filter_status: str
        :param filter_section: sections to change status
        :type filter_section: str
        :param hide: hides plot window
        :type hide: bool
        """

        exp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)
        Log.info("Getting job list...")
        as_conf = AutosubmitConfig(expid, BasicConfig, ConfigParserFactory())
        as_conf.check_conf_files(False)
        # Getting output type from configuration
        output_type = as_conf.get_output_type()
        pkl_dir = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, 'pkl')
        job_list = Autosubmit.load_job_list(
            expid, as_conf, notransitive=notransitive, monitor=True)
        Log.debug("Job list restored from {0} files", pkl_dir)

        if not isinstance(job_list, type([])):
            jobs = []
            if filter_chunks:
                fc = filter_chunks
                Log.debug(fc)

                if fc == 'Any':
                    jobs = job_list.get_job_list()
                else:
                    # noinspection PyTypeChecker
                    data = json.loads(Autosubmit._create_json(fc))
                    for date_json in data['sds']:
                        date = date_json['sd']
                        jobs_date = filter(lambda j: date2str(
                            j.date) == date, job_list.get_job_list())

                        for member_json in date_json['ms']:
                            member = member_json['m']
                            jobs_member = filter(
                                lambda j: j.member == member, jobs_date)

                            for chunk_json in member_json['cs']:
                                chunk = int(chunk_json)
                                jobs = jobs + \
                                    [job for job in filter(
                                        lambda j: j.chunk == chunk, jobs_member)]

            elif filter_status:
                Log.debug("Filtering jobs with status {0}", filter_status)
                if filter_status == 'Any':
                    jobs = job_list.get_job_list()
                else:
                    fs = Autosubmit._get_status(filter_status)
                    jobs = [job for job in filter(
                        lambda j: j.status == fs, job_list.get_job_list())]

            elif filter_section:
                ft = filter_section
                Log.debug(ft)

                if ft == 'Any':
                    jobs = job_list.get_job_list()
                else:
                    for job in job_list.get_job_list():
                        if job.section == ft:
                            jobs.append(job)

            elif lst:
                jobs_lst = lst.split()

                if jobs == 'Any':
                    jobs = job_list.get_job_list()
                else:
                    for job in job_list.get_job_list():
                        if job.name in jobs_lst:
                            jobs.append(job)
            else:
                jobs = job_list.get_job_list()

        referenced_jobs_to_remove = set()
        for job in jobs:
            for child in job.children:
                if child not in jobs:
                    referenced_jobs_to_remove.add(child)
            for parent in job.parents:
                if parent not in jobs:
                    referenced_jobs_to_remove.add(parent)

        for job in jobs:
            job.children = job.children - referenced_jobs_to_remove
            job.parents = job.parents - referenced_jobs_to_remove
        # WRAPPERS
        if as_conf.get_wrapper_type() != 'none' and check_wrapper:
            # Class constructor creates table if it does not exist
            packages_persistence = JobPackagePersistence(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl"),
                                                         "job_packages_" + expid)
            # Permissons
            os.chmod(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid,
                                  "pkl", "job_packages_" + expid + ".db"), 0644)
            # Database modification
            packages_persistence.reset_table(True)
            referenced_jobs_to_remove = set()
            job_list_wrappers = copy.deepcopy(job_list)
            jobs_wr_aux = copy.deepcopy(jobs)
            jobs_wr = []
            [jobs_wr.append(job) for job in jobs_wr_aux if (
                job.status == Status.READY or job.status == Status.WAITING)]
            for job in jobs_wr:
                for child in job.children:
                    if child not in jobs_wr:
                        referenced_jobs_to_remove.add(child)
                for parent in job.parents:
                    if parent not in jobs_wr:
                        referenced_jobs_to_remove.add(parent)

            for job in jobs_wr:
                job.children = job.children - referenced_jobs_to_remove
                job.parents = job.parents - referenced_jobs_to_remove
            Autosubmit.generate_scripts_andor_wrappers(as_conf, job_list_wrappers, jobs_wr,
                                                       packages_persistence, True)

            packages = packages_persistence.load(True)
            packages += JobPackagePersistence(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl"),
                                              "job_packages_" + expid).load()
        else:
            packages = JobPackagePersistence(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl"),
                                             "job_packages_" + expid).load()

        groups_dict = dict()
        if group_by:
            status = list()
            if expand_status:
                for s in expand_status.split():
                    status.append(Autosubmit._get_status(s.upper()))

            job_grouping = JobGrouping(group_by, copy.deepcopy(
                jobs), job_list, expand_list=expand, expanded_status=status)
            groups_dict = job_grouping.group_jobs()

        monitor_exp = Monitor()

        if txt_only or txt_logfiles:
            monitor_exp.generate_output_txt(expid, jobs, os.path.join(
                exp_path, "/tmp/LOG_"+expid), txt_logfiles, job_list_object=job_list)
        else:
            # if file_format is set, use file_format, otherwise use conf value
            monitor_exp.generate_output(expid,
                                        jobs,
                                        os.path.join(
                                            exp_path, "/tmp/LOG_", expid),
                                        output_format=file_format if file_format is not None else output_type,
                                        packages=packages,
                                        show=not hide,
                                        groups=groups_dict,
                                        hide_groups=hide_groups,
                                        job_list_object=job_list)

        if detail:
            current_length = len(job_list.get_job_list())
            if current_length > 1000:
                Log.warning(
                    "-d option: Experiment has too many jobs to be printed in the terminal. Maximum job quantity is 1000, your experiment has " + str(current_length) + " jobs.")
            else:
                Log.info(job_list.print_with_status())
                Log.status(job_list.print_with_status())

        return True

    @staticmethod
    def statistics(expid, filter_type, filter_period, file_format, hide, notransitive=False):
        """
        Plots statistics graph for a given experiment.
        Plot is created in experiment's plot folder with name <expid>_<date>_<time>.<file_format>

        :type file_format: str
        :type expid: str
        :param expid: identifier of the experiment to plot
        :param filter_type: type of the jobs to plot
        :param filter_period: period to plot
        :param file_format: plot's file format. It can be pdf, png, ps or svg
        :param hide: hides plot window
        :type hide: bool
        """
        exp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)
        Log.info("Loading jobs...")
        as_conf = AutosubmitConfig(expid, BasicConfig, ConfigParserFactory())
        as_conf.check_conf_files(False)


        pkl_dir = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, 'pkl')
        job_list = Autosubmit.load_job_list(
            expid, as_conf, notransitive=notransitive)
        Log.debug("Job list restored from {0} files", pkl_dir)

        if filter_type:
            ft = filter_type
            Log.debug(ft)
            if ft == 'Any':
                job_list = job_list.get_job_list()
            else:
                job_list = [job for job in job_list.get_job_list()
                            if job.section == ft]
        else:
            ft = 'Any'
            job_list = job_list.get_job_list()

        period_fi = datetime.datetime.now().replace(second=0, microsecond=0)
        if filter_period:
            period_ini = period_fi - datetime.timedelta(hours=filter_period)
            Log.debug(str(period_ini))
            job_list = [job for job in job_list if
                        job.check_started_after(period_ini) or job.check_running_after(period_ini)]
        else:
            period_ini = None

        if len(job_list) > 0:
            try:
                Log.info("Plotting stats...")
                monitor_exp = Monitor()
                # noinspection PyTypeChecker
                monitor_exp.generate_output_stats(
                    expid, job_list, file_format, period_ini, period_fi, not hide)
                Log.result("Stats plot ready")
            except Exception as e:
                raise AutosubmitCritical("Stats couldn't be shown",7061,e.message)
        else:
            Log.info("There are no {0} jobs in the period from {1} to {2}...".format(
                ft, period_ini, period_fi))
        return True

    @staticmethod
    def clean(expid, project, plot, stats):
        """
        Clean experiment's directory to save storage space.
        It removes project directory and outdated plots or stats.

        :param create_log_file: if true, creates log file
        :type create_log_file: bool
        :type plot: bool
        :type project: bool
        :type expid: str
        :type stats: bool
        :param expid: identifier of experiment to clean
        :param project: set True to delete project directory
        :param plot: set True to delete outdated plots
        :param stats: set True to delete outdated stats
        """
        exp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)

        if project:
            autosubmit_config = AutosubmitConfig(
                expid, BasicConfig, ConfigParserFactory())
            autosubmit_config.check_conf_files(False)

            project_type = autosubmit_config.get_project_type()
            if project_type == "git":
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
    def recovery(expid, noplot, save, all_jobs, hide, group_by=None, expand=list(), expand_status=list(),
                 notransitive=False, no_recover_logs=False, detail=False):
        """
        Method to check all active jobs. If COMPLETED file is found, job status will be changed to COMPLETED,
        otherwise it will be set to WAITING. It will also update the jobs list.

        :param expid: identifier of the experiment to recover
        :type expid: str
        :param save: If true, recovery saves changes to the jobs list
        :type save: bool
        :param all_jobs: if True, it tries to get completed files for all jobs, not only active.
        :type all_jobs: bool
        :param hide: hides plot window
        :type hide: bool
        """
        Autosubmit._check_ownership(expid)

        exp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)

        as_conf = AutosubmitConfig(expid, BasicConfig, ConfigParserFactory())
        as_conf.check_conf_files(False)

        Log.info('Recovering experiment {0}'.format(expid))
        pkl_dir = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, 'pkl')
        job_list = Autosubmit.load_job_list(
            expid, as_conf, notransitive=notransitive, monitor=True)
        Log.debug("Job list restored from {0} files", pkl_dir)

        as_conf.check_conf_files(False)

        # Getting output type provided by the user in config, 'pdf' as default
        output_type = as_conf.get_output_type()
        hpcarch = as_conf.get_platform()

        submitter = Autosubmit._get_submitter(as_conf)
        submitter.load_platforms(as_conf)
        if submitter.platforms is None:
            return False
        platforms = submitter.platforms

        platforms_to_test = set()
        for job in job_list.get_job_list():
            job.submitter = submitter
            if job.platform_name is None:
                job.platform_name = hpcarch
            # noinspection PyTypeChecker
            job.platform = platforms[job.platform_name.lower()]
            # noinspection PyTypeChecker
            platforms_to_test.add(platforms[job.platform_name.lower()])

        if all_jobs:
            jobs_to_recover = job_list.get_job_list()
        else:
            jobs_to_recover = job_list.get_active()

        Log.info("Looking for COMPLETED files")
        start = datetime.datetime.now()
        for job in jobs_to_recover:
            if job.platform_name is None:
                job.platform_name = hpcarch
            # noinspection PyTypeChecker
            job.platform = platforms[job.platform_name.lower()]

            if job.platform.get_completed_files(job.name, 0, True):
                job.status = Status.COMPLETED
                Log.info("CHANGED job '{0}' status to COMPLETED".format(job.name))
                Log.status("CHANGED job '{0}' status to COMPLETED".format(job.name))

                if not no_recover_logs:
                    try:
                        job.platform.get_logs_files(expid, job.remote_logs)
                    except:
                        pass
            elif job.status != Status.SUSPENDED:
                job.status = Status.WAITING
                job.fail_count = 0
                Log.info("CHANGED job '{0}' status to WAITING".format(job.name))
                Log.status("CHANGED job '{0}' status to WAITING".format(job.name))


        end = datetime.datetime.now()
        Log.info("Time spent: '{0}'".format(end - start))
        Log.info("Updating the jobs list")
        job_list.update_list(as_conf)

        if save:
            job_list.save()
        else:
            Log.warning(
                'Changes NOT saved to the jobList. Use -s option to save')

        Log.result("Recovery finalized")

        packages = JobPackagePersistence(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl"),
                                         "job_packages_" + expid).load()

        groups_dict = dict()
        if group_by:
            status = list()
            if expand_status:
                for s in expand_status.split():
                    status.append(Autosubmit._get_status(s.upper()))

            job_grouping = JobGrouping(group_by, copy.deepcopy(job_list.get_job_list()), job_list, expand_list=expand,
                                       expanded_status=status)
            groups_dict = job_grouping.group_jobs()

        if not noplot:
            Log.info("\nPlotting the jobs list...")
            monitor_exp = Monitor()
            monitor_exp.generate_output(expid,
                                        job_list.get_job_list(),
                                        os.path.join(
                                            exp_path, "/tmp/LOG_", expid),
                                        output_format=output_type,
                                        packages=packages,
                                        show=not hide,
                                        groups=groups_dict,
                                        job_list_object=job_list)

        if detail == True:
            current_length = len(job_list.get_job_list())
            if current_length > 1000:
                Log.warning(
                    "-d option: Experiment has too many jobs to be printed in the terminal. Maximum job quantity is 1000, your experiment has " + str(current_length) + " jobs.")
            else:
                Log.info(job_list.print_with_status())
                Log.status(job_list.print_with_status())
        return True

    @staticmethod
    def migrate(experiment_id, offer, pickup):
        """
        Migrates experiment files from current to other user.
        It takes mapping information for new user from config files.

        :param experiment_id: experiment identifier:
        :param pickup:
        :param offer:
        """

        error = False
        if offer:
            Log.info('Migrating experiment {0}'.format(experiment_id))
            as_conf = AutosubmitConfig(
                experiment_id, BasicConfig, ConfigParserFactory())
            as_conf.check_conf_files(False)
            submitter = Autosubmit._get_submitter(as_conf)
            submitter.load_platforms(as_conf)
            if submitter.platforms is None:
                return False
            Log.info("Checking remote platforms")
            platforms = filter(lambda x: x not in [
                               'local', 'LOCAL'], submitter.platforms)
            already_moved = set()
            backup_files = []
            backup_conf = []
            for platform in platforms:
                # Checks
                Log.info(
                    "Checking [{0}] from platforms configuration...", platform)
                if not as_conf.get_migrate_user_to(platform):
                    Log.printlog(
                        "Missing directive USER_TO in [{0}]".format( platform),7014)
                    error = True
                    break
                if as_conf.get_migrate_project_to(platform):
                    Log.info("Project in platform configuration file successfully updated to {0}",
                             as_conf.get_current_project(platform))
                    as_conf.get_current_project(platform)
                    backup_conf.append([platform, as_conf.get_current_user(
                        platform), as_conf.get_current_project(platform)])
                    as_conf.set_new_user(
                        platform, as_conf.get_migrate_user_to(platform))

                    as_conf.set_new_project(
                        platform, as_conf.get_migrate_project_to(platform))
                    as_conf.get_current_project(platform)
                    as_conf.get_current_user(platform)
                else:
                    Log.info(
                        "[OPTIONAL] PROJECT_TO directive not found. The directive PROJECT will remain unchanged")
                    backup_conf.append(
                        [platform, as_conf.get_current_user(platform), None])
                    as_conf.set_new_user(
                        platform, as_conf.get_migrate_user_to(platform))
                    as_conf.get_current_project(platform)
                    as_conf.get_current_user(platform)

                if as_conf.get_migrate_host_to(platform) != "none":
                    Log.info(
                        "Host in platform configuration file successfully updated to {0}", as_conf.get_migrate_host_to(platform))
                    as_conf.set_new_host(
                        platform, as_conf.get_migrate_host_to(platform))
                else:
                    Log.warning(
                        "[OPTIONAL] HOST_TO directive not found. The directive HOST will remain unchanged")

                Log.info("Moving local files/dirs")
                p = submitter.platforms[platform]
                if p.temp_dir not in already_moved:
                    if p.root_dir != p.temp_dir and len(p.temp_dir) > 0:
                        already_moved.add(p.temp_dir)
                        Log.info("Converting abs symlink to relative")
                        # find /home/bsc32/bsc32070/dummy3 -type l -lname '/*' -printf ' ln -sf "$(realpath -s --relative-to="%p" $(readlink "%p")")" \n' > script.sh

                        Log.info(
                            "Converting the absolute symlinks into relatives on platform {0} ", platform)
                        #command = "find " + p.root_dir + " -type l -lname \'/*\' -printf 'var=\"$(realpath -s --relative-to=\"%p\" \"$(readlink \"%p\")\")\" && var=${var:3} && ln -sf $var \"%p\"  \\n'"
                        if p.root_dir.find(experiment_id) < 0:
                            Log.error(
                                "[Aborting] it is not safe to change symlinks in {0} due an invalid expid", p.root_dir)
                            error = True
                            break
                        command = "find " + p.root_dir + \
                            " -type l -lname \'/*\' -printf 'var=\"$(realpath -s --relative-to=\"%p\" \"$(readlink \"%p\")\")\" && var=${var:3} && ln -sf $var \"%p\"  \\n' "
                        try:
                            p.send_command(command, True)
                            if p.get_ssh_output().startswith("var="):
                                convertLinkPath = os.path.join(
                                    BasicConfig.LOCAL_ROOT_DIR, experiment_id, BasicConfig.LOCAL_TMP_DIR, 'convertLink.sh')
                                with open(convertLinkPath, 'w') as convertLinkFile:
                                    convertLinkFile.write(p.get_ssh_output())
                                p.send_file("convertLink.sh")
                                convertLinkPathRemote = os.path.join(
                                    p.remote_log_dir, "convertLink.sh")
                                command = "chmod +x " + convertLinkPathRemote + " && " + \
                                    convertLinkPathRemote + " && rm " + convertLinkPathRemote
                                Log.info(
                                    "Converting absolute symlinks this can take a while depending on the experiment size ")
                                p.send_command(command, True)
                        except IOError:
                            Log.debug(
                                "The platform {0} does not contain absolute symlinks", platform)
                        except BaseException:
                            Log.printlog(
                                "Absolute symlinks failed to convert, check user in platform.conf",3000)
                            error = True
                            break

                        try:
                            Log.info(
                                "Moving remote files/dirs on {0}", platform)
                            p.send_command("chmod 777 -R " + p.root_dir)
                            if not p.move_file(p.root_dir, os.path.join(p.temp_dir, experiment_id), True):
                                Log.printlog(
                                    "The files/dirs on {0} cannot be moved to {1}.".format(p.root_dir,
                                             os.path.join(p.temp_dir, experiment_id), 6012))
                                error = True
                                break
                        except (IOError, BaseException) as e:
                            Log.printlog("The files/dirs on {0} cannot be moved to {1}.".format(p.root_dir,
                                         os.path.join(p.temp_dir, experiment_id)),6012)
                            error = True
                            break

                        backup_files.append(platform)
                Log.result(
                    "Files/dirs on {0} have been successfully offered", platform)
                Log.result("[{0}] from platforms configuration OK", platform)

            if error:
                Log.printlog(
                    "The experiment cannot be offered, reverting changes",7012)
                as_conf = AutosubmitConfig(
                    experiment_id, BasicConfig, ConfigParserFactory())
                as_conf.check_conf_files(False)
                for platform in backup_files:
                    p = submitter.platforms[platform]
                    p.move_file(os.path.join(
                        p.temp_dir, experiment_id), p.root_dir, True)
                for platform in backup_conf:
                    as_conf.set_new_user(platform[0], platform[1])
                    if platform[2] is not None:
                        as_conf.set_new_project(platform[0], platform[2])
                    if as_conf.get_migrate_host_to(platform[0]) != "none":
                        as_conf.set_new_host(
                            platform[0], as_conf.get_migrate_host_to(platform[0]))
                return False
            else:
                if not Autosubmit.archive(experiment_id, False, False):
                    Log.printlog(
                        "The experiment cannot be offered, reverting changes", 7012)
                    for platform in backup_files:
                        p = submitter.platforms[platform]
                        p.move_file(os.path.join(
                            p.temp_dir, experiment_id), p.root_dir, True)
                    for platform in backup_conf:
                        as_conf.set_new_user(platform[0], platform[1])
                        if platform[2] is not None:
                            as_conf.set_new_project(platform[0], platform[2])

                    return False
                else:

                    Log.result("The experiment has been successfully offered.")

        elif pickup:
            Log.info('Migrating experiment {0}'.format(experiment_id))
            Log.info("Moving local files/dirs")
            if not Autosubmit.unarchive(experiment_id, False):
                raise AutosubmitCritical("The experiment cannot be picked up",7012)
            Log.info("Local files/dirs have been successfully picked up")
            as_conf = AutosubmitConfig(
                experiment_id, BasicConfig, ConfigParserFactory())
            as_conf.check_conf_files(False)
            Log.info("Checking remote platforms")
            submitter = Autosubmit._get_submitter(as_conf)
            submitter.load_platforms(as_conf)
            if submitter.platforms is None:
                return False
            platforms = filter(lambda x: x not in [
                               'local', 'LOCAL'], submitter.platforms)
            already_moved = set()
            backup_files = []
            for platform in platforms:
                p = submitter.platforms[platform]
                if p.temp_dir not in already_moved:
                    if p.root_dir != p.temp_dir and len(p.temp_dir) > 0:
                        already_moved.add(p.temp_dir)
                        Log.info("Copying remote files/dirs on {0}", platform)
                        Log.info("Copying from {0} to {1}", os.path.join(
                            p.temp_dir, experiment_id), p.root_dir)
                        try:
                            p.send_command(
                                "cp -rP " + os.path.join(p.temp_dir, experiment_id) + " " + p.root_dir)
                            p.send_command("chmod 755 -R "+p.root_dir)
                            Log.result(
                                "Files/dirs on {0} have been successfully picked up", platform)
                        except (IOError, BaseException):
                            error = True
                            Log.printlog("The files/dirs on {0} cannot be copied to {1}.".format(os.path.join(p.temp_dir, experiment_id), p.root_dir),6012)
                            break
                        backup_files.append(platform)
                    else:
                        Log.result(
                            "Files/dirs on {0} have been successfully picked up", platform)
            if error:
                Autosubmit.archive(experiment_id, False, False)
                Log.printlog(
                    "The experiment cannot be picked,reverting changes.",7012)
                for platform in backup_files:
                    p = submitter.platforms[platform]
                    p.send_command("rm -R " + p.root_dir)
                return False
            else:
                for platform in backup_files:
                    p = submitter.platforms[platform]
                    p.send_command("rm -R " + p.temp_dir+"/"+experiment_id)
                Log.result("The experiment has been successfully picked up.")
                #Log.info("Refreshing the experiment.")
                # Autosubmit.refresh(experiment_id,False,False)
                return True

    @staticmethod
    def check(experiment_id, notransitive=False):
        """
        Checks experiment configuration and warns about any detected error or inconsistency.

        :param experiment_id: experiment identifier:
        :type experiment_id: str
        """
        exp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, experiment_id)

        as_conf = AutosubmitConfig(
            experiment_id, BasicConfig, ConfigParserFactory())
        as_conf.check_conf_files(False)


        project_type = as_conf.get_project_type()

        submitter = Autosubmit._get_submitter(as_conf)
        submitter.load_platforms(as_conf)
        if len(submitter.platforms) == 0:
            return False

        pkl_dir = os.path.join(
            BasicConfig.LOCAL_ROOT_DIR, experiment_id, 'pkl')
        job_list = Autosubmit.load_job_list(
            experiment_id, as_conf, notransitive=notransitive)
        Log.debug("Job list restored from {0} files", pkl_dir)

        Autosubmit._load_parameters(as_conf, job_list, submitter.platforms)

        hpc_architecture = as_conf.get_platform()
        for job in job_list.get_job_list():
            if job.platform_name is None:
                job.platform_name = hpc_architecture
            job.platform = submitter.platforms[job.platform_name.lower()]
            job.update_parameters(as_conf, job_list.parameters)

        return job_list.check_scripts(as_conf)

    @staticmethod
    def describe(experiment_id):
        """
        Show details for specified experiment

        :param experiment_id: experiment identifier:
        :type experiment_id: str
        """

        Log.info("Describing {0}", experiment_id)
        exp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, experiment_id)

        as_conf = AutosubmitConfig(
            experiment_id, BasicConfig, ConfigParserFactory())
        as_conf.check_conf_files(False)

        user = os.stat(as_conf.experiment_file).st_uid
        try:
            user = pwd.getpwuid(user).pw_name
        except:
            Log.warning(
                "The user does not exist anymore in the system, using id instead")

        created = datetime.datetime.fromtimestamp(
            os.path.getmtime(as_conf.experiment_file))

        project_type = as_conf.get_project_type()
        if (as_conf.get_svn_project_url()):
            model = as_conf.get_svn_project_url()
            branch = as_conf.get_svn_project_url()
        else:
            model = as_conf.get_git_project_origin()
            branch = as_conf.get_git_project_branch()
        if model is "":
            model = "Not Found"
        if branch is "":
            branch = "Not Found"

        submitter = Autosubmit._get_submitter(as_conf)
        submitter.load_platforms(as_conf)
        if len(submitter.platforms) == 0:
            return False
        hpc = as_conf.get_platform()

        Log.result("Owner: {0}", user)
        Log.result("Created: {0}", created)
        Log.result("Model: {0}", model)
        Log.result("Branch: {0}", branch)
        Log.result("HPC: {0}", hpc)
        return user, created, model, branch, hpc

    @staticmethod
    def configure(advanced, database_path, database_filename, local_root_path, platforms_conf_path, jobs_conf_path,
                  smtp_hostname, mail_from, machine, local):
        """
        Configure several paths for autosubmit: database, local root and others. Can be configured at system,
        user or local levels. Local level configuration precedes user level and user level precedes system
        configuration.

        :param database_path: path to autosubmit database
        :type database_path: str
        :param database_filename: database filename
        :type database_filename: str
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
        :param mail_from:
        :type mail_from: str
        :param smtp_hostname:
        :type smtp_hostname: str
        """
        home_path = os.path.expanduser('~')
        # Setting default values
        if not advanced and database_path is None and local_root_path is None:
            database_path = home_path
            local_root_path = home_path + '/autosubmit'
            database_filename = 'autosubmit.db'

        while database_path is None:
            database_path = raw_input("Introduce Database path: ")
        database_path = database_path.replace('~', home_path)
        if not os.path.exists(database_path):
            Log.error("Database path does not exist.")
            return False

        while local_root_path is None:
            local_root_path = raw_input("Introduce path to experiments: ")
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
            if smtp_hostname is not None or mail_from is not None:
                parser.add_section('mail')
                parser.set('mail', 'smtp_server', smtp_hostname)
                parser.set('mail', 'mail_from', mail_from)
            parser.write(config_file)
            config_file.close()
            Log.result("Configuration file written successfully")
        except (IOError, OSError) as e:
            raise AutosubmitCritical("Can not write config file: {0}",7012,e.message)
        return True

    @staticmethod
    def configure_dialog():
        """
        Configure several paths for autosubmit interactively: database, local root and others.
        Can be configured at system, user or local levels. Local level configuration precedes user level and user level
        precedes system configuration.
        """

        not_enough_screen_size_msg = 'The size of your terminal is not enough to draw the configuration wizard,\n' \
                                     'so we\'ve closed it to prevent errors. Resize it and then try it again.'

        home_path = os.path.expanduser('~')

        try:
            d = dialog.Dialog(
                dialog="dialog", autowidgetsize=True, screen_color='GREEN')
        except dialog.DialogError:
            raise AutosubmitCritical("Graphical visualization failed, not enough screen size",7060)
        except Exception:
            raise AutosubmitCritical("Dialog libs aren't found in your Operational system",7060)

        d.set_background_title("Autosubmit configure utility")
        if os.geteuid() == 0:
            text = ''
            choice = [
                ("All", "All users on this machine (may require root privileges)")]
        else:
            text = "If you want to configure Autosubmit for all users, you will need to provide root privileges"
            choice = []

        choice.append(("User", "Current user"))
        choice.append(
            ("Local", "Only when launching Autosubmit from this path"))

        try:
            code, level = d.menu(text, choices=choice, width=60,
                                 title="Choose when to apply the configuration")
            if code != dialog.Dialog.OK:
                os.system('clear')
                return False
        except dialog.DialogError:
            raise AutosubmitCritical("Graphical visualization failed, not enough screen size",7060)

        filename = '.autosubmitrc'
        if level == 'All':
            path = '/etc'
            filename = 'autosubmitrc'
        elif level == 'User':
            path = home_path
        else:
            path = '.'
        path = os.path.join(path, filename)

        # Setting default values
        database_path = home_path
        local_root_path = home_path
        database_filename = 'autosubmit.db'
        jobs_conf_path = ''
        platforms_conf_path = ''

        d.infobox("Reading configuration file...", width=50, height=5)
        try:
            if os.path.isfile(path):
                parser = SafeConfigParser()
                parser.optionxform = str
                parser.read(path)
                if parser.has_option('database', 'path'):
                    database_path = parser.get('database', 'path')
                if parser.has_option('database', 'filename'):
                    database_filename = parser.get('database', 'filename')
                if parser.has_option('local', 'path'):
                    local_root_path = parser.get('local', 'path')
                if parser.has_option('conf', 'platforms'):
                    platforms_conf_path = parser.get('conf', 'platforms')
                if parser.has_option('conf', 'jobs'):
                    jobs_conf_path = parser.get('conf', 'jobs')

        except (IOError, OSError) as e:
            raise AutosubmitCritical("Can not read config file",7014,e.message)

        while True:
            try:
                code, database_path = d.dselect(database_path, width=80, height=20,
                                                title='\Zb\Z1Select path to database\Zn', colors='enable')
            except dialog.DialogError:
                raise AutosubmitCritical("Graphical visualization failed, not enough screen size", 7060)
            if Autosubmit._requested_exit(code, d):
                raise AutosubmitCritical("Graphical visualization failed, requested exit", 7060)
            elif code == dialog.Dialog.OK:
                database_path = database_path.replace('~', home_path)
                if not os.path.exists(database_path):
                    d.msgbox(
                        "Database path does not exist.\nPlease, insert the right path", width=50, height=6)
                else:
                    break

        while True:
            try:
                code, local_root_path = d.dselect(local_root_path, width=80, height=20,
                                                  title='\Zb\Z1Select path to experiments repository\Zn',
                                                  colors='enable')
            except dialog.DialogError:
                raise AutosubmitCritical("Graphical visualization failed, not enough screen size",7060)


            if Autosubmit._requested_exit(code, d):
                raise AutosubmitCritical("Graphical visualization failed,requested exit",7060)
            elif code == dialog.Dialog.OK:
                database_path = database_path.replace('~', home_path)
                if not os.path.exists(database_path):
                    d.msgbox(
                        "Local root path does not exist.\nPlease, insert the right path", width=50, height=6)
                else:
                    break
        while True:
            try:
                (code, tag) = d.form(text="",
                                     elements=[("Database filename", 1, 1, database_filename, 1, 40, 20, 20),
                                               (
                                                   "Default platform.conf path", 2, 1, platforms_conf_path, 2, 40, 40,
                                                   200),
                                               ("Default jobs.conf path", 3, 1, jobs_conf_path, 3, 40, 40, 200)],
                                     height=20,
                                     width=80,
                                     form_height=10,
                                     title='\Zb\Z1Just a few more options:\Zn', colors='enable')
            except dialog.DialogError:
                raise AutosubmitCritical("Graphical visualization failed, not enough screen size",7060)

            if Autosubmit._requested_exit(code, d):
                raise AutosubmitCritical("Graphical visualization failed, _requested_exit", 7060)
            elif code == dialog.Dialog.OK:
                database_filename = tag[0]
                platforms_conf_path = tag[1]
                jobs_conf_path = tag[2]

                platforms_conf_path = platforms_conf_path.replace(
                    '~', home_path).strip()
                jobs_conf_path = jobs_conf_path.replace('~', home_path).strip()

                if platforms_conf_path and not os.path.exists(platforms_conf_path):
                    d.msgbox(
                        "Platforms conf path does not exist.\nPlease, insert the right path", width=50, height=6)
                elif jobs_conf_path and not os.path.exists(jobs_conf_path):
                    d.msgbox(
                        "Jobs conf path does not exist.\nPlease, insert the right path", width=50, height=6)
                else:
                    break

        smtp_hostname = "mail.bsc.es"
        mail_from = "automail@bsc.es"
        while True:
            try:
                (code, tag) = d.form(text="",
                                     elements=[("STMP server hostname", 1, 1, smtp_hostname, 1, 40, 20, 20),
                                               ("Notifications sender address", 2, 1, mail_from, 2, 40, 40, 200)],
                                     height=20,
                                     width=80,
                                     form_height=10,
                                     title='\Zb\Z1Mail notifications configuration:\Zn', colors='enable')
            except dialog.DialogError:
                raise AutosubmitCritical("Graphical visualization failed, not enough screen size", 7060)

            if Autosubmit._requested_exit(code, d):
                raise AutosubmitCritical("Graphical visualization failed, requested exit", 7060)
            elif code == dialog.Dialog.OK:
                smtp_hostname = tag[0]
                mail_from = tag[1]
                break
                # TODO: Check that is a valid config?

        config_file = open(path, 'w')
        d.infobox("Writing configuration file...", width=50, height=5)
        try:
            parser = SafeConfigParser()
            parser.add_section('database')
            parser.set('database', 'path', database_path)
            if database_filename:
                parser.set('database', 'filename', database_filename)
            parser.add_section('local')
            parser.set('local', 'path', local_root_path)
            if jobs_conf_path or platforms_conf_path:
                parser.add_section('conf')
                if jobs_conf_path:
                    parser.set('conf', 'jobs', jobs_conf_path)
                if platforms_conf_path:
                    parser.set('conf', 'platforms', platforms_conf_path)
            parser.add_section('mail')
            parser.set('mail', 'smtp_server', smtp_hostname)
            parser.set('mail', 'mail_from', mail_from)
            parser.write(config_file)
            config_file.close()
            d.msgbox("Configuration file written successfully",
                     width=50, height=5)
            os.system('clear')
        except (IOError, OSError) as e:
            raise AutosubmitCritical("Can not write config file", 7012,e.message)
        return True

    @staticmethod
    def _requested_exit(code, d):
        if code != dialog.Dialog.OK:
            code = d.yesno(
                'Exit configure utility without saving?', width=50, height=5)
            if code == dialog.Dialog.OK:
                os.system('clear')
                return True
        return False

    @staticmethod
    def install():
        """
        Creates a new database instance for autosubmit at the configured path

        """
        if not os.path.exists(BasicConfig.DB_PATH):
            Log.info("Creating autosubmit database...")
            qry = resource_string('autosubmit.database', 'data/autosubmit.sql')
            if not create_db(qry):
                raise AutosubmitCritical("Can not write database file", 7004)
            Log.result("Autosubmit database created successfully")
        else:
            raise AutosubmitCritical("Database already exists.", 7004)
        return True

    @staticmethod
    def refresh(expid, model_conf, jobs_conf):
        """
        Refresh project folder for given experiment

        :param model_conf:
        :type model_conf: bool
        :param jobs_conf:
        :type jobs_conf: bool
        :param expid: experiment identifier
        :type expid: str
        """
        Autosubmit._check_ownership(expid)
        as_conf = AutosubmitConfig(expid, BasicConfig, ConfigParserFactory())
        as_conf.reload()
        as_conf.check_conf_files()
        if "Expdef" in as_conf.wrong_config:
            as_conf.show_messages()
        project_type = as_conf.get_project_type()
        if Autosubmit._copy_code(as_conf, expid, project_type, True):
            Log.result("Project folder updated")
        Autosubmit._create_project_associated_conf(
            as_conf, model_conf, jobs_conf)
        return True

    @staticmethod
    def update_version(expid):
        """
        Refresh experiment version with the current autosubmit version
        :param expid: experiment identifier
        :type expid: str
        """
        Autosubmit._check_ownership(expid)

        as_conf = AutosubmitConfig(expid, BasicConfig, ConfigParserFactory())
        as_conf.reload()
        as_conf.check_expdef_conf(False)

        Log.info("Changing {0} experiment version from {1} to  {2}",
                 expid, as_conf.get_version(), Autosubmit.autosubmit_version)
        as_conf.set_version(Autosubmit.autosubmit_version)
        return True

    @staticmethod
    def archive(expid, clean=True, compress=True):
        """
        Archives an experiment: call clean (if experiment is of version 3 or later), compress folder
        to tar.gz and moves to year's folder

        :param clean,compress:
        :return:
        :param expid: experiment identifier
        :type expid: str
        """

        exp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)

        exp_folder = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)

        if clean:
            # Cleaning to reduce file size.
            version = get_autosubmit_version(expid)
            if version is not None and version.startswith('3') and not Autosubmit.clean(expid, True, True, True, False):
                raise AutosubmitCritical("Can not archive project. Clean not successful", 7012)

        # Getting year of last completed. If not, year of expid folder
        year = None
        tmp_folder = os.path.join(exp_folder, BasicConfig.LOCAL_TMP_DIR)
        if os.path.isdir(tmp_folder):
            for filename in os.listdir(tmp_folder):
                if filename.endswith("COMPLETED"):
                    file_year = time.localtime(os.path.getmtime(
                        os.path.join(tmp_folder, filename))).tm_year
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
                os.chmod(year_path, 0o755)
            if compress:
                compress_type = "w:gz"
                output_filepath = '{0}.tar.gz'.format(expid)
            else:
                compress_type = "w"
                output_filepath = '{0}.tar'.format(expid)
            with tarfile.open(os.path.join(year_path, output_filepath), compress_type) as tar:
                tar.add(exp_folder, arcname='')
                tar.close()
                os.chmod(os.path.join(year_path, output_filepath), 0o755)
        except Exception as e:
            raise AutosubmitCritical("Can not write tar file", 7012,e.message)


        Log.info("Tar file created!")

        try:
            shutil.rmtree(exp_folder)
        except Exception as e:
            Log.warning(
                "Can not fully remove experiments folder: {0}".format(e))
            if os.stat(exp_folder):
                try:
                    tmp_folder = os.path.join(
                        BasicConfig.LOCAL_ROOT_DIR, "tmp")
                    tmp_expid = os.path.join(tmp_folder, expid+"_to_delete")
                    os.rename(exp_folder, tmp_expid)
                    Log.warning("Experiment folder renamed to: {0}".format(
                        exp_folder+"_to_delete "))
                except Exception as e:

                    Autosubmit.unarchive(expid, compress, True)
                    raise AutosubmitCritical("Can not remove or rename experiments folder",7012,e.message)

        Log.result("Experiment archived successfully")
        return True

    @staticmethod
    def unarchive(experiment_id, compress=True, overwrite=False):
        """
        Unarchives an experiment: uncompress folder from tar.gz and moves to experiments root folder

        :param experiment_id: experiment identifier
        :type experiment_id: str
        :type compress: boolean
        :type overwrite: boolean
        """
        exp_folder = os.path.join(BasicConfig.LOCAL_ROOT_DIR, experiment_id)

        # Searching by year. We will store it on database
        year = datetime.datetime.today().year
        archive_path = None
        if compress:
            compress_type = "r:gz"
            output_pathfile = '{0}.tar.gz'.format(experiment_id)
        else:
            compress_type = "r:"
            output_pathfile = '{0}.tar'.format(experiment_id)
        while year > 2000:
            archive_path = os.path.join(
                BasicConfig.LOCAL_ROOT_DIR, str(year), output_pathfile)
            if os.path.exists(archive_path):
                break
            year -= 1

        if year == 2000:
            Log.error("Experiment {0} is not archived", experiment_id)
            return False
        Log.info("Experiment located in {0} archive", year)

        # Creating tar file
        Log.info("Unpacking tar file ... ")
        if not os.path.isdir(exp_folder):
            os.mkdir(exp_folder)
        try:
            with tarfile.open(os.path.join(archive_path), compress_type) as tar:
                tar.extractall(exp_folder)
                tar.close()
        except Exception as e:
            shutil.rmtree(exp_folder, ignore_errors=True)
            Log.printlog("Can not extract tar file: {0}".format(e),6012)
            return False

        Log.info("Unpacking finished")

        try:
            os.remove(archive_path)
        except Exception as e:
            Log.printlog("Can not remove archived file folder: {0}".format(e),7012)
            return False

        Log.result("Experiment {0} unarchived successfully", experiment_id)
        return True

    @staticmethod
    def _create_project_associated_conf(as_conf, force_model_conf, force_jobs_conf):
        project_destiny = as_conf.project_file
        jobs_destiny = as_conf.jobs_file

        if as_conf.get_project_type() != 'none':
            if as_conf.get_file_project_conf():
                copy = True
                if os.path.exists(project_destiny):
                    if force_model_conf:
                        os.remove(project_destiny)
                    else:
                        copy = False
                if copy:
                    shutil.copyfile(os.path.join(as_conf.get_project_dir(), as_conf.get_file_project_conf()),
                                    project_destiny)

            if as_conf.get_file_jobs_conf():
                copy = True
                if os.path.exists(jobs_destiny):
                    if force_jobs_conf:
                        os.remove(jobs_destiny)
                    else:
                        copy = False
                if copy:
                    shutil.copyfile(os.path.join(as_conf.get_project_dir(), as_conf.get_file_jobs_conf()),
                                    jobs_destiny)

    @staticmethod
    def create(expid, noplot, hide, output='pdf', group_by=None, expand=list(), expand_status=list(), notransitive=False, check_wrappers=False, detail=False):
        """
        Creates job list for given experiment. Configuration files must be valid before realizing this process.

        :param expid: experiment identifier
        :type expid: str
        :param noplot: if True, method omits final plotting of the jobs list. Only needed on large experiments when
        plotting time can be much larger than creation time.
        :type noplot: bool
        :return: True if successful, False if not
        :rtype: bool
        :param hide: hides plot window
        :type hide: bool
        :param hide: hides plot window
        :type hide: bool
        :param output: plot's file format. It can be pdf, png, ps or svg
        :type output: str

        """
        Autosubmit._check_ownership(expid)
        exp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)
        tmp_path = os.path.join(exp_path, BasicConfig.LOCAL_TMP_DIR)

        # checking if there is a lock file to avoid multiple running on the same expid
        try:
            # Encapsulating the lock
            with portalocker.Lock(os.path.join(tmp_path, 'autosubmit.lock'), timeout=1) as fh:
                try:
                    Log.info("Preparing .lock file to avoid multiple instances with same expid.")

                    as_conf = AutosubmitConfig(expid, BasicConfig, ConfigParserFactory())
                    as_conf.check_conf_files(False)
                    project_type = as_conf.get_project_type()
                    # Getting output type provided by the user in config, 'pdf' as default
                    output_type = as_conf.get_output_type()

                    if not Autosubmit._copy_code(as_conf, expid, project_type, False):
                        return False
                    update_job = not os.path.exists(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl",
                                                                 "job_list_" + expid + ".pkl"))
                    Autosubmit._create_project_associated_conf(
                        as_conf, False, update_job)


                    # Load parameters
                    Log.info("Loading parameters...")
                    parameters = as_conf.load_parameters()

                    date_list = as_conf.get_date_list()
                    if len(date_list) != len(set(date_list)):
                        raise AutosubmitCritical('There are repeated start dates!',7014)
                    num_chunks = as_conf.get_num_chunks()
                    chunk_ini = as_conf.get_chunk_ini()
                    member_list = as_conf.get_member_list()
                    if len(member_list) != len(set(member_list)):
                        raise AutosubmitCritical("There are repeated member names!")
                    rerun = as_conf.get_rerun()

                    Log.info("\nCreating the jobs list...")
                    job_list = JobList(expid, BasicConfig, ConfigParserFactory(),
                                       Autosubmit._get_job_list_persistence(expid, as_conf))

                    date_format = ''
                    if as_conf.get_chunk_size_unit() is 'hour':
                        date_format = 'H'
                    for date in date_list:
                        if date.hour > 1:
                            date_format = 'H'
                        if date.minute > 1:
                            date_format = 'M'
                    job_list.generate(date_list, member_list, num_chunks, chunk_ini, parameters, date_format,
                                      as_conf.get_retrials(),
                                      as_conf.get_default_job_type(),
                                      as_conf.get_wrapper_type(), as_conf.get_wrapper_jobs(), notransitive=notransitive, update_structure=True)

                    if rerun == "true":
                        chunk_list = Autosubmit._create_json(
                            as_conf.get_chunk_list())
                        job_list.rerun(chunk_list, notransitive)
                    else:
                        job_list.remove_rerun_only_jobs(notransitive)
                    Log.info("\nSaving the jobs list...")
                    job_list.save()
                    JobPackagePersistence(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl"),
                                          "job_packages_" + expid).reset_table()

                    groups_dict = dict()

                    if not noplot:
                        if group_by:
                            status = list()
                            if expand_status:
                                for s in expand_status.split():
                                    status.append(
                                        Autosubmit._get_status(s.upper()))

                            job_grouping = JobGrouping(group_by, copy.deepcopy(job_list.get_job_list()), job_list,
                                                       expand_list=expand, expanded_status=status)
                            groups_dict = job_grouping.group_jobs()
                        # WRAPPERS
                        if as_conf.get_wrapper_type() != 'none' and check_wrappers:
                            packages_persistence = JobPackagePersistence(
                                os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl"), "job_packages_" + expid)
                            packages_persistence.reset_table(True)
                            referenced_jobs_to_remove = set()
                            job_list_wrappers = copy.deepcopy(job_list)
                            jobs_wr = job_list_wrappers.get_job_list()
                            for job in jobs_wr:
                                for child in job.children:
                                    if child not in jobs_wr:
                                        referenced_jobs_to_remove.add(child)
                                for parent in job.parents:
                                    if parent not in jobs_wr:
                                        referenced_jobs_to_remove.add(parent)

                            for job in jobs_wr:
                                job.children = job.children - referenced_jobs_to_remove
                                job.parents = job.parents - referenced_jobs_to_remove
                            Autosubmit.generate_scripts_andor_wrappers(
                                as_conf, job_list_wrappers, jobs_wr, packages_persistence, True)

                            packages = packages_persistence.load(True)
                        else:
                            packages = None

                        Log.info("\nPlotting the jobs list...")
                        monitor_exp = Monitor()
                        # if output is set, use output
                        monitor_exp.generate_output(expid, job_list.get_job_list(),
                                                    os.path.join(
                                                        exp_path, "/tmp/LOG_", expid),
                                                    output if output is not None else output_type,
                                                    packages,
                                                    not hide,
                                                    groups=groups_dict,
                                                    job_list_object=job_list)
                    Log.result("\nJob list created successfully")
                    Log.warning(
                        "Remember to MODIFY the MODEL config files!")
                    fh.flush()
                    os.fsync(fh.fileno())

                    # Detail after lock has been closed.
                    if detail == True:
                        current_length = len(job_list.get_job_list())
                        if current_length > 1000:
                            Log.warning(
                                "-d option: Experiment has too many jobs to be printed in the terminal. Maximum job quantity is 1000, your experiment has " + str(current_length) + " jobs.")
                        else:
                            Log.info(job_list.print_with_status())
                            Log.status(job_list.print_with_status())

                    return True
                # catching Exception
                except (KeyboardInterrupt) as e:
                    # Setting signal handler to handle subsequent CTRL-C
                    signal.signal(signal.SIGINT, signal_handler_create)
                    fh.flush()
                    os.fsync(fh.fileno())
                    raise AutosubmitCritical("Stopped by user input", 7010)
        except portalocker.AlreadyLocked:
            message = "We have detected that there is another Autosubmit instance using the experiment\n. Stop other Autosubmit instances that are using the experiment or delete autosubmit.lock file located on tmp folder"
            raise AutosubmitCritical(message,7000)
        except AutosubmitCritical as e:
            raise AutosubmitCritical(e.message,e.code)

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
            submitter = Autosubmit._get_submitter(as_conf)
            submitter.load_platforms(as_conf)
            try:
                hpcarch = submitter.platforms[as_conf.get_platform()]
            except:
                raise AutosubmitCritical("Can't set main platform",7014)
            return AutosubmitGit.clone_repository(as_conf, force, hpcarch)
        elif project_type == "svn":
            svn_project_url = as_conf.get_svn_project_url()
            svn_project_revision = as_conf.get_svn_project_revision()
            project_path = os.path.join(
                BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_PROJ_DIR)
            if os.path.exists(project_path):
                Log.info("Using project folder: {0}", project_path)
                if not force:
                    Log.debug("The project folder exists. SKIPPING...")
                    return True
                else:
                    shutil.rmtree(project_path, ignore_errors=True)
            os.mkdir(project_path)
            Log.debug("The project folder {0} has been created.", project_path)
            Log.info("Checking out revision {0} into {1}",
                     svn_project_revision + " " + svn_project_url, project_path)
            try:
                output = subprocess.check_output("cd " + project_path + "; svn --force-interactive checkout -r " +
                                                 svn_project_revision + " " + svn_project_url + " " +
                                                 project_destination, shell=True)
            except subprocess.CalledProcessError:

                shutil.rmtree(project_path, ignore_errors=True)
                raise AutosubmitCritical("Can not check out revision {0} into {1}".format(svn_project_revision + " " + svn_project_url,
                          project_path),7062)
            Log.debug("{0}", output)

        elif project_type == "local":
            local_project_path = as_conf.get_local_project_path()
            project_path = os.path.join(
                BasicConfig.LOCAL_ROOT_DIR, expid, BasicConfig.LOCAL_PROJ_DIR)
            local_destination = os.path.join(project_path, project_destination)

            if os.path.exists(project_path):
                Log.info("Using project folder: {0}", project_path)
                if os.path.exists(local_destination):
                    if force:
                        try:
                            cmd = ["rsync -ach --info=progress2 " +
                                   local_project_path+"/* "+local_destination]
                            subprocess.call(cmd, shell=True)
                        except subprocess.CalledProcessError:
                            raise AutosubmitCritical("Can not rsync {0} into {1}. Exiting...".format(
                                local_project_path, project_path), 7063)
                else:
                    os.mkdir(local_destination)
                    try:
                        output = subprocess.check_output(
                            "cp -R " + local_project_path + "/* " + local_destination, shell=True)
                    except subprocess.CalledProcessError:
                        shutil.rmtree(project_path)
                        raise AutosubmitCritical("Can not copy {0} into {1}. Exiting...".format(
                            local_project_path, project_path), 7063)
            else:
                os.mkdir(project_path)
                os.mkdir(local_destination)
                Log.debug(
                    "The project folder {0} has been created.", project_path)
                Log.info("Copying {0} into {1}",
                         local_project_path, project_path)
                try:
                    output = subprocess.check_output(
                        "cp -R " + local_project_path + "/* " + local_destination, shell=True)
                except subprocess.CalledProcessError:
                    shutil.rmtree(project_path)
                    raise AutosubmitCritical(
                        "Can not copy {0} into {1}. Exiting...".format( local_project_path, project_path), 7063)
                Log.debug("{0}", output)
        return True

    @staticmethod
    def change_status(final, final_status, job, save):
        """
        Set job status to final

        :param final:
        :param final_status:
        :param job:
        """

        if (job.status == Status.QUEUING or job.status == Status.HELD) and save and (final_status != Status.QUEUING and final_status != Status.HELD and final_status != Status.SUSPENDED):
            job.hold = False
            if job.platform_name is not None and job.platform_name.lower() != "local":
                job.platform.send_command(
                    job.platform.cancel_cmd + " " + str(job.id), ignore_log=True)
        elif (job.status == Status.QUEUING or job.status == Status.RUNNING or job.status == Status.SUBMITTED) and save and (final_status == Status.SUSPENDED):
            if job.platform_name is not None and job.platform_name.lower() != "local":
                job.platform.send_command(
                    "scontrol hold " + "{0}".format(job.id), ignore_log=True)
        elif (final_status == Status.QUEUING or final_status == Status.RUNNING) and save and (job.status == Status.SUSPENDED):
            if job.platform_name is not None and job.platform_name.lower() != "local":
                job.platform.send_command(
                    "scontrol release " + "{0}".format(job.id), ignore_log=True)
        job.status = final_status
        Log.info("CHANGED: job: " + job.name + " status to: " + final)
        Log.status("CHANGED: job: " + job.name + " status to: " + final)

    @staticmethod
    def set_status(expid, noplot, save, final, lst, filter_chunks, filter_status, filter_section, filter_type_chunk, hide, group_by=None,
                   expand=list(), expand_status=list(), notransitive=False, check_wrapper=False, detail=False):
        """
        Set status

        :param expid: experiment identifier
        :type expid: str
        :param save: if true, saves the new jobs list
        :type save: bool
        :param final: status to set on jobs
        :type final: str
        :param lst: list of jobs to change status
        :type lst: str
        :param filter_chunks: chunks to change status
        :type filter_chunks: str
        :param filter_status: current status of the jobs to change status
        :type filter_status: str
        :param filter_section: sections to change status
        :type filter_section: str
        :param hide: hides plot window
        :type hide: bool
        """
        Autosubmit._check_ownership(expid)
        exp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid)
        tmp_path = os.path.join(exp_path, BasicConfig.LOCAL_TMP_DIR)
        # checking if there is a lock file to avoid multiple running on the same expid
        try:
            with portalocker.Lock(os.path.join(tmp_path, 'autosubmit.lock'), timeout=1):
                Log.info(
                    "Preparing .lock file to avoid multiple instances with same expid.")

                Log.debug('Exp ID: {0}', expid)
                Log.debug('Save: {0}', save)
                Log.debug('Final status: {0}', final)
                Log.debug('List of jobs to change: {0}', lst)
                Log.debug('Chunks to change: {0}', filter_chunks)
                Log.debug('Status of jobs to change: {0}', filter_status)
                Log.debug('Sections to change: {0}', filter_section)
                wrongExpid = 0
                as_conf = AutosubmitConfig(
                    expid, BasicConfig, ConfigParserFactory())
                as_conf.check_conf_files(False)

                # Getting output type from configuration
                output_type = as_conf.get_output_type()

                # Validating job sections, if filter_section -ft has been set:
                if filter_section is not None:
                    section_validation_error = False
                    section_error = False
                    section_not_foundList = list()
                    section_validation_message = "\n## Section Validation Message ##"
                    countStart = filter_section.count('[')
                    countEnd = filter_section.count(']')
                    if countStart > 1 or countEnd > 1:
                        section_validation_error = True
                        section_validation_message += "\n\tList of sections has a format error. Perhaps you were trying to use -fc instead."
                    #countUnderscore = filter_section.count('_')
                    # if countUnderscore > 1:
                    #    section_validation_error = True
                    #    section_validation_message += "\n\tList of sections provided has a format error. Perhaps you were trying to use -fl instead."
                    if section_validation_error == False:
                        if len(str(filter_section).strip()) > 0:
                            if len(filter_section.split()) > 0:
                                jobSections = as_conf.get_jobs_sections()
                                for section in filter_section.split():
                                    # print(section)
                                    # Provided section is not an existing section or it is not the keyword 'Any'
                                    if section not in jobSections and (section != "Any"):
                                        section_error = True
                                        section_not_foundList.append(section)
                        else:
                            section_validation_error = True
                            section_validation_message += "\n\tEmpty input. No changes performed."
                    if section_validation_error == True or section_error == True:
                        if section_error == True:
                            section_validation_message += "\n\tSpecified section(s) : [" + str(section_not_foundList) + \
                                "] not found in the experiment " + str(expid) + \
                                ".\n\tProcess stopped. Review the format of the provided input. Comparison is case sensitive." + \
                                "\n\tRemember that this option expects section names separated by a blank space as input."

                        raise AutosubmitCritical("Error in the supplied input for -ft.",7011,section_validation_message)
                job_list = Autosubmit.load_job_list(
                    expid, as_conf, notransitive=notransitive)
                submitter = Autosubmit._get_submitter(as_conf)
                submitter.load_platforms(as_conf)
                hpcarch = as_conf.get_platform()
                for job in job_list.get_job_list():
                    if job.platform_name is None:
                        job.platform_name = hpcarch
                    # noinspection PyTypeChecker
                    job.platform = submitter.platforms[job.platform_name.lower(
                    )]
                # Validating list of jobs, if filter_list -fl has been set:
                # Seems that Autosubmit.load_job_list call is necessary before verification is executed
                if job_list is not None and lst is not None:
                    job_validation_error = False
                    job_error = False
                    job_not_foundList = list()
                    job_validation_message = "\n## Job Validation Message ##"
                    jobs = list()
                    countStart = lst.count('[')
                    countEnd = lst.count(']')
                    if countStart > 1 or countEnd > 1:
                        job_validation_error = True
                        job_validation_message += "\n\tList of jobs has a format error. Perhaps you were trying to use -fc instead."

                    if job_validation_error == False:
                        for job in job_list.get_job_list():
                            jobs.append(job.name)
                        if len(str(lst).strip()) > 0:
                            if len(lst.split()) > 0:
                                for sentJob in lst.split():
                                    # Provided job does not exist or it is not the keyword 'Any'
                                    if sentJob not in jobs and (sentJob != "Any"):
                                        job_error = True
                                        job_not_foundList.append(sentJob)
                        else:
                            job_validation_error = True
                            job_validation_message += "\n\tEmpty input. No changes performed."

                    if job_validation_error == True or job_error == True:
                        if job_error == True:
                            job_validation_message += "\n\tSpecified job(s) : [" + str(job_not_foundList) + "] not found in the experiment " + \
                                str(expid) + ". \n\tProcess stopped. Review the format of the provided input. Comparison is case sensitive." + \
                                "\n\tRemember that this option expects job names separated by a blank space as input."
                        raise AutosubmitCritical("Error in the supplied input for -ft.",7011,section_validation_message)

                # Validating fc if filter_chunks -fc has been set:
                if filter_chunks is not None:
                    fc_validation_message = "## -fc Validation Message ##"
                    fc_filter_is_correct = True
                    selected_sections = filter_chunks.split(",")[1:]
                    selected_formula = filter_chunks.split(",")[0]
                    current_sections = as_conf.get_jobs_sections()
                    fc_deserializedJson = object()
                    # Starting Validation
                    if len(str(selected_sections).strip()) == 0:
                        fc_filter_is_correct = False
                        fc_validation_message += "\n\tMust include a section (job type)."
                    else:
                        for section in selected_sections:
                            # section = section.strip()
                            # Validating empty sections
                            if len(str(section).strip()) == 0:
                                fc_filter_is_correct = False
                                fc_validation_message += "\n\tEmpty sections are not accepted."
                                break
                            # Validating existing sections
                            # Retrieve experiment data

                            if section not in current_sections:
                                fc_filter_is_correct = False
                                fc_validation_message += "\n\tSection " + section + \
                                    " does not exist in experiment. Remember not to include blank spaces."

                    # Validating chunk formula
                    if len(selected_formula) == 0:
                        fc_filter_is_correct = False
                        fc_validation_message += "\n\tA formula for chunk filtering has not been provided."

                    # If everything is fine until this point
                    if fc_filter_is_correct == True:
                        # Retrieve experiment data
                        current_dates = as_conf._exp_parser.get_option(
                            'experiment', 'DATELIST', '').split()
                        current_members = as_conf.get_member_list()
                        # Parse json
                        try:
                            fc_deserializedJson = json.loads(
                                Autosubmit._create_json(selected_formula))
                        except:
                            fc_filter_is_correct = False
                            fc_validation_message += "\n\tProvided chunk formula does not have the right format. Were you trying to use another option?"
                        if fc_filter_is_correct == True:
                            for startingDate in fc_deserializedJson['sds']:
                                if startingDate['sd'] not in current_dates:
                                    fc_filter_is_correct = False
                                    fc_validation_message += "\n\tStarting date " + \
                                        startingDate['sd'] + \
                                        " does not exist in experiment."
                                for member in startingDate['ms']:
                                    if member['m'] not in current_members:
                                        fc_filter_is_correct = False
                                        fc_validation_message += "\n\tMember " + \
                                            member['m'] + \
                                            " does not exist in experiment."

                     # Ending validation
                    if fc_filter_is_correct == False:
                        raise AutosubmitCritical("Error in the supplied input for -fc.",7011,section_validation_message)
                # Validating status, if filter_status -fs has been set:
                # At this point we already have job_list from where we are getting the allows STATUS
                if filter_status is not None:
                    status_validation_error = False
                    status_validation_message = "\n## Status Validation Message ##"
                    # Trying to identify chunk formula
                    countStart = filter_status.count('[')
                    countEnd = filter_status.count(']')
                    if countStart > 1 or countEnd > 1:
                        status_validation_error = True
                        status_validation_message += "\n\tList of status provided has a format error. Perhaps you were trying to use -fc instead."
                    # Trying to identify job names, implying status names won't use more than 1 underscore _
                    #countUnderscore = filter_status.count('_')
                    # if countUnderscore > 1:
                    #    status_validation_error = True
                    #    status_validation_message += "\n\tList of status provided has a format error. Perhaps you were trying to use -fl instead."
                    # If everything is fine until this point
                    if status_validation_error == False:
                        status_filter = filter_status.split()
                        status_reference = Status()
                        status_list = list()
                        for job in job_list.get_job_list():
                            reference = status_reference.VALUE_TO_KEY[job.status]
                            if reference not in status_list:
                                status_list.append(reference)
                        for status in status_filter:
                            if status not in status_list:
                                status_validation_error = True
                                status_validation_message += "\n\t There are no jobs with status " + \
                                    status + " in this experiment."
                    if status_validation_error == True:
                        raise AutosubmitCritical("Error in the supplied input for -fs.",7011,section_validation_message)

                jobs_filtered = []
                final_status = Autosubmit._get_status(final)
                if filter_section or filter_chunks:
                    if filter_section:
                        ft = filter_section.split()
                    else:
                        ft = filter_chunks.split(",")[1:]
                    if ft == 'Any':
                        for job in job_list.get_job_list():
                            Autosubmit.change_status(
                                final, final_status, job, save)
                    else:
                        for section in ft:
                            for job in job_list.get_job_list():
                                if job.section == section:
                                    if filter_chunks:
                                        jobs_filtered.append(job)
                                    else:
                                        Autosubmit.change_status(
                                            final, final_status, job, save)

                # New feature : Change status by section, member, and chunk; freely.
                # Including inner validation. Trying to make it independent.
                if filter_type_chunk:
                    validation_message = "## -ftc Validation Message ##"
                    filter_is_correct = True
                    selected_sections = filter_type_chunk.split(",")[1:]
                    selected_formula = filter_type_chunk.split(",")[0]
                    deserializedJson = object()
                    performed_changes = dict()

                    # Starting Validation
                    if len(str(selected_sections).strip()) == 0:
                        filter_is_correct = False
                        validation_message += "\n\tMust include a section (job type). If you want to apply the changes to all sections, include 'Any'."
                    else:
                        for section in selected_sections:
                            # Validating empty sections
                            if len(str(section).strip()) == 0:
                                filter_is_correct = False
                                validation_message += "\n\tEmpty sections are not accepted."
                                break
                            # Validating existing sections
                            # Retrieve experiment data
                            current_sections = as_conf.get_jobs_sections()
                            if section not in current_sections and section != "Any":
                                filter_is_correct = False
                                validation_message += "\n\tSection " + \
                                    section + " does not exist in experiment."

                    # Validating chunk formula
                    if len(selected_formula) == 0:
                        filter_is_correct = False
                        validation_message += "\n\tA formula for chunk filtering has not been provided. If you want to change all chunks, include 'Any'."

                    # If everything is fine until this point
                    if filter_is_correct == True:
                        # Retrieve experiment data
                        current_dates = as_conf._exp_parser.get_option(
                            'experiment', 'DATELIST', '').split()
                        current_members = as_conf.get_member_list()
                        # Parse json
                        try:
                            deserializedJson = json.loads(
                                Autosubmit._create_json(selected_formula))
                        except:
                            filter_is_correct = False
                            validation_message += "\n\tProvided chunk formula does not have the right format. Were you trying to use another option?"
                        if filter_is_correct == True:
                            for startingDate in deserializedJson['sds']:
                                if startingDate['sd'] not in current_dates:
                                    filter_is_correct = False
                                    validation_message += "\n\tStarting date " + \
                                        startingDate['sd'] + \
                                        " does not exist in experiment."
                                for member in startingDate['ms']:
                                    if member['m'] not in current_members and member['m'] != "Any":
                                        filter_is_correct_ = False
                                        validation_message += "\n\tMember " + \
                                            member['m'] + \
                                            " does not exist in experiment."

                    # Ending validation
                    if filter_is_correct == False:
                        raise AutosubmitCritical("Error in the supplied input for -ftc.", 7011, section_validation_message)

                    # If input is valid, continue.
                    record = dict()
                    final_list = []
                    # Get current list
                    working_list = job_list.get_job_list()
                    for section in selected_sections:
                        if section == "Any":
                            # Any section
                            section_selection = working_list
                            # Go through start dates
                            for starting_date in deserializedJson['sds']:
                                date = starting_date['sd']
                                date_selection = filter(lambda j: date2str(
                                    j.date) == date, section_selection)
                                # Members for given start date
                                for member_group in starting_date['ms']:
                                    member = member_group['m']
                                    if member == "Any":
                                        # Any member
                                        member_selection = date_selection
                                        chunk_group = member_group['cs']
                                        for chunk in chunk_group:
                                            filtered_job = filter(
                                                lambda j: j.chunk == int(chunk), member_selection)
                                            for job in filtered_job:
                                                final_list.append(job)
                                            # From date filter and sync is not None
                                            for job in filter(lambda j: j.chunk == int(chunk) and j.synchronize is not None, date_selection):
                                                final_list.append(job)
                                    else:
                                        # Selected members
                                        member_selection = filter(
                                            lambda j: j.member == member, date_selection)
                                        chunk_group = member_group['cs']
                                        for chunk in chunk_group:
                                            filtered_job = filter(
                                                lambda j: j.chunk == int(chunk), member_selection)
                                            for job in filtered_job:
                                                final_list.append(job)
                                            # From date filter and sync is not None
                                            for job in filter(lambda j: j.chunk == int(chunk) and j.synchronize is not None, date_selection):
                                                final_list.append(job)
                        else:
                            # Only given section
                            section_selection = filter(
                                lambda j: j.section == section, working_list)
                            # Go through start dates
                            for starting_date in deserializedJson['sds']:
                                date = starting_date['sd']
                                date_selection = filter(lambda j: date2str(
                                    j.date) == date, section_selection)
                                # Members for given start date
                                for member_group in starting_date['ms']:
                                    member = member_group['m']
                                    if member == "Any":
                                        # Any member
                                        member_selection = date_selection
                                        chunk_group = member_group['cs']
                                        for chunk in chunk_group:
                                            filtered_job = filter(
                                                lambda j: j.chunk == int(chunk), member_selection)
                                            for job in filtered_job:
                                                final_list.append(job)
                                            # From date filter and sync is not None
                                            for job in filter(lambda j: j.chunk == int(chunk) and j.synchronize is not None, date_selection):
                                                final_list.append(job)
                                    else:
                                        # Selected members
                                        member_selection = filter(
                                            lambda j: j.member == member, date_selection)
                                        chunk_group = member_group['cs']
                                        for chunk in chunk_group:
                                            filtered_job = filter(
                                                lambda j: j.chunk == int(chunk), member_selection)
                                            for job in filtered_job:
                                                final_list.append(job)
                                            # From date filter and sync is not None
                                            for job in filter(lambda j: j.chunk == int(chunk) and j.synchronize is not None, date_selection):
                                                final_list.append(job)
                    status = Status()
                    for job in final_list:
                        if job.status != final_status:
                            # Only real changes
                            performed_changes[job.name] = str(
                                Status.VALUE_TO_KEY[job.status]) + " -> " + str(final)
                            Autosubmit.change_status(
                                final, final_status, job, save)
                    # If changes have been performed
                    if len(performed_changes.keys()) > 0:
                        if detail == True:
                            current_length = len(job_list.get_job_list())
                            if current_length > 1000:
                                Log.warning(
                                    "-d option: Experiment has too many jobs to be printed in the terminal. Maximum job quantity is 1000, your experiment has " + str(current_length) + " jobs.")
                            else:
                                Log.info(job_list.print_with_status(statusChange = performed_changes))
                    else: 
                        Log.warning("No changes were performed.")
                # End of New Feature

                if filter_chunks:
                    if len(jobs_filtered) == 0:
                        jobs_filtered = job_list.get_job_list()

                    fc = filter_chunks
                    Log.debug(fc)

                    if fc == 'Any':
                        for job in jobs_filtered:
                            Autosubmit.change_status(
                                final, final_status, job, save)
                    else:
                        # noinspection PyTypeChecker
                        data = json.loads(Autosubmit._create_json(fc))
                        for date_json in data['sds']:
                            date = date_json['sd']
                            jobs_date = filter(lambda j: date2str(
                                j.date) == date, jobs_filtered)

                            for member_json in date_json['ms']:
                                member = member_json['m']
                                jobs_member = filter(
                                    lambda j: j.member == member, jobs_date)

                                for chunk_json in member_json['cs']:
                                    chunk = int(chunk_json)
                                    for job in filter(lambda j: j.chunk == chunk and j.synchronize is not None, jobs_date):
                                        Autosubmit.change_status(
                                            final, final_status, job, save)

                                    for job in filter(lambda j: j.chunk == chunk, jobs_member):
                                        Autosubmit.change_status(
                                            final, final_status, job, save)

                if filter_status:
                    status_list = filter_status.split()

                    Log.debug("Filtering jobs with status {0}", filter_status)
                    if status_list == 'Any':
                        for job in job_list.get_job_list():
                            Autosubmit.change_status(
                                final, final_status, job, save)
                    else:
                        for status in status_list:
                            fs = Autosubmit._get_status(status)
                            for job in filter(lambda j: j.status == fs, job_list.get_job_list()):
                                Autosubmit.change_status(
                                    final, final_status, job, save)

                if lst:
                    jobs = lst.split()
                    expidJoblist = defaultdict(int)
                    for x in lst.split():
                        expidJoblist[str(x[0:4])] += 1

                    if str(expid) in expidJoblist:
                        wrongExpid = jobs.__len__()-expidJoblist[expid]
                    if wrongExpid > 0:
                        Log.warning(
                            "There are {0} job.name with an invalid Expid", wrongExpid)

                    if jobs == 'Any':
                        for job in job_list.get_job_list():
                            Autosubmit.change_status(
                                final, final_status, job, save)
                    else:
                        for job in job_list.get_job_list():
                            if job.name in jobs:
                                Autosubmit.change_status(
                                    final, final_status, job, save)

                job_list.update_list(as_conf, False, True)

                if save and wrongExpid == 0:
                    job_list.save()
                else:
                    Log.printlog(
                        "Changes NOT saved to the JobList!!!!:  use -s option to save",3000)

                if as_conf.get_wrapper_type() != 'none' and check_wrapper:
                    packages_persistence = JobPackagePersistence(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl"),
                                                                 "job_packages_" + expid)
                    os.chmod(os.path.join(BasicConfig.LOCAL_ROOT_DIR,
                                          expid, "pkl", "job_packages_" + expid+".db"), 0775)
                    packages_persistence.reset_table(True)
                    referenced_jobs_to_remove = set()
                    job_list_wrappers = copy.deepcopy(job_list)
                    jobs_wr = copy.deepcopy(job_list.get_job_list())
                    [job for job in jobs_wr if (
                        job.status != Status.COMPLETED)]
                    for job in jobs_wr:
                        for child in job.children:
                            if child not in jobs_wr:
                                referenced_jobs_to_remove.add(child)
                        for parent in job.parents:
                            if parent not in jobs_wr:
                                referenced_jobs_to_remove.add(parent)

                    for job in jobs_wr:
                        job.children = job.children - referenced_jobs_to_remove
                        job.parents = job.parents - referenced_jobs_to_remove
                    Autosubmit.generate_scripts_andor_wrappers(as_conf, job_list_wrappers, jobs_wr,
                                                               packages_persistence, True)

                    packages = packages_persistence.load(True)
                else:
                    packages = JobPackagePersistence(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl"),
                                                     "job_packages_" + expid).load()
                if not noplot:
                    groups_dict = dict()
                    if group_by:
                        status = list()
                        if expand_status:
                            for s in expand_status.split():
                                status.append(
                                    Autosubmit._get_status(s.upper()))

                        job_grouping = JobGrouping(group_by, copy.deepcopy(job_list.get_job_list()), job_list, expand_list=expand,
                                                   expanded_status=status)
                        groups_dict = job_grouping.group_jobs()
                    Log.info("\nPloting joblist...")
                    monitor_exp = Monitor()
                    monitor_exp.generate_output(expid,
                                                job_list.get_job_list(),
                                                os.path.join(
                                                    exp_path, "/tmp/LOG_", expid),
                                                output_format=output_type,
                                                packages=packages,
                                                show=not hide,
                                                groups=groups_dict,
                                                job_list_object=job_list)

                if not filter_type_chunk and detail == True:
                    Log.warning("-d option only works with -ftc.")
                return True


        except portalocker.AlreadyLocked:
            message = "We have detected that there is another Autosubmit instance using the experiment\n. Stop other Autosubmit instances that are using the experiment or delete autosubmit.lock file located on tmp folder"
            raise AutosubmitCritical(message,7000)

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
                 if sys.version_info[0] == 3:
                     answer = raw_input()
                 else:
                     # noinspection PyCompatibility
                     answer = raw_input()
                 return strtobool(answer.lower())
             except ValueError:
                 sys.stdout.write('Please respond with \'y\' or \'n\'.\n')

    @staticmethod
    def _prepare_conf_files(exp_id, hpc, autosubmit_version, dummy):
        """
        Changes default configuration files to match new experiment values

        :param exp_id: experiment identifier
        :type exp_id: str
        :param hpc: hpc to use
        :type hpc: str
        :param autosubmit_version: current autosubmit's version
        :type autosubmit_version: str
        :param dummy: if True, creates a dummy experiment adding some default values
        :type dummy: bool
        """
        as_conf = AutosubmitConfig(exp_id, BasicConfig, ConfigParserFactory())
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
        s = s.upper()
        if s == 'READY':
            return Status.READY
        elif s == 'COMPLETED':
            return Status.COMPLETED
        elif s == 'WAITING':
            return Status.WAITING
        elif s == 'HELD':
            return Status.HELD
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
                ms = {'m': out[count],
                      'cs': Autosubmit._get_chunks(out[count + 1])}
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
    def _get_submitter(as_conf):
        """
        Returns the submitter corresponding to the communication defined on autosubmit's config file

        :return: submitter
        :rtype: Submitter
        """
        communications_library = as_conf.get_communications_library()
        if communications_library == 'paramiko':
            return ParamikoSubmitter()
        else:
            return ParamikoSubmitter()# only paramiko is avaliable right now so..

    @staticmethod
    def _get_job_list_persistence(expid, as_conf):
        """
        Returns the JobListPersistence corresponding to the storage type defined on autosubmit's config file

        :return: job_list_persistence
        :rtype: JobListPersistence
        """
        storage_type = as_conf.get_storage_type()
        if storage_type == 'pkl':
            return JobListPersistencePkl()
        elif storage_type == 'db':
            return JobListPersistenceDb(os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "pkl"),
                                        "job_list_" + expid)
        raise AutosubmitCritical('Storage type not known',7014)

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
                sd = {'sd': out[0][count], 'ms': Autosubmit._get_members(
                    out[0][count + 1])}
                data.append(sd)
                count += 1
            else:
                count += 1

        sds = {'sds': data}
        result = json.dumps(sds)
        return result

    @staticmethod
    def testcase(copy_id, description, chunks=None, member=None, start_date=None, hpc=None, branch=None):
        """
        Method to create a test case. It creates a new experiment whose id starts by 't'.


        :param copy_id: experiment identifier
        :type copy_id: str
        :param description: test case experiment description
        :type description: str
        :param chunks: number of chunks to be run by the experiment. If None, it uses configured chunk(s).
        :type chunks: int
        :param member: member to be used by the test. If None, it uses configured member(s).
        :type member: str
        :param start_date: start date to be used by the test. If None, it uses configured start date(s).
        :type start_date: str
        :param hpc: HPC to be used by the test. If None, it uses configured HPC.
        :type hpc: str
        :param branch: branch or revision to be used by the test. If None, it uses configured branch.
        :type branch: str
        :return: test case id
        :rtype: str
        """

        testcaseid = Autosubmit.expid(hpc, description, copy_id, False, True)
        if testcaseid == '':
            return False

        Autosubmit._change_conf(
            testcaseid, hpc, start_date, member, chunks, branch, False)

        return testcaseid

    @staticmethod
    def test(expid, chunks, member=None, start_date=None, hpc=None, branch=None):
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
        :param start_date: start date to be used by the test. If None, it uses a random one from which are defined on
                         the experiment.
        :type start_date: str
        :param hpc: HPC to be used by the test. If None, it uses a random one from which are defined on
                    the experiment.
        :type hpc: str
        :param branch: branch or revision to be used by the test. If None, it uses configured branch.
        :type branch: str
        :return: True if test was succesful, False otherwise
        :rtype: bool
        """
        testid = Autosubmit.expid(
            'test', 'test experiment for {0}'.format(expid), expid, False, True)
        if testid == '':
            return False

        Autosubmit._change_conf(testid, hpc, start_date,
                                member, chunks, branch, True)

        Autosubmit.create(testid, False, True)
        if not Autosubmit.run_experiment(testid):
            return False
        return True

    @staticmethod
    def _change_conf(testid, hpc, start_date, member, chunks, branch, random_select=False):
        as_conf = AutosubmitConfig(testid, BasicConfig, ConfigParserFactory())
        exp_parser = as_conf.get_parser(
            ConfigParserFactory(), as_conf.experiment_file)
        if exp_parser.get_bool_option('rerun', "RERUN", True):
            raise AutosubmitCritical('Can not test a RERUN experiment',7014)

        content = open(as_conf.experiment_file).read()
        if random_select:
            if hpc is None:
                platforms_parser = as_conf.get_parser(
                    ConfigParserFactory(), as_conf.platforms_file)
                test_platforms = list()
                for section in platforms_parser.sections():
                    if platforms_parser.get_option(section, 'TEST_SUITE', 'false').lower() == 'true':
                        test_platforms.append(section)
                if len(test_platforms) == 0:
                    raise AutosubmitCritical("Missing hpcarch setting in expdef",7014)

                hpc = random.choice(test_platforms)
            if member is None:
                member = random.choice(exp_parser.get(
                    'experiment', 'MEMBERS').split(' '))
            if start_date is None:
                start_date = random.choice(exp_parser.get(
                    'experiment', 'DATELIST').split(' '))
            if chunks is None:
                chunks = 1

        # Experiment
        content = content.replace(re.search('^EXPID =.*', content, re.MULTILINE).group(0),
                                  "EXPID = " + testid)
        if start_date is not None:
            content = content.replace(re.search('^DATELIST =.*', content, re.MULTILINE).group(0),
                                      "DATELIST = " + start_date)
        if member is not None:
            content = content.replace(re.search('^MEMBERS =.*', content, re.MULTILINE).group(0),
                                      "MEMBERS = " + member)
        if chunks is not None:
            # noinspection PyTypeChecker
            content = content.replace(re.search('^NUMCHUNKS =.*', content, re.MULTILINE).group(0),
                                      "NUMCHUNKS = " + chunks)
        if hpc is not None:
            content = content.replace(re.search('^HPCARCH =.*', content, re.MULTILINE).group(0),
                                      "HPCARCH = " + hpc)
        if branch is not None:
            content = content.replace(re.search('^PROJECT_BRANCH =.*', content, re.MULTILINE).group(0),
                                      "PROJECT_BRANCH = " + branch)
            content = content.replace(re.search('^PROJECT_REVISION =.*', content, re.MULTILINE).group(0),
                                      "PROJECT_REVISION = " + branch)

        open(as_conf.experiment_file, 'w').write(content)

    @staticmethod
    def load_job_list(expid, as_conf, notransitive=False, monitor=False):
        rerun = as_conf.get_rerun()

        job_list = JobList(expid, BasicConfig, ConfigParserFactory(),
                           Autosubmit._get_job_list_persistence(expid, as_conf))

        date_list = as_conf.get_date_list()
        date_format = ''
        if as_conf.get_chunk_size_unit() is 'hour':
            date_format = 'H'
        for date in date_list:
            if date.hour > 1:
                date_format = 'H'
            if date.minute > 1:
                date_format = 'M'
        job_list.generate(date_list, as_conf.get_member_list(), as_conf.get_num_chunks(), as_conf.get_chunk_ini(),
                          as_conf.load_parameters(), date_format, as_conf.get_retrials(),
                          as_conf.get_default_job_type(), as_conf.get_wrapper_type(), as_conf.get_wrapper_jobs(),
                          new=False, notransitive=notransitive)
        if rerun == "true":

            chunk_list = Autosubmit._create_json(as_conf.get_chunk_list())
            if not monitor:
                job_list.rerun(chunk_list, notransitive)
            else:
                rerun_list = JobList(expid, BasicConfig, ConfigParserFactory(),
                                     Autosubmit._get_job_list_persistence(expid, as_conf))
                rerun_list.generate(date_list, as_conf.get_member_list(), as_conf.get_num_chunks(),
                                    as_conf.get_chunk_ini(),
                                    as_conf.load_parameters(), date_format, as_conf.get_retrials(),
                                    as_conf.get_default_job_type(), as_conf.get_wrapper_type(),
                                    as_conf.get_wrapper_jobs(),
                                    new=False, notransitive=notransitive)
                rerun_list.rerun(chunk_list, notransitive)
                job_list = Autosubmit.rerun_recovery(
                    expid, job_list, rerun_list, as_conf)
        else:
            job_list.remove_rerun_only_jobs(notransitive)

        return job_list

    @staticmethod
    def rerun_recovery(expid, job_list, rerun_list, as_conf):
        """
        Method to check all active jobs. If COMPLETED file is found, job status will be changed to COMPLETED,
        otherwise it will be set to WAITING. It will also update the jobs list.

        :param expid: identifier of the experiment to recover
        :type expid: str
        :param save: If true, recovery saves changes to the jobs list
        :type save: bool
        :param all_jobs: if True, it tries to get completed files for all jobs, not only active.
        :type all_jobs: bool
        :param hide: hides plot window
        :type hide: bool
        """

        hpcarch = as_conf.get_platform()
        submitter = Autosubmit._get_submitter(as_conf)
        try:
            submitter.load_platforms(as_conf)
            if submitter.platforms is None:
                raise AutosubmitCritical("platforms couldn't be loaded",7014)
        except:
            raise AutosubmitCritical("platforms couldn't be loaded", 7014)
        platforms = submitter.platforms

        platforms_to_test = set()
        for job in job_list.get_job_list():
            if job.platform_name is None:
                job.platform_name = hpcarch
            # noinspection PyTypeChecker
            job.platform = platforms[job.platform_name.lower()]
            # noinspection PyTypeChecker
            platforms_to_test.add(platforms[job.platform_name.lower()])
        rerun_names = []

        [rerun_names.append(job.name) for job in rerun_list.get_job_list()]
        jobs_to_recover = [
            i for i in job_list.get_job_list() if i.name not in rerun_names]

        Log.info("Looking for COMPLETED files")
        start = datetime.datetime.now()
        for job in jobs_to_recover:
            if job.platform_name is None:
                job.platform_name = hpcarch
            # noinspection PyTypeChecker
            job.platform = platforms[job.platform_name.lower()]

            if job.platform.get_completed_files(job.name, 0):
                job.status = Status.COMPLETED
                Log.info("CHANGED job '{0}' status to COMPLETED".format(job.name))

            job.platform.get_logs_files(expid, job.remote_logs)
        return job_list
