#!/usr/bin/env python3

# Copyright 2015-2022 Earth Sciences Department, BSC-CNS

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
from ruamel.yaml import YAML
import locale
import os
import re
import subprocess
import traceback
import json

from pyparsing import nestedExpr

from bscearth.utils.date import parse_date
from log.log import Log, AutosubmitError, AutosubmitCritical

from autosubmit.config.basicConfig import BasicConfig
from collections import defaultdict
import collections
import pathlib
from pathlib import Path

class AutosubmitConfig(object):
    """
    Class to handle experiment configuration coming from file or database

    :param expid: experiment identifier
    :type expid: str
    """

    def __init__(self, expid, basic_config, parser_factory):
        self.ignore_undefined_platforms = False
        self.expid = expid
        self.basic_config = basic_config
        self.parser_factory = parser_factory
        self.experiment_data = None

        self._conf_parser = None
        self._conf_parser_file = Path(self.basic_config.LOCAL_ROOT_DIR) / expid / "conf" / ("autosubmit_" + expid + ".yml")
        self._exp_parser = None
        self._exp_parser_file = Path(self.basic_config.LOCAL_ROOT_DIR) / expid / "conf" / ("expdef_" + expid + ".yml")
        self._platforms_parser = None
        self._platforms_parser_file = Path(self.basic_config.LOCAL_ROOT_DIR) / expid / "conf" / ("platforms_" + expid + ".yml")
        self._jobs_parser = None
        self._jobs_parser_file = Path(self.basic_config.LOCAL_ROOT_DIR) / expid / "conf" / ("jobs_" + expid + ".yml")
        self._proj_parser = None
        self._proj_parser_file = Path(self.basic_config.LOCAL_ROOT_DIR) / expid / "conf" / ("proj_" + expid +".yml")
        custom_folder_path = Path(self.basic_config.LOCAL_ROOT_DIR) / expid / "conf"
        self._custom_parser_files = []
        #todo convert rest of files to path
        for f in custom_folder_path.rglob("*.yml"):
            if not f == self._proj_parser_file and not f.samefile(self._jobs_parser_file) and not f.samefile(self._platforms_parser_file) and not f.samefile(self._exp_parser_file) and not f.samefile(self._conf_parser_file):
                self._custom_parser_files.append(f)

        self.ignore_file_path = False
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
            with open(self._proj_parser_file, 'rb+') as f:
                first_line = f.readline()
                if not re.match('^\[[^\[\]\# \t\n]*\][ \t]*$|^[ \t]+\[[^\[\]# \t\n]*\]', first_line):
                    content = f.read()
                    f.seek(0, 0)
                    f.write('[DEFAULT]'.rstrip('\r\n') +
                            '\n' + first_line + content)
                    f.close()

    @property
    def jobs_file(self):
        """
        Returns project's jobs file name
        """
        return self._jobs_parser_file

    def get_full_config_as_dict(self):
        """
        Returns full configuration as json object
        """
        _conf = _exp = _platforms = _jobs = _proj = None
        result = {}

        def get_data(parser):
            """
            dictionary comprehension to get data from parser
            """
            res = {sec: {option: parser.get(sec, option) for option in parser.options(sec)} for sec in [
                section for section in parser.sections()]}
            return res

        result["conf"] = get_data(
            self._conf_parser) if self._conf_parser else None
        result["exp"] = get_data(
            self._exp_parser) if self._exp_parser else None
        result["platforms"] = get_data(
            self._platforms_parser) if self._platforms_parser else None
        result["jobs"] = get_data(
            self._jobs_parser) if self._jobs_parser else None
        result["proj"] = get_data(
            self._proj_parser) if self._proj_parser else None
        return result

    def get_wrapper_export(self,wrapper_name=[]):
        """
         Returns modules variable from wrapper

         :return: string
         :rtype: string
         """
        wrapper_section = ["WRAPPERS"].extend(wrapper_name)
        return self.get_section(wrapper_section.extend('EXPORT'), 'none')

    def get_full_config_as_json(self):
        """
        Return config as json object
        """
        try:
            return json.dumps(self.get_full_config_as_dict())
        except Exception as exp:
            Log.warning(
                "Autosubmit was not able to retrieve and save the configuration into the historical database.")
            return ""

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
        return self.get_section([["JOBS"]+section, 'WALLCLOCK'], '02:00')


    def get_export(self, section):
        """
        Gets command line for being submitted with
        :param section: job type
        :type section: str
        :return: wallclock time
        :rtype: str
        """
        return self.get_section([["JOBS"]+section, 'EXPORT'], None)

    def get_x11(self, section):
        """
        Active X11 for this section
        :param section: job type
        :type section: str
        :return: false/true
        :rtype: str
        """
        return self.get_section(section, 'X11', 'false')

    def deep_search(self,unified_config, new_dict):
        """
        Update a nested dictionary or similar mapping.
        Modify ``source`` in place.
        """
        for key, val in new_dict.items():
            if isinstance(val, collections.Mapping):
                tmp = self.deep_update(unified_config.get(key, {}), val)
                unified_config[key] = tmp
            elif isinstance(val, list):
                unified_config[key] = (unified_config.get(key, []) + val)
            else:
                unified_config[key] = new_dict[key]
        return unified_config
    def get_section(self, section, d_value="-", must_exists = False ):
        """
        Gets any section if it exists within the dictionary, else returns - or error if must exists.
        :param section:
        :type list
        :param must_exists:
        :type bool
        :param d_value:
        :type str
        :return:
        """
        section = [ s.upper() for s in section ]
        current_value = self.data
        section_str = str(section[0])
        # For text redeability
        for section_str in section[:1]:
            section_str += "." + str(section_str)
        # Look for section
        for section_level in section:
            if current_value is not type(dict):
                if must_exists:
                    raise AutosubmitCritical("INDEX ERROR, {0} must exists.Check that subsection is really an subsedtion{1} exists.".format(section_str, str(section_level)), 7014)
                else:
                    current_value = d_value
                    break
            if section_level not in current_value:
                if must_exists:
                    raise AutosubmitCritical("{0} must exists. Check that subsection {1} exists.".format(section_str,str(section_level)), 7014)
                return d_value
            else:
                current_value = current_value[section_level]

        return current_value


    def get_wchunkinc(self, section):
        """
        Gets the chunk increase to wallclock  
        :param section: job type
        :type section: str
        :return: wallclock increase per chunk
        :rtype: str
        """
        return self.get_section(section, 'WCHUNKINC', '')

    def get_synchronize(self, section):
        """
        Gets wallclock for the given job type
        :param section: job type
        :type section: str
        :return: wallclock time
        :rtype: str
        """
        return self.get_section(section, 'SYNCHRONIZE', '')

    def get_processors(self, section):
        """
        Gets processors needed for the given job type
        :param section: job type
        :type section: str
        :return: wallclock time
        :rtype: str
        """
        return str(self.get_section(section, 'PROCESSORS', 1))

    def get_threads(self, section):
        """
        Gets threads needed for the given job type
        :param section: job type
        :type section: str
        :return: threads needed
        :rtype: str
        """

        return str(self.get_section(section, 'THREADS', 1))

    def get_tasks(self, section):
        """
        Gets tasks needed for the given job type
        :param section: job type
        :type section: str
        :return: tasks (processes) per host
        :rtype: str
        """
        return str(self.get_section(section, 'TASKS', 0))

    def get_scratch_free_space(self, section):
        """
        Gets scratch free space needed for the given job type
        :param section: job type
        :type section: str
        :return: percentage of scratch free space needed
        :rtype: int
        """
        return int(self.get_section(section, 'SCRATCH_FREE_SPACE', 0))

    def get_memory(self, section):
        """
        Gets memory needed for the given job type
        :param section: job type
        :type section: str
        :return: memory needed
        :rtype: str
        """
        return str(self.get_section(section, 'MEMORY', ''))

    def get_memory_per_task(self, section):
        """
        Gets memory per task needed for the given job type
        :param section: job type
        :type section: str
        :return: memory per task needed
        :rtype: str
        """
        return str(self.get_section(section, 'MEMORY_PER_TASK', ''))

    def get_migrate_user_to(self, section):
        """
        Returns the user to change to from platform config file.

        :return: migrate user to
        :rtype: str
        """
        return self.get_section(section, 'USER_TO', '').lower()

    def get_migrate_duplicate(self, section):
        """
        Returns the user to change to from platform config file.

        :return: migrate user to
        :rtype: str
        """
        return self.get_section(section, 'SAME_USER', 'false').lower()

    def get_current_user(self, section):
        """
        Returns the user to be changed from platform config file.

        :return: migrate user to
        :rtype: str
        """
        return self.get_section(section, 'USER', '').lower()

    def get_current_host(self, section):
        """
        Returns the user to be changed from platform config file.

        :return: migrate user to
        :rtype: str
        """
        return self.get_section(section, 'HOST', '')

    def get_current_project(self, section):
        """
        Returns the project to be changed from platform config file.

        :return: migrate user to
        :rtype: str
        """
        return self.get_section(section, 'PROJECT', '')

    def set_new_user(self, section, new_user):
        """
        Sets new user for given platform
        :param new_user: 
        :param section: platform name
        :type: str
        """

        with open(self._platforms_parser_file) as p_file:
            contentLine = p_file.readline()
            contentToMod = ""
            content = ""
            mod = False
            while contentLine:
                if re.search(section, contentLine):
                    mod = True
                if mod:
                    contentToMod += contentLine
                else:
                    content += contentLine
                contentLine = p_file.readline()
        if mod:
            old_user = self.get_current_user(section)
            contentToMod = contentToMod.replace(re.search(
                r'[^#]\bUSER\b =.*', contentToMod).group(0)[1:], "USER = " + new_user)
            contentToMod = contentToMod.replace(re.search(
                r'[^#]\bUSER_TO\b =.*', contentToMod).group(0)[1:], "USER_TO = " + old_user)
        open(self._platforms_parser_file, 'wb').write(content)
        open(self._platforms_parser_file, 'ab').write(contentToMod)

    def set_new_host(self, section, new_host):
        """
        Sets new host for given platform
        :param new_host:
        :param section: platform name
        :type: str
        """
        with open(self._platforms_parser_file) as p_file:
            contentLine = p_file.readline()
            contentToMod = ""
            content = ""
            mod = False
            while contentLine:
                if re.search(section, contentLine):
                    mod = True
                if mod:
                    contentToMod += contentLine
                else:
                    content += contentLine
                contentLine = p_file.readline()
        if mod:
            old_host = self.get_current_host(section)
            contentToMod = contentToMod.replace(re.search(
                r'[^#]\bHOST\b =.*', contentToMod).group(0)[1:], "HOST = " + new_host)
            contentToMod = contentToMod.replace(re.search(
                r'[^#]\bHOST_TO\b =.*', contentToMod).group(0)[1:], "HOST_TO = " + old_host)
        open(self._platforms_parser_file, 'wb').write(content)
        open(self._platforms_parser_file, 'ab').write(contentToMod)

    def get_migrate_project_to(self, section):
        """
        Returns the project to change to from platform config file.

        :return: migrate project to
        :rtype: str
        """
        return self.get_section(section, 'PROJECT_TO', '')

    def get_migrate_host_to(self, section):
        """
        Returns the host to change to from platform config file.

        :return: host_to
        :rtype: str
        """
        return self.get_section(section, 'HOST_TO', "none")

    def set_new_project(self, section, new_project):
        """
        Sets new project for given platform
        :param new_project: 
        :param section: platform name
        :type: str
        """
        with open(self._platforms_parser_file) as p_file:
            contentLine = p_file.readline()
            contentToMod = ""
            content = ""
            mod = False
            while contentLine:
                if re.search(section, contentLine):
                    mod = True
                if mod:
                    contentToMod += contentLine
                else:
                    content += contentLine
                contentLine = p_file.readline()
        if mod:
            old_project = self.get_current_project(section)
            contentToMod = contentToMod.replace(re.search(
                r"[^#]\bPROJECT\b =.*", contentToMod).group(0)[1:], "PROJECT = " + new_project)
            contentToMod = contentToMod.replace(re.search(
                r"[^#]\bPROJECT_TO\b =.*", contentToMod).group(0)[1:], "PROJECT_TO = " + old_project)
        open(self._platforms_parser_file, 'wb').write(content)
        open(self._platforms_parser_file, 'ab').write(contentToMod)

    def get_custom_directives(self, section):
        """
        Gets custom directives needed for the given job type
        :param section: job type
        :type section: str
        :return: custom directives needed
        :rtype: str
        """
        return str(self.get_section(section, 'CUSTOM_DIRECTIVES', ''))

    def show_messages(self):

        if len(list(self.warn_config.keys())) == 0 and len(list(self.wrong_config.keys())) == 0:
            Log.result("Configuration files OK\n")
        elif len(list(self.warn_config.keys())) > 0 and len(list(self.wrong_config.keys())) == 0:
            Log.result("Configuration files contain some issues ignored")
        if len(list(self.warn_config.keys())) > 0:
            message = "In Configuration files:\n"
            for section in self.warn_config:
                message += "Issues in [{0}] config file:".format(section)
                for parameter in self.warn_config[section]:
                    message += "\n[{0}] {1} ".format(parameter[0],
                                                     parameter[1])
                message += "\n"
            Log.printlog(message, 6013)

        if len(list(self.wrong_config.keys())) > 0:
            message = "On Configuration files:\n"
            for section in self.wrong_config:
                message += "Critical Issues on [{0}] config file:".format(
                    section)
                for parameter in self.wrong_config[section]:
                    message += "\n[{0}] {1}".format(parameter[0], parameter[1])
                message += "\n"
            raise AutosubmitCritical(message, 7014)
        else:
            return True

    def deep_normalize(self,data):
        """
        normalize a nested dictionary or similar mapping to uppercase.
        Modify ``source`` in place.
        """
        normalized_data =  dict()
        for key, val in data.items():
            normalized_data[key.upper()] = val
            if isinstance(val, collections.Mapping):
                normalized_value = self.deep_normalize(data.get(key, {}))
                normalized_data[key.upper()] = normalized_value
        return normalized_data

    def deep_update(self,unified_config, new_dict):
        """
        Update a nested dictionary or similar mapping.
        Modify ``source`` in place.
        """
        for key, val in new_dict.items():
            if isinstance(val, collections.Mapping):
                tmp = self.deep_update(unified_config.get(key, {}), val)
                unified_config[key] = tmp
            elif isinstance(val, list):
                unified_config[key] = (unified_config.get(key, []) + val)
            else:
                unified_config[key] = new_dict[key]
        return unified_config
    def unify_conf(self, running_time= False):
        self._conf_parser.data = self.deep_normalize(self._conf_parser.data)
        self._exp_parser.data = self.deep_normalize(self._exp_parser.data)
        self._jobs_parser.data = self.deep_normalize(self._jobs_parser.data)
        self._platforms_parser.data = self.deep_normalize(self._platforms_parser.data)
        self.experiment_data = self.deep_update(self._conf_parser.data,self._exp_parser.data)
        self.experiment_data = self.deep_update(self.experiment_data,self._jobs_parser.data)
        self.experiment_data = self.deep_update(self.experiment_data,self._platforms_parser.data)
        if self._proj_parser_file.exists():
            self._proj_parser.data = self.deep_normalize(self._proj_parser.data)
            self.experiment_data = self.deep_update(self.experiment_data,self._proj_parser.data)
        for c_parser in self._custom_parser:
            c_parser.data = self.deep_normalize(c_parser.data)
            self.experiment_data = self.deep_update(self.experiment_data,c_parser.data)



    def check_conf_files(self, running_time=False):
        """
        Checks configuration files (autosubmit, experiment jobs and platforms), looking for invalid values, missing
        required options. Prints results in log

        :return: True if everything is correct, False if it finds any error
        :rtype: bool
        """

        Log.info('\nChecking configuration files...')
        self.ignore_file_path = running_time
        self.ignore_undefined_platforms = running_time

        try:
            self.reload()
        except IOError as e:
            raise AutosubmitError(
                "I/O Issues con config files", 6016, e.message)
        except (AutosubmitCritical, AutosubmitError) as e:
            raise
        except BaseException as e:
            raise AutosubmitCritical("Unknown issue while checking the configulation files (check_conf_files)",7040,str(e))
        # Annotates all errors found in the configuration files in dictionaries self.warn_config and self.wrong_config.
        # TODO checks should be now a single function without rely on get_option methods
        self.check_expdef_conf()
        self.check_platforms_conf()
        self.check_jobs_conf()
        self.check_autosubmit_conf()
        try:
            if self.get_project_type() != "none":
                # Check proj configuration
                self.check_proj()
        except:
            # This exception is in case that the experiment doesn't contains any file ( usefull for test the workflow with None Option)
            pass
        # End of checkers.

        # This Try/Except is in charge of  print all the info gathered by all the checkers and stop the program if any critical error is found.
        try:
            result = self.show_messages()
            return result
        except AutosubmitCritical as e:
            # In case that there are critical errors in the configuration, Autosubmit won't continue.
            if running_time is True:
                raise AutosubmitCritical(e.message, e.code, e.trace)
        except Exception as e:
            raise AutosubmitCritical(
                "There was an error while showing the config log messages", 7014, str(e))

    def check_autosubmit_conf(self):
        """
        Checks experiment's autosubmit configuration file.

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """
        if not self._conf_parser.check_exists('config', 'AUTOSUBMIT_VERSION'):
            self.wrong_config["Autosubmit"] += [['config',
                                                 "AUTOSUBMIT_VERSION parameter not found"]]
        if not self._conf_parser.check_exists('config', 'MAXWAITINGJOBS')[1] == type(int):
            self.wrong_config["Autosubmit"] += [['config',
                                                 "MAXWAITINGJOBS parameter not found or non-integer"]]
        if not self._conf_parser.check_exists('config', 'TOTALJOBS')[1] == type(int):
            self.wrong_config["Autosubmit"] += [['config',
                                                 "TOTALJOBS parameter not found or non-integer"]]
        if not self._conf_parser.check_exists('config', 'SAFETYSLEEPTIME')[1] == type(int):
            self.set_safetysleeptime(10)
            # self.wrong_config["Autosubmit"] += [['config',
            #                                     "SAFETYSLEEPTIME parameter not found or non-integer"]]
        if not self._conf_parser.check_exists('config', 'RETRIALS')[1] == type(int):
            self.wrong_config["Autosubmit"] += [['config',
                                                 "RETRIALS parameter not found or non-integer"]]
        if not self._conf_parser.check_exists('mail', 'NOTIFICATIONS')[1] == type(bool):
            self.wrong_config["Autosubmit"] += [['mail',
                                                 "NOTIFICATIONS parameter not found or non-boolean"]]
        if self._conf_parser.check_is_choice('storage', 'TYPE', False, ['pkl', 'db']):
            self.wrong_config["Autosubmit"] += [['storage',
                                                 "TYPE parameter not found"]]


        if self.get_wrapper_type()[0] == 'multi':
            list_of_wrappers = self.get_wrapper_multi() # list
            for wrapper_section_name in self.get_wrapper_multi():
                self.check_wrapper_conf(wrapper_section_name)
        elif self.get_wrapper_type()[0]:
            self.check_wrapper_conf()

        if self.get_notifications() is True:
            for mail in self.data["NOTIFICATIONS"]:
                if not self.is_valid_mail_address(mail):
                    self.wrong_config["Autosubmit"] += [['mail',
                                                         "invalid e-mail"]]
        if "Autosubmit" not in self.wrong_config:
            Log.result('{0} OK'.format(
                os.path.basename(self._conf_parser_file)))
            return True
        else:
            Log.warning('{0} Issues'.format(
                os.path.basename(self._conf_parser_file)))
            return True
        return False

    def check_platforms_conf(self):
        """
        Checks experiment's queues configuration file.
        """
        main_platform_found = False
        if self.hpcarch.lower() == "local":
            main_platform_found = True
        elif self.ignore_undefined_platforms:
            main_platform_found = True
        for section in self._platforms_parser.data:
            if section == self.hpcarch:
                main_platform_found = True
                platform_type = self._platforms_parser.check_exists(section, 'TYPE')[0]
                if not platform_type:
                    self.wrong_config["Platform"] += [[section,"Mandatory TYPE parameter not found"]]
                platform_type = platform_type.lower()
                if platform_type != 'ps':
                    if not self._platforms_parser.check_exists(section, 'PROJECT'):
                        self.wrong_config["Platform"] += [[section,
                                                           "Mandatory PROJECT parameter not found"]]
                    if not self._platforms_parser.check_exists(section, 'USER'):
                        self.wrong_config["Platform"] += [[section,
                                                           "Mandatory USER parameter not found"]]
            if not self._platforms_parser.check_exists(section, 'HOST'):
                self.wrong_config["Platform"] += [[section,
                                                   "Mandatory HOST parameter not found"]]
            if not self._platforms_parser.check_exists(section, 'SCRATCH_DIR'):
                self.wrong_config["Platform"] += [[section,
                                                   "Mandatory SCRATCH_DIR parameter not found"]]
            if not self._platforms_parser.check_exists(section, 'ADD_PROJECT_TO_HOST')[1] == type(bool):
                self.wrong_config["Platform"] += [
                    [section, "Mandatory ADD_PROJECT_TO_HOST parameter not found or non-boolean"]]
            if not self._platforms_parser.check_exists(section, 'TEST_SUITE')[1] == type(bool):
                self.wrong_config["Platform"] += [[section,
                                                   "Mandatory TEST_SUITE parameter not found or non-boolean"]]
            if not self._platforms_parser.check_exists(section, 'MAX_WAITING_JOBS')[1] == type(int):
                self.wrong_config["Platform"] += [
                    [section, "Mandatory MAX_WAITING_JOBS parameter not found or non-integer"]]
            if not self._platforms_parser.check_exists(section, 'TOTAL_JOBS')[1] == type(int):
                self.wrong_config["Platform"] += [[section,
                                                   "Mandatory TOTAL_JOBS parameter not found or non-integer"]]
        if not main_platform_found:
            self.wrong_config["Expdef"] += [["Default",
                                             "Main platform is not defined! check if [HPCARCH = {0}] has any typo".format(self.hpcarch)]]
        if "Platform" not in self.wrong_config:
            Log.result('{0} OK'.format(
                os.path.basename(self._platforms_parser_file)))
            return True
        return False

    def check_jobs_conf(self):
        """
        Checks experiment's jobs configuration file.

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """
        parser = self._jobs_parser
        platforms = self._platforms_parser.data
        #platforms.append('LOCAL')
        #platforms.append('local')
        for section in parser.data:
            if not parser.check_exists(section, 'FILE'):
                self.wrong_config["Jobs"] += [[section,
                                               "Mandatory FILE parameter not found"]]
            else:
                section_file_path = parser.check_exists(section, 'FILE')
                try:
                    if self.ignore_file_path:
                        if not os.path.exists(os.path.join(self.get_project_dir(), section_file_path)):
                            if parser.check_exists(section, 'CHECK'):
                                if not parser.get_option(section, 'CHECK') in "on_submission":
                                    self.wrong_config["Jobs"] += [
                                        [section, "FILE {0} doesn't exist and check parameter is not set on_submission value".format(section_file_path)]]
                            else:
                                self.wrong_config["Jobs"] += [[section, "FILE {0}  doesn't exist".format(
                                    os.path.join(self.get_project_dir(), section_file_path))]]
                except BaseException:
                    pass  # tests conflict quick-patch
            if not parser.check_exists(section, 'RERUN_ONLY')[1] == type(bool):
                self.wrong_config["Jobs"] += [[section,
                                               "Mandatory RERUN_ONLY parameter not found or non-bool"]]
            if not parser.check_is_choice(section, 'PLATFORM', False, platforms):
                self.wrong_config["Jobs"] += [
                    [section, "PLATFORM parameter is invalid, this platform is not configured"]]

            dependencies = str(parser.check_exists(section, 'DEPENDENCIES')[0])
            if not dependencies:
                for dependency in dependencies.split(' '):
                    if '-' in dependency:
                        dependency = dependency.split('-')[0]
                    elif '+' in dependency:
                        dependency = dependency.split('+')[0]
                    elif '*' in dependency:
                        dependency = dependency.split('*')[0]
                    elif '?' in dependency:
                        dependency = dependency.split('?')[0]
                    if '[' in dependency:
                        dependency = dependency[:dependency.find('[')]
                    if dependency not in parser.data.keys():
                        self.warn_config["Jobs"].append(
                            [section, "Dependency parameter is invalid, job {0} is not configured".format(dependency)])
            rerun_dependencies = str(parser.check_exists(section, 'RERUN_DEPENDENCIES')[0])
            if not rerun_dependencies:
                for dependency in rerun_dependencies.split(' '):
                    if '-' in dependency:
                        dependency = dependency.split('-')[0]
                    if '[' in dependency:
                        dependency = dependency[:dependency.find('[')]
                    if dependency not in parser.data.keys():
                        self.warn_config["Jobs"] += [
                            [section, "RERUN_DEPENDENCIES parameter is invalid, job {0} is not configured".format(dependency)]]

            if not parser.check_is_choice(section, 'RUNNING', False, ['once', 'date', 'member', 'chunk']):
                self.wrong_config["Jobs"] += [[section,
                                               "Mandatory RUNNING parameter is invalid"]]
        if "Jobs" not in self.wrong_config:
            Log.result('{0} OK'.format(
                os.path.basename(self._jobs_parser_file)))
            return True
        return False

    def check_expdef_conf(self):
        """
        Checks experiment's experiment configuration file.

        :return: True if everything is correct, False if it founds any error
        :rtype: bool
        """
        parser = self._exp_parser
        if not parser.check_exists('DEFAULT', 'EXPID'):
            self.wrong_config["Expdef"] += [['DEFAULT',
                                             "Mandatory EXPID parameter is invalid"]]

        self.hpcarch,_ = parser.check_exists('DEFAULT', 'HPCARCH')
        if not self.hpcarch:
            self.wrong_config["Expdef"] += [['DEFAULT',
                                             "Mandatory HPCARCH parameter is invalid"]]
        if not parser.check_exists('experiment', 'DATELIST'):
            self.wrong_config["Expdef"] += [['DEFAULT',
                                             "Mandatory DATELIST parameter is invalid"]]
        if not parser.check_exists('experiment', 'MEMBERS'):
            self.wrong_config["Expdef"] += [['DEFAULT',
                                             "Mandatory MEMBERS parameter is invalid"]]
        if not parser.check_is_choice('experiment', 'CHUNKSIZEUNIT', True, ['year', 'month', 'day', 'hour']):
            self.wrong_config["Expdef"] += [['experiment',"Mandatory CHUNKSIZEUNIT choice is invalid"]]

        if not parser.check_exists('experiment', 'CHUNKSIZE'):
            self.wrong_config["Expdef"] += [['experiment',
                                             "Mandatory CHUNKSIZE is not an integer"]]
        if parser.check_exists('experiment', 'NUMCHUNKS')[1] == type(int):
            self.wrong_config["Expdef"] += [['experiment',
                                             "Mandatory NUMCHUNKS is not an integer"]]

        if not parser.check_is_choice('experiment', 'CALENDAR', True,
                                      ['standard', 'noleap']):
            self.wrong_config["Expdef"] += [['experiment',
                                             "Mandatory CALENDAR choice is invalid"]]

        if parser.check_exists('rerun', 'RERUN')[1] == type(bool):
            self.wrong_config["Expdef"] += [['experiment',
                                             "Mandatory RERUN choice is not a boolean"]]
        project_type = parser.check_is_choice('project', 'PROJECT_TYPE', True, ['none', 'git', 'svn', 'local'])
        if project_type is not False:
            if project_type == 'git':
                if not parser.check_exists('git', 'PROJECT_ORIGIN'):
                    self.wrong_config["Expdef"] += [['git',
                                                     "PROJECT_ORIGIN parameter is invalid"]]
                if not parser.check_exists('git', 'PROJECT_BRANCH'):
                    self.wrong_config["Expdef"] += [['git',
                                                     "PROJECT_BRANCH parameter is invalid"]]

            elif project_type == 'svn':
                if not parser.check_exists('svn', 'PROJECT_URL'):
                    self.wrong_config["Expdef"] += [['svn',
                                                     "PROJECT_URL parameter is invalid"]]
                if not parser.check_exists('svn', 'PROJECT_REVISION'):
                    self.wrong_config["Expdef"] += [['svn',
                                                     "PROJECT_REVISION parameter is invalid"]]
            elif project_type == 'local':
                if not parser.check_exists('local', 'PROJECT_PATH'):
                    self.wrong_config["Expdef"] += [['local',
                                                     "PROJECT_PATH parameter is invalid"]]
            elif project_type == 'none':  # debug propouses
                self.ignore_file_path = False

            if project_type != 'none':
                if not parser.check_exists('project_files', 'FILE_PROJECT_CONF'):
                    self.wrong_config["Expdef"] += [['project_files',
                                                     "FILE_PROJECT_CONF parameter is invalid"]]
        else:
            self.wrong_config["Expdef"] += [['project',
                                             "Mandatory project choice is invalid"]]

        if "Expdef" not in self.wrong_config:
            Log.result('{0} OK'.format(
                os.path.basename(self._exp_parser_file)))
            return True
        return False

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
                self._proj_parser = AutosubmitConfig.get_parser(
                    self.parser_factory, self._proj_parser_file)
            return True
        except Exception as e:
            self.wrong_config["Proj"] += [['project_files',
                                           "FILE_PROJECT_CONF parameter is invalid"]]
            return False

    def check_wrapper_conf(self,wrapper_section_name="wrapper"):
        if not self.is_valid_jobs_in_wrapper(wrapper_section_name):
            self.wrong_config["Wrapper"] += [[wrapper_section_name,
                                              "JOBS_IN_WRAPPER contains non-defined jobs.  parameter is invalid"]]
        if 'horizontal' in self.get_wrapper_type(wrapper_section_name):
            if not self._platforms_parser.check_exists(self.get_platform(), 'PROCESSORS_PER_NODE'):
                self.wrong_config["Wrapper"] += [
                    [wrapper_section_name, "PROCESSORS_PER_NODE no exist in the horizontal-wrapper platform"]]
            if not self._platforms_parser.check_exists(self.get_platform(), 'MAX_PROCESSORS'):
                self.wrong_config["Wrapper"] += [[wrapper_section_name,
                                                  "MAX_PROCESSORS no exist in the horizontal-wrapper platform"]]
        if 'vertical' in self.get_wrapper_type(wrapper_section_name):
            if not self._platforms_parser.check_exists(self.get_platform(), 'MAX_WALLCLOCK'):
                self.wrong_config["Wrapper"] += [[wrapper_section_name,
                                                  "MAX_WALLCLOCK no exist in the vertical-wrapper platform"]]
        if "Wrapper" not in self.wrong_config:
            Log.result('wrappers OK')
            return True

    def reload(self):
        """
        Creates parser objects for configuration files
        """
        try:
            self._conf_parser = AutosubmitConfig.get_parser(
                self.parser_factory, self._conf_parser_file)
            self._platforms_parser = AutosubmitConfig.get_parser(
                self.parser_factory, self._platforms_parser_file)
            self._jobs_parser = AutosubmitConfig.get_parser(
                self.parser_factory, self._jobs_parser_file)
            self._exp_parser = AutosubmitConfig.get_parser(
                self.parser_factory, self._exp_parser_file)
            self._custom_parser = []
            for custom_file in self._custom_parser_files:
                self._custom_parser.append(AutosubmitConfig.get_parser(
                self.parser_factory, custom_file))
        except IOError as e:
            raise AutosubmitError("IO issues during the parsing of configuration files",6014,str(e))
        except Exception as e:
            raise AutosubmitCritical(
                "{0} \n Repeated parameter, check if you have any uncommented value that should be commented".format(str(e)), 7014)
        try:
            if self._proj_parser_file == '':
                self._proj_parser = None
            else:
                self._proj_parser = AutosubmitConfig.get_parser(
                    self.parser_factory, self._proj_parser_file)
        except IOError as e:
            raise AutosubmitError("IO issues during the parsing of configuration files",6014,str(e))
        self.unify_conf()

    def load_parameters(self):
        """
        Load parameters from experiment and autosubmit config files. If experiment's type is not none,
        also load parameters from model's config file

        :return: a dictionary containing tuples [parameter_name, parameter_value]
        :rtype: dict
        """
        try:
            parameters = dict()
            for section in self._exp_parser.sections():
                for option in self._exp_parser.options(section):
                    parameters[option] = self._exp_parser.get(section, option)
            for section in self._conf_parser.sections():
                for option in self._conf_parser.options(section):
                    parameters[option] = self._conf_parser.get(section, option)
            parameters['PROJECT_TYPE'] = self.get_project_type()
            if parameters['PROJECT_TYPE'] != "none" and self._proj_parser is not None:
                # Load project parameters
                Log.debug("Loading project parameters...")
                parameters2 = parameters.copy()
                parameters2.update(self.load_project_parameters())
                parameters = parameters2
            return parameters
        except IOError as e:
            raise AutosubmitError("Local Platform IO_ERROR, Can't not get experiment parameters from files.",6000,str(e))
        except Exception as e:
            raise AutosubmitError("Local Platform IO_ERROR, Can't not get experiment parameters from files.", 6000,str(e))

    def load_platform_parameters(self):
        """
        Load parameters from platform config files.

        :return: a dictionary containing tuples [parameter_name, parameter_value]
        :rtype: dict
        """
        parameters = dict()
        for section in self._platforms_parser.sections():
            for option in self._platforms_parser.options(section):
                parameters[section + "_" +
                           option] = self._platforms_parser.get(section, option)
        return parameters

    def load_section_parameters(self, job_list, as_conf, submitter):
        """
        Load parameters from job config files.

        :return: a dictionary containing tuples [parameter_name, parameter_value]
        :rtype: dict
        """
        as_conf.check_conf_files(False)

        job_list_by_section = defaultdict()
        parameters = defaultdict()
        for job in job_list.get_job_list():
            if job.platform_name is None:
                job.platform_name = self.hpcarch
            if job.section not in list(job_list_by_section.keys()):
                job_list_by_section[job.section] = [job]
            else:
                job_list_by_section[job.section].append(job)
            try:
                job.platform = submitter.platforms[job.platform_name.lower()]
            except:
                job.platform = submitter.platforms["local"]

        for section in list(job_list_by_section.keys()):
            job_list_by_section[section][0].update_parameters(
                as_conf, job_list.parameters)
            section_list = list(job_list_by_section[section][0].parameters.keys())
            for section_param in section_list:
                if section_param not in list(job_list.parameters.keys()):
                    parameters[section + "_" +
                               section_param] = job_list_by_section[section][0].parameters[section_param]
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
            content = content.replace(
                re.search('EXPID =.*', content).group(0), "EXPID = " + exp_id)
        open(self._exp_parser_file, 'wb').write(content)

        content = open(self._conf_parser_file).read()
        if re.search('EXPID =.*', content):
            content = content.replace(
                re.search('EXPID =.*', content).group(0), "EXPID = " + exp_id)
        open(self._conf_parser_file, 'wb').write(content)

    def get_project_type(self):
        """
        Returns project type from experiment config file

        :return: project type
        :rtype: str
        """
        return self.get_section(["project", "project_type"],must_exists=True)


    def get_parse_two_step_start(self):
        """
        Returns two step start jobs

        :return: jobs_list
        :rtype: str
        """

        return self.get_section('experiment', 'TWO_STEP_START', '').lower()

    def get_rerun_jobs(self):
        """
        Returns rerun jobs

        :return: jobs_list
        :rtype: str
        """

        return self.get_section('rerun', 'RERUN_JOBLIST', '').lower()

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
        return self.get_section('project_files', 'FILE_JOBS_CONF', '')

    def get_git_project_origin(self):
        """
        Returns git origin from experiment config file

        :return: git origin
        :rtype: str
        """
        return self.get_section('git', 'PROJECT_ORIGIN', '')

    def get_git_project_branch(self):
        """
        Returns git branch  from experiment's config file

        :return: git branch
        :rtype: str
        """
        return self.get_section('git', 'PROJECT_BRANCH', 'master')

    def get_git_project_commit(self):
        """
        Returns git commit from experiment's config file

        :return: git commit
        :rtype: str
        """
        return self.get_section('git', 'PROJECT_COMMIT', None)

    def get_git_remote_project_root(self):
        """
        Returns remote machine ROOT PATH

        :return: git commit
        :rtype: str
        """
        return self.get_section('git', 'REMOTE_CLONE_ROOT', '')

    def get_submodules_list(self):
        """
        Returns submodules list from experiment's config file
        Default is --recursive
        :return: submodules to load
        :rtype: list
        """
        return ' '.join(self.get_section('git', 'PROJECT_SUBMODULES', '').split()).split()

    def get_fetch_single_branch(self):
        """
        Returns fetch single branch from experiment's config file
        Default is -single-branch
        :return: fetch_single_branch(Y/N)
        :rtype: boolean
        """
        return self.get_section('git', 'FETCH_SINGLE_BRANCH', 'False').lower()

    def get_project_destination(self):
        """
        Returns git commit from experiment's config file

        :return: git commit
        :rtype: str
        """
        try:
            value = self._exp_parser.get('project', 'PROJECT_DESTINATION')
            if not value:
                if self.get_project_type().lower() == "local":
                    value = os.path.split(self.get_local_project_path())[1]
                elif self.get_project_type().lower() == "svn":
                    value = self.get_svn_project_url().split('/')[-1]
                elif self.get_project_type().lower() == "git":
                    value = self.get_git_project_origin().split(
                        '/')[-1].split('.')[-2]
            return value
        except Exception as exp:
            Log.debug(str(exp))
            Log.debug(traceback.format_exc())
            return ''

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
        except subprocess.CalledProcessError as e:
            raise AutosubmitCritical(
                "Failed to retrieve project branch...", 7014, str(e))

        project_branch = output
        Log.debug("Project branch is: " + project_branch)
        try:
            output = subprocess.check_output(
                "cd {0}; git rev-parse HEAD".format(full_project_path), shell=True)
        except subprocess.CalledProcessError as e:
            raise AutosubmitCritical(
                "Failed to retrieve project commit SHA...", 7014, str(e))
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
        open(self._exp_parser_file, 'wb').write(content)
        Log.debug(
            "Project commit SHA succesfully registered to the configuration file.")
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
                            date_list.append(parse_date(
                                string_date + str(count).zfill(len(numbers[0]))))
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
        chunk_ini = self.get_section(
            'experiment', 'CHUNKINI', default)
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

    def get_chunk_size(self, default=1):
        """
        Chunk Size as defined in the expdef file.

        :return: Chunksize, 1 as default.
        :rtype: int
        """
        chunk_size = self.get_section(
            'experiment', 'CHUNKSIZE', default)
        if chunk_size == '':
            return default
        return int(chunk_size)

    def get_member_list(self, run_only=False):
        """
        Returns members list from experiment's config file

        :return: experiment's members
        :rtype: list
        """
        member_list = list()
        string = self._exp_parser.get('experiment', 'MEMBERS') if run_only == False else self.get_section(
            'experiment', 'RUN_ONLY_MEMBERS', '')
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
                            member_list.append(
                                string_member + str(count).zfill(len(numbers[0])))
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
    def get_dependencies(self, section="None"):
        """
        Returns dependencies list from jobs config file

        :return: experiment's members
        :rtype: list
        """
        try:
            return self.jobs_parser.get_option(section, "DEPENDENCIES", "").split()
        except:
            return []

        if section is not None:
            return member_list
        else:
            return None

    def get_rerun(self):
        """
        Returns startdates list from experiment's config file

        :return: rerurn value
        :rtype: list
        """

        return self._exp_parser.get('rerun', 'RERUN').lower()



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
        content = open(self._exp_parser_file).read()
        if re.search('HPCARCH =.*', content):
            content = content.replace(
                re.search('HPCARCH =.*', content).group(0), "HPCARCH = " + hpc)
        open(self._exp_parser_file, 'wb').write(content)

    def set_version(self, autosubmit_version):
        """
        Sets autosubmit's version in autosubmit's config file

        :param autosubmit_version: autosubmit's version
        :type autosubmit_version: str
        """
        content = open(self._conf_parser_file, 'rb').read()
        if re.search(rb'AUTOSUBMIT_VERSION =.*', content):
            content = content.replace(re.search(rb'AUTOSUBMIT_VERSION =.*', content).group(0),str.encode("AUTOSUBMIT_VERSION = " + autosubmit_version,locale.getlocale()[1]))
        open(self._conf_parser_file, 'wb').write(content)

    def get_version(self):
        """
        Returns version number of the current experiment from autosubmit's config file

        :return: version
        :rtype: str
        """
        return self.get_section(['config', 'AUTOSUBMIT_VERSION'], 'None')

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
        return self.get_section(['config', 'OUTPUT'], 'pdf')

    def get_max_wallclock(self):
        """
        Returns max wallclock

        :rtype: str
        """
        return self.get_section(['config', 'MAX_WALLCLOCK'], '')

    def get_disable_recovery_threads(self, section):
        """
        Returns FALSE/TRUE
        :return: recovery_threads_option
        :rtype: str
        """
        return self.get_section(section, 'DISABLE_RECOVERY_THREADS', 'FALSE').lower()

    def get_max_processors(self):
        """
        Returns max processors from autosubmit's config file

        :rtype: str
        """
        return  self.get_section(['config', 'MAX_PROCESSORS'], None)

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
        return self.get_section('project_files', 'JOB_SCRIPTS_TYPE', 'bash')

    def get_safetysleeptime(self):
        """
        Returns safety sleep time from autosubmit's config file

        :return: safety sleep time
        :rtype: int
        """
        return self.get_section(['config', 'SAFETYSLEEPTIME'], 10)

    def set_safetysleeptime(self, sleep_time):
        """
        Sets autosubmit's version in autosubmit's config file

        :param sleep_time: value to set
        :type sleep_time: int
        """
        content = open(self._conf_parser_file).read()
        content = content.replace(re.search('SAFETYSLEEPTIME:.*', content).group(0),"SAFETYSLEEPTIME: %d" % sleep_time)
        open(self._conf_parser_file, 'w').write(content)

    def get_retrials(self):
        """
        Returns max number of retrials for job from autosubmit's config file

        :return: safety sleep time
        :rtype: int
        """
        return int(self._conf_parser.get('config', 'RETRIALS'))

    def get_delay_retry_time(self):
        """
        Returns delay time from autosubmit's config file

        :return: safety sleep time
        :rtype: int
        """
        return self.get_section(['config', 'DELAY_RETRY_TIME'], -1)

    def get_notifications(self):
        """
        Returns if the user has enabled the notifications from autosubmit's config file

        :return: if notifications
        :rtype: string
        """
        return self._conf_parser.check_exists('config', 'MAXWAITINGJOBS')

    def get_notifications_crash(self):
        """
        Returns if the user has enabled the notifications from autosubmit's config file

        :return: if notifications
        :rtype: string
        """
        return self.get_section(['mail', 'NOTIFY_ON_REMOTE_FAIL'], True)
    def get_remote_dependencies(self):
        """
        Returns if the user has enabled the PRESUBMISSION configuration parameter from autosubmit's config file

        :return: if remote dependencies
        :rtype: bool
        """
        return self.get_section(['config', 'PRESUBMISSION'], False)


    def get_wrapper_type(self, wrapper_section_name="wrapper"):
        """
        Returns what kind of wrapper (VERTICAL, MIXED-VERTICAL, HORIZONTAL, HYBRID, MULTI NONE) the user has configured in the autosubmit's config

        :return: wrapper type (or none)
        :rtype: string
        """

        value1,value2 = self._conf_parser.check_exists(wrapper_section_name, 'TYPE')
        if not value1:
            return value1,value2
        else:
            return value1.lower(),value2

    def get_wrapper_retrials(self, wrapper_section_name=[]):
        """
        Returns max number of retrials for job from autosubmit's config file

        :return: safety sleep time
        :rtype: int
        """
        #todo
        return self.get_section(["WRAPPER"].extend(wrapper_section_name)+['INNER_RETRIALS'], 0)
    def get_wrapper_multi(self):
        """
        return the section name of the wrappers

        :return: wrapper section list
        :rtype: string
        """
        list_of_wrappers = self._conf_parser.check_exists("wrapper", 'WRAPPER_LIST')
        if "," in list_of_wrappers:
            list_of_wrappers = list_of_wrappers.split(',')
        else:
            list_of_wrappers = []
        return list_of_wrappers

    def get_wrapper_policy(self,wrapper_section_name="wrapper"):
        """
        Returns what kind of policy (flexible, strict, mixed ) the user has configured in the autosubmit's config

        :return: wrapper type (or none)
        :rtype: string
        """
        return self.get_section(wrapper_section_name, 'POLICY', 'flexible').lower()

    def get_wrapper_jobs(self,wrapper_section_name="wrapper"):
        """
        Returns the jobs that should be wrapped, configured in the autosubmit's config

        :return: expression (or none)
        :rtype: string
        """
        return self.get_section(wrapper_section_name, 'JOBS_IN_WRAPPER', 'None')

    def get_extensible_wallclock(self, wrapper_section_name="wrapper"):
        """
        Gets extend_wallclock for the given wrapper
        :param section: job type
        :type section: str
        :return: wallclock time
        :rtype: str
        """
        return int(self.get_section(wrapper_section_name, 'EXTEND_WALLCLOCK', 0))

    def get_x11_jobs(self):
        """
        Returns the jobs that should support x11, configured in the autosubmit's config

        :return: expression (or none)
        :rtype: string
        """
        return self.get_section(['config', 'X11_JOBS'], None)

    def get_wrapper_queue(self,wrapper_section_name="wrapper"):
        """
        Returns the wrapper queue if not defined, will be the one of the first job wrapped

        :return: expression (or none)
        :rtype: string
        """
        return self.get_section(wrapper_section_name, 'QUEUE', 'None')

    def get_min_wrapped_jobs(self,wrapper_section_name="wrapper"):
        """
         Returns the minim number of jobs that can be wrapped together as configured in autosubmit's config file

        :return: minim number of jobs (or total jobs)
        :rtype: int
        """
        return int(self.get_section(wrapper_section_name, 'MIN_WRAPPED', 2))

    def get_max_wrapped_jobs(self,wrapper_section_name="wrapper"):
        """
         Returns the maximum number of jobs that can be wrapped together as configured in autosubmit's config file

         :return: maximum number of jobs (or total jobs)
         :rtype: int
         """
        return int(self.get_section(wrapper_section_name, 'MAX_WRAPPED', self.get_total_jobs()))

    def get_max_wrapped_jobs_vertical(self, wrapper_section_name="wrapper"):
        """
         Returns the maximum number of jobs that can be wrapped together as configured in autosubmit's config file

         :return: maximum number of jobs (or total jobs)
         :rtype: int
         """
        max_wrapped = self.get_max_wrapped_jobs(wrapper_section_name)
        return int(self.get_section(wrapper_section_name, 'MAX_WRAPPED_V', max_wrapped))

    def get_max_wrapped_jobs_horizontal(self, wrapper_section_name="wrapper"):
        """
         Returns the maximum number of jobs that can be wrapped together as configured in autosubmit's config file

         :return: maximum number of jobs (or total jobs)
         :rtype: int
         """
        max_wrapped = self.get_max_wrapped_jobs(wrapper_section_name)
        return int(self.get_section(wrapper_section_name, 'MAX_WRAPPED_H', max_wrapped))

    def get_min_wrapped_jobs_vertical(self, wrapper_section_name="wrapper"):
        """
         Returns the maximum number of jobs that can be wrapped together as configured in autosubmit's config file

         :return: maximum number of jobs (or total jobs)
         :rtype: int
         """
        return int(self.get_section(wrapper_section_name, 'MIN_WRAPPED_V', 1))

    def get_min_wrapped_jobs_horizontal(self, wrapper_section_name="wrapper"):
        """
         Returns the maximum number of jobs that can be wrapped together as configured in autosubmit's config file

         :return: maximum number of jobs (or total jobs)
         :rtype: int
         """
        return int(self.get_section(wrapper_section_name, 'MIN_WRAPPED_H', 1))

    def get_wrapper_method(self,wrapper_section_name="wrapper"):
        """
         Returns the method of make the wrapper

         :return: method
         :rtype: string
         """
        return self.get_section(wrapper_section_name, 'METHOD', 'ASThread')

    def get_wrapper_check_time(self,wrapper_section_name="wrapper"):
        """
         Returns time to check the status of jobs in the wrapper

         :return: wrapper check time
         :rtype: int
         """
        return int(self.get_section(wrapper_section_name, 'CHECK_TIME_WRAPPER', self.get_safetysleeptime()))

    def get_wrapper_machinefiles(self,wrapper_section_name="wrapper"):
        """
         Returns the strategy for creating the machinefiles in wrapper jobs

         :return: machinefiles function to use
         :rtype: string
         """
        return self.get_section(wrapper_section_name, 'MACHINEFILES', '')
    def get_export(self, section):
        """
        Gets command line for being submitted with
        :param section: job type
        :type section: str
        :return: wallclock time
        :rtype: str
        """
        return self.get_section(section, 'EXPORT', "none")

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
        return self.get_section(['storage', 'COPY_REMOTE_LOGS'], True)

    def get_mails_to(self):
        """
        Returns the address where notifications will be sent from autosubmit's config file

        :return: mail address
        :rtype: [str]
        """
        return  self.get_section(['mail', 'TO'], [])

    def get_communications_library(self):
        """
        Returns the communications library from autosubmit's config file. Paramiko by default.

        :return: communications library
        :rtype: str
        """
        return self.get_section(['communications', 'API'], 'paramiko')

    def get_storage_type(self):
        """
        Returns the storage system from autosubmit's config file. Pkl by default.

        :return: communications library
        :rtype: str
        """
        return self.get_section(['storage', 'TYPE'], 'pkl').lower()

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

    def is_valid_jobs_in_wrapper(self,wrapper_section_name="wrapper"):
        expression = self.get_wrapper_jobs(wrapper_section_name="wrapper")
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
        :type file_path: Path
        :return: parser
        :rtype: YAMLParser
        """
        parser = parser_factory.create_parser()
        # For testing purposes
        if file_path == Path('/dummy/local/root/dir/a000/conf/') or file_path == Path('dummy/file/path'):
            parser.data = parser.load(file_path)

            return parser

            # proj file might not be present

        if file_path.match("*proj*"):
            if file_path.exists():
                parser.data = parser.load(file_path)
            else:
                Log.warning( "{0} was not found. Some variables might be missing. If your experiment does not need a proj file, you can ignore this message.", file_path)
        else:
            # This block may rise an exception but all its callers handle it
            try:
                with open(file_path) as f:
                    parser.data = parser.load(f)
            except IOError as exp:
                raise
            except Exception as exp:
                raise Exception(
                    "{}\n This file and the correctness of its content are necessary.".format(str(exp)))
        return parser

