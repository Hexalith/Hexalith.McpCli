#!/usr/bin/env python3
"""Recheck the recorded local package in an isolated copy of the generic host."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

CODE_PATHS = [
    'src', '.editorconfig', 'Directory.Build.props', 'Directory.Build.targets',
    'Directory.Packages.props', 'global.json', 'references/Hexalith.Builds',
    'tests/Hexalith.McpCli.ConformanceHost/Program.cs',
    'tools/conformance-vectors/v1/validate.py', 'tools/conformance-vectors/v1/schema.json',
    'tools/conformance-vectors/v1/run_loopback.py', 'tools/conformance-vectors/v1/requirements.txt',
]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def check_manifest(root, manifest):
    for name, expected in json.loads(manifest.read_text()).items():
        source = root / name
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f'Recorded input drift: {source}')


def check_recorded_inputs(repo, parties_root, evidence):
    binding = json.loads((evidence / 'maintainer-vector-approval.json').read_text())
    for name, key in [('source-files.sha256.json', 'sourceManifestSha256'),
                      ('vector-files.sha256.json', 'vectorManifestSha256'),
                      ('verifier-files.sha256.json', 'verifierManifestSha256')]:
        require(hashlib.sha256((evidence / name).read_bytes()).hexdigest() == binding[key],
                f'Recorded manifest hash drift: {name}')
    artifact = evidence / 'artifacts/Hexalith.Parties.Contracts.0.0.0-story49.nupkg'
    receipt_hash = (evidence / 'artifact.sha512').read_text().split()[0]
    require(receipt_hash == binding['artifactHash'], 'Recorded artifact receipt hash drift.')
    actual_hash = 'sha512-' + base64.b64encode(hashlib.sha512(artifact.read_bytes()).digest()).decode('ascii')
    require(actual_hash == receipt_hash, 'The immutable scratch artifact changed.')
    check_manifest(parties_root, evidence / 'source-files.sha256.json')
    check_manifest(parties_root, evidence / 'vector-files.sha256.json')
    expected_vectors = set(json.loads((evidence / 'vector-files.sha256.json').read_text()))
    live_vectors = {str(path.relative_to(parties_root)) for path in
                    (parties_root / 'tests/conformance-vectors/mcpcli-v1').glob('*.json')}
    if live_vectors != expected_vectors:
        raise RuntimeError('Recorded vector file set drift.')
    check_manifest(evidence, evidence / 'verifier-files.sha256.json')
    approval = json.loads((evidence / 'maintainer-vector-approval.json').read_text())
    validator = repo / 'tools/conformance-vectors/v1/validate.py'
    if hashlib.sha256(validator.read_bytes()).hexdigest() != approval['validatorFileSha256']:
        raise RuntimeError(f'Recorded validator hash drift: {validator}')
    revision = approval['validatorRevision']
    resolved = subprocess.run(['git', 'rev-parse', revision + '^{commit}'], cwd=repo,
                              capture_output=True, text=True, check=True).stdout.strip()
    if resolved != revision:
        raise RuntimeError('The declared verifier revision must be a full commit identifier.')
    subprocess.run(['git', 'diff', '--exit-code', '--ignore-submodules=none', revision, '--', *CODE_PATHS],
                   cwd=repo, capture_output=True, text=True, check=True)
    untracked = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard', '--', *CODE_PATHS],
                               cwd=repo, capture_output=True, text=True, check=True).stdout
    if untracked.strip():
        raise RuntimeError(f'Unrecorded host/validator files relative to {revision}: {untracked.strip()}')


def runtime_environment(scratch):
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('MCPCLI_', 'EVENTSTORE_'))}
    env['MCPCLI_CONFORMANCE_PROFILE_PATH'] = str(scratch / 'mcpcli.json')
    return env


def verify(repo, parties_root, evidence):
    check_recorded_inputs(repo, parties_root, evidence)
    artifact = evidence / 'artifacts/Hexalith.Parties.Contracts.0.0.0-story49.nupkg'
    expected_hash = (evidence / 'artifact.sha512').read_text().split()[0]
    assets = repo / 'src/Hexalith.McpCli/obj/project.assets.json'
    assets_before = assets.read_bytes() if assets.exists() else None
    with zipfile.ZipFile(artifact) as package:
        nuspec = ET.fromstring(package.read(next(n for n in package.namelist() if n.endswith('.nuspec'))))
        eventstore = next(d.attrib['version'] for d in nuspec.iter() if d.tag.endswith('dependency') and d.attrib.get('id') == 'Hexalith.EventStore.Contracts')
        commons = next(d.attrib['version'] for d in nuspec.iter() if d.tag.endswith('dependency') and d.attrib.get('id') == 'Hexalith.Commons.UniqueIds')
    pending_outputs = {}
    with tempfile.TemporaryDirectory(prefix='hexalith-story49-') as tmp:
        scratch = Path(tmp)
        env = runtime_environment(scratch)
        for name in ['src', 'references/Hexalith.Builds/Props']:
            shutil.copytree(repo / name, scratch / name, ignore=shutil.ignore_patterns('bin', 'obj', '.git'))
        for name in ['Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props', 'global.json', '.editorconfig']:
            if (repo / name).exists():
                shutil.copy2(repo / name, scratch / name)
        props = scratch / 'Directory.Packages.props'
        props.write_text(props.read_text().replace('</Project>', '<ItemGroup><PackageVersion Update="Hexalith.Parties.Contracts" Version="0.0.0-story49" /></ItemGroup></Project>'))
        host = scratch / 'host'
        host.mkdir()
        shutil.copy2(evidence / 'ScratchProgram.cs', host / 'Program.cs')
        (host / 'ScratchHost.csproj').write_text('''<Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup><OutputType>Exe</OutputType><IsPackable>false</IsPackable><RequireContractsFlag>true</RequireContractsFlag></PropertyGroup>
    <ItemGroup><ProjectReference Include="../src/Hexalith.McpCli/Hexalith.McpCli.csproj" />
    <PackageReference Include="Hexalith.Parties.Contracts" HexalithContracts="true" /></ItemGroup>
    <Import Project="../src/Hexalith.McpCli/Build/ModuleAssemblyManifest.targets" /></Project>''')
        common = [f'-p:HexalithEventStoreVersion={eventstore}', f'-p:HexalithCommonsVersion={commons}']
        subprocess.run(['dotnet', 'restore', 'host/ScratchHost.csproj', *common,
                        f'-p:RestoreAdditionalProjectSources={artifact.parent}', f'-p:RestorePackagesPath={scratch / "packages"}'], cwd=scratch, env=env, check=True)
        subprocess.run(['dotnet', 'build', 'host/ScratchHost.csproj', '--no-restore', '-c', 'Release', '-m:1', *common,
                        f'-p:RestorePackagesPath={scratch / "packages"}'], cwd=scratch, env=env, check=True)
        entry = ['dotnet', str(host / 'bin/Release/net10.0/ScratchHost.dll')]
        catalog = subprocess.run([*entry, '--full-catalog'], capture_output=True, text=True, env=env, check=True)
        require(not catalog.stderr, f'Catalog emitted diagnostics: {catalog.stderr}')
        snapshot = json.loads(catalog.stdout)
        require(snapshot['diagnostics'] == [], f'Catalog diagnostics: {snapshot["diagnostics"]}')
        expected = json.loads((evidence / 'expected-operations.json').read_text())
        require([op['name'] for module in snapshot['modules'] for op in module['operations']] == expected,
                'Catalog command coverage differs from the recorded operations.')
        pending_outputs['catalog.json'] = catalog.stdout
        pending_outputs['catalog.stderr.txt'] = catalog.stderr
        catalog_checks = [{'command': [*entry, '--full-catalog'], 'exitCode': 0, 'stdout': 'catalog.json', 'stderr': 'catalog.stderr.txt'}]
        discovery = [('manifest-catalog', ['--manifest-catalog']), ('modules', ['modules', '--strict']),
                     ('operations', ['operations', 'parties', '--strict'])]
        discovery.extend((operation.split('.', 1)[1], ['describe', operation, '--lint', '--strict']) for operation in expected)
        for label, arguments in discovery:
            result = subprocess.run([*entry, *arguments], capture_output=True, text=True, env=env, check=True)
            require(not result.stderr, f'{label} emitted diagnostics: {result.stderr}')
            if arguments[0] == 'describe':
                require(json.loads(result.stdout)['lintFindings'] == [], f'{label} has lint findings.')
            pending_outputs[label + '.json'] = result.stdout
            pending_outputs[label + '.stderr.txt'] = result.stderr
            catalog_checks.append({'command': [*entry, *arguments], 'exitCode': result.returncode,
                                   'stdout': label + '.json', 'stderr': label + '.stderr.txt'})
        pending_outputs['catalog-checks.json'] = json.dumps(catalog_checks, indent=2) + '\n'
        smoke = scratch / 'command-routing-smoke'
        smoke.mkdir()
        for original in sorted((parties_root / 'tests/conformance-vectors/mcpcli-v1').glob('*.json')):
            vector = json.loads(original.read_text())
            vector['postconditions'] = []
            (smoke / original.name).write_text(json.dumps(vector, indent=2) + '\n')
        print('Command-routing smoke: temporary copies omit only unavailable Query postconditions; no semantic-effects claim.', flush=True)
        subprocess.run([sys.executable, 'tools/conformance-vectors/v1/run_loopback.py', '--host', str(host / 'bin/Release/net10.0/ScratchHost.dll'),
                        '--artifact', str(artifact), '--expected-package-id', 'Hexalith.Parties.Contracts',
                        '--expected-package-version', '0.0.0-story49', *map(str, sorted(smoke.glob('*.json')))], cwd=repo, env=env, check=True)
        restored_hash = (scratch / 'packages/hexalith.parties.contracts/0.0.0-story49/hexalith.parties.contracts.0.0.0-story49.nupkg.sha512').read_text().strip()
        require('sha512-' + restored_hash == expected_hash, 'Restored artifact identity differs from the receipt.')
    validation = subprocess.run([sys.executable, 'tools/conformance-vectors/v1/validate.py', '--artifact', str(artifact),
                    '--expected-package-id', 'Hexalith.Parties.Contracts', '--expected-package-version', '0.0.0-story49',
                    '--operations-file', str(evidence / 'expected-operations.json'),
                    *map(str, sorted((parties_root / 'tests/conformance-vectors/mcpcli-v1').glob('*.json')))], cwd=repo, env=env, capture_output=True, text=True, check=True)
    pending_outputs['vector-validation.txt'] = validation.stdout
    assets_after = assets.read_bytes() if assets.exists() else None
    require(assets_after == assets_before, 'Production McpCli restored assets changed.')
    for name, content in pending_outputs.items():
        (evidence / name).write_text(content)
    print(validation.stdout, end='')
    print('Scratch Catalog, lint, strict, command-routing smoke, restored artifact identity and four-vector coverage passed; production assets unchanged.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mcpcli-root', type=Path, default=Path(__file__).resolve().parents[5])
    parser.add_argument('--parties-root', type=Path, default=Path('/home/administrator/projects/hexalith/parties'))
    args = parser.parse_args()
    try:
        verify(args.mcpcli_root.resolve(), args.parties_root.resolve(), Path(__file__).resolve().parent)
    except subprocess.CalledProcessError as error:
        command = shlex.join(map(str, error.cmd)) if isinstance(error.cmd, (list, tuple)) else str(error.cmd)
        print(f'Command failed ({error.returncode}): {command}', file=sys.stderr)
        for captured in [error.stdout, error.stderr]:
            if captured:
                print(captured, end='' if captured.endswith('\n') else '\n', file=sys.stderr)
        return error.returncode or 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
