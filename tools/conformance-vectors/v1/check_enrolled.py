#!/usr/bin/env python3
"""Check every production-enrolled package against its approved exact artifact and vectors."""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from verify_artifact import restored_package, verify
from validate import _load_json
from run_loopback import run_catalog


def artifact_for(assets: dict, package_id: str, receipt: dict) -> Path:
    if not isinstance(receipt, dict):
        raise RuntimeError(f'{package_id}: approval receipt must be a JSON object.')
    matches = [(key, library) for key, library in assets['libraries'].items()
               if key.rsplit('/', 1)[0].casefold() == package_id.casefold() and library['type'] == 'package']
    if len(matches) != 1:
        raise RuntimeError(f'{package_id}: expected one exact restored package.')
    identity, library = matches[0]
    version = identity.rsplit('/', 1)[1]
    approved_id = receipt.get('packageId')
    if not isinstance(approved_id, str) or approved_id.casefold() != package_id.casefold() or receipt.get('version') != version:
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


def approval_directory(modules: Path, package_id: str) -> Path:
    matches = [path for path in modules.iterdir() if path.is_dir() and path.name.casefold() == package_id.casefold()]
    if len(matches) != 1:
        raise RuntimeError(f'{package_id}: expected one approval directory (package IDs are case-insensitive).')
    return matches[0]


def approved_inventory(inventory: Path, receipt: dict) -> str:
    expected = receipt.get('inventorySha256')
    if not isinstance(expected, str) or re.fullmatch('[0-9a-f]{64}', expected) is None:
        raise RuntimeError('Approval receipt requires inventorySha256 as a lowercase SHA256 digest.')
    if hashlib.sha256(inventory.read_bytes()).hexdigest() != expected:
        raise RuntimeError('Inventory bytes differ from the approved inventorySha256.')
    return expected


def invalidate_children(output: Path) -> None:
    """An enrollment preflight must never leave a previous successful child receipt current."""
    for path in output.glob('*/artifact.sha512'):
        path.unlink()
    for path in output.glob('*/verification.json'):
        path.write_text(json.dumps({'result': 'invalidated', 'error': 'Enrollment preflight has not verified this package.'}, indent=2) + '\n')


def required_scope(path: Path, modules: set[str]) -> list[str]:
    document = _load_json(path)
    required = document.get('requiredModules') if isinstance(document, dict) else None
    if not isinstance(required, list) or not required or any(not isinstance(name, str) or not name for name in required) \
            or len(required) != len(set(required)):
        raise RuntimeError(f'{path}: /requiredModules must be a nonempty array of unique module names.')
    return sorted(set(required) - modules)


