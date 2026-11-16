"""Include the module-owned Node notes tests in ordinary Python discovery."""
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]


def run_notes_tests():
    return subprocess.run(['node','--test','scripts/tests/migration-release-notes.test.mjs'],cwd=ROOT,capture_output=True,text=True)


def main():
    result=run_notes_tests()
    sys.stdout.write(result.stdout);sys.stderr.write(result.stderr)
    return result.returncode


class MigrationReleaseNotesTests(unittest.TestCase):
    def test_pinned_generator_and_status_refusals(self):
        result=run_notes_tests()
        self.assertEqual(result.returncode,0,f'Node exit {result.returncode}\n{result.stdout}{result.stderr}')

    def test_direct_adapter_preserves_exact_failure_code_and_streams(self):
        import contextlib
        import io
        stdout,stderr=io.StringIO(),io.StringIO()
        with mock.patch(__name__+'.run_notes_tests',return_value=subprocess.CompletedProcess([],7,'out\n','err\n')),contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            self.assertEqual(main(),7)
        self.assertEqual((stdout.getvalue(),stderr.getvalue()),('out\n','err\n'))


if __name__=='__main__':sys.exit(main())
