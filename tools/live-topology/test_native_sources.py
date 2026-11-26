"""Exercise actual private Git fixtures and byte/identity custody without starting services."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import native_sources


class NativeSourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'module'
        self.root.mkdir()
        self.selection = {'sources': {}}
        for module in native_sources.MODULES:
            checkout = self.root / 'references' / module
            checkout.mkdir(parents=True)
            subprocess.run(['git', 'init', '--quiet', str(checkout)], check=True)
            project = checkout / 'src' / module / (module + '.csproj')
            project.parent.mkdir(parents=True)
            project.write_text('<Project/>')
            (checkout / '.gitignore').write_text('bin/\nobj/\n')
            subprocess.run(['git', 'add', '.'], cwd=checkout, check=True)
            subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                            '-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', 'test: fixture source'], cwd=checkout, check=True)
            commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout).decode().strip()
            self.selection['sources'][module] = {'commit': commit}
        self.calls = []

    def bounded(self, command, _seconds, _output, *, cwd=None, **_kwargs):
        self.calls.append(command)
        subprocess.run(command, cwd=cwd, check=True, capture_output=True)
        return ''

    def create(self):
        return native_sources.create(self.root, self.root.parent / 'private', self.selection, self.root.parent, self.bounded)

    def test_private_fixtures_preserve_source_identity_and_seal_source_assets_and_outputs(self):
        proof = self.create()
        for module, entry in proof['modules'].items():
            checkout = Path(entry['path'])
            output = checkout / 'src' / module / 'bin/Release/net11.0/host.dll'
            output.parent.mkdir(parents=True)
            output.write_bytes(b'distinct fixture build')
            assets = checkout / 'src' / module / 'obj/project.assets.json'
            assets.parent.mkdir()
            assets.write_text('{}')
            self.assertFalse((checkout / 'references/Hexalith.Builds/.git').exists())
        native_sources.seal(proof)
        native_sources.require(proof)
        self.assertEqual('prepared', proof['result'])
        self.assertEqual(set(native_sources.MODULES), set(proof['modules']))
        entry = proof['modules']['Hexalith.Tenants']
        self.assertIn('src/Hexalith.Tenants/bin/Release/net11.0/host.dll', entry['files'])
        self.assertIn('src/Hexalith.Tenants/obj/project.assets.json', entry['files'])
        output = Path(entry['path']) / 'src/Hexalith.Tenants/bin/Release/net11.0/host.dll'
        output.write_bytes(b'changed fixture')
        with self.assertRaisesRegex(ValueError, 'bytes changed'):
            native_sources.require(proof)
        self.assertFalse(any((self.root / 'references/Hexalith.Tenants').rglob('host.dll')))

    def test_dirty_source_is_rejected_before_it_can_become_a_new_seal(self):
        proof = self.create()
        project = Path(proof['modules']['Hexalith.Parties']['path']) / 'src/Hexalith.Parties/Hexalith.Parties.csproj'
        project.write_text('<Changed/>')
        with self.assertRaisesRegex(ValueError, 'source identity'):
            native_sources.seal(proof)

    def test_nested_builds_and_in_place_source_fixtures_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            native_sources.create(self.root, self.root / 'private', self.selection, self.root, self.bounded)
        proof = self.create()
        nested = Path(proof['modules']['Hexalith.Tenants']['path']) / 'references/Hexalith.Builds/Props/Directory.Packages.props'
        nested.parent.mkdir(parents=True)
        nested.write_text('<Project/>')
        with self.assertRaises(ValueError):
            native_sources.seal(proof)

    def test_missing_local_checkout_fetches_origin_without_nested_submodules(self):
        module = 'Hexalith.Projects'
        shutil.rmtree(self.root / 'references' / module)
        (self.root / 'references' / module).mkdir()
        commit = self.selection['sources'][module]['commit']
        calls = []

        def bounded(command, _seconds, _output, *, cwd=None, **_kwargs):
            calls.append(command)
            if command[1] == 'clone' and str(command[-2]).endswith('Hexalith.Projects'):
                raise AssertionError('An uninitialized gitlink must not clone the empty local path.')
            if command[1] == 'clone':
                subprocess.run(command, check=True, capture_output=True)
                return ''
            if command[:2] == ['git', 'init']:
                subprocess.run(['git', 'init', '--quiet'], cwd=cwd, check=True)
                return ''
            if command[:3] == ['git', 'remote', 'add']:
                subprocess.run(command, cwd=cwd, check=True, capture_output=True)
                return ''
            if command[1] == 'fetch':
                self.assertIn('--no-recurse-submodules', command)
                return ''
            if command[1] == 'checkout':
                self.assertIn('--no-recurse-submodules', command)
                return ''
            subprocess.run(command, cwd=cwd, check=True, capture_output=True)
            return ''

        proof = native_sources.create(self.root, self.root.parent / 'private-gitlink', self.selection,
                                      self.root.parent, bounded)
        self.assertEqual(commit, proof['modules'][module]['commit'])
        self.assertEqual([commit], [command[-1] for command in calls if command[1] == 'fetch'])
        self.assertTrue(any(command[1] == 'init' for command in calls))
        self.assertFalse(any(command[1] == 'clone' and str(command[-2]).endswith(module) for command in calls))


if __name__ == '__main__':
    unittest.main()
