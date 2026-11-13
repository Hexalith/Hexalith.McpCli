#!/usr/bin/env python3
"""Check the chained PS10/PS11 README citation patch; never apply or deliver it."""
import argparse
import importlib.util
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
E = Path('_bmad-output/implementation-artifacts/evidence/story-5-8')


def load(root,name,path):
    spec = importlib.util.spec_from_file_location(name,root/path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = load(ROOT,'owner58labels',E/'verify_amendment.py')
B = V.B
L57 = load(ROOT,'prior57labels',B.ART/'evidence/story-5-7/verify_labels.py')
require, read_json = V.require, V.read_json


def checked_file(root,item):
    require(isinstance(item,dict) and isinstance(item.get('path'),str), 'label artifact path missing')
    path = Path(item['path'])
    require(not path.is_absolute() and (root/path).resolve().is_relative_to(root), 'label path escapes repository')
    data = (root/path).read_bytes()
    require(B.sha(data) == item.get('sha256'), f'label artifact hash mismatch: {path}')
    return data


def verify(root,completion=False,owner_checked=False):
    root = Path(root).resolve()
    register = read_json(root/E/'labels.json')
    require(register.get('schemaVersion') == '1.0.0', 'unsupported label register schema')
    require(register.get('state') in {'candidate-pending-owner-approval-and-delivery','integrated'}, 'invalid label register state')
    completion = completion or register.get('state') == 'integrated' or V.completion_requested(root,False)
    if completion and not owner_checked:
        V.verify_owner_packet(root,True)
    prior_path = B.ART/'evidence/story-5-7/labels.json'
    require(register.get('predecessor') == {'path':str(prior_path),'sha256':B.sha((root/prior_path).read_bytes())}, 'Story 5.7 label predecessor chain mismatch')
    prior = read_json(root/prior_path)
    old_rows = [r for r in prior['rows'] if r['repository'] == 'folders']
    rows = register.get('rows')
    require(isinstance(rows,list) and len(rows) == 2 and all(isinstance(r,dict) for r in rows) and {r['id'] for r in rows} == {'PS10','PS11'}, 'Folders PS10/PS11 label coverage/duplicate mismatch')
    inventory_hash = B.sha((root/B.NEW).read_bytes())
    require(register.get('inventoryArtifacts') == {str(B.NEW):inventory_hash}, 'labels bind wrong Folders inventory hash')
    repo = register.get('repository')
    require(isinstance(repo,dict),'Folders label repository must be an object')
    require(repo.get('name') == 'folders' and repo.get('repository') == 'https://github.com/Hexalith/Hexalith.Folders' and repo.get('baseRevision') == B.LABEL_PIN, 'Folders label repository/base mismatch')
    owner = Path(repo['ownerCheckout'])
    origin = B.git(owner,'remote','get-url','origin').decode().strip()
    require(L57.github_repository(origin) == 'hexalith/hexalith.folders', 'folders: checkout origin does not match owning repository')
    before_section,after_section,patch = (checked_file(root,repo[k]) for k in ['before','after','patch'])
    before = B.git(owner,'show',B.LABEL_PIN+':README.md')
    expected,files = B.label_candidate(root,inventory_hash)
    require(repo['readme'] == expected['repository']['readme'] and before_section == files['README.before.section.md'] and after_section == files['README.after.section.md'], 'folders: committed base or candidate README hash mismatch')
    require(patch == files['README.patch'] and patch.startswith(b'--- a/README.md\n+++ b/README.md\n'), 'folders: patch is not exact README-only citation diff')
    for row in rows:
        key = row['id']
        old = next(r for r in old_rows if r['id'] == key)
        target = next(r for r in expected['rows'] if r['id'] == key)
        require(row.get('repository') == 'folders' and row.get('surface') == old['surface'] and row.get('gate') == old['gate'], f'{key}: surface, owner or removal gate changed')
        require(row['label'] == target['label'], f'{key}: version/hash/anchor/citation differs from Folders 1.1.0')
        text = row['label']['text']
        require('[technical-tools inventory 1.0.3]' in text and old['gate'] in text and 'Folders inventory SHA-256: `'+inventory_hash+'`.' in text, f'{key}: retained technical authority or successor hash missing')
    after = before.replace(before_section,after_section)
    require(B.compatibility_section(after) == after_section and b'They are not retired' in after_section, 'folders: compatibility retention semantics missing')
    if completion:
        require(register.get('state') == 'integrated', 'completion requires integrated Folders PS10/PS11 labels')
        auth = register.get('deliveryAuthorization')
        require(isinstance(auth,dict) and all(V.nonblank(auth.get(k)) for k in ['exactWords','source','approvedOn']), 'completion requires separate explicit label delivery authorization')
        integration = repo.get('integration')
        require(isinstance(integration,dict) and re.fullmatch('[0-9a-f]{40}',integration.get('commit','')) is not None, 'folders: completion requires canonical integrated label commit')
        revision = integration['commit']
        require(B.git(owner,'show',revision+':README.md') == after, 'folders: integrated README bytes differ from candidate')
        B.git(owner,'merge-base','--is-ancestor',revision,'origin/main')
        require(B.git(owner,'diff','--name-only',revision+'^',revision).decode().splitlines() == ['README.md'], 'folders: delivered commit is not README-only')
        require(integration.get('commitSha256') == B.sha(B.git(owner,'cat-file','commit',revision)), 'folders: integrated commit byte hash mismatch')
        inv_revision = register.get('inventoryRevision','')
        require(isinstance(inv_revision,str) and re.fullmatch('[0-9a-f]{40}',inv_revision) is not None, 'completion requires canonical integrated inventory revision')
        B.git(root,'merge-base','--is-ancestor',inv_revision,'origin/main')
        for path in [B.NEW,E/'approval.json']:
            digest = B.sha((root/path).read_bytes())
            require(B.sha(B.git(root,'show',f'{inv_revision}:{path}')) == digest and B.sha(B.git(root,'show',f'origin/main:{path}')) == digest, f'{path}: published artifact differs from owner-approved bytes')
    else:
        require(register.get('inventoryRevision') is None and register.get('deliveryAuthorization') is None and repo.get('integration') is None, 'pending label packet must not claim integration or delivery authorization')
    current = B.git(owner,'show','origin/main:README.md')
    try:
        current_section = B.compatibility_section(current)
    except ValueError:
        current_section = None
    if current_section != (after_section if completion else before_section):
        print('reported: folders: current origin/main compatibility labels differ from '+('delivered' if completion else 'prepared base')+' candidate',file=sys.stderr)
    return completion


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--approved-completion',action='store_true')
    args = parser.parse_args(argv)
    try:
        completed = verify(args.root,args.approved_completion)
    except (ValueError,KeyError,TypeError,OSError,IndexError) as error:
        print(f'FAIL: {error}',file=sys.stderr)
        return 1
    print('PASS: Story 5.7 register chain; PS10/PS11 Folders 1.1.0 README-only citation patch; '+('integrated delivery verified' if completed else 'candidate only; owner approval and delivery pending'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
