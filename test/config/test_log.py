import os
from unittest import TestCase

import shutil

from autosubmit.config.log import LogFormatter, Log
from logging import LogRecord
import tempfile


class TestLogFormatter(TestCase):

    def setUp(self):
        self.file = LogFormatter(True)
        self.console = LogFormatter(False)

    def test_format(self):
        record = LogRecord('record', Log.DEBUG, 'path', 1, 'Message', ['args'], None)
        self.assertEqual(self.file.format(record), record.asctime + ' Message',)
        self.assertEqual('Message', self.console.format(record))

        record = LogRecord('record', Log.INFO, 'path', 1, 'Message', ['args'], None)
        self.assertEqual(self.file.format(record), record.asctime + ' Message',)
        self.assertEqual('Message', self.console.format(record))

        record = LogRecord('record', Log.RESULT, 'path', 1, 'Message', ['args'], None)
        self.assertEqual(self.file.format(record), record.asctime + ' Message',)
        self.assertEqual(LogFormatter.RESULT + 'Message' + LogFormatter.DEFAULT, self.console.format(record))

        record = LogRecord('record', Log.USER_WARNING, 'path', 1, 'Message', ['args'], None)
        self.assertEqual(self.file.format(record), record.asctime + ' Message',)
        self.assertEqual(LogFormatter.WARNING + 'Message' + LogFormatter.DEFAULT, self.console.format(record))

        record = LogRecord('record', Log.WARNING, 'path', 1, 'Message', ['args'], None)
        self.assertEqual(self.file.format(record), '[WARNING] ' + record.asctime + ' Message',)
        self.assertEqual(LogFormatter.WARNING + '[WARNING] Message' + LogFormatter.DEFAULT,
                         self.console.format(record))

        record = LogRecord('record', Log.ERROR, 'path', 1, 'Message', ['args'], None)
        self.assertEqual(self.file.format(record), '[ERROR] ' + record.asctime + ' Message',)
        self.assertEqual(LogFormatter.ERROR + '[ERROR] Message' + LogFormatter.DEFAULT,
                         self.console.format(record))

        record = LogRecord('record', Log.CRITICAL, 'path', 1, 'Message', ['args'], None)
        self.assertEqual(self.file.format(record), '[CRITICAL] ' + record.asctime + ' Message',)
        self.assertEqual(LogFormatter.ERROR + '[CRITICAL] Message' + LogFormatter.DEFAULT,
                         self.console.format(record))


class TestLog(TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_set_file(self):
        Log.set_file(os.path.join(self.tempdir, 'test.log'))

    def test_set_console_level(self):
        Log.set_console_level(Log.NO_LOG)
        Log.set_console_level(Log.EVERYTHING)

    def test_set_file_level(self):
        Log.set_file_level(Log.NO_LOG)
        Log.set_file_level(Log.EVERYTHING)

    def test_debug(self):
        Log.debug('Message')
        Log.debug('{0} {1}', 'complex', 'message')
        with self.assertRaises(IndexError):
            Log.debug('{0} {1}', 'Parameter mising')

    def test_info(self):
        Log.info('Message')
        Log.info('{0} {1}', 'complex', 'message')
        with self.assertRaises(IndexError):
            Log.info('{0} {1}', 'Parameter mising')

    def test_result(self):
        Log.result('Message')
        Log.result('{0} {1}', 'complex', 'message')
        with self.assertRaises(IndexError):
            Log.result('{0} {1}', 'Parameter mising')

    def test_user_warning(self):
        Log.user_warning('Message')
        Log.user_warning('{0} {1}', 'complex', 'message')
        with self.assertRaises(IndexError):
            Log.user_warning('{0} {1}', 'Parameter mising')

    def test_warning(self):
        Log.warning('Message')
        Log.warning('{0} {1}', 'complex', 'message')
        with self.assertRaises(IndexError):
            Log.warning('{0} {1}', 'Parameter mising')

    def test_error(self):
        Log.error('Message')
        Log.error('{0} {1}', 'complex', 'message')
        with self.assertRaises(IndexError):
            Log.error('{0} {1}', 'Parameter mising')

    def test_critical(self):
        Log.critical('Message')
        Log.critical('{0} {1}', 'complex', 'message')
        with self.assertRaises(IndexError):
            Log.critical('{0} {1}', 'Parameter mising')
