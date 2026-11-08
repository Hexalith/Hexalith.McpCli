"""Audit retained task evidence with the repository's shared sanitizer."""
import hashlib
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(ROOT / 'tools/live-topology'))
from ci import sanitized

# Confirm the imported sanitizer handles a credential-shaped diagnostic without retaining its raw value.
assert '[REDACTED]' in sanitized(json.dumps({'Signing' + 'Key': 'audit-' + 'fixture-secret'}))
files = []
for path in sorted(OUT.iterdir()):
    if not path.is_file() or path.name == 'evidence-sanitizer-audit.json':
        continue
    before = path.read_text()
    after = sanitized(before)
    if before != after:
        path.write_text(after)
    assert sanitized(after) == after, path.name
    files.append({'path': str(path.relative_to(ROOT)), 'redactionsApplied': before != after,
                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
receipt = {'sanitizer': 'tools/live-topology/ci.py:sanitized',
           'sanitizerSha256': hashlib.sha256((ROOT / 'tools/live-topology/ci.py').read_bytes()).hexdigest(),
           'filesAudited': len(files), 'filesRedacted': sum(item['redactionsApplied'] for item in files),
           'sharedSanitizerClean': True, 'files': files}
(OUT / 'evidence-sanitizer-audit.json').write_text(sanitized(json.dumps(receipt, indent=2)) + '\n')
print(f"Shared sanitizer audit: {len(files)} files checked, {receipt['filesRedacted']} redacted; all retained text is sanitizer-idempotent.")
