"""Verify the frozen packet using unchanged bytes and Git's actual checkout filters."""
import hashlib
import json
from pathlib import Path
import subprocess


def git(*arguments):
    return subprocess.check_output(['git', '-c', 'core.autocrlf=true', *arguments])


root = Path(git('rev-parse', '--show-toplevel').decode().strip())
revision = git('rev-parse', 'HEAD').decode().strip()
packet = root / '_bmad-output/implementation-artifacts/evidence/story-4-12/publication-20261023/expanded-source-candidate'
index_path = packet / 'qualification-packet-index.json'
index = json.loads(index_path.read_bytes())
results = []
for name, expected in index['files'].items():
    path = packet / name
    relative = path.relative_to(root).as_posix()
    workspace = path.read_bytes()
    indexed = git('cat-file', 'blob', revision + ':' + relative)
    filtered = git('cat-file', '--filters', '--path=' + relative, revision + ':' + relative)
    hashes = {key: hashlib.sha256(value).hexdigest()
              for key, value in (('workspace', workspace), ('indexed', indexed), ('checkoutFiltered', filtered))}
    results.append({'path': relative, 'expectedSha256': expected['sha256'], 'actualSha256': hashes,
                    'matches': all(value == expected['sha256'] for value in hashes.values())})

relative_index = index_path.relative_to(root).as_posix()
index_bytes = index_path.read_bytes()
indexed_index = git('cat-file', 'blob', revision + ':' + relative_index)
filtered_index = git('cat-file', '--filters', '--path=' + relative_index, revision + ':' + relative_index)
receipt = {
    'command': 'python3 ' + Path(__file__).resolve().relative_to(root).as_posix(),
    'repositoryRevision': revision,
    'qualifiedSourceRevision': index['sourceCommit'],
    'coreAutocrlf': True,
    'checkoutFilterCommand': 'git -c core.autocrlf=true cat-file --filters --path=<path> <repositoryRevision>:<path>',
    'fileCount': len(results),
    'expectedFileCount': index['fileCount'],
    'allIndexedHashesMatch': len(results) == index['fileCount'] and all(item['matches'] for item in results),
    'packetIndex': {'path': relative_index, 'sha256': hashlib.sha256(index_bytes).hexdigest(),
                    'unchangedThroughCheckoutFilters': index_bytes == indexed_index == filtered_index},
    'files': results,
}
print(json.dumps(receipt, indent=2))
if not receipt['allIndexedHashesMatch'] or not receipt['packetIndex']['unchangedThroughCheckoutFilters']:
    raise SystemExit(1)
