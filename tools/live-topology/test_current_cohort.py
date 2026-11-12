"""Current routing is a bounded compatibility-selector update; historical evidence stays immutable."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import native_cohort

ROOT = Path(__file__).resolve().parents[2]


class CurrentCohortTests(unittest.TestCase):
    def test_historical_native_selection_and_all_vectors_and_plans_are_preserved(self):
        authority = json.loads((ROOT / 'evidence/release-maintenance-20261112/current-cohort/authorization.json').read_text())
        for relative, digest in authority['historicalInputs'].items():
            with self.subTest(path=relative):
                self.assertEqual(digest, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())
        self.assertEqual(authority['historicalNativeRuntimeSha256'], hashlib.sha256(
            (ROOT / 'tools/live-topology/native-runtime.json').read_bytes()).hexdigest())
        self.assertIs(False, authority['runtimeAcceptance'])

    def test_current_vectors_only_change_package_versions_and_exact_deprecated_party_hints(self):
        legacy = ROOT / 'tools/conformance-vectors/v1/modules'
        current = ROOT / 'tools/conformance-vectors/v1/current/modules'
        self.assertEqual({p.relative_to(legacy) for p in legacy.rglob('*.vector.json')},
                         {p.relative_to(current) for p in current.rglob('*.vector.json')})
        changes = []
        def transform(value, package):
            if isinstance(value, dict):
                if value.get('id') == package and 'version' in value:
                    value['version'] = {'Hexalith.Parties.Contracts': '3.1.1', 'Hexalith.Tenants.Contracts': '7.0.7'}[package]
                if 'projectionActorType' in value and package == 'Hexalith.Parties.Contracts':
                    self.assertIn(value['projectionActorType'], ('PartyDetailProjectionQueryActor', 'PartyIndexProjectionQueryActor'))
                    self.assertEqual('party', value['domain'])
                    self.assertIn(value['projectionType'], ('party-detail', 'party-index'))
                    changes.append(value.pop('projectionActorType'))
                for child in value.values(): transform(child, package)
            elif isinstance(value, list):
                for child in value: transform(child, package)
        for path in legacy.rglob('*.vector.json'):
            with self.subTest(vector=path.name):
                expected = json.loads(path.read_bytes())
                transform(expected, expected['package']['id'])
                self.assertEqual(expected, json.loads((current / path.relative_to(legacy)).read_bytes()))
        self.assertTrue(changes)

    def test_manifest_accepts_each_closed_cohort_and_refuses_crossed_or_unknown_versions(self):
        old = native_cohort.manifest(ROOT / 'tools/live-topology/native-runtime.json')
        current = native_cohort.manifest(ROOT / 'tools/live-topology/native-runtime-current.json')
        self.assertEqual('4.1.0', old['eventStoreVersion'])
        self.assertEqual('4.2.0', current['eventStoreVersion'])
        for version, replace_packages in [('4.1.0', False), ('4.3.0', False), ('4.2.0-local', False), ('4.3.0', True)]:
            crossed = copy.deepcopy(current)
            crossed['eventStoreVersion'] = version
            if replace_packages:
                for package in crossed['packages']:
                    if package['id'].startswith('Hexalith.EventStore.'):
                        package['version'] = version
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'selection.json'
                path.write_text(json.dumps(crossed))
                with self.assertRaises(ValueError): native_cohort.manifest(path)


if __name__ == '__main__':
    unittest.main()
