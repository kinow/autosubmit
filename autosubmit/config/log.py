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

import logging
import sys


class LogFormatter:
    RESULT = '\033[32m'
    WARNING = '\033[33m'
    ERROR = '\033[31m'
    CRITICAL = '\033[1m \033[31m'
    DEFAULT = '\033[0m\033[39m'

    def __init__(self, to_file=False):
        self._file = to_file
        if self._file:
            self._formatter = logging.Formatter('%(asctime)s %(message)s')
        else:
            self._formatter = logging.Formatter('%(message)s')

    def format(self, record):
        header = ''
        if record.levelno == Log.RESULT:
            if not self._file:
                header = LogFormatter.RESULT
        elif record.levelno == Log.USER_WARNING:
            if not self._file:
                header = LogFormatter.WARNING
        elif record.levelno == Log.WARNING:
            if not self._file:
                header = LogFormatter.WARNING
            header += "[WARNING] "
        elif record.levelno == Log.ERROR:
            if not self._file:
                header = LogFormatter.ERROR
            header += "[ERROR] "
        elif record.levelno == Log.CRITICAL:
            if not self._file:
                header = LogFormatter.ERROR
            header += "[CRITICAL] "

        msg = self._formatter.format(record)
        if header != '' and not self._file:
            msg += LogFormatter.DEFAULT
        return header + msg


class Log:
    """
    Static class to manage the log for the application. Messages will be sent to console and to file if it is
    configured. Levels can be set for each output independently. These levels are (from lower to higher priority):

    EVERYTHING : this level is just defined to show every output
    DEBUG
    INFO
    RESULT
    USER_WARNING
    WARNING
    ERROR
    CRITICAL
    NO_LOG : this level is just defined to remove every output
    """
    EVERYTHING = 0
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    RESULT = 25
    USER_WARNING = 29
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    NO_LOG = CRITICAL + 1

    logging.basicConfig()

    log = logging.Logger('Autosubmit', EVERYTHING)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(INFO)
    console_handler.setFormatter(LogFormatter(False))
    log.addHandler(console_handler)

    file_handler = None
    file_level = INFO

    @staticmethod
    def set_file(file_path):
        """
        Configure the file to store the log. If another file was specified earlier, new messages will only go to the
        new file.
        :param file_path: file to store the log
        """
        if Log.file_handler is not None:
            Log.log.removeHandler(Log.file_handler)
        Log.file_handler = logging.FileHandler(file_path, 'w')
        Log.file_handler.setLevel(Log.file_level)
        Log.file_handler.setFormatter(LogFormatter(True))
        Log.log.addHandler(Log.file_handler)

    @staticmethod
    def set_console_level(level):
        if type(level) is str:
            level = getattr(Log, level)
        Log.console_handler.level = level

    @staticmethod
    def set_file_level(level):
        if type(level) is str:
            level = getattr(Log, level)
        Log.file_level = level
        if Log.file_handler is not None:
            Log.file_handler.level = level

    @staticmethod
    def debug(msg, *args, **kwargs):
        """
        Sends debug information to the log
        :param msg: message to show
        :param args:
        :param kwargs:
        """
        Log.log.debug(msg, *args, **kwargs)

    @staticmethod
    def info(msg, *args, **kwargs):
        """
        Sends information to the log
        :param msg: message to show
        :param args:
        :param kwargs:
        """
        Log.log.info(msg, *args, **kwargs)

    @staticmethod
    def result(msg, *args, **kwargs):
        """
        Sends results information to the log. It will be shown in green in the console.
        :param msg: message to show
        :param args:
        :param kwargs:
        """
        Log.log.log(Log.RESULT, msg, *args, **kwargs)

    @staticmethod
    def user_warning(msg, *args, **kwargs):
        """
        Sends warnings for the user to the log. It will be shown in yellow in the console.
        :param msg: message to show
        :param args:
        :param kwargs:
        """
        Log.log.log(Log.USER_WARNING, msg, *args, **kwargs)

    @staticmethod
    def warning(msg, *args, **kwargs):
        """
        Sends program warnings to the log. It will be shown in yellow in the console.
        :param msg: message to show
        :param args:
        :param kwargs:
        """
        Log.log.warning(msg, *args, **kwargs)

    @staticmethod
    def error(msg, *args, **kwargs):
        """
        Sends errors to the log. It will be shown in red in the console.
        :param msg: message to show
        :param args:
        :param kwargs:
        """
        Log.log.error(msg, *args, **kwargs)

    @staticmethod
    def critical(msg, *args, **kwargs):
        """
        Sends critical errors to the log. It will be shown in red in the console.
        :param msg: message to show
        :param args:
        :param kwargs:
        """
        Log.log.critical(msg, *args, **kwargs)


