"""Finite current runtime identity, binary and mutation-sensitive profile checks."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import ci


class CurrentRuntimeProfileTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.tools = self.root / 'tools/live-topology'
        self.tools.mkdir(parents=True)
        self.profile = json.loads((ci.ROOT / 'tools/live-topology/runtime-profile-current.json').read_text())
        self.binaries = self.tools / 'binaries-current.json'
        self.binaries.write_text('[]\n')
        self.profile['binaries']['sha256'] = hashlib.sha256(self.binaries.read_bytes()).hexdigest()
        self.path = self.tools / 'runtime-profile-current.json'
        self.path.write_text(json.dumps(self.profile))

    def load(self):
        with patch.object(ci, 'ROOT', self.root): return ci.current_runtime_profile()

    def test_exact_current_tuple_and_binary_manifest_are_required(self):
        self.assertEqual(self.profile, self.load())
        for change in ['version', 'archive', 'manifest', 'unknown-tool', 'managed-runtime', 'product-retarget']:
            value = copy.deepcopy(self.profile)
            if change == 'version': value['tools']['dapr']['version'] = '1.20.0'
            if change == 'archive': value['tools']['aspire']['archiveSha256'] = 'a' * 64
            if change == 'manifest': value['binaries']['sha256'] = 'a' * 64
            if change == 'managed-runtime': value['managedTestHosts']['runtime'] = '10.0.15'
            if change == 'product-retarget': value['managedTestHosts']['projects'].append('Hexalith.Tenants')
            if change == 'unknown-tool': value['tools']['additional'] = value['tools']['dapr']
            self.path.write_text(json.dumps(value))
            with self.subTest(change=change), self.assertRaises(ValueError): self.load()

    def test_forged_version_string_cannot_admit_altered_tool_bytes(self):
        paths = {}
        for name, data in [('aspire', b'current aspire fixture'), ('dapr', b'current cli fixture'), ('daprd', b'current runtime fixture')]:
            path = self.root / name
            path.write_bytes(data)
            paths[name] = path
            self.profile['tools'][name]['binarySha256'] = hashlib.sha256(data).hexdigest()
        ci.verify_current_tool_bytes(self.profile, paths)
        for name, path in paths.items():
            original = path.read_bytes()
            try:
                path.write_bytes(original + b'changed despite matching --version')
                with self.subTest(tool=name), self.assertRaisesRegex(ValueError, 'executable hash mismatch: ' + name):
                    ci.verify_current_tool_bytes(self.profile, paths)
            finally: path.write_bytes(original)
        with self.assertRaisesRegex(ValueError, 'complete exact current executable set'):
            ci.verify_current_tool_bytes(self.profile, {'dapr': paths['dapr']})

    def test_current_resource_rollforward_is_closed_to_measured_runtime(self):
        output = 'Microsoft.NETCore.App 10.0.15 [/trusted/core]\nMicrosoft.NETCore.App 11.0.0 [/trusted/core]\nMicrosoft.AspNetCore.App 11.0.0 [/trusted/aspnet]\n'
        self.assertEqual({'Microsoft.AspNetCore.App': '11.0.0', 'Microsoft.NETCore.App': '11.0.0'},
                         ci.current_managed_runtime_selection(output))
        for changed in [output.replace('11.0.0', '11.0.1'), output.replace('11.0.0', '12.0.0'),
                        output.replace('11.0.0', '12.0.0-preview.1'), output.split('Microsoft.AspNetCore.App')[0]]:
            with self.subTest(output=changed), self.assertRaises(ValueError): ci.current_managed_runtime_selection(changed)

    def test_original_runtime_binary_profile_remains_immutable(self):
        root = Path(__file__).resolve().parents[2]
        authority = json.loads((root / 'evidence/release-maintenance-20261112/current-cohort/authorization.json').read_text())
        expected = authority['historicalInputs']['tools/live-topology/binaries.json']
        self.assertEqual(expected, hashlib.sha256((root / 'tools/live-topology/binaries.json').read_bytes()).hexdigest())


if __name__ == '__main__': unittest.main()
