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
# along with Autosubmit.  If not, see <http: www.gnu.org / licenses / >.


import time

import os

from autosubmit.config.basicConfig import BasicConfig
from autosubmit.config.config_common import AutosubmitConfig
from submitter import Submitter
from autosubmit.platforms.psplatform import PsPlatform
from autosubmit.platforms.lsfplatform import LsfPlatform
from autosubmit.platforms.pbsplatform import PBSPlatform
from autosubmit.platforms.sgeplatform import SgePlatform
from autosubmit.platforms.ecplatform import EcPlatform
from autosubmit.platforms.slurmplatform import SlurmPlatform
from autosubmit.platforms.locplatform import LocalPlatform
from autosubmit.platforms.paramiko_platform import ParamikoPlatformException


class ParamikoSubmitter(Submitter):
    """
    Class to manage the experiments platform
    """

    def load_platforms(self, asconf, retries=5):
        """
        Create all the platforms object that will be used by the experiment

        :param retries: retries in case creation of service fails
        :param asconf: autosubmit config to use
        :type asconf: AutosubmitConfig
        :return: platforms used by the experiment
        :rtype: dict
        """

        platforms_used = list()
        hpcarch = asconf.get_platform()

        job_parser = asconf.jobs_parser
        for job in job_parser.sections():
            hpc = AutosubmitConfig.get_option(job_parser, job, 'PLATFORM', hpcarch).lower()
            if hpc not in platforms_used:
                platforms_used.append(hpc)

        parser = asconf.platforms_parser

        platforms = dict()
        local_platform = LocalPlatform(asconf.expid, 'local', BasicConfig)
        local_platform.max_waiting_jobs = asconf.get_max_waiting_jobs()
        local_platform.total_jobs = asconf.get_total_jobs()
        local_platform.scratch = os.path.join(BasicConfig.LOCAL_ROOT_DIR, asconf.expid, BasicConfig.LOCAL_TMP_DIR)
        local_platform.root_dir = os.path.join(BasicConfig.LOCAL_ROOT_DIR, local_platform.expid)
        local_platform.host = 'localhost'
        platforms['local'] = local_platform
        platforms['LOCAL'] = local_platform

        for section in parser.sections():

            if section.lower() not in platforms_used:
                continue

            platform_type = AutosubmitConfig.get_option(parser, section, 'TYPE', '').lower()
            platform_version = AutosubmitConfig.get_option(parser, section, 'VERSION', '')
            try:
                if platform_type == 'pbs':
                    remote_platform = PBSPlatform(asconf.expid, section.lower(), BasicConfig, platform_version)
                elif platform_type == 'sge':
                    remote_platform = SgePlatform(asconf.expid, section.lower(), BasicConfig)
                elif platform_type == 'ps':
                    remote_platform = PsPlatform(asconf.expid, section.lower(), BasicConfig)
                elif platform_type == 'lsf':
                    remote_platform = LsfPlatform(asconf.expid, section.lower(), BasicConfig)
                elif platform_type == 'ecaccess':
                    remote_platform = EcPlatform(asconf.expid, section.lower(), BasicConfig, platform_version)
                elif platform_type == 'slurm':
                    remote_platform = SlurmPlatform(asconf.expid, section.lower(), BasicConfig)
                else:
                    raise Exception("Queue type not specified on platform {0}".format(section))

            except ParamikoPlatformException as e:
                Log.error("Queue exception: {0}".format(e.message))
                return None

            remote_platform.type = platform_type
            remote_platform._version = platform_version

            if AutosubmitConfig.get_option(parser, section, 'ADD_PROJECT_TO_HOST', '').lower() == 'true':
                host = '{0}-{1}'.format(AutosubmitConfig.get_option(parser, section, 'HOST', None),
                                        AutosubmitConfig.get_option(parser, section, 'PROJECT', None))
            else:
                host = AutosubmitConfig.get_option(parser, section, 'HOST', None)

            remote_platform.host = host
            remote_platform.max_waiting_jobs = int(AutosubmitConfig.get_option(parser, section, 'MAX_WAITING_JOBS',
                                                                               asconf.get_max_waiting_jobs()))
            remote_platform.total_jobs = int(AutosubmitConfig.get_option(parser, section, 'TOTAL_JOBS',
                                                                         asconf.get_total_jobs()))
            remote_platform.project = AutosubmitConfig.get_option(parser, section, 'PROJECT', None)
            remote_platform.budget = AutosubmitConfig.get_option(parser, section, 'BUDGET', remote_platform.project)
            remote_platform.reservation = AutosubmitConfig.get_option(parser, section, 'RESERVATION', '')
            remote_platform.exclusivity = AutosubmitConfig.get_option(parser, section, 'EXCLUSIVITY', '').lower()
            remote_platform.user = AutosubmitConfig.get_option(parser, section, 'USER', None)
            remote_platform.scratch = AutosubmitConfig.get_option(parser, section, 'SCRATCH_DIR', None)
            remote_platform._default_queue = AutosubmitConfig.get_option(parser, section, 'QUEUE', None)
            remote_platform._serial_queue = AutosubmitConfig.get_option(parser, section, 'SERIAL_QUEUE', None)
            remote_platform.processors_per_node = AutosubmitConfig.get_option(parser, section, 'PROCESSORS_PER_NODE',
                                                                              None)
            remote_platform.root_dir = os.path.join(remote_platform.scratch, remote_platform.project,
                                                    remote_platform.user, remote_platform.expid)
            remote_platform.update_cmds()
            platforms[section.lower()] = remote_platform

        for section in parser.sections():
            if parser.has_option(section, 'SERIAL_PLATFORM'):
                platforms[section.lower()].serial_platform = platforms[AutosubmitConfig.get_option(parser, section,
                                                                                                   'SERIAL_PLATFORM',
                                                                                                   None).lower()]

        self.platforms = platforms
