#!/usr/bin/env python3
"""Install only the staged tool into a private environment and retain raw offline checks."""

import argparse
import json
import os
from pathlib import Path
import platform
import queue
import subprocess
import sys
import threading
from paired_release import check_prepared, digest, module, packages, write_new


def require(condition, message):
    if not condition:
        raise ValueError(message)


def json_document(raw):
    require(raw.endswith(b'\n') and b'\r' not in raw and not raw.startswith(b'\xef\xbb\xbf'), 'JSON output must use UTF-8 with LF internally and at its terminator.')
    return json.loads(raw)


def smoke(staging, prepared_path, output):
    staging = Path(staging).absolute()
    prepared = check_prepared(staging, prepared_path)
    output = Path(output).absolute()
    require(not output.exists() and not output.is_symlink(), 'Smoke output already exists; prior evidence will not be overwritten.')
    output.mkdir(parents=True)
    captures = output / 'discovery'
    captures.mkdir()
    private = output / 'private'
    private.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith(('EVENTSTORE_', 'MCPCLI_', 'NUGET_'))}
    env.update({'MCPCLI_HOME': str(private / 'home'), 'DOTNET_CLI_HOME': str(private / 'dotnet-home'),
                'NUGET_PACKAGES': str(private / 'packages'), 'NUGET_HTTP_CACHE_PATH': str(private / 'http-cache'),
                'NUGET_PLUGINS_CACHE_PATH': str(private / 'plugin-cache'), 'DOTNET_SKIP_FIRST_TIME_EXPERIENCE': '1',
                'DOTNET_CLI_TELEMETRY_OPTOUT': '1', 'DOTNET_NOLOGO': '1', 'DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE': 'true'})
    config = private / 'NuGet.Config'
    from xml.sax.saxutils import escape
    config.write_text('<configuration><packageSources><clear/><add key="staged" value="' + escape(str(staging), {'"': '&quot;'})
                      + '"/></packageSources><fallbackPackageFolders><clear/></fallbackPackageFolders></configuration>', encoding='utf-8')
    tools = private / 'tools'

    def execute(name, argv, expected=0, override=None):
        completed = subprocess.run([str(item) for item in argv], env=override or env, cwd=private, capture_output=True, timeout=120)
        (output / (name + '.stdout.txt')).write_bytes(completed.stdout)
        (output / (name + '.stderr.txt')).write_bytes(completed.stderr)
        write_new(output / (name + '.command.json'), {'argv': [str(item) for item in argv], 'exit_code': completed.returncode})
        require(completed.returncode == expected, f'{name} returned {completed.returncode}; inspect its retained stdout/stderr.')
        return completed

    execute('install', ['dotnet', 'tool', 'install', 'Hexalith.McpCli', '--tool-path', tools, '--version', prepared['version'],
                        '--configfile', config, '--no-cache'])
    tool = tools / ('hexalith.exe' if os.name == 'nt' else 'hexalith')
    result = execute('version', [tool, '--version'])
    require(result.stdout.decode('utf-8').strip() == prepared['version'] and not result.stderr, 'Installed tool version/channel mismatch.')

    def discovery(name, *arguments):
        result = execute(name, [tool, *arguments])
        require(not result.stderr, f'{name} wrote unexpected diagnostics.')
        (captures / (name + '.json')).write_bytes(result.stdout)
        return json_document(result.stdout)

    modules = discovery('modules', 'modules')
    require(modules.get('modules'), 'The installed tool catalog is empty.')
    operation_names = []
    for item in modules['modules']:
        operations = discovery('operations-' + item['name'], 'operations', item['name'])
        operation_names.extend(operation['name'] for operation in operations['operations'])
    require(operation_names, 'The installed tool has no operations.')
    for name in operation_names:
        discovery('describe-' + name, 'describe', name)
    target = private / 'result.json'
    result = execute('output-file', [tool, 'modules', '--output', target])
    require(not result.stdout and not result.stderr and target.read_bytes() == (captures / 'modules.json').read_bytes(), 'Output-file bytes/channels differ from discovery.')
    result = execute('table', [tool, 'modules', '--format', 'table'])
    require(result.stdout.startswith(b'NAME\tOPERATIONS\tDESCRIPTION') and not result.stderr, 'Table output/channel mismatch.')
    result = execute('invalid-home', [tool, 'config', 'current'], 2, {**env, 'MCPCLI_HOME': 'relative-secret-home'})
    expected_error = {'error': {'code': 'configuration_invalid', 'message': 'Invalid mcpcli profile file: MCPCLI_HOME must be an absolute directory path.'}}
    require(not result.stderr and json_document(result.stdout) == expected_error, 'Invalid home did not fail safely on the JSON stdout channel.')
    result = execute('mcp-invalid-home', [tool, 'mcp', '--transport', 'stdio'], 2, {**env, 'MCPCLI_HOME': 'relative-secret-home'})
    require(not result.stdout and json_document(result.stderr) == expected_error, 'MCP startup error polluted the protocol channel.')
    for name, args in [
        ('config-add', ['profile', 'add', 'staged', '--url', 'http://127.0.0.1:1', '--token', 'staged-private-token']),
        ('config-use', ['use', 'staged']), ('config-current', ['current']), ('config-clear', ['use', '--clear']),
        ('config-remove', ['profile', 'remove', 'staged']),
    ]:
        result = execute(name, [tool, 'config', *args])
        json_document(result.stdout)
        require(not result.stderr and b'staged-private-token' not in result.stdout, 'Config output exposed a token or wrote diagnostics.')
    require((private / 'home/.eventstore/mcpcli.json').is_file(), 'Config did not use the isolated MCPCLI_HOME.')
    mcp_smoke(tool, env, private, output, captures, modules, operation_names[0])
    require(packages(staging, prepared['version']) == prepared['packages'], 'Staged bytes changed during installation smoke.')
    receipt = {'schema': 'mcpcli-paired-smoke/v1', 'status': 'passed', 'os': platform.system(),
               'source_sha': prepared['source_sha'], 'version': prepared['version'], 'packages': prepared['packages'],
               'preparation_sha256': digest(prepared_path),
               'discovery': {path.name: digest(path) for path in sorted(captures.iterdir())},
               'checks': ['version', 'offline-discovery', 'config', 'json-lf', 'errors', 'mcp-protocol', 'output-file', 'table']}
    write_new(output / 'smoke.json', receipt)


