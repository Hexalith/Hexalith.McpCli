
import base64, json, os, pathlib, signal, subprocess, sys, time
root = pathlib.Path(os.environ['FIXTURE_ROOT'])
runtime = pathlib.Path(os.environ['MCPCLI_ISOLATED_RUNTIME_DIR'])
mode = os.environ.get('FIXTURE_MODE', '')
with (root / 'runner-environment.jsonl').open('a') as log:
    log.write(json.dumps([pathlib.Path(__file__).name,
                          sorted(key for key in os.environ if key.startswith(('MCPCLI_LIVE_', 'EVENTSTORE_')))]) + '\n')
with (root / 'runner-gateway-environment.jsonl').open('a') as log:
    log.write(json.dumps({'profile': os.environ.get('Topology__UsePackagedGateway'),
                         'sourceCommit': os.environ.get('MCPCLI_EVENTSTORE_PACKAGE_SOURCE_COMMIT')}) + '\n')
with (root / 'runner-source-overrides.jsonl').open('a') as log:
    log.write(json.dumps(os.environ.get('CustomAfterMicrosoftCommonTargets')) + '\n')
with (root / 'runner-after-directory.jsonl').open('a') as log:
    log.write(json.dumps(os.environ.get('CustomAfterDirectoryBuildTargets')) + '\n')
with (root / 'runner-restore.jsonl').open('a') as log:
    log.write(json.dumps({'config': os.environ.get('RestoreConfigFile'),
                         'httpCache': os.environ.get('NUGET_HTTP_CACHE_PATH')}) + '\n')
with (root / 'runner-reader-audit.jsonl').open('a') as log:
    log.write(json.dumps({'path': os.environ.get('MCPCLI_NATIVE_READER_AUDIT_PATH'),
                         'sha256': os.environ.get('MCPCLI_NATIVE_READER_AUDIT_SHA256')}) + '\n')
if mode == 'audit-before-smoke' and pathlib.Path(__file__).name == 'run-vectors.py':
    pathlib.Path(os.environ['MCPCLI_NATIVE_READER_AUDIT_PATH']).write_text('{}')
if mode == 'nested-before-smoke' and pathlib.Path(__file__).name == 'run-vectors.py':
    nested = root / 'references/Hexalith.Tenants/references/Hexalith.Builds/.git'
    nested.parent.mkdir(parents=True)
    nested.write_bytes(b'untouched nested checkout')
if mode.startswith('source-before-smoke-') and pathlib.Path(__file__).name == 'run-vectors.py':
    drift = mode.removeprefix('source-before-smoke-')
    if drift == 'selection':
        selection_path = root / 'tools/live-topology/native-runtime-current.json'
        selection = json.loads(selection_path.read_text())
        selection['sources']['Hexalith.Parties']['commit'] = 'e' * 40
        selection_path.write_text(json.dumps(selection))
    else:
        (root / 'source-drift.json').write_text(json.dumps({'source': 'Hexalith.Parties', 'mode': drift}))
def owned(name, base=runtime):
    path = base / 'runs' / name; path.mkdir(parents=True)
    namespaces = {key: key + ':[' + str(2000 + index) + ']' for index, key in enumerate(('user', 'pid', 'net', 'mnt'))}
    result = {'commandExitCode': 0, 'prerequisitesReady': True, 'namespaces': namespaces, 'supervisorPid': 1,
              'ownedInfrastructureStopped': {key: 0 for key in ('sentry', 'redis', 'placement', 'scheduler')}}
    if mode == 'missing-cleanup' or (mode == 'smoke-missing-cleanup' and name == 'smoke'):
        result['ownedInfrastructureStopped'].pop('redis')
    (path / 'result.json').write_text(json.dumps(result))
    (path / 'outside.json').write_text(json.dumps({'namespaces': {key: key + ':[' + str(1000 + index) + ']' for index, key in enumerate(namespaces)}}))
    (path / 'command.stdout.txt').write_text('eyJfixture.payload.signature\n-----BEGIN PRIVATE KEY-----\nfixture credential\n-----END PRIVATE KEY-----\n' + os.environ.get('TEST_SECRET_TOKEN', ''))
    (path / 'issuer.key').write_text('must not be uploaded')
    (path / 'dump.rdb').write_text('must not be uploaded')
    secret = base64.b64encode(os.urandom(32)).decode()
    with (root / 'generated-signing-keys.txt').open('a') as keys: keys.write(secret + '\n')
    (path / 'generated-json.txt').write_text(json.dumps({'SigningKey': secret}))
    with (path / 'command.stdout.txt').open('a') as log:
        log.write('\n' + json.dumps({'Authentication:JwtBearer:SigningKey': secret}) + '\n')
        log.write(json.dumps({'diagnostic': json.dumps({'SigningKey': secret})}) + '\n')
    return path
