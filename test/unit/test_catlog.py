from unittest import TestCase

import io
import sys
from contextlib import suppress, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from autosubmit.autosubmit import Autosubmit, AutosubmitCritical
from autosubmitconfigparser.config.basicconfig import BasicConfig


class TestJob(TestCase):

    def setUp(self):
        self.autosubmit = Autosubmit()
        # directories used when searching for logs to cat
        self.original_root_dir = BasicConfig.LOCAL_ROOT_DIR
        self.root_dir = TemporaryDirectory()
        BasicConfig.LOCAL_ROOT_DIR = self.root_dir.name
        self.exp_path = Path(self.root_dir.name, 'a000')
        self.tmp_dir = self.exp_path / BasicConfig.LOCAL_TMP_DIR
        self.aslogs_dir = self.tmp_dir / BasicConfig.LOCAL_ASLOG_DIR
        self.status_path = self.exp_path / 'status'
        self.aslogs_dir.mkdir(parents=True)
        self.status_path.mkdir()

    def tearDown(self) -> None:
        BasicConfig.LOCAL_ROOT_DIR = self.original_root_dir
        if self.root_dir is not None:
            self.root_dir.cleanup()

    def test_invalid_file(self):
        def _fn():
            self.autosubmit.cat_log(None, '8', None)  # type: ignore
        self.assertRaises(AutosubmitCritical, _fn)

    def test_invalid_mode(self):
        def _fn():
            self.autosubmit.cat_log(None, 'o', '8')  # type: ignore
        self.assertRaises(AutosubmitCritical, _fn)

    # -- workflow

    def test_is_workflow_invalid_file(self):
        def _fn():
            self.autosubmit.cat_log('a000', 'j', None)
        self.assertRaises(AutosubmitCritical, _fn)

    @patch('autosubmit.autosubmit.Log')
    def test_is_workflow_not_found(self, Log):
        self.autosubmit.cat_log('a000', 'o', 'c')
        assert Log.info.called
        assert Log.info.call_args[0][0] == 'No logs found.'

    def test_is_workflow_log_is_dir(self):
        log_file_actually_dir = Path(self.aslogs_dir, 'log_run.log')
        log_file_actually_dir.mkdir()
        def _fn():
            self.autosubmit.cat_log('a000', 'o', 'c')
        self.assertRaises(AutosubmitCritical, _fn)

    @patch('subprocess.Popen')
    def test_is_workflow_out_cat(self, popen):
        log_file = Path(self.aslogs_dir, 'log_run.log')
        with open(log_file, 'w') as f:
            f.write('as test')
            f.flush()
            self.autosubmit.cat_log('a000', file=None, mode='c')
            assert popen.called
            args = popen.call_args[0][0]
            assert args[0] == 'cat'
            assert args[1] == str(log_file)

    @patch('subprocess.Popen')
    def test_is_workflow_status_tail(self, popen):
        log_file = Path(self.status_path, 'a000_anything.txt')
        with open(log_file, 'w') as f:
            f.write('as test')
            f.flush()
            self.autosubmit.cat_log('a000', file='s', mode='t')
            assert popen.called
            args = popen.call_args[0][0]
            assert args[0] == 'tail'
            assert str(args[-1]) == str(log_file)

    # --- jobs

    @patch('autosubmit.autosubmit.Log')
    def test_is_jobs_not_found(self, Log):
        for file in ['j', 's', 'o']:
            self.autosubmit.cat_log('a000_INI', file=file, mode='c')
            assert Log.info.called
            assert Log.info.call_args[0][0] == 'No logs found.'

    def test_is_jobs_log_is_dir(self):
        log_file_actually_dir = Path(self.tmp_dir, 'LOG_a000/a000_INI.20000101.out')
        log_file_actually_dir.mkdir(parents=True)
        def _fn():
            self.autosubmit.cat_log('a000_INI', 'o', 'c')
        self.assertRaises(AutosubmitCritical, _fn)

    @patch('subprocess.Popen')
    def test_is_jobs_out_tail(self, popen):
        log_dir = self.tmp_dir / 'LOG_a000'
        log_dir.mkdir()
        log_file = log_dir / 'a000_INI.20200101.out'
        with open(log_file, 'w') as f:
            f.write('as test')
            f.flush()
            self.autosubmit.cat_log('a000_INI', file=None, mode='t')
            assert popen.called
            args = popen.call_args[0][0]
            assert args[0] == 'tail'
            assert str(args[-1]) == str(log_file)

    # --- command-line

    def test_command_line_help(self):
        args = ['autosubmit', 'cat-log', '--help']
        with patch.object(sys, 'argv', args) as _, io.StringIO() as buf, redirect_stdout(buf):
            with suppress(SystemExit):
                assert Autosubmit.parse_args()
            assert buf
            assert 'View workflow and job logs.' in buf.getvalue()
