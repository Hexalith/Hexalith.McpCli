"""Require signatures before either historical caller accepts a public download."""

import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile


SCRIPTS = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('recover_bootstrap', SCRIPTS / 'recover-bootstrap-release.py')
RECOVERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECOVERY)


class PublicPackageSignatureTests(unittest.TestCase):
    def test_public_download_refuses_unsigned_and_malformed_signatures(self):
        class Response(io.BytesIO):
            status = 200

        for signature in (None, b'invalid signature'):
            with self.subTest(signature=signature), tempfile.TemporaryDirectory() as directory:
                body = io.BytesIO()
                with ZipFile(body, 'w') as archive:
                    archive.writestr('library.txt', 'test package contents')
                    if signature is not None:
                        archive.writestr('.signature.p7s', signature)

                for pushed in (False, True):
                    with self.subTest(pushed=pushed):
                        downloaded = Path(directory) / 'example.nupkg'
                        with patch.object(RECOVERY, 'urlopen', return_value=Response(body.getvalue())) as download:
                            with self.assertRaisesRegex(ValueError, 'signature verification failed.*CalledProcessError'):
                                RECOVERY.download_public_package('https://example.test/package', downloaded, pushed)
                        download.assert_called_once_with('https://example.test/package', timeout=30)

    def test_signature_check_runs_once_and_times_out_closed(self):
        package = Path('example.nupkg').resolve()
        command = ['dotnet', 'nuget', 'verify', '--all', str(package)]
        with patch.object(RECOVERY.subprocess, 'run', side_effect=subprocess.TimeoutExpired(command, 120)) as verify:
            with self.assertRaisesRegex(ValueError, 'signature verification failed.*TimeoutExpired'):
                RECOVERY.verify_public_signature(package)
        verify.assert_called_once_with(command, check=True, capture_output=True, timeout=120)
