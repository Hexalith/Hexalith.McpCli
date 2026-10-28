"""Check pass-4 identity/hash and diagnostic assertions in disposable fixtures."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'tools/live-topology'))
import test_ci

identity_test = 'test_preparation_order_bounds_source_flags_and_nonsecret_exports'
mutations = [
    ('source-commit-cwd-removal', identity_test,
     "'commit': bounded(['git', 'rev-parse', 'HEAD'], 10, evidence / (module + '-commit'), cwd=checkout)",
     "'commit': bounded(['git', 'rev-parse', 'HEAD'], 10, evidence / (module + '-commit'))"),
    ('source-status-removal', identity_test,
     "'status': bounded(['git', 'status', '--porcelain', '--untracked-files=normal'], 10, evidence / (module + '-status'), cwd=checkout)",
     "**{}"),
    ('source-status-cwd-removal', identity_test,
     "'status': bounded(['git', 'status', '--porcelain', '--untracked-files=normal'], 10, evidence / (module + '-status'), cwd=checkout)",
     "'status': bounded(['git', 'status', '--porcelain', '--untracked-files=normal'], 10, evidence / (module + '-status'))"),
    ('executable-hash-corruption', identity_test,
     "'sha256': hashlib.sha256(Path(shutil.which(name)).read_bytes()).hexdigest()",
     "'sha256': '0' * 64"),
    ('daprd-hash-corruption', identity_test,
     "tools['daprdSha256'] = hashlib.sha256(daprd.read_bytes()).hexdigest()",
     "tools['daprdSha256'] = '0' * 64"),
    ('bundle-index-hash-corruption', identity_test,
     "save(evidence / 'aspire-bundle-hashes.json', expected_bundle)",
     "save(evidence / 'aspire-bundle-hashes.json', {relative: '0' * 64 for relative in expected_bundle})"),
    ('bundle-tool-hash-corruption', identity_test,
     "tools[relative] = {'path': str(binary), 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}",
     "tools[relative] = {'path': str(binary), 'sha256': '0' * 64}"),
    ('lane-receipt-diagnostic-removal',
     'test_lane_level_errors_are_named_and_only_failed_operations_are_failures',
     "detail += f'; lane receipt: {vectors / \"live-lane.json\"}; runner stdout: {generation / \"vectors-process.stdout.txt\"}'",
     "detail += f'; runner stdout: {generation / \"vectors-process.stdout.txt\"}'"),
]

checks = []
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

Path(__file__).with_name('mutation-results.json').write_text(json.dumps(checks, indent=2) + '\n')
raise SystemExit(0 if all(item['detected'] for item in checks) else 1)
