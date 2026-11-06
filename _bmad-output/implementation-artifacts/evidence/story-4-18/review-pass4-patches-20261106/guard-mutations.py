"""Remove each guarded clause in turn, run the publication tests, and restore the exact original bytes."""
import json, subprocess, sys
from pathlib import Path

repo = Path('/home/administrator/projects/hexalith/mcpcli')
target = repo / 'scripts/verify-paired-publication.py'
original = target.read_bytes()
actor_line = "or not actor or actor.endswith('[bot]') or decision.get('approved_by') != actor"
mutations = [
    ('automated-bot', actor_line, "or not actor or decision.get('approved_by') != actor", 1),
    ('actual-bot', actor_line, "or not actor or decision.get('approved_by') != actor", 2),
    ('automated-empty-actor', actor_line, "or actor.endswith('[bot]') or decision.get('approved_by') != actor", 1),
    ('actual-empty-actor', actor_line, "or actor.endswith('[bot]') or decision.get('approved_by') != actor", 2),
    ('actual-future', 'if decided_at > datetime.now(timezone.utc):', 'if False:', 1),
    ('extract-duplicate', 'item.filename in names or ', '', 1),
    ('extract-absolute', 'or name.is_absolute() ', '', 1),
    ('extract-parent', "or '..' in name.parts", '', 1),
    ('extract-backslash', "or '\\\\' in item.filename ", '', 1),
    ('extract-drive', "or re.match(r'^[A-Za-z]:', item.filename)", '', 1),
    ('extract-symlink', 'or (item.external_attr >> 16) & 0o170000 == 0o120000', '', 1),
    ('package-duplicate', 'len(names) != len(set(names)) or ', 'False or ', 1),
    ('package-absolute', 'PurePosixPath(item).is_absolute() or ', '', 1),
    ('package-parent', "'..' in PurePosixPath(item).parts or ", '', 1),
    ('package-backslash', " or '\\\\' in item for item in names", ' for item in names', 1),
    ('candidate-symlink', 'candidate.is_symlink() or ', '', 1),
    ('candidate-listing', '{item.name for item in candidate.iterdir()} != expected', 'False', 1),
]
results = []
try:
    for name, old, new, occurrence in mutations:
        text = original.decode()
        index = -1
        for _ in range(occurrence):
            index = text.index(old, index + 1)
        target.write_text(text[:index] + new + text[index + len(old):])
        run = subprocess.run([sys.executable, '-m', 'unittest', 'test_paired_publication'], cwd=repo / 'scripts/tests',
                             capture_output=True, text=True, env={'PYTHONDONTWRITEBYTECODE': '1', 'PATH': '/usr/bin:/bin'}, timeout=300)
        failed = [line for line in run.stderr.splitlines() if line.startswith(('FAIL:', 'ERROR:'))]
        results.append({'mutation': name, 'exit': run.returncode, 'detected': run.returncode != 0, 'failing': failed})
        print(name, 'detected' if run.returncode else 'NOT DETECTED', failed[:3], flush=True)
finally:
    target.write_bytes(original)
assert target.read_bytes() == original
Path(sys.argv[1]).write_text(json.dumps(results, indent=2) + '\n')
