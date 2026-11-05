"""Synthetic exact-source and public-archive rejection controls; no services or real checkouts."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

import native_cohort as native


class NativeCohortTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.selection = {'eventStoreVersion': '4.1.0', 'sources': {
            module: {'repository': native.REPOSITORIES[module], 'commit': 'a' * 40} for module in native.MODULES},
            'packages': []}
        for name, version in [('Hexalith.EventStore.Gateway', '4.1.0'), ('Hexalith.EventStore.Aspire', '4.1.0'),
                              ('Hexalith.Tenants.Contracts', '7.0.4'), ('Hexalith.Tenants.Aspire', '7.0.4')]:
            self.selection['packages'].append({'id': name, 'version': version, 'sourceCommit': 'a' * 40, 'sha256': 'b' * 64})
        self.path = self.root / 'selection.json'
        self.path.write_text(json.dumps(self.selection))
        self.calls = []
        self.heads = {module: 'a' * 40 for module in native.MODULES}
        self.dirty = None
        self.wrong_repository = None
        for module in native.MODULES:
            checkout = self.root / 'references' / module
            (checkout / '.git').mkdir(parents=True)
            project = checkout / 'src' / (module + '.CatalogBuilder' if module == 'Hexalith.Platform' else module)
            project.mkdir(parents=True)
            (project / (project.name + '.csproj')).touch()

    def bounded(self, command, seconds, output, *, cwd=None):
        self.calls.append((command, cwd))
        module = Path(cwd).name if cwd else None
        if command[1] == 'config':
            return '\n'.join(f'submodule.{name}.path references/{name}' for name in native.MODULES)
        if command[1:] == ['rev-parse', '--show-toplevel']:
            return str(cwd)
        if command[1:] == ['remote', 'get-url', 'origin']:
            return 'https://example.invalid/forged.git' if module == self.wrong_repository else native.REPOSITORIES[module]
        if command[1] == 'status':
            return ' M owned.cs' if module == self.dirty else ''
        if command[1] == 'rev-parse' and command[-1].endswith('^{commit}'):
            return 'a' * 40
        if command[1:] == ['rev-parse', 'HEAD']:
            return self.heads[module]
        if command[1] == 'checkout':
            self.heads[module] = command[-1]
        return ''

    def select(self):
        return native.select_sources(self.root, self.selection, self.root, self.bounded)

    def test_exact_clean_sources_preserve_local_checkouts(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS': '', 'RUNNER_ENVIRONMENT': ''}):
            sources = self.select()
        self.assertEqual(list(native.MODULES), [source['module'] for source in sources])
        self.assertFalse(any(command[1] in ('checkout', 'fetch') for command, _ in self.calls))

    def test_any_dirty_source_refuses_before_any_selection(self):
        self.heads['Hexalith.EventStore'] = 'b' * 40
        self.dirty = 'Hexalith.Platform'
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted'}):
            with self.assertRaisesRegex(ValueError, 'dirty owned files'):
                self.select()
        self.assertFalse(any(command[1] in ('checkout', 'fetch') for command, _ in self.calls))

    def test_wrong_repository_refuses_before_mutation(self):
        self.wrong_repository = 'Hexalith.Tenants'
        with self.assertRaisesRegex(ValueError, 'Wrong repository identity'):
            self.select()
        self.assertFalse(any(command[1] in ('checkout', 'fetch') for command, _ in self.calls))

    def test_local_revision_mismatch_never_fetches_or_updates_nested_inputs(self):
        self.heads['Hexalith.Tenants'] = 'b' * 40
        with patch.dict(os.environ, {'GITHUB_ACTIONS': '', 'RUNNER_ENVIRONMENT': ''}):
            with self.assertRaisesRegex(ValueError, 'only in disposable GitHub-hosted CI'):
                self.select()
        self.assertFalse(any(command[1] in ('checkout', 'fetch') for command, _ in self.calls))

    def test_disposable_ci_selects_only_exact_qualified_revision_without_recursion(self):
        self.heads['Hexalith.Parties'] = 'b' * 40
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted'}):
            self.select()
        mutations = [command for command, _ in self.calls if command[1] in ('checkout', 'fetch')]
        self.assertEqual([['git', 'fetch', '--no-recurse-submodules', '--depth=1', 'origin', 'a' * 40],
                          ['git', 'checkout', '--no-recurse-submodules', '--detach', 'a' * 40]], mutations)

    def test_competing_nested_catalog_refuses_before_selection_without_touching_it(self):
        for marker in ('.git', 'Props/Directory.Packages.props'):
            with self.subTest(marker=marker):
                path = self.root / 'references/Hexalith.Tenants/references/Hexalith.Builds' / marker
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'private nested input')
                try:
                    with self.assertRaisesRegex(ValueError, 'Competing nested Builds catalog'):
                        self.select()
                    self.assertEqual(b'private nested input', path.read_bytes())
                    self.assertEqual([], self.calls)
                finally:
                    path.unlink()

    def test_missing_qualified_commit_refuses_before_any_checkout(self):
        self.heads['Hexalith.EventStore'] = 'b' * 40
        original = self.bounded
        def missing(command, *args, **kwargs):
            if command[1] == 'rev-parse' and command[-1].endswith('^{commit}'):
                return 'c' * 40
            return original(command, *args, **kwargs)
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted'}):
            with self.assertRaisesRegex(ValueError, 'missing or mismatched'):
                native.select_sources(self.root, self.selection, self.root, missing)
        self.assertFalse(any(command[1] == 'checkout' for command, _ in self.calls))

    def test_missing_and_linked_sources_refuse(self):
        checkout = self.root / 'references/Hexalith.Platform'
        (checkout / '.git').rmdir()
        with self.assertRaisesRegex(ValueError, 'Missing declared direct root source'):
            self.select()

    def test_manifest_rejects_missing_wrong_repository_and_unpublished_candidate_inputs(self):
        for field, value in [('commit', 'moving-main'), ('repository', 'https://example.invalid/forged.git')]:
            changed = json.loads(json.dumps(self.selection))
            changed['sources']['Hexalith.Tenants'][field] = value
            self.path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, 'Invalid qualified source identity'):
                native.manifest(self.path)
        changed = json.loads(json.dumps(self.selection))
        changed['packages'][-1]['version'] = '7.0.4-local'
        self.path.write_text(json.dumps(changed))
        with self.assertRaisesRegex(ValueError, 'archive identities are required'):
            native.manifest(self.path)

    def test_archive_bytes_and_embedded_repository_must_both_match(self):
        package = next(item for item in self.selection['packages'] if item['id'] == 'Hexalith.Tenants.Contracts')
        archive = self.root / 'tenants.nupkg'
        def write(commit):
            with ZipFile(archive, 'w') as content:
                content.writestr('package.nuspec', '<package><metadata><id>Hexalith.Tenants.Contracts</id><version>7.0.4</version>'
                    '<repository url="https://github.com/Hexalith/Hexalith.Tenants.git" commit="' + commit + '" /></metadata></package>')
        write('a' * 40)
        package['sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.assertEqual(package, native.verify_archive(archive, package))
        write('b' * 40)
        with self.assertRaisesRegex(ValueError, 'archive hash mismatch'):
            native.verify_archive(archive, package)
        package['sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'repository source differs'):
            native.verify_archive(archive, package)
        with self.assertRaisesRegex(ValueError, 'no authenticated public archive'):
            native.require_restored_archive(archive, self.selection, 'Hexalith.EventStore.Contracts/4.1.0')


if __name__ == '__main__':
    unittest.main()
