#!/usr/bin/env python3
"""Accept only one source/hash-bound pair with complete matching three-OS evidence."""

import argparse
import json
import re
from pathlib import Path
import sys
from paired_release import check_prepared, digest, module, write_new


def compare(staging, prepared_path, consumers, output):
    prepared_path = Path(prepared_path)
    prepared = check_prepared(staging, prepared_path)
    if prepared.get('eligibility') != 'current-main' or prepared.get('source_clean') is not True:
        raise ValueError('Local-only or dirty-source preparation cannot become accepted staging.')
    evidence = prepared_path.parent / 'evidence'
    if not {'source-before.json', 'source-after.json', 'validation.json', 'consumer.json', 'consumer.command.json',
            'consumer.stdout.txt', 'consumer.stderr.txt', 'consumer-build.log'} <= set(prepared.get('evidence', {})):
        raise ValueError('Required preparation evidence is absent.')
    for name, sha in prepared['evidence'].items():
        if Path(name).name != name or digest(evidence / name) != sha:
            raise ValueError('Preparation evidence changed after packing.')
    for name in ('source-before', 'source-after'):
        gate = json.loads((evidence / f'{name}.json').read_text())
        if (gate.get('schema') != 'mcpcli-paired-source/v1' or gate.get('source_sha') != prepared['source_sha']
                or gate.get('current_main') != prepared['source_sha'] or gate.get('source_clean') is not True
                or not gate.get('fr22') or set(gate.get('gates', {})) != {'ci.yml', 'commitlint.yml'}):
            raise ValueError('Preparation lacks eligible current-main gates and FR-22 evidence.')
        verifier = module('verify-release-source')
        fr22 = gate['fr22']
        if (fr22.get('source_sha') != prepared['source_sha'] or fr22.get('source_clean') is not True
                or any(not isinstance(fr22.get(key), str) or re.fullmatch('[0-9a-f]{40}', fr22[key]) is None
                       for key in ('baseline_revision', 'upstream_main'))
                or fr22.get('required_revision') != module('verify-paired-prerequisites').REQUIRED
                or len(set(fr22.get('synchronization', {}).values())) != 1
                or set(fr22.get('synchronization', {})) != {'AGENTS.md', 'CLAUDE.md', '.github/copilot-instructions.md'}):
            raise ValueError('FR-22 evidence is incomplete or belongs to different source.')
        for workflow, required in [('ci.yml', verifier.STAGING_JOBS), ('commitlint.yml', verifier.STAGING_COMMITLINT_JOBS)]:
            run = gate['gates'][workflow]
            if run.get('source_sha') != prepared['source_sha'] or run.get('status') != 'completed' or run.get('conclusion') != 'success':
                raise ValueError('A required source workflow did not succeed at the exact SHA.')
            verifier.validate_jobs(run.get('jobs', []), required)
    validation = json.loads((evidence / 'validation.json').read_text())
    if any(validation.get(key) != prepared[key] for key in ('source_sha', 'version', 'packages')) or validation.get('phase') != 'paired':
        raise ValueError('Package validation does not bind the prepared pair.')
    consumer = json.loads((evidence / 'consumer.json').read_text())
    command = json.loads((evidence / 'consumer.command.json').read_text())
    compiler = (evidence / 'consumer-build.log').read_text()
    if (consumer.get('schema') != 'mcpcli-paired-consumer/v1' or consumer.get('status') != 'passed'
            or any(consumer.get(key) != prepared[key] for key in ('source_sha', 'version', 'packages'))
            or consumer.get('compiler_sha256') != digest(evidence / 'consumer-build.log')
            or consumer.get('command_sha256') != digest(evidence / 'consumer.command.json')
            or command.get('exit_code') != 0
            or command.get('argv', [])[:3] != ['bash', 'scripts/smoke-bootstrap-consumer.sh', prepared['version']]
            or re.search(r'MissingDescriptionQuery\.cs\([^)]*\): warning MCPCLI001:', compiler) is None
            or re.search(r'^\s*1 Warning\(s\)$', compiler, re.MULTILINE) is None
            or re.search(r'CS8032|CS9057', compiler)):
        raise ValueError('The staged Abstractions compiler/analyzer consumer did not succeed.')
    receipts = {}
    baseline = None
    for directory in consumers:
        directory = Path(directory)
        smoke_path = directory / 'smoke/smoke.json'
        smoke = json.loads(smoke_path.read_text())
        system = smoke['os']
        if system in receipts or system not in ('Linux', 'Windows', 'Darwin'):
            raise ValueError('A required operating-system receipt is duplicate or unknown.')
        for key in ('source_sha', 'version', 'packages'):
            if smoke.get(key) != prepared[key]:
                raise ValueError('Smoke receipt source, version or package hashes differ.')
        required = {'version', 'offline-discovery', 'config', 'json-lf', 'errors', 'mcp-protocol', 'output-file', 'table'}
        if (smoke.get('schema') != 'mcpcli-paired-smoke/v1' or smoke.get('status') != 'passed'
                or set(smoke.get('checks', [])) != required or smoke.get('preparation_sha256') != digest(prepared_path)):
            raise ValueError('Platform smoke was missing, failed or incomplete.')
        captures = {}
        for name, sha in smoke['discovery'].items():
            path = directory / 'smoke/discovery' / name
            if Path(name).name != name or digest(path) != sha:
                raise ValueError('Raw discovery capture differs from its receipt.')
            captures[name] = path.read_bytes()
        if not captures or 'modules.json' not in captures or 'mcp-tools.json' not in captures:
            raise ValueError('Raw discovery captures are incomplete.')
        expected = {'modules.json', 'mcp-tools.json', 'mcp-modules.json'}
        modules = json.loads(captures['modules.json']).get('modules', [])
        if not modules:
            raise ValueError('Raw discovery contains an empty catalog.')
        for item in modules:
            name = 'operations-' + item['name'] + '.json'
            expected.add(name)
            if name not in captures:
                raise ValueError('Raw operation captures are missing.')
            for operation in json.loads(captures[name])['operations']:
                expected.update({'describe-' + operation['name'] + '.json', 'mcp-describe-' + operation['name'] + '.json'})
            expected.add('mcp-operations-' + item['name'] + '.json')
        if set(captures) != expected or any(not raw.endswith(b'\n') or b'\r' in raw for raw in captures.values()):
            raise ValueError('Raw discovery captures are incomplete or do not use LF.')
        if baseline is not None and captures != baseline:
            raise ValueError('Raw discovery bytes differ across operating systems.')
        baseline = captures
        tests_path = directory / 'tests/tests.json'
        tests = json.loads(tests_path.read_text())
        suites = ['Core', 'Cli'] if system == 'Windows' else ['Cli'] if system == 'Darwin' else []
        if (tests.get('schema') != 'mcpcli-paired-platform-tests/v1' or tests.get('status') != 'passed'
                or tests.get('os') != system or tests.get('suites') != suites
                or any(tests.get(key) != prepared[key] for key in ('source_sha', 'version', 'packages'))):
            raise ValueError('Required platform suites were missing or unsuccessful.')
        expected_xml = {f'Hexalith.McpCli.{suite}.Tests.xml' for suite in suites}
        if set(tests.get('xml', {})) != expected_xml:
            raise ValueError('Platform XML does not contain the exact required suites.')
        outcomes = {}
        runner = module('run-paired-platform-tests')
        for name, sha in tests['xml'].items():
            path = directory / 'tests' / name
            if digest(path) != sha:
                raise ValueError('Platform XML bytes changed.')
            outcomes.update(runner.inspect_xml(path))
        if system == 'Windows' and any(outcomes.get(name) != 'Pass' for name in runner.WINDOWS_REQUIRED):
            raise ValueError('A required Windows ACL or isolated-process test was skipped or missing.')
        receipts[system] = {'smoke_sha256': digest(smoke_path), 'tests_sha256': digest(tests_path)}
    if set(receipts) != {'Linux', 'Windows', 'Darwin'}:
        raise ValueError('All three actual operating-system receipts are required.')
    write_new(output, {'schema': 'mcpcli-accepted-staged-pair/v1', 'status': 'accepted-staging-only',
                       'source_sha': prepared['source_sha'], 'version': prepared['version'], 'packages': prepared['packages'],
                       'preparation_sha256': digest(prepared_path), 'platforms': receipts,
                       'publication': 'refused; stories 4.17–4.18 remain outstanding'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staging', type=Path, required=True)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--consumer', action='append', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        compare(args.staging, args.prepared, args.consumer, args.output)
        return 0
    except (ValueError, KeyError, OSError) as error:
        print(f'Paired acceptance refused: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
