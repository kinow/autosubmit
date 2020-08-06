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
    from config_parser import SafeConfigParser
except ImportError:
    # noinspection PyCompatibility
    from ConfigParser import SafeConfigParser
import os
import re
import subprocess

from pyparsing import nestedExpr

from bscearth.utils.date import parse_date
from log.log import Log
from autosubmit.config.basicConfig import BasicConfig
from log.log import AutosubmitError
from collections import defaultdict
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
        self.wrong_config = defaultdict(list)
        self.warn_config = defaultdict(list)


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
                if not re.match('^\[[^\[\]\# \t\n]*\][ \t]*$|^[ \t]+\[[^\[\]# \t\n]*\]', first_line):
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

    def get_synchronize(self, section):
        """
        Gets wallclock for the given job type
        :param section: job type
        :type section: str
        :return: wallclock time
        :rtype: str
        """
        return self._jobs_parser.get_option(section, 'SYNCHRONIZE', '')
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
    def get_current_user(self, section):
        """
        Returns the user to be changed from platform config file.

        :return: migrate user to
        :rtype: str
        """
        return self._platforms_parser.get_option(section, 'USER', '').lower()

    def get_current_host(self, section):
        """
        Returns the user to be changed from platform config file.

        :return: migrate user to
        :rtype: str
        """
        return self._platforms_parser.get_option(section, 'HOST', '').lower()
    def get_current_project(self, section):
        """
        Returns the project to be changed from platform config file.

        :return: migrate user to
        :rtype: str
        """
        return self._platforms_parser.get_option(section, 'PROJECT', '').lower()
    def set_new_user(self, section, new_user):
        """
        Sets new user for given platform
        :param new_user: 
        :param section: platform name
        :type: str
        """
        with open(self._platforms_parser_file) as p_file:
            contentLine = p_file.readline()
            contentToMod=""
            content=""
            mod=False
            while contentLine:
                if re.search(section, contentLine):
                    mod=True
                if mod:
                    contentToMod += contentLine
                else:
                    content += contentLine
                contentLine = p_file.readline()
        if mod:
            old_user = self.get_current_user(section)
            contentToMod = contentToMod.replace(re.search(r'[^#]\bUSER\b =.*', contentToMod).group(0)[1:], "USER = " + new_user)
            contentToMod = contentToMod.replace(re.search(r'[^#]\bUSER_TO\b =.*', contentToMod).group(0)[1:], "USER_TO = " + old_user)
        open(self._platforms_parser_file, 'w').write(content)
        open(self._platforms_parser_file, 'a').write(contentToMod)
    def set_new_host(self, section, new_host):
        """
        Sets new host for given platform
        :param new_host:
        :param section: platform name
        :type: str
        """
        with open(self._platforms_parser_file) as p_file:
            contentLine = p_file.readline()
            contentToMod=""
            content=""
            mod=False
            while contentLine:
                if re.search(section, contentLine):
                    mod=True
                if mod:
                    contentToMod += contentLine
                else:
                    content += contentLine
                contentLine = p_file.readline()
        if mod:
            old_host = self.get_current_host(section)
            contentToMod = contentToMod.replace(re.search(r'[^#]\bHOST\b =.*', contentToMod).group(0)[1:], "HOST = " + new_host)
            contentToMod = contentToMod.replace(re.search(r'[^#]\bHOST_TO\b =.*', contentToMod).group(0)[1:], "HOST_TO = " + old_host)
        open(self._platforms_parser_file, 'w').write(content)
        open(self._platforms_parser_file, 'a').write(contentToMod)
    def get_migrate_project_to(self, section):
        """
        Returns the project to change to from platform config file.

        :return: migrate project to
        :rtype: str
        """
        return self._platforms_parser.get_option(section, 'PROJECT_TO', '').lower()
    def get_migrate_host_to(self, section):
        """
        Returns the host to change to from platform config file.

        :return: host_to
        :rtype: str
        """
        return self._platforms_parser.get_option(section, 'HOST_TO', "none").lower()
    def set_new_project(self, section, new_project):
        """
        Sets new project for given platform
        :param new_project: 
        :param section: platform name
        :type: str
        """
        with open(self._platforms_parser_file) as p_file:
            contentLine = p_file.readline()
            contentToMod=""
            content=""
            mod=False
            while contentLine:
                if re.search(section, contentLine):
                    mod=True
                if mod:
                    contentToMod += contentLine
                else:
                    content += contentLine
                contentLine = p_file.readline()
        if mod:
            old_project = self.get_current_project(section)
            contentToMod = contentToMod.replace(re.search(r"[^#]\bPROJECT\b =.*", contentToMod).group(0)[1:], "PROJECT = " + new_project)
            contentToMod = contentToMod.replace(re.search(r"[^#]\bPROJECT_TO\b =.*", contentToMod).group(0)[1:], "PROJECT_TO = " + old_project)
        open(self._platforms_parser_file, 'w').write(content)
        open(self._platforms_parser_file, 'a').write(contentToMod)


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

        :return: True if everything is correct, False if it finds any error
        :rtype: bool
        """
        Log.info('\nChecking configuration files...')
        self.reload()
        self.check_platforms_conf()
        self.check_jobs_conf()
        self.check_autosubmit_conf()
        self.check_expdef_conf()
        project_type = self.get_project_type()
        if project_type != "none":
            # Check proj configuration
            self.check_proj()
        if len(self.warn_config.keys()) == 0 and len(self.wrong_config.keys()) == 0:
            Log.result("Configuration files OK\n")
        elif len(self.warn_config.keys()) > 0 and len(self.wrong_config.keys()) == 0:
            Log.result("Configuration files contains some issues ignored")
        if len(self.warn_config.keys()) > 0:
            message = "On Configuration files:\n"
            for section in self.warn_config:
                message += "Issues on [{0}] config file:".format(section)
                for parameter in self.warn_config[section]:
                    message += "\n{0} with value of {1} ".format(parameter[0],parameter[1])
                message += "\n"
            Log.printlog(message,6000)

        if len(self.wrong_config.keys()) > 0:
            message = "On Configuration files:\n"
            for section in self.wrong_config:
                message += "Critical Issues on [{0}] config file:".format(section)
                for parameter in self.wrong_config[section]:
                    message += "\n{0} with value of {1}".format(parameter[0], parameter[1])
                message += "\n"
            raise AutosubmitError(message,9000)

    def check_autosubmit_conf(self):
        """
        Checks experiment's autosubmit configuration file.

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """

        self._conf_parser.read(self._conf_parser_file)
        if not self._conf_parser.check_exists('config', 'AUTOSUBMIT_VERSION'):
            self.wrong_config["Autosubmit"]+=[['config', "AUTOSUBMIT_VERSION parameter not found"]]
        if not self._conf_parser.check_is_int('config', 'MAXWAITINGJOBS', True):
            self.wrong_config["Autosubmit"]+=[['config', "MAXWAITINGJOBS parameter not found or non-integer"]]
        if not  self._conf_parser.check_is_int('config', 'TOTALJOBS', True):
            self.wrong_config["Autosubmit"]+=[['config', "TOTALJOBS parameter not found or non-integer"]]
        if not  self._conf_parser.check_is_int('config', 'SAFETYSLEEPTIME', True):
            self.wrong_config["Autosubmit"]+=[['config', "SAFETYSLEEPTIME parameter not found or non-integer"]]
        if not  self._conf_parser.check_is_int('config', 'RETRIALS', True):
            self.wrong_config["Autosubmit"]+=[['config', "RETRIALS parameter not found or non-integer"]]
        if not  self._conf_parser.check_is_boolean('mail', 'NOTIFICATIONS', False):
            self.wrong_config["Autosubmit"]+=[['mail', "NOTIFICATIONS parameter not found or non-boolean"]]
        if not  self.is_valid_communications_library():
            self.wrong_config["Autosubmit"]+=[['config', "LIBRARY parameter not found or is not paramiko"]]
        if not  self.is_valid_storage_type():
            self.wrong_config["Autosubmit"]+=[['storage', "TYPE parameter not found"]]
        if self.get_wrapper_type() != 'None':
            self.check_wrapper_conf()
        if self.get_notifications() == 'true':
            for mail in self.get_mails_to():
                if not self.is_valid_mail_address(mail):
                    self.wrong_config["Autosubmit"]+=[['mail', "Some of the configured e-mail is not valid"]]
        if  "Autosubmit" not in  self.wrong_config:
            Log.result('{0} OK'.format(os.path.basename(self._conf_parser_file)))


    def check_platforms_conf(self):
        """
        Checks experiment's queues configuration file.
        """
        if len(self._platforms_parser.sections()) == 0:
            self.wrong_config["Platform"] += [["Global","No remote platforms found"]]

        if len(self._platforms_parser.sections()) != len(set(self._platforms_parser.sections())):
            self.wrong_config["Platform"]+=[["Global", "Platforms found multiple times"]]

        for section in self._platforms_parser.sections():
            if not self._platforms_parser.check_exists(section, 'TYPE'):
                self.wrong_config["Platform"]+=[[section, "Mandatory TYPE parameter not found"]]
                platform_type = self._platforms_parser.get_option(section, 'TYPE', '').lower()
                if platform_type != 'ps':
                    if not  self._platforms_parser.check_exists(section, 'PROJECT'):
                        self.wrong_config["Platform"]+=[[ section, "Mandatory PROJECT parameter not found"]]
                    if not  self._platforms_parser.check_exists(section, 'USER'):
                        self.wrong_config["Platform"]+=[[ section, "Mandatory USER parameter not found"]]
            if not  self._platforms_parser.check_exists(section, 'HOST'):
                self.wrong_config["Platform"]+=[[ section, "Mandatory HOST parameter not found"]]
            if not  self._platforms_parser.check_exists(section, 'SCRATCH_DIR'):
                self.wrong_config["Platform"]+=[[ section, "Mandatory SCRATCH_DIR parameter not found"]]
            if not  self._platforms_parser.check_is_boolean(section,'ADD_PROJECT_TO_HOST', False):
                self.wrong_config["Platform"]+=[[ section, "Mandatory ADD_PROJECT_TO_HOST parameter not found or non-boolean"]]
            if not  self._platforms_parser.check_is_boolean(section, 'TEST_SUITE', False):
                self.wrong_config["Platform"]+=[[ section, "Mandatory TEST_SUITE parameter not found or non-boolean"]]
            if not  self._platforms_parser.check_is_int(section, 'MAX_WAITING_JOBS',False):
                self.wrong_config["Platform"]+=[[ section, "Mandatory MAX_WAITING_JOBS parameter not found or non-integer"]]
            if not  self._platforms_parser.check_is_int(section, 'TOTAL_JOBS', False):
                self.wrong_config["Platform"]+=[[ section, "Mandatory TOTAL_JOBS parameter not found or non-integer"]]
        if "Platform" not in self.wrong_config:
            Log.result('{0} OK'.format(os.path.basename(self._platforms_parser_file)))

    def check_jobs_conf(self):
        """
        Checks experiment's jobs configuration file.

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """
        parser = self._jobs_parser
        sections = parser.sections()
        platforms = self._platforms_parser.sections()
        platforms.append('LOCAL')

        if len(sections) != len(set(sections)):
            self.wrong_config["Jobs"] += [["Global", "There are repeated job names"]]

        for section in sections:
            if not  parser.check_exists(section, 'FILE'):
                self.wrong_config["Jobs"]+=[[ section, "Mandatory FILE parameter not found"]]
            if not  parser.check_is_boolean(section, 'RERUN_ONLY', False):
                self.wrong_config["Jobs"]+=[[ section, "Mandatory RERUN_ONLY parameter not found or non-bool"]]
            if parser.has_option(section, 'PLATFORM'):
                if not  parser.check_is_choice(section, 'PLATFORM', False, platforms):
                    self.wrong_config["Jobs"] += [[section, "PLATFORM parameter is invalid, this platform is not configured"]]

            if parser.has_option(section, 'DEPENDENCIES'):
                for dependency in str(parser.get_option(section, 'DEPENDENCIES', '')).split(' '):
                    if '-' in dependency:
                        dependency = dependency.split('-')[0]
                    elif '+' in dependency:
                        dependency = dependency.split('+')[0]
                    elif '*' in dependency:
                        dependency = dependency.split('*')[0]
                    if '[' in dependency:
                        dependency = dependency[:dependency.find('[')]
                    if dependency not in sections:
                        self.warn_config["Jobs"].append([section, "Dependency parameter is invalid, job {0} is not configured".format(dependency)])

            if parser.has_option(section, 'RERUN_DEPENDENCIES'):
                for dependency in str(parser.get_option(section, 'RERUN_DEPENDENCIES','')).split(' '):
                    if '-' in dependency:
                        dependency = dependency.split('-')[0]
                    if '[' in dependency:
                        dependency = dependency[:dependency.find('[')]
                    if dependency not in sections:
                        self.warn_config["Jobs"]+=[[section, "RERUN_DEPENDENCIES parameter is invalid, job {0} is not configured".format(dependency)]]

            if not parser.check_is_choice(section, 'RUNNING', False, ['once', 'date', 'member', 'chunk']):
                self.wrong_config["Jobs"]+=[[section, "Mandatory RUNNING parameter is invalid"]]
        if "Jobs" not in self.wrong_config:
            Log.result('{0} OK'.format(os.path.basename(self._jobs_parser_file)))

    def check_expdef_conf(self):
        """
        Checks experiment's experiment configuration file.

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """
        parser = self._exp_parser
        if not  parser.check_exists('DEFAULT', 'EXPID'):
            self.wrong_config["Expdef"]+=[['DEFAULT', "Mandatory EXPID parameter is invalid"]]

        if not  parser.check_exists('DEFAULT', 'HPCARCH'):
            self.wrong_config["Expdef"]+=[['DEFAULT', "Mandatory HPCARCH parameter is invalid"]]

        if not  parser.check_exists('experiment', 'DATELIST'):
            self.wrong_config["Expdef"]+=[['DEFAULT', "Mandatory DATELIST parameter is invalid"]]
        if not  parser.check_exists('experiment', 'MEMBERS'):
            self.wrong_config["Expdef"]+=[['DEFAULT', "Mandatory MEMBERS parameter is invalid"]]
        if not  parser.check_is_choice('experiment', 'CHUNKSIZEUNIT', True,['year', 'month', 'day', 'hour']):
            self.wrong_config["Expdef"]+=[['experiment', "Mandatory CHUNKSIZEUNIT choice is invalid"]]

        if not  parser.check_is_int('experiment', 'CHUNKSIZE', True):
            self.wrong_config["Expdef"]+=[['experiment', "Mandatory CHUNKSIZE is not an integer"]]
        if not  parser.check_is_int('experiment', 'NUMCHUNKS', True):
            self.wrong_config["Expdef"]+=[['experiment', "Mandatory NUMCHUNKS is not an integer"]]

        if not  parser.check_is_choice('experiment', 'CALENDAR', True,
                                                   ['standard', 'noleap']):
            self.wrong_config["Expdef"]+=[['experiment', "Mandatory CALENDAR choice is invalid"]]

        if not  parser.check_is_boolean('rerun', 'RERUN', True):
            self.wrong_config["Expdef"]+=[['experiment', "Mandatory RERUN choice is not a boolean"]]

        if parser.check_is_choice('project', 'PROJECT_TYPE', True, ['none', 'git', 'svn', 'local']):
            project_type = parser.get_option('project', 'PROJECT_TYPE', '')

            if project_type == 'git':
                if not  parser.check_exists('git', 'PROJECT_ORIGIN'):
                    self.wrong_config["Expdef"]+=[['git', "PROJECT_ORIGIN parameter is invalid"]]
                if not  parser.check_exists('git', 'PROJECT_BRANCH'):
                    self.wrong_config["Expdef"]+=[['git', "PROJECT_BRANCH parameter is invalid"]]

            elif project_type == 'svn':
                if not  parser.check_exists('svn', 'PROJECT_URL'):
                    self.wrong_config["Expdef"]+=[['svn', "PROJECT_URL parameter is invalid"]]
                if not  parser.check_exists('svn', 'PROJECT_REVISION'):
                    self.wrong_config["Expdef"]+=[['svn', "PROJECT_REVISION parameter is invalid"]]
            elif project_type == 'local':
                if not  parser.check_exists('local', 'PROJECT_PATH'):
                    self.wrong_config["Expdef"]+=[['local', "PROJECT_PATH parameter is invalid"]]

            if project_type != 'none':
                if not  parser.check_exists('project_files', 'FILE_PROJECT_CONF'):
                    self.wrong_config["Expdef"]+=[['project_files', "FILE_PROJECT_CONF parameter is invalid"]]
        else:
            self.wrong_config["Expdef"]+=[['project', "Mandatory project choice is invalid"]]

        if "Jobs" not in self.wrong_config:
            Log.result('{0} OK'.format(os.path.basename(self._exp_parser_file)))


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
        except Exception as e:
            self.wrong_config["Proj"]+=[['project_files', "FILE_PROJECT_CONF parameter is invalid"]]
    def check_wrapper_conf(self):
        if not self.is_valid_jobs_in_wrapper():
            self.wrong_config["Wrapper"]+=[['wrapper', "JOBS_IN_WRAPPER contains non-defined jobs.  parameter is invalid"]]
        if 'horizontal' in self.get_wrapper_type():
            if not  self._platforms_parser.check_exists(self.get_platform(), 'PROCESSORS_PER_NODE'):
                self.wrong_config["Wrapper"]+=[['wrapper', "PROCESSORS_PER_NODE no exists in the horizontal-wrapper platform"]]
            if not  self._platforms_parser.check_exists(self.get_platform(), 'MAX_PROCESSORS'):
                self.wrong_config["Wrapper"]+=[['wrapper', "MAX_PROCESSORS no exists in the horizontal-wrapper platform"]]
        if 'vertical' in self.get_wrapper_type():
            if not self._platforms_parser.check_exists(self.get_platform(), 'MAX_WALLCLOCK'):
                self.wrong_config["Wrapper"]+=[['wrapper', "MAX_WALLCLOCK no exists in the vertical-wrapper platform"]]
        if "Wrapper"  not in self.wrong_config:
            Log.result('wrappers OK')




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
        return self._exp_parser.get_option('git', 'PROJECT_BRANCH', 'master')
    def get_git_project_commit(self):
        """
        Returns git commit from experiment's config file

        :return: git commit
        :rtype: str
        """
        return self._exp_parser.get_option('git', 'PROJECT_COMMIT', None)
    def get_git_remote_project_root(self):
        """
        Returns remote machine ROOT PATH

        :return: git commit
        :rtype: str
        """
        return self._exp_parser.get_option('git', 'REMOTE_CLONE_ROOT', '')
    def get_submodules_list(self):
        """
        Returns submodules list from experiment's config file
        Default is --recursive
        :return: submodules to load
        :rtype: list
        """
        return ' '.join(self._exp_parser.get_option('git', 'PROJECT_SUBMODULES','').split()).split()

    def get_fetch_single_branch(self):
        """
        Returns fetch single branch from experiment's config file
        Default is -single-branch
        :return: fetch_single_branch(Y/N)
        :rtype: boolean
        """
        return self._exp_parser.get_option('git', 'FETCH_SINGLE_BRANCH', 'False').lower()
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
        full_project_path=as_conf.get_project_dir()
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

    def get_version(self):
        """
        Returns version number of the current experiment from autosubmit's config file

        :return: version
        :rtype: str
        """
        return self._conf_parser.get('config', 'AUTOSUBMIT_VERSION' , 'None')
    def get_total_jobs(self):
        """
        Returns max number of running jobs  from autosubmit's config file

        :return: max number of running jobs
        :rtype: int
        """
        return int(self._conf_parser.get('config', 'TOTALJOBS'))
    
    def get_output_type(self):
        """
        Returns default output type, pdf if none

        :return: output type
        :rtype: string
        """
        return self._conf_parser.get_option('config', 'OUTPUT','pdf')

    def get_max_wallclock(self):
        """
        Returns max wallclock

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
        Returns if the user has enabled the PRESUBMISSION configuration parameter from autosubmit's config file

        :return: if remote dependencies
        :rtype: bool
        """
        config_value = self._conf_parser.get_option('config', 'PRESUBMISSION', 'false').lower()
        if config_value == "true":
            return True
        else:
            return False
    def get_wrapper_type(self):
        """
        Returns what kind of wrapper (VERTICAL, MIXED-VERTICAL, HORIZONTAL, HYBRID, NONE) the user has configured in the autosubmit's config

        :return: wrapper type (or none)
        :rtype: string
        """
        return self._conf_parser.get_option('wrapper', 'TYPE', 'None').lower()
    def get_wrapper_policy(self):
        """
        Returns what kind of wrapper (VERTICAL, MIXED-VERTICAL, HORIZONTAL, HYBRID, NONE) the user has configured in the autosubmit's config

        :return: wrapper type (or none)
        :rtype: string
        """
        return self._conf_parser.get_option('wrapper', 'POLICY', 'flexible').lower()

    def get_wrapper_jobs(self):
        """
        Returns the jobs that should be wrapped, configured in the autosubmit's config

        :return: expression (or none)
        :rtype: string
        """
        return self._conf_parser.get_option('wrapper', 'JOBS_IN_WRAPPER', 'None')
    def get_wrapper_queue(self):
        """
        Returns the wrapper queue if not defined, will be the one of the first job wrapped

        :return: expression (or none)
        :rtype: string
        """
        return self._conf_parser.get_option('wrapper', 'QUEUE', 'None')
    def get_min_wrapped_jobs(self):
        """
         Returns the minim number of jobs that can be wrapped together as configured in autosubmit's config file

        :return: minim number of jobs (or total jobs)
        :rtype: int
        """
        return int(self._conf_parser.get_option('wrapper', 'MIN_WRAPPED', 2))

    def get_max_wrapped_jobs(self):
        """
         Returns the maximum number of jobs that can be wrapped together as configured in autosubmit's config file

         :return: maximum number of jobs (or total jobs)
         :rtype: int
         """
        return int(self._conf_parser.get_option('wrapper', 'MAX_WRAPPED', self.get_total_jobs()))
    def get_wrapper_method(self):
        """
         Returns the method of make the wrapper

         :return: method
         :rtype: string
         """
        return self._conf_parser.get_option('wrapper', 'METHOD', 'ASThread')
    def get_wrapper_check_time(self):
        """
         Returns time to check the status of jobs in the wrapper

         :return: wrapper check time
         :rtype: int
         """
        return int(self._conf_parser.get_option('wrapper', 'CHECK_TIME_WRAPPER', self.get_safetysleeptime()))

    def get_wrapper_machinefiles(self):
        """
         Returns the strategy for creating the machinefiles in wrapper jobs

         :return: machinefiles function to use
         :rtype: string
         """
        return self._conf_parser.get_option('wrapper', 'MACHINEFILES', '')

    def get_jobs_sections(self):
        """
        Returns the list of sections defined in the jobs config file

        :return: sections
        :rtype: list
        """
        return self._jobs_parser.sections()

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
        return library in ['paramiko']

    def is_valid_storage_type(self):
        storage_type = self.get_storage_type()
        return storage_type in ['pkl', 'db']

    def is_valid_jobs_in_wrapper(self):
        expression = self.get_wrapper_jobs()
        if expression != 'None':
            parser = self._jobs_parser
            sections = parser.sections()
            for section in expression.split(" "):
                if "&" in section:
                    for inner_section in section.split("&"):
                        if inner_section not in sections:
                            return False
                elif section not in sections:
                    return False
        return True

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
