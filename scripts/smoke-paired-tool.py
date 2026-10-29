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
import time
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
        return execute_command(output, private, override or env, name, argv, expected)

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
    config_smoke(tool, execute, private / 'home/.eventstore/mcpcli.json')
    mcp_smoke(tool, env, private, output, captures, modules)
    require(packages(staging, prepared['version']) == prepared['packages'], 'Staged bytes changed during installation smoke.')
    receipt = {'schema': 'mcpcli-paired-smoke/v1', 'status': 'passed', 'os': platform.system(),
               'source_sha': prepared['source_sha'], 'version': prepared['version'], 'packages': prepared['packages'],
               'preparation_sha256': digest(prepared_path),
               'discovery': {path.name: digest(path) for path in sorted(captures.iterdir())},
               'checks': ['version', 'offline-discovery', 'config', 'json-lf', 'errors', 'mcp-protocol', 'output-file', 'table']}
    write_new(output / 'smoke.json', receipt)


def execute_command(output, private, env, name, argv, expected=0):
    argv = [str(item) for item in argv]
    try:
        completed = subprocess.run(argv, env=env, cwd=private, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired as error:
        (output / (name + '.stdout.txt')).write_bytes(error.stdout or b'')
        (output / (name + '.stderr.txt')).write_bytes(error.stderr or b'')
        write_new(output / (name + '.command.json'), {'argv': argv, 'exit_code': None, 'outcome': 'timeout', 'timeout_seconds': 120})
        raise
    (output / (name + '.stdout.txt')).write_bytes(completed.stdout)
    (output / (name + '.stderr.txt')).write_bytes(completed.stderr)
    write_new(output / (name + '.command.json'), {'argv': argv, 'exit_code': completed.returncode})
    require(completed.returncode == expected, f'{name} returned {completed.returncode}; inspect its retained stdout/stderr.')
    return completed


def config_smoke(tool, execute, profile_path):
    profile = {'url': 'http://127.0.0.1:1', 'token': 'staged-private-token'}
    empty = {'version': 1, 'profiles': {}}
    saved = {'version': 1, 'profiles': {'staged': profile}}
    selected = {**saved, 'activeProfile': 'staged'}
    sources = {key: 'default' for key in ('tenant', 'actor', 'format', 'allowTenantOverride', 'readOnly', 'strict', 'output', 'allowedExtensions')}
    current = {'profile': 'staged', 'url': 'http://127.0.0.1:1/', 'token': 'stag***', 'tenant': None,
               'actor': None, 'allowTenantOverride': False, 'allowedExtensions': [], 'format': 'json',
               'output': None, 'readOnly': False, 'strict': False,
               'sources': {**sources, 'profile': 'activeProfile', 'url': 'profile', 'token': 'profile'}}
    for name, args, document, state in [
        ('config-add', ['profile', 'add', 'staged', '--url', profile['url'], '--token', profile['token']],
         {'name': 'staged', 'activeProfile': None}, saved),
        ('config-use', ['use', 'staged'], {'activeProfile': 'staged'}, selected),
        ('config-current', ['current'], current, selected),
        ('config-clear', ['use', '--clear'], {'activeProfile': None}, saved),
        ('config-remove', ['profile', 'remove', 'staged'], {'name': 'staged', 'activeProfile': None}, empty),
    ]:
        result = execute(name, [tool, 'config', *args])
        require(not result.stderr and profile['token'].encode() not in result.stdout,
                'Config output exposed a token or wrote diagnostics.')
        require(json_document(result.stdout) == document, f'{name} output document differs from the command contract.')
        require(json.loads(profile_path.read_text()) == state, f'{name} did not persist the expected isolated profile state.')


def protocol_document(line):
    document = json.loads(line)
    valid = isinstance(document, dict) and document.get('jsonrpc') == '2.0'
    if valid and 'id' in document:
        identity = document['id']
        valid = (identity is None or type(identity) in (int, str)) and (('result' in document) != ('error' in document))
        valid = valid and set(document) <= {'jsonrpc', 'id', 'result', 'error'}
        if valid and 'error' in document:
            error = document['error']
            valid = (isinstance(error, dict) and type(error.get('code')) is int
                     and isinstance(error.get('message'), str) and set(error) <= {'code', 'message', 'data'})
    elif valid:
        valid = (isinstance(document.get('method'), str) and bool(document['method'])
                 and set(document) <= {'jsonrpc', 'method', 'params'}
                 and ('params' not in document or isinstance(document['params'], (dict, list))))
    require(valid, 'Non-protocol data appeared on MCP stdout.')
    return document


def request_mcp(send, messages, identity, method, parameters):
    deadline = time.monotonic() + 60
    send({'jsonrpc': '2.0', 'id': identity, 'method': method, 'params': parameters})
    while True:
        remaining = deadline - time.monotonic()
        require(remaining > 0, f'MCP request {method} exceeded its 60 second deadline.')
        line = messages.get(timeout=remaining)
        require(line is not None, 'MCP exited before responding.')
        document = protocol_document(line)
        if document.get('id') == identity:
            require('result' in document and 'error' not in document, f'MCP request {method} failed.')
            return document['result'], line


def mcp_smoke(tool, env, private, output, captures, modules):
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
        return request_mcp(send, messages, identity, method, parameters)

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
        identity = 4
        for item in modules['modules']:
            name = item['name']
            operations = json.loads((captures / ('operations-' + name + '.json')).read_bytes())
            result, raw = request(identity, 'tools/call', {'name': 'list_operations', 'arguments': {'module': name}})
            require(result.get('isError') is False and result['structuredContent'] == operations
                    and json.loads(result['content'][0]['text']) == operations, 'MCP/CLI operation discovery differs.')
            (captures / ('mcp-operations-' + name + '.json')).write_bytes(raw)
            identity += 1
            for operation in operations['operations']:
                name = operation['name']
                expected = json.loads((captures / ('describe-' + name + '.json')).read_bytes())
                description, raw = request(identity, 'tools/call', {'name': 'describe_operation', 'arguments': {'operation': name}})
                require(description.get('isError') is False and description['structuredContent'] == expected
                        and json.loads(description['content'][0]['text']) == expected, 'MCP/CLI operation description differs.')
                (captures / ('mcp-describe-' + name + '.json')).write_bytes(raw)
                identity += 1
        failure, _ = request(identity, 'tools/call', {'name': 'describe_operation', 'arguments': {'operation': '__missing__'}})
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
        for stream in (child.stdin, child.stdout, child.stderr):
            stream.close()
        (output / 'mcp.stdout.jsonl').write_bytes(transcript)
        (output / 'mcp.stderr.txt').write_bytes(errors)
    for line in transcript.splitlines():
        protocol_document(line)


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
