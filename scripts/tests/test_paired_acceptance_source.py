"""Bind retained staged acceptance to the final source evidence at preparation."""

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paired_release import digest, module


COMPARATOR = module('compare-paired-evidence')
VERIFIER = module('verify-release-source')
PREREQUISITES = module('verify-paired-prerequisites')
SHA = 'a' * 40


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
