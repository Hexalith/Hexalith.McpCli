#!/usr/bin/env python3
"""Exercise real enrollment, rejected inventory and failed semantic replay with temporary sample data."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def run(command, cwd, env, expected=0):
    result = subprocess.run(list(map(str, command)), cwd=cwd, env=env, capture_output=True, text=True)
    if result.returncode != expected:
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f'Process fixture command returned {result.returncode}, expected {expected}: {command}')
    return result


def enroll_fixture(project: ET.Element, package_id: str) -> None:
    """Select only the synthetic fixture in the temporary production manifest."""
    for parent in project.iter():
        for item in list(parent):
            if item.tag == 'PackageReference':
                marked = item.get('HexalithContracts', item.findtext('HexalithContracts', ''))
                if marked.casefold() == 'true':
                    parent.remove(item)
    ET.SubElement(ET.SubElement(project, 'ItemGroup'), 'PackageReference',
                  Include=package_id, HexalithContracts='true')


def fixture(repo: Path, artifact: Path):
    artifact = artifact.resolve(strict=True)
    package_id, version = 'Hexalith.McpCli.Sample.Contracts', '1.0.0'
    with tempfile.TemporaryDirectory(prefix='mcpcli-packaged-process-') as temporary:
        root = Path(temporary).resolve()
        # The synthetic receipt, inventory and flagged project exist only in this temporary repository.
        for name in ['src', 'references/Hexalith.Builds/Props', 'tools/conformance-vectors/v1']:
            shutil.copytree(repo / name, root / name, ignore=shutil.ignore_patterns('bin', 'obj', '.git', '__pycache__'))
        for name in ['Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props', 'global.json', '.editorconfig']:
            if (repo / name).exists():
                shutil.copy2(repo / name, root / name)
        host = root / 'tests/Hexalith.McpCli.ConformanceHost'
        host.mkdir(parents=True)
        shutil.copy2(repo / 'tests/Hexalith.McpCli.ConformanceHost/Program.cs', host / 'Program.cs')
        core = root / 'tests/Hexalith.McpCli.Core.Tests'
        core.mkdir(parents=True)
        for source in (repo / 'tests/Hexalith.McpCli.Core.Tests').glob('InventoryCoverage*.cs'):
            if source.name not in ('InventoryCoverageTests.cs', 'InventoryCoverageContractsAssembly.cs'):
                shutil.copy2(source, core / source.name)
        project = root / 'src/Hexalith.McpCli/Hexalith.McpCli.csproj'
        tree = ET.parse(project)
        enroll_fixture(tree.getroot(), package_id)
        tree.write(project, encoding='unicode')
        props = root / 'Directory.Packages.props'
        tree = ET.parse(props)
        ET.SubElement(ET.SubElement(tree.getroot(), 'ItemGroup'), 'PackageVersion', Include=package_id, Version=version)
        tree.write(props, encoding='unicode')
        env = {key: value for key, value in os.environ.items() if not key.startswith(('MCPCLI_', 'EVENTSTORE_'))}
        env['NUGET_PACKAGES'] = str(root / 'packages')
        run(['dotnet', 'restore', project, '-p:Configuration=Release', f'-p:RestoreAdditionalProjectSources={artifact.parent}'], root, env)
        directory = root / 'tools/conformance-vectors/v1/modules' / package_id
        directory.mkdir(parents=True)
        vectors = []
        for source in ['sample-command.json', 'sample-query.json', 'sample-rename.json']:
            destination = directory / source.replace('.json', '.vector.json')
            shutil.copy2(repo / 'tools/conformance-vectors/v1' / source, destination)
            vectors.append(destination)
        inventories = root / 'tools/inventory-coverage/v1'
        inventories.mkdir(parents=True)
        inventory = inventories / 'sample-approved.json'
        shutil.copy2(repo / 'tools/inventory-coverage/v1/sample-approved.json', inventory)
        accepted = inventories / 'sample-accepted-lint.json'
        accepted.write_text('[]')
        digest = 'sha512-' + base64.b64encode(hashlib.sha512(artifact.read_bytes()).digest()).decode('ascii')
        receipt = {'packageId': package_id, 'version': version, 'module': 'sample', 'artifactHash': digest,
                   'inventorySha256': hashlib.sha256(inventory.read_bytes()).hexdigest(),
                   'approvalReference': 'temporary synthetic sample fixture only; no owner release approval',
                   'vectorFilesSha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in vectors}}
        (directory / 'approval.json').write_text(json.dumps(receipt))
        output = root / 'positive'
        run([sys.executable, root / 'tools/conformance-vectors/v1/check_enrolled.py', '--output', output], root, env)
        report = json.loads((output / 'enrolled.json').read_text())
        if report['result'] != 'passed' or report['packages'] != [package_id] or len(report['results']) != 1:
            raise RuntimeError('Nonempty sample enrollment did not reach successful artifact verification.')
        verified = report['results'][0]
        if verified['candidateDependencyOverrides'] != []:
            raise RuntimeError('Enrolled verification must use the shipped dependency pins without candidate overrides.')
        if not verified['resolvedPackages'] or any(item['cacheContentHash'] != item['assetsHash'] or not item['artifactHash'].startswith('sha512-') for item in verified['resolvedPackages']):
            raise RuntimeError('Actual restored package identities/hashes were not retained.')
        for kind, source in [('inventory', inventory), ('acceptedLint', accepted)]:
            if verified['approvalInputs'][kind]['sha256'] != hashlib.sha256(source.read_bytes()).hexdigest():
                raise RuntimeError(f'{kind} input bytes were not bound to the verification receipt.')
        if not any(check['label'] == 'replay' and check['exitCode'] == 0 for check in verified['checks']):
            raise RuntimeError('Nonempty orchestration did not execute complete replay.')
        print(f'PASS nonempty enrollment: exact packaged sample, {len(verified["resolvedPackages"])} resolved packages, approval input hashes and complete replay.', flush=True)

        # Reach the real C# inventory adapter with valid vectors and a rejected decision.
        pending_inventory = inventories / 'sample-pending.json'
        pending = json.loads(inventory.read_text())
        pending['legacyRows'][0]['approval']['status'] = 'pending'
        pending_inventory.write_text(json.dumps(pending))
        rejected_output = root / 'rejected-inventory'
        rejected_output.mkdir()
        (rejected_output / 'verification.json').write_text('{"result":"passed"}')
        (rejected_output / 'artifact.sha512').write_text('stale successful artifact receipt')
        result = run([sys.executable, root / 'tools/conformance-vectors/v1/verify_artifact.py', '--artifact', artifact,
                      '--output', rejected_output, '--inventory', pending_inventory, '--accepted-lint', accepted,
                      '--expected-hash', digest, *vectors], root, env, expected=1)
        rejected = json.loads((rejected_output / 'verification.json').read_text())
        expected_diagnostic = str(rejected_output / 'inventory.input.json') + ":row L01: approval.status must be 'approved'; actual 'pending'."
        findings = json.loads((rejected_output / 'inventory.stdout.txt').read_text())
        if findings != [expected_diagnostic] or 'approval.status must be' not in result.stderr:
            raise RuntimeError('Rejected inventory did not expose its exact useful diagnostic: ' + result.stderr)
        if rejected['result'] != 'failed' or (rejected_output / 'artifact.sha512').exists():
            raise RuntimeError('A rejected inventory retained stale success evidence.')
        if not any(check['label'] == 'inventory' and check['exitCode'] == 1 for check in rejected['checks']):
            raise RuntimeError('The rejected inventory did not reach the real inventory checker.')
        if any(check['label'] == 'replay' for check in rejected['checks']):
            raise RuntimeError('Replay ran despite rejected inventory approval.')
        print('PASS pending inventory: exact approval diagnostic from the real checker; replay blocked and stale success/hash invalidated.', flush=True)

        # Keep the vector structurally valid while making one semantic assertion deliberately false.
        query = directory / 'sample-query.vector.json'
        document = json.loads(query.read_text())
        document['invocation']['assertions'][0]['value'] = 'deliberately false semantic assertion'
        query.write_text(json.dumps(document))
        failed_output = root / 'negative'
        failed_output.mkdir()
        (failed_output / 'verification.json').write_text('{"result":"passed"}')
        (failed_output / 'artifact.sha512').write_text('stale successful artifact receipt')
        result = run([sys.executable, root / 'tools/conformance-vectors/v1/verify_artifact.py', '--artifact', artifact,
                      '--output', failed_output, '--inventory', inventory, '--accepted-lint', accepted, '--expected-hash', digest, *vectors], root, env, expected=1)
        failed = json.loads((failed_output / 'verification.json').read_text())
        if failed['result'] != 'failed' or (failed_output / 'artifact.sha512').exists():
            raise RuntimeError('A failed semantic replay retained stale success evidence.')
        if 'assertion equals at /document/title' not in result.stderr or 'deliberately false semantic assertion' not in result.stderr:
            raise RuntimeError('Failed semantic replay did not expose useful captured diagnostics: ' + result.stderr)
        if not any(check['label'] == 'replay' and check['exitCode'] == 1 for check in failed['checks']):
            raise RuntimeError('The negative vector failed before reaching semantic replay.')
        print('PASS false semantic assertion: replay failed with useful diagnostics; stale success/hash invalidated.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    args = parser.parse_args()
    try:
        fixture(Path(__file__).resolve().parents[3], args.artifact)
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
