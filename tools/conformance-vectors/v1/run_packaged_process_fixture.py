#!/usr/bin/env python3
"""Exercise real enrollment, rejected inventory and failed semantic replay with temporary sample data."""
from __future__ import annotations

import argparse
import base64
import copy
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


def enroll_fixture(project: ET.Element, package_id: str, preserve_existing: bool = False) -> None:
    """Select the synthetic fixture, optionally retaining the temporary combined population."""
    for parent in project.iter():
        for item in list(parent):
            if item.tag == 'PackageReference':
                metadata = {child.tag.casefold(): child.text or '' for child in item}
                metadata.update((name.casefold(), value) for name, value in item.attrib.items())
                if metadata.get('hexalithcontracts', '').casefold() == 'true' and (
                        not preserve_existing or item.get('Include', '').casefold() == package_id.casefold()):
                    parent.remove(item)
    ET.SubElement(ET.SubElement(project, 'ItemGroup'), 'PackageReference',
                  Include=package_id, HexalithContracts='true')


def sdk_response_cases(repo: Path, root: Path, host: Path, artifact: Path, env: dict) -> None:
    """Use the real pinned SDK and complete runner for typed/default/parser outcomes."""
    sources = root / 'sdk-response-cases'
    sources.mkdir()
    documents = [json.loads((repo / 'tools/conformance-vectors/v1' / name).read_text())
                 for name in ['sample-command.json', 'sample-query.json', 'sample-rename.json']]
    command, query, rename = documents
    opaque = {'MixedCase': [True, 1], 'payload': {'SUCCESS': 'true'}}
    correlation = '01J9MZHXT3RKM0VWXRXGSJDATK'
    base = {'correlationId': correlation, 'payload': opaque}
    nested = 0
    for _ in range(63):
        nested = {'nested': nested}
    cases = [
        ('omitted-success', base, None),
        ('typed-property-casing', {'CORRELATIONID': correlation, 'PAYLOAD': opaque, 'SUCCESS': True,
                                  'METADATA': {'PAGING': {'OFFSET': None, 'unknown': 7}}}, {'pageSize': 0}),
        ('typed-paging', dict(base, metadata={'paging': {'pageSize': '7', 'offset': '2',
             'totalCount': '3', 'hasMore': False, 'nextCursor': None, 'unknown': True}}),
             {'pageSize': 7, 'offset': 2, 'totalCount': 3, 'hasMore': False}),
        ('signed-paging', dict(base, metadata={'paging': {'pageSize': '+007', 'offset': '+2', 'totalCount': '+3'}}),
             {'pageSize': 7, 'offset': 2, 'totalCount': 3}),
        ('long-leading-zero-paging', dict(base, metadata={'paging': {'pageSize': '0' * 5000 + '7'}}), {'pageSize': 7}),
        ('explicit-null-payload', dict(base, payload=None), None),
        ('unicode-lookalike-is-unknown', dict(base, **{'ſuccess': False}), None),
        ('valid-later-case-variant', dict(base, success=False, Success=True), None),
        ('depth64', dict(base, ignored=nested), None),
        ('paging-array-parse-error', dict(base, metadata={'paging': []}), 'parse-error'),
        ('success-string-parse-error', dict(base, success='true'), 'parse-error'),
        ('depth65-parse-error', dict(base, ignored={'nested': nested}), 'parse-error'),
        ('invalid-earlier-success', dict(base, success='true', Success=True), 'parse-error'),
        ('invalid-earlier-correlation', dict(base, correlationId=False, CorrelationId=correlation), 'parse-error'),
        ('invalid-earlier-metadata', dict(base, metadata={'servedAt': 'bad', 'ServedAt': '2026-10-22T12:34:56Z'}), 'parse-error'),
        ('invalid-earlier-paging', dict(base, metadata={'paging': {'pageSize': 'bad', 'PageSize': 7}}), 'parse-error'),
    ]
    for timestamp in ['2026-10-22', '2026-10-22T12:34', '2026-10-22T12:34Z',
                      '2026-10-22T12:34:56Z', '2026-10-22T12:34:56.1234567890123456+02:00',
                      '2026-10-22T12:34:56.Z', '2026-10-22T12:34:56.+02:00',
                      '2026-10-22T12:34:56', '2026-10-22T12:34:56+14:00']:
        cases.append(('valid-timestamp', dict(base, metadata={'servedAt': timestamp}), None))
    for timestamp in ['2026-W43-4T12:34:56Z', '2026-10-22 12:34:56Z', '2026-10-22T12:34:56,5Z',
                      '2026-10-22t12:34:56z', '2026-10-22T12:34:56.12345678901234567Z',
                      '2026-10-22T12:34:56+14:01', '2026-10-22T12:34:56+00:60']:
        cases.append(('invalid-timestamp', dict(base, metadata={'servedAt': timestamp}), 'parse-error'))
    query['prerequisites'] = []
    for _, body, paging in cases:
        step = copy.deepcopy(query['invocation'])
        step['scriptedResponse']['body'] = body
        if paging == 'parse-error':
            step['assertions'] = [{'path': '/error', 'operator': 'equals', 'value': {
                'code': 'gateway_error', 'status': 200, 'detail': 'Query response body could not be parsed.'}}]
        else:
            step['assertions'] = [{'path': '/document', 'operator': 'equals', 'value': body.get('payload', body.get('PAYLOAD', opaque))},
                                  {'path': '/paging', 'operator': 'exists', 'value': paging is not None}]
            if paging is not None:
                step['assertions'].append({'path': '/paging', 'operator': 'equals', 'value': paging})
        query['prerequisites'].append(step)
    errors = [
        (304, {}, {'code': 'gateway_error', 'status': 502,
                   'detail': 'Not-modified query response requires projection-backed provenance and a strong ETag.'}),
        (200, dict(base, success=False, errorMessage='scripted semantic failure'),
                   {'code': 'gateway_error', 'status': 200, 'detail': 'scripted semantic failure', 'correlationId': correlation}),
        (409, {'status': 422, 'detail': 'status override'}, {'code': 'gateway_error', 'status': 422, 'detail': 'status override'}),
    ]
    for status in ['422', None, True]:
        errors.append((503, {'status': status, 'detail': 'bad status'},
                       {'code': 'internal_error', 'message': 'Operation execution failed.'}))
    for status, body, expected in errors:
        step = copy.deepcopy(query['invocation'])
        step['scriptedResponse'] = {'statusCode': status, 'body': body, 'echoRequestFields': []}
        step['assertions'] = [{'path': '/error', 'operator': 'equals', 'value': expected}]
        query['prerequisites'].append(step)
    message = '01J9MZHXT3RKM0VWXRXGSJDATP'
    command['invocation']['scriptedResponse'] = {'statusCode': 202,
        'body': {'MESSAGEID': message, 'RESULTPAYLOAD': opaque}, 'echoRequestFields': ['correlationId']}
    command['invocation']['assertions'] = [
        {'path': '/result', 'operator': 'equals', 'value': opaque},
        {'path': '/messageId', 'operator': 'equals', 'value': message}]
    # Exercise both supplied and generated request correlations through the full
    # binding/masking path: the SDK's 204 parse error contains neither echo.
    supplied = copy.deepcopy(command['invocation'])
    supplied['scriptedResponse']['statusCode'] = 204
    expected_error = {'code': 'gateway_error', 'status': 204, 'detail': 'Command response body could not be parsed.'}
    supplied['assertions'] = [{'path': '/error', 'operator': 'equals', 'value': expected_error}]
    rename['prerequisites'] = [supplied]
    rename['invocation']['scriptedResponse']['statusCode'] = 204
    rename['invocation']['assertions'] = copy.deepcopy(supplied['assertions'])
    vectors = []
    for document in documents:
        path = sources / (document['operation'] + '.vector.json')
        path.write_text(json.dumps(document))
        vectors.append(path)
    result = run([sys.executable, repo / 'tools/conformance-vectors/v1/run_loopback.py', '--host', host,
                  '--artifact', artifact, '--expected-package-id', 'Hexalith.McpCli.Sample.Contracts',
                  '--expected-package-version', '1.0.0', *vectors], root, env)
    (sources / 'replay.stdout.txt').write_text(result.stdout)
    (sources / 'replay.stderr.txt').write_text(result.stderr)
    # An omitted JsonElement remains Undefined, which fails in each head's
    # serializer. Preserve the two actual error documents and require parity refusal.
    from run_loopback import HeadProcess, ReplayGateway, _assert_error_parity, _run_step
    from validate import VectorError
    missing = copy.deepcopy(query['invocation'])
    missing['scriptedResponse']['body'] = {'correlationId': correlation}
    observed = {}
    head = HeadProcess(host, str(sources), 30)
    head.env.update(env)
    for label, message in [('CLI', 'The CLI action failed.'), ('MCP', 'MCP tool invocation failed.')]:
        missing['assertions'] = [{'path': '/error', 'operator': 'equals', 'value': {'code': 'internal_error', 'message': message}}]
        with ReplayGateway([missing]) as gateway:
            observed[label], _ = _run_step(head, missing, gateway.url, label)
            gateway.assert_consumed('missing-payload ' + label)
    (sources / 'missing-payload-head-outcomes.json').write_text(json.dumps(observed, indent=2) + '\n')
    try:
        _assert_error_parity(observed['CLI'], observed['MCP'], 'missing-payload')
    except VectorError:
        pass
    else:
        raise RuntimeError('Missing-payload head-specific internal errors falsely passed parity.')
    print('PASS real SDK signed paging, timestamp grammar, ordered ASCII property matching, explicit-null/missing payload, internal errors, 304/semantic/status-override outcomes and command204 replay; missing-payload head differences refuse parity.', flush=True)