def mcp_smoke(tool, env, private, output, captures, modules, operation):
    child = subprocess.Popen([str(tool), 'mcp', '--transport', 'stdio'], cwd=private, env=env,
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    messages = queue.Queue()
    transcript = bytearray()
    errors = bytearray()

    def read_stdout():
        for line in child.stdout:
            transcript.extend(line)
            messages.put(line)
        messages.put(None)

    def read_stderr():
        errors.extend(child.stderr.read())

    readers = [threading.Thread(target=read_stdout), threading.Thread(target=read_stderr)]
    for reader in readers:
        reader.start()

    def send(document):
        child.stdin.write((json.dumps(document, separators=(',', ':')) + '\n').encode())
        child.stdin.flush()

    def request(identity, method, parameters):
        send({'jsonrpc': '2.0', 'id': identity, 'method': method, 'params': parameters})
        while True:
            line = messages.get(timeout=60)
            require(line is not None, 'MCP exited before responding.')
            document = json.loads(line)
            require(document.get('jsonrpc') == '2.0', 'Non-protocol data appeared on MCP stdout.')
            if document.get('id') == identity:
                require('result' in document and 'error' not in document, f'MCP request {method} failed.')
                return document['result'], line

    try:
        initialized, _ = request(1, 'initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
                                                'clientInfo': {'name': 'paired-stage-smoke', 'version': '1.0.0'}})
        require(initialized['protocolVersion'] == '2025-06-18', 'MCP initialization version mismatch.')
        send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        tools, raw = request(2, 'tools/list', {})
        require([tool['name'] for tool in tools['tools']] == ['list_modules', 'list_operations', 'describe_operation', 'send_command', 'run_query'], 'MCP tool discovery differs from the fixed surface.')
        (captures / 'mcp-tools.json').write_bytes(raw)
        result, raw = request(3, 'tools/call', {'name': 'list_modules', 'arguments': {}})
        require(result.get('isError') is False and result['structuredContent'] == modules
                and json.loads(result['content'][0]['text']) == modules, 'MCP/CLI module discovery differs.')
        (captures / 'mcp-modules.json').write_bytes(raw)
        description, _ = request(4, 'tools/call', {'name': 'describe_operation', 'arguments': {'operation': operation}})
        require(description.get('isError') is False and description['structuredContent'] == json.loads((captures / ('describe-' + operation + '.json')).read_bytes()), 'MCP/CLI operation description differs.')
        failure, _ = request(5, 'tools/call', {'name': 'describe_operation', 'arguments': {'operation': '__missing__'}})
        require(failure.get('isError') is True and failure['structuredContent']['error']['code'] == 'unknown_operation'
                and json.loads(failure['content'][0]['text']) == failure['structuredContent'], 'MCP error document/channel mismatch.')
        child.stdin.close()
        child.wait(timeout=30)
        require(child.returncode == 0, 'MCP did not exit cleanly after stdin closed.')
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=30)
        for reader in readers:
            reader.join(timeout=30)
        (output / 'mcp.stdout.jsonl').write_bytes(transcript)
        (output / 'mcp.stderr.txt').write_bytes(errors)
    for line in transcript.splitlines():
        require(json.loads(line).get('jsonrpc') == '2.0', 'MCP stdout contains non-protocol output.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staging', type=Path, required=True)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        smoke(args.staging, args.prepared, args.output)
        return 0
    except (ValueError, KeyError, OSError, subprocess.SubprocessError, queue.Empty) as error:
        print(f'Paired tool smoke failed: {module("verify-release-source").failure_detail(error)}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
