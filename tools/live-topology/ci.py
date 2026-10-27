#!/usr/bin/env python3
"""Bounded CI preparation and acceptance for the existing isolated semantic lane."""
from __future__ import annotations

import ctypes
import ctypes.util
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PROJECT = 'tests/Hexalith.McpCli.Integration.Tests'
TESTS = ROOT / PROJECT / 'bin/Release/net10.0/Hexalith.McpCli.Integration.Tests.dll'
MODULES = ('Hexalith.EventStore', 'Hexalith.Tenants', 'Hexalith.Parties')
SERVICES = {'sentry', 'redis', 'placement', 'scheduler'}
NAMESPACES = {'user', 'pid', 'net', 'mnt'}
OWNER_FILE = '.mcpcli-ci-owner'
ASPIRE_CLI_URL = 'https://github.com/microsoft/aspire/releases/download/v13.6.1/aspire-cli-linux-x64-13.6.1.tar.gz'
ASPIRE_CLI_SHA256 = 'f5498a1b30f894186a805c08798d9ca4f112dfc3b5f24ab0acef3f8aa5d009b8'


def sanitized(text: str) -> str:
    """Retain diagnostics without copying credentials or PEM material into artifacts."""
    text = re.sub(r'-----BEGIN [^-]+-----.*?-----END [^-]+-----', '[REDACTED PEM]', text, flags=re.S)
    text = re.sub(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[REDACTED JWT]', text)
    text = re.sub(r'(?i)((?P<quote>\\+)"[^"\r\n]*SigningKey(?P=quote)"\s*:\s*)(?P=quote)"[^"\r\n]*(?P=quote)"',
                  lambda match: match[1] + match['quote'] + '"[REDACTED]' + match['quote'] + '"', text)
    # A JSON string token can also contain an escaped JSON diagnostic or command.
    def redact_string(match):
        if '\\' not in match.group():
            return match.group()
        try:
            decoded = json.loads(match.group())
            redacted = sanitized(decoded)
            return json.dumps(redacted) if redacted != decoded else match.group()
        except json.JSONDecodeError:
            return match.group()
    text = re.sub(r'"(?:[^"\\]|\\.)*"', redact_string, text)
    # Preserve all quote/escape delimiters when the surrounding text is not a JSON document.
    text = re.sub(r'(?i)("(?:[^"\\]|\\.)*SigningKey"\s*:\s*)"(?:[^"\\]|\\.)*"',
                  r'\1"[REDACTED]"', text)
    text = re.sub(r'(?i)(SigningKey(?:=|:|\s)+)[^\s,\]"}]+', r'\1[REDACTED]', text)
    for key, value in os.environ.items():
        if value and len(value) >= 8 and re.search(r'TOKEN|PASSWORD|SECRET|CERT_KEY|SIGNINGKEY', key, re.I):
            text = text.replace(value, '[REDACTED]')
    return text


def save(path: Path, value) -> None:
    path.write_text(sanitized(json.dumps(value, indent=2)) + '\n')


def bounded(command: list[str], seconds: int, output: Path, *, cwd=ROOT, environment=None) -> str:
    """Enforce a process bound, retain both sanitized channels, and propagate failures."""
    output.parent.mkdir(parents=True, exist_ok=True)
    actual = ['timeout', '--signal=TERM', '--kill-after=30s', str(seconds), *map(str, command)]
    print(f'Running ({seconds}s): {" ".join(map(str, command))}', flush=True)
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        child = subprocess.Popen(actual, cwd=cwd, env=environment, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            code = child.wait(timeout=seconds + 40)
        finally:
            if child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass  # The child can exit between poll and the process-group signal.
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    child.wait(timeout=5)
            stdout.seek(0)
            stderr.seek(0)
            content = sanitized(stdout.read().decode(errors='replace'))
            error = sanitized(stderr.read().decode(errors='replace'))
            output.parent.joinpath(output.name + '.stdout.txt').write_text(content)
            output.parent.joinpath(output.name + '.stderr.txt').write_text(error)
            save(output.parent / (output.name + '.command.json'), {'command': list(map(str, command)), 'cwd': str(cwd),
                 'timeoutSeconds': seconds, 'exitCode': child.returncode})
    if code != 0:
        raise RuntimeError(f'{" ".join(map(str, command))} exited {code}; see {output.parent / (output.name + ".stderr.txt")}')
    return content.strip()


def evidence_directory(*, preparing: bool) -> Path:
    value = os.environ.get('ASPIRE_EVIDENCE_PATH', 'TestResults/live-ci')
    if not re.fullmatch(r'[A-Za-z0-9_./-]+', value) or value.startswith('/') or any(part in ('', '.', '..') for part in value.split('/')):
        raise ValueError('ASPIRE_EVIDENCE_PATH must be a repository-relative directory without traversal.')
    path = ROOT / value
    if any(item.is_symlink() for item in [path, *path.parents] if ROOT in item.parents):
        raise ValueError('ASPIRE_EVIDENCE_PATH must not traverse symbolic links.')
    if preparing:
        path.mkdir(parents=True, exist_ok=True)
        if any(path.iterdir()):
            raise ValueError('Preparation requires a fresh empty evidence directory; existing files were left unchanged.')
        (path / OWNER_FILE).write_text(uuid.uuid4().hex + '\n')
    elif not path.is_dir() or not (path / OWNER_FILE).is_file() \
            or re.fullmatch(r'[0-9a-f]{32}\n', (path / OWNER_FILE).read_text()) is None:
        raise ValueError('A task-owned prepared evidence directory is required.')
    return path


def require_contract() -> None:
    if os.environ.get('ASPIRE_TEST_PROJECT', PROJECT) != PROJECT:
        raise ValueError(f'ASPIRE_TEST_PROJECT must be {PROJECT}.')
    if os.environ.get('TEST_PLATFORM', 'microsoft-testing-platform') != 'microsoft-testing-platform':
        raise ValueError('TEST_PLATFORM must be microsoft-testing-platform.')


def prepare(evidence: Path) -> None:
    receipt = {'result': 'preparing', 'runId': uuid.uuid4().hex, 'sources': [], 'tools': {},
               'ownershipId': (evidence / OWNER_FILE).read_text().strip()}
    save(evidence / 'preparation.json', receipt)
    save(evidence / 'ci-live.json', {'result': 'not-run', 'fullLiveAccepted': False})
    try:
        require_contract()
        if sys.version_info < (3, 11) or platform.system() != 'Linux' or platform.machine() != 'x86_64':
            raise RuntimeError('Live CI requires Linux amd64 and Python 3.11 or later.')
        for tool in ('timeout', 'git', 'dotnet', 'docker', 'dapr', 'unshare', 'ip', 'curl', 'bash'):
            if not shutil.which(tool):
                raise RuntimeError(f'Missing prerequisite: {tool}')
        for library in ('libssl.so.3', 'libcrypto.so.3'):
            try:
                ctypes.CDLL(library)
            except OSError as error:
                raise RuntimeError(f'Missing prerequisite shared library: {library}') from error
        for library in ('z', 'zstd'):
            if not ctypes.util.find_library(library):
                raise RuntimeError(f'Missing prerequisite shared library: {library}')
        tools = receipt['tools']
        tools['sdkPolicy'] = json.loads((ROOT / 'global.json').read_text())['sdk']
        # This command runs at ROOT, so the SDK resolver enforces global.json,
        # including its explicitly permitted patch roll-forward policy.
        tools['dotnet'] = bounded(['dotnet', '--version'], 30, evidence / 'dotnet-version')
        tools['dapr'] = bounded(['dapr', '--version'], 30, evidence / 'dapr-version')
        if not re.search(r'CLI version: 1\.18\.2\s', tools['dapr'] + '\n') or not re.search(r'Runtime version: 1\.18\.7\s', tools['dapr'] + '\n'):
            raise RuntimeError('Dapr CLI 1.18.2 and initialized runtime 1.18.7 are required; initialize Dapr in the reusable workflow.')
        daprd = Path.home() / '.dapr/bin/daprd'
        if not daprd.is_file():
            raise RuntimeError(f'Missing initialized Dapr runtime: {daprd}')
        bounded(['docker', 'info', '--format', '{{.ServerVersion}}'], 30, evidence / 'docker-info')
        namespace_probe = ['unshare', '--user', '--map-root-user', '--net', '--pid', '--mount', '--fork', '--mount-proc', 'true']
        try:
            bounded(namespace_probe, 30, evidence / 'namespace-probe')
        except RuntimeError:
            if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted':
                raise
            # Only the disposable hosted VM is configured; every test still
            # proves private user/PID/network/mount namespaces in the wrapper.
            bounded(['sudo', '-n', 'sysctl', '-w', 'kernel.apparmor_restrict_unprivileged_userns=0'],
                    30, evidence / 'hosted-namespace-setup')
            bounded(namespace_probe, 30, evidence / 'namespace-probe-configured')
        temporary_root = Path(os.environ.get('RUNNER_TEMP') or tempfile.gettempdir()).resolve()
        if temporary_root.is_relative_to(evidence.resolve()):
            raise RuntimeError('RUNNER_TEMP must be outside the evidence upload directory; no private directory was created.')
        private = Path(tempfile.mkdtemp(prefix='mcpcli-live-ci-', dir=temporary_root)).resolve()
        receipt['privateDirectory'] = str(private)
        save(evidence / 'preparation.json', receipt)
        if not shutil.which('aspire'):
            archive = private / 'aspire-cli.tar.gz'
            bounded(['curl', '--fail', '--silent', '--show-error', '--location', '--connect-timeout', '15', '--max-time', '120',
                     ASPIRE_CLI_URL, '-o', str(archive)], 130, evidence / 'aspire-download')
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            if digest != ASPIRE_CLI_SHA256:
                raise RuntimeError('Aspire CLI release archive SHA-256 mismatch; refusing extraction.')
            tools['aspireArchive'] = {'url': ASPIRE_CLI_URL, 'sha256': digest}
            installed_cli = private / 'aspire-cli'
            with tarfile.open(archive, 'r:gz') as release:
                release.extractall(installed_cli, filter='data')
            os.environ['PATH'] = str(installed_cli) + os.pathsep + os.environ['PATH']
        tools['aspire'] = bounded(['aspire', '--version'], 30, evidence / 'aspire-version')
        if tools['aspire'].split('+')[0] != '13.6.1':
            raise RuntimeError('Aspire CLI 13.6.1 is required.')
        tools['hostPython'] = sys.version
        tools['executables'] = {name: {'path': shutil.which(name), 'sha256': hashlib.sha256(Path(shutil.which(name)).read_bytes()).hexdigest()}
                                for name in ('aspire', 'dapr', 'dotnet')}
        tools['daprdSha256'] = hashlib.sha256(daprd.read_bytes()).hexdigest()
        bundle = Path.home() / '.aspire'
        fresh_bundle = private / 'qualified-aspire'
        bounded(['aspire', 'setup', '--install-path', str(fresh_bundle), '--force', '--non-interactive'],
                180, evidence / 'aspire-bundle-extract')
        hosted_runner = os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
        if hosted_runner or any(not (bundle / 'bundle' / relative).is_file() for relative in ('dcp/dcp', 'dashboard/Aspire.Dashboard')):
            bounded(['aspire', 'setup', '--install-path', str(bundle), '--force', '--non-interactive'], 180, evidence / 'aspire-bundle-setup')
        expected_bundle = {str(path.relative_to(fresh_bundle / 'bundle')): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in (fresh_bundle / 'bundle').rglob('*') if path.is_file()}
        if not {'dcp/dcp', 'dashboard/Aspire.Dashboard'} <= set(expected_bundle):
            raise RuntimeError('Selected qualified Aspire CLI did not extract its required embedded bundle files.')
        for relative, expected_hash in expected_bundle.items():
            installed = bundle / 'bundle' / relative
            if not installed.is_file() or hashlib.sha256(installed.read_bytes()).hexdigest() != expected_hash:
                raise RuntimeError(f'Qualified Aspire bundle mismatch: {relative}; installed bytes differ from the selected CLI embedded bundle.')
        save(evidence / 'aspire-bundle-hashes.json', expected_bundle)
        for relative in ('dcp/dcp', 'dashboard/Aspire.Dashboard'):
            binary = Path.home() / '.aspire/bundle' / relative
            if not binary.is_file():
                raise RuntimeError(f'Missing qualified Aspire bundle prerequisite: {binary}')
            tools[relative] = {'path': str(binary), 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
        # Check every checkout before building any source. Never initialize nested dependencies.
        declared = bounded(['git', 'config', '--file', str(ROOT / '.gitmodules'), '--get-regexp', r'^submodule\..*\.path$'],
                           10, evidence / 'root-submodules')
        paths = {line.split(maxsplit=1)[1] for line in declared.splitlines()}
        for module in MODULES:
            relative = 'references/' + module
            checkout = ROOT / relative
            project = checkout / 'src' / module / (module + '.csproj')
            if relative not in paths or checkout.is_symlink() or not (checkout / '.git').exists() or not project.is_file():
                raise RuntimeError(f'Missing declared direct root source prerequisite: {project}')
            actual = bounded(['git', 'rev-parse', '--show-toplevel'], 10, evidence / (module + '-root'), cwd=checkout)
            if Path(actual).resolve() != checkout.resolve():
                raise RuntimeError(f'{checkout} is not its own Git working tree.')
            source = {'module': module, 'path': relative,
                      'commit': bounded(['git', 'rev-parse', 'HEAD'], 10, evidence / (module + '-commit'), cwd=checkout),
                      'status': bounded(['git', 'status', '--porcelain', '--untracked-files=normal'], 10, evidence / (module + '-status'), cwd=checkout)}
            receipt['sources'].append(source)
        for source in receipt['sources']:
            module = source['module']
            project = f'src/{module}/{module}.csproj'
            source['HexalithEventStoreVersion'] = bounded(
                ['dotnet', 'msbuild', project, '-getProperty:HexalithEventStoreVersion',
                 '-p:UseHexalithProjectReferences=false', '-p:UseNuGetDeps=true'],
                30, evidence / (module + '-eventstore-version'), cwd=ROOT / 'references' / module)
            command = ['dotnet', 'build', f'src/{module}/{module}.csproj', '--configuration', 'Release', '-warnaserror', '-m:1',
                       '-p:UseHexalithProjectReferences=false', '-p:UseNuGetDeps=true']
            bounded(command, 300, evidence / (module + '-build'), cwd=ROOT / 'references' / module)
        python = private / 'venv/bin/python'
        bounded([sys.executable, '-m', 'venv', str(private / 'venv')], 60, evidence / 'python-venv')
        bounded([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '-r', str(ROOT / 'tools/conformance-vectors/v1/requirements.txt')],
                180, evidence / 'python-requirements')
        tools['python'] = bounded([str(python), '--version'], 30, evidence / 'python-version')
        tools['jsonschema'] = bounded([str(python), '-c', 'import importlib.metadata; print(importlib.metadata.version("jsonschema"))'],
                                     30, evidence / 'jsonschema-version')
        runtime = private / 'runtime'
        bounded([str(python), str(ROOT / 'tools/live-topology/bootstrap-runtime.py'), str(runtime)], 900, evidence / 'runtime-bootstrap')
        binaries = json.loads((ROOT / 'tools/live-topology/binaries.json').read_text())
        for row in binaries:
            path = runtime / 'bin' / Path(row['source']).name
            if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
                raise RuntimeError(f'Private runtime binary hash mismatch: {path.name}')
        receipt.update(result='prepared', python=str(python), runtime=str(runtime),
                       path=str(python.parent) + os.pathsep + os.environ['PATH'])
        save(evidence / 'preparation.json', receipt)
        if os.environ.get('GITHUB_ENV'):
            with Path(os.environ['GITHUB_ENV']).open('a') as output:
                output.write(f'MCPCLI_CI_PREPARATION={evidence / "preparation.json"}\n')
        print(f'Prepared live CI: {evidence / "preparation.json"}', flush=True)
    except BaseException as error:
        receipt.update(result='failed', error=f'{type(error).__name__}: {error}')
        save(evidence / 'preparation.json', receipt)
        raise


def require_owned(path: Path, runtime: Path) -> dict:
    path = path.resolve()
    if path.name != 'result.json' or path.parent.parent != (runtime / 'runs').resolve():
        raise ValueError('Isolated receipt is outside the prepared runtime.')
    owned = json.loads(path.read_text())
    stopped = owned.get('ownedInfrastructureStopped', {})
    namespaces = owned.get('namespaces', {})
    outside = json.loads((path.parent / 'outside.json').read_text())['namespaces']
    def native_namespaces(value):
        return isinstance(value, dict) and set(value) == NAMESPACES and all(
            isinstance(identity, str) and re.fullmatch(name + r':\[[1-9][0-9]*\]', identity)
            for name, identity in value.items())
    if type(owned.get('commandExitCode')) is not int or owned['commandExitCode'] != 0 \
            or type(owned.get('supervisorPid')) is not int or owned['supervisorPid'] != 1 \
            or owned.get('prerequisitesReady') is not True \
            or not isinstance(stopped, dict) or set(stopped) != SERVICES \
            or any(type(value) is not int or not -signal.NSIG < value <= 255 for value in stopped.values()) \
            or not native_namespaces(namespaces) or not native_namespaces(outside) \
            or any(namespaces[key] == outside[key] for key in namespaces):
        raise ValueError('Private runtime did not prove prerequisites, private namespaces and owned cleanup.')
    return owned


def copy_diagnostics(runtime: Path, output: Path) -> None:
    """Copy an explicit allowlist, excluding state stores, issuer credentials and keys."""
    names = {'result.json', 'outside.json', 'command.stdout.txt', 'command.stderr.txt',
             'sentry.log', 'redis.log', 'placement.log', 'scheduler.log', 'initial-redis-backup.json'}
    for run in sorted((runtime / 'runs').glob('*')):
        if run.is_dir() and not run.is_symlink():
            for name in names:
                path = run / name
                if path.is_file() and not path.is_symlink():
                    target = output / run.name / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(sanitized(path.read_text(errors='replace')))


def run(evidence: Path) -> None:
    report = {'result': 'running', 'fullLiveAccepted': False, 'runId': uuid.uuid4().hex}
    save(evidence / 'ci-live.json', report)
    runtime = None
    try:
        require_contract()
        source = Path(os.environ.get('MCPCLI_CI_PREPARATION', str(evidence / 'preparation.json')))
        if source.resolve() != (evidence / 'preparation.json').resolve():
            raise ValueError('Preparation must come from the current evidence directory.')
        prepared = json.loads(source.read_text())
        if prepared.get('result') != 'prepared' or prepared.get('ownershipId') != (evidence / OWNER_FILE).read_text().strip():
            raise ValueError('Current successful preparation receipt is required.')
        prepared_runtime = Path(prepared['runtime']).resolve()
        python = Path(prepared['python'])
        if not prepared_runtime.is_dir() or not python.is_file() or not TESTS.is_file():
            raise ValueError('Prepared private runtime, Python and built Release integration tests are required.')
        for row in json.loads((ROOT / 'tools/live-topology/binaries.json').read_text()):
            binary = prepared_runtime / 'bin' / Path(row['source']).name
            if hashlib.sha256(binary.read_bytes()).hexdigest() != row['sha256']:
                raise ValueError(f'Prepared runtime binary hash mismatch: {binary.name}')
        if (prepared_runtime / 'runs').exists():
            raise ValueError('CI requires a fresh prepared runtime with no previous runs.')
        runtime = prepared_runtime
        environment = os.environ.copy()
        for key in list(environment):
            if key.startswith(('MCPCLI_LIVE_', 'EVENTSTORE_')):
                del environment[key]
        environment.update(MCPCLI_ISOLATED_RUNTIME_DIR=str(runtime),
                           PATH=str(python.parent) + os.pathsep + prepared['path'])
        generation = evidence / report['runId']
        generation.mkdir()
        vectors = generation / 'vectors'
        report.update(preparationRunId=prepared['runId'], output=str(generation))
        vector_error = None
        try:
            bounded([str(python), str(ROOT / 'tools/live-topology/run-vectors.py'), '--output', str(vectors)],
                    16200, generation / 'vectors-process', environment=environment)
            lane = json.loads((vectors / 'live-lane.json').read_text())
            expected = sorted(json.loads(path.read_text())['operation'] for path in
                              (ROOT / 'tools/conformance-vectors/v1/modules').rglob('*.vector.json'))
            outcomes = lane.get('vectors', [])
            if len(expected) != 21 or len(set(expected)) != 21 or lane.get('coverage') != expected \
                    or lane.get('result') != 'passed' or lane.get('fullLiveAccepted') is not True \
                    or lane.get('passed') != 21 or lane.get('failed') != 0 \
                    or sorted(item.get('operation', '') for item in outcomes) != expected \
                    or len({item.get('isolatedReceipt') for item in outcomes}) != 21 \
                    or any(item.get('result') != 'passed' or item.get('exitCode') != 0 for item in outcomes):
                raise ValueError('Complete current passing evidence for all 21 vectors is required; partial/preflight/skipped evidence is refused.')
            for item in outcomes:
                require_owned(Path(item['isolatedReceipt']), runtime)
            report['vectors'] = {'result': 'passed', 'count': 21, 'receipt': str(vectors / 'live-lane.json')}
        except Exception as error:
            failures = []
            if (vectors / 'live-lane.json').is_file():
                try:
                    lane = json.loads((vectors / 'live-lane.json').read_text())
                    failures = [{key: item.get(key) for key in ('operation', 'result', 'error')}
                                for item in lane.get('vectors', []) if item.get('result') != 'passed']
                except (ValueError, AttributeError, TypeError):
                    pass  # Retain the original failure and still attempt the independent smoke.
            detail = '; failed Operations: ' + ', '.join(str(item['operation']) for item in failures) if failures else ''
            vector_error = RuntimeError(str(error) + detail)
            report['vectors'] = {'result': 'failed', 'error': str(vector_error), 'failures': failures}
        # Smoke stays independent and runs even after a vector assertion failure.
        smoke = generation / 'smoke'
        smoke.mkdir()
        bounded([str(python), str(ROOT / 'tools/live-topology/run-isolated.py'), '--', 'dotnet', str(TESTS),
                 '-class', 'Hexalith.McpCli.Integration.Tests.GatewaySmokeTests', '-failSkips', '-result-xml', str(smoke / 'tests.xml')],
                960, smoke / 'process', environment=environment)
        xml = ET.parse(smoke / 'tests.xml').getroot()
        assemblies, cases = xml.findall('assembly'), xml.findall('.//test')
        if len(assemblies) != 1 or len(cases) != 1 or any(assemblies[0].get(key) != value for key, value in
                [('total', '1'), ('passed', '1'), ('failed', '0'), ('skipped', '0'), ('errors', '0')]) \
                or cases[0].get('result') != 'Pass' or cases[0].get('method') != 'AuthenticatedQueryReturnsSuccessfulDocument' \
                or cases[0].get('type') != 'Hexalith.McpCli.Integration.Tests.GatewaySmokeTests':
            raise ValueError('Independent smoke must contain exactly one passing, unskipped authenticated Gateway case.')
        lines = (smoke / 'process.stdout.txt').read_text().splitlines()
        runs = [Path(line.removeprefix('Isolated run: ')) for line in lines if line.startswith('Isolated run: ')]
        if len(runs) != 1:
            raise ValueError('Independent smoke omitted its isolated runtime receipt.')
        require_owned(runs[0] / 'result.json', runtime)
        report['smoke'] = {'result': 'passed', 'receipt': str(runs[0] / 'result.json')}
        if vector_error:
            raise vector_error
        if len(list((runtime / 'runs').iterdir())) != 22:
            raise ValueError('Expected exactly 21 fresh vector runtimes and one independent smoke runtime.')
        report.update(result='passed', fullLiveAccepted=True)
    except BaseException as error:
        report.update(result='failed', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        if runtime:
            copy_diagnostics(runtime, evidence / report['runId'] / 'runtime-diagnostics')
        for pattern in ('*.stdout.txt', '*.stderr.txt', 'tests.xml'):
            for path in (evidence / report['runId']).rglob(pattern):
                path.write_text(sanitized(path.read_text(errors='replace')))
        save(evidence / 'ci-live.json', report)


def main() -> int:
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        evidence = evidence_directory(preparing=sys.argv[1:] == ['prepare'])
        if sys.argv[1:] == ['prepare']:
            prepare(evidence)
        elif sys.argv[1:] == ['run']:
            run(evidence)
        else:
            raise ValueError('Expected prepare or run.')
        return 0
    except Exception as error:
        print(sanitized(f'Live CI failed: {type(error).__name__}: {error}'), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
