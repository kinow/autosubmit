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


import sys
import saga
import os
from autosubmit.config.config_common import AutosubmitConfig
from autosubmit.config.basicConfig import  BasicConfig
from platform import Platform


class Submitter:
    def load_platforms(self, asconf):
        """

        :param asconf:
        :type asconf: AutosubmitConfig
        """
        parser = asconf.platforms_parser

        platforms = dict()
        local_platform = Platform(asconf.expid, 'local')
        local_platform.service = saga.job.Service("fork://localhost")
        local_platform.type = 'local'
        local_platform.queue = ''
        local_platform.max_waiting_jobs = asconf.get_max_waiting_jobs()
        local_platform.total_jobs = asconf.get_total_jobs()
        local_platform.scratch = os.path.join(BasicConfig.LOCAL_ROOT_DIR, asconf.expid, BasicConfig.LOCAL_TMP_DIR)
        local_platform.project = asconf.expid
        local_platform.budget = asconf.expid
        local_platform.user = ''
        local_platform.root_dir = os.path.join(BasicConfig.LOCAL_ROOT_DIR, local_platform.expid)
        local_platform.transfer = "file"
        local_platform.host = 'localhost'
        platforms['local'] = local_platform

        for section in parser.sections():
            platform_type = AutosubmitConfig.get_option(parser, section, 'TYPE', '').lower()

            remote_platform = Platform(asconf.expid, section.lower())
            remote_platform.type = platform_type

            # platform_version = AutosubmitConfig.get_option(parser, section, 'VERSION', '')
            if platform_type == 'pbs':
                adaptor = 'pbs+ssh'
            elif platform_type == 'sge':
                adaptor = 'sge+ssh'
            elif platform_type == 'ps':
                adaptor = 'ssh'
            elif platform_type == 'lsf':
                adaptor = 'lsf+ssh'
            elif platform_type == 'ecaccess':
                adaptor = 'ecaccess'
            elif platform_type == 'slurm':
                adaptor = 'slurm+ssh'
            elif platform_type == '':
                raise Exception("Queue type not specified on platform {0}".format(section))
            else:
                raise Exception("Queue type {0} specified on platform {0} is not valid".format(platform_type, section))

            if AutosubmitConfig.get_option(parser, section, 'ADD_PROJECT_TO_HOST', '').lower() == 'true':
                host = '{0}-{1}'.format(AutosubmitConfig.get_option(parser, section, 'HOST', None),
                                        AutosubmitConfig.get_option(parser, section, 'PROJECT', None))
            else:
                host = AutosubmitConfig.get_option(parser, section, 'HOST', None)

            ctx = saga.Context("ssh")
            ctx.user_id = AutosubmitConfig.get_option(parser, section, 'USER', None)
            session = saga.Session()
            session.add_context(ctx)
            remote_platform.service = saga.job.Service("{0}://{1}".format(adaptor, host), session=session)
            remote_platform.host = host
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


def main():
        ctx = saga.Context("ssh")
        ctx.user_id = "bsc32906"

        session = saga.Session()
        session.add_context(ctx)

        js = saga.job.Service("lsf+ssh://mn-bsc32", session=session)

        # Next, we describe the job we want to run. A complete set of job
        # description attributes can be found in the API documentation.
        jd = saga.job.Description()
        jd.wall_time_limit   = 1  # minutes
        jd.executable        = '/gpfs/scratch/bsc32/bsc32906/a000/a000_REMOTE_SETUP.cmd'

        jd.total_cpu_count   = 1
        jd.queue             = "sequential"
        jd.project           = "bsc32"

        jd.working_directory = "/gpfs/scratch/bsc32/bsc32906/a000"
        jd.output            = "a000_REMOTE_SETUP.out"
        jd.error             = "a000_REMOTE_SETUP.err"

        # Create a new job from the job description. The initial state of
        # the job is 'New'.
        touchjob = js.create_job(jd)
        touchjob.run()



if __name__ == "__main__":
    sys.exit(main())