#!/usr/bin/env python

# Copyright 2015 Earth Sciences Department, BSC-CNS

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
try:
    # noinspection PyCompatibility
    from configparser import SafeConfigParser
except ImportError:
    # noinspection PyCompatibility
    from ConfigParser import SafeConfigParser
import os
import re
import subprocess

from pyparsing import nestedExpr

from autosubmit.date.chunk_date_lib import parse_date
from autosubmit.config.log import Log
from autosubmit.config.basicConfig import BasicConfig


class AutosubmitConfig:
    """
    Class to handle experiment configuration coming from file or database

    :param expid: experiment identifier
    :type expid: str
    """

    def __init__(self, expid, basic_config, parser_factory):
        self.expid = expid

        self.basic_config = basic_config

        self.parser_factory = parser_factory

        self._conf_parser_file = os.path.join(self.basic_config.LOCAL_ROOT_DIR, expid, "conf",
                                              "autosubmit_" + expid + ".conf")
        self._exp_parser_file = os.path.join(self.basic_config.LOCAL_ROOT_DIR, expid, "conf",
                                             "expdef_" + expid + ".conf")
        self._platforms_parser_file = os.path.join(self.basic_config.LOCAL_ROOT_DIR, expid, "conf",
                                                   "platforms_" + expid + ".conf")
        self._jobs_parser_file = os.path.join(self.basic_config.LOCAL_ROOT_DIR, expid, "conf",
                                              "jobs_" + expid + ".conf")
        self._proj_parser_file = os.path.join(self.basic_config.LOCAL_ROOT_DIR, expid, "conf",
                                              "proj_" + expid + ".conf")

    @property
    def experiment_file(self):
        """
        Returns experiment's config file name
        """
        return self._exp_parser_file

    @property
    def platforms_parser(self):
        """
        Returns experiment's platforms parser object

        :return: platforms config parser object
        :rtype: SafeConfigParser
        """
        return self._platforms_parser

    @property
    def platforms_file(self):
        """
        Returns experiment's platforms config file name

        :return: platforms config file's name
        :rtype: str
        """
        return self._platforms_parser_file

    @property
    def project_file(self):
        """
        Returns project's config file name
        """
        return self._proj_parser_file

    @property
    def jobs_file(self):
        """
        Returns project's jobs file name
        """
        return self._jobs_parser_file

    def get_project_dir(self):
        """
        Returns experiment's project directory

        :return: experiment's project directory
        :rtype: str
        """
        dir_templates = os.path.join(self.basic_config.LOCAL_ROOT_DIR, self.expid, BasicConfig.LOCAL_PROJ_DIR,
                                     self.get_project_destination())
        return dir_templates

    def get_wallclock(self, section):
        """
        Gets wallclock for the given job type
        :param section: job type
        :type section: str
        :return: wallclock time
        :rtype: str
        """
        return AutosubmitConfig.get_option(self.jobs_parser, section, 'WALLCLOCK', '')

    def get_processors(self, section):
        """
        Gets processors needed for the given job type
        :param section: job type
        :type section: str
        :return: wallclock time
        :rtype: str
        """
        return int(AutosubmitConfig.get_option(self.jobs_parser, section, 'PROCESSORS', 1))

    def get_threads(self, section):
        """
        Gets threads needed for the given job type
        :param section: job type
        :type section: str
        :return: threads needed
        :rtype: str
        """
        return int(AutosubmitConfig.get_option(self.jobs_parser, section, 'THREADS', 1))

    def get_tasks(self, section):
        """
        Gets tasks needed for the given job type
        :param section: job type
        :type section: str
        :return: tasks needed
        :rtype: str
        """
        return int(AutosubmitConfig.get_option(self.jobs_parser, section, 'TASKS', 1))

    def get_memory(self, section):
        """
        Gets memory needed for the given job type
        :param section: job type
        :type section: str
        :return: memory needed
        :rtype: str
        """
        return int(AutosubmitConfig.get_option(self.jobs_parser, section, 'MEMORY', 0))

    def check_conf_files(self):
        """
        Checks configuration files (autosubmit, experiment jobs and platforms), looking for invalid values, missing
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

        self._conf_parser.read(self._conf_parser_file)
        result = result and AutosubmitConfig.check_exists(self._conf_parser, 'config', 'AUTOSUBMIT_VERSION')
        result = result and AutosubmitConfig.check_is_int(self._conf_parser, 'config', 'MAXWAITINGJOBS', True)
        result = result and AutosubmitConfig.check_is_int(self._conf_parser, 'config', 'TOTALJOBS', True)
        result = result and AutosubmitConfig.check_is_int(self._conf_parser, 'config', 'SAFETYSLEEPTIME', True)
        result = result and AutosubmitConfig.check_is_int(self._conf_parser, 'config', 'RETRIALS', True)
        result = result and AutosubmitConfig.check_is_boolean(self._conf_parser, 'mail', 'NOTIFICATIONS', False)

        if self.get_notifications() == 'true':
            for mail in self.get_mails_to():
                if not self.is_valid_mail_address(mail):
                    Log.warning('One or more of the email addresses configured for the mail notifications are wrong')
                    break

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
            result = result and AutosubmitConfig.check_exists(self._platforms_parser, section, 'TYPE')
            platform_type = AutosubmitConfig.get_option(self._platforms_parser, section, 'TYPE', '').lower()
            if platform_type != 'ps':
                result = result and AutosubmitConfig.check_exists(self._platforms_parser, section, 'PROJECT')
                result = result and AutosubmitConfig.check_exists(self._platforms_parser, section, 'USER')

            # if platform_type in ['pbs', 'ecaccess']:
            #     result = result and AutosubmitConfig.check_exists(self._platforms_parser, section, 'VERSION')

            result = result and AutosubmitConfig.check_exists(self._platforms_parser, section, 'HOST')
            result = result and AutosubmitConfig.check_is_boolean(self._platforms_parser, section,
                                                                  'ADD_PROJECT_TO_HOST', False)
            result = result and AutosubmitConfig.check_is_boolean(self._platforms_parser, section, 'TEST_SUITE', False)
            result = result and AutosubmitConfig.check_is_int(self._platforms_parser, section, 'MAX_WAITING_JOBS',
                                                              False)
            result = result and AutosubmitConfig.check_is_int(self._platforms_parser, section, 'TOTAL_JOBS', False)

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
        parser = self.jobs_parser
        sections = parser.sections()
        platforms = self._platforms_parser.sections()
        platforms.append('LOCAL')
        if len(sections) == 0:
            Log.warning("No remote platforms configured")

        if len(sections) != len(set(sections)):
            Log.error('There are repeated job names')

        for section in sections:
            result = result and AutosubmitConfig.check_exists(parser, section, 'FILE')
            result = result and AutosubmitConfig.check_is_boolean(parser, section, 'RERUN_ONLY', False)

            if parser.has_option(section, 'PLATFORM'):
                result = result and AutosubmitConfig.check_is_choice(parser, section, 'PLATFORM', False, platforms)

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
                self._proj_parser = AutosubmitConfig.get_parser(self.parser_factory, self._proj_parser_file)
            return True
        except Exception as e:
            Log.error('Project conf file error: {0}', e)
            return False

    def reload(self):
        """
        Creates parser objects for configuration files
        """
        self._conf_parser = AutosubmitConfig.get_parser(self.parser_factory, self._conf_parser_file)
        self._platforms_parser = AutosubmitConfig.get_parser(self.parser_factory, self._platforms_parser_file)
        self.jobs_parser = AutosubmitConfig.get_parser(self.parser_factory, self._jobs_parser_file)
        self._exp_parser = AutosubmitConfig.get_parser(self.parser_factory, self._exp_parser_file)
        if self._proj_parser_file == '':
            self._proj_parser = None
        else:
            self._proj_parser = AutosubmitConfig.get_parser(self.parser_factory, self._proj_parser_file)

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

    def set_expid(self, exp_id):
        """
        Set experiment identifier in autosubmit and experiment config files

        :param exp_id: experiment identifier to store
        :type exp_id: str
        """
        # Experiment conf
        content = open(self._exp_parser_file).read()
        if re.search('EXPID =.*', content):
            content = content.replace(re.search('EXPID =.*', content).group(0), "EXPID = " + exp_id)
        open(self._exp_parser_file, 'w').write(content)

        content = open(self._conf_parser_file).read()
        if re.search('EXPID =.*', content):
            content = content.replace(re.search('EXPID =.*', content).group(0), "EXPID = " + exp_id)
        open(self._conf_parser_file, 'w').write(content)

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

    def get_file_jobs_conf(self):
        """
        Returns path to project config file from experiment config file

        :return: path to project config file
        :rtype: str
        """
        return AutosubmitConfig.get_option(self._exp_parser, 'project_files', 'FILE_JOBS_CONF', '')

    def get_git_project_origin(self):
        """
        Returns git origin from experiment config file

        :return: git origin
        :rtype: str
        """
        return AutosubmitConfig.get_option(self._exp_parser, 'git', 'PROJECT_ORIGIN', '')

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

    def set_git_project_commit(self, as_conf):
        """
        Function to register in the configuration the commit SHA of the git project version.
        :param as_conf: Configuration class for exteriment
        :type as_conf: AutosubmitConfig
        """
        full_project_path = as_conf.get_project_dir()
        try:
            output = subprocess.check_output("cd {0}; git rev-parse --abbrev-ref HEAD".format(full_project_path),
                                             shell=True)
        except subprocess.CalledProcessError:
            Log.critical("Failed to retrieve project branch...")
            return False

        project_branch = output
        Log.debug("Project branch is: " + project_branch)
        try:
            output = subprocess.check_output("cd {0}; git rev-parse HEAD".format(full_project_path), shell=True)
        except subprocess.CalledProcessError:
            Log.critical("Failed to retrieve project commit SHA...")
            return False
        project_sha = output
        Log.debug("Project commit SHA is: " + project_sha)

        # register changes
        content = open(self._exp_parser_file).read()
        if re.search('PROJECT_BRANCH =.*', content):
            content = content.replace(re.search('PROJECT_BRANCH =.*', content).group(0),
                                      "PROJECT_BRANCH = " + project_branch)
        if re.search('PROJECT_COMMIT =.*', content):
            content = content.replace(re.search('PROJECT_COMMIT =.*', content).group(0),
                                      "PROJECT_COMMIT = " + project_sha)
        open(self._exp_parser_file, 'w').write(content)
        Log.debug("Project commit SHA succesfully registered to the configuration file.")
        return True

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
                    if split_in.find("-") != -1:
                        numbers = split_in.split("-")
                        for count in range(int(numbers[0]), int(numbers[1]) + 1):
                            date_list.append(parse_date(string_date + str(count).zfill(len(numbers[0]))))
                    else:
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
        member_list = list()
        string = self._exp_parser.get('experiment', 'MEMBERS')
        if not string.startswith("["):
            string = '[{0}]'.format(string)
        split_string = nestedExpr('[', ']').parseString(string).asList()
        string_member = None
        for split in split_string[0]:
            if type(split) is list:
                for split_in in split:
                    if split_in.find("-") != -1:
                        numbers = split_in.split("-")
                        for count in range(int(numbers[0]), int(numbers[1]) + 1):
                            member_list.append(string_member + str(count).zfill(len(numbers[0])))
                    else:
                        member_list.append(string_member + split_in)
                string_member = None
            else:
                if string_member is not None:
                    member_list.append(string_member)
                string_member = split
        if string_member is not None:
            member_list.append(string_member)
        return member_list

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
        return self._exp_parser.get('experiment', 'HPCARCH')

    def set_platform(self, hpc):
        """
        Sets main platforms in experiment's config file

        :param hpc: main platforms
        :type: str
        """
        content = open(self._exp_parser_file).read()
        if re.search('HPCARCH =.*', content):
            content = content.replace(re.search('HPCARCH =.*', content).group(0), "HPCARCH = " + hpc)
        open(self._exp_parser_file, 'w').write(content)

    def set_version(self, autosubmit_version):
        """
        Sets autosubmit's version in autosubmit's config file

        :param autosubmit_version: autosubmit's version
        :type autosubmit_version: str
        """
        content = open(self._conf_parser_file).read()
        if re.search('AUTOSUBMIT_VERSION =.*', content):
            content = content.replace(re.search('AUTOSUBMIT_VERSION =.*', content).group(0),
                                      "AUTOSUBMIT_VERSION = " + autosubmit_version)
        open(self._conf_parser_file, 'w').write(content)

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
        content = open(self._conf_parser_file).read()
        content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0),
                                  "SAFETYSLEEPTIME = %d" % sleep_time)
        open(self._conf_parser_file, 'w').write(content)

    def get_retrials(self):
        """
        Returns max number of retrials for job from autosubmit's config file

        :return: safety sleep time
        :rtype: int
        """
        return int(self._conf_parser.get('config', 'RETRIALS'))

    def get_notifications(self):
        """
        Returns if the user has enabled the notifications from autosubmit's config file

        :return: if notifications
        :rtype: bool
        """
        return self.get_option(self._conf_parser, 'mail', 'NOTIFICATIONS', 'false').lower()

    def get_mails_to(self):
        """
        Returns the address where notifications will be sent from autosubmit's config file

        :return: mail address
        :rtype: [str]
        """
        return [str(x) for x in self.get_option(self._conf_parser, 'mail', 'TO', '').split(' ')]

    @staticmethod
    def is_valid_mail_address(mail_address):
        if re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', mail_address):
            return True
        else:
            return False

    @staticmethod
    def get_parser(parser_factory, file_path):
        """
        Gets parser for given file

        :param parser_factory:
        :param file_path: path to file to be parsed
        :type file_path: str
        :return: parser
        :rtype: SafeConfigParser
        """
        parser = parser_factory.create_parser()
        parser.optionxform = str
        parser.read(file_path)
        return parser

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
        if value not in choices:
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
