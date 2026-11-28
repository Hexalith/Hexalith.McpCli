"""Bind retained staged acceptance to the final source evidence at preparation."""

import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from paired_release import ROOT, digest, module


COMPARATOR = module('compare-paired-evidence')
PUBLICATION = module('verify-paired-publication')
VERIFIER = module('verify-release-source')
PREREQUISITES = module('verify-paired-prerequisites')
SHA = 'a' * 40
HISTORICAL_201_SHA = 'aa2845edbea23444a1d362060b8d0f5dc05a132e'


class PairedAcceptanceSourceTests(unittest.TestCase):
    @staticmethod
    def source():
        completed = {'status': 'completed', 'conclusion': 'success'}
        gates = {}
        for name, required in (('ci.yml', VERIFIER.STAGING_JOBS), ('commitlint.yml', VERIFIER.STAGING_COMMITLINT_JOBS)):
            jobs = [{'name': job, **completed, 'steps': [{'name': step, **completed} for step in steps]}
                    for job, steps in required.items()]
            gates[name] = {'source_sha': SHA, **completed, 'run_id': 12345, 'run_attempt': 1, 'jobs': jobs}
        return {
            'schema': 'mcpcli-paired-source/v1', 'source_sha': SHA, 'current_main': SHA,
            'source_clean': True, 'gates': gates,
            'fr22': {
                'source_sha': SHA, 'source_clean': True, 'baseline_revision': 'b' * 40,
                'upstream_main': 'c' * 40, 'required_revision': PREREQUISITES.REQUIRED,
                'synchronization': dict.fromkeys(('AGENTS.md', 'CLAUDE.md', '.github/copilot-instructions.md'), 'd' * 64),
            },
        }

    def test_acceptance_requires_the_exact_final_preparation_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / 'evidence'
            evidence.mkdir()
            source = self.source()
            initial_source = copy.deepcopy(source)
            initial_source['gates']['ci.yml']['run_id'] = 12344
            files = {
                'source-before.json': json.dumps(initial_source), 'source-after.json': json.dumps(source),
                'validation.json': '{}', 'consumer.json': '{}', 'consumer.command.json': '{}',
                'consumer.stdout.txt': '', 'consumer.stderr.txt': '', 'consumer-build.log': '',
            }
            for name, content in files.items():
                (evidence / name).write_text(content, encoding='utf-8')
            prepared = {'eligibility': 'current-main', 'source_clean': True, 'source_sha': SHA,
                        'version': '1.0.0', 'packages': {}, 'evidence': {name: digest(evidence / name) for name in files}}
            accepted = root / 'acceptance-source.json'
            output = root / 'accepted.json'

            rerun = copy.deepcopy(source)
            rerun['gates']['ci.yml']['run_attempt'] = 2
            upstream_moved = copy.deepcopy(source)
            upstream_moved['fr22']['upstream_main'] = 'e' * 40
            with patch.object(COMPARATOR, 'check_prepared', return_value=prepared):
                for document in (initial_source, rerun, upstream_moved):
                    accepted.write_text(json.dumps(document), encoding='utf-8')
                    with self.assertRaisesRegex(ValueError, 'Acceptance source evidence differs'):
                        COMPARATOR.compare(root / 'packages', root / 'prepared.json', [], output,
                                           acceptance_source=accepted)
                    self.assertFalse(output.exists())

                duplicate_source = '{"source_sha":"' + 'f' * 40 + '",' + json.dumps(source)[1:]
                accepted.write_text(duplicate_source, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'duplicate JSON keys'):
                    COMPARATOR.compare(root / 'packages', root / 'prepared.json', [], output,
                                       acceptance_source=accepted)
                self.assertFalse(output.exists())

                accepted.write_text(json.dumps(source, sort_keys=True, indent=2), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Package validation does not bind'):
                    COMPARATOR.compare(root / 'packages', root / 'prepared.json', [], output,
                                       acceptance_source=accepted)
                self.assertFalse(output.exists())

    def test_compare_receipt_has_no_stale_story_417_418_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / 'evidence'
            evidence.mkdir()
            source = self.source()
            version = '3.0.1'
            pkgs = {f'Hexalith.McpCli.Abstractions.{version}.nupkg': '1' * 64, f'Hexalith.McpCli.{version}.nupkg': '2' * 64}
            compiler_log = 'MissingDescriptionQuery.cs(2,1): warning MCPCLI001: blank\n    1 Warning(s)\n'
            (evidence / 'source-before.json').write_text(json.dumps(source), encoding='utf-8')
            (evidence / 'source-after.json').write_text(json.dumps(source), encoding='utf-8')
            (evidence / 'validation.json').write_text(json.dumps({'phase': 'paired', 'source_sha': SHA, 'version': version, 'packages': pkgs}), encoding='utf-8')
            (evidence / 'consumer.command.json').write_text(json.dumps({'exit_code': 0, 'argv': ['bash', 'scripts/smoke-bootstrap-consumer.sh', version]}), encoding='utf-8')
            (evidence / 'consumer.stdout.txt').write_text('', encoding='utf-8')
            (evidence / 'consumer.stderr.txt').write_text('', encoding='utf-8')
            (evidence / 'consumer-build.log').write_text(compiler_log, encoding='utf-8')
            (evidence / 'consumer.json').write_text(json.dumps({
                'schema': 'mcpcli-paired-consumer/v1', 'status': 'passed',
                'source_sha': SHA, 'version': version, 'packages': pkgs,
                'compiler_sha256': digest(evidence / 'consumer-build.log'),
                'command_sha256': digest(evidence / 'consumer.command.json'),
            }), encoding='utf-8')
            prepared_path = root / 'prepared.json'
            prepared = {
                'schema': 'mcpcli-paired-preparation/v1',
                'eligibility': 'current-main', 'source_clean': True,
                'source_sha': SHA, 'version': version, 'packages': pkgs,
                'evidence': {p.name: digest(p) for p in sorted(evidence.iterdir())},
            }
            prepared_path.write_text(json.dumps(prepared), encoding='utf-8')
            accepted_source = root / 'acceptance-source.json'
            accepted_source.write_text(json.dumps(source), encoding='utf-8')

            runner = module('run-paired-platform-tests')
            consumers = []
            for system, suites in (('Linux', []), ('Windows', ['Core', 'Cli']), ('Darwin', ['Cli'])):
                cdir = root / f'consumer-{system}'
                disc = cdir / 'smoke/discovery'
                disc.mkdir(parents=True)
                files = {
                    'modules.json': b'{"modules":[{"name":"alpha"}]}\n',
                    'operations-alpha.json': b'{"operations":[{"name":"alpha.one"}]}\n',
                    'describe-alpha.one.json': b'{"name":"alpha.one"}\n',
                    'mcp-tools.json': b'{"tools":[]}\n',
                    'mcp-modules.json': b'{"modules":[{"name":"alpha"}]}\n',
                    'mcp-operations-alpha.json': b'{"operations":[{"name":"alpha.one"}]}\n',
                    'mcp-describe-alpha.one.json': b'{"name":"alpha.one"}\n',
                }
                for name, raw in files.items():
                    (disc / name).write_bytes(raw)
                (cdir / 'smoke/smoke.json').write_text(json.dumps({
                    'schema': 'mcpcli-paired-smoke/v1', 'status': 'passed', 'os': system,
                    'source_sha': SHA, 'version': version, 'packages': pkgs,
                    'preparation_sha256': digest(prepared_path),
                    'checks': ['version', 'offline-discovery', 'config', 'json-lf', 'errors', 'mcp-protocol', 'output-file', 'table'],
                    'discovery': {name: digest(disc / name) for name in sorted(files)},
                }), encoding='utf-8')
                tdir = cdir / 'tests'
                tdir.mkdir(parents=True)
                xml_map = {}
                for suite in suites:
                    xname = f'Hexalith.McpCli.{suite}.Tests.xml'
                    tests_xml = ''.join(f'<test name="{t}" result="Pass" />' for t in (runner.WINDOWS_REQUIRED if system == 'Windows' else ['Sample.Pass']))
                    (tdir / xname).write_text(f'<assemblies><assembly failed="0" errors="0">{tests_xml}</assembly></assemblies>', encoding='utf-8')
                    xml_map[xname] = digest(tdir / xname)
                (tdir / 'tests.json').write_text(json.dumps({
                    'schema': 'mcpcli-paired-platform-tests/v1', 'status': 'passed', 'os': system,
                    'source_sha': SHA, 'version': version, 'packages': pkgs, 'suites': suites, 'xml': xml_map,
                }), encoding='utf-8')
                consumers.append(cdir)

            output = root / 'accepted-pair.json'
            with patch.object(COMPARATOR, 'check_prepared', return_value=prepared):
                COMPARATOR.compare(root / 'packages', prepared_path, consumers, output, acceptance_source=accepted_source)
            receipt = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(receipt['status'], 'accepted-staging-only')
            self.assertNotIn('4.17', receipt['publication'])
            self.assertNotIn('4.18', receipt['publication'])
            self.assertIn('refused', receipt['publication'])


class LegacyBypassAndTimingGuardsTests(unittest.TestCase):
    def _acceptance_context(self, directory: Path, version: str, sha: str):
        prepared = {
            'source_sha': sha,
            'version': version,
            'packages': {f'Hexalith.McpCli.Abstractions.{version}.nupkg': '1' * 64, f'Hexalith.McpCli.{version}.nupkg': '2' * 64},
        }
        accepted_path = directory / 'accepted-pair.json'
        accepted_path.write_text(json.dumps({'preparation_sha256': '3' * 64}), encoding='utf-8')
        completed = datetime.now(timezone.utc) - timedelta(minutes=10)
        decided = datetime.now(timezone.utc) - timedelta(minutes=2)
        origin = {'staging_run_id': 42080077255, 'completed_at': completed.strftime('%Y-%m-%dT%H:%M:%SZ')}
        bindings = {
            'source_sha': sha,
            'version': version,
            'packages': prepared['packages'],
            'staging_run_id': origin['staging_run_id'],
            'preparation_sha256': '3' * 64,
            'acceptance_sha256': digest(accepted_path),
            'readme_sha256': digest(ROOT / 'README.md'),
        }
        return prepared, accepted_path, origin, bindings, decided.strftime('%Y-%m-%dT%H:%M:%SZ')

    def test_timing_constant_points_to_docs_release_not_bmad_output(self):
        self.assertEqual(PUBLICATION.TIMING, 'docs/release/operator-setup-timing-exception.json')
        self.assertFalse(PUBLICATION.TIMING.startswith('_bmad-output/'))
        self.assertTrue((ROOT / PUBLICATION.TIMING).is_file())

    def test_automated_bypass_pinned_strictly_to_historical_201(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # Exact historical 2.0.1 + aa2845ed... is accepted.
            prepared, accepted_path, origin, bindings, decided = self._acceptance_context(root, '2.0.1', HISTORICAL_201_SHA)
            packet = root / 'ok-201.json'
            packet.write_text(json.dumps({
                'schema': 'mcpcli-paired-automated-acceptance/v1',
                'decision': 'approved',
                'authorization': 'user-requested-human-validation-bypass',
                'approved_by': 'jpiquot',
                'decided_at_utc': decided,
                **bindings,
            }), encoding='utf-8')
            result = PUBLICATION.operator_acceptance(packet, prepared, accepted_path, origin, 'jpiquot')
            self.assertEqual(result['version'], '2.0.1')

            # Future version or different SHA MUST be refused.
            for version, sha in (('3.0.0', HISTORICAL_201_SHA), ('2.0.2', HISTORICAL_201_SHA), ('2.0.1', SHA), ('3.0.1', SHA)):
                prepared, accepted_path, origin, bindings, decided = self._acceptance_context(root, version, sha)
                bad = root / f'bad-{version}-{sha[:6]}.json'
                bad.write_text(json.dumps({
                    'schema': 'mcpcli-paired-automated-acceptance/v1',
                    'decision': 'approved',
                    'authorization': 'user-requested-human-validation-bypass',
                    'approved_by': 'jpiquot',
                    'decided_at_utc': decided,
                    **bindings,
                }), encoding='utf-8')
                with self.subTest(version=version, sha=sha), self.assertRaisesRegex(ValueError, 'restricted to historical release 2.0.1'):
                    PUBLICATION.operator_acceptance(bad, prepared, accepted_path, origin, 'jpiquot')

    def test_operator_acceptance_validates_docs_timing_exception_and_rejects_bmad_or_tampered_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepared, accepted_path, origin, bindings, decided = self._acceptance_context(root, '3.0.1', SHA)
            # Reject stale _bmad-output reference
            stale = root / 'stale-timing.json'
            stale.write_text(json.dumps({
                'schema': 'mcpcli-paired-operator-acceptance/v1',
                'decision': 'approved',
                'approved_by': 'jpiquot',
                'decided_at_utc': decided,
                **bindings,
                'timing_exception': {
                    'reference': '_bmad-output/implementation-artifacts/evidence/story-4-17/timing-attempts.json',
                    'sha256': '0' * 64,
                    'elapsed_seconds': 685,
                    'first_time_operator': False,
                    'unassisted_success': False,
                    'decision': 'accepted-existing-exception',
                },
                'sessions': [],
            }), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, '685-second timing exception'):
                PUBLICATION.operator_acceptance(stale, prepared, accepted_path, origin, 'jpiquot')

            # Reject tampered tracked timing file (e.g. elapsedSeconds != 685)
            fake_root = root / 'fake-repo'
            (fake_root / 'docs/release').mkdir(parents=True)
            (fake_root / 'README.md').write_bytes((ROOT / 'README.md').read_bytes())
            tampered_timing = fake_root / PUBLICATION.TIMING
            tampered_doc = json.loads((ROOT / PUBLICATION.TIMING).read_text(encoding='utf-8'))
            tampered_doc['attempts'][0]['elapsedSeconds'] = 999
            tampered_timing.write_text(json.dumps(tampered_doc), encoding='utf-8')
            packet = root / 'tampered-timing-packet.json'
            packet.write_text(json.dumps({
                'schema': 'mcpcli-paired-operator-acceptance/v1',
                'decision': 'approved',
                'approved_by': 'jpiquot',
                'decided_at_utc': decided,
                **bindings,
                'timing_exception': {
                    'reference': PUBLICATION.TIMING,
                    'sha256': digest(tampered_timing),
                    'elapsed_seconds': 685,
                    'first_time_operator': False,
                    'unassisted_success': False,
                    'decision': 'accepted-existing-exception',
                },
                'sessions': [],
            }), encoding='utf-8')
            with patch.object(PUBLICATION, 'ROOT', fake_root):
                with self.assertRaisesRegex(ValueError, '685-second timing exception'):
                    PUBLICATION.operator_acceptance(packet, prepared, accepted_path, origin, 'jpiquot')
