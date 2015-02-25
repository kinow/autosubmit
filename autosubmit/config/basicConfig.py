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


class BasicConfig:

    DB_DIR = '/home/jvegas/debug/autosubmit'
    DB_FILE = 'autosubmit.db'
    DB_NAME = 'autosubmit'
    DB_PATH = DB_DIR + "/" + DB_FILE
    LOCAL_ROOT_DIR = '/home/jvegas/debug/autosubmit'
    LOCAL_TMP_DIR = 'tmp'
    LOCAL_PROJ_DIR = 'proj'

    @staticmethod
    def update_config():
        # De momento solo hace uno. Ya veremos si son necesarios mas
        BasicConfig.DB_PATH = os.path.join(BasicConfig.DB_DIR, BasicConfig.DB_FILE)

    @staticmethod
    def __read_file_config(file_path):
        if not os.path.isfile(file_path):
            return
        parser = SafeConfigParser()
        parser.optionxform = str
        parser.read(file_path)

        if parser.has_option('database', 'path'):
            BasicConfig.DB_DIR = parser.get('database', 'path')
        if parser.has_option('local', 'path'):
            BasicConfig.LOCAL_ROOT_DIR = parser.get('local', 'path')

    @staticmethod
    def read():
        filename = '.autosubmitrc'

        BasicConfig.__read_file_config(os.path.join('/etc', filename))
        BasicConfig.__read_file_config(os.path.join(os.path.expanduser('~'), filename))
        BasicConfig.__read_file_config(os.path.join('.', filename))

        BasicConfig.update_config()
        return