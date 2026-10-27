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

HERE = Path(__file__).resolve().parent

TOOL = r'''#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys
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
        if mode == 'build-failure' and 'Tenants' in args[1]:
            print('named source build failure', file=sys.stderr); sys.exit(23)
    elif args[0] == 'msbuild':
        print('3.127.0' if pathlib.Path.cwd().name == 'Hexalith.Parties' else '3.128.0')
    sys.exit(0)
if name == 'dapr':
    print('CLI version: 1.18.2\nRuntime version: ' + ('1.18.0' if mode == 'wrong-dapr' else '1.18.7'))
elif name == 'daprd':
    print('1.18.7')
elif name == 'aspire':
    if args and args[0] == 'setup':
        if mode == 'bundle-setup-failure': sys.exit(18)
        for relative in ('dcp/dcp', 'dashboard/Aspire.Dashboard', 'managed/aspire-managed'):
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
        print('a' * 40)
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
    if mode == 'cancel-vectors':
        def terminate(*_):
            print('detached vector stopped', flush=True)
            print('detached vector stderr stopped', file=sys.stderr, flush=True)
            (root / 'cancel-child-stopped').touch()
            sys.exit(143)
        signal.signal(signal.SIGTERM, terminate)
        print('detached vector started', flush=True)
        (root / 'cancel-child.json').write_text(json.dumps({'pid': os.getpid(), 'pgid': os.getpgrp()}))
        while True: time.sleep(1)
    output = pathlib.Path(sys.argv[sys.argv.index('--output') + 1]); output.mkdir()
    operations = sorted(json.loads(path.read_text())['operation'] for path in (root / 'tools/conformance-vectors/v1/modules').glob('*.vector.json'))
    outcomes = [{'operation': name, 'result': 'passed', 'exitCode': 0, 'isolatedReceipt': str(owned(name) / 'result.json')} for name in operations]
    receipt = {'result': 'passed', 'fullLiveAccepted': True, 'coverage': operations, 'vectors': outcomes, 'passed': 21, 'failed': 0}
    if mode == 'partial-vectors': receipt['fullLiveAccepted'] = False
    if mode == 'skipped-vector': outcomes[0]['result'] = 'skipped'
    if mode == 'incomplete-vectors': outcomes.pop()
    if mode == 'failed-vectors':
        receipt.update(result='failed', passed=20, failed=1)
        outcomes[0].update(result='failed', error='phase observe-party: gateway_error 500')
    if mode == 'duplicate-isolation': outcomes[1]['isolatedReceipt'] = outcomes[0]['isolatedReceipt']
    if mode == 'stale-isolation': outcomes[0]['isolatedReceipt'] = str(owned('foreign', runtime.parent / 'sibling-runtime') / 'result.json')
    if mode == 'extra-runtime': (runtime / 'runs/unexpected').mkdir()
    if mode == 'generation-secrets':
        secret = base64.b64encode(os.urandom(32)).decode()
        with (root / 'generated-signing-keys.txt').open('a') as keys: keys.write(secret + '\n')
        content = 'eyJfixture.payload.signature\n-----BEGIN PRIVATE KEY-----\nfixture credential\n-----END PRIVATE KEY-----\n' + os.environ['TEST_SECRET_TOKEN'] + '\n' + json.dumps({'SigningKey': secret})
        child = output / operations[0]; child.mkdir()
        (child / 'child.stdout.txt').write_text(content)
        (child / 'tests.xml').write_text('<test>' + content + '</test>')
    if mode != 'missing-vectors':
        (output / 'live-lane.json').write_text('{' if mode == 'malformed-vectors' else json.dumps(receipt))
    sys.exit(19 if mode == 'vector-exit' else 1 if mode == 'failed-vectors' else 0)
else:
    path = owned('smoke')
    result = 'Skip' if mode == 'skipped-smoke' else 'Pass'
    xml = '<assemblies><assembly total="1" passed="1" failed="0" skipped="0" errors="0"><collection><test result="' + result + '" type="Hexalith.McpCli.Integration.Tests.GatewaySmokeTests" method="AuthenticatedQueryReturnsSuccessfulDocument" /></collection></assembly></assemblies>'
    if mode == 'wrong-smoke-case': xml = xml.replace('AuthenticatedQueryReturnsSuccessfulDocument', 'OtherTest')
    if mode == 'skipped-smoke-count': xml = xml.replace('skipped="0"', 'skipped="1"')
    if mode == 'empty-smoke': xml = '<assemblies><assembly total="0" passed="0" failed="0" skipped="0" errors="0" /></assemblies>'
    destination = pathlib.Path(sys.argv[sys.argv.index('-result-xml') + 1])
    if mode != 'missing-smoke': destination.write_text(xml)
    print('Isolated run: ' + str(path))
    sys.exit(17 if mode == 'smoke-exit' else 0)
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
        self.assertEqual(['Hexalith.EventStore', 'Hexalith.Tenants', 'Hexalith.Parties'], [Path(call[1]).name for call in source_builds])
        for call in source_builds:
            self.assertIn('-p:UseHexalithProjectReferences=false', call)
            self.assertIn('-p:UseNuGetDeps=true', call)
            self.assertIn('Release', call)
        deadlines = [call[4] for call in calls if call[0] == 'timeout' and call[5:7] == ['dotnet', 'build']]
        self.assertEqual(['300'] * 3, deadlines)
        self.assertLess(next(index for index, call in enumerate(calls) if call[0] == 'unshare'), calls.index(source_builds[0]))
        self.assertEqual(3, len(prepared['sources']))
        self.assertEqual(['3.128.0', '3.128.0', '3.127.0'],
                         [source['HexalithEventStoreVersion'] for source in prepared['sources']])
        property_calls = [call for call in calls if call[0] == 'dotnet' and call[2] == 'msbuild']
        self.assertEqual(3, len(property_calls))
        for call in property_calls:
            self.assertIn('-getProperty:HexalithEventStoreVersion', call)
            self.assertIn('-p:UseHexalithProjectReferences=false', call)
            self.assertIn('-p:UseNuGetDeps=true', call)
        self.assertEqual(['timeout', str(self.root), '--signal=TERM', '--kill-after=30s', '2280',
                          'python3', 'tools/live-topology/ci.py', 'prepare'], calls[0])
        self.assertEqual(['MCPCLI_CI_PREPARATION=' + str(self.evidence / 'preparation.json')], (self.root / 'github-env').read_text().splitlines())
        self.assertNotIn('fixture-secret-token', json.dumps(prepared))

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
                self.assertIn('dotnet build src/Hexalith.', result.stderr)
                self.assertFalse(any('run-vectors.py' in str(call) or 'bootstrap-runtime.py' in str(call) for call in self.calls()))

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

    def test_smoke_skips_missing_receipts_nonzero_and_cleanup_fail_closed(self):
        preparation = self.prepare()
        for mode in ('skipped-smoke', 'missing-smoke', 'smoke-exit', 'missing-cleanup', 'wrong-smoke-case', 'skipped-smoke-count', 'empty-smoke'):
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

    def test_preparation_path_and_ownership_must_match_current_evidence(self):
        prepared = self.prepare()
        alternate = self.root / 'other-preparation.json'
        alternate.write_text(json.dumps(prepared))
        self.env['MCPCLI_CI_PREPARATION'] = str(alternate)
        result = self.invoke('run-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Preparation must come from the current evidence directory.', result.stderr)
        self.env.pop('MCPCLI_CI_PREPARATION')
        prepared['ownershipId'] = '0' * 32
        (self.evidence / 'preparation.json').write_text(json.dumps(prepared))
        result = self.invoke('run-ci.sh')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Current successful preparation receipt is required.', result.stderr)
        self.assertFalse(any('run-vectors.py' in str(call) for call in self.calls()))

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
        kill.assert_called_once_with(child.pid, signal.SIGTERM)
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
        with patch.object(module.subprocess, 'Popen', return_value=child), patch.object(module.os, 'killpg') as kill:
            with self.assertRaises(SystemExit):
                module.bounded(['inert-child'], 1, self.root / 'escalation')
        self.assertEqual([41, 10, 5], child.timeouts)
        self.assertEqual([(child.pid, signal.SIGTERM), (child.pid, signal.SIGKILL)], [call.args for call in kill.call_args_list])


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
        workflow = (root / '.github/workflows/ci.yml').read_text()
        caller = workflow.split('  ci:\n', 1)[1].split('\n  conformance-vector-contract:', 1)[0]
        match = re.search(
            r'uses: Hexalith/Hexalith.Builds/\.github/workflows/domain-ci.yml@([0-9a-f]{40})\n',
            caller)
        self.assertIsNotNone(match)
        recorded = subprocess.run(
            ['git', 'ls-tree', 'HEAD', 'references/Hexalith.Builds'],
            cwd=root, check=True, capture_output=True, text=True).stdout.split()
        self.assertEqual(match.group(1), recorded[2])


if __name__ == '__main__':
    unittest.main()
