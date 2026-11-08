"""Record sanitized command evidence and the source/probe/binary bytes it verifies."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(ROOT / 'tools/live-topology'))
from ci import sanitized


def hashes():
    sources = [
        'src/Hexalith.McpCli.Core/Serialization/ResultDocumentSchema.cs',
        'src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs',
        'src/Hexalith.McpCli.Core/Catalog/RoutingResolver.cs',
        'src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs',
        'src/Hexalith.McpCli.Mcp/McpOutputSchema.cs',
        'src/Hexalith.McpCli/Cli/CliRunner.cs',
        'src/Hexalith.McpCli/Cli/GlobalOptionsBinding.cs',
        'tests/Hexalith.McpCli.Core.Tests/ResultDocumentSchemaTests.cs',
        'tests/Hexalith.McpCli.Mcp.Tests/McpOutputSchemaTests.cs',
        'tools/live-topology/ci.py',
    ]
    binaries = [
        'src/Hexalith.McpCli.Core/bin/Release/net10.0/Hexalith.McpCli.Core.dll',
        'src/Hexalith.McpCli.Mcp/bin/Release/net10.0/Hexalith.McpCli.Mcp.dll',
        'src/Hexalith.McpCli/bin/Release/net10.0/Hexalith.McpCli.dll',
        'tests/fixtures/StdioHost/bin/Release/net10.0/Hexalith.McpCli.StdioHost.dll',
        'tests/Hexalith.McpCli.Core.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.Tests.dll',
        'tests/Hexalith.McpCli.Mcp.Tests/bin/Release/net10.0/Hexalith.McpCli.Mcp.Tests.dll',
        'tests/fixtures/StdioHost/bin/Release/net10.0/Hexalith.McpCli.Core.dll',
        'tests/fixtures/StdioHost/bin/Release/net10.0/Hexalith.McpCli.Mcp.dll',
        'src/Hexalith.McpCli/bin/Release/net10.0/Hexalith.McpCli.Core.dll',
        'src/Hexalith.McpCli/bin/Release/net10.0/Hexalith.McpCli.Mcp.dll',
        'tests/Hexalith.McpCli.Core.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.dll',
        'tests/Hexalith.McpCli.Mcp.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.dll',
        'tests/Hexalith.McpCli.Mcp.Tests/bin/Release/net10.0/Hexalith.McpCli.Mcp.dll',
    ]
    probes = [str(path.relative_to(ROOT)) for path in sorted(OUT.iterdir()) if path.suffix in ('.py', '.mjs')]
    return {group: {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}
            for group, names in (('sources', sources), ('probes', probes), ('binaries', binaries))}


def main():
    name, command = sys.argv[1], sys.argv[2:]
    started = time.monotonic()
    result = subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
    stdout, stderr = sanitized(result.stdout), sanitized(result.stderr)
    (OUT / f'{name}.stdout.txt').write_text(stdout)
    (OUT / f'{name}.stderr.txt').write_text(stderr)
    receipt = {'command': command, 'cwd': str(ROOT), 'exitCode': result.returncode,
               'seconds': round(time.monotonic() - started, 2), 'hashAlgorithm': 'sha256',
               'hashesRecordedAt': 'command completion', 'hashes': hashes()}
    (OUT / f'{name}.json').write_text(sanitized(json.dumps(receipt, indent=2)) + '\n')
    print(stdout[-6000:])
    print(stderr[-1000:])
    print('exit', result.returncode)
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
