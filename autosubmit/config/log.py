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

import logging
import os
import sys
from datetime import datetime


class LogFormatter:
    """
    Class to format log output.

    :param to_file: If True, creates a LogFormatter for files; if False, for console
    :type to_file: bool
    """
    RESULT = '\033[32m'
    WARNING = '\033[33m'
    ERROR = '\033[31m'
    CRITICAL = '\033[1m \033[31m'
    DEFAULT = '\033[0m\033[39m'

    def __init__(self, to_file=False):
        """
        Initializer for LogFormatter


        """
        self._file = to_file
        if self._file:
            self._formatter = logging.Formatter('%(asctime)s %(message)s')
        else:
            self._formatter = logging.Formatter('%(message)s')

    def format(self, record):
        """
        Format log output, adding labels if needed for log level. If logging to console, also manages font color.
        If logging to file adds timestamp

        :param record: log record to format
        :type record: LogRecord
        :return: formatted record
        :rtype: str
        """
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

        - EVERYTHING : this level is just defined to show every output
        - DEBUG
        - INFO
        - RESULT
        - USER_WARNING
        - WARNING
        - ERROR
        - CRITICAL
        - NO_LOG : this level is just defined to remove every output

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
        :type file_path: str
        """
        (directory, filename) = os.path.split(file_path)
        if not os.path.exists(directory):
            os.mkdir(directory)
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and
                 f.endswith(filename)]
        if len(files) >= 5:
            files.sort()
            os.remove(os.path.join(directory, files[0]))
        file_path = os.path.join(directory, '{0:%Y%m%d_%H%M%S}_'.format(datetime.now()) + filename)
        if Log.file_handler is not None:
            Log.log.removeHandler(Log.file_handler)
        Log.file_handler = logging.FileHandler(file_path, 'w')
        Log.file_handler.setLevel(Log.file_level)
        Log.file_handler.setFormatter(LogFormatter(True))
        Log.log.addHandler(Log.file_handler)
        os.chmod(file_path, 0o775)

    @staticmethod
    def set_console_level(level):
        """
        Sets log level for logging to console. Every output of level equal or higher to parameter level will be
        printed on console

        :param level: new level for console
        :return: None
        """
        if type(level) is str:
            level = getattr(Log, level)
        Log.console_handler.level = level

    @staticmethod
    def set_file_level(level):
        """
        Sets log level for logging to file. Every output of level equal or higher to parameter level will be
        added to log file

        :param level: new level for log file
        """
        if type(level) is str:
            level = getattr(Log, level)
        Log.file_level = level
        if Log.file_handler is not None:
            Log.file_handler.level = level

    @staticmethod
    def debug(msg, *args):
        """
        Sends debug information to the log

        :param msg: message to show
        :param args: arguments for message formating (it will be done using format() method on str)
        """
        Log.log.debug(msg.format(*args))

    @staticmethod
    def info(msg, *args):
        """
        Sends information to the log

        :param msg: message to show
        :param args: arguments for message formatting (it will be done using format() method on str)
        """
        Log.log.info(msg.format(*args))

    @staticmethod
    def result(msg, *args):
        """
        Sends results information to the log. It will be shown in green in the console.

        :param msg: message to show
        :param args: arguments for message formating (it will be done using format() method on str)
        """
        Log.log.log(Log.RESULT, msg.format(*args))

    @staticmethod
    def user_warning(msg, *args):
        """
        Sends warnings for the user to the log. It will be shown in yellow in the console.

        :param msg: message to show
        :param args: arguments for message formating (it will be done using format() method on str)
        """
        Log.log.log(Log.USER_WARNING, msg.format(*args))

    @staticmethod
    def warning(msg, *args):
        """
        Sends program warnings to the log. It will be shown in yellow in the console.

        :param msg: message to show
        :param args: arguments for message formatting (it will be done using format() method on str)
        """
        Log.log.warning(msg.format(*args))

    @staticmethod
    def error(msg, *args):
        """
        Sends errors to the log. It will be shown in red in the console.

        :param msg: message to show
        :param args: arguments for message formatting (it will be done using format() method on str)
        """
        Log.log.error(msg.format(*args))

    @staticmethod
    def critical(msg, *args):
        """
        Sends critical errors to the log. It will be shown in red in the console.

        :param msg: message to show
        :param args: arguments for message formatting (it will be done using format() method on str)
        """
        Log.log.critical(msg.format(*args))
