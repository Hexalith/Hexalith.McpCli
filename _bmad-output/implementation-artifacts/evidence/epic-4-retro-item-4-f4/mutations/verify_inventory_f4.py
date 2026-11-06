from pathlib import Path
import difflib
import hashlib
import json
import shlex
import subprocess
import sys

root = Path('/home/administrator/projects/hexalith/mcpcli')
evidence = Path(__file__).resolve().parent
project = 'tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj'
assembly = str(root / 'tests/Hexalith.McpCli.Core.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.Tests.dll')
gate = root / 'tests/Hexalith.McpCli.Core.Tests/InventoryCoverageGate.cs'
original_bytes = gate.read_bytes()
original = original_bytes.decode()
receipts = json.loads((evidence / 'commands.json').read_text()) if (evidence / 'commands.json').exists() else []
build = ['dotnet', 'build', project, '--no-restore', '--configuration', 'Release', '-warnaserror']


def run(name, argv, cwd, expected):
    log = evidence / (name + '.log')
    command = shlex.join(argv)
    print('START ' + name + ': ' + command, flush=True)
    with log.open('w') as stream:
        stream.write('cwd: ' + str(cwd) + '\ncommand: ' + command + '\n\n')
        stream.flush()
        result = subprocess.run(argv, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT, check=False)
        stream.write('\nexit_code: ' + str(result.returncode) + '\n')
    receipt = {'name': name, 'argv': argv, 'command': command, 'cwd': str(cwd),
               'exit_code': result.returncode, 'expected': expected, 'log': str(log)}
    receipts.append(receipt)
    (evidence / 'commands.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print('DONE ' + name + ': exit ' + str(result.returncode), flush=True)
    if (expected == 'pass' and result.returncode != 0) or (expected == 'test-failure' and result.returncode != 1):
        print(log.read_text(), flush=True)
        raise RuntimeError('Unexpected result for ' + name)
    return receipt


def test_command(method=None):
    selector = ['-method', '*InventoryCoverageTests.' + method] if method else ['-class', '*InventoryCoverageTests']
    return ['dotnet', assembly, *selector, '-verbose', '-noLogo']


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError('Mutation requires exactly one match: ' + repr(old))
    return text.replace(old, new, 1)


mode = sys.argv[1]
if mode == 'baseline':
    run('baseline-build', build, root, 'pass')
    run('baseline-inventory-tests-from-tmp', test_command(), Path('/tmp'), 'pass')
elif mode == 'mutations':
    mutations = [
        ('internal-catalog-null-guard', 'RejectsUnavailableInternalCatalogDespiteUsablePublicDocument',
         [('if (access.Catalog is null || result.Document is null || result.Error is not null)',
           'if (result.Document is null || result.Error is not null)'),
          ('OperationDescriptor[] descriptors = access.Catalog.Modules',
           'OperationDescriptor[] descriptors = access.Catalog!.Modules')]),
        ('unauthorized-access-catch', 'RejectsInventoryDirectoryReadDenied',
         [('exception is IOException or UnauthorizedAccessException', 'exception is IOException')]),
        ('unknown-exclusion-disposition', 'RejectsInvalidScope',
         [('row.Coverage == "exclude" && row.Disposition is not ("withdraw" or "defer")',
           'row.Coverage == "exclude" && row.Disposition == "replace"')]),
        ('target-name-start-anchor', 'RejectsInvalidScope',
         [(r'!Regex.IsMatch(target.Name, "\\A" + Regex.Escape(inventory.Module)',
           r'!Regex.IsMatch(target.Name, Regex.Escape(inventory.Module)')]),
        ('json-comment-rejection', 'RejectsJsonCommentsAndTrailingCommas',
         [('parsed = JsonDocument.Parse(json);',
           'parsed = JsonDocument.Parse(json, new JsonDocumentOptions { CommentHandling = JsonCommentHandling.Skip });')]),
        ('json-trailing-comma-rejection', 'RejectsJsonCommentsAndTrailingCommas',
         [('parsed = JsonDocument.Parse(json);',
           'parsed = JsonDocument.Parse(json, new JsonDocumentOptions { AllowTrailingCommas = true });')]),
    ]
    try:
        for name, method, replacements in mutations:
            mutated = original
            for old, new in replacements:
                mutated = replace_once(mutated, old, new)
            (evidence / (name + '.patch')).write_text(''.join(difflib.unified_diff(
                original.splitlines(keepends=True), mutated.splitlines(keepends=True),
                fromfile='InventoryCoverageGate.cs.original', tofile='InventoryCoverageGate.cs.mutated')))
            gate.write_bytes(mutated.encode())
            try:
                run(name + '-build', build, root, 'pass')
                run(name + '-tests', test_command(method), Path('/tmp'), 'test-failure')
            finally:
                gate.write_bytes(original_bytes)
    finally:
        gate.write_bytes(original_bytes)
        (evidence / 'restoration.json').write_text(json.dumps({
            'file': str(gate), 'original_sha256': hashlib.sha256(original_bytes).hexdigest(),
            'restored_sha256': hashlib.sha256(gate.read_bytes()).hexdigest(),
            'byte_identical': gate.read_bytes() == original_bytes,
            'note': 'Null-forgiving operator in the internal-catalog mutation only suppresses the nullable compiler warning to allow runtime guard verification.'
        }, indent=2) + '\n')
    run('restored-final-build', build, root, 'pass')
    run('restored-final-inventory-tests-from-tmp', test_command(), Path('/tmp'), 'pass')
else:
    raise RuntimeError('Unknown mode')