def fixture(repo: Path, artifact: Path):
    artifact = artifact.resolve(strict=True)
    package_id, version = 'Hexalith.McpCli.Sample.Contracts', '1.0.0'
    with tempfile.TemporaryDirectory(prefix='mcpcli-packaged-process-') as temporary:
        root = Path(temporary).resolve()
        # The synthetic receipt, inventory and flagged project exist only in this temporary repository.
        for name in ['src', 'references/Hexalith.Builds/Props', 'tools/conformance-vectors/v1', 'tools/inventory-coverage/v1']:
            shutil.copytree(repo / name, root / name, ignore=shutil.ignore_patterns('bin', 'obj', '.git', '__pycache__'))
        for name in ['Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props', 'global.json', '.editorconfig']:
            if (repo / name).exists():
                shutil.copy2(repo / name, root / name)
        host = root / 'tests/Hexalith.McpCli.ConformanceHost'
        host.mkdir(parents=True)
        for source in (repo / 'tests/Hexalith.McpCli.ConformanceHost').glob('*.cs'):
            shutil.copy2(source, host / source.name)
        shutil.copy2(repo / 'tests/Hexalith.McpCli.ConformanceHost/Hexalith.McpCli.ConformanceHost.csproj',
                     host / 'Hexalith.McpCli.ConformanceHost.csproj')
        (host / 'Directory.Packages.props').write_text('<Project><Import Project="../../Directory.Packages.props" /></Project>')
        (root / 'tools/conformance-vectors/v1/v1-scope.json').write_text(json.dumps({'requiredModules': ['sample']}))
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
            document = json.loads(destination.read_text())
            for step in document['prerequisites'] + [document['invocation']] + document['postconditions']:
                if step['kind'] == 'command':
                    extensions = {'trace-id': 'story411 value=preserved'}
                    step['envelope']['extensions'] = extensions
                    step['expectedGateway']['body']['extensions'] = extensions
            destination.write_text(json.dumps(document))
            vectors.append(destination)
        inventories = root / 'tools/inventory-coverage/v1'
        inventories.mkdir(parents=True, exist_ok=True)
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

        # The real Core adapter must reject every incompatible step before any Gateway exists.
        host_dll = host / 'bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll'
        sdk_response_cases(repo, root, host_dll, artifact, env)
        for group in ['prerequisites', 'invocation', 'postconditions']:
            for mutation in ['unknown-property', 'wrong-kind', 'invalid-id', 'depth64-schema', 'excess-depth']:
                document = json.loads((repo / 'tools/conformance-vectors/v1/sample-command.json').read_text())
                step = copy.deepcopy(document['invocation'])
                if mutation == 'unknown-property':
                    step['payload']['Unknown'] = 1
                elif mutation == 'wrong-kind':
                    step['kind'] = 'query'
                elif mutation == 'invalid-id':
                    step['payload']['ItemId'] = 'not-a-ulid'
                else:
                    nested = 1
                    for _ in range(64 if mutation == 'depth64-schema' else 65):
                        nested = {'nested': nested}
                    step['payload'] = nested
                pointer = '/invocation' if group == 'invocation' else '/' + group + '/0'
                document[group] = step if group == 'invocation' else [step]
                source = root / 'incompatible.vector.json'
                source.write_text(json.dumps(document))
                failed = run(['dotnet', host_dll, '--validate-vectors', source], root, env, expected=1)
                if failed.stderr:
                    raise RuntimeError('Core preflight wrote unexpected stderr: ' + failed.stderr)
                findings = json.loads(failed.stdout)['findings']
                if not any(str(source) + ':' + pointer in finding and 'Core compatibility failed' in finding for finding in findings):
                    raise RuntimeError('Core preflight lost the source/step diagnostic: ' + failed.stdout)
                if mutation in ['depth64-schema', 'excess-depth']:
                    parse_failure = any('The payload must be valid JSON' in finding for finding in findings)
                    if parse_failure != (mutation == 'excess-depth'):
                        raise RuntimeError('Core depth 64/65 boundary differs from parser/schema rules: ' + failed.stdout)
        print('PASS all prerequisite/invocation/postcondition kinds, schemas, identifiers and excessive depth fail offline with located Core diagnostics.', flush=True)

        # Preserve the real enrolled packages and add the synthetic fixture only in this temporary repository.
        combined_project = ET.parse(repo / 'src/Hexalith.McpCli/Hexalith.McpCli.csproj')
        enroll_fixture(combined_project.getroot(), package_id, preserve_existing=True)
        combined_project.write(project, encoding='unicode')
        run(['dotnet', 'restore', project, '-p:Configuration=Release', f'-p:RestoreAdditionalProjectSources={artifact.parent}'], root, env)
        combined_output = root / 'combined'
        run([sys.executable, root / 'tools/conformance-vectors/v1/check_enrolled.py', '--output', combined_output], root, env)
        combined = json.loads((combined_output / 'enrolled.json').read_text())
        expected_packages = [p['Identity'] for p in json.loads(run(['dotnet', 'msbuild', project,
            '-getItem:PackageReference'], root, env).stdout)['Items']['PackageReference']
            if p.get('HexalithContracts', '').lower() == 'true']
        if combined['result'] != 'passed' or set(combined['packages']) != set(expected_packages) \
                or len(expected_packages) < 2 or combined['productionReplay']['packageCount'] != len(expected_packages):
            raise RuntimeError('Combined production manifest was not completely replayed.')
        print('PASS combined manifest: all production packages plus the explicit temporary sample pass independent artifact and complete Catalog replay.', flush=True)

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
