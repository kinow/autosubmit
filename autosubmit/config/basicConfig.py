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

from autosubmit.config.log import Log


class BasicConfig:
    """
    Class to manage configuration for autosubmit path, database and default values for new experiments
    """

    def __init__(self):
        pass

    DB_DIR = os.path.join(os.path.expanduser('~'), 'debug', 'autosubmit')
    DB_FILE = 'autosubmit.db'
    DB_PATH = os.path.join(DB_DIR, DB_FILE)
    LOCAL_ROOT_DIR = DB_DIR
    LOCAL_TMP_DIR = 'tmp'
    LOCAL_PROJ_DIR = 'proj'
    DEFAULT_PLATFORMS_CONF = ''
    DEFAULT_JOBS_CONF = ''
    SMTP_SERVER = ''
    MAIL_FROM = ''

    @staticmethod
    def _update_config():
        """
        Updates commonly used composed paths
        """
        # Just one needed for the moment.
        BasicConfig.DB_PATH = os.path.join(BasicConfig.DB_DIR, BasicConfig.DB_FILE)

    @staticmethod
    def __read_file_config(file_path):
        """
        Reads configuration file. If configuration file dos not exist in given path,
        no error is raised. Configuration options also are not required to exist

        :param file_path: configuration file to read
        :type file_path: str
        """
        if not os.path.isfile(file_path):
            return
        Log.debug('Reading config from ' + file_path)
        parser = SafeConfigParser()
        parser.optionxform = str
        parser.read(file_path)

        if parser.has_option('database', 'path'):
            BasicConfig.DB_DIR = parser.get('database', 'path')
        if parser.has_option('database', 'filename'):
            BasicConfig.DB_FILE = parser.get('database', 'filename')
        if parser.has_option('local', 'path'):
            BasicConfig.LOCAL_ROOT_DIR = parser.get('local', 'path')
        if parser.has_option('conf', 'platforms'):
            BasicConfig.DEFAULT_PLATFORMS_CONF = parser.get('conf', 'platforms')
        if parser.has_option('conf', 'jobs'):
            BasicConfig.DEFAULT_JOBS_CONF = parser.get('conf', 'jobs')
        if parser.has_option('mail', 'smtp_server'):
            BasicConfig.SMTP_SERVER = parser.get('mail', 'smtp_server')
        if parser.has_option('mail', 'mail_from'):
            BasicConfig.MAIL_FROM = parser.get('mail', 'mail_from')

    @staticmethod
    def read():
        """
        Reads configuration from .autosubmitrc files, first from /etc, then for user
        directory and last for current path.
        """
        filename = 'autosubmitrc'

        BasicConfig.__read_file_config(os.path.join('/etc', filename))
        BasicConfig.__read_file_config(os.path.join(os.path.expanduser('~'), '.' + filename))
        BasicConfig.__read_file_config(os.path.join('.', '.' + filename))

        BasicConfig._update_config()
        return
