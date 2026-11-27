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

    def advisory_fixture(self, name='cache', revision='revision', updated='2026-11-16T00:00:00Z',
                         base_doc=None, update_doc=None):
        cache = self.root / name
        cache.mkdir(parents=True, exist_ok=True)
        pages = [{'@name': page_name,
                  '@id': f'https://data.nuget.org/v3-vulnerabilities/{revision}/{page_name}.json',
                  '@updated': updated} for page_name in ('base', 'update')]
        (cache / 'vuln_index.dat').write_text(json.dumps(pages))
        (cache / 'vuln_data_base.dat').write_text(json.dumps({} if base_doc is None else base_doc))
        (cache / 'vuln_data_update.dat').write_text(json.dumps({} if update_doc is None else update_doc))
        return cache

    def make_live_fetcher(self, index_pages, page_docs, *, status_map=None, headers_map=None,
                          curl_error_pages=None, raw_overrides=None, call_counts=None):
        status_map = status_map or {}
        headers_map = headers_map or {}
        curl_error_pages = set(curl_error_pages or ())
        raw_overrides = raw_overrides or {}

        def fetch(command, *_args, **_kwargs):
            name = Path(command[-1]).stem
            if call_counts is not None:
                call_counts[name] = call_counts.get(name, 0) + 1
            headers_path = Path(command[command.index('--dump-header') + 1])
            destination = Path(command[-1])
            status = status_map.get(name, 200)
            extra = headers_map.get(name, 'ETag: "etag-' + name + '"\r\nDate: Fri, 27 Nov 2026 17:00:00 GMT\r\n')
            headers_path.write_text(f'HTTP/2 {status}\r\n{extra}\r\n')
            if name in curl_error_pages:
                raise RuntimeError(f'curl exited 22 for {name} (HTTP {status})')
            if name in raw_overrides:
                raw = raw_overrides[name]
                if isinstance(raw, bytes):
                    destination.write_bytes(raw)
                else:
                    destination.write_text(raw)
            elif name == 'index':
                destination.write_text(json.dumps(index_pages))
            else:
                destination.write_text(json.dumps(page_docs[name]))
        return fetch

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
                       'advisory-suppression', 'no-warn', 'warn-not-error', 'package-no-warn',
                       'nu1901', 'nu1902', 'nu1903', 'nu1904'):
            value = json.loads(json.dumps(self.document))
            restore = value['project']['restore']
            if defect == 'disabled': restore['restoreAuditProperties']['enableAudit'] = 'false'
            if defect == 'direct': restore['restoreAuditProperties']['auditMode'] = 'direct'
            if defect == 'moderate': restore['restoreAuditProperties']['auditLevel'] = 'moderate'
            if defect == 'no-warnings-as-errors': restore['warningProperties']['allWarningsAsErrors'] = False
            if defect == 'feed-outage': value['logs'] = [{'code': 'NU1900', 'level': 'Warning', 'message': 'Unable to load audit source'}]
            if defect == 'advisory-suppression': restore['restoreAuditProperties']['suppressedAdvisories'] = {'https://advisory': None}
            if defect == 'no-warn': restore['warningProperties']['noWarn'] = ['NU1901']
            if defect == 'warn-not-error': restore['warningProperties']['warnNotAsError'] = ['NU1902']
            if defect == 'package-no-warn': value['project']['frameworks']['net11.0']['dependencies'] = {'Direct': {'noWarn': ['NU1903']}}
            if defect in ('nu1901', 'nu1902', 'nu1903', 'nu1904'):
                value['logs'] = [{'code': defect.upper(), 'level': 'Warning', 'libraryId': 'Direct',
                                  'message': f"Package 'Direct' 1.0.0 has a known vulnerability ({defect.upper()})"}]
            self.assets.write_text(json.dumps(value))
            diag_path = self.root / f'policy-diag-{defect}.json'
            with self.subTest(defect=defect), self.assertRaisesRegex(ValueError, 'low-and-higher') as ctx:
                native_audit.require_policy(self.assets, diagnostic_path=diag_path)
            self.assertTrue(diag_path.is_file())
            diag = json.loads(diag_path.read_text())
            if defect == 'feed-outage':
                self.assertEqual(native_audit.CLASSIFICATION_UNAVAILABLE, diag['classification'])
                self.assertIn('unavailable', str(ctx.exception))
            elif defect in ('nu1901', 'nu1902', 'nu1903', 'nu1904'):
                self.assertEqual(native_audit.CLASSIFICATION_ADVISORY_AFFECTING_GRAPH, diag['classification'])
                self.assertIn('advisory_affecting_graph', str(ctx.exception))
                self.assertIn(defect.upper(), str(ctx.exception))
                self.assertEqual(['direct'], [item['packageId'] for item in diag['semanticDiff']['restoredPackageIntersection']])

    def test_every_advisory_page_must_match_independent_online_200_response(self):
        cache = self.advisory_fixture()

        def fetch(command, *_args, **_kwargs):
            name = Path(command[-1]).stem
            cached = cache / ('vuln_index.dat' if name == 'index' else 'vuln_data_' + name + '.dat')
            Path(command[-1]).write_bytes(cached.read_bytes())
            Path(command[command.index('--dump-header') + 1]).write_text('HTTP/2 200\nETag: "v1"\n')

        diag_path = self.root / 'stable-diag.json'
        receipt = native_audit.online_advisories(
            cache, self.root / 'proof', fetch,
            restored_packages={'Direct/1.0.0', 'Transitive/1.0.0'},
            diagnostic_path=diag_path,
        )
        self.assertEqual(native_audit.CLASSIFICATION_MATCH, receipt['classification'])
        self.assertEqual(0, receipt['recoveryAttempt'])
        self.assertEqual({'index', 'base', 'update'}, set(receipt['pages']))
        self.assertEqual('https://data.nuget.org/v3/vulnerabilities/index.json', receipt['pages']['index']['url'])
        self.assertEqual('https://data.nuget.org/v3-vulnerabilities/revision/update.json', receipt['pages']['update']['url'])
        self.assertEqual({'etag': '"v1"'}, receipt['pages']['update']['headers'])
        self.assertIsNotNone(receipt['cacheRetrievedAtUtc'])
        self.assertIsNotNone(receipt['onlineRetrievedAtUtc'])
        diag = json.loads(diag_path.read_text())
        self.assertEqual(native_audit.CLASSIFICATION_MATCH, diag['classification'])
        self.assertEqual(2, diag['semanticDiff']['restoredPackageCount'])
        self.assertEqual([], diag['semanticDiff']['restoredPackageIntersection'])

        for defect, expected_cls in (
            ('outage', native_audit.CLASSIFICATION_UNAVAILABLE),
            ('stale-index', native_audit.CLASSIFICATION_UNAVAILABLE),
            ('stale-page', native_audit.CLASSIFICATION_PERSISTENT_MISMATCH),
            ('cache-only', native_audit.CLASSIFICATION_UNAVAILABLE),
            ('missing-page', native_audit.CLASSIFICATION_PERSISTENT_MISMATCH),
        ):
            defective_cache = self.advisory_fixture(name='cache-' + defect)
            calls = []

            def defective(command, *_args, **_kwargs):
                calls.append(Path(command[-1]).stem)
                if defect == 'outage':
                    raise RuntimeError('offline')
                name = Path(command[-1]).stem
                cached = defective_cache / ('vuln_index.dat' if name == 'index' else 'vuln_data_' + name + '.dat')
                Path(command[-1]).write_bytes(cached.read_bytes())
                Path(command[command.index('--dump-header') + 1]).write_text('HTTP/2 200\n')
                path = Path(command[-1])
                if defect == 'stale-index' and path.stem == 'index':
                    path.write_text('[]')
                if defect == 'stale-page' and path.stem == 'update':
                    path.write_text('{"changed": []}')
                if defect == 'cache-only':
                    Path(command[command.index('--dump-header') + 1]).write_text('HTTP/2 304\n')
                if defect == 'missing-page' and path.stem == 'base':
                    (defective_cache / 'vuln_data_base.dat').unlink()

            defect_diag = self.root / f'diag-{defect}.json'
            with self.subTest(defect=defect), self.assertRaises((RuntimeError, ValueError)) as ctx:
                native_audit.online_advisories(defective_cache, self.root / defect, defective, diagnostic_path=defect_diag)
            self.assertIn(expected_cls, str(ctx.exception))
            self.assertTrue(defect_diag.is_file())
            self.assertEqual(expected_cls, json.loads(defect_diag.read_text())['classification'])
            self.assertEqual(len(calls), len(set(calls)), 'must not retry fetches against an unchanged cache')

    def test_rejects_advisory_pages_outside_the_configured_audit_source(self):
        cache = self.advisory_fixture()
        index = cache / 'vuln_index.dat'
        index.write_text(index.read_text().replace('data.nuget.org', 'api.nuget.org'))
        diag_path = self.root / 'foreign-cached-diag.json'
        with self.assertRaisesRegex(ValueError, 'not bound to its official source') as ctx:
            native_audit.online_advisories(cache, self.root / 'foreign', lambda *_: self.fail('unexpected fetch'),
                                           diagnostic_path=diag_path)
        self.assertEqual(native_audit.CLASSIFICATION_UNAVAILABLE, ctx.exception.classification)
        self.assertEqual(native_audit.CLASSIFICATION_UNAVAILABLE, json.loads(diag_path.read_text())['classification'])

        # Also test foreign / traversal / query URLs returned by live index.
        valid_cache = self.advisory_fixture(name='valid-cache-live-foreign')
        for label, bad_url in (
            ('foreign-host', 'https://evil.example/v3-vulnerabilities/rev/base.json'),
            ('api-host', 'https://api.nuget.org/v3-vulnerabilities/rev/base.json'),
            ('traversal', 'https://data.nuget.org/v3-vulnerabilities/../secret/base.json'),
            ('query', 'https://data.nuget.org/v3-vulnerabilities/rev/base.json?x=1'),
            ('http-scheme', 'http://data.nuget.org/v3-vulnerabilities/rev/base.json'),
        ):
            live_pages = [
                {'@name': 'base', '@id': bad_url, '@updated': '2026-11-17T00:00:00Z'},
                {'@name': 'update', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev/update.json', '@updated': '2026-11-17T00:00:00Z'},
            ]
            counts = {}
            fetcher = self.make_live_fetcher(live_pages, {'base': {}, 'update': {}}, call_counts=counts)
            diag = self.root / f'live-bad-url-{label}.json'
            with self.subTest(label=label), self.assertRaises(native_audit.AdvisoryVerificationError) as ctx:
                native_audit.online_advisories(valid_cache, self.root / ('out-' + label), fetcher, diagnostic_path=diag)
            self.assertEqual(native_audit.CLASSIFICATION_UNAVAILABLE, ctx.exception.classification)
            self.assertEqual({'index': 1}, counts)
            self.assertEqual(native_audit.CLASSIFICATION_UNAVAILABLE, json.loads(diag.read_text())['classification'])

    def test_single_fetch_without_cache_reusing_retries_refuses_invalid_live_index(self):
        cache = self.advisory_fixture()
        counts = {}
        fetcher = self.make_live_fetcher([], {}, call_counts=counts)
        diag_path = self.root / 'no-retry-diag.json'
        with self.assertRaises(native_audit.AdvisoryVerificationError) as ctx:
            native_audit.online_advisories(cache, self.root / 'no-retry', fetcher, diagnostic_path=diag_path)
        self.assertEqual({'index': 1}, counts)
        self.assertEqual(native_audit.CLASSIFICATION_UNAVAILABLE, ctx.exception.classification)
        self.assertEqual(native_audit.CLASSIFICATION_UNAVAILABLE, json.loads(diag_path.read_text())['classification'])

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
        self.assertEqual(native_audit.CLASSIFICATION_MATCH, receipt['classification'])
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
        self.assertEqual(native_audit.CLASSIFICATION_MATCH, receipt['classification'])
        self.assertEqual(hashlib.sha256((proven / 'index.json').read_bytes()).hexdigest(),
                         receipt['pages']['index']['sha256'])
        (cache / 'vuln_data_update.dat').write_text('{"changed": []}')
        diag_path = self.root / 'proven-drift-diag.json'
        with self.assertRaisesRegex(ValueError, 'persistent_mismatch.*cache=') as ctx:
            native_audit.online_advisories(cache, self.root / 'drifted', forbidden, proven=proven, diagnostic_path=diag_path)
        self.assertEqual(native_audit.CLASSIFICATION_PERSISTENT_MISMATCH, ctx.exception.classification)
        self.assertEqual(native_audit.CLASSIFICATION_PERSISTENT_MISMATCH, json.loads(diag_path.read_text())['classification'])

    def test_confirmed_rotation_records_page_identities_headers_timestamps_and_semantic_diff(self):
        cache = self.advisory_fixture(
            name='cache-rot',
            revision='2026.11.16',
            updated='2026-11-16T00:00:00Z',
            base_doc={'existing.pkg': [{'url': 'https://github.com/advisories/GHSA-0001', 'severity': 1, 'versions': '[1.0.0, 1.1.0)'}]},
            update_doc={},
        )
        live_pages = [
            {'@name': 'base', '@id': 'https://data.nuget.org/v3-vulnerabilities/2026.11.16/base.json', '@updated': '2026-11-16T00:00:00Z'},
            {'@name': 'update', '@id': 'https://data.nuget.org/v3-vulnerabilities/2026.11.17/update.json', '@updated': '2026-11-17T01:02:03.1234567Z'},
        ]
        live_docs = {
            'base': {'existing.pkg': [{'url': 'https://github.com/advisories/GHSA-0001', 'severity': 1, 'versions': '[1.0.0, 1.1.0)'}]},
            'update': {
                'direct': [{'url': 'https://github.com/advisories/GHSA-direct', 'severity': 2, 'versions': '[0.1.0, 0.9.0)'}],
                'unrelated.pkg': [{'url': 'https://github.com/advisories/GHSA-unrel', 'severity': 1, 'versions': '[1.0.0, 2.0.0)'}],
            },
        }
        redirect_headers = (
            'HTTP/2 302\r\nLocation: https://data.nuget.org/v3-vulnerabilities/2026.11.17/update.json\r\n\r\n'
            'HTTP/2 200\r\nETag: "rev-2"\r\nLast-Modified: Fri, 27 Nov 2026 01:02:03 GMT\r\nAuthorization: Bearer secret\r\n'
        )
        fetcher = self.make_live_fetcher(
            live_pages, live_docs,
            headers_map={'update': 'ETag: "rev-2"\r\nLast-Modified: Fri, 27 Nov 2026 01:02:03 GMT\r\nAuthorization: Bearer secret\r\n'},
        )
        # Override update header writing with full multi-block redirect headers.
        def fetch_with_redirect(command, *args, **kwargs):
            fetcher(command, *args, **kwargs)
            if Path(command[-1]).stem == 'update':
                Path(command[command.index('--dump-header') + 1]).write_text(redirect_headers)

        diag_path = self.root / 'rotation-diag.json'
        with self.assertRaises(native_audit.AdvisoryVerificationError) as ctx:
            native_audit.online_advisories(
                cache, self.root / 'rot-out', fetch_with_redirect,
                restored_packages={'Direct/1.0.0', 'Transitive/1.0.0'},
                diagnostic_path=diag_path,
            )
        self.assertEqual(native_audit.CLASSIFICATION_CONFIRMED_ROTATION, ctx.exception.classification)
        diag = json.loads(diag_path.read_text())
        self.assertEqual(native_audit.CLASSIFICATION_CONFIRMED_ROTATION, diag['classification'])
        self.assertEqual(0, diag['recoveryAttempt'])
        self.assertIsNotNone(diag['cacheRetrievedAtUtc'])
        self.assertIsNotNone(diag['onlineRetrievedAtUtc'])
        self.assertEqual(['update'], diag['offendingPages'])
        self.assertEqual('advanced', diag['pages']['update']['updatedDirection'])
        self.assertEqual('unchanged', diag['pages']['base']['updatedDirection'])
        self.assertTrue(diag['pages']['base']['bytesMatch'])
        self.assertEqual('"rev-2"', diag['pages']['update']['headers']['etag'])
        self.assertNotIn('authorization', diag['pages']['update']['headers'])
        self.assertEqual(['direct', 'unrelated.pkg'], diag['semanticDiff']['addedPackages'])
        self.assertEqual(2, diag['semanticDiff']['addedAdvisoriesCount'])
        self.assertEqual(1, len(diag['semanticDiff']['restoredPackageIntersection']))
        self.assertEqual('direct', diag['semanticDiff']['restoredPackageIntersection'][0]['packageId'])
        self.assertEqual(['Direct/1.0.0'], diag['semanticDiff']['restoredPackageIntersection'][0]['restoredIdentities'])

    def test_persistent_mismatch_guards_unchanged_id_drift_regression_removed_page_and_no_advance(self):
        cases = (
            'unchanged-id-content-drift',
            'unchanged-updated-changed-id-and-content-with-other-advance',
            'regressed-with-other-advance',
            'single-page-regressed',
            'id-changed-without-updated-advance',
            'added-page-without-updated-advance',
            'removed-page',
            'missing-cached-page-during-rotation',
        )
        for case in cases:
            with self.subTest(case=case):
                cache = self.advisory_fixture(name='pm-' + case, revision='rev1', updated='2026-11-16T00:00:00Z')
                live_pages = [
                    {'@name': 'base', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev1/base.json', '@updated': '2026-11-16T00:00:00Z'},
                    {'@name': 'update', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev2/update.json', '@updated': '2026-11-17T00:00:00Z'},
                ]
                live_docs = {'base': {}, 'update': {'pkg.new': [{'url': 'https://github.com/advisories/GHSA-new', 'severity': 1, 'versions': '[1.0.0, 2.0.0)'}]}}
                expected_page = 'base'
                if case == 'unchanged-id-content-drift':
                    live_docs['base'] = {'tampered.pkg': [{'url': 'https://github.com/advisories/GHSA-x', 'severity': 1, 'versions': '[1.0.0, 2.0.0)'}]}
                    expected_page = 'base'
                elif case == 'unchanged-updated-changed-id-and-content-with-other-advance':
                    live_pages[0]['@id'] = 'https://data.nuget.org/v3-vulnerabilities/rev2/base.json'
                    live_docs['base'] = {'drifted.pkg': [{'url': 'https://github.com/advisories/GHSA-d', 'severity': 1, 'versions': '[1.0.0, 2.0.0)'}]}
                    expected_page = 'base'
                elif case == 'regressed-with-other-advance':
                    live_pages[0]['@updated'] = '2026-11-15T23:59:59Z'
                    expected_page = 'base'
                elif case == 'single-page-regressed':
                    live_pages[1]['@updated'] = '2026-11-15T00:00:00Z'
                    expected_page = 'update'
                elif case == 'id-changed-without-updated-advance':
                    live_pages[1]['@updated'] = '2026-11-16T00:00:00Z'
                    expected_page = 'update'
                elif case == 'added-page-without-updated-advance':
                    live_pages[1] = {'@name': 'update', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev1/update.json', '@updated': '2026-11-16T00:00:00Z'}
                    live_pages.append({'@name': 'extra', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev1/extra.json', '@updated': '2026-11-16T00:00:00Z'})
                    live_docs = {'base': {}, 'update': {}, 'extra': {'extra.pkg': [{'url': 'https://github.com/advisories/GHSA-e', 'severity': 1, 'versions': '[1.0.0, 2.0.0)'}]}}
                    # Ensure stray cache file for live-added page is never loaded.
                    (cache / 'vuln_data_extra.dat').write_text('{"stray": []}')
                    expected_page = 'extra'
                elif case == 'removed-page':
                    live_pages = [live_pages[1]]
                    expected_page = 'base'
                elif case == 'missing-cached-page-during-rotation':
                    (cache / 'vuln_data_base.dat').unlink()
                    expected_page = 'base'

                diag_path = self.root / f'pm-diag-{case}.json'
                fetcher = self.make_live_fetcher(live_pages, live_docs)
                with self.assertRaises(native_audit.AdvisoryVerificationError) as ctx:
                    native_audit.online_advisories(cache, self.root / ('pm-out-' + case), fetcher, diagnostic_path=diag_path)
                self.assertEqual(native_audit.CLASSIFICATION_PERSISTENT_MISMATCH, ctx.exception.classification)
                self.assertIn('persistent_mismatch', str(ctx.exception))
                self.assertIn(expected_page, str(ctx.exception))
                diag = json.loads(diag_path.read_text())
                self.assertEqual(native_audit.CLASSIFICATION_PERSISTENT_MISMATCH, diag['classification'])
                self.assertIn(expected_page, diag['offendingPages'])
                if case == 'added-page-without-updated-advance':
                    self.assertIsNone(diag['pages']['extra']['cachedSha256'])
                    self.assertNotIn('stray', diag['semanticDiff']['removedPackages'])

    def test_unavailable_feed_conditions_fail_closed_with_zero_retries_and_diagnostic(self):
        cases = (
            'curl-error-index',
            'curl-error-page',
            'http-304-index',
            'http-404-page',
            'http-500-index',
            'http-503-page',
            'bad-json-index',
            'bad-json-page',
            'non-object-page',
            'naive-updated-timestamp',
        )
        for case in cases:
            with self.subTest(case=case):
                cache = self.advisory_fixture(name='unavail-' + case)
                pages = json.loads((cache / 'vuln_index.dat').read_text())
                docs = {'base': {}, 'update': {}}
                status_map, curl_errors, raw_overrides = {}, set(), {}
                if case == 'curl-error-index':
                    status_map['index'] = 503
                    curl_errors.add('index')
                elif case == 'curl-error-page':
                    status_map['update'] = 503
                    curl_errors.add('update')
                elif case == 'http-304-index':
                    status_map['index'] = 304
                elif case == 'http-404-page':
                    status_map['update'] = 404
                elif case == 'http-500-index':
                    status_map['index'] = 500
                elif case == 'http-503-page':
                    status_map['base'] = 503
                elif case == 'bad-json-index':
                    raw_overrides['index'] = '{not-json'
                elif case == 'bad-json-page':
                    raw_overrides['update'] = '{not-json'
                elif case == 'non-object-page':
                    raw_overrides['update'] = '["not-an-object"]'
                elif case == 'naive-updated-timestamp':
                    pages[1]['@updated'] = '2026-11-17T00:00:00'

                counts = {}
                fetcher = self.make_live_fetcher(
                    pages, docs, status_map=status_map, curl_error_pages=curl_errors,
                    raw_overrides=raw_overrides, call_counts=counts,
                )
                diag_path = self.root / f'unavail-diag-{case}.json'
                with self.assertRaises((RuntimeError, native_audit.AdvisoryVerificationError)) as ctx:
                    native_audit.online_advisories(cache, self.root / ('unavail-out-' + case), fetcher, diagnostic_path=diag_path)
                self.assertIn(native_audit.CLASSIFICATION_UNAVAILABLE, str(ctx.exception))
                self.assertTrue(all(count == 1 for count in counts.values()), f'expected 0 retries, got {counts}')
                diag = json.loads(diag_path.read_text())
                self.assertEqual(native_audit.CLASSIFICATION_UNAVAILABLE, diag['classification'])
                self.assertEqual(0, diag['recoveryAttempt'])

    def test_classify_restore_failure_distinguishes_nu1900_from_nu1901_to_nu1904(self):
        graph = native_audit.package_graph(self.assets)
        for code, expected_cls in (
            ('NU1900', native_audit.CLASSIFICATION_UNAVAILABLE),
            ('NU1901', native_audit.CLASSIFICATION_ADVISORY_AFFECTING_GRAPH),
            ('NU1902', native_audit.CLASSIFICATION_ADVISORY_AFFECTING_GRAPH),
            ('NU1903', native_audit.CLASSIFICATION_ADVISORY_AFFECTING_GRAPH),
            ('NU1904', native_audit.CLASSIFICATION_ADVISORY_AFFECTING_GRAPH),
        ):
            with self.subTest(code=code):
                stem = self.root / ('restore-' + code)
                (self.root / ('restore-' + code + '.stdout.txt')).write_text(
                    f"audit.csproj : error {code}: Package 'Direct' 1.0.0 has a known vulnerability.\n"
                )
                (self.root / ('restore-' + code + '.stderr.txt')).write_text('')
                diag_path = self.root / f'restore-diag-{code}.json'
                enriched = native_audit.classify_restore_failure(
                    RuntimeError('dotnet restore exited 1'), stem,
                    diagnostic_path=diag_path, restored_packages=graph,
                )
                self.assertIn(expected_cls, str(enriched))
                self.assertIn(code, str(enriched))
                diag = json.loads(diag_path.read_text())
                self.assertEqual(expected_cls, diag['classification'])
                self.assertEqual([code], diag['advisoryCodes'])
                self.assertEqual(['direct'], [item['packageId'] for item in diag['semanticDiff']['restoredPackageIntersection']])

    def _run_fake_audit_project(self, name, restore_behavior, fetch_behavior, proven=None):
        """Helper driving audit_project with controlled fake dotnet restore + curl fetch."""
        restore_envs = []

        def bounded(command, _timeout, output, *, cwd=None, environment=None, **_kwargs):
            if command[0] == 'dotnet' and command[1] == 'restore':
                restore_envs.append({'packages': environment['NUGET_PACKAGES'], 'http': environment['NUGET_HTTP_CACHE_PATH']})
                attempt_index = len(restore_envs) - 1
                restore_behavior(attempt_index, Path(cwd), Path(environment['NUGET_PACKAGES']),
                                 Path(environment['NUGET_HTTP_CACHE_PATH']), output)
            elif command[0] == 'curl':
                fetch_behavior(len(restore_envs) - 1, command)
            else:
                raise AssertionError('unexpected command: ' + repr(command))

        return restore_envs, native_audit.audit_project(
            self.project, self.root / name, self.root / (name + '-ev'),
            {'version': '11.0.100', 'rollForward': 'latestPatch'}, bounded,
            proven_advisories=proven,
        )

    def _populate_audit_restore(self, target_dir: Path, pkg_cache: Path, http_cache: Path,
                                revision: str, updated: str, update_doc: dict):
        pkg_cache.mkdir(parents=True, exist_ok=True)
        for pkg_name in ('Direct', 'Transitive'):
            identity = pkg_name + '/1.0.0'
            folder = pkg_cache / identity.lower()
            folder.mkdir(parents=True, exist_ok=True)
            data = ('public archive ' + pkg_name).encode()
            (folder / (pkg_name.lower() + '.1.0.0.nupkg')).write_bytes(data)
        audited = json.loads(json.dumps(self.document))
        audited['packageFolders'] = {str(pkg_cache): {}}
        (target_dir / 'obj').mkdir(exist_ok=True)
        (target_dir / 'obj/project.assets.json').write_text(json.dumps(audited))
        http = http_cache / 'fixture'
        http.mkdir(parents=True, exist_ok=True)
        pages = [
            {'@name': 'base', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev1/base.json', '@updated': '2026-11-16T00:00:00Z'},
            {'@name': 'update', '@id': f'https://data.nuget.org/v3-vulnerabilities/{revision}/update.json', '@updated': updated},
        ]
        (http / 'vuln_index.dat').write_text(json.dumps(pages))
        (http / 'vuln_data_base.dat').write_text('{}')
        (http / 'vuln_data_update.dat').write_text(json.dumps(update_doc))

    def test_audit_project_recovers_once_in_fresh_caches_on_confirmed_rotation(self):
        rev2_pages = [
            {'@name': 'base', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev1/base.json', '@updated': '2026-11-16T00:00:00Z'},
            {'@name': 'update', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev2/update.json', '@updated': '2026-11-17T00:00:00Z'},
        ]
        rev2_doc = {'unrelated.pkg': [{'url': 'https://github.com/advisories/GHSA-r2', 'severity': 1, 'versions': '[1.0.0, 2.0.0)'}]}
        live_fetch = self.make_live_fetcher(rev2_pages, {'base': {}, 'update': rev2_doc})

        def restore_behavior(attempt, cwd, pkg_cache, http_cache, _output):
            if attempt == 0:
                self._populate_audit_restore(cwd, pkg_cache, http_cache, 'rev1', '2026-11-16T00:00:00Z', {})
            else:
                self._populate_audit_restore(cwd, pkg_cache, http_cache, 'rev2', '2026-11-17T00:00:00Z', rev2_doc)

        restore_envs, receipt = self._run_fake_audit_project(
            'mod-rot', restore_behavior, lambda _attempt, cmd: live_fetch(cmd)
        )
        self.assertEqual(2, len(restore_envs))
        self.assertNotEqual(restore_envs[0]['packages'], restore_envs[1]['packages'])
        self.assertNotEqual(restore_envs[0]['http'], restore_envs[1]['http'])
        self.assertTrue(receipt['privateDirectory'].endswith('mod-rot-retry-1'))
        self.assertEqual(1, receipt['recoveryAttempt'])
        self.assertEqual(native_audit.CLASSIFICATION_MATCH, receipt['advisories']['classification'])
        self.assertEqual(native_audit.CLASSIFICATION_CONFIRMED_ROTATION,
                         receipt['advisories']['priorRotationDiagnostic']['classification'])
        native_audit.require_audit(receipt, self.project)
        diag = json.loads(Path(receipt['diagnosticPath']).read_text())
        self.assertEqual(1, diag['recoveryAttempt'])
        self.assertEqual(native_audit.CLASSIFICATION_MATCH, diag['classification'])
        self.assertEqual(native_audit.CLASSIFICATION_CONFIRMED_ROTATION, diag['priorRotationDiagnostic']['classification'])

    def test_audit_project_refuses_second_mismatch_after_single_retry(self):
        rev2_pages = [
            {'@name': 'base', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev1/base.json', '@updated': '2026-11-16T00:00:00Z'},
            {'@name': 'update', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev2/update.json', '@updated': '2026-11-17T00:00:00Z'},
        ]
        rev3_pages = [
            {'@name': 'base', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev1/base.json', '@updated': '2026-11-16T00:00:00Z'},
            {'@name': 'update', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev3/update.json', '@updated': '2026-11-18T00:00:00Z'},
        ]
        fetches = [
            self.make_live_fetcher(rev2_pages, {'base': {}, 'update': {'p2': []}}),
            self.make_live_fetcher(rev3_pages, {'base': {}, 'update': {'p3': []}}),
        ]
        restore_count = [0]

        def restore_behavior(attempt, cwd, pkg_cache, http_cache, _output):
            restore_count[0] += 1
            if attempt == 0:
                self._populate_audit_restore(cwd, pkg_cache, http_cache, 'rev1', '2026-11-16T00:00:00Z', {})
            else:
                self._populate_audit_restore(cwd, pkg_cache, http_cache, 'rev2', '2026-11-17T00:00:00Z', {'p2': []})

        with self.assertRaises(native_audit.AdvisoryVerificationError) as ctx:
            self._run_fake_audit_project('mod-rot2', restore_behavior, lambda attempt, cmd: fetches[attempt](cmd))
        self.assertEqual(2, restore_count[0], 'must never attempt a second retry')
        self.assertEqual(native_audit.CLASSIFICATION_PERSISTENT_MISMATCH, ctx.exception.classification)
        self.assertIn('persistent_mismatch', str(ctx.exception))
        diag = json.loads((self.root / 'mod-rot2-ev-advisory-diagnostic.json').read_text())
        self.assertEqual(native_audit.CLASSIFICATION_PERSISTENT_MISMATCH, diag['classification'])
        self.assertEqual('second_mismatch_after_retry', diag['reason'])
        self.assertEqual(1, diag['recoveryAttempt'])
        self.assertEqual(native_audit.CLASSIFICATION_CONFIRMED_ROTATION, diag['priorRotationDiagnostic']['classification'])

    def test_audit_project_handles_module_snapshot_drift_against_proven_advisories(self):
        # Create a proven snapshot at rev1.
        proven = self.root / 'proven-rev1'
        proven.mkdir()
        rev1_pages = [
            {'@name': 'base', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev1/base.json', '@updated': '2026-11-16T00:00:00Z'},
            {'@name': 'update', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev1/update.json', '@updated': '2026-11-16T00:00:00Z'},
        ]
        (proven / 'index.json').write_text(json.dumps(rev1_pages))
        (proven / 'base.json').write_text('{}')
        (proven / 'update.json').write_text('{}')

        # Subcase 1: module restore sees newer rev2 matching live rev2 -> accepted without retry.
        rev2_pages = [
            rev1_pages[0],
            {'@name': 'update', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev2/update.json', '@updated': '2026-11-17T00:00:00Z'},
        ]
        rev2_doc = {'other': [{'url': 'https://github.com/advisories/GHSA-m2', 'severity': 1, 'versions': '[1.0.0, 2.0.0)'}]}
        live_rev2 = self.make_live_fetcher(rev2_pages, {'base': {}, 'update': rev2_doc})
        restore_envs, receipt = self._run_fake_audit_project(
            'mod-drift-match',
            lambda _a, cwd, pkg, http, _o: self._populate_audit_restore(cwd, pkg, http, 'rev2', '2026-11-17T00:00:00Z', rev2_doc),
            lambda _a, cmd: live_rev2(cmd),
            proven=proven,
        )
        self.assertEqual(1, len(restore_envs))
        self.assertEqual(0, receipt['recoveryAttempt'])
        self.assertEqual(native_audit.CLASSIFICATION_MATCH, receipt['advisories']['classification'])
        diag = json.loads(Path(receipt['diagnosticPath']).read_text())
        self.assertEqual('forward_rotation_over_proven_verified_against_live', diag['provenSnapshotDrift'])

        # Subcase 2: module restore sees rev2 while live already moved to rev3 -> 1 fresh retry gets rev3 and passes.
        rev3_pages = [
            rev1_pages[0],
            {'@name': 'update', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev3/update.json', '@updated': '2026-11-18T00:00:00Z'},
        ]
        rev3_doc = {'other': [{'url': 'https://github.com/advisories/GHSA-m3', 'severity': 1, 'versions': '[1.0.0, 2.0.0)'}]}
        live_rev3 = self.make_live_fetcher(rev3_pages, {'base': {}, 'update': rev3_doc})

        def restore_rev2_then_rev3(attempt, cwd, pkg, http, _o):
            if attempt == 0:
                self._populate_audit_restore(cwd, pkg, http, 'rev2', '2026-11-17T00:00:00Z', rev2_doc)
            else:
                self._populate_audit_restore(cwd, pkg, http, 'rev3', '2026-11-18T00:00:00Z', rev3_doc)

        restore_envs2, receipt2 = self._run_fake_audit_project(
            'mod-drift-retry', restore_rev2_then_rev3, lambda _a, cmd: live_rev3(cmd), proven=proven
        )
        self.assertEqual(2, len(restore_envs2))
        self.assertEqual(1, receipt2['recoveryAttempt'])
        native_audit.require_audit(receipt2, self.project)

        # Subcase 3: module restore sees older rev0 than proven rev1 -> fails closed as persistent_mismatch without live fetch.
        with self.assertRaises(native_audit.AdvisoryVerificationError) as ctx:
            self._run_fake_audit_project(
                'mod-drift-regress',
                lambda _a, cwd, pkg, http, _o: self._populate_audit_restore(cwd, pkg, http, 'rev0', '2026-11-15T00:00:00Z', {}),
                lambda _a, _cmd: self.fail('must not fetch live on regression vs proven snapshot'),
                proven=proven,
            )
        self.assertEqual(native_audit.CLASSIFICATION_PERSISTENT_MISMATCH, ctx.exception.classification)

    def test_audit_project_fails_closed_on_nu1902_restore_without_retry(self):
        restore_calls = [0]

        def restore_nu1902(_attempt, _cwd, _pkg, _http, output):
            restore_calls[0] += 1
            (output.parent / (output.name + '.stdout.txt')).write_text(
                "audit.csproj : error NU1902: Package 'Direct' 1.0.0 has a known moderate severity vulnerability.\n"
            )
            (output.parent / (output.name + '.stderr.txt')).write_text('')
            raise RuntimeError('dotnet restore exited 1')

        with self.assertRaises(RuntimeError) as ctx:
            self._run_fake_audit_project('mod-nu1902', restore_nu1902, lambda *_: self.fail('unexpected fetch'))
        self.assertEqual(1, restore_calls[0])
        self.assertIn(native_audit.CLASSIFICATION_ADVISORY_AFFECTING_GRAPH, str(ctx.exception))
        self.assertIn('NU1902', str(ctx.exception))
        diag = json.loads((self.root / 'mod-nu1902-ev-advisory-diagnostic.json').read_text())
        self.assertEqual(native_audit.CLASSIFICATION_ADVISORY_AFFECTING_GRAPH, diag['classification'])
        self.assertEqual(['NU1902'], diag['advisoryCodes'])

    def test_parse_iso8601_utc_compares_fractional_ticks_and_offsets_and_rejects_naive(self):
        t1 = native_audit.parse_iso8601_utc('2026-11-16T00:00:00.1234561Z')
        t2 = native_audit.parse_iso8601_utc('2026-11-16T00:00:00.1234562Z')
        t3 = native_audit.parse_iso8601_utc('2026-11-16T02:00:00.1234562+02:00')
        self.assertLess(t1, t2)
        self.assertEqual(t2, t3)
        for bad in ('2026-11-16T00:00:00', '2026-11-16', '', None, 'not-a-date'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                native_audit.parse_iso8601_utc(bad)

    def test_snapshot_matches_cache_until_restore_rewrites_advisory_bytes(self):
        cache = self.advisory_fixture()
        snapshot = self.root / 'snapshot'
        snapshot.mkdir()
        (snapshot / 'index.json').write_bytes((cache / 'vuln_index.dat').read_bytes())
        for name in ('base', 'update'):
            (snapshot / (name + '.json')).write_bytes((cache / ('vuln_data_' + name + '.dat')).read_bytes())
        self.assertTrue(native_audit.snapshot_matches_cache(cache, snapshot))
        (cache / 'vuln_index.dat').write_text('[]')
        self.assertFalse(native_audit.snapshot_matches_cache(cache, snapshot))

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

    def test_proven_mode_corrupt_or_missing_cache_writes_diagnostic_and_keeps_non_inverted_fields(self):
        proven_doc = {'proven.only': [{'url': 'https://github.com/advisories/GHSA-p', 'severity': 1, 'versions': '[1.0.0, 2.0.0)'}]}
        cache_match = self.advisory_fixture(name='prov-match-cache', update_doc=proven_doc)
        proven = self.root / 'prov-snapshot'
        proven.mkdir()
        (proven / 'index.json').write_bytes((cache_match / 'vuln_index.dat').read_bytes())
        (proven / 'base.json').write_bytes((cache_match / 'vuln_data_base.dat').read_bytes())
        (proven / 'update.json').write_bytes((cache_match / 'vuln_data_update.dat').read_bytes())

        match_diag = self.root / 'prov-match-diag.json'
        native_audit.online_advisories(
            cache_match, self.root / 'prov-match-out',
            lambda *_: self.fail('unexpected fetch'), proven=proven, diagnostic_path=match_diag,
        )
        diag = json.loads(match_diag.read_text())
        self.assertEqual(hashlib.sha256((cache_match / 'vuln_data_update.dat').read_bytes()).hexdigest(),
                         diag['pages']['update']['cachedSha256'])
        self.assertEqual(hashlib.sha256((proven / 'update.json').read_bytes()).hexdigest(),
                         diag['pages']['update']['onlineSha256'])

        # Drifted cache: cache has cache.only, proven has proven.only -> addedPackages=['proven.only'], removedPackages=['cache.only'].
        cache_drift = self.advisory_fixture(
            name='prov-drift-cache',
            update_doc={'cache.only': [{'url': 'https://github.com/advisories/GHSA-c', 'severity': 1, 'versions': '[1.0.0, 2.0.0)'}]},
        )
        drift_diag = self.root / 'prov-drift-diag.json'
        with self.assertRaises(native_audit.AdvisoryVerificationError) as ctx:
            native_audit.online_advisories(
                cache_drift, self.root / 'prov-drift-out',
                lambda *_: self.fail('unexpected fetch'), proven=proven, diagnostic_path=drift_diag,
            )
        self.assertEqual(native_audit.CLASSIFICATION_PERSISTENT_MISMATCH, ctx.exception.classification)
        d = json.loads(drift_diag.read_text())
        self.assertEqual(hashlib.sha256((cache_drift / 'vuln_data_update.dat').read_bytes()).hexdigest(),
                         d['pages']['update']['cachedSha256'])
        self.assertEqual(hashlib.sha256((proven / 'update.json').read_bytes()).hexdigest(),
                         d['pages']['update']['onlineSha256'])
        self.assertEqual(['proven.only'], d['semanticDiff']['addedPackages'])
        self.assertEqual(['cache.only'], d['semanticDiff']['removedPackages'])

        # Corrupt and missing cached pages under proven mode must raise AdvisoryVerificationError + write diagnostic.
        for defect in ('corrupt', 'missing'):
            with self.subTest(defect=defect):
                bad_cache = self.advisory_fixture(name='prov-' + defect)
                if defect == 'corrupt':
                    (bad_cache / 'vuln_data_update.dat').write_text('{not-json')
                else:
                    (bad_cache / 'vuln_data_update.dat').unlink()
                bad_diag = self.root / f'prov-{defect}-diag.json'
                with self.assertRaises(native_audit.AdvisoryVerificationError) as ctx:
                    native_audit.online_advisories(
                        bad_cache, self.root / ('prov-' + defect + '-out'),
                        lambda *_: self.fail('unexpected fetch'), proven=proven, diagnostic_path=bad_diag,
                    )
                self.assertEqual(native_audit.CLASSIFICATION_PERSISTENT_MISMATCH, ctx.exception.classification)
                self.assertTrue(bad_diag.is_file())
                bd = json.loads(bad_diag.read_text())
                self.assertEqual(native_audit.CLASSIFICATION_PERSISTENT_MISMATCH, bd['classification'])
                self.assertIn('update', bd['offendingPages'])

    def test_validation_guards_unhashable_names_diagnostic_name_overflow_encoded_urls_and_nondict_entries(self):
        # Unhashable @name and reserved @name == 'diagnostic'.
        for bad_name in (['base'], {'k': 'v'}, 'diagnostic', 'index'):
            with self.subTest(bad_name=bad_name):
                raw = json.dumps([{'@name': bad_name, '@id': 'https://data.nuget.org/v3-vulnerabilities/rev/a.json',
                                   '@updated': '2026-11-16T00:00:00Z'}]).encode()
                with self.assertRaises(ValueError):
                    native_audit.validate_advisory_index(raw)

        # @updated OverflowError (UTC conversion past year 9999).
        with self.assertRaisesRegex(ValueError, 'out of range|invalid'):
            native_audit.parse_iso8601_utc('9999-12-31T23:59:59-10:00')

        # Percent-encoded traversal/slashes and backslashes in @id.
        for bad_url in (
            'https://data.nuget.org/v3-vulnerabilities/%2e%2e/secret.json',
            'https://data.nuget.org/v3-vulnerabilities/rev%2f..%2fsecret.json',
            'https://data.nuget.org/v3-vulnerabilities/rev%5cbase.json',
            'https://data.nuget.org/v3-vulnerabilities/rev\\base.json',
        ):
            with self.subTest(bad_url=bad_url):
                raw = json.dumps([{'@name': 'base', '@id': bad_url, '@updated': '2026-11-16T00:00:00Z'}]).encode()
                with self.assertRaisesRegex(ValueError, 'not bound to its official source'):
                    native_audit.validate_advisory_index(raw)

        # Non-dict advisory list entries.
        with self.assertRaisesRegex(ValueError, 'malformed entries'):
            native_audit.parse_advisory_page(json.dumps({'pkg': ['not-a-dict']}).encode(), name='update')

        # require_policy tolerates level: None and code: None without crashing or producing 'NONE'.
        value = json.loads(json.dumps(self.document))
        value['logs'] = [{'code': None, 'level': None}, {'code': None, 'level': 'Warning', 'message': 'plain warning'}]
        self.assets.write_text(json.dumps(value))
        diag_path = self.root / 'null-log-diag.json'
        with self.assertRaises(native_audit.AdvisoryVerificationError) as ctx:
            native_audit.require_policy(self.assets, diagnostic_path=diag_path)
        self.assertEqual([], ctx.exception.diagnostic['advisoryCodes'])
        self.assertEqual([], json.loads(diag_path.read_text())['advisoryCodes'])

    def test_parse_http_headers_ignores_proxy_tunnel_and_redacts_api_keys_and_partial_live_diag_preserves_cache_meta(self):
        headers_file = self.root / 'proxy.headers'
        headers_file.write_text(
            'HTTP/1.1 200 Connection established\r\nProxy-Agent: test\r\n\r\n'
            'HTTP/2 503\r\nRetry-After: 12\r\nX-Api-Key: secret1\r\nX-NuGet-ApiKey: secret2\r\n'
            'WWW-Authenticate: Bearer realm="test"\r\n\r\n'
        )
        status, parsed = native_audit.parse_http_headers(headers_file)
        self.assertEqual(503, status)
        self.assertEqual({'retry-after': '12'}, parsed)

        # Proxy tunnel alone (no upstream response yet) must not report 200.
        tunnel_only = self.root / 'tunnel-only.headers'
        tunnel_only.write_text('HTTP/1.1 200 Connection established\r\n\r\n')
        self.assertEqual((None, {}), native_audit.parse_http_headers(tunnel_only))

        # Partial diagnostic on page-2 failure retains cachedId/cachedUpdated and actual bytesMatch for index and page 1.
        cache = self.advisory_fixture(name='partial-meta-cache')
        pages = json.loads((cache / 'vuln_index.dat').read_text())
        fetcher = self.make_live_fetcher(pages, {'base': {}, 'update': {}}, status_map={'update': 503})
        diag_path = self.root / 'partial-meta-diag.json'
        with self.assertRaises(native_audit.AdvisoryVerificationError):
            native_audit.online_advisories(cache, self.root / 'partial-meta-out', fetcher, diagnostic_path=diag_path)
        diag = json.loads(diag_path.read_text())
        self.assertTrue(diag['pages']['index']['bytesMatch'])
        self.assertTrue(diag['pages']['base']['bytesMatch'])
        self.assertEqual(pages[0]['@id'], diag['pages']['base']['cachedId'])
        self.assertEqual(pages[0]['@updated'], diag['pages']['base']['cachedUpdated'])

    def test_audit_project_attempt_1_non_rotation_failures_preserve_prior_rotation_diagnostic(self):
        rev2_pages = [
            {'@name': 'base', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev1/base.json', '@updated': '2026-11-16T00:00:00Z'},
            {'@name': 'update', '@id': 'https://data.nuget.org/v3-vulnerabilities/rev2/update.json', '@updated': '2026-11-17T00:00:00Z'},
        ]
        rev2_fetch = self.make_live_fetcher(rev2_pages, {'base': {}, 'update': {'p2': []}})

        for failure_mode in ('retry-nu1902', 'retry-policy', 'retry-curl-503', 'retry-http-304'):
            with self.subTest(failure_mode=failure_mode):
                def restore_behavior(attempt, cwd, pkg_cache, http_cache, output):
                    if attempt == 0:
                        self._populate_audit_restore(cwd, pkg_cache, http_cache, 'rev1', '2026-11-16T00:00:00Z', {})
                        return
                    if failure_mode == 'retry-nu1902':
                        (output.parent / (output.name + '.stdout.txt')).write_text(
                            "audit.csproj : error NU1902: Package 'Direct' 1.0.0 has a known vulnerability.\n"
                        )
                        (output.parent / (output.name + '.stderr.txt')).write_text('')
                        raise RuntimeError('dotnet restore exited 1')
                    self._populate_audit_restore(cwd, pkg_cache, http_cache, 'rev2', '2026-11-17T00:00:00Z', {'p2': []})
                    if failure_mode == 'retry-policy':
                        assets = cwd / 'obj/project.assets.json'
                        doc = json.loads(assets.read_text())
                        doc['project']['restore']['restoreAuditProperties']['auditLevel'] = 'high'
                        assets.write_text(json.dumps(doc))

                retry_fetch = (
                    self.make_live_fetcher(rev2_pages, {'base': {}, 'update': {'p2': []}},
                                           status_map={'index': 503}, curl_error_pages={'index'})
                    if failure_mode == 'retry-curl-503'
                    else self.make_live_fetcher(rev2_pages, {'base': {}, 'update': {'p2': []}}, status_map={'index': 304})
                )

                with self.assertRaises((RuntimeError, native_audit.AdvisoryVerificationError)):
                    self._run_fake_audit_project(
                        'mod-retry-fail-' + failure_mode,
                        restore_behavior,
                        lambda attempt, cmd: rev2_fetch(cmd) if attempt == 0 else retry_fetch(cmd),
                    )
                diag = json.loads((self.root / f'mod-retry-fail-{failure_mode}-ev-advisory-diagnostic.json').read_text())
                self.assertIsNotNone(diag['priorRotationDiagnostic'])
                self.assertEqual(native_audit.CLASSIFICATION_CONFIRMED_ROTATION,
                                 diag['priorRotationDiagnostic']['classification'])
                self.assertEqual(1, diag['recoveryAttempt'])


if __name__ == '__main__':
    unittest.main()
