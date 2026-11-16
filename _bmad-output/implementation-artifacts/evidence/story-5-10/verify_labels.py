#!/usr/bin/env python3
"""Verify five chained README-only patches; completion requires authorized integration."""
import argparse
import importlib.util
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
E = Path('_bmad-output/implementation-artifacts/evidence/story-5-10')


def load(root,name,path):
    spec = importlib.util.spec_from_file_location(name,root/path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = load(ROOT,'owner510labels',E/'verify_amendment.py')
B = V.B
require,read_json = V.require,V.read_json
L57 = load(ROOT,'prior57labels510',B.ART/'evidence/story-5-7/verify_labels.py')


def checked_file(root,item):
    require(isinstance(item,dict) and isinstance(item.get('path'),str),'label artifact path missing')
    path = Path(item['path'])
    require(not path.is_absolute() and (root/path).resolve().is_relative_to(root),'label artifact path escapes repository')
    data = (root/path).read_bytes()
    require(B.sha(data) == item.get('sha256'),f'label artifact hash mismatch: {path}')
    return data


def check_delivery(root,register,repository,before,after):
    require(register.get('state') == 'integrated','completion requires integrated PS06/PS07/PS12/PS13/PS14 labels')
    auth = register.get('deliveryAuthorization')
    require(isinstance(auth,dict) and all(V.nonblank(auth.get(k)) for k in ['exactWords','source','approvedOn'])
            and auth['exactWords'].strip().casefold() == 'authorize',
            'completion requires separate explicit authorize instruction for label delivery')
    owner,name = Path(repository['ownerCheckout']),repository['name']
    integration = repository.get('integration')
    require(isinstance(integration,dict) and re.fullmatch('[0-9a-f]{40}',integration.get('commit','')) is not None,
            f'{name}: completion requires canonical integrated label commit')
    revision = integration['commit']
    parent = B.git(owner,'show',revision+'^:README.md')
    delivered = B.git(owner,'show',revision+':README.md')
    before_section,after_section = B.compatibility_section(before),B.compatibility_section(after)
    require(B.compatibility_section(parent) == before_section,f'{name}: parent compatibility section differs from authorized before bytes')
    require(B.compatibility_section(delivered) == after_section and delivered == parent.replace(before_section,after_section,1),
            f'{name}: integrated README bytes mismatch; expected only the authorized section swap')
    B.git(owner,'merge-base','--is-ancestor',revision,'origin/main')
    require(B.git(owner,'diff','--name-only',revision+'^',revision).decode().splitlines() == ['README.md'],f'{name}: delivered commit is not README-only')
    require(integration.get('commitSha256') == B.sha(B.git(owner,'cat-file','commit',revision)),f'{name}: integrated commit hash mismatch')
    current = B.git(owner,'show','origin/main:README.md')
    require(B.compatibility_section(current) == B.compatibility_section(after),f'{name}: current origin/main does not cite exact successor labels')
    inv_revision = register.get('inventoryRevision')
    require(isinstance(inv_revision,str) and re.fullmatch('[0-9a-f]{40}',inv_revision) is not None,'completion requires canonical integrated inventory revision')
    B.git(root,'merge-base','--is-ancestor',inv_revision,'origin/main')
    for path in [*[m['new'] for m in B.MODULES.values()],E/'approval.json']:
        digest = B.sha((root/path).read_bytes())
        require(B.sha(B.git(root,'show',f'{inv_revision}:{path}')) == digest and B.sha(B.git(root,'show',f'origin/main:{path}')) == digest,
                f'{path}: published bytes differ from approved candidate')


def verify(root,completion=False,owner_checked=False):
    root = Path(root).resolve()
    register = read_json(root/E/'labels.json')
    require(register.get('schemaVersion') == '1.0.0','unsupported label register schema')
    require(register.get('state') in {'candidate-pending-owner-approval-and-delivery','integrated'},'invalid label register state')
    completion = completion or register['state'] == 'integrated' or V.completion_requested(root,False)
    if completion and not owner_checked: V.verify_owner_packet(root,True)
    inventory = {str(m['new']):B.sha((root/m['new']).read_bytes()) for m in B.MODULES.values()}
    expected,writes = B.label_candidate(root,inventory)
    require(register.get('predecessor') == expected['predecessor'],'Story 5.9 label predecessor chain mismatch')
    require(register.get('priorRows') == expected['priorRows'],'Story 5.7 prior label rows hash mismatch')
    require(register.get('inventoryArtifacts') == inventory,'labels bind wrong successor inventory hashes')
    rows,repositories = register.get('rows'),register.get('repositories')
    require(isinstance(rows,list) and len(rows) == 5 and all(isinstance(r,dict) for r in rows)
            and {r.get('id') for r in rows} == {'PS06','PS07','PS12','PS13','PS14'},'label row coverage/duplicate mismatch')
    require(isinstance(repositories,list) and len(repositories) == 2 and all(isinstance(r,dict) for r in repositories)
            and {r.get('name') for r in repositories} == {'chatbot','memories'},'label repository coverage/duplicate mismatch')
    for row in rows:
        target = next(r for r in expected['rows'] if r['id'] == row['id'])
        require(row == target,f'{row["id"]}: successor citation/hash/anchor/surface/removal gate mismatch')
        text = row['label']['text']
        require('[technical-tools inventory 1.0.3]' in text and row['gate'] in text,f'{row["id"]}: technical authority or gate lost')
        if row['id'] == 'PS14':
            require(all(s in text for s in ['T01–T04','1.2.0','Never counted as retired','independent safety gates']),
                    'PS14: mode inventory or retained exemption lost')
        if row['id'] in {'PS06','PS07'}:
            require('necessary but not sufficient' in text,f'{row["id"]}: HTTP prerequisite lost')
    for repository in repositories:
        name = repository['name']
        target = next(r for r in expected['repositories'] if r['name'] == name)
        require({k:v for k,v in repository.items() if k != 'integration'} == {k:v for k,v in target.items() if k != 'integration'},f'{name}: owner/base/README patch register mismatch')
        ownership_checkout = Path(repository['ownerCheckout']) if completion else root/B.repo(name)
        if not completion:
            declared = B.git(root,'config','--file',str(root/'.gitmodules'),'--get',f'submodule.{B.repo(name)}.path').decode().strip()
            require(declared == str(B.repo(name)),f'{name}: ownership reference is not root-declared')
        origin = B.git(ownership_checkout,'remote','get-url','origin').decode().strip()
        require(L57.github_repository(origin) == L57.github_repository(repository['repository']),f'{name}: checkout origin differs from owning repository')
        for key in ['before','after','patch']:
            require(checked_file(root,repository[key]) == writes[Path(repository[key]['path'])],f'{name}: patch/section is not isolated exact README diff')
        before = B.blob(root,name,'README.md')
        before_section,after_section = checked_file(root,repository['before']),checked_file(root,repository['after'])
        after = before.replace(before_section,after_section)
        require(B.sha(after) == repository['readme']['afterSha256'] and b'They are not retired' in after_section,f'{name}: reconstructed README/retention mismatch')
        if completion: check_delivery(root,register,repository,before,after)
        else:
            require(register.get('deliveryAuthorization') is None and register.get('inventoryRevision') is None and repository.get('integration') is None,'pending labels must not claim authorization or integration')
    return completion


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--approved-completion',action='store_true')
    args = parser.parse_args(argv)
    try:
        completed = verify(args.root,args.approved_completion)
        decision = read_json(args.root/E/'approval.json')['decision']
    except (ValueError,KeyError,TypeError,OSError,IndexError,UnicodeError) as error:
        print(f'FAIL: {error}',file=sys.stderr)
        return 1
    remaining = 'delivery integration pending' if decision == 'approved' else 'approval and delivery integration pending'
    print('PASS: Story 5.9 register chain; PS06/PS07/PS12/PS13/PS14 in two README-only patches; '+('integrated delivery verified' if completed else 'candidate only; owner decision: '+decision+'; '+remaining))
    return 0


if __name__ == '__main__':
    sys.exit(main())
