from collections import namedtuple
from unittest import TestCase

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

from autosubmit.platforms.slurmplatform import SlurmPlatform
from log.log import AutosubmitCritical, AutosubmitError


class TestSlurmPlatform(TestCase):

    Config = namedtuple('Config', ['LOCAL_ROOT_DIR', 'LOCAL_TMP_DIR', 'LOCAL_ASLOG_DIR'])

    def setUp(self):
        self.local_root_dir = TemporaryDirectory()
        self.config = TestSlurmPlatform.Config(
            LOCAL_ROOT_DIR=self.local_root_dir.name,
            LOCAL_TMP_DIR='tmp',
            LOCAL_ASLOG_DIR='ASLOG_a000'
        )
        # We need to create the submission archive that AS expects to find in this location:
        p = Path(self.local_root_dir.name) / 'a000' / 'tmp' / 'ASLOG_a000'
        p.mkdir(parents=True)
        submit_platform_script = Path(p) / 'submit_local.sh'
        submit_platform_script.touch(exist_ok=True)

        self.platform = SlurmPlatform(expid='a000', name='local', config=self.config)

    def tearDown(self) -> None:
        self.local_root_dir.cleanup()

    def test_slurm_platform_submit_script_raises_autosubmit_critical_with_trace(self):
        package = MagicMock()
        package.jobs.return_value = []
        valid_packages_to_submit = [
            package
        ]

        ae = AutosubmitError(message='invalid partition', code=123, trace='ERR!')
        self.platform.submit_Script = MagicMock(side_effect=ae)

        # AS will handle the AutosubmitError above, but then raise an AutosubmitCritical.
        # This new error won't contain all the info from the upstream error.
        with self.assertRaises(AutosubmitCritical) as cm:
            self.platform.process_batch_ready_jobs(
                valid_packages_to_submit=valid_packages_to_submit,
                failed_packages=[]
            )

        # AS will handle the error and then later will raise another error message.
        # But the AutosubmitError object we created will have been correctly used
        # without raising any exceptions (such as AttributeError).
        assert cm.exception.message != ae.message
