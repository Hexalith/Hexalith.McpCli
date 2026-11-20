"""Product audit policy, transitive/byte coverage and online advisory provenance."""
import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import native_audit


class NativeAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / 'module/host.csproj'
        self.project.parent.mkdir()
        self.project.write_text('<Project/>')
        self.assets = self.project.parent / 'obj/project.assets.json'
        self.assets.parent.mkdir()
        self.output = self.project.parent / 'bin/Release/net11.0/host.dll'
        self.output.parent.mkdir(parents=True)
        self.output.write_bytes(b'already built production host')
        self.document = {'libraries': {}, 'packageFolders': {str(self.root / 'packages'): {}},
                         'project': {'restore': {'restoreAuditProperties': {'enableAudit': 'true', 'auditLevel': 'low', 'auditMode': 'all'},
                                                'warningProperties': {'allWarningsAsErrors': True}},
                                     'frameworks': {'net11.0': {}}}}
        for name in ('Direct', 'Transitive'):
            identity = name + '/1.0.0'
            folder = self.root / 'packages' / identity.lower()
            folder.mkdir(parents=True)
            data = ('public archive ' + name).encode()
            (folder / (name.lower() + '.1.0.0.nupkg')).write_bytes(data)
            self.document['libraries'][identity] = {'type': 'package', 'sha512': base64.b64encode(hashlib.sha512(data).digest()).decode()}
        self.assets.write_text(json.dumps(self.document))

    def test_complete_transitive_graph_and_actual_archive_bytes_are_bound(self):
        graph = native_audit.package_graph(self.assets)
        self.assertEqual({'Direct/1.0.0', 'Transitive/1.0.0'}, set(graph))
        for defect in ('missing', 'changed-content', 'changed-archive'):
            actual = json.loads(json.dumps(graph))
            if defect == 'missing': del actual['Transitive/1.0.0']
            else: actual['Transitive/1.0.0']['contentSha512' if defect == 'changed-content' else 'archiveSha512'] = 'changed'
            with self.subTest(defect=defect), self.assertRaisesRegex(ValueError, 'coverage'):
                native_audit.require_coverage(graph, actual)

    def test_missing_hash_or_archive_is_not_accepted(self):
        self.document['libraries']['Transitive/1.0.0'].pop('sha512')
        self.assets.write_text(json.dumps(self.document))
        with self.assertRaisesRegex(ValueError, 'content hash'):
            native_audit.package_graph(self.assets)
        self.document['libraries']['Transitive/1.0.0']['sha512'] = base64.b64encode(b'x' * 64).decode()
        self.assets.write_text(json.dumps(self.document))
        (self.root / 'packages/transitive/1.0.0/transitive.1.0.0.nupkg').unlink()
        with self.assertRaisesRegex(ValueError, 'archive'):
            native_audit.package_graph(self.assets)

    def test_audit_policy_refuses_feed_failure_suppressions_and_weakened_severity(self):
        for defect in ('disabled', 'direct', 'moderate', 'no-warnings-as-errors', 'feed-outage',
                       'advisory-suppression', 'no-warn', 'warn-not-error', 'package-no-warn'):
            value = json.loads(json.dumps(self.document))
            restore = value['project']['restore']
            if defect == 'disabled': restore['restoreAuditProperties']['enableAudit'] = 'false'
            if defect == 'direct': restore['restoreAuditProperties']['auditMode'] = 'direct'
            if defect == 'moderate': restore['restoreAuditProperties']['auditLevel'] = 'moderate'
            if defect == 'no-warnings-as-errors': restore['warningProperties']['allWarningsAsErrors'] = False
            if defect == 'feed-outage': value['logs'] = [{'code': 'NU1900', 'level': 'Warning'}]
            if defect == 'advisory-suppression': restore['restoreAuditProperties']['suppressedAdvisories'] = {'https://advisory': None}
            if defect == 'no-warn': restore['warningProperties']['noWarn'] = ['NU1901']
            if defect == 'warn-not-error': restore['warningProperties']['warnNotAsError'] = ['NU1902']
            if defect == 'package-no-warn': value['project']['frameworks']['net11.0']['dependencies'] = {'Direct': {'noWarn': ['NU1903']}}
            self.assets.write_text(json.dumps(value))
            with self.subTest(defect=defect), self.assertRaisesRegex(ValueError, 'low-and-higher'):
                native_audit.require_policy(self.assets)

    def advisory_fixture(self):
        cache = self.root / 'cache'
        cache.mkdir()
        pages = [{'@name': name, '@id': 'https://api.nuget.org/v3-vulnerabilities/revision/' + name + '.json',
                  '@updated': '2026-11-16T00:00:00Z'} for name in ('base', 'update')]
        (cache / 'vuln_index.dat').write_text(json.dumps(pages))
        for name in ('base', 'update'):
            (cache / ('vuln_data_' + name + '.dat')).write_text('{}')
        return cache

    def test_every_advisory_page_must_match_independent_online_200_response(self):
        cache = self.advisory_fixture()
        def fetch(command, *_args, **_kwargs):
            name = Path(command[-1]).stem
            cached = cache / ('vuln_index.dat' if name == 'index' else 'vuln_data_' + name + '.dat')
            Path(command[-1]).write_bytes(cached.read_bytes())
            Path(command[command.index('--dump-header') + 1]).write_text('HTTP/2 200\n')
        receipt = native_audit.online_advisories(cache, self.root / 'proof', fetch)
        self.assertEqual({'index', 'base', 'update'}, set(receipt['pages']))
        for defect in ('outage', 'stale-index', 'stale-page', 'cache-only', 'missing-page'):
            def defective(command, *_args, **_kwargs):
                if defect == 'outage': raise RuntimeError('offline')
                fetch(command)
                path = Path(command[-1])
                if defect == 'stale-index' and path.stem == 'index': path.write_text('[]')
                if defect == 'stale-page' and path.stem == 'update': path.write_text('{"changed": []}')
                if defect == 'cache-only': Path(command[command.index('--dump-header') + 1]).write_text('HTTP/2 304\n')
                if defect == 'missing-page' and path.stem == 'base': (cache / 'vuln_data_base.dat').unlink()
            with self.subTest(defect=defect), self.assertRaises((RuntimeError, ValueError)):
                native_audit.online_advisories(cache, self.root / defect, defective)

    def test_transient_online_mismatch_is_retried_then_accepted(self):
        cache = self.advisory_fixture()
        attempts = {'index': 0}

        def fetch(command, *_args, **_kwargs):
            name = Path(command[-1]).stem
            cached = cache / ('vuln_index.dat' if name == 'index' else 'vuln_data_' + name + '.dat')
            Path(command[command.index('--dump-header') + 1]).write_text('HTTP/2 200\n')
            destination = Path(command[-1])
            if name == 'index':
                attempts['index'] += 1
                if attempts['index'] == 1:
                    destination.write_text('[]')
                    return
            destination.write_bytes(cached.read_bytes())

        receipt = native_audit.online_advisories(cache, self.root / 'retried', fetch)
        self.assertEqual(2, attempts['index'])
        self.assertEqual(hashlib.sha256((cache / 'vuln_index.dat').read_bytes()).hexdigest(),
                         receipt['pages']['index']['sha256'])

    def test_equivalent_advisory_json_is_accepted(self):
        cache = self.advisory_fixture()
        pages = json.loads((cache / 'vuln_index.dat').read_text())

        def fetch(command, *_args, **_kwargs):
            name = Path(command[-1]).stem
            Path(command[command.index('--dump-header') + 1]).write_text('HTTP/2 200\n')
            destination = Path(command[-1])
            if name == 'index':
                destination.write_text(json.dumps(pages, indent=2))
            else:
                destination.write_bytes((cache / ('vuln_data_' + name + '.dat')).read_bytes())

        receipt = native_audit.online_advisories(cache, self.root / 'pretty', fetch)
        self.assertEqual(hashlib.sha256(json.dumps(pages, indent=2).encode()).hexdigest(),
                         receipt['pages']['index']['sha256'])

    def test_proven_advisory_snapshot_skips_live_fetch_and_refuses_drift(self):
        cache = self.advisory_fixture()

        def fetch(command, *_args, **_kwargs):
            name = Path(command[-1]).stem
            cached = cache / ('vuln_index.dat' if name == 'index' else 'vuln_data_' + name + '.dat')
            Path(command[-1]).write_bytes(cached.read_bytes())
            Path(command[command.index('--dump-header') + 1]).write_text('HTTP/2 200\n')

        proven = self.root / 'proven'
        native_audit.online_advisories(cache, proven, fetch)

        def forbidden(*_args, **_kwargs):
            raise AssertionError('already-proven advisory pages must not be fetched again')

        receipt = native_audit.online_advisories(cache, self.root / 'reused', forbidden, proven=proven)
        self.assertEqual(hashlib.sha256((proven / 'index.json').read_bytes()).hexdigest(),
                         receipt['pages']['index']['sha256'])
        (cache / 'vuln_data_update.dat').write_text('{"changed": []}')
        with self.assertRaisesRegex(ValueError, 'cache='):
            native_audit.online_advisories(cache, self.root / 'drifted', forbidden, proven=proven)

    def test_reuse_rechecks_module_outputs_fixture_graph_and_advisory_bytes(self):
        private = self.root / 'audited'
        (private / 'obj').mkdir(parents=True)
        (private / 'audit.csproj').write_text('<Project/>')
        audited = private / 'obj/project.assets.json'
        audited.write_bytes(self.assets.read_bytes())
        advisories = private / 'advisories'
        advisories.mkdir()
        page = advisories / 'index.json'
        page.write_text('[]')
        digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        receipt = {'privateDirectory': str(private), 'sourceOutputs': native_audit.output_snapshot(self.project),
                   'sourceAssetsSha256': digest(self.assets), 'packages': native_audit.package_graph(self.assets),
                   'fixtureSha256': digest(private / 'audit.csproj'), 'auditAssetsSha256': digest(audited),
                   'policy': native_audit.require_policy(audited), 'auditedPackages': native_audit.package_graph(audited),
                   'advisories': {'pages': {'index': {'sha256': digest(page)}}}}
        native_audit.require_audit(receipt, self.project)
        for path in (self.output, audited, page, private / 'audit.csproj'):
            original = path.read_bytes()
            path.write_bytes(original + b' ')
            with self.subTest(path=path.name), self.assertRaises(ValueError):
                native_audit.require_audit(receipt, self.project)
            path.write_bytes(original)

    def test_output_snapshot_includes_existing_build_and_assets(self):
        before = native_audit.output_snapshot(self.project)
        self.assertEqual({'obj/project.assets.json', 'bin/Release/net11.0/host.dll'}, set(before))
        self.output.write_bytes(b'changed')
        self.assertNotEqual(before, native_audit.output_snapshot(self.project))


if __name__ == '__main__':
    unittest.main()