def production_replay(repo: Path, output: Path, results: list[dict], record_progress=None) -> dict:
    """Exercise the real combined manifest; independent artifact hosts remain a separate gate."""
    project = repo / 'tests/Hexalith.McpCli.ConformanceHost/Hexalith.McpCli.ConformanceHost.csproj'
    progress = {'result': 'pending', 'checks': []}

    def save():
        if record_progress is not None:
            record_progress(progress)

    try:
        for command, label in [
            (['dotnet', 'restore', str(project), '-p:ConformanceProduction=true'], 'production-restore'),
            (['dotnet', 'build', str(project), '--no-restore', '-c', 'Release', '-m:1', '-warnaserror',
              '-p:ConformanceProduction=true'], 'production-build')]:
            progress['phase'] = label
            check = {'command': command, 'result': 'running'}
            progress['checks'].append(check)
            save()
            result = subprocess.run(command, cwd=repo, capture_output=True, text=True)
            (output / (label + '.stdout.txt')).write_text(result.stdout)
            (output / (label + '.stderr.txt')).write_text(result.stderr)
            check.update(exitCode=result.returncode, result='passed' if result.returncode == 0 else 'failed')
            save()
            if result.returncode != 0:
                raise RuntimeError(f'{label} failed with exit {result.returncode}; see {output}: {result.stderr[-4000:]}')
        progress['phase'] = 'production-replay'
        save()
        host = project.parent / 'bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll'
        selections = []
        for receipt in results:
            root = output / receipt['packageId']
            inputs = receipt['retainedInputs']
            selections.append((root / inputs['artifact'], (receipt['packageId'], receipt['version']),
                               [root / path for path in inputs['vectors'].values()]))
            if set(inputs['vectors']) != set(receipt['vectors']):
                raise RuntimeError(f"{receipt['packageId']}: retained vector map differs from recorded verification hashes.")
            for source, path in inputs['vectors'].items():
                if hashlib.sha256((root / path).read_bytes()).hexdigest() != receipt['vectors'][source]:
                    raise RuntimeError(f"{root / path}: retained vector bytes differ from recorded verification hash.")
        with (output / 'production-replay.stdout.txt').open('w') as stdout, \
                (output / 'production-replay.stderr.txt').open('w') as stderr:
            try:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    discovered = run_catalog(host, selections, assets_path=project.parent / 'obj/project.assets.json',
                                evidence_dir=output / 'production-observations',
                                expected_modules={receipt['packageId']: receipt['approvedModule'] for receipt in results})
            except Exception as error:
                stderr.write(str(error) + '\n')
                raise
        progress.update(result='passed', packageCount=len(selections),
                        operationCount=sum(len(result['operations']) for result in results), **discovered)
        save()
        return progress
    except Exception as error:
        progress.update(result='failed', error=str(error))
        save()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--local', action='store_true', help='collect available-package evidence; never grants full-v1 acceptance')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    args.output.mkdir(parents=True, exist_ok=True)
    status = {'result': 'pending', 'fullV1Accepted': False, 'packages': [], 'results': []}
    report = args.output / 'enrolled.json'
    report.write_text(json.dumps(status, indent=2) + '\n')
    try:
        invalidate_children(args.output)
        required_scope(repo / 'tools/conformance-vectors/v1/v1-scope.json', set())
        for stale in (args.output / 'production-observations').glob('*.json'):
            stale.unlink()
        project = repo / 'src/Hexalith.McpCli/Hexalith.McpCli.csproj'
        evaluation = subprocess.run(['dotnet', 'msbuild', str(project), '-p:Configuration=Release', '-getItem:PackageReference'],
                                    cwd=repo, capture_output=True, text=True, check=True)
        packages = [p['Identity'] for p in json.loads(evaluation.stdout)['Items']['PackageReference']
                    if any(name.casefold() == 'hexalithcontracts' and value.casefold() == 'true'
                           for name, value in p.items())]
        status['packages'] = packages
        report.write_text(json.dumps(status, indent=2) + '\n')
        assets = json.loads((project.parent / 'obj/project.assets.json').read_text())
        results = []
        for package_id in packages:
            directory = approval_directory(repo / 'tools/conformance-vectors/v1/modules', package_id)
            receipt = _load_json(directory / 'approval.json')
            artifact = artifact_for(assets, package_id, receipt)
            module = receipt.get('module')
            if not isinstance(module, str) or not module or '/' in module or '\\' in module:
                raise RuntimeError(f'{package_id}: receipt requires a canonical module name.')
            vectors = approved_vectors(directory, receipt)
            inventory = repo / 'tools/inventory-coverage/v1' / (module + '-approved.json')
            inventory_hash = approved_inventory(inventory, receipt)
            vector_hashes = {str((directory / name).resolve()): digest for name, digest in receipt['vectorFilesSha256'].items()}
            accepted = repo / 'tools/inventory-coverage/v1' / (module + '-accepted-lint.json')
            results.append(verify(repo, artifact, vectors, args.output.resolve() / package_id,
                                  inventory, receipt['artifactHash'], accepted if accepted.exists() else None,
                                  align_candidate_dependencies=False, expected_inventory_hash=inventory_hash,
                                  expected_vector_hashes=vector_hashes))
            results[-1]['approvedModule'] = module
        args.output.mkdir(parents=True, exist_ok=True)
        if not packages:
            raise RuntimeError('Production manifest has no enrolled Contracts packages.')
        status.update(results=results)
        report.write_text(json.dumps(status, indent=2) + '\n')
        def record_production(progress):
            status['productionReplay'] = progress
            report.write_text(json.dumps(status, indent=2) + '\n')

        status['productionReplay'] = production_replay(repo, args.output.resolve(), results, record_production)
        missing = required_scope(repo / 'tools/conformance-vectors/v1/v1-scope.json', set(status['productionReplay']['modules']))
        status.update(missingRequiredModules=missing, fullV1Accepted=not missing and not args.local)
        if missing and not args.local:
            raise RuntimeError('Full-v1 gate: missing required production module(s): ' + ', '.join(missing))
        status.update(result='local-only' if args.local else 'passed', packages=packages, results=results)
        report.write_text(json.dumps(status, indent=2) + '\n')
        print(f'Validated {len(packages)} enrolled production package(s); full-v1 acceptance: {status["fullV1Accepted"]}.')
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
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
