"""Execute the CI shell hooks with controlled tools; real runner tests live beside these."""
from __future__ import annotations

import json
import importlib.util
import hashlib
import io
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from unittest.mock import patch
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent

TOOL = r'''#!/usr/bin/env python3
import hashlib, json, os, pathlib, subprocess, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
root = pathlib.Path(os.environ['FIXTURE_ROOT'])
with (root / 'calls.jsonl').open('a') as log:
    log.write(json.dumps([name, str(pathlib.Path.cwd()), *args]) + '\n')
mode = os.environ.get('FIXTURE_MODE', '')
if name == 'timeout':
    command = args[3:]
    if mode == 'build-timeout' and command[:2] == ['dotnet', 'build']:
        sys.exit(124)
    if mode == 'vector-timeout' and any(value.endswith('run-vectors.py') for value in command):
        sys.exit(124)
    if '-m' in command and 'venv' in command:
        python = pathlib.Path(command[-1]) / 'bin/python'
        python.parent.mkdir(parents=True)
        python.symlink_to(sys.executable)
        python.with_name('python3').symlink_to(sys.executable)
        (python.parent.parent / 'pyvenv.cfg').write_text('home = ' + str(pathlib.Path(sys.executable).parent) + '\ninclude-system-site-packages = false\n')
        site = python.parent.parent / ('lib/python' + str(sys.version_info.major) + '.' + str(sys.version_info.minor) + '/site-packages')
        site.mkdir(parents=True)
        (site / 'ci_prepared_only.py').write_text('marker = "prepared-venv-only"\n')
        sys.exit(0)
    if '-m' in command and 'pip' in command:
        sys.exit(0)
    if '-c' in command and 'jsonschema' in command[-1]:
        print('4.26.0'); sys.exit(0)
    os.execvp(command[0], command)
if name == 'dotnet':
    if args == ['--version']:
        if mode == 'missing-sdk':
            print('A compatible .NET SDK was not found.', file=sys.stderr); sys.exit(145)
        print('10.0.403' if mode == 'sdk-patch-rollforward' else '10.0.402')
    elif args[0] == 'build':
        if mode in ('build-failure', 'build-stdout-failure') and 'Tenants' in args[1]:
            print('named source build failure', file=sys.stdout if mode == 'build-stdout-failure' else sys.stderr); sys.exit(23)
    elif args[0] == 'msbuild':
        print('3.128.3' if mode == 'wrong-package-cohort' else '3.128.4')
    sys.exit(0)
if name == 'dapr':
    print('CLI version: ' + ('1.18.0' if mode == 'wrong-dapr-cli' else '1.18.2') + '\nRuntime version: ' + ('1.18.0' if mode == 'wrong-dapr' else '1.18.7'))
elif name == 'docker' and mode == 'docker-unavailable':
    print('Cannot connect to the Docker daemon', file=sys.stderr); sys.exit(1)
elif name == 'daprd':
    print('1.18.7')
elif name == 'aspire':
    if args and args[0] == 'setup':
        if mode == 'bundle-setup-failure': sys.exit(18)
        for relative in ('dcp/dcp', 'dashboard/Aspire.Dashboard', 'managed/aspire-managed'):
            if mode == 'incomplete-bundle' and relative == 'dcp/dcp': continue
            file = pathlib.Path(args[args.index('--install-path') + 1]) / 'bundle' / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            wrong = mode == 'bundle-home-mismatch' and relative == 'managed/aspire-managed' and file.parents[2] == pathlib.Path.home() / '.aspire'
            file.write_text('corrupted managed bundle' if wrong else 'qualified bundle')
    else:
        print('13.6.2+unqualified' if mode == 'wrong-aspire' else '13.6.1+qualified')
elif name == 'curl':
    import shutil
    destination = pathlib.Path(args[args.index('-o') + 1])
    if mode == 'corrupted-aspire-archive': destination.write_bytes(b'unqualified archive')
    else: shutil.copyfile(root / 'aspire-fixture.tar.gz', destination)
elif name == 'git':
    if args[0] == 'config':
        for module in ('EventStore', 'Tenants', 'Parties'):
            if mode != 'undeclared-source' or module != 'Parties':
                print('submodule.' + module + '.path references/Hexalith.' + module)
    elif args == ['rev-parse', '--show-toplevel']:
        print(root if mode == 'copied-source' else pathlib.Path.cwd())
    elif args == ['rev-parse', 'HEAD']:
        print(hashlib.sha1(str(pathlib.Path.cwd()).encode()).hexdigest())
    elif args[0] == 'show':
        sys.stdout.buffer.write((pathlib.Path.cwd() / args[1].split(':', 1)[1]).read_bytes())
    elif args == ['status', '--porcelain', '--untracked-files=normal']:
        print('M  ' + pathlib.Path.cwd().name + '-fixture.txt')
elif name == 'sudo':
    if args != ['-n', 'sysctl', '-w', 'kernel.apparmor_restrict_unprivileged_userns=0']:
        sys.exit(89)
    if mode == 'namespace-setup-failure':
        print('hosted namespace setup failed', file=sys.stderr); sys.exit(1)
    (root / 'namespace-enabled').touch()
elif name == 'unshare':
    if mode in ('namespace-denied', 'namespace-still-denied', 'namespace-setup-failure') or \
            (mode == 'namespace-needs-setup' and not (root / 'namespace-enabled').exists()):
        print('unshare: write failed /proc/self/uid_map: Operation not permitted', file=sys.stderr); sys.exit(1)
'''

BOOTSTRAP = r'''
import hashlib, json, pathlib, sys
runtime = pathlib.Path(sys.argv[1]); (runtime / 'bin').mkdir(parents=True)
for row in json.loads(pathlib.Path(__file__).with_name('binaries.json').read_text()):
    (runtime / 'bin' / pathlib.Path(row['source']).name).write_bytes(b'tampered' if __import__('os').environ.get('FIXTURE_MODE') == 'bootstrap-hash-mismatch' else b'qualified-fixture')
(runtime / 'bootstrap-receipt.json').write_text('[]')
'''

RUNNERS = r'''
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
    operations = sorted(json.loads(path.read_text())['operation'] for path in (root / 'tools/conformance-vectors/v1/modules').glob('*.vector.json'))
    if mode == 'cancel-vectors':
        outcomes = [{'operation': name, 'result': 'not-run'} for name in operations]
        outcomes[0]['result'] = 'running'
        (output / 'live-lane.json').write_text(json.dumps({'result': 'pending', 'fullLiveAccepted': False, 'coverage': operations, 'vectors': outcomes}))
        def terminate(*_):
            print('detached vector stopped', flush=True)
            print('detached vector stderr stopped', file=sys.stderr, flush=True)
            (root / 'cancel-child-stopped').touch()
            sys.exit(143)
        signal.signal(signal.SIGTERM, terminate)
        print('detached vector started', flush=True)
        (root / 'cancel-child.json').write_text(json.dumps({'pid': os.getpid(), 'pgid': os.getpgrp()}))
        while True: time.sleep(1)
    outcomes = [{'operation': name, 'result': 'passed', 'exitCode': 0, 'isolatedReceipt': str(owned(name + '-' + str(index)) / 'result.json')} for index, name in enumerate(operations)]
    receipt = {'result': 'passed', 'fullLiveAccepted': True, 'coverage': operations, 'vectors': outcomes, 'passed': 21, 'failed': 0}
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
    if mode != 'missing-vectors':
        (output / 'live-lane.json').write_text('{' if mode == 'malformed-vectors' else json.dumps(receipt))
    if mode == 'tamper-after-vectors':
        (root / 'tests/Hexalith.McpCli.EventStoreGateway.TestHost/bin/Release/net10.0/Hexalith.EventStore.Gateway.dll').write_bytes(b'changed-after-vector-lane')
    # Like run-vectors.py, every failed lane result exits 1.
    sys.exit(124 if mode == 'lane-timeout' else 19 if mode == 'vector-exit' else 1 if mode in (
        'failed-vectors', 'both-fail', 'cancel-smoke-after-vector-failure',
        'lane-preflight', 'lane-admission', 'lane-coverage', 'lane-runtime') else 0)
else:
    path = owned('smoke')
    if mode == 'cancel-smoke-after-vector-failure':
        def terminate(*_):
            print('independent smoke stopped', flush=True)
            (root / 'cancel-child-stopped').touch()
            sys.exit(143)
        signal.signal(signal.SIGTERM, terminate)
        (root / 'cancel-child.json').write_text(json.dumps({'pid': os.getpid(), 'pgid': os.getpgrp()}))
        while True: time.sleep(1)
    result = 'Skip' if mode == 'skipped-smoke' else 'Pass'
    xml = '<assemblies><assembly total="1" passed="1" failed="0" skipped="0" errors="0"><collection><test result="' + result + '" type="Hexalith.McpCli.Integration.Tests.GatewaySmokeTests" method="AuthenticatedQueryReturnsSuccessfulDocument" /></collection></assembly></assemblies>'
    if mode == 'wrong-smoke-case': xml = xml.replace('AuthenticatedQueryReturnsSuccessfulDocument', 'OtherTest')
    if mode == 'skipped-smoke-count': xml = xml.replace('skipped="0"', 'skipped="1"')
    if mode == 'empty-smoke': xml = '<assemblies><assembly total="0" passed="0" failed="0" skipped="0" errors="0" /></assemblies>'
    if mode == 'smoke-assembly-error': xml = xml.replace('errors="0"', 'errors="1"')
    if mode == 'wrong-smoke-type': xml = xml.replace('GatewaySmokeTests"', 'OtherTests"')
    destination = pathlib.Path(sys.argv[sys.argv.index('-result-xml') + 1])
    if mode != 'missing-smoke': destination.write_text(xml)
    if mode != 'missing-smoke-receipt': print('Isolated run: ' + str(path))
    if mode == 'duplicate-smoke-receipt': print('Isolated run: ' + str(path))
    sys.exit(17 if mode in ('smoke-exit', 'both-fail') else 0)
'''


class CiHooksTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.tools = self.root / 'tools/live-topology'
        self.tools.mkdir(parents=True)
        for name in ('prepare-ci.sh', 'run-ci.sh', 'ci.py'):
            shutil.copyfile(HERE / name, self.tools / name)
        for name, content in [('bootstrap-runtime.py', BOOTSTRAP), ('run-vectors.py', RUNNERS), ('run-isolated.py', RUNNERS)]:
            (self.tools / name).write_text(content)
        binaries = [{'source': '/' + name, 'sha256': hashlib.sha256(b'qualified-fixture').hexdigest()}
                    for name in ('redis-server', 'sentry', 'placement', 'scheduler')]
        (self.tools / 'binaries.json').write_text(json.dumps(binaries))
        modules = self.root / 'tools/conformance-vectors/v1/modules'
        modules.mkdir(parents=True)
        (modules.parent / 'requirements.txt').write_text('jsonschema==4.26.0\n')
        for index in range(21):
            (modules / f'{index}.vector.json').write_text(json.dumps({'operation': f'sample.operation-{index:02}'}))
        (self.root / 'global.json').write_text('{"sdk":{"version":"10.0.402","rollForward":"latestPatch"}}')
        (self.root / '.gitmodules').touch()
        for module in ('EventStore', 'Tenants', 'Parties'):
            checkout = self.root / 'references' / ('Hexalith.' + module)
            project = checkout / 'src' / checkout.name / (checkout.name + '.csproj')
            project.parent.mkdir(parents=True)
            project.touch()
            (checkout / '.git').touch()
        tests = self.root / 'tests/Hexalith.McpCli.Integration.Tests/bin/Release/net10.0/Hexalith.McpCli.Integration.Tests.dll'
        tests.parent.mkdir(parents=True)
        tests.touch()
        gateway = self.root / 'tests/Hexalith.McpCli.EventStoreGateway.TestHost'
        (gateway / 'obj').mkdir(parents=True)
        (gateway / 'Hexalith.McpCli.EventStoreGateway.TestHost.csproj').touch()
        cache = self.root / 'package-cache'
        assemblies = ('Gateway', 'Server', 'DomainService', 'Contracts')
        for suffix in assemblies:
            name = 'Hexalith.EventStore.' + suffix
            package = cache / name.lower() / '3.128.4'
            package.mkdir(parents=True)
            nuspec = ('<package><metadata><id>' + name + '</id><version>3.128.4</version><repository commit="'
                      + 'a' * 40 + '" /></metadata></package>').encode()
            payload = (name + '-qualified-fixture').encode()
            (package / (name.lower() + '.nuspec')).write_bytes(nuspec)
            extracted = package / ('lib/net10.0/' + name + '.dll')
            extracted.parent.mkdir(parents=True)
            extracted.write_bytes(payload)
            with ZipFile(package / (name.lower() + '.3.128.4.nupkg'), 'w') as archive:
                archive.writestr(name + '.nuspec', nuspec)
                archive.writestr('lib/net10.0/' + name + '.dll', payload)
        projects = [gateway, *(self.root / 'references' / ('Hexalith.' + module) / 'src' / ('Hexalith.' + module)
                              for module in ('Tenants', 'Parties'))]
        for project in projects:
            (project / 'obj').mkdir(exist_ok=True)
            output = project / 'bin/Release/net10.0'
            output.mkdir(parents=True)
            libraries = {'Hexalith.EventStore.' + suffix + '/3.128.4': {'type': 'package'} for suffix in assemblies}
            target = {name: {'type': 'package', 'runtime': {'lib/net10.0/' + name.split('/')[0] + '.dll': {}}}
                      for name in libraries}
            (project / 'obj/project.assets.json').write_text(json.dumps({
                'libraries': libraries, 'targets': {'net10.0': target}, 'packageFolders': {str(cache): {}}}))
            for suffix in assemblies:
                name = 'Hexalith.EventStore.' + suffix
                (output / (name + '.dll')).write_bytes((name + '-qualified-fixture').encode())
        native = self.root / 'references/Hexalith.EventStore/src/Hexalith.EventStore'
        (native / 'Properties').mkdir()
        (native / 'appsettings.json').write_text('{"nativeDefaults":true}')
        (native / 'Properties/launchSettings.json').write_text('{"profiles":{}}')
        (gateway / 'Properties').mkdir()
        (gateway / 'Properties/launchSettings.json').write_text('{"profiles":{}}')
        (gateway / 'bin/Release/net10.0/appsettings.gateway.json').write_text('{"nativeDefaults":true}')
        (gateway / 'Configuration').mkdir()
        (gateway / 'Configuration/appsettings.gateway.json').write_text('{"nativeDefaults":true}')
        files = {
            'Configuration/appsettings.gateway.json': 'src/Hexalith.EventStore/appsettings.json',
            'Properties/launchSettings.json': 'src/Hexalith.EventStore/Properties/launchSettings.json',
        }
        (gateway / 'Configuration/provenance.json').write_text(json.dumps({
            'profile': 'published', 'eventStoreVersion': '3.128.4',
            'sourceRepository': 'https://github.com/Hexalith/Hexalith.EventStore.git', 'sourceCommit': 'a' * 40,
            'files': {relative: {'sourcePath': original, 'sha256': hashlib.sha256((gateway / relative).read_bytes()).hexdigest()}
                      for relative, original in files.items()}}))
        apphost = self.root / 'tests/Hexalith.McpCli.AppHost'
        (apphost / 'DaprComponents').mkdir(parents=True)
        (apphost / 'appsettings.json').write_text('{"testOwned":true}')
        (apphost / 'DaprComponents/accesscontrol.published.yaml').write_text('{"defaultAction":"deny"}')
        self.bin = self.root / 'stub-bin'
        self.bin.mkdir()
        for tool in ('timeout', 'git', 'dotnet', 'docker', 'dapr', 'aspire', 'unshare', 'ip', 'daprd', 'sudo', 'curl'):
            path = self.bin / tool
            path.write_text(TOOL)
            path.chmod(0o700)
        archive = self.root / 'aspire-fixture.tar.gz'
        with tarfile.open(archive, 'w:gz') as release:
            member = tarfile.TarInfo('aspire')
            payload = TOOL.encode()
            member.size = len(payload)
            member.mode = 0o700
            release.addfile(member, io.BytesIO(payload))
        ci = self.tools / 'ci.py'
        ci.write_text(ci.read_text().replace(
            "ASPIRE_CLI_SHA256 = 'f5498a1b30f894186a805c08798d9ca4f112dfc3b5f24ab0acef3f8aa5d009b8'",
            'ASPIRE_CLI_SHA256 = ' + repr(hashlib.sha256(archive.read_bytes()).hexdigest())))
        home = self.root / 'home'
        (home / '.dapr/bin').mkdir(parents=True)
        (home / '.dapr/bin/daprd').symlink_to(self.bin / 'daprd')
        for name in ('dcp/dcp', 'dashboard/Aspire.Dashboard', 'managed/aspire-managed'):
            file = home / '.aspire/bundle' / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('qualified bundle')
        self.env = os.environ.copy()
        self.env.update(FIXTURE_ROOT=str(self.root), HOME=str(home), RUNNER_TEMP=str(self.root),
                        PATH=str(self.bin) + os.pathsep + self.env['PATH'], ASPIRE_EVIDENCE_PATH='evidence',
                        GITHUB_ENV=str(self.root / 'github-env'), TEST_SECRET_TOKEN='fixture-secret-token')
        self.env.pop('MCPCLI_CI_PREPARATION', None)
        self.env.pop('ASPIRE_TEST_PROJECT', None)
        self.env.pop('TEST_PLATFORM', None)
        self.env.pop('GITHUB_ACTIONS', None)
        self.env.pop('RUNNER_ENVIRONMENT', None)

    def invoke(self, script, mode=''):
        self.env['FIXTURE_MODE'] = mode
        return subprocess.run(['bash', str(self.tools / script)], env=self.env, text=True, capture_output=True, timeout=20)

    @property
    def evidence(self):
        return self.root / self.env['ASPIRE_EVIDENCE_PATH']

    def fresh_evidence(self):
        self.env['ASPIRE_EVIDENCE_PATH'] = 'evidence-' + str(time.monotonic_ns())

    def ci_module(self):
        spec = importlib.util.spec_from_file_location('ci_fixture', self.tools / 'ci.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def prepare(self):
        result = self.invoke('prepare-ci.sh')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return json.loads((self.evidence / 'preparation.json').read_text())

    def calls(self):
        return [json.loads(line) for line in (self.root / 'calls.jsonl').read_text().splitlines()]

    def test_preparation_order_bounds_source_flags_and_nonsecret_exports(self):
        prepared = self.prepare()
        calls = self.calls()
        source_builds = [call for call in calls if call[0] == 'dotnet' and call[2] == 'build']
        self.assertEqual(['tests/Hexalith.McpCli.EventStoreGateway.TestHost/Hexalith.McpCli.EventStoreGateway.TestHost.csproj',
                          'src/Hexalith.Tenants/Hexalith.Tenants.csproj', 'src/Hexalith.Parties/Hexalith.Parties.csproj'],
                         [call[3] for call in source_builds])
        self.assertEqual(str(self.root), source_builds[0][1])
        for call in source_builds:
            self.assertIn('-p:UseHexalithProjectReferences=false', call)
            self.assertIn('-p:UseNuGetDeps=true', call)
            self.assertIn('Release', call)
            self.assertIn('-p:HexalithEventStoreFromSource=false', call)
            self.assertIn('-p:HexalithEventStoreVersion=3.128.4', call)
            self.assertNotIn('-p:HexalithEventStoreFromSource=true', call)
        for call in source_builds:
            for package_pin in ('-p:HexalithMemoriesVersion=3.0.11', '-p:HexalithTenantsVersion=5.11.2'):
                self.assertEqual('src/Hexalith.Parties/Hexalith.Parties.csproj' == call[3], package_pin in call)
        deadlines = [call[4] for call in calls if call[0] == 'timeout' and call[5:7] == ['dotnet', 'build']]
        self.assertEqual(['300'] * 3, deadlines)
        self.assertLess(next(index for index, call in enumerate(calls) if call[0] == 'unshare'), calls.index(source_builds[0]))
        self.assertEqual(3, len(prepared['sources']))
        checkouts = [self.root / 'references' / module for module in
                     ('Hexalith.EventStore', 'Hexalith.Tenants', 'Hexalith.Parties')]
        for source, checkout in zip(prepared['sources'], checkouts):
            self.assertEqual(checkout.name, source['module'])
            self.assertEqual(str(checkout.relative_to(self.root)), source['path'])
            self.assertEqual(hashlib.sha1(str(checkout).encode()).hexdigest(), source['commit'])
            self.assertEqual('M  ' + checkout.name + '-fixture.txt', source['status'])
        for arguments in (['rev-parse', 'HEAD'], ['status', '--porcelain', '--untracked-files=normal']):
            self.assertEqual([str(checkout) for checkout in checkouts],
                             [call[1] for call in calls if call[0] == 'git' and call[2:] == arguments][:3])
        tools = prepared['tools']
        self.assertEqual({'aspire', 'dapr', 'dotnet'}, set(tools['executables']))
        for name, executable in tools['executables'].items():
            self.assertEqual(str(self.bin / name), executable['path'])
            self.assertRegex(executable['sha256'], r'\A[0-9a-f]{64}\Z')
            self.assertEqual(hashlib.sha256((self.bin / name).read_bytes()).hexdigest(), executable['sha256'])
        self.assertRegex(tools['daprdSha256'], r'\A[0-9a-f]{64}\Z')
        self.assertEqual(hashlib.sha256((self.bin / 'daprd').read_bytes()).hexdigest(), tools['daprdSha256'])
        bundle_hashes = json.loads((self.evidence / 'aspire-bundle-hashes.json').read_text())
        self.assertEqual({'dcp/dcp', 'dashboard/Aspire.Dashboard', 'managed/aspire-managed'}, set(bundle_hashes))
        for relative, digest in bundle_hashes.items():
            self.assertRegex(digest, r'\A[0-9a-f]{64}\Z')
            self.assertEqual(hashlib.sha256(b'qualified bundle').hexdigest(), digest)
        for relative in ('dcp/dcp', 'dashboard/Aspire.Dashboard'):
            self.assertEqual(str(Path(self.env['HOME']) / '.aspire/bundle' / relative), tools[relative]['path'])
            self.assertEqual(bundle_hashes[relative], tools[relative]['sha256'])
        self.assertEqual(['3.128.4'] * 3,
                         [source['HexalithEventStoreVersion'] for source in prepared['sources']])
        self.assertEqual({'profile': 'published', 'version': '3.128.4', 'sourceCommit': 'a' * 40},
                         {key: prepared['gateway'][key] for key in ('profile', 'version', 'sourceCommit')})
        self.assertEqual({'Hexalith.Tenants', 'Hexalith.Parties'}, set(prepared['gateway']['domainHosts']))
        property_calls = [call for call in calls if call[0] == 'dotnet' and call[2] == 'msbuild']
        self.assertEqual(3, len(property_calls))
        for call in property_calls:
            self.assertIn('-getProperty:HexalithEventStoreVersion', call)
            self.assertIn('-p:UseHexalithProjectReferences=false', call)
            self.assertIn('-p:UseNuGetDeps=true', call)
            self.assertIn('-p:HexalithEventStoreFromSource=false', call)
            self.assertIn('-p:HexalithEventStoreVersion=3.128.4', call)
        self.assertEqual(['timeout', str(self.root), '--signal=TERM', '--kill-after=30s', '2280',
                          'python3', 'tools/live-topology/ci.py', 'prepare'], calls[0])
        self.assertEqual(['MCPCLI_CI_PREPARATION=' + str(self.evidence / 'preparation.json')], (self.root / 'github-env').read_text().splitlines())
        self.assertNotIn('fixture-secret-token', json.dumps(prepared))

    def test_published_gateway_profile_binds_both_vector_and_independent_smoke(self):
        self.prepare()
        result = self.invoke('run-ci.sh')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        actual = [json.loads(line) for line in (self.root / 'runner-gateway-environment.jsonl').read_text().splitlines()]
        self.assertEqual([{'profile': 'true', 'sourceCommit': 'a' * 40}] * 2, actual)

    def test_changed_gateway_package_bytes_refuse_before_any_live_runner(self):
        self.prepare()
        with ZipFile(self.root / 'package-cache/hexalith.eventstore.gateway/3.128.4/hexalith.eventstore.gateway.3.128.4.nupkg', 'a') as archive:
            archive.writestr('changed.txt', b'changed')
        result = self.invoke('run-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('gateway package identity or bytes changed', result.stderr)
        self.assertFalse((self.root / 'runner-gateway-environment.jsonl').exists())

    def test_different_gateway_cohort_refuses_before_build_or_runtime(self):
        result = self.invoke('prepare-ci.sh', 'wrong-package-cohort')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('did not select the exact published EventStore cohort', result.stderr)
        self.assertFalse(any(call[0] == 'dotnet' and call[2] == 'build' for call in self.calls()))

    def test_actual_domain_asset_version_and_project_mutations_refuse_prepare_and_execute(self):
        for module in ('Tenants', 'Parties'):
            asset = self.root / f'references/Hexalith.{module}/src/Hexalith.{module}/obj/project.assets.json'
            original = asset.read_text()
            for phase in ('prepare', 'run'):
                for defect in ('transitive-version', 'project-type'):
                    with self.subTest(module=module, phase=phase, defect=defect):
                        self.fresh_evidence()
                        if phase == 'run': self.prepare()
                        (self.root / 'runner-gateway-environment.jsonl').unlink(missing_ok=True)
                        changed = json.loads(original)
                        identity = 'Hexalith.EventStore.Contracts/3.128.4'
                        if defect == 'transitive-version':
                            changed['libraries']['Hexalith.EventStore.Contracts/3.128.3'] = changed['libraries'].pop(identity)
                        else:
                            changed['libraries'][identity]['type'] = 'project'
                        asset.write_text(json.dumps(changed))
                        try:
                            result = self.invoke('prepare-ci.sh' if phase == 'prepare' else 'run-ci.sh')
                            self.assertNotEqual(0, result.returncode)
                            self.assertIn('restored assets must contain only the exact published EventStore package cohort', result.stderr)
                            self.assertFalse((self.root / 'runner-gateway-environment.jsonl').exists())
                        finally:
                            asset.write_text(original)

    def test_archive_extracted_deployed_and_configuration_mutations_refuse_before_runners(self):
        package = self.root / 'package-cache/hexalith.eventstore.gateway/3.128.4'
        deployed = self.root / 'tests/Hexalith.McpCli.EventStoreGateway.TestHost/bin/Release/net10.0'
        source = self.root / 'references/Hexalith.EventStore/src/Hexalith.EventStore/appsettings.json'
        cases = [package / 'hexalith.eventstore.gateway.nuspec',
                 package / 'lib/net10.0/Hexalith.EventStore.Gateway.dll',
                 deployed / 'Hexalith.EventStore.Gateway.dll',
                 deployed / 'appsettings.gateway.json', source,
                 deployed.parents[2] / 'Configuration/appsettings.gateway.json',
                 deployed.parents[2] / 'Properties/launchSettings.json']
        for phase in ('prepare', 'run'):
            for path in cases:
                with self.subTest(phase=phase, path=str(path.relative_to(self.root))):
                    self.fresh_evidence()
                    if phase == 'run': self.prepare()
                    original = path.read_bytes()
                    path.write_bytes(original + b'changed')
                    try:
                        result = self.invoke('prepare-ci.sh' if phase == 'prepare' else 'run-ci.sh')
                        self.assertNotEqual(0, result.returncode)
                        self.assertIn('differs from', result.stderr)
                        self.assertFalse((self.root / 'runner-gateway-environment.jsonl').exists())
                    finally:
                        path.write_bytes(original)

    def test_embedded_archive_identity_and_source_are_validated_before_preparation(self):
        folder = self.root / 'package-cache/hexalith.eventstore.gateway/3.128.4'
        archive = folder / 'hexalith.eventstore.gateway.3.128.4.nupkg'
        nuspec = folder / 'hexalith.eventstore.gateway.nuspec'
        original_archive, original_nuspec = archive.read_bytes(), nuspec.read_bytes()
        for before, after in ((b'<id>Hexalith.EventStore.Gateway</id>', b'<id>Wrong.Package</id>'),
                              (b'<version>3.128.4</version>', b'<version>3.128.3</version>'),
                              (b'a' * 40, b'not-a-source-commit')):
            with self.subTest(replacement=after):
                self.fresh_evidence()
                with ZipFile(archive) as opened:
                    files = {name: opened.read(name) for name in opened.namelist()}
                name = next(name for name in files if name.endswith('.nuspec'))
                files[name] = files[name].replace(before, after)
                with ZipFile(archive, 'w') as changed:
                    for name, value in files.items(): changed.writestr(name, value)
                nuspec.write_bytes(original_nuspec.replace(before, after))
                try:
                    result = self.invoke('prepare-ci.sh')
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn('Package archive must identify its exact published identity and source', result.stderr)
                    self.assertFalse((self.root / 'runner-gateway-environment.jsonl').exists())
                finally:
                    archive.write_bytes(original_archive)
                    nuspec.write_bytes(original_nuspec)

    def test_configuration_change_with_preserved_native_parity_still_refuses(self):
        self.prepare()
        host = self.root / 'tests/Hexalith.McpCli.EventStoreGateway.TestHost'
        for path in (self.root / 'references/Hexalith.EventStore/src/Hexalith.EventStore/appsettings.json',
                     host / 'Configuration/appsettings.gateway.json',
                     host / 'bin/Release/net10.0/appsettings.gateway.json'):
            path.write_text('{"changedButMatching":true}')
        manifest = host / 'Configuration/provenance.json'
        changed = json.loads(manifest.read_text())
        changed['files']['Configuration/appsettings.gateway.json']['sha256'] = hashlib.sha256(
            (host / 'Configuration/appsettings.gateway.json').read_bytes()).hexdigest()
        manifest.write_text(json.dumps(changed))
        result = self.invoke('run-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('gateway package identity or bytes changed', result.stderr)
        self.assertFalse((self.root / 'runner-gateway-environment.jsonl').exists())

    def test_snapshot_manifest_cohort_source_identity_and_blob_binding_refuse_before_runners(self):
        host = self.root / 'tests/Hexalith.McpCli.EventStoreGateway.TestHost'
        manifest = host / 'Configuration/provenance.json'
        original = manifest.read_text()
        cases = [('eventStoreVersion', '3.128.3'), ('sourceCommit', 'not-a-commit'),
                 ('sourceRepository', 'https://example.invalid/forged'), ('profile', 'native')]
        for phase in ('prepare', 'run'):
            for key, value in cases:
                with self.subTest(phase=phase, field=key):
                    self.fresh_evidence()
                    if phase == 'run': self.prepare()
                    changed = json.loads(original)
                    changed[key] = value
                    manifest.write_text(json.dumps(changed))
                    try:
                        result = self.invoke('prepare-ci.sh' if phase == 'prepare' else 'run-ci.sh')
                        self.assertNotEqual(0, result.returncode)
                        self.assertIn('snapshot must declare its exact published cohort and native source identity', result.stderr)
                        self.assertFalse((self.root / 'runner-gateway-environment.jsonl').exists())
                    finally:
                        manifest.write_text(original)
        # A freshly rehashed snapshot still must match the exact declared source blob.
        self.fresh_evidence()
        snapshot = host / 'Configuration/appsettings.gateway.json'
        snapshot.write_text('{"changed":true}')
        changed = json.loads(original)
        changed['files']['Configuration/appsettings.gateway.json']['sha256'] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(changed))
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('snapshot differs from its exact native source blob', result.stderr)
        self.assertFalse((self.root / 'runner-gateway-environment.jsonl').exists())

    def test_second_provenance_check_refuses_drift_after_vectors_before_smoke(self):
        self.prepare()
        result = self.invoke('run-ci.sh', 'tamper-after-vectors')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Deployed EventStore binary differs from its archive', result.stderr)
        actual = (self.root / 'runner-gateway-environment.jsonl').read_text().splitlines()
        self.assertEqual(1, len(actual), 'The independent smoke must not start after vector-time drift.')

    def test_fresh_pkcs8_private_keys_are_redacted_in_direct_escaped_and_xml_diagnostics(self):
        import base64
        from html import escape
        pem = subprocess.check_output(
            ['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:2048'],
            stderr=subprocess.DEVNULL)
        key = base64.b64encode(subprocess.check_output(
            ['openssl', 'pkcs8', '-topk8', '-nocrypt', '-outform', 'DER'], input=pem,
            stderr=subprocess.DEVNULL)).decode()
        module = self.ci_module()
        field = 'Authentication__BoundStreamRead__PrivateKey'
        direct = json.dumps({field: key, 'meaningful': 'retained', 'publicKey': 'nonsecret-public-trust'})
        for text in (direct, json.dumps({'diagnostic': direct}), field + '=' + key,
                     json.dumps({'diagnostic': json.dumps({'nested': direct})})):
            sanitized = module.sanitized(text)
            self.assertNotIn(key, sanitized)
            if text != field + '=' + key: self.assertIn('retained', sanitized)
        for text in ('<error message="' + escape(direct, quote=True) + '" />',
                     '<PrivateKey>' + key + '</PrivateKey>',
                     '<setting name="' + field + '" value="' + key + '" other="retained" />'):
            sanitized = module.sanitized_xml(text)
            self.assertNotIn(key, sanitized)
            self.assertIn('[REDACTED]', sanitized)

    def test_repository_sdk_rollforward_accepts_selected_newer_patch(self):
        result = self.invoke('prepare-ci.sh', 'sdk-patch-rollforward')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        receipt = json.loads((self.evidence / 'preparation.json').read_text())
        self.assertEqual('prepared', receipt['result'])
        self.assertEqual('10.0.403', receipt['tools']['dotnet'])
        self.assertEqual({'version': '10.0.402', 'rollForward': 'latestPatch'}, receipt['tools']['sdkPolicy'])
        version_call = next(call for call in self.calls() if call[0] == 'dotnet' and call[2:] == ['--version'])
        self.assertEqual(str(self.root), version_call[1])

    def test_repository_sdk_resolution_failure_stops_before_source_builds(self):
        result = self.invoke('prepare-ci.sh', 'missing-sdk')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('dotnet --version exited 145', result.stderr)
        receipt = json.loads((self.evidence / 'preparation.json').read_text())
        self.assertEqual('failed', receipt['result'])
        self.assertEqual('A compatible .NET SDK was not found.\n', (self.evidence / 'dotnet-version.stderr.txt').read_text())
        self.assertFalse(any(call[0] == 'dotnet' and call[2] == 'build' for call in self.calls()))

    def test_prerequisite_failures_precede_source_builds(self):
        for mode, message in [('namespace-denied', 'unshare --user'),
                              ('docker-unavailable', 'docker info'),
                              ('wrong-dapr', 'Dapr CLI 1.18.2 and initialized runtime 1.18.7 are required'),
                              ('undeclared-source', 'Missing declared direct root source prerequisite'),
                              ('copied-source', 'is not its own Git working tree')]:
            with self.subTest(mode=mode):
                self.fresh_evidence()
                (self.root / 'calls.jsonl').unlink(missing_ok=True)
                result = self.invoke('prepare-ci.sh', mode)
                self.assertNotEqual(0, result.returncode)
                self.assertIn(message, result.stderr)
                self.assertEqual('failed', json.loads((self.evidence / 'preparation.json').read_text())['result'])
                self.assertFalse(any(call[0] == 'dotnet' and call[2] == 'build' for call in self.calls()))

    def assert_no_build_or_live(self):
        calls = self.calls() if (self.root / 'calls.jsonl').exists() else []
        self.assertFalse(any(call[0] == 'dotnet' and call[2] == 'build' or
                             any(value.endswith(('run-vectors.py', 'run-isolated.py')) for value in call)
                             for call in calls))

    def test_platform_and_python_patch_prerequisites_stop_before_commands(self):
        module = self.ci_module()
        for version, system, machine in [((3, 11, 3), 'Linux', 'x86_64'),
                                          ((3, 12, 0), 'Windows', 'x86_64'),
                                          ((3, 12, 0), 'Linux', 'aarch64')]:
            with self.subTest(version=version, system=system, machine=machine):
                self.fresh_evidence()
                with patch.dict(os.environ, self.env, clear=True), patch.object(module.sys, 'version_info', version), \
                        patch.object(module.platform, 'system', return_value=system), \
                        patch.object(module.platform, 'machine', return_value=machine), patch.object(module, 'bounded') as command:
                    evidence = module.evidence_directory(preparing=True)
                    with self.assertRaisesRegex(RuntimeError, 'Live CI requires Linux amd64 and Python 3.11.4 or later.'):
                        module.prepare(evidence)
                    command.assert_not_called()
                self.assertEqual('failed', json.loads((evidence / 'preparation.json').read_text())['result'])

    def test_compression_libraries_are_required_before_commands(self):
        module = self.ci_module()
        for missing in ('z', 'zstd'):
            with self.subTest(missing=missing):
                self.fresh_evidence()
                with patch.dict(os.environ, self.env, clear=True), \
                        patch.object(module.ctypes.util, 'find_library', side_effect=lambda name: None if name == missing else name), \
                        patch.object(module, 'bounded') as command:
                    evidence = module.evidence_directory(preparing=True)
                    with self.assertRaisesRegex(RuntimeError, 'Missing prerequisite shared library: ' + missing):
                        module.prepare(evidence)
                    command.assert_not_called()
                self.assertEqual('failed', json.loads((evidence / 'preparation.json').read_text())['result'])

    def test_dapr_cli_and_initialized_runtime_are_independently_required(self):
        result = self.invoke('prepare-ci.sh', 'wrong-dapr-cli')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Dapr CLI 1.18.2 and initialized runtime 1.18.7 are required', result.stderr)
        self.assert_no_build_or_live()
        self.fresh_evidence()
        (Path(self.env['HOME']) / '.dapr/bin/daprd').unlink()
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Missing initialized Dapr runtime:', result.stderr)
        self.assert_no_build_or_live()

    def test_incomplete_embedded_bundle_stops_before_builds(self):
        result = self.invoke('prepare-ci.sh', 'incomplete-bundle')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Selected qualified Aspire CLI did not extract its required embedded bundle files.', result.stderr)
        self.assert_no_build_or_live()

    def test_missing_git_marker_and_symlinked_source_stop_before_builds(self):
        checkout = self.root / 'references/Hexalith.Parties'
        (checkout / '.git').unlink()
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Missing declared direct root source prerequisite:', result.stderr)
        self.assert_no_build_or_live()
        (checkout / '.git').touch()
        target = self.root / 'actual-parties'
        checkout.rename(target)
        checkout.symlink_to(target, target_is_directory=True)
        self.fresh_evidence()
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Missing declared direct root source prerequisite:', result.stderr)
        self.assert_no_build_or_live()

    def test_diagnostic_copy_excludes_symlinked_runs_and_files(self):
        module = self.ci_module()
        runtime = self.root / 'runtime'
        runs = runtime / 'runs'
        runs.mkdir(parents=True)
        foreign = self.root / 'foreign'
        foreign.mkdir()
        (foreign / 'command.stdout.txt').write_text('foreign diagnostic')
        (runs / 'linked-run').symlink_to(foreign, target_is_directory=True)
        local = runs / 'local'
        local.mkdir()
        (local / 'command.stdout.txt').symlink_to(foreign / 'command.stdout.txt')
        (local / 'command.stderr.txt').write_text('owned diagnostic')
        output = self.root / 'copied'
        module.copy_diagnostics(runtime, output)
        self.assertEqual(['local/command.stderr.txt'], [str(path.relative_to(output)) for path in output.rglob('*') if path.is_file()])
        self.assertEqual('owned diagnostic', (output / 'local/command.stderr.txt').read_text())
        self.assertEqual('foreign diagnostic', (foreign / 'command.stdout.txt').read_text())

    def test_hosted_namespace_setup_reprobes_before_building_sources(self):
        self.env.update(GITHUB_ACTIONS='true', RUNNER_ENVIRONMENT='github-hosted')
        result = self.invoke('prepare-ci.sh', 'namespace-needs-setup')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        calls = self.calls()
        probes = [index for index, call in enumerate(calls) if call[0] == 'unshare']
        setup = next(index for index, call in enumerate(calls) if call[0] == 'sudo')
        build = next(index for index, call in enumerate(calls) if call[0] == 'dotnet' and call[2] == 'build')
        self.assertEqual(2, len(probes))
        self.assertLess(probes[0], setup)
        self.assertLess(setup, probes[1])
        self.assertLess(probes[1], build)
        self.assertIn('Operation not permitted', (self.evidence / 'namespace-probe.stderr.txt').read_text())

    def test_hosted_namespace_setup_and_reprobe_failures_stop_source_builds(self):
        self.env.update(GITHUB_ACTIONS='true', RUNNER_ENVIRONMENT='github-hosted')
        for mode in ('namespace-setup-failure', 'namespace-still-denied'):
            with self.subTest(mode=mode):
                self.fresh_evidence()
                (self.root / 'calls.jsonl').unlink(missing_ok=True)
                result = self.invoke('prepare-ci.sh', mode)
                self.assertNotEqual(0, result.returncode)
                self.assertIn('exited 1', result.stderr)
                self.assertIn('sudo -n sysctl' if mode == 'namespace-setup-failure' else 'unshare --user', result.stderr)
                self.assertEqual('failed', json.loads((self.evidence / 'preparation.json').read_text())['result'])
                self.assertFalse(any(call[0] == 'dotnet' and call[2] == 'build' for call in self.calls()))

    def test_self_hosted_namespace_failure_never_changes_host_configuration(self):
        self.env.update(GITHUB_ACTIONS='true', RUNNER_ENVIRONMENT='self-hosted')
        result = self.invoke('prepare-ci.sh', 'namespace-denied')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('unshare --user', result.stderr)
        self.assertFalse(any(call[0] == 'sudo' for call in self.calls()))

    def test_missing_source_is_named_before_build(self):
        source = self.root / 'references/Hexalith.Parties/src/Hexalith.Parties/Hexalith.Parties.csproj'
        source.unlink()
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn(str(source), result.stderr)
        self.assertFalse(any(call[0] == 'dotnet' and call[2] == 'build' for call in self.calls()))

    def test_missing_tool_is_named_before_build(self):
        for tool in ('python3', 'bash', 'curl', 'dirname'):
            (self.bin / tool).unlink(missing_ok=True)
            (self.bin / tool).symlink_to(shutil.which(tool))
        self.env['PATH'] = str(self.bin)
        (self.bin / 'ip').unlink()
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Missing prerequisite: ip', result.stderr)

    def test_missing_bundle_is_provisioned_before_build_and_setup_failure_propagates(self):
        dashboard = Path(self.env['HOME']) / '.aspire/bundle/dashboard/Aspire.Dashboard'
        dashboard.unlink()
        self.prepare()
        self.assertTrue(dashboard.is_file())
        self.assertTrue(any(call[0] == 'aspire' and call[2] == 'setup' for call in self.calls()))
        dashboard.unlink()
        self.fresh_evidence()
        result = self.invoke('prepare-ci.sh', 'bundle-setup-failure')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('aspire setup', result.stderr)
        self.assertIn('exited 18', result.stderr)

    def test_source_failure_and_timeout_never_prepare_or_execute_live(self):
        for mode, code in [('build-failure', 23), ('build-timeout', 124)]:
            with self.subTest(mode=mode):
                self.fresh_evidence()
                (self.root / 'calls.jsonl').unlink(missing_ok=True)
                result = self.invoke('prepare-ci.sh', mode)
                self.assertNotEqual(0, result.returncode)
                self.assertIn(f'exited {code}', result.stderr)
                self.assertIn('dotnet build ', result.stderr)
                self.assertFalse(any('run-vectors.py' in str(call) or 'bootstrap-runtime.py' in str(call) for call in self.calls()))

    def test_stdout_only_source_failure_names_both_retained_output_paths(self):
        result = self.invoke('prepare-ci.sh', 'build-stdout-failure')
        self.assertEqual(1, result.returncode)
        command = ('dotnet build src/Hexalith.Tenants/Hexalith.Tenants.csproj --configuration Release '
                   '-warnaserror -m:1 -p:UseHexalithProjectReferences=false -p:UseNuGetDeps=true '
                   '-p:HexalithEventStoreFromSource=false -p:HexalithEventStoreVersion=3.128.4')
        stdout = self.evidence / 'Hexalith.Tenants-build.stdout.txt'
        stderr = self.evidence / 'Hexalith.Tenants-build.stderr.txt'
        error = f'{command} exited 23; stdout: {stdout}; stderr: {stderr}'
        self.assertEqual(f'Live CI failed: RuntimeError: {error}\n', result.stderr)
        self.assertIn('Running (300s): ' + command, result.stdout)
        self.assertEqual('named source build failure\n', stdout.read_text())
        self.assertEqual('', stderr.read_text())
        receipt = json.loads((self.evidence / 'preparation.json').read_text())
        self.assertEqual('failed', receipt['result'])
        self.assertEqual('RuntimeError: ' + error, receipt['error'])
        self.assertEqual({'result': 'not-run', 'fullLiveAccepted': False},
                         json.loads((self.evidence / 'ci-live.json').read_text()))
        self.assertFalse(any(any(value.endswith(('bootstrap-runtime.py', 'run-vectors.py', 'run-isolated.py'))
                                 for value in call) for call in self.calls()))

    def test_complete_lane_and_smoke_acceptance_retains_only_sanitized_diagnostics(self):
        prepared = self.prepare()
        result = self.invoke('run-ci.sh')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        receipt = json.loads((self.evidence / 'ci-live.json').read_text())
        self.assertIs(True, receipt['fullLiveAccepted'])
        self.assertEqual(21, receipt['vectors']['count'])
        self.assertEqual('passed', receipt['smoke']['result'])
        files = list(Path(receipt['output']).rglob('*'))
        self.assertEqual(22, len([file for file in files if file.name == 'result.json']))
        self.assertFalse(any(file.name in ('issuer.key', 'dump.rdb') for file in files))
        content = ''.join(file.read_text() for file in files if file.is_file())
        secrets = ['fixture credential', 'fixture-secret-token', 'eyJfixture.payload.signature',
                   *(self.root / 'generated-signing-keys.txt').read_text().splitlines()]
        for secret in secrets:
            self.assertNotIn(secret, content)
        deadlines = [call[4] for call in self.calls() if call[0] == 'timeout' and any(value.endswith(('run-vectors.py', 'run-isolated.py')) for value in call)]
        self.assertEqual(['16200', '960'], deadlines)
        self.assertIn(['timeout', str(self.root), '--signal=TERM', '--kill-after=30s', '17700',
                       'python3', 'tools/live-topology/ci.py', 'run'], self.calls())
        self.assertTrue(Path(prepared['runtime']).is_dir())
        self.fresh_evidence()
        failed_preparation = self.invoke('prepare-ci.sh', 'wrong-dapr')
        self.assertNotEqual(0, failed_preparation.returncode)
        self.assertIn('Dapr CLI 1.18.2 and initialized runtime 1.18.7 are required', failed_preparation.stderr)
        self.assertIs(False, json.loads((self.evidence / 'ci-live.json').read_text())['fullLiveAccepted'])

    def test_vector_nonacceptance_and_nonzero_exits_still_run_smoke(self):
        self.prepare()
        preparation = json.loads((self.evidence / 'preparation.json').read_text())
        for mode in ('partial-vectors', 'skipped-vector', 'incomplete-vectors', 'failed-vectors', 'missing-vectors', 'malformed-vectors', 'vector-exit', 'vector-timeout', 'duplicate-isolation', 'stale-isolation'):
            with self.subTest(mode=mode):
                shutil.rmtree(Path(preparation['runtime']) / 'runs', ignore_errors=True)
                result = self.invoke('run-ci.sh', mode)
                self.assertNotEqual(0, result.returncode)
                receipt = json.loads((self.evidence / 'ci-live.json').read_text())
                self.assertIs(False, receipt['fullLiveAccepted'])
                self.assertEqual('passed', receipt['smoke']['result'])
                expected = {'missing-vectors': 'live-lane.json', 'malformed-vectors': 'Expecting property name enclosed in double quotes',
                            'vector-exit': 'exited 19', 'failed-vectors': 'exited 1',
                            'vector-timeout': 'exited 124', 'stale-isolation': 'Isolated receipt is outside the prepared runtime.'}
                self.assertIn(expected.get(mode, 'Complete current passing evidence for all 21 vectors is required'), result.stderr)
                if mode == 'failed-vectors':
                    self.assertIn('failed Operations: sample.operation-00', result.stderr)
                    self.assertEqual([{'operation': 'sample.operation-00', 'result': 'failed',
                                       'error': 'phase observe-party: gateway_error 500'}], receipt['vectors']['failures'])

    def test_each_vector_acceptance_field_is_independently_required(self):
        prepared = self.prepare()
        for mode in ('wrong-coverage', 'wrong-lane-result', 'wrong-passed-count', 'wrong-failed-count',
                     'wrong-outcome-operation', 'wrong-outcome-exit', 'extra-approved-vector', 'duplicate-approved-operation'):
            with self.subTest(mode=mode):
                shutil.rmtree(Path(prepared['runtime']) / 'runs', ignore_errors=True)
                modules = self.root / 'tools/conformance-vectors/v1/modules'
                extra = modules / 'extra.vector.json'
                if mode == 'extra-approved-vector':
                    extra.write_text(json.dumps({'operation': 'sample.operation-00'}))
                original = (modules / '0.vector.json').read_text()
                if mode == 'duplicate-approved-operation':
                    (modules / '0.vector.json').write_text((modules / '1.vector.json').read_text())
                try:
                    result = self.invoke('run-ci.sh', mode)
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn('Complete current passing evidence for all 21 vectors is required', result.stderr)
                    receipt = json.loads((self.evidence / 'ci-live.json').read_text())
                    self.assertIs(False, receipt['fullLiveAccepted'])
                    self.assertEqual('passed', receipt['smoke']['result'])
                finally:
                    extra.unlink(missing_ok=True)
                    (modules / '0.vector.json').write_text(original)

    def test_lane_level_errors_are_named_and_only_failed_operations_are_failures(self):
        prepared = self.prepare()
        for mode in ('lane-preflight', 'lane-admission', 'lane-coverage', 'lane-runtime'):
            with self.subTest(mode=mode):
                shutil.rmtree(Path(prepared['runtime']) / 'runs', ignore_errors=True)
                result = self.invoke('run-ci.sh', mode)
                self.assertNotEqual(0, result.returncode)
                message = 'named ' + mode + ' prerequisite failure'
                self.assertIn(message, result.stderr)
                self.assertIn(' exited 1; stdout: ', result.stderr)
                self.assertIn('vectors-process.stdout.txt', result.stderr)
                receipt = json.loads((self.evidence / 'ci-live.json').read_text())
                self.assertEqual(message, receipt['vectors']['laneError'])
                self.assertIn(message, receipt['vectors']['error'])
                lane_receipt = 'lane receipt: ' + str(Path(receipt['output']) / 'vectors/live-lane.json')
                self.assertIn(lane_receipt, result.stderr)
                self.assertIn(lane_receipt, receipt['vectors']['error'])
                self.assertIs(False, receipt['fullLiveAccepted'])
                self.assertEqual('passed', receipt['smoke']['result'])
                self.assertEqual([], receipt['vectors']['failures'])
                self.assertNotIn('failed Operations:', result.stderr)

    def test_aggregate_deadline_names_interrupted_operation_from_pending_lane(self):
        self.prepare()
        result = self.invoke('run-ci.sh', 'lane-timeout')
        self.assertNotEqual(0, result.returncode)
        receipt = json.loads((self.evidence / 'ci-live.json').read_text())
        self.assertIs(False, receipt['fullLiveAccepted'])
        self.assertEqual('passed', receipt['smoke']['result'])
        self.assertIsNone(receipt['vectors']['laneError'])
        self.assertEqual([{'operation': 'sample.operation-00', 'result': 'failed',
                           'error': 'phase observe: assertion mismatch'}], receipt['vectors']['failures'])
        self.assertEqual([{'operation': 'sample.operation-01', 'result': 'running', 'error': None}],
                         receipt['vectors']['interrupted'])
        for message in ('exited 124', 'failed Operations: sample.operation-00;',
                        'interrupted Operations: sample.operation-01;', 'vectors-process.stdout.txt'):
            self.assertIn(message, result.stderr)
            self.assertIn(message, receipt['vectors']['error'])
        self.assertNotIn('sample.operation-02', result.stderr)

    def test_smoke_requires_exactly_one_runtime_receipt(self):
        prepared = self.prepare()
        for mode in ('missing-smoke-receipt', 'duplicate-smoke-receipt'):
            with self.subTest(mode=mode):
                shutil.rmtree(Path(prepared['runtime']) / 'runs', ignore_errors=True)
                result = self.invoke('run-ci.sh', mode)
                self.assertNotEqual(0, result.returncode)
                self.assertIn('Independent smoke omitted its isolated runtime receipt.', result.stderr)
                receipt = json.loads((self.evidence / 'ci-live.json').read_text())
                self.assertEqual('passed', receipt['vectors']['result'])
                self.assertIs(False, receipt['fullLiveAccepted'])

    def test_smoke_skips_missing_receipts_nonzero_and_cleanup_fail_closed(self):
        preparation = self.prepare()
        for mode in ('skipped-smoke', 'missing-smoke', 'smoke-exit', 'missing-cleanup', 'wrong-smoke-case', 'skipped-smoke-count', 'empty-smoke',
                     'smoke-assembly-error', 'wrong-smoke-type'):
            with self.subTest(mode=mode):
                shutil.rmtree(Path(preparation['runtime']) / 'runs', ignore_errors=True)
                result = self.invoke('run-ci.sh', mode)
                self.assertNotEqual(0, result.returncode)
                self.assertIs(False, json.loads((self.evidence / 'ci-live.json').read_text())['fullLiveAccepted'])
                expected = {'missing-smoke': 'tests.xml', 'smoke-exit': 'exited 17',
                            'missing-cleanup': 'Private runtime did not prove prerequisites, private namespaces and owned cleanup.'}
                self.assertIn(expected.get(mode, 'Independent smoke must contain exactly one passing, unskipped authenticated Gateway case.'), result.stderr)

    def test_smoke_cleanup_proof_is_required_after_all_vectors_pass(self):
        self.prepare()
        result = self.invoke('run-ci.sh', 'smoke-missing-cleanup')
        self.assertNotEqual(0, result.returncode)
        receipt = json.loads((self.evidence / 'ci-live.json').read_text())
        self.assertEqual('passed', receipt['vectors']['result'])
        self.assertIs(False, receipt['fullLiveAccepted'])
        self.assertIn('Private runtime did not prove prerequisites, private namespaces and owned cleanup.', receipt['error'])
        self.assertIn('Private runtime did not prove prerequisites', result.stderr)

    def test_extra_runtime_refuses_complete_lane_acceptance(self):
        self.prepare()
        result = self.invoke('run-ci.sh', 'extra-runtime')
        self.assertNotEqual(0, result.returncode)
        receipt = json.loads((self.evidence / 'ci-live.json').read_text())
        self.assertEqual('passed', receipt['vectors']['result'])
        self.assertEqual('passed', receipt['smoke']['result'])
        self.assertIs(False, receipt['fullLiveAccepted'])
        self.assertIn('Expected exactly 21 fresh vector runtimes and one independent smoke runtime.', result.stderr)

    def test_generation_child_logs_and_xml_are_redacted(self):
        self.prepare()
        result = self.invoke('run-ci.sh', 'generation-secrets')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        receipt = json.loads((self.evidence / 'ci-live.json').read_text())
        content = ''.join(path.read_text() for path in Path(receipt['output']).rglob('*') if path.is_file())
        secrets = ['fixture credential', 'fixture-secret-token', 'eyJfixture.payload.signature',
                   *(self.root / 'generated-signing-keys.txt').read_text().splitlines()]
        for secret in secrets:
            self.assertNotIn(secret, content)
        for name in ('child.stdout.txt', 'tests.xml'):
            child = Path(receipt['output']) / 'vectors/sample.operation-00' / name
            self.assertIn('[REDACTED PEM]', child.read_text())
            self.assertIn('[REDACTED JWT]', child.read_text())
            self.assertIn('"SigningKey": "[REDACTED]"', child.read_text())

    def test_missing_preparation_and_reused_runtime_refuse_live(self):
        result = self.invoke('run-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('A task-owned prepared evidence directory is required.', result.stderr)
        prepared = self.prepare()
        stale = Path(prepared['runtime']) / 'runs/old-generation'
        stale.mkdir(parents=True)
        (stale / 'command.stdout.txt').write_text('previous invocation diagnostics')
        result = self.invoke('run-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('fresh prepared runtime', result.stderr)
        self.assertFalse(any('run-vectors.py' in str(call) for call in self.calls()))
        receipt = json.loads((self.evidence / 'ci-live.json').read_text())
        self.assertFalse((self.evidence / receipt['runId']).exists())
        self.assertEqual('previous invocation diagnostics', (stale / 'command.stdout.txt').read_text())

    def test_changed_prepared_binary_refuses_live(self):
        prepared = self.prepare()
        (Path(prepared['runtime']) / 'bin/sentry').write_text('tampered')
        result = self.invoke('run-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('binary hash mismatch: sentry', result.stderr)
        self.assertFalse(any('run-vectors.py' in str(call) for call in self.calls()))

    def test_caller_contract_and_unsafe_evidence_paths_are_refused(self):
        for key, value, message in [('ASPIRE_TEST_PROJECT', 'other-tests', 'ASPIRE_TEST_PROJECT must be tests/Hexalith.McpCli.Integration.Tests.'),
                                   ('TEST_PLATFORM', 'vstest', 'TEST_PLATFORM must be microsoft-testing-platform.'),
                                   ('ASPIRE_EVIDENCE_PATH', '../outside', 'ASPIRE_EVIDENCE_PATH must be a repository-relative directory without traversal.'),
                                   ('ASPIRE_EVIDENCE_PATH', '.', 'ASPIRE_EVIDENCE_PATH must be a repository-relative directory without traversal.')]:
            with self.subTest(key=key, value=value):
                self.fresh_evidence()
                old = self.env.get(key)
                self.env[key] = value
                result = self.invoke('prepare-ci.sh')
                self.assertNotEqual(0, result.returncode)
                self.assertIn(message, result.stderr)
                if old is None:
                    self.env.pop(key)
                else:
                    self.env[key] = old

    def test_runner_contract_mismatch_refuses_live_after_preparation(self):
        for key, value, message in [('ASPIRE_TEST_PROJECT', 'other-tests', 'ASPIRE_TEST_PROJECT must be tests/Hexalith.McpCli.Integration.Tests.'),
                                   ('TEST_PLATFORM', 'vstest', 'TEST_PLATFORM must be microsoft-testing-platform.')]:
            with self.subTest(key=key, value=value):
                self.fresh_evidence()
                self.prepare()
                (self.root / 'calls.jsonl').unlink()
                self.env[key] = value
                try:
                    result = self.invoke('run-ci.sh')
                finally:
                    self.env.pop(key)
                self.assertEqual(1, result.returncode)
                self.assertEqual('', result.stdout)
                self.assertEqual(f'Live CI failed: ValueError: {message}\n', result.stderr)
                receipt = json.loads((self.evidence / 'ci-live.json').read_text())
                self.assertRegex(receipt['runId'], r'\A[0-9a-f]{32}\Z')
                self.assertEqual({'result': 'failed', 'fullLiveAccepted': False, 'runId': receipt['runId'],
                                  'error': f'ValueError: {message}'}, receipt)
                self.assertFalse(any(value.endswith(('run-vectors.py', 'run-isolated.py'))
                                     for call in self.calls() for value in call))

    def test_symlinked_evidence_is_refused_without_touching_its_target(self):
        target = self.root / 'outside-evidence'
        target.mkdir()
        original = target / 'owned-by-user.txt'
        original.write_text('preserve user data')
        self.evidence.symlink_to(target, target_is_directory=True)
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('ASPIRE_EVIDENCE_PATH must not traverse symbolic links.', result.stderr)
        self.assertEqual([original], list(target.iterdir()))
        self.assertEqual('preserve user data', original.read_text())
        (self.root / 'linked-parent').symlink_to(target, target_is_directory=True)
        self.env['ASPIRE_EVIDENCE_PATH'] = 'linked-parent/evidence'
        result = self.invoke('prepare-ci.sh')
        self.assertEqual(1, result.returncode)
        self.assertEqual('', result.stdout)
        self.assertEqual('Live CI failed: ValueError: ASPIRE_EVIDENCE_PATH must not traverse symbolic links.\n', result.stderr)
        self.assertEqual([original], list(target.iterdir()))

    def test_preparation_path_and_ownership_must_match_current_evidence(self):
        prepared = self.prepare()
        alternate = self.root / 'other-preparation.json'
        alternate.write_text(json.dumps(prepared))
        self.env['MCPCLI_CI_PREPARATION'] = str(alternate)
        result = self.invoke('run-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Preparation must come from the current evidence directory.', result.stderr)
        self.env.pop('MCPCLI_CI_PREPARATION')
        owner = prepared['ownershipId']
        prepared['ownershipId'] = '0' * 32
        (self.evidence / 'preparation.json').write_text(json.dumps(prepared))
        result = self.invoke('run-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Current successful preparation receipt is required.', result.stderr)
        # A current receipt that still names its runtime must also report success.
        prepared.update(ownershipId=owner, result='failed')
        (self.evidence / 'preparation.json').write_text(json.dumps(prepared))
        result = self.invoke('run-ci.sh')
        self.assertEqual(1, result.returncode)
        self.assertEqual('', result.stdout)
        message = 'ValueError: Current successful preparation receipt is required.'
        self.assertEqual(f'Live CI failed: {message}\n', result.stderr)
        receipt = json.loads((self.evidence / 'ci-live.json').read_text())
        self.assertEqual({'result': 'failed', 'fullLiveAccepted': False, 'runId': receipt['runId'], 'error': message}, receipt)
        self.assertFalse(any('run-vectors.py' in str(call) for call in self.calls()))

    def test_malformed_ownership_marker_refuses_live(self):
        self.prepare()
        (self.evidence / '.mcpcli-ci-owner').write_text('user file\n')
        result = self.invoke('run-ci.sh')
        self.assertEqual(1, result.returncode)
        self.assertEqual('', result.stdout)
        self.assertEqual('Live CI failed: ValueError: A task-owned prepared evidence directory is required.\n', result.stderr)
        self.assertEqual({'result': 'not-run', 'fullLiveAccepted': False},
                         json.loads((self.evidence / 'ci-live.json').read_text()))
        self.assertFalse(any(value.endswith(('run-vectors.py', 'run-isolated.py')) for call in self.calls() for value in call))

    def test_inherited_live_and_gateway_variables_never_reach_vectors_or_smoke(self):
        self.prepare()
        self.env.update(MCPCLI_LIVE_TOKEN='inherited-live-token', EVENTSTORE_TENANT='inherited-tenant')
        result = self.invoke('run-ci.sh')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        recorded = [json.loads(line) for line in (self.root / 'runner-environment.jsonl').read_text().splitlines()]
        self.assertEqual([['run-vectors.py', []], ['run-isolated.py', []]], recorded)

    def test_missing_built_integration_tests_refuses_live(self):
        self.prepare()
        tests = self.root / 'tests/Hexalith.McpCli.Integration.Tests/bin/Release/net10.0/Hexalith.McpCli.Integration.Tests.dll'
        tests.unlink()
        result = self.invoke('run-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Prepared private runtime, Python and built Release integration tests are required.', result.stderr)
        self.assertFalse(any('run-vectors.py' in str(call) for call in self.calls()))

    def test_wrong_aspire_version_refuses_source_builds(self):
        result = self.invoke('prepare-ci.sh', 'wrong-aspire')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Aspire CLI 13.6.1 is required.', result.stderr)
        self.assertFalse(any(call[0] == 'dotnet' and call[2] == 'build' for call in self.calls()))

    def test_bootstrapped_binary_hash_mismatch_refuses_preparation(self):
        result = self.invoke('prepare-ci.sh', 'bootstrap-hash-mismatch')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Private runtime binary hash mismatch: redis-server', result.stderr)
        receipt = json.loads((self.evidence / 'preparation.json').read_text())
        self.assertEqual('failed', receipt['result'])

    def test_missing_aspire_installs_only_a_digest_verified_release_archive(self):
        (self.bin / 'aspire').unlink()
        for tool in ('python3', 'bash', 'dirname'):
            (self.bin / tool).symlink_to(shutil.which(tool))
        self.env['PATH'] = str(self.bin)
        prepared = self.prepare()
        downloaded = prepared['tools']['aspireArchive']
        self.assertEqual('https://github.com/microsoft/aspire/releases/download/v13.6.1/aspire-cli-linux-x64-13.6.1.tar.gz', downloaded['url'])
        self.assertEqual(hashlib.sha256((self.root / 'aspire-fixture.tar.gz').read_bytes()).hexdigest(), downloaded['sha256'])
        self.assertTrue((Path(prepared['privateDirectory']) / 'aspire-cli/aspire').is_file())
        self.assertFalse(any('install.sh' in str(call) for call in self.calls()))
        self.fresh_evidence()
        result = self.invoke('prepare-ci.sh', 'corrupted-aspire-archive')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Aspire CLI release archive SHA-256 mismatch; refusing extraction.', result.stderr)
        receipt = json.loads((self.evidence / 'preparation.json').read_text())
        self.assertFalse((Path(receipt['privateDirectory']) / 'aspire-cli').exists())

    def test_exact_openssl_three_sonames_are_required_before_builds(self):
        module = self.ci_module()
        for missing in ('libssl.so.3', 'libcrypto.so.3'):
            with self.subTest(missing=missing):
                self.fresh_evidence()
                def load(name):
                    if name == missing:
                        raise OSError('missing exact soname')
                    return object()
                with patch.dict(os.environ, self.env, clear=True), patch.object(module.ctypes, 'CDLL', side_effect=load):
                    evidence = module.evidence_directory(preparing=True)
                    with self.assertRaisesRegex(RuntimeError, 'Missing prerequisite shared library: ' + re.escape(missing)):
                        module.prepare(evidence)
                receipt = json.loads((self.evidence / 'preparation.json').read_text())
                self.assertEqual('failed', receipt['result'])
                self.assertIn(missing, receipt['error'])

    def test_nested_python_uses_prepared_venv_and_its_installed_modules(self):
        prepared = self.prepare()
        result = self.invoke('run-ci.sh')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        nested = json.loads((self.root / 'nested-python.json').read_text())
        self.assertEqual(str(Path(prepared['python']).parent / 'python3'), nested['executable'])
        self.assertEqual(str(Path(prepared['python']).parents[1]), nested['prefix'])
        self.assertEqual('prepared-venv-only', nested['marker'])

    def test_generated_signing_keys_are_redacted_without_breaking_json(self):
        import base64
        module = self.ci_module()
        secret = base64.b64encode(os.urandom(32)).decode()
        self.assertNotIn(secret, self.env.values())
        diagnostic = {'SigningKey': secret, 'Authentication:JwtBearer:SigningKey': secret,
                      'escaped': json.dumps({'SigningKey': secret, 'message': 'retain this'}),
                      'twiceEscaped': json.dumps(json.dumps({'signingKey': secret}))}
        result = module.sanitized(json.dumps(diagnostic))
        self.assertNotIn(secret, result)
        parsed = json.loads(result)
        self.assertEqual('[REDACTED]', parsed['SigningKey'])
        self.assertEqual('[REDACTED]', parsed['Authentication:JwtBearer:SigningKey'])
        self.assertEqual({'SigningKey': '[REDACTED]', 'message': 'retain this'}, json.loads(parsed['escaped']))
        self.assertEqual({'signingKey': '[REDACTED]'}, json.loads(json.loads(parsed['twiceEscaped'])))
        escaped_fragment = json.dumps(json.dumps({'SigningKey': secret}))[1:-1]
        escaped_result = module.sanitized('log: ' + escaped_fragment).removeprefix('log: ')
        self.assertNotIn(secret, escaped_result)
        self.assertEqual({'SigningKey': '[REDACTED]'}, json.loads(json.loads('"' + escaped_result + '"')))
        # The fixture passes its key as an unquoted command-line argument.
        for line, marker in [(f'dotnet Gateway.dll --Authentication:JwtBearer:SigningKey={secret}', 'SigningKey=[REDACTED]'),
                             (f'Authentication__JwtBearer__SigningKey: {secret}', 'SigningKey: [REDACTED]')]:
            with self.subTest(marker=marker):
                redacted = module.sanitized(line)
                self.assertNotIn(secret, redacted)
                self.assertIn(marker, redacted)
        xml = module.sanitized_xml(f'<failure message="args --Authentication:JwtBearer:SigningKey={secret}" />')
        self.assertNotIn(secret, xml)
        self.assertIn('SigningKey=[REDACTED]', xml)

    def test_json_escaped_known_environment_secrets_are_redacted_without_changing_ordinary_text(self):
        module = self.ci_module()
        ordinary = 'retain "quotes", back\\slashes and new\nlines'
        for secret in ('quoted-"credential"', 'back\\slash-credential', 'new\nline-credential'):
            with self.subTest(secret=repr(secret)), patch.dict(os.environ, {'TEST_SECRET_TOKEN': secret}):
                diagnostic = {'diagnostic': secret, 'ordinary': ordinary}
                result = module.sanitized(json.dumps(diagnostic))
                self.assertEqual({'diagnostic': '[REDACTED]', 'ordinary': ordinary}, json.loads(result))
                self.assertNotIn(json.dumps(secret)[1:-1], result)
                nested = module.sanitized(json.dumps({'nested': json.dumps(diagnostic)}))
                self.assertEqual({'diagnostic': '[REDACTED]', 'ordinary': ordinary}, json.loads(json.loads(nested)['nested']))
                self.assertEqual('before [REDACTED] after', module.sanitized('before ' + secret + ' after'))
                self.assertEqual(ordinary, module.sanitized(ordinary))

    def test_unowned_evidence_is_untouched_and_retry_requires_fresh_directory(self):
        self.evidence.mkdir()
        key = self.evidence / 'issuer.key'
        key.write_bytes(os.urandom(48))
        original = key.read_bytes()
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('fresh empty evidence directory', result.stderr)
        self.assertEqual(original, key.read_bytes())
        self.assertEqual([key], list(self.evidence.iterdir()))
        self.fresh_evidence()
        self.prepare()
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('fresh empty evidence directory', result.stderr)

    def test_private_temp_root_must_not_overlap_evidence(self):
        for child in ('', 'raw-private'):
            with self.subTest(child=child):
                self.fresh_evidence()
                temporary = self.evidence / child
                self.env['RUNNER_TEMP'] = str(temporary)
                result = self.invoke('prepare-ci.sh')
                self.assertNotEqual(0, result.returncode)
                self.assertIn('RUNNER_TEMP must be outside', result.stderr)
                self.assertFalse(any(self.evidence.rglob('mcpcli-live-ci-*')))
                self.assertNotIn('privateDirectory', json.loads((self.evidence / 'preparation.json').read_text()))

    def test_failed_preparation_retains_owned_private_location(self):
        result = self.invoke('prepare-ci.sh', 'bundle-setup-failure')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('aspire setup', result.stderr)
        self.assertIn('exited 18', result.stderr)
        receipt = json.loads((self.evidence / 'preparation.json').read_text())
        self.assertEqual('failed', receipt['result'])
        self.assertTrue(Path(receipt['privateDirectory']).is_dir())
        self.assertFalse(Path(receipt['privateDirectory']).is_relative_to(self.evidence))

    def test_hosted_runner_refreshes_complete_existing_bundle_before_hash_validation(self):
        self.env.update(GITHUB_ACTIONS='true', RUNNER_ENVIRONMENT='github-hosted')
        managed = Path(self.env['HOME']) / '.aspire/bundle/managed/aspire-managed'
        managed.write_text('older cached managed bundle')
        self.prepare()
        self.assertEqual('qualified bundle', managed.read_text())
        setup = [call for call in self.calls() if call[0] == 'aspire' and call[2] == 'setup'
                 and str(Path(self.env['HOME']) / '.aspire') in call]
        self.assertEqual(1, len(setup))
        self.assertIn('--force', setup[0])

    def test_hosted_bundle_refresh_still_rejects_mismatched_managed_payload(self):
        self.env.update(GITHUB_ACTIONS='true', RUNNER_ENVIRONMENT='github-hosted')
        result = self.invoke('prepare-ci.sh', 'bundle-home-mismatch')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Qualified Aspire bundle mismatch: managed/aspire-managed', result.stderr)
        self.assertFalse(any(call[0] == 'dotnet' and call[2] == 'build' for call in self.calls()))

    def test_installed_bundle_must_match_fresh_selected_cli_bytes(self):
        installed = Path(self.env['HOME']) / '.aspire/bundle/dcp/dcp'
        installed.write_text('stale or replaced bundle')
        result = self.invoke('prepare-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Qualified Aspire bundle mismatch: dcp/dcp', result.stderr)
        self.assertEqual('stale or replaced bundle', installed.read_text())
        self.assertFalse(any(call[0] == 'dotnet' and call[2] == 'build' for call in self.calls()))

    def test_malformed_native_ownership_proof_is_refused(self):
        module = self.ci_module()
        runtime = self.root / 'native-runtime'
        run = runtime / 'runs/example'
        run.mkdir(parents=True)
        namespaces = {name: name + ':[' + str(index + 2000) + ']' for index, name in enumerate(('user', 'pid', 'net', 'mnt'))}
        baseline = {'commandExitCode': 0, 'supervisorPid': 1, 'prerequisitesReady': True, 'namespaces': namespaces,
                    'ownedInfrastructureStopped': {name: -15 for name in ('redis', 'sentry', 'placement', 'scheduler')}}
        outside = {'namespaces': {name: name + ':[' + str(index + 1000) + ']' for index, name in enumerate(namespaces)}}
        (run / 'result.json').write_text(json.dumps(baseline))
        (run / 'outside.json').write_text(json.dumps(outside))
        self.assertEqual(baseline, module.require_owned(run / 'result.json', runtime))
        mutations = [('namespaces', 'user', None), ('namespaces', 'user', 'arbitrary-string'),
                     ('ownedInfrastructureStopped', 'redis', '0'), ('ownedInfrastructureStopped', 'redis', False),
                     ('ownedInfrastructureStopped', 'redis', 9999), (None, 'supervisorPid', 2),
                     (None, 'supervisorPid', '1'), (None, 'supervisorPid', True), (None, 'commandExitCode', False)]
        for section, key, value in mutations:
            with self.subTest(section=section, key=key, value=value):
                document = json.loads(json.dumps(baseline))
                (document[section] if section else document)[key] = value
                (run / 'result.json').write_text(json.dumps(document))
                with self.assertRaises(ValueError):
                    module.require_owned(run / 'result.json', runtime)
        (run / 'result.json').write_text(json.dumps(baseline))
        for identity in (None, 'user:[0]', namespaces['user']):
            outside['namespaces']['user'] = identity
            (run / 'outside.json').write_text(json.dumps(outside))
            with self.assertRaises(ValueError):
                module.require_owned(run / 'result.json', runtime)

    def test_sigterm_stops_detached_child_and_retains_failed_receipt_and_diagnostics(self):
        self.prepare()
        self.env['FIXTURE_MODE'] = 'cancel-vectors'
        process = subprocess.Popen(['bash', str(self.tools / 'run-ci.sh')], env=self.env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        child = None
        try:
            deadline = time.monotonic() + 8
            while not (self.root / 'cancel-child.json').exists():
                if process.poll() is not None or time.monotonic() >= deadline:
                    self.fail('Detached child did not become ready: ' + ''.join(process.communicate(timeout=2)))
                time.sleep(0.01)
            child = json.loads((self.root / 'cancel-child.json').read_text())
            self.assertEqual(child['pid'], child['pgid'])
            self.assertNotEqual(process.pid, child['pgid'])
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=8)
            self.assertEqual(143, process.returncode, stdout + stderr)
            with self.assertRaises(ProcessLookupError):
                os.kill(child['pid'], 0)
            self.assertTrue((self.root / 'cancel-child-stopped').exists())
            receipt = json.loads((self.evidence / 'ci-live.json').read_text())
            self.assertEqual('failed', receipt['result'])
            self.assertIs(False, receipt['fullLiveAccepted'])
            self.assertEqual('SystemExit: 143', receipt['error'])
            self.assertEqual([{'operation': 'sample.operation-00', 'result': 'running', 'error': None}],
                             receipt['vectors']['interrupted'])
            self.assertIn('interrupted Operations: sample.operation-00;', receipt['vectors']['error'])
            self.assertIn('interrupted Operations: sample.operation-00;', stderr)
            self.assertNotIn('smoke', receipt)
            output = Path(receipt['output'])
            self.assertIn('detached vector stopped', (output / 'vectors-process.stdout.txt').read_text())
            self.assertIn('detached vector stderr stopped', (output / 'vectors-process.stderr.txt').read_text())
            self.assertEqual(143, json.loads((output / 'vectors-process.command.json').read_text())['exitCode'])
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=3)
            if child:
                try:
                    os.killpg(child['pgid'], signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.stdout.close()
            process.stderr.close()

    def test_xml_entities_cannot_hide_known_secrets(self):
        module = self.ci_module()
        secret = 'quote-"secret&value'
        xml = '<assemblies><failure message="quote-&quot;secret&amp;value">quote-"secret&amp;value</failure></assemblies>'
        with patch.dict(os.environ, {'TEST_SECRET_TOKEN': secret}):
            result = module.sanitized_xml(xml)
        self.assertNotIn('secret', result)
        self.assertEqual(2, result.count('[REDACTED]'))
        clean = '<assemblies>\n  <assembly passed="1" />\n</assemblies>'
        self.assertEqual(clean, module.sanitized_xml(clean))
        self.env['TEST_SECRET_TOKEN'] = secret
        self.prepare()
        result = self.invoke('run-ci.sh', 'generation-xml-secrets')
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads((self.evidence / 'ci-live.json').read_text())
        for path in Path(report['output']).rglob('tests.xml'):
            self.assertNotIn('secret', path.read_text())

    def test_vector_and_smoke_failures_are_both_named(self):
        self.prepare()
        result = self.invoke('run-ci.sh', 'both-fail')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('failed Operations: sample.operation-00', result.stderr)
        self.assertIn('independent smoke failed:', result.stderr)
        self.assertIn('exited 17', result.stderr)
        receipt = json.loads((self.evidence / 'ci-live.json').read_text())
        self.assertIs(False, receipt['fullLiveAccepted'])
        self.assertIn('failed Operations: sample.operation-00', receipt['error'])
        self.assertIn('exited 17', receipt['error'])

    def test_sigterm_during_smoke_preserves_cancellation_after_vector_failure(self):
        self.prepare()
        self.env['FIXTURE_MODE'] = 'cancel-smoke-after-vector-failure'
        process = subprocess.Popen(['bash', str(self.tools / 'run-ci.sh')], env=self.env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        child = None
        try:
            deadline = time.monotonic() + 8
            while not (self.root / 'cancel-child.json').exists():
                if process.poll() is not None or time.monotonic() >= deadline:
                    self.fail('Smoke child did not become ready: ' + ''.join(process.communicate(timeout=2)))
                time.sleep(.01)
            child = json.loads((self.root / 'cancel-child.json').read_text())
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=8)
            self.assertEqual(143, process.returncode, stdout + stderr)
            with self.assertRaises(ProcessLookupError):
                os.kill(child['pid'], 0)
            self.assertTrue((self.root / 'cancel-child-stopped').exists())
            receipt = json.loads((self.evidence / 'ci-live.json').read_text())
            self.assertEqual('failed', receipt['result'])
            self.assertIs(False, receipt['fullLiveAccepted'])
            self.assertEqual('SystemExit: 143', receipt['error'])
            self.assertEqual('sample.operation-00', receipt['vectors']['failures'][0]['operation'])
            self.assertNotIn('independent smoke failed:', stderr)
            output = Path(receipt['output']) / 'smoke'
            self.assertIn('independent smoke stopped', (output / 'process.stdout.txt').read_text())
            self.assertEqual(143, json.loads((output / 'process.command.json').read_text())['exitCode'])
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=3)
            if child:
                try:
                    os.killpg(child['pgid'], signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.stdout.close()
            process.stderr.close()

    def test_smoke_control_exceptions_are_not_combined_with_vector_failure(self):
        prepared = self.prepare()
        module = self.ci_module()
        bounded = module.bounded
        self.env['FIXTURE_MODE'] = 'failed-vectors'
        for error in (SystemExit(143), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__):
                shutil.rmtree(Path(prepared['runtime']) / 'runs', ignore_errors=True)
                def execute(command, *args, **kwargs):
                    if any(value.endswith('run-isolated.py') for value in command):
                        raise error
                    return bounded(command, *args, **kwargs)
                with patch.dict(os.environ, self.env, clear=True), patch.object(module, 'bounded', side_effect=execute):
                    with self.assertRaises(type(error)) as raised:
                        module.run(self.evidence)
                self.assertIs(error, raised.exception)
                receipt = json.loads((self.evidence / 'ci-live.json').read_text())
                self.assertEqual(f'{type(error).__name__}: {error}', receipt['error'])
                self.assertIs(False, receipt['fullLiveAccepted'])
                self.assertEqual('failed', receipt['vectors']['result'])

    def test_cancellation_waits_for_real_vector_runner_detached_child_cleanup(self):
        output = self.root / 'nested-cancellation'
        output.mkdir()
        runner = output / 'vector.py'
        runner.write_text('''
import importlib.util,os,pathlib,signal,sys
sys.path.insert(0,sys.argv[1])
spec=importlib.util.spec_from_file_location('lane',pathlib.Path(sys.argv[1])/'run-vectors.py')
lane=importlib.util.module_from_spec(spec);spec.loader.exec_module(lane)
signal.signal(signal.SIGTERM,lambda *_:sys.exit(143))
child="import os,pathlib,signal,sys,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); pathlib.Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(120)"
lane.bounded_child([sys.executable,'-c',child,sys.argv[2]],os.environ.copy(),pathlib.Path(sys.argv[2]).parent,120)
''')
        supervisor = output / 'ci.py'
        supervisor.write_text('''
import importlib.util,pathlib,signal,sys
spec=importlib.util.spec_from_file_location('ci',pathlib.Path(sys.argv[1])/'ci.py')
ci=importlib.util.module_from_spec(spec);spec.loader.exec_module(ci)
signal.signal(signal.SIGTERM,lambda *_:sys.exit(143))
ci.bounded([sys.executable,sys.argv[2],sys.argv[1],sys.argv[3]],120,pathlib.Path(sys.argv[3]).parent/'process')
''')
        pid_file = output / 'child.pid'
        process = subprocess.Popen([sys.executable, str(supervisor), str(HERE), str(runner), str(pid_file)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        child = None
        try:
            deadline = time.monotonic() + 10
            while not pid_file.exists():
                if process.poll() is not None or time.monotonic() >= deadline:
                    self.fail('Nested child did not start: ' + ''.join(process.communicate(timeout=2)))
                time.sleep(.01)
            child = int(pid_file.read_text())
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=29)
            self.assertEqual(143, process.returncode, stdout + stderr)
            with self.assertRaises(ProcessLookupError):
                os.kill(child, 0)
            self.assertTrue((output / 'process.stderr.txt').is_file())
            # uutils reports external TERM as 124; GNU propagates the child's 143.
            self.assertIn(json.loads((output / 'process.command.json').read_text())['exitCode'], (124, 143))
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=3)
            if child:
                try:
                    os.kill(child, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_exited_supervisor_still_stops_remaining_owned_group(self):
        module = self.ci_module()
        child = type('Exited', (), {'pid': 123456789, 'returncode': 0,
                                    'wait': lambda *_, **__: 0, 'poll': lambda *_: 0})()
        with patch.object(module.subprocess, 'Popen', return_value=child), patch.object(module.os, 'killpg') as kill:
            module.bounded(['inert-child'], 1, self.root / 'exited-supervisor')
        kill.assert_called_once_with(child.pid, signal.SIGKILL)

    def test_exited_child_signal_race_preserves_cancellation_diagnostics(self):
        module = self.ci_module()
        class ExitedBetweenPollAndSignal:
            pid = 123456789
            returncode = None
            calls = 0
            def poll(self):
                return None
            def wait(self, **_):
                self.calls += 1
                if self.calls == 1:
                    raise SystemExit(143)
                self.returncode = 0
                return 0
        child = ExitedBetweenPollAndSignal()
        def launch(*_, **kwargs):
            kwargs['stdout'].write(b'last child diagnostic\n')
            kwargs['stdout'].flush()
            return child
        output = self.root / 'race/output'
        with patch.object(module.subprocess, 'Popen', side_effect=launch), \
                patch.object(module.os, 'killpg', side_effect=ProcessLookupError) as kill:
            with self.assertRaises(SystemExit):
                module.bounded(['inert-child'], 1, output)
        self.assertEqual([(child.pid, signal.SIGKILL)], [call.args for call in kill.call_args_list if call.args[1] != 0])
        self.assertIn('last child diagnostic', output.with_name('output.stdout.txt').read_text())
        self.assertEqual(0, json.loads(output.with_name('output.command.json').read_text())['exitCode'])

    def test_cancellation_escalation_finishes_within_outer_kill_grace(self):
        module = self.ci_module()
        class IgnoresTerm:
            pid = 123456789
            returncode = None
            timeouts = []
            def poll(self):
                return None
            def wait(self, *, timeout):
                self.timeouts.append(timeout)
                if len(self.timeouts) == 1:
                    raise SystemExit(143)
                if len(self.timeouts) == 2:
                    raise subprocess.TimeoutExpired('inert-child', timeout)
                self.returncode = -9
                return self.returncode
        child = IgnoresTerm()
        def signal_group(pid, signum):
            if signum == 0:
                raise ProcessLookupError
        with patch.object(module.subprocess, 'Popen', return_value=child), patch.object(module.os, 'killpg', side_effect=signal_group) as kill:
            with self.assertRaises(SystemExit):
                module.bounded(['inert-child'], 1, self.root / 'escalation')
        self.assertEqual([41, 25, 1], child.timeouts)
        self.assertEqual([(child.pid, signal.SIGKILL), (child.pid, signal.SIGKILL)], [call.args for call in kill.call_args_list if call.args[1] != 0])


class CiWorkflowTests(unittest.TestCase):
    def test_required_inputs_and_existing_focused_lanes_remain_configured(self):
        workflow = (HERE.parents[1] / '.github/workflows/ci.yml').read_text()
        caller = workflow.split('  ci:\n', 1)[1].split('\n  conformance-vector-contract:', 1)[0]
        for line in ('test-platform: microsoft-testing-platform',
                     'aspire-test-project: tests/Hexalith.McpCli.Integration.Tests',
                     'aspire-continue-on-error: false', 'aspire-timeout-minutes: 360',
                     "dapr-version: '1.18.2'", "dapr-runtime-version: '1.18.7'",
                     'aspire-prepare-script: tools/live-topology/prepare-ci.sh',
                     'aspire-runner-script: tools/live-topology/run-ci.sh',
                     'aspire-prepare-timeout-minutes: 40', 'aspire-runner-timeout-minutes: 300',
                     'aspire-evidence-path: TestResults/live-ci'):
            self.assertIn(line, caller)
        for project in ('Abstractions', 'Analyzers', 'Core', 'Manifest', 'Cli', 'Mcp'):
            self.assertIn(f'tests/Hexalith.McpCli.{project}.Tests', caller)
        self.assertRegex(caller, r'uses: Hexalith/Hexalith.Builds/\.github/workflows/domain-ci.yml@[0-9a-f]{40}\n')
        self.assertIn('len(operations) != 21 or sorted(discovered) != sorted(expected)', workflow)

    def test_workflow_pin_matches_builds_gitlink(self):
        root = HERE.parents[1]
        recorded = subprocess.run(
            ['git', 'ls-tree', 'HEAD', 'references/Hexalith.Builds'],
            cwd=root, check=True, capture_output=True, text=True).stdout.split()
        references = []
        for workflow in sorted((root / '.github/workflows').rglob('*')):
            if workflow.suffix in ('.yml', '.yaml'):
                references.extend((workflow, pin) for pin in re.findall(
                    r'Hexalith/Hexalith\.Builds/[^\s@]+@([^\s#]+)', workflow.read_text()))
        self.assertTrue(references, 'Expected pinned Hexalith.Builds workflow references.')
        for workflow, pin in references:
            with self.subTest(workflow=str(workflow.relative_to(root)), pin=pin):
                self.assertEqual(recorded[2], pin)


if __name__ == '__main__':
    unittest.main()
