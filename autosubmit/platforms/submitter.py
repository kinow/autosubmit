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


import saga
import os
import time

from autosubmit.config.config_common import AutosubmitConfig
from autosubmit.config.basicConfig import BasicConfig
from platform import Platform


class Submitter:
    """
    Class to manage the experiments platform
    """
    def load_platforms(self, asconf, retries=30):
        """
        Create all the platforms object that will be used by the experiment

        :param retries: retries in case creation of service fails
        :param asconf: autosubmit config to use
        :type asconf: AutosubmitConfig
        :return: platforms used by the experiment
        :rtype: dict
        """
        adaptors_variable = os.environ.get('SAGA_ADAPTOR_PATH')
        if adaptors_variable is None:
            adaptors_variable = ''
        if 'autosubmit.platforms.ecmwf_adaptor' not in adaptors_variable:
            if len(adaptors_variable) > 0 and not adaptors_variable.endswith(':'):
                adaptors_variable += ':'
            adaptors_variable += 'autosubmit.platforms.ecmwf_adaptor'

        if 'autosubmit.platforms.mn_adaptor' not in adaptors_variable:
            if len(adaptors_variable) > 0 and not adaptors_variable.endswith(':'):
                adaptors_variable += ':'
            adaptors_variable += 'autosubmit.platforms.mn_adaptor'

        platforms_used = list()
        hpcarch = asconf.get_platform()

        job_parser = asconf.jobs_parser
        for job in job_parser.sections():
            hpc = AutosubmitConfig.get_option(job_parser, job, 'PLATFORM', hpcarch).lower()
            if hpc not in platforms_used:
                platforms_used.append(hpc)

        os.environ['SAGA_ADAPTOR_PATH'] = adaptors_variable
        parser = asconf.platforms_parser

        session = None

        platforms = dict()
        local_platform = Platform(asconf.expid, 'local', BasicConfig)
        local_platform.service = None
        retry = retries
        while local_platform.service is None and retry > 0:
            try:
                local_platform.service = saga.job.Service("fork://localhost", session=session)
            except saga.SagaException:
                retry -= 1
                time.sleep(5)
        local_platform.type = 'local'
        local_platform.queue = ''
        local_platform.max_waiting_jobs = asconf.get_max_waiting_jobs()
        local_platform.total_jobs = asconf.get_total_jobs()
        local_platform.scratch = os.path.join(BasicConfig.LOCAL_ROOT_DIR, asconf.expid, BasicConfig.LOCAL_TMP_DIR)
        local_platform.project = ''
        local_platform.budget = ''
        local_platform.user = ''
        local_platform.root_dir = os.path.join(BasicConfig.LOCAL_ROOT_DIR, local_platform.expid)
        local_platform.transfer = "file"
        local_platform.host = 'localhost'
        platforms['local'] = local_platform

        for section in parser.sections():

            if section.lower() not in platforms_used:
                continue

            platform_type = AutosubmitConfig.get_option(parser, section, 'TYPE', '').lower()

            remote_platform = Platform(asconf.expid, section.lower(), BasicConfig)
            remote_platform.type = platform_type

            # platform_version = AutosubmitConfig.get_option(parser, section, 'VERSION', '')
            if platform_type == 'pbs':
                adaptor = 'pbs+ssh'
            elif platform_type == 'sge':
                adaptor = 'sge+ssh'
            elif platform_type == 'ps':
                adaptor = 'ssh'
            elif platform_type == 'lsf':
                adaptor = 'mn+ssh'
            elif platform_type == 'ecaccess':
                adaptor = 'ecaccess'
                remote_platform.scheduler = AutosubmitConfig.get_option(parser, section, 'SCHEDULER', 'pbs').lower()
            elif platform_type == 'slurm':
                adaptor = 'slurm+ssh'
            elif platform_type == '':
                raise Exception("Queue type not specified on platform {0}".format(section))
            else:
                adaptor = platform_type

            if AutosubmitConfig.get_option(parser, section, 'ADD_PROJECT_TO_HOST', '').lower() == 'true':
                host = '{0}-{1}'.format(AutosubmitConfig.get_option(parser, section, 'HOST', None),
                                        AutosubmitConfig.get_option(parser, section, 'PROJECT', None))
            else:
                host = AutosubmitConfig.get_option(parser, section, 'HOST', None)

            # if adaptor.endswith('ssh'):
            #     ctx = saga.Context('ssh')
            #     ctx.user_id = AutosubmitConfig.get_option(parser, section, 'USER', None)
            #     session = saga.Session()
            #     session.add_context(ctx)
            # else:
            session = None

            remote_platform.host = host
            if remote_platform.type == 'ecaccess':
                # It has to be fork because we are communicating through commands at the local machine
                host = 'localhost'

            remote_platform.service = None
            retry = retries
            while remote_platform.service is None and retry > 0:
                try:
                    # noinspection PyTypeChecker
                    remote_platform.service = saga.job.Service("{0}://{1}".format(adaptor, host), session=session)
                except saga.SagaException:
                    retry -= 1
                    time.sleep(5)
            # noinspection PyProtectedMember
            remote_platform.service._adaptor.host = remote_platform.host
            # noinspection PyProtectedMember
            remote_platform.service._adaptor.scheduler = remote_platform.scheduler

            remote_platform.max_waiting_jobs = int(AutosubmitConfig.get_option(parser, section, 'MAX_WAITING_JOBS',
                                                                               asconf.get_max_waiting_jobs()))
            remote_platform.total_jobs = int(AutosubmitConfig.get_option(parser, section, 'TOTAL_JOBS',
                                                                         asconf.get_total_jobs()))

            remote_platform.project = AutosubmitConfig.get_option(parser, section, 'PROJECT', None)
            remote_platform.budget = AutosubmitConfig.get_option(parser, section, 'BUDGET', remote_platform.project)
            remote_platform.user = AutosubmitConfig.get_option(parser, section, 'USER', None)
            remote_platform.scratch = AutosubmitConfig.get_option(parser, section, 'SCRATCH_DIR', None)
            remote_platform._default_queue = AutosubmitConfig.get_option(parser, section, 'QUEUE', None)
            remote_platform._serial_queue = AutosubmitConfig.get_option(parser, section, 'SERIAL_QUEUE', None)
            remote_platform.root_dir = os.path.join(remote_platform.scratch, remote_platform.project,
                                                    remote_platform.user, remote_platform.expid)
            platforms[section.lower()] = remote_platform

        for section in parser.sections():
            if parser.has_option(section, 'SERIAL_PLATFORM'):
                platforms[section.lower()].serial_platform = platforms[AutosubmitConfig.get_option(parser, section,
                                                                                                   'SERIAL_PLATFORM',
                                                                                                   None).lower()]

        self.platforms = platforms