if pathlib.Path(__file__).name == 'run-vectors.py':
    nested = subprocess.check_output(['python3', '-c', 'import ci_prepared_only,json,sys; print(json.dumps({"prefix":sys.prefix,"executable":sys.executable,"marker":ci_prepared_only.marker}))'], text=True)
    (root / 'nested-python.json').write_text(nested)
    output = pathlib.Path(sys.argv[sys.argv.index('--output') + 1]); output.mkdir()
    operations = sorted(operation for operation in (json.loads(path.read_text())['operation'] for path in (root / 'tools/conformance-vectors/v1/current/modules').glob('*.vector.json'))
                        if (root / 'tools/live-topology/plans-current' / (operation + '.json')).is_file())
    if mode == 'cancel-vectors':
        outcomes = [{'operation': name, 'result': 'not-run'} for name in operations]
        outcomes[0]['result'] = 'running'
        (output / 'live-lane.json').write_text(json.dumps({'result': 'pending', 'fullLiveAccepted': False, 'coverage': operations, 'vectors': outcomes}))
        def terminate(*_):
            print('detached vector stopped', flush=True)
            print('detached vector stderr stopped', file=sys.stderr, flush=True)
            (root / 'cancel-child-stopped').touch()
            sys.exit(143)
        child = output / operations[0]; child.mkdir()
        pem = '-----BEGIN EC PRIVATE KEY-----\ncancel-pem-canary'
        (child / 'child.stdout.txt').write_text('Authorization: Bearer cancel-bearer-canary\n' + pem)
        (child / 'tests.xml').write_text('<root><PrivateKey>cancel-xml-canary</PrivateKey><unfinished')
        print('Authorization: Bearer cancel-bearer-canary', flush=True)
        print(json.dumps({'diagnostic': pem}), file=sys.stderr, flush=True)
        signal.signal(signal.SIGTERM, terminate)
        print('detached vector started', flush=True)
        (root / 'cancel-child.json').write_text(json.dumps({'pid': os.getpid(), 'pgid': os.getpgrp()}))
        while True: time.sleep(1)
    outcomes = [{'operation': name, 'result': 'passed', 'exitCode': 0, 'isolatedReceipt': str(owned(name + '-' + str(index)) / 'result.json')} for index, name in enumerate(operations)]
    receipt = {'result': 'passed', 'fullLiveAccepted': True, 'coverage': operations, 'vectors': outcomes, 'passed': len(operations), 'failed': 0}
    if mode == 'extra-approved-vector': outcomes[-1]['isolatedReceipt'] = outcomes[0]['isolatedReceipt']
    if mode == 'wrong-coverage': receipt['coverage'] = operations[:-1]
    if mode == 'wrong-lane-result': receipt['result'] = 'failed'
    if mode == 'wrong-passed-count': receipt['passed'] = 20
    if mode == 'wrong-failed-count': receipt['failed'] = 1
    if mode == 'wrong-outcome-operation': outcomes[0]['operation'] = 'sample.unexpected'
    if mode == 'wrong-outcome-exit': outcomes[0]['exitCode'] = 1
    if mode in ('lane-preflight', 'lane-admission', 'lane-coverage', 'lane-runtime'):
        receipt.update(result='failed', fullLiveAccepted=False, error='named ' + mode + ' prerequisite failure')
        receipt['vectors'] = []
    if mode == 'lane-timeout':
        outcomes = [{'operation': name, 'result': 'not-run'} for name in operations]
        outcomes[0].update(result='failed', error='phase observe: assertion mismatch')
        outcomes[1]['result'] = 'running'
        receipt = {'result': 'pending', 'fullLiveAccepted': False, 'coverage': operations, 'vectors': outcomes}
    if mode == 'partial-vectors': receipt['fullLiveAccepted'] = False
    if mode == 'skipped-vector': outcomes[0]['result'] = 'skipped'
    if mode == 'incomplete-vectors': outcomes.pop()
    if mode in ('failed-vectors', 'both-fail', 'cancel-smoke-after-vector-failure'):
        receipt.update(result='failed', passed=20, failed=1)
        outcomes[0].update(result='failed', error='phase observe-party: gateway_error 500')
    if mode == 'fail-fast-vectors':
        receipt.update(result='failed', fullLiveAccepted=False, passed=0, failed=2,
                       skipped=len(operations) - 2, failFastTriggered=True,
                       failFastReason='reached --max-failures 2 after ' + operations[1])
        outcomes[0].update(result='failed', error='phase observe-0: gateway_error 500')
        outcomes[1].update(result='failed', error='phase observe-1: gateway_error 500')
        for item in outcomes[2:]:
            item.update(result='skipped-fail-fast')
            item.pop('exitCode', None)
            item.pop('isolatedReceipt', None)
    if mode == 'forged-fail-fast-passed':
        receipt.update(failFastTriggered=True, skipped=1)
    if mode == 'forged-fail-fast-flag-only':
        receipt.update(failFastTriggered=True, skipped=0)
    if mode == 'forged-fail-fast-nonbool':
        receipt.update(failFastTriggered='yes', skipped=0)
    if mode == 'forged-skipped-only':
        receipt.update(failFastTriggered=False, skipped=1)
    if mode == 'forged-skipped-bool':
        receipt.update(failFastTriggered=False, skipped=False)
    if mode == 'duplicate-isolation': outcomes[1]['isolatedReceipt'] = outcomes[0]['isolatedReceipt']
    if mode == 'stale-isolation': outcomes[0]['isolatedReceipt'] = str(owned('foreign', runtime.parent / 'sibling-runtime') / 'result.json')
    if mode == 'extra-runtime': (runtime / 'runs/unexpected').mkdir()
    if mode in ('generation-secrets', 'generation-xml-secrets'):
        secret = base64.b64encode(os.urandom(32)).decode()
        with (root / 'generated-signing-keys.txt').open('a') as keys: keys.write(secret + '\n')
        content = 'eyJfixture.payload.signature\n-----BEGIN PRIVATE KEY-----\nfixture credential\n-----END PRIVATE KEY-----\n' + os.environ['TEST_SECRET_TOKEN'] + '\n' + json.dumps({'SigningKey': secret})
        child = output / operations[0]; child.mkdir()
        (child / 'child.stdout.txt').write_text(content)
        from html import escape
        (child / 'tests.xml').write_text('<test>' + (escape(content) if mode == 'generation-xml-secrets' else content) + '</test>')
    if mode == 'generation-redaction-regressions':
        child = output / operations[0]; child.mkdir()
        pem = '-----BEGIN RSA PRIVATE KEY-----\nretained-pem-canary'
        content = 'retained child diagnostic\nAuthorization: Bearer retained-bearer-canary\n' + json.dumps({'nested': pem, 'safe': 'retained sibling'})
        (child / 'child.stdout.txt').write_text(content)
        (child / 'child.stderr.txt').write_text('retained stderr\n' + pem)
        (child / 'tests.xml').write_text('<root><ns:PrivateKey>retained-xml-canary</ns:PrivateKey><unfinished')
        print('retained process stdout Authorization: Bearer retained-bearer-canary', flush=True)
        print(json.dumps({'stderr': pem, 'safe': 'retained process stderr'}), file=sys.stderr, flush=True)
    if mode != 'missing-vectors':
        (output / 'live-lane.json').write_text('{' if mode == 'malformed-vectors' else json.dumps(receipt))
    if mode == 'tamper-after-vectors':
        (root / 'tests/Hexalith.McpCli.EventStoreGateway.TestHost/bin/Release/net11.0/Hexalith.EventStore.Gateway.dll').write_bytes(b'changed-after-vector-lane')
    # Like run-vectors.py, every failed lane result exits 1.
    sys.exit(124 if mode == 'lane-timeout' else 19 if mode == 'vector-exit' else 1 if mode in (
        'failed-vectors', 'fail-fast-vectors', 'both-fail', 'cancel-smoke-after-vector-failure',
        'lane-preflight', 'lane-admission', 'lane-coverage', 'lane-runtime') else 0)
