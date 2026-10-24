"""Record sequential final validation commands and immutable source inputs."""
import datetime
import hashlib
import json
import pathlib
import shlex
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[6]
OUT = pathlib.Path(__file__).resolve().parent
CHECKS = []


def run(label, command, timeout=1200):
    started = time.monotonic()
    with (OUT / (label + '.stdout.txt')).open('wb') as stdout, (OUT / (label + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr, timeout=timeout)
    receipt = {'label': label, 'command': command, 'displayCommand': shlex.join(command),
               'cwd': str(ROOT), 'exitCode': result.returncode,
               'elapsedSeconds': round(time.monotonic() - started, 3),
               'recordedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'stdout': label + '.stdout.txt', 'stderr': label + '.stderr.txt'}
    (OUT / (label + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    CHECKS.append(receipt)
    (OUT / 'commands.json').write_text(json.dumps(CHECKS, indent=2) + '\n')
    print(json.dumps({key: receipt[key] for key in ('label', 'exitCode', 'elapsedSeconds')}), flush=True)
    if result.returncode:
        raise RuntimeError(label + ' failed; inspect its recorded output')


if __name__ == '__main__':
    template = json.loads((OUT.parent / 'implementation-file-map.json').read_text())
    inputs = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in template['files']}
    (OUT / 'source-inputs.json').write_text(json.dumps(inputs, indent=2) + '\n')
    run('restore', ['dotnet', 'restore', 'Hexalith.McpCli.slnx'])
    run('release-build', ['dotnet', 'build', 'Hexalith.McpCli.slnx', '--no-restore', '--configuration', 'Release', '-warnaserror'])
    for suite in ('Abstractions', 'Analyzers', 'Core', 'Cli', 'Mcp', 'Manifest'):
        run(suite.lower() + '-tests', ['dotnet', 'test', 'tests/Hexalith.McpCli.' + suite + '.Tests', '--no-build', '--configuration', 'Release'])
    run('runtime-tests', ['python3', '-m', 'unittest', 'discover', '-v', '-s', 'tools/live-topology', '-p', 'test_*.py'])
    for module in ('EventStore', 'Tenants', 'Parties'):
        project = 'Hexalith.' + module
        run('source-' + module.lower() + '-build', ['bash', '-c', 'cd references/' + project + ' && timeout 300 dotnet build src/' + project + '/' + project + '.csproj --configuration Release -warnaserror -m:1 -p:UseHexalithProjectReferences=false -p:UseNuGetDeps=true'])
    run('smoke-discovery', ['dotnet', 'tests/Hexalith.McpCli.Integration.Tests/bin/Release/net10.0/Hexalith.McpCli.Integration.Tests.dll', '-list', 'tests'])
    run('host-dapr-before', ['dapr', 'list', '--output', 'json'])
    run('live-smoke', ['env', 'MCPCLI_ISOLATED_RUNTIME_DIR=/tmp/story-4-12-pass-3-20261024-lnlNCH/runtime', 'PYTHONOPTIMIZE=1', 'HEXALITH_EVENTSTORE_TEST_REDIS_PORT=19999', 'timeout', '--signal=TERM', '--kill-after=20s', '960', 'python3', 'tools/live-topology/run-isolated.py', '--', 'dotnet', 'tests/Hexalith.McpCli.Integration.Tests/bin/Release/net10.0/Hexalith.McpCli.Integration.Tests.dll', '-class', 'Hexalith.McpCli.Integration.Tests.GatewaySmokeTests', '-failSkips'])
    run('host-dapr-after', ['dapr', 'list', '--output', 'json'])
    assert inputs == {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in inputs}, 'Source changed during final validation'
    run('npm-ci', ['npm', 'ci'])
    run('whitespace-check', ['git', 'diff', '--check'])
