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
import os
import platform
from pyparsing import nestedExpr
import re
from os import listdir
from commands import getstatusoutput

from autosubmit.date.chunk_date_lib import parse_date

from autosubmit.config.log import Log
from autosubmit.config.basicConfig import BasicConfig

from autosubmit.platforms.psplatform import PsPlatform
from autosubmit.platforms.lsfplatform import LsfPlatform
from autosubmit.platforms.pbsplatform import PBSPlatform
from autosubmit.platforms.sgeplatform import SgePlatform
from autosubmit.platforms.ecplatform import EcPlatform
from autosubmit.platforms.slurmplatform import SlurmPlatform
from autosubmit.platforms.localplatform import LocalPlatform
from autosubmit.platforms.hpcplatform import HPCPlatformException


class AutosubmitConfig:
    """Class to handle experiment configuration coming from file or database"""

    def __init__(self, expid):
        self.expid = expid
        self._conf_parser_file = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "conf",
                                              "autosubmit_" + expid + ".conf")
        self._exp_parser_file = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "conf",
                                             "expdef_" + expid + ".conf")
        self._platforms_parser_file = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "conf",
                                                   "platforms_" + expid + ".conf")
        self._jobs_parser_file = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "conf",
                                              "jobs_" + expid + ".conf")
        self._proj_parser_file = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "conf",
                                              "proj_" + expid + ".conf")

    @property
    def experiment_file(self):
        """
        Returns experiment's config file name
        """
        return self._exp_parser_file

    @property
    def platforms_file(self):
        """
        Returns experiment's queues config file name

        :return: queues config file's name
        :rtype: str
        """
        return self._platforms_parser_file

    @property
    def project_file(self):
        """
        Returns model's config file name
        """
        return self._proj_parser_file

    def get_project_dir(self):
        """
        Returns experiment's project directory

        :return: experiment's project directory
        :rtype: str
        """
        dir_templates = os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.get_expid(), BasicConfig.LOCAL_PROJ_DIR)
        # Getting project name for each type of project
        if self.get_project_type().lower() == "local":
            dir_templates = os.path.join(dir_templates, os.path.split(self.get_local_project_path())[1])
        elif self.get_project_type().lower() == "svn":
            dir_templates = os.path.join(dir_templates, self.get_svn_project_url().split('/')[-1])
        elif self.get_project_type().lower() == "git":
            dir_templates = os.path.join(dir_templates, self.get_project_destination())
        return dir_templates

    def check_conf_files(self):
        """
        Checks configuration files (autosubmit, experiment jobs and queues), looking for invalid values, missing
        required options. Prints results in log

        :return: True if everithing is correct, False if it founds any error
        :rtype: bool
        """
        Log.info('\nChecking configuration files...')
        self.reload()
        result = self._check_autosubmit_conf()
        result = result and self._check_platforms_conf()
        result = result and self._check_jobs_conf()
        result = result and self._check_expdef_conf()
        if result:
            Log.result("Configuration files OK\n")
        else:
            Log.error("Configuration files invalid\n")
        return result

    def _check_autosubmit_conf(self):
        """
        Checks experiment's autosubmit configuration file.

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """
        result = True
        result = result and AutosubmitConfig.check_exists(self._conf_parser, 'config', 'AUTOSUBMIT_VERSION')
        result = result and AutosubmitConfig.check_is_int(self._conf_parser, 'config', 'MAXWAITINGJOBS', True)
        result = result and AutosubmitConfig.check_is_int(self._conf_parser, 'config', 'TOTALJOBS', True)
        result = result and AutosubmitConfig.check_is_int(self._conf_parser, 'config', 'SAFETYSLEEPTIME', True)
        result = result and AutosubmitConfig.check_is_int(self._conf_parser, 'config', 'RETRIALS', True)

        if not result:
            Log.critical("{0} is not a valid config file".format(os.path.basename(self._conf_parser_file)))
        else:
            Log.info('{0} OK'.format(os.path.basename(self._conf_parser_file)))
        return result

    def _check_platforms_conf(self):
        """
        Checks experiment's queues configuration file.

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """
        result = True
        if len(self._platforms_parser.sections()) == 0:
            Log.warning("No remote platforms configured")

        if len(self._platforms_parser.sections()) != len(set(self._platforms_parser.sections())):
            Log.error('There are repeated platforms names')

        for section in self._platforms_parser.sections():
            result = result and AutosubmitConfig.check_is_choice(self._platforms_parser, section, 'TYPE', True,
                                                                 ['ps', 'pbs', 'sge', 'lsf', 'ecaccess', 'slurm'])
            platform_type = AutosubmitConfig.get_option(self._platforms_parser, section, 'TYPE', '').lower()
            if platform_type != 'ps':
                result = result and AutosubmitConfig.check_exists(self._platforms_parser, section, 'PROJECT')
                result = result and AutosubmitConfig.check_exists(self._platforms_parser, section, 'USER')

            if platform_type in ['pbs', 'ecaccess']:
                result = result and AutosubmitConfig.check_exists(self._platforms_parser, section, 'VERSION')

            result = result and AutosubmitConfig.check_exists(self._platforms_parser, section, 'HOST')
            result = result and AutosubmitConfig.check_is_boolean(self._platforms_parser, section,
                                                                  'ADD_PROJECT_TO_HOST', False)
            result = result and AutosubmitConfig.check_is_boolean(self._platforms_parser, section, 'TEST_SUITE', False)

        if not result:
            Log.critical("{0} is not a valid config file".format(os.path.basename(self._platforms_parser_file)))
        else:
            Log.info('{0} OK'.format(os.path.basename(self._platforms_parser_file)))
        return result

    def _check_jobs_conf(self):
        """
        Checks experiment's jobs configuration file.

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """
        result = True
        parser = self._jobs_parser
        sections = parser.sections()
        if len(sections) == 0:
            Log.warning("No remote platforms configured")

        if len(sections) != len(set(sections)):
            Log.error('There are repeated job names')

        for section in sections:
            result = result and AutosubmitConfig.check_exists(parser, section, 'FILE')
            result = result and AutosubmitConfig.check_is_boolean(parser, section, 'RERUN_ONLY', False)
            if parser.has_option(section, 'DEPENDENCIES'):
                for dependency in str(AutosubmitConfig.get_option(parser, section, 'DEPENDENCIES', '')).split(' '):
                    if '-' in dependency:
                        dependency = dependency.split('-')[0]
                    if dependency not in sections:
                        Log.error('Job {0} depends on job {1} that is not defined'.format(section, dependency))

            if parser.has_option(section, 'RERUN_DEPENDENCIES'):
                for dependency in str(AutosubmitConfig.get_option(parser, section, 'RERUN_DEPENDENCIES',
                                                                  '')).split(' '):
                    if '-' in dependency:
                        dependency = dependency.split('-')[0]
                    if dependency not in sections:
                        Log.error('Job {0} depends on job {1} that is not defined'.format(section, dependency))
            result = result and AutosubmitConfig.check_is_choice(parser, section, 'RUNNING', False,
                                                                 ['once', 'date', 'member', 'chunk'])

        if not result:
            Log.critical("{0} is not a valid config file".format(os.path.basename(self._jobs_parser_file)))
        else:
            Log.info('{0} OK'.format(os.path.basename(self._jobs_parser_file)))

        return result

    def _check_expdef_conf(self):
        """
        Checks experiment's experiment configuration file.

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """
        result = True
        parser = self._exp_parser

        result = result and AutosubmitConfig.check_exists(parser, 'DEFAULT', 'EXPID')
        result = result and AutosubmitConfig.check_exists(parser, 'DEFAULT', 'HPCARCH')

        result = result and AutosubmitConfig.check_exists(parser, 'experiment', 'DATELIST')
        result = result and AutosubmitConfig.check_exists(parser, 'experiment', 'MEMBERS')
        result = result and AutosubmitConfig.check_is_choice(parser, 'experiment', 'CHUNKSIZEUNIT', True,
                                                             ['year', 'month', 'day', 'hour'])
        result = result and AutosubmitConfig.check_is_int(parser, 'experiment', 'CHUNKSIZE', True)
        result = result and AutosubmitConfig.check_is_int(parser, 'experiment', 'NUMCHUNKS', True)
        result = result and AutosubmitConfig.check_is_choice(parser, 'experiment', 'CALENDAR', True,
                                                             ['standard', 'noleap'])

        result = result and AutosubmitConfig.check_is_boolean(parser, 'rerun', 'RERUN', True)

        if AutosubmitConfig.check_is_choice(parser, 'project', 'PROJECT_TYPE', True,
                                            ['none', 'git', 'svn', 'local']):
            project_type = AutosubmitConfig.get_option(parser, 'project', 'PROJECT_TYPE', '')

            if project_type == 'git':
                result = result and AutosubmitConfig.check_exists(parser, 'git', 'PROJECT_ORIGIN')
                result = result and AutosubmitConfig.check_exists(parser, 'git', 'PROJECT_BRANCH')
            elif project_type == 'svn':
                result = result and AutosubmitConfig.check_exists(parser, 'svn', 'PROJECT_URL')
                result = result and AutosubmitConfig.check_exists(parser, 'svn', 'PROJECT_REVISION')
            elif project_type == 'local':
                result = result and AutosubmitConfig.check_exists(parser, 'local', 'PROJECT_PATH')

            if project_type != 'none':
                result = result and AutosubmitConfig.check_exists(parser, 'project_files', 'FILE_PROJECT_CONF')
        else:
            result = False

        if not result:
            Log.critical("{0} is not a valid config file".format(os.path.basename(self._exp_parser_file)))
        else:
            Log.info('{0}  OK'.format(os.path.basename(self._exp_parser_file)))
        return result

    def check_proj(self):
        """
        Checks project config file

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """
        try:
            if self._proj_parser_file == '':
                self._proj_parser = None
            else:
                self._proj_parser = AutosubmitConfig.get_parser(self._proj_parser_file)
            return True
        except Exception as e:
            Log.error('Project conf file error: {0}', e)
            return False

    def reload(self):
        """
        Creates parser objects for configuration files
        """
        self._conf_parser = AutosubmitConfig.get_parser(self._conf_parser_file)
        self._platforms_parser = AutosubmitConfig.get_parser(self._platforms_parser_file)
        self._jobs_parser = AutosubmitConfig.get_parser(self._jobs_parser_file)
        self._exp_parser = AutosubmitConfig.get_parser(self._exp_parser_file)

    def load_parameters(self):
        """
        Load parameters from experiment and autosubmit config files. If experiment's type is not none,
        also load parameters from model's config file

        :return: a dictionary containing tuples [parameter_name, parameter_value]
        :rtype: dict
        """
        parameters = dict()
        for section in self._exp_parser.sections():
            for option in self._exp_parser.options(section):
                parameters[option] = self._exp_parser.get(section, option)
        for section in self._conf_parser.sections():
            for option in self._conf_parser.options(section):
                parameters[option] = self._conf_parser.get(section, option)

        project_type = self.get_project_type()
        if project_type != "none" and self._proj_parser is not None:
            # Load project parameters
            Log.debug("Loading project parameters...")
            parameters2 = parameters.copy()
            parameters2.update(self.load_project_parameters())
            parameters = parameters2

        return parameters

    def load_project_parameters(self):
        """
        Loads parameters from model config file

        :return: dictionary containing tuples [parameter_name, parameter_value]
        :rtype: dict
        """
        projdef = []
        for section in self._proj_parser.sections():
            projdef += self._proj_parser.items(section)

        parameters = dict()
        for item in projdef:
            parameters[item[0]] = item[1]

        return parameters

    @staticmethod
    def print_parameters(title, parameters):
        """
        Prints the parameters table in a tabular mode

        :param title: table's title
        :type title: str
        :param parameters: parameters to print
        :type: list
        """
        Log.info(title)
        Log.info("----------------------")
        Log.info("{0:<{col1}}| {1:<{col2}}".format("-- Parameter --", "-- Value --", col1=15, col2=15))
        for i in parameters:
            Log.info("{0:<{col1}}| {1:<{col2}}".format(i[0], i[1], col1=15, col2=15))
        Log.info("")

    def check_parameters(self):
        """
        Function to check configuration of Autosubmit.

        :return: True if all variables are set. If some parameter do not exist, the function returns False.
        :rtype: bool
        """
        result = True

        for section in self._conf_parser.sections():
            self.print_parameters("AUTOSUBMIT PARAMETERS - " + section, self._conf_parser.items(section))
            if "" in [item[1] for item in self._conf_parser.items(section)]:
                result = False
        for section in self._exp_parser.sections():
            self.print_parameters("EXPERIMENT PARAMETERS - " + section, self._exp_parser.items(section))
            if "" in [item[1] for item in self._exp_parser.items(section)]:
                result = False

        project_type = self.get_project_type()
        if project_type != "none" and self._proj_parser is not None:
            for section in self._proj_parser.sections():
                self.print_parameters("PROJECT PARAMETERS - " + section, self._proj_parser.items(section))
                if "" in [item[1] for item in self._proj_parser.items(section)]:
                    result = False

        return result

    def get_expid(self):
        """
        Returns experiment identifier read from experiment's config file

        :return: experiment identifier
        :rtype: str
        """
        return self._exp_parser.get('DEFAULT', 'EXPID')

    def set_expid(self, exp_id):
        """
        Set experiment identifier in autosubmit and experiment config files

        :param exp_id: experiment identifier to store
        :type exp_id: str
        """
        # Experiment conf
        content = file(self._exp_parser_file).read()
        if re.search('EXPID =.*', content):
            content = content.replace(re.search('EXPID =.*', content).group(0), "EXPID = " + exp_id)
        file(self._exp_parser_file, 'w').write(content)

        content = file(self._conf_parser_file).read()
        if re.search('EXPID =.*', content):
            content = content.replace(re.search('EXPID =.*', content).group(0), "EXPID = " + exp_id)
        file(self._conf_parser_file, 'w').write(content)

    def get_project_type(self):
        """
        Returns project type from experiment config file

        :return: project type
        :rtype: str
        """
        return self._exp_parser.get('project', 'PROJECT_TYPE').lower()

    def get_file_project_conf(self):
        """
        Returns path to project config file from experiment config file

        :return: path to project config file
        :rtype: str
        """
        return self._exp_parser.get('project_files', 'FILE_PROJECT_CONF')

    def get_git_project_origin(self):
        """
        Returns git origin from experiment config file

        :return: git origin
        :rtype: str
        """
        return self._exp_parser.get('git', 'PROJECT_ORIGIN')

    def get_git_project_branch(self):
        """
        Returns git branch  from experiment's config file

        :return: git branch
        :rtype: str
        """
        return self._exp_parser.get('git', 'PROJECT_BRANCH')

    def get_git_project_commit(self):
        """
        Returns git commit from experiment's config file

        :return: git commit
        :rtype: str
        """
        return self._exp_parser.get('git', 'PROJECT_COMMIT')

    def get_project_destination(self):
        """
        Returns git commit from experiment's config file

        :return: git commit
        :rtype: str
        """
        value = self._exp_parser.get('project', 'PROJECT_DESTINATION')
        if not value:
            if self.get_project_type().lower() == "local":
                value = os.path.split(self.get_local_project_path())[1]
            elif self.get_project_type().lower() == "svn":
                value = self.get_svn_project_url().split('/')[-1]
            elif self.get_project_type().lower() == "git":
                value = self.get_git_project_origin().split('/')[-1].split('.')[-2]
        return value

    def set_git_project_commit(self):
        """
        Function to register in the configuration the commit SHA of the git project version.
        """
        save = False
        project_branch_sha = None
        full_proj_dir = os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.get_expid(), BasicConfig.LOCAL_PROJ_DIR)
        project_name = listdir(full_proj_dir)[0]
        full_project_path = os.path.join(full_proj_dir, project_name)
        (status1, output) = getstatusoutput("cd " + full_project_path)
        (status2, output) = getstatusoutput("cd " + full_project_path + "; " +
                                            "git rev-parse --abbrev-ref HEAD")
        if status1 == 0 and status2 == 0:
            project_branch = output
            Log.debug("Project branch is: " + project_branch)

            (status1, output) = getstatusoutput("cd " + full_project_path)
            (status2, output) = getstatusoutput("cd " + full_project_path + "; " +
                                                "git rev-parse HEAD")
            if status1 == 0 and status2 == 0:
                project_sha = output
                save = True
                Log.debug("Project commit SHA is: " + project_sha)
                project_branch_sha = project_branch + " " + project_sha
            else:
                Log.critical("Failed to retrieve project commit SHA...")

        else:
            Log.critical("Failed to retrieve project branch...")

            # register changes
        if save:
            content = file(self._exp_parser_file).read()
            if re.search('PROJECT_COMMIT =.*', content):
                content = content.replace(re.search('PROJECT_COMMIT =.*', content).group(0),
                                          "PROJECT_COMMIT = " + project_branch_sha)
            file(self._exp_parser_file, 'w').write(content)
            Log.debug("Project commit SHA succesfully registered to the configuration file.")
            return True
        else:
            Log.critical("Changes NOT registered to the configuration file...")
        return False

    def get_svn_project_url(self):
        """
        Gets subversion project url

        :return: subversion project url
        :rtype: str
        """
        return self._exp_parser.get('svn', 'PROJECT_URL')

    def get_svn_project_revision(self):
        """
        Get revision for subversion project

        :return: revision for subversion project
        :rtype: str
        """
        return self._exp_parser.get('svn', 'PROJECT_REVISION')

    def get_local_project_path(self):
        """
        Gets path to origin for local project

        :return: path to local project
        :rtype: str
        """
        return self._exp_parser.get('local', 'PROJECT_PATH')

    def get_date_list(self):
        """
        Returns startdates list from experiment's config file

        :return: experiment's startdates
        :rtype: list
        """
        date_list = list()
        string = self._exp_parser.get('experiment', 'DATELIST')
        if not string.startswith("["):
            string = '[{0}]'.format(string)
        split_string = nestedExpr('[', ']').parseString(string).asList()
        string_date = None
        for split in split_string[0]:
            if type(split) is list:
                for split_in in split:
                    date_list.append(parse_date(string_date + split_in))
                string_date = None
            else:
                if string_date is not None:
                    date_list.append(parse_date(string_date))
                string_date = split
        if string_date is not None:
            date_list.append(parse_date(string_date))
        return date_list

    def get_num_chunks(self):
        """
        Returns number of chunks to run for each member

        :return: number of chunks
        :rtype: int
        """
        return int(self._exp_parser.get('experiment', 'NUMCHUNKS'))

    def get_chunk_size_unit(self):
        """
        Unit for the chunk length

        :return: Unit for the chunk length  Options: {hour, day, month, year}
        :rtype: str
        """
        return self._exp_parser.get('experiment', 'CHUNKSIZEUNIT').lower()

    def get_member_list(self):
        """
        Returns members list from experiment's config file

        :return: experiment's members
        :rtype: list
        """
        return self._exp_parser.get('experiment', 'MEMBERS').split(' ')

    def get_rerun(self):
        """
        Returns startdates list from experiment's config file

        :return: rerurn value
        :rtype: list
        """
        return self._exp_parser.get('rerun', 'RERUN').lower()

    def get_chunk_list(self):
        """
        Returns chunk list from experiment's config file

        :return: experiment's chunks
        :rtype: list
        """
        return self._exp_parser.get('rerun', 'CHUNKLIST')

    def get_platform(self):
        """
        Returns main platforms from experiment's config file

        :return: main platforms
        :rtype: str
        """
        return self._exp_parser.get('experiment', 'HPCARCH').lower()

    def set_platform(self, hpc):
        """
        Sets main platforms in experiment's config file

        :param hpc: main platforms
        :type: str
        """
        content = file(self._exp_parser_file).read()
        if re.search('HPCARCH =.*', content):
            content = content.replace(re.search('HPCARCH =.*', content).group(0), "HPCARCH = " + hpc)
        file(self._exp_parser_file, 'w').write(content)

    def set_version(self, autosubmit_version):
        """
        Sets autosubmit's version in autosubmit's config file

        :param autosubmit_version: autosubmit's version
        :type autosubmit_version: str
        """
        content = file(self._conf_parser_file).read()
        if re.search('AUTOSUBMIT_VERSION =.*', content):
            content = content.replace(re.search('AUTOSUBMIT_VERSION =.*', content).group(0),
                                      "AUTOSUBMIT_VERSION = " + autosubmit_version)
        file(self._conf_parser_file, 'w').write(content)

    def get_total_jobs(self):
        """
        Returns max number of running jobs  from autosubmit's config file

        :return: max number of running jobs
        :rtype: int
        """
        return int(self._conf_parser.get('config', 'TOTALJOBS'))

    def get_max_waiting_jobs(self):
        """
        Returns max number of waitng jobs from autosubmit's config file

        :return: main platforms
        :rtype: int
        """
        return int(self._conf_parser.get('config', 'MAXWAITINGJOBS'))

    def get_safetysleeptime(self):
        """
        Returns safety sleep time from autosubmit's config file

        :return: safety sleep time
        :rtype: int
        """
        return int(self._conf_parser.get('config', 'SAFETYSLEEPTIME'))

    def set_safetysleeptime(self, sleep_time):
        """
        Sets autosubmit's version in autosubmit's config file

        :param sleep_time: value to set
        :type sleep_time: int
        """
        content = file(self._conf_parser_file).read()
        content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0),
                                  "SAFETYSLEEPTIME = %d" % sleep_time)
        file(self._conf_parser_file, 'w').write(content)

    def get_retrials(self):
        """
        Returns max number of retrials for job from autosubmit's config file

        :return: safety sleep time
        :rtype: int
        """
        return int(self._conf_parser.get('config', 'RETRIALS'))

    @staticmethod
    def get_parser(file_path):
        """
        Gets parser for given file

        :param file_path: path to file to be parsed
        :type file_path: str
        :return: parser
        :rtype: SafeConfigParser
        """
        parser = SafeConfigParser()
        parser.optionxform = str
        parser.read(file_path)
        return parser

    def read_platforms_conf(self):
        """
        Read platforms configuration file and create defined platforms. Also adds the local remote_platform to the list

        :return: platforms defined on file and local remote_platform. None if configuration is invalid
        :rtype: list
        """
        parser = self._platforms_parser

        platforms = dict()
        local_platform = LocalPlatform(self.expid)
        local_platform.name = 'local'
        local_platform.type = 'local'
        local_platform.version = ''
        local_platform.queue = ''
        local_platform.set_host(platform.node())
        local_platform.set_scratch(os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.expid, BasicConfig.LOCAL_TMP_DIR))
        local_platform.set_project(self.expid)
        local_platform.set_budget(self.expid)
        local_platform.set_user('')
        local_platform.update_cmds()

        platforms['local'] = local_platform
        for section in parser.sections():
            platform_type = AutosubmitConfig.get_option(parser, section, 'TYPE', '').lower()
            platform_version = AutosubmitConfig.get_option(parser, section, 'VERSION', '')
            try:
                if platform_type == 'pbs':
                    remote_platform = PBSPlatform(self.expid, platform_version)
                elif platform_type == 'sge':
                    remote_platform = SgePlatform(self.expid)
                elif platform_type == 'ps':
                    remote_platform = PsPlatform(self.expid)
                elif platform_type == 'lsf':
                    remote_platform = LsfPlatform(self.expid)
                elif platform_type == 'ecaccess':
                    remote_platform = EcPlatform(self.expid, platform_version)
                elif platform_type == 'slurm':
                    remote_platform = SlurmPlatform(self.expid)
                elif platform_type == '':
                    Log.error("Queue type not specified".format(platform_type))
                    return None
                else:
                    Log.error("Queue type {0} not defined".format(platform_type))
                    return None
            except HPCPlatformException as e:
                Log.error("Queue exception: {0}".format(e.message))
                return None

            remote_platform.type = platform_type
            remote_platform.version = platform_version
            if AutosubmitConfig.get_option(parser, section, 'ADD_PROJECT_TO_HOST', '').lower() == 'true':
                host = '{0}-{1}'.format(AutosubmitConfig.get_option(parser, section, 'HOST', None),
                                        AutosubmitConfig.get_option(parser, section, 'PROJECT', None))
            else:
                host = AutosubmitConfig.get_option(parser, section, 'HOST', None)
            remote_platform.set_host(host)
            remote_platform.set_project(AutosubmitConfig.get_option(parser, section, 'PROJECT', None))
            remote_platform.set_budget(AutosubmitConfig.get_option(parser, section, 'BUDGET', remote_platform.project))
            remote_platform.set_user(AutosubmitConfig.get_option(parser, section, 'USER', None))
            remote_platform.set_scratch(AutosubmitConfig.get_option(parser, section, 'SCRATCH_DIR', None))
            remote_platform._default_queue = AutosubmitConfig.get_option(parser, section, 'QUEUE', None)
            remote_platform._serial_queue = AutosubmitConfig.get_option(parser, section, 'SERIAL_QUEUE', None)
            remote_platform.name = section.lower()
            remote_platform.update_cmds()
            platforms[section.lower()] = remote_platform

        for section in parser.sections():
            if parser.has_option(section, 'SERIAL_PLATFORM'):
                platforms[section.lower()].set_serial_platform(platforms[AutosubmitConfig.get_option(parser, section,
                                                                                                     'SERIAL_PLATFORM',
                                                                                                     None).lower()])

        return platforms

    @staticmethod
    def get_option(parser, section, option, default):
        """
        Gets an option from given parser

        :param parser: parser to use
        :type parser: SafeConfigParser
        :param section: section that contains the option
        :type section: str
        :param option: option to get
        :type option: str
        :param default: value to be returned if option is not present
        :type default: object
        :return: option value
        :rtype: str
        """
        if parser.has_option(section, option):
            return parser.get(section, option)
        else:
            return default

    @staticmethod
    def get_bool_option(parser, section, option, default):
        """
        Gets a boolean option from given parser

        :param parser: parser to use
        :type parser: SafeConfigParser
        :param section: section that contains the option
        :type section: str
        :param option: option to get
        :type option: str
        :param default: value to be returned if option is not present
        :type default: bool
        :return: option value
        :rtype: bool
        """
        if parser.has_option(section, option):
            return parser.get(section, option).lower().strip() == 'true'
        else:
            return default

    @staticmethod
    def check_exists(parser, section, option):
        """
        Checks if an option exists in given parser

        :param parser: parser to use
        :type parser: SafeConfigParser
        :param section: section that contains the option
        :type section: str
        :param option: option to check
        :type option: str
        :return: True if option exists, False otherwise
        :rtype: bool
        """
        if parser.has_option(section, option):
            return True
        else:
            Log.error('Option {0} in section {1} not found'.format(option, section))
            return False

    @staticmethod
    def check_is_boolean(parser, section, option, must_exist):
        """
        Checks if an option is a boolean value in given parser

        :param parser: parser to use
        :type parser: SafeConfigParser
        :param section: section that contains the option
        :type section: str
        :param option: option to check
        :type option: str
        :param must_exist: if True, option must exist
        :type must_exist: bool
        :return: True if option value is boolean, False otherwise
        :rtype: bool
        """
        if must_exist and not AutosubmitConfig.check_exists(parser, section, option):
            Log.error('Option {0} in section {1} must exist'.format(option, section))
            return False
        if AutosubmitConfig.get_option(parser, section, option, 'false').lower() not in ['false', 'true']:
            Log.error('Option {0} in section {1} must be true or false'.format(option, section))
            return False
        return True

    @staticmethod
    def check_is_choice(parser, section, option, must_exist, choices):
        """
        Checks if an option is a valid choice in given parser

        :param parser: parser to use
        :type parser: SafeConfigParser
        :param section: section that contains the option
        :type section: str
        :param option: option to check
        :type option: str
        :param must_exist: if True, option must exist
        :type must_exist: bool
        :param choices: valid choices
        :type choices: list
        :return: True if option value is a valid choice, False otherwise
        :rtype: bool
        """
        if must_exist and not AutosubmitConfig.check_exists(parser, section, option):
            return False
        value = AutosubmitConfig.get_option(parser, section, option, choices[0])
        if value.lower() not in choices:
            Log.error('Value {2} in option {0} in section {1} is not a valid choice'.format(option, section, value))
            return False
        return True

    @staticmethod
    def check_is_int(parser, section, option, must_exist):
        """
        Checks if an option is an integer value in given parser

        :param parser: parser to use
        :type parser: SafeConfigParser
        :param section: section that contains the option
        :type section: str
        :param option: option to check
        :type option: str
        :param must_exist: if True, option must exist
        :type must_exist: bool
        :return: True if option value is integer, False otherwise
        :rtype: bool
        """
        if must_exist and not AutosubmitConfig.check_exists(parser, section, option):
            return False
        value = AutosubmitConfig.get_option(parser, section, option, '1')
        try:
            int(value)
        except ValueError:
            Log.error('Option {0} in section {1} is not valid an integer'.format(option, section))
            return False
        return True

    @staticmethod
    def check_regex(parser, section, option, must_exist, regex):
        """
        Checks if an option complies with a regular expression in given parser

        :param parser: parser to use
        :type parser: SafeConfigParser
        :param section: section that contains the option
        :type section: str
        :param option: option to check
        :type option: str
        :param must_exist: if True, option must exist
        :type must_exist: bool
        :param regex: regular expression to check
        :type regex: str
        :return: True if option complies with regex, False otherwise
        :rtype: bool
        """
        if must_exist and not AutosubmitConfig.check_exists(parser, section, option):
            return False
        prog = re.compile(regex)
        value = AutosubmitConfig.get_option(parser, section, option, '1')
        if not prog.match(value):
            Log.error('Option {0} in section {1} is not valid: {2}'.format(option, section, value))
            return False
        return True

    @staticmethod
    def check_json(key, value):
        """
        Checks if value is a valid json

        :param key: key to check
        :type key: str
        :param value: value
        :type value: str
        :return: True if value is a valid json, False otherwise
        :rtype: bool
        """
        # noinspection PyBroadException
        try:
            nestedExpr('[', ']').parseString(value).asList()
            return True
        except:
            Log.error("Invalid value {0}: {1}", key, value)
            return False




