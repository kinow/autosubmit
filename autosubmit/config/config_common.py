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

from bscearth.utils.date import parse_date
from bscearth.utils.log import Log
from autosubmit.config.basicConfig import BasicConfig


class AutosubmitConfig(object):
    """
    Class to handle experiment configuration coming from file or database

    :param expid: experiment identifier
    :type expid: str
    """

    def __init__(self, expid, basic_config, parser_factory):
        self.expid = expid

        self.basic_config = basic_config

        self.parser_factory = parser_factory

        self._conf_parser = None
        self._conf_parser_file = os.path.join(self.basic_config.LOCAL_ROOT_DIR, expid, "conf",
                                              "autosubmit_" + expid + ".conf")
        self._exp_parser = None
        self._exp_parser_file = os.path.join(self.basic_config.LOCAL_ROOT_DIR, expid, "conf",
                                             "expdef_" + expid + ".conf")
        self._platforms_parser = None
        self._platforms_parser_file = os.path.join(self.basic_config.LOCAL_ROOT_DIR, expid, "conf",
                                                   "platforms_" + expid + ".conf")
        self._jobs_parser = None
        self._jobs_parser_file = os.path.join(self.basic_config.LOCAL_ROOT_DIR, expid, "conf",
                                              "jobs_" + expid + ".conf")
        self._proj_parser = None
        self._proj_parser_file = os.path.join(self.basic_config.LOCAL_ROOT_DIR, expid, "conf",
                                              "proj_" + expid + ".conf")

        self.check_proj_file()

    @property
    def jobs_parser(self):
        return self._jobs_parser

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

    def check_proj_file(self):
        """
        Add a section header to the project's configuration file (if not exists)
        """
        if os.path.exists(self._proj_parser_file):
            with open(self._proj_parser_file, 'r+') as f:
                first_line = f.readline()
                if not re.match('[[a-zA-Z0-9]*]', first_line):
                    content = f.read()
                    f.seek(0, 0)
                    f.write('[DEFAULT]'.rstrip('\r\n') + '\n' + first_line + content)

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
        return self._jobs_parser.get_option(section, 'WALLCLOCK', '')

    def get_processors(self, section):
        """
        Gets processors needed for the given job type
        :param section: job type
        :type section: str
        :return: wallclock time
        :rtype: str
        """
        return str(self._jobs_parser.get_option(section, 'PROCESSORS', 1))

    def get_threads(self, section):
        """
        Gets threads needed for the given job type
        :param section: job type
        :type section: str
        :return: threads needed
        :rtype: str
        """
        return str(self._jobs_parser.get_option(section, 'THREADS', 1))

    def get_tasks(self, section):
        """
        Gets tasks needed for the given job type
        :param section: job type
        :type section: str
        :return: tasks (processes) per host
        :rtype: str
        """
        return str(self._jobs_parser.get_option(section, 'TASKS', 0))

    def get_scratch_free_space(self, section):
        """
        Gets scratch free space needed for the given job type
        :param section: job type
        :type section: str
        :return: percentage of scratch free space needed
        :rtype: int
        """
        return int(self._jobs_parser.get_option(section, 'SCRATCH_FREE_SPACE', 0))

    def get_memory(self, section):
        """
        Gets memory needed for the given job type
        :param section: job type
        :type section: str
        :return: memory needed
        :rtype: str
        """
        return str(self._jobs_parser.get_option(section, 'MEMORY', ''))

    def get_memory_per_task(self, section):
        """
        Gets memory per task needed for the given job type
        :param section: job type
        :type section: str
        :return: memory per task needed
        :rtype: str
        """
        return str(self._jobs_parser.get_option(section, 'MEMORY_PER_TASK', ''))

    def get_migrate_user_to(self, section):
        """
        Returns the user to change to from platform config file.

        :return: migrate user to
        :rtype: str
        """
        return self._platforms_parser.get_option(section, 'USER_TO', '').lower()

    def set_new_user(self, section, new_user):
        """
        Sets new user for given platform
        :param new_user: 
        :param section: platform name
        :type: str
        """
        content = open(self._platforms_parser_file).read()
        if re.search(section, content):
            content = content.replace(re.search('USER =.*', content).group(0), "USER = " + new_user)
        open(self._platforms_parser_file, 'w').write(content)

    def get_migrate_project_to(self, section):
        """
        Returns the project to change to from platform config file.

        :return: migrate project to
        :rtype: str
        """
        return self._platforms_parser.get_option(section, 'PROJECT_TO', '').lower()

    def set_new_project(self, section, new_project):
        """
        Sets new project for given platform
        :param new_project: 
        :param section: platform name
        :type: str
        """
        content = open(self._platforms_parser_file).read()
        if re.search(section, content):
            content = content.replace(re.search('PROJECT =.*', content).group(0), "PROJECT = " + new_project)
        open(self._platforms_parser_file, 'w').write(content)

    def get_custom_directives(self, section):
        """
        Gets custom directives needed for the given job type
        :param section: job type
        :type section: str
        :return: custom directives needed
        :rtype: str
        """
        return str(self._jobs_parser.get_option(section, 'CUSTOM_DIRECTIVES', ''))

    def check_conf_files(self):
        """
        Checks configuration files (autosubmit, experiment jobs and platforms), looking for invalid values, missing
        required options. Prints results in log

        :return: True if everithing is correct, False if it founds any error
        :rtype: bool
        """
        Log.info('\nChecking configuration files...')
        self.reload()
        result = self.check_autosubmit_conf()
        result = result and self.check_platforms_conf()
        result = result and self.check_jobs_conf()
        result = result and self.check_expdef_conf()
        if result:
            Log.result("Configuration files OK\n")
        else:
            Log.error("Configuration files invalid\n")
        return result

    def check_autosubmit_conf(self):
        """
        Checks experiment's autosubmit configuration file.

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """
        result = True

        self._conf_parser.read(self._conf_parser_file)
        result = result and self._conf_parser.check_exists('config', 'AUTOSUBMIT_VERSION')
        result = result and self._conf_parser.check_is_int('config', 'MAXWAITINGJOBS', True)
        result = result and self._conf_parser.check_is_int('config', 'TOTALJOBS', True)
        result = result and self._conf_parser.check_is_int('config', 'SAFETYSLEEPTIME', True)
        result = result and self._conf_parser.check_is_int('config', 'RETRIALS', True)
        result = result and self._conf_parser.check_is_boolean('mail', 'NOTIFICATIONS', False)
        result = result and self.is_valid_communications_library()
        result = result and self.is_valid_storage_type()

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

    def check_platforms_conf(self):
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
            result = result and self._platforms_parser.check_exists(section, 'TYPE')
            platform_type = self._platforms_parser.get_option(section, 'TYPE', '').lower()
            if platform_type != 'ps':
                result = result and self._platforms_parser.check_exists(section, 'PROJECT')
                result = result and self._platforms_parser.check_exists(section, 'USER')

            result = result and self._platforms_parser.check_exists(section, 'HOST')
            result = result and self._platforms_parser.check_exists(section, 'SCRATCH_DIR')
            result = result and self._platforms_parser.check_is_boolean(section,
                                                                        'ADD_PROJECT_TO_HOST', False)
            result = result and self._platforms_parser.check_is_boolean(section, 'TEST_SUITE', False)
            result = result and self._platforms_parser.check_is_int(section, 'MAX_WAITING_JOBS',
                                                                    False)
            result = result and self._platforms_parser.check_is_int(section, 'TOTAL_JOBS', False)

        if not result:
            Log.critical("{0} is not a valid config file".format(os.path.basename(self._platforms_parser_file)))
        else:
            Log.info('{0} OK'.format(os.path.basename(self._platforms_parser_file)))
        return result

    def check_jobs_conf(self):
        """
        Checks experiment's jobs configuration file.

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """
        result = True
        parser = self._jobs_parser
        sections = parser.sections()
        platforms = self._platforms_parser.sections()
        platforms.append('LOCAL')
        if len(sections) == 0:
            Log.warning("No remote platforms configured")

        if len(sections) != len(set(sections)):
            Log.error('There are repeated job names')

        for section in sections:
            result = result and parser.check_exists(section, 'FILE')
            result = result and parser.check_is_boolean(section, 'RERUN_ONLY', False)

            if parser.has_option(section, 'PLATFORM'):
                result = result and parser.check_is_choice(section, 'PLATFORM', False, platforms)

            if parser.has_option(section, 'DEPENDENCIES'):
                for dependency in str(parser.get_option(section, 'DEPENDENCIES', '')).split(' '):
                    if '-' in dependency:
                        dependency = dependency.split('-')[0]
                    elif '+' in dependency:
                        dependency = dependency.split('+')[0]
                    if dependency not in sections:
                        Log.error(
                            'Job {0} depends on job {1} that is not defined. It will be ignored.'.format(section,
                                                                                                         dependency))

            if parser.has_option(section, 'RERUN_DEPENDENCIES'):
                for dependency in str(parser.get_option(section, 'RERUN_DEPENDENCIES',
                                                        '')).split(' '):
                    if '-' in dependency:
                        dependency = dependency.split('-')[0]
                    if dependency not in sections:
                        Log.error(
                            'Job {0} depends on job {1} that is not defined. It will be ignored.'.format(section,
                                                                                                         dependency))
            result = result and parser.check_is_choice(section, 'RUNNING', False,
                                                                 ['once', 'date', 'member', 'chunk'])

        if not result:
            Log.critical("{0} is not a valid config file".format(os.path.basename(self._jobs_parser_file)))
        else:
            Log.info('{0} OK'.format(os.path.basename(self._jobs_parser_file)))

        return result

    def check_expdef_conf(self):
        """
        Checks experiment's experiment configuration file.

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """
        result = True
        parser = self._exp_parser

        result = result and parser.check_exists('DEFAULT', 'EXPID')
        result = result and parser.check_exists('DEFAULT', 'HPCARCH')

        result = result and parser.check_exists('experiment', 'DATELIST')
        result = result and parser.check_exists('experiment', 'MEMBERS')
        result = result and parser.check_is_choice('experiment', 'CHUNKSIZEUNIT', True,
                                                   ['year', 'month', 'day', 'hour'])
        result = result and parser.check_is_int('experiment', 'CHUNKSIZE', True)
        result = result and parser.check_is_int('experiment', 'NUMCHUNKS', True)
        result = result and parser.check_is_choice('experiment', 'CALENDAR', True,
                                                   ['standard', 'noleap'])

        result = result and parser.check_is_boolean('rerun', 'RERUN', True)

        if parser.check_is_choice('project', 'PROJECT_TYPE', True,
                                  ['none', 'git', 'svn', 'local']):
            project_type = parser.get_option('project', 'PROJECT_TYPE', '')

            if project_type == 'git':
                result = result and parser.check_exists('git', 'PROJECT_ORIGIN')
                result = result and parser.check_exists('git', 'PROJECT_BRANCH')
            elif project_type == 'svn':
                result = result and parser.check_exists('svn', 'PROJECT_URL')
                result = result and parser.check_exists('svn', 'PROJECT_REVISION')
            elif project_type == 'local':
                result = result and parser.check_exists('local', 'PROJECT_PATH')

            if project_type != 'none':
                result = result and parser.check_exists('project_files', 'FILE_PROJECT_CONF')
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
        self._jobs_parser = AutosubmitConfig.get_parser(self.parser_factory, self._jobs_parser_file)
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
        return self._exp_parser.get_option('project_files', 'FILE_JOBS_CONF', '')

    def get_git_project_origin(self):
        """
        Returns git origin from experiment config file

        :return: git origin
        :rtype: str
        """
        return self._exp_parser.get_option('git', 'PROJECT_ORIGIN', '')

    def get_git_project_branch(self):
        """
        Returns git branch  from experiment's config file

        :return: git branch
        :rtype: str
        """
        return self._exp_parser.get_option('git', 'PROJECT_BRANCH', None)

    def get_git_project_commit(self):
        """
        Returns git commit from experiment's config file

        :return: git commit
        :rtype: str
        """
        return self._exp_parser.get_option('git', 'PROJECT_COMMIT', None)

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

    def get_chunk_ini(self, default=1):
        """
        Returns the first chunk from where the experiment will start

        :param default:
        :return: initial chunk
        :rtype: int
        """
        chunk_ini = self._exp_parser.get_option('experiment', 'CHUNKINI', default)
        if chunk_ini == '':
            return default
        return int(chunk_ini)

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

    def get_max_wallclock(self):
        """
        Returns max wallclock from autosubmit's config file

        :rtype: str
        """
        return self._conf_parser.get_option('config', 'MAX_WALLCLOCK', '')

    def get_max_processors(self):
        """
        Returns max processors from autosubmit's config file

        :rtype: str
        """
        config_value = self._conf_parser.get_option('config', 'MAX_PROCESSORS', None)
        return int(config_value) if config_value is not None else config_value

    def get_max_waiting_jobs(self):
        """
        Returns max number of waiting jobs from autosubmit's config file

        :return: main platforms
        :rtype: int
        """
        return int(self._conf_parser.get('config', 'MAXWAITINGJOBS'))

    def get_default_job_type(self):
        """
        Returns the default job type from experiment's config file

        :return: default type such as bash, python, r..
        :rtype: str
        """
        return self._exp_parser.get_option('project_files', 'JOB_SCRIPTS_TYPE', 'bash')

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
        :rtype: string
        """
        return self._conf_parser.get_option('mail', 'NOTIFICATIONS', 'false').lower()

    def get_remote_dependencies(self):
        """
        Returns if the user has enabled the remote dependencies from autosubmit's config file

        :return: if remote dependencies
        :rtype: bool
        """
        return self._conf_parser.get_option('wrapper', 'DEPENDENCIES', 'false').lower() == 'true'

    def get_wrapper_type(self):
        """
        Returns what kind of wrapper (VERTICAL, HORIZONTAL, NONE) the user has configured in the autosubmit's config

        :return: wrapper type (or none)
        :rtype: string
        """
        return self._conf_parser.get_option('wrapper', 'TYPE', 'None').lower()

    def get_copy_remote_logs(self):
        """
        Returns if the user has enabled the logs local copy from autosubmit's config file

        :return: if logs local copy
        :rtype: bool
        """
        return self._conf_parser.get_option('storage', 'COPY_REMOTE_LOGS', 'true').lower()

    def get_mails_to(self):
        """
        Returns the address where notifications will be sent from autosubmit's config file

        :return: mail address
        :rtype: [str]
        """
        return [str(x) for x in self._conf_parser.get_option('mail', 'TO', '').split(' ')]

    def get_communications_library(self):
        """
        Returns the communications library from autosubmit's config file. Paramiko by default.

        :return: communications library
        :rtype: str
        """
        return self._conf_parser.get_option('communications', 'API', 'paramiko').lower()

    def get_storage_type(self):
        """
        Returns the communications library from autosubmit's config file. Paramiko by default.

        :return: communications library
        :rtype: str
        """
        return self._conf_parser.get_option('storage', 'TYPE', 'pkl').lower()

    @staticmethod
    def is_valid_mail_address(mail_address):
        if re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', mail_address):
            return True
        else:
            return False

    def is_valid_communications_library(self):
        library = self.get_communications_library()
        return library in ['paramiko', 'saga']

    def is_valid_storage_type(self):
        storage_type = self.get_storage_type()
        return storage_type in ['pkl', 'db']

    def is_valid_git_repository(self):
        origin_exists = self._exp_parser.check_exists('git', 'PROJECT_ORIGIN')
        branch = self.get_git_project_branch()
        commit = self.get_git_project_commit()
        return origin_exists and (branch is not None or commit is not None)

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
