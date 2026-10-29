#!/usr/bin/env python3
"""Run the required platform suites and retain actual xUnit XML, including skips."""

import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from xml.etree import ElementTree
from paired_release import digest, git, module, write_new

WINDOWS_REQUIRED = [
    'Hexalith.McpCli.Core.Tests.ProfileStoreTests.WindowsProfileFilesHavePrivateAcls',
    'Hexalith.McpCli.Core.Tests.ProfileStoreTests.WindowsRestrictionPreservesInheritedExistingFiles',
    'Hexalith.McpCli.Core.Tests.ProfileStoreTests.WindowsTemporaryFileHasPrivateAclBeforeTokenBytesAreWritten',
    'Hexalith.McpCli.Cli.Tests.ConfigCommandTests.ConcurrentSetProcessesPreserveBothValuesAsync',
    'Hexalith.McpCli.Cli.Tests.ConfigCommandTests.VerbsNeverOpenAdminProfilesAsync',
    'Hexalith.McpCli.Cli.Tests.CliOutputContractTests.MissingExistingFileStagingDirectoryPreventsMutationAsync',
    'Hexalith.McpCli.Cli.Tests.CliOutputContractTests.WindowsInaccessibleExistingOutputPreventsProfileMutationAsync',
]


def inspect_xml(path):
    root = ElementTree.parse(path).getroot()
    tests = root.findall('.//test')
    assemblies = root.findall('.//assembly')
    if (not any(test.get('result') == 'Pass' for test in tests) or root.findall('.//error')
            or any(int(assembly.get('failed', '0')) or int(assembly.get('errors', '0')) for assembly in assemblies)
            or any(test.get('result') not in ('Pass', 'Skip') for test in tests)):
        raise ValueError('Platform suite has no executed tests or contains a failure.')
    return {test.get('name'): test.get('result') for test in tests}


def run_tests(prepared_path, output):
    prepared = json.loads(Path(prepared_path).read_text())
    if git('rev-parse', 'HEAD') != prepared['source_sha']:
        raise ValueError('Platform tests do not use the preparation source SHA.')
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    system = platform.system()
    suites = ['Core', 'Cli'] if system == 'Windows' else ['Cli'] if system == 'Darwin' else []
    env = {key: value for key, value in os.environ.items() if not key.startswith(('EVENTSTORE_', 'MCPCLI_'))}
    env['MCPCLI_HOME'] = str(output / 'home')
    def command(name, arguments, required=True):
        try:
            result = subprocess.run(arguments, env=env, capture_output=True)
        except OSError as error:
            (output / f'{name}.stdout.txt').write_bytes(b'')
            (output / f'{name}.stderr.txt').write_text(str(error) + '\n')
            write_new(output / f'{name}.command.json', {'argv': arguments, 'exit_code': None, 'error': str(error)})
            raise
        (output / f'{name}.stdout.txt').write_bytes(result.stdout)
        (output / f'{name}.stderr.txt').write_bytes(result.stderr)
        write_new(output / f'{name}.command.json', {'argv': arguments, 'exit_code': result.returncode})
        if required:
            result.check_returncode()
        return result
    if suites:
        command('restore', ['dotnet', 'restore', 'Hexalith.McpCli.slnx', '-p:Version=' + prepared['version']])
        command('build', ['dotnet', 'build', 'Hexalith.McpCli.slnx', '--no-restore', '--configuration', 'Release', '-warnaserror', '-p:Version=' + prepared['version']])
    outcomes = {}
    failures = []
    reports = []
    for suite in suites:
        name = 'Hexalith.McpCli.' + suite + '.Tests'
        xml = output / (name + '.xml')
        report = {'suite': suite, 'exit_code': None, 'xml_status': 'missing'}
        reports.append(report)
        try:
            result = command(name, ['dotnet', f'tests/{name}/bin/Release/net10.0/{name}.dll', '-xml', str(xml)], required=False)
            report['exit_code'] = result.returncode
            if result.returncode:
                failures.append(f'{name} exited {result.returncode}')
        except (OSError, subprocess.SubprocessError) as error:
            report['launch_error'] = str(error)
            failures.append(f'{name} could not complete: {error}')
        try:
            outcomes.update(inspect_xml(xml))
            report['xml_status'] = 'passed'
        except (OSError, ValueError, ElementTree.ParseError) as error:
            report['xml_status'] = 'failed'
            report['xml_error'] = str(error)
            failures.append(f'{name} XML: {error}')
    if system == 'Windows':
        missing = [name for name in WINDOWS_REQUIRED if outcomes.get(name) != 'Pass']
        if missing:
            failures.append('Required Windows tests did not pass: ' + ', '.join(missing))
    write_new(output / 'suite-outcomes.json', {'schema': 'mcpcli-paired-suite-outcomes/v1', 'os': system,
              'status': 'failed' if failures else 'passed', 'source_sha': prepared['source_sha'],
              'version': prepared['version'], 'packages': prepared['packages'], 'suites': reports, 'failures': failures})
    if failures:
        raise ValueError('Platform suites failed after collecting all required suites: ' + '; '.join(failures))
    write_new(output / 'tests.json', {'schema': 'mcpcli-paired-platform-tests/v1', 'os': system, 'status': 'passed',
                                     'source_sha': prepared['source_sha'], 'version': prepared['version'],
                                     'packages': prepared['packages'], 'suites': suites,
                                     'xml': {path.name: digest(path) for path in sorted(output.glob('*.xml'))}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        run_tests(args.prepared, args.output)
        return 0
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(f'Platform validation failed: {module("verify-release-source").failure_detail(error)}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
