"""Actual timeout/exit cleanup, including Linux grandchildren that detach from the session."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import product_process


class ProductProcessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_short_child_credential_refuses_before_launch_or_output(self):
        marker = self.root / 'launched'
        output = self.root / 'evidence' / 'run'
        command = [sys.executable, '-c', 'from pathlib import Path; import sys; Path(sys.argv[1]).touch()', str(marker)]
        with self.assertRaisesRegex(ValueError, 'Structured evidence requires known environment credentials'):
            product_process.run(command, cwd=self.root, output=output, timeout=5,
                                environment={**os.environ, 'PRODUCT_SECRET': 'abc1234'})
        self.assertFalse(marker.exists())
        self.assertFalse(output.parent.exists())

    def test_failure_is_propagated_with_both_sanitized_channels_and_outcome(self):
        output = self.root / 'failure'
        environment = {**os.environ, 'PRODUCT_SECRET': 'owned-process-secret'}
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            product_process.run([sys.executable, '-c', 'import os,sys; print(os.environ["PRODUCT_SECRET"]); print("retained stderr",file=sys.stderr);sys.exit(7)'],
                                cwd=self.root, output=output, timeout=5, environment=environment)
        self.assertEqual(7, caught.exception.returncode)
        self.assertEqual('[REDACTED]\n', output.with_suffix('.stdout.txt').read_text())
        self.assertIn('retained stderr', output.with_suffix('.stderr.txt').read_text())
        receipt = json.loads(output.with_suffix('.command.json').read_text())
        self.assertEqual('complete', receipt['cleanup'])
        self.assertFalse(receipt['timedOut'])
        self.assertEqual(7, receipt['exitCode'])

    def test_timeout_stops_and_reaps_detached_grandchild_while_preserving_foreign_process(self):
        self.assertTrue(sys.platform.startswith('linux'), 'This retained suite runs in the Linux product hook.')
        marker = self.root / 'child.pid'
        child_code = 'import os,signal,time;from pathlib import Path;signal.signal(signal.SIGTERM,signal.SIG_IGN);Path('+repr(str(marker))+').write_text(str(os.getpid()));time.sleep(60)'
        parent_code = 'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",'+repr(child_code)+'],start_new_session=True);print("parent ready",flush=True);time.sleep(60)'
        foreign = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(60)'])
        try:
            output = self.root / 'timeout'
            with self.assertRaises(subprocess.TimeoutExpired):
                product_process.run([sys.executable, '-c', parent_code], cwd=self.root, output=output, timeout=1, grace=.2)
            self.assertTrue(marker.is_file())
            with self.assertRaises(ProcessLookupError): os.kill(int(marker.read_text()), 0)
            self.assertIsNone(foreign.poll())
            receipt = json.loads(output.with_suffix('.command.json').read_text())
            self.assertTrue(receipt['timedOut'])
            self.assertEqual('complete', receipt['cleanup'])
            self.assertIn('parent ready', output.with_suffix('.stdout.txt').read_text())
        finally:
            foreign.kill(); foreign.wait(timeout=5)

    def test_reaped_root_identity_is_not_treated_as_a_live_owned_process(self):
        self.assertTrue(sys.platform.startswith('linux'))
        foreign = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(60)'])
        supervisor = product_process.LinuxTree()
        class Reaped:
            pid = foreign.pid
            returncode = 0
            def poll(self): return 0
            def wait(self, timeout): return 0
        try:
            self.assertNotIn(foreign.pid, supervisor.owned(Reaped()))
            supervisor.close(Reaped(), .1)
            self.assertIsNone(foreign.poll())
        finally:
            foreign.kill(); foreign.wait(timeout=5)

    def test_missing_executable_records_failure_and_restores_supervision_state(self):
        before = None
        if sys.platform.startswith('linux'):
            import ctypes
            before = ctypes.c_int(); product_process.ctypes.CDLL(None).prctl(37, ctypes.byref(before), 0, 0, 0)
        with self.assertRaises(FileNotFoundError):
            product_process.run([str(self.root / 'missing-command')], cwd=self.root, output=self.root / 'missing', timeout=1)
        receipt = json.loads((self.root / 'missing.command.json').read_text())
        self.assertIsNone(receipt['exitCode'])
        self.assertIn('missing-command', receipt['error'])
        if before is not None:
            import ctypes
            after = ctypes.c_int(); product_process.ctypes.CDLL(None).prctl(37, ctypes.byref(after), 0, 0, 0)
            self.assertEqual(before.value, after.value)


if __name__ == '__main__': unittest.main()
