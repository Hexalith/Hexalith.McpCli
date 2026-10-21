#!/usr/bin/env python3
"""Check every production-enrolled package against its approved exact artifact and vectors."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from verify_artifact import restored_package, verify
from validate import _load_json


def artifact_for(assets: dict, package_id: str, receipt: dict) -> Path:
    matches = [(key, library) for key, library in assets['libraries'].items()
               if key.rsplit('/', 1)[0].casefold() == package_id.casefold() and library['type'] == 'package']
    if len(matches) != 1:
        raise RuntimeError(f'{package_id}: expected one exact restored package.')
    identity, library = matches[0]
    version = identity.rsplit('/', 1)[1]
    if receipt.get('packageId') != package_id or receipt.get('version') != version:
        raise RuntimeError(f'{package_id}: approval receipt does not match the restored package version.')
    if not isinstance(receipt.get('approvalReference'), str) or not receipt['approvalReference'].strip():
        raise RuntimeError(f'{package_id}: missing owning-maintainer approval reference.')
    artifact, restored = restored_package(assets, identity, library)
    if restored['artifactHash'] != receipt.get('artifactHash'):
        raise RuntimeError(f'{package_id}: restored bytes differ from the approved artifact hash.')
    return artifact


def approved_vectors(directory: Path, receipt: dict) -> list[Path]:
    vectors = sorted(directory.rglob('*.vector.json'))
    expected = receipt.get('vectorFilesSha256')
    if not vectors or not isinstance(expected, dict) or not expected:
        raise RuntimeError('Missing complete approved vector filename/SHA256 map.')
    actual = {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in vectors}
    if actual != expected:
        raise RuntimeError('Vector files differ from approval: added, removed or changed vector bytes.')
    return vectors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    args.output.mkdir(parents=True, exist_ok=True)
    status = {'result': 'pending', 'packages': [], 'results': []}
    report = args.output / 'enrolled.json'
    report.write_text(json.dumps(status, indent=2) + '\n')
    try:
        project = repo / 'src/Hexalith.McpCli/Hexalith.McpCli.csproj'
        evaluation = subprocess.run(['dotnet', 'msbuild', str(project), '-p:Configuration=Release', '-getItem:PackageReference'],
                                    cwd=repo, capture_output=True, text=True, check=True)
        packages = [p['Identity'] for p in json.loads(evaluation.stdout)['Items']['PackageReference']
                    if p.get('HexalithContracts', '').casefold() == 'true']
        status['packages'] = packages
        report.write_text(json.dumps(status, indent=2) + '\n')
        assets = json.loads((project.parent / 'obj/project.assets.json').read_text())
        results = []
        for package_id in packages:
            directory = repo / 'tools/conformance-vectors/v1/modules' / package_id
            receipt = _load_json(directory / 'approval.json')
            artifact = artifact_for(assets, package_id, receipt)
            module = receipt.get('module')
            if not isinstance(module, str) or not module or '/' in module or '\\' in module:
                raise RuntimeError(f'{package_id}: receipt requires a canonical module name.')
            vectors = approved_vectors(directory, receipt)
            accepted = repo / 'tools/inventory-coverage/v1' / (module + '-accepted-lint.json')
            results.append(verify(repo, artifact, vectors, args.output.resolve() / package_id,
                                  repo / 'tools/inventory-coverage/v1' / (module + '-approved.json'), receipt['artifactHash'], accepted if accepted.exists() else None, align_candidate_dependencies=False))
        args.output.mkdir(parents=True, exist_ok=True)
        status.update(result='passed', packages=packages, results=results)
        report.write_text(json.dumps(status, indent=2) + '\n')
        print(f'Validated {len(packages)} enrolled production package(s).')
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        status.update(result='failed', error=str(error))
        report.write_text(json.dumps(status, indent=2) + '\n')
        if isinstance(error, subprocess.CalledProcessError):
            for captured in [error.stdout, error.stderr]:
                if captured:
                    print(captured[-16000:], file=sys.stderr)
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