else:
    independent = 'boundary' if 'Hexalith.McpCli.Integration.Tests.SharedHeadBoundaryTests' in sys.argv else 'smoke'
    output = pathlib.Path(os.environ['MCPCLI_LIVE_OUTPUT'])
    expected = pathlib.Path(sys.argv[sys.argv.index('-result-xml') + 1]).parent
    if output != expected or not output.is_dir():
        raise RuntimeError('Smoke writer bootstrap requires its selected evidence directory.')
    (root / ('runner-' + independent + '-output.json')).write_text(json.dumps(str(output)))
    path = owned(independent)
    if mode == 'cancel-smoke-after-vector-failure' and independent == 'smoke':
        def terminate(*_):
            print('independent smoke stopped', flush=True)
            (root / 'cancel-child-stopped').touch()
            sys.exit(143)
        signal.signal(signal.SIGTERM, terminate)
        (root / 'cancel-child.json').write_text(json.dumps({'pid': os.getpid(), 'pgid': os.getpgrp()}))
        while True: time.sleep(1)
    result = 'Skip' if mode == 'skipped-smoke' and independent == 'smoke' else 'Pass'
    xml = '<assemblies><assembly total="1" passed="1" failed="0" skipped="0" errors="0"><collection><test result="' + result + '" type="Hexalith.McpCli.Integration.Tests.GatewaySmokeTests" method="AuthenticatedQueryReturnsSuccessfulDocument" /></collection></assembly></assemblies>'
    if independent == 'boundary':
        xml = xml.replace('GatewaySmokeTests', 'SharedHeadBoundaryTests').replace('AuthenticatedQueryReturnsSuccessfulDocument', 'SharedHeadsPreserveAuthorizationAndDeactivationSafety')
        if mode == 'wrong-boundary-case': xml = xml.replace('SharedHeadsPreserveAuthorizationAndDeactivationSafety', 'OtherTest')
        if mode == 'skipped-boundary': xml = xml.replace('result="Pass"', 'result="Skip"')
    if mode == 'wrong-smoke-case': xml = xml.replace('AuthenticatedQueryReturnsSuccessfulDocument', 'OtherTest')
    if mode == 'skipped-smoke-count' and independent == 'smoke': xml = xml.replace('skipped="0"', 'skipped="1"')
    if mode == 'empty-smoke' and independent == 'smoke': xml = '<assemblies><assembly total="0" passed="0" failed="0" skipped="0" errors="0" /></assemblies>'
    if mode == 'smoke-assembly-error' and independent == 'smoke': xml = xml.replace('errors="0"', 'errors="1"')
    if mode == 'wrong-smoke-type': xml = xml.replace('GatewaySmokeTests"', 'OtherTests"')
    destination = pathlib.Path(sys.argv[sys.argv.index('-result-xml') + 1])
    if mode != 'missing-smoke' or independent != 'smoke': destination.write_text(xml)
    if mode == 'reused-independent-receipt' and independent == 'smoke': path = runtime / 'runs/boundary'
    if mode != 'missing-smoke-receipt' or independent != 'smoke': print('Isolated run: ' + str(path))
    if mode == 'duplicate-smoke-receipt' and independent == 'smoke': print('Isolated run: ' + str(path))
    if mode == 'tamper-after-boundary' and independent == 'boundary':
        (root / 'tests/Hexalith.McpCli.EventStoreGateway.TestHost/bin/Release/net11.0/Hexalith.EventStore.Gateway.dll').write_bytes(b'changed-after-boundary')
    if mode == 'tamper-tenant-after-boundary' and independent == 'boundary':
        (pathlib.Path(json.loads(pathlib.Path(os.environ['MCPCLI_NATIVE_SOURCE_FIXTURES']).read_text())['modules']['Hexalith.Tenants']['path']) / 'src/Hexalith.Tenants/bin/Release/net11.0/Hexalith.Tenants.dll').write_bytes(b'changed-after-boundary')
    sys.exit(17 if mode in ('smoke-exit', 'both-fail') and independent == 'smoke' else 0)
