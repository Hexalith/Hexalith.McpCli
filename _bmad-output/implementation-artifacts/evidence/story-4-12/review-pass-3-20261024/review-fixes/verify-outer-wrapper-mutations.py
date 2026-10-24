"""Prove that the new public-wrapper tests reject dropped arguments and empty commands."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

source = Path('tools/live-topology').resolve()
evidence = Path(__file__).resolve().parent
original = (source / 'run-isolated.py').read_text()
mutations = [
    ('empty-command-guard-removed',
     "    if not command:\n        sys.exit('A command to execute is required.')\n", '',
     'test_public_wrapper_requires_a_command_before_creating_files_or_launching_namespaces'),
    ('outer-command-forwarding-removed',
     "'--inside', str(run_dir), '--', *command])", "'--inside', str(run_dir), '--'])",
     'test_public_wrapper_forwards_the_supplied_child_and_its_failure_through_namespace_launch'),
]
results = []
for name, before, after, method in mutations:
    assert original.count(before) == 1, name
    mutated = original.replace(before, after, 1)
    with tempfile.TemporaryDirectory(prefix='mcpcli-wrapper-review-mutation-') as directory:
        target = Path(directory)
        for file in ('test_runtime.py', 'bootstrap-runtime.py', 'binaries.json'):
            shutil.copyfile(source / file, target / file)
        (target / 'run-isolated.py').write_text(mutated)
        command = ['python3', str(target / 'test_runtime.py'), 'RuntimeTests.' + method]
        result = subprocess.run(command, text=True, capture_output=True, timeout=20)
        (evidence / (name + '.stdout.txt')).write_text(result.stdout)
        (evidence / (name + '.stderr.txt')).write_text(result.stderr)
        assert result.returncode != 0 and 'AssertionError' in result.stderr, name
        results.append({'mutation': name, 'method': method, 'command': command,
                        'exitCode': result.returncode, 'rejectedByAssertion': True,
                        'mutatedWrapperSha256': hashlib.sha256(mutated.encode()).hexdigest(),
                        'stdout': name + '.stdout.txt', 'stderr': name + '.stderr.txt'})
(evidence / 'outer-wrapper-mutations.json').write_text(json.dumps(results, indent=2) + '\n')
print('Both public-wrapper mutations were rejected by their targeted assertions.')
