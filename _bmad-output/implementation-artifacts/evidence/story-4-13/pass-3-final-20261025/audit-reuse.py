"""Prove reused validation still binds to unchanged .NET sources, binaries and references."""
import hashlib,json,subprocess
from pathlib import Path
root=Path('/home/administrator/projects/hexalith/mcpcli')
out=Path(__file__).resolve().parent
prior=out.with_name('pass-3-patches-20261025')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
previous=json.loads((prior/'source-bindings.json').read_text())
expected={'tools/live-topology/plans/parties.list-parties.json','tools/live-topology/plans/parties.search-parties.json','tools/live-topology/test_live_runner.py'}
changed={name for name,digest in previous['sha256'].items() if sha(root/name)!=digest}
assert changed==expected,changed
assert all(sha(root/name)==digest for name,digest in previous['binarySha256'].items())
for name,commit in previous['referenceCommits'].items():
    actual=subprocess.check_output(['git','-C',str(root/'references'/name),'rev-parse','HEAD'],stderr=subprocess.DEVNULL,text=True).strip()
    assert actual==commit,(name,actual,commit)
index=json.loads((prior/'artifact-index.json').read_text())
assert all(sha(prior/name)==digest for name,digest in index.items())
binding=dict(previous)
binding.pop('documentationUpdatedAfterExecution',None)
binding['sha256']={name:sha(root/name) for name in previous['sha256']}
(out/'source-bindings.json').write_text(json.dumps(binding,indent=2)+'\n')
records=json.loads((prior/'runtime-bootstrap-receipt.json').read_text())
runtime=Path('/tmp/mcpcli-413-pass3-runtime-20261025/runtime')
assert len(records)==4
for row in records:
    assert sha(runtime/'bin'/Path(row['source']).name)==row['sha256']
reused=['restore','build','eventstore-build','tenants-build','parties-build','abstractions-tests','analyzers-tests','core-tests','manifest-tests','cli-tests','mcp-tests','conformance-tools','discovery','smoke','mutation-audit']
commands={}
for name in reused:
    path=prior/(name+'.command.json');receipt=json.loads(path.read_text());assert receipt['exitCode']==0
    commands[name]=dict(receipt=str(path.relative_to(root)),sha256=sha(path),command=receipt['command'],exitCode=0)
report=dict(result='passed',historicalEvidencePreserved=True,historicalFilesVerified=len(index),changedSources=sorted(changed),
            unchangedSources=len(previous['sha256'])-len(changed),unchangedBinaries=len(previous['binarySha256']),
            referenceCommits=previous['referenceCommits'],privateRuntimeBinariesVerified=records,
            priorArtifactIndex=dict(path=str((prior/'artifact-index.json').relative_to(root)),sha256=sha(prior/'artifact-index.json')),
            reusedValidation=commands)
(out/'validation-reuse.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:report[key] for key in ['result','historicalFilesVerified','changedSources','unchangedSources','unchangedBinaries']},indent=2))
