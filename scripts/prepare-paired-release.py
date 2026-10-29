#!/usr/bin/env python3
"""Prepare one immutable local package pair; this script has no publication path."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from paired_release import PAIR, digest, module, packages, source, write_new


def prepare(selection_path, output, local=False):
    selection = json.loads(Path(selection_path).read_text(encoding='utf-8'))
    before = source()
    if selection.get('schema') != 'mcpcli-version-selection/v1' or selection.get('source_sha') != before['source_sha']:
        raise ValueError('Version selection does not match the exact source SHA.')
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('Staging/evidence already exists; preserve it and select a fresh output directory.')
    output.mkdir(parents=True)
    if selection.get('release') is False and selection.get('version') is None:
        write_new(output / 'no-release.json', {**selection, 'status': 'no-release'})
        return
    if selection.get('release') is not True:
        raise ValueError('Invalid semantic-release selection.')
    version = selection['version']
    module('release-request').validate_version(version)
    staging = output / 'packages'
    evidence = output / 'evidence'
    evidence.mkdir()

    def command(name, arguments, **kwargs):
        result = subprocess.run([str(item) for item in arguments], capture_output=True, **kwargs)
        (evidence / f'{name}.stdout.txt').write_bytes(result.stdout)
        (evidence / f'{name}.stderr.txt').write_bytes(result.stderr)
        write_new(evidence / f'{name}.command.json', {'argv': [str(item) for item in arguments], 'exit_code': result.returncode})
        result.check_returncode()

    def gate(name):
        command(name, [sys.executable, 'scripts/verify-release-source.py', '--staging', '--output', evidence / f'{name}.json',
                       before['source_sha'], 'refs/heads/main', 'paired'])

    if not local:
        gate('source-before')
    staging.mkdir()
    flags = ['-p:IncludeSourceRevisionInInformationalVersion=false', f'-p:Version={version}', f'-p:InformationalVersion={version}', f'-p:RepositoryCommit={before["source_sha"]}']
    command('restore', ['dotnet', 'restore', 'Hexalith.McpCli.slnx', *flags])
    command('build', ['dotnet', 'build', 'Hexalith.McpCli.slnx', '--no-restore', '--configuration', 'Release', '-warnaserror', *flags])
    manifest = json.loads(Path('tools/release-packages.json').read_text())['packages']
    if [item['id'] for item in manifest] != PAIR:
        raise ValueError('The release manifest must declare exactly the approved pair.')
    for item in manifest:
        command('pack-' + item['id'], ['dotnet', 'pack', item['project'], '--no-build', '--configuration', 'Release',
                                     '--output', staging, *flags])
    command('validate', [sys.executable, 'scripts/validate-release-packages.py', '--source-sha', before['source_sha'],
                         '--output', evidence / 'validation.json', staging, version, 'paired'])
    with tempfile.TemporaryDirectory(prefix='mcpcli-paired-consumer-') as temporary:
        private = Path(temporary)
        consumer = private / 'consumer'
        consumer_env = {key: value for key, value in os.environ.items() if not key.startswith(('NUGET_', 'DOTNET_'))}
        consumer_env.update({'DOTNET_CLI_HOME': str(private / 'dotnet-home'), 'DOTNET_NOLOGO': '1',
                             'DOTNET_CLI_TELEMETRY_OPTOUT': '1', 'DOTNET_SKIP_FIRST_TIME_EXPERIENCE': '1'})
        compiler = consumer / 'build.log'
        try:
            command('consumer', ['bash', 'scripts/smoke-bootstrap-consumer.sh', version, staging, consumer], env=consumer_env)
        finally:
            if compiler.is_file():
                (evidence / 'consumer-build.log').write_bytes(compiler.read_bytes())
        if not compiler.is_file():
            raise ValueError('The staged consumer did not retain its compiler/analyzer log.')
    write_new(evidence / 'consumer.json', {'schema': 'mcpcli-paired-consumer/v1', 'status': 'passed',
              'source_sha': before['source_sha'], 'version': version, 'packages': packages(staging, version),
              'compiler_sha256': digest(evidence / 'consumer-build.log'),
              'command_sha256': digest(evidence / 'consumer.command.json')})
    after = source()
    if after != before:
        raise ValueError('Source SHA or working-tree state changed during preparation.')
    if not local:
        gate('source-after')
    if json.loads((evidence / 'validation.json').read_text())['packages'] != packages(staging, version):
        raise ValueError('Staged package bytes changed after validation.')
    receipt = {'schema': 'mcpcli-paired-preparation/v1', **before, 'version': version,
               'eligibility': 'local-only' if local else 'current-main', 'packages': packages(staging, version),
               'evidence': {path.name: digest(path) for path in sorted(evidence.iterdir())}}
    write_new(output / 'prepared.json', receipt)
    print(json.dumps(receipt))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--local', action='store_true', help='Collect local-only checks; never eligible for accepted staging.')
    args = parser.parse_args()
    try:
        prepare(args.selection, args.output, args.local)
        return 0
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f'Paired preparation failed: {module("verify-release-source").failure_detail(error)}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
