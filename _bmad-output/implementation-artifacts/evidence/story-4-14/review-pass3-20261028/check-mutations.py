"""Run pass-3 removal/drift checks in disposable fixtures, preserving repository files."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'tools/live-topology'))
import test_ci

checks = []
mutations = [
    ('docker-readiness-removal', 'test_prerequisite_failures_precede_source_builds',
     "        bounded(['docker', 'info', '--format', '{{.ServerVersion}}'], 30, evidence / 'docker-info')\n", ''),
    ('interrupted-operation-removal', 'test_aggregate_deadline_names_interrupted_operation_from_pending_lane',
     "for item in lane.get('vectors', []) if item.get('result') == 'running']",
     "for item in lane.get('vectors', []) if False]"),
    ('vector-control-exception-capture-removal', 'test_sigterm_stops_detached_child_and_retains_failed_receipt_and_diagnostics',
     '        except BaseException as error:\n            failures = []',
     '        except Exception as error:\n            failures = []'),
    ('smoke-control-exception-guard-removal', 'test_sigterm_during_smoke_preserves_cancellation_after_vector_failure',
     "if isinstance(error, Exception) and report.get('vectors', {}).get('result') == 'failed' and not report.get('smoke'):",
     "if report.get('vectors', {}).get('result') == 'failed' and not report.get('smoke'):"),
]

for name, method, original, replacement in mutations:
    class MutatedCase(test_ci.CiHooksTests):
        def setUp(self):
            super().setUp()
            source = self.tools / 'ci.py'
            text = source.read_text()
            assert text.count(original) == 1, (name, 'mutation target changed')
            source.write_text(text.replace(original, replacement, 1))
    output = io.StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        result = unittest.TextTestRunner(stream=output, verbosity=2).run(MutatedCase(method))
    checks.append({'name': name, 'detected': not result.wasSuccessful(),
                   'failures': len(result.failures), 'errors': len(result.errors)})
    print(name + '\n' + output.getvalue())

recorded = subprocess.run(['git', 'ls-tree', 'HEAD', 'references/Hexalith.Builds'],
                          cwd=ROOT, check=True, capture_output=True, text=True).stdout
pin = recorded.split()[2]
for filename, mutation in [('ci.yml', 'caller-pin-drift'), ('commitlint.yml', 'commitlint-pin-drift'),
                           (None, 'gitlink-drift'), ('additional.yaml', 'additional-unpinned-reference')]:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        workflows = root / '.github/workflows'
        workflows.mkdir(parents=True)
        for source in (ROOT / '.github/workflows').glob('*.yml'):
            shutil.copyfile(source, workflows / source.name)
        if filename == 'additional.yaml':
            (workflows / filename).write_text('uses: Hexalith/Hexalith.Builds/.github/workflows/other.yml@main\n')
        elif filename:
            source = workflows / filename
            text = source.read_text()
            assert pin in text
            source.write_text(text.replace(pin, 'f' * 40))
        tree = recorded.replace(pin, 'f' * 40) if filename is None else recorded
        output = io.StringIO()
        with patch.object(test_ci, 'HERE', root / 'tools/live-topology'), \
                patch.object(test_ci.subprocess, 'run', return_value=SimpleNamespace(stdout=tree)), \
                redirect_stdout(output), redirect_stderr(output):
            result = unittest.TextTestRunner(stream=output, verbosity=2).run(
                test_ci.CiWorkflowTests('test_workflow_pin_matches_builds_gitlink'))
        checks.append({'name': mutation, 'detected': not result.wasSuccessful(),
                       'failures': len(result.failures), 'errors': len(result.errors)})
        print(mutation + '\n' + output.getvalue())

Path(__file__).with_name('mutation-results.json').write_text(json.dumps(checks, indent=2) + '\n')
raise SystemExit(0 if all(item['detected'] for item in checks) else 1)
