#!/usr/bin/env python3
"""Remove one Story 5.11 guard or AND operand at a time and run every test."""
import argparse
import ast
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import importlib.util
import io
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import CodeType
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
STORY = HERE.parent
previous_spec = importlib.util.spec_from_file_location(
    'pass6_sweep', STORY/'review-pass-6-20261126/sweep_guards.py')
previous = importlib.util.module_from_spec(previous_spec)
previous_spec.loader.exec_module(previous)
from evidence_redaction import known_credentials

BUILDER = 'build_packet.py'
MODULES = previous.MODULES | {BUILDER: previous.test_verify_reconciliation.B}
SOURCES = {name: (STORY/name).read_bytes() for name in MODULES}
TREES = {name: ast.parse(raw) for name, raw in SOURCES.items()}
BASELINE_TESTS = 0
RUNNER_SOURCES = {path: path.read_bytes() for path in (Path(__file__),Path(previous.__file__))}


def cache_ledger_parsing():
    # Ledger parsing and redaction have no mutation targets. Cache their pure
    # results by exact inputs and give each test an independent copy of the rows.
    verifier = MODULES['verify_reconciliation.py']
    builder = MODULES[BUILDER]
    scoped = builder.scoped_deferrals
    historical = verifier.historical_deferrals
    frozen = {}

    @lru_cache(maxsize=32)
    def ambient_rows(text, credentials):
        return scoped(text)

    def scoped_rows(text, sanitize=None):
        if sanitize is not None:
            return scoped(text, sanitize)
        return deepcopy(ambient_rows(text, frozenset(known_credentials())))

    def historical_rows(root):
        revision = verifier.INVENTORY_PUBLICATION
        policy = builder.git(root, 'show', revision+':scripts/evidence_redaction.py')
        ledger = builder.git(root, 'show', revision+':'+str(verifier.LEDGER))
        key = (policy, ledger)
        if key not in frozen:
            frozen[key] = historical(root)
        return deepcopy(frozen[key])

    builder.scoped_deferrals = scoped_rows
    verifier.historical_deferrals = historical_rows


def cache_fixture_subprocesses():
    # Reuse real Git results for exact, approved one-file patches applied to
    # fresh isolated fixtures. A cached apply also writes the actual result
    # bytes. Altered patches, nested scratch directories and mock failures
    # still exercise the ordinary call path.
    root = MODULES[BUILDER].ROOT
    manifest = json.loads((STORY/'upstream/manifest.json').read_bytes())
    patch_paths = {
        (root/file['patch']['path']).read_bytes(): file['path']
        for owner in manifest['owners'] for file in owner['files']
        if file.get('format') != 'literal-replacements'
    }
    commands = {('apply','--numstat','-z','-'),('apply','--check','-'),('apply','-')}
    outputs = {}
    initializations = {}
    sync_results = {}
    sync_script = 'scripts/check-agent-instructions-sync.sh'

    def raw_bytes(path):
        with open(path,'rb') as stream:
            return stream.read()

    def run(command, *args, **kwargs):
        if command == ['bash',sync_script] and not args and kwargs == {'cwd':root,'capture_output':True}:
            inputs = (sync_script,'AGENTS.md','CLAUDE.md','.github/copilot-instructions.md')
            key = tuple(raw_bytes(root/path) for path in inputs)
            if key not in sync_results:
                sync_results[key] = previous.RUN(command,**kwargs)
            return sync_results[key]
        if not isinstance(command,list) or len(command) < 4 or command[:2] != ['git','-C'] or args:
            return previous.run_cached_git(command,*args,**kwargs)
        scratch = Path(command[2])
        if scratch.parent != previous.SCRATCH or not scratch.name.startswith('reconciliation-patch-'):
            return previous.run_cached_git(command,**kwargs)
        if command[3:] == ['init','--quiet'] and kwargs.keys() == {'env','capture_output'} and not any(scratch.iterdir()):
            key = tuple(sorted(kwargs['env'].items()))
            repository = scratch/'.git'
            if key not in initializations:
                result = previous.RUN(command,**kwargs)
                if result.returncode == 0:
                    template = Path(tempfile.mkdtemp(prefix='guard-git-',dir=previous.SCRATCH))/'.git'
                    shutil.copytree(repository,template)
                    initializations[key] = (template,result.stdout,result.stderr)
                return result
            template,stdout,stderr = initializations[key]
            shutil.copytree(template,repository)
            return subprocess.CompletedProcess(command,0,stdout,stderr)
        if (tuple(command[3:]) not in commands
                or kwargs.keys() != {'input','env','capture_output'} or kwargs['capture_output'] is not True
                or kwargs['input'] not in patch_paths):
            return previous.run_cached_git(command,*args,**kwargs)
        target = scratch/patch_paths[kwargs['input']]
        config = scratch/'.git/config'
        if (not config.is_file() or (scratch/'.git/index').exists()
                or not target.is_file() or target.is_symlink()):
            return previous.run_cached_git(command,*args,**kwargs)
        operation = tuple(command[3:])
        key = (operation, kwargs['input'], raw_bytes(target), target.stat().st_mode,
               raw_bytes(config), tuple(sorted(kwargs['env'].items())))
        applies = operation == ('apply','-')
        if key not in outputs:
            result = previous.RUN(command,**kwargs)
            if result.returncode != 0:
                return result
            applied = raw_bytes(target) if applies else None
            outputs[key] = (result.stdout,result.stderr,applied)
        stdout,stderr,applied = outputs[key]
        if applied is not None:
            target.write_bytes(applied)
        return subprocess.CompletedProcess(command,0,stdout,stderr)

    subprocess.run = run


@dataclass(frozen=True)
class Target:
    file: str
    names: tuple
    line: int
    column: int
    kind: str
    operand: int | None
    expression: str

    @property
    def key(self):
        position = f'{self.file}:{self.line}:{self.column}'
        return position if self.operand is None else f'{position}:and{self.operand + 1}'


def referenced_helpers():
    """Find builder functions reached directly or through other builder functions."""
    functions = {node.name: node for node in TREES[BUILDER].body
                 if isinstance(node, ast.FunctionDef)}
    callers = [node.func.attr for node in ast.walk(TREES['verify_reconciliation.py'])
               if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and isinstance(node.func.value, ast.Name) and node.func.value.id == 'B'
               and node.func.attr in functions]
    visited = set()
    while callers:
        name = callers.pop()
        if name in visited:
            continue
        visited.add(name)
        callers.extend(node.func.id for node in ast.walk(functions[name])
                       if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                       and node.func.id in functions)
    return visited


def function_bodies(tree):
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            yield (node.name,), node
        elif isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, ast.FunctionDef):
                    yield (node.name, member.name), member


def guard_kind(node):
    if (isinstance(node, ast.If) and not node.orelse and len(node.body) == 1
            and isinstance(node.body[0], ast.Raise)):
        return 'if-raise'
    return previous.guard_kind(node)


def targets():
    helpers = referenced_helpers()
    for filename, tree in TREES.items():
        for names, function in function_bodies(tree):
            if filename == BUILDER and names[0] not in helpers:
                continue
            for statement in ast.walk(function):
                kind = guard_kind(statement)
                if kind is None:
                    continue
                yield Target(filename, names, statement.lineno, statement.col_offset,
                             kind, None, ast.unparse(statement))
                if kind == 'require':
                    condition = statement.value.args[0]
                    if isinstance(condition, ast.BoolOp) and isinstance(condition.op, ast.And):
                        for index, operand in enumerate(condition.values):
                            yield Target(filename, names, statement.lineno, statement.col_offset,
                                         'require-operand', index, ast.unparse(operand))


def changed_code(target):
    class Remove(ast.NodeTransformer):
        removed = 0

        def generic_visit(self, node):
            if ((getattr(node, 'lineno', None), getattr(node, 'col_offset', None))
                    != (target.line, target.column) or guard_kind(node) is None):
                return super().generic_visit(node)
            self.removed += 1
            if target.operand is None:
                return ast.copy_location(ast.Pass(), node)
            condition = node.value.args[0]
            del condition.values[target.operand]
            if len(condition.values) == 1:
                node.value.args[0] = condition.values[0]
            return node

    modifier = Remove()
    tree = modifier.visit(ast.parse(SOURCES[target.file]))
    if modifier.removed != 1:
        raise ValueError(f'{target.key} changed {modifier.removed} guards')
    return compile(ast.fix_missing_locations(tree), str(STORY/target.file), 'exec')


def mutate(target):
    function = MODULES[target.file]
    changed = changed_code(target)
    for name in target.names:
        function = getattr(function, name)
        changed = next(code for code in changed.co_consts
                       if isinstance(code, CodeType) and code.co_name == name)
    original = function.__code__
    function.__code__ = changed
    try:
        run = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite(previous.suite()))
    finally:
        function.__code__ = original

    if run.testsRun != BASELINE_TESTS or run.skipped:
        raise ValueError(f'{target.key} did not run all {BASELINE_TESTS} tests')
    failures = [case.id() for case, _ in run.failures + run.errors]
    return {
        'target': target.key,
        'function': '.'.join(target.names),
        'kind': target.kind,
        'status': 'killed' if failures else 'survived',
        'testsRun': run.testsRun,
        'failureCount': len(failures),
        'firstFailure': failures[0] if failures else None,
    }


def account(results, bindings, chosen):
    survivors = {item['target'] for item in results if item['status'] == 'survived'}
    matched = set()
    for item in results:
        key = item['target']
        if key in survivors:
            expression = chosen[key].expression
            item['expression'] = expression
            record = bindings.get(key)
            if record is not None and record['expression'] == expression:
                item['binding'] = record['binding']
                matched.add(key)
    missing = sorted(survivors - matched)
    stale = sorted(bindings.keys() - matched)
    return missing, stale


def execute(chosen, jobs):
    results = []
    with multiprocessing.get_context('fork').Pool(jobs) as workers:
        for item in workers.imap_unordered(mutate, chosen.values()):
            results.append(item)
            if item['status'] == 'survived':
                print(f"survived {item['target']}: {chosen[item['target']].expression}", flush=True)
            if len(results) % 25 == 0 or len(results) == len(chosen):
                print(f'{len(results)} of {len(chosen)} removals tested', flush=True)
    return results


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def execution_rows(results, chosen, test_count):
    rows = {}
    for item in results:
        key = item['target']
        failed = item['status'] == 'killed'
        if (key in rows or key not in chosen or item['kind'] != chosen[key].kind
                or item['function'] != '.'.join(chosen[key].names) or item['testsRun'] != test_count
                or item['status'] not in {'killed','survived'}
                or failed != (item['failureCount'] > 0) or failed != bool(item['firstFailure'])):
            raise ValueError(f'invalid or partial mutation result: {key}')
        rows[key] = {field: value for field,value in item.items() if field not in {'binding','expression'}}
    if rows.keys() != chosen.keys():
        raise ValueError('result does not cover the current target set')
    return [rows[key] for key in chosen]


def main():
    global BASELINE_TESTS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=('all','statements','operands'), default='all')
    parser.add_argument('--jobs', type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument('--reuse', type=Path, help='Reconcile dispositions against a complete run on the same bytes')
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    if previous.SCRATCH is None:
        parser.error('run under run-with-temp')

    tests = previous.suite()
    BASELINE_TESTS = len(tests)
    all_targets = {target.key: target for target in targets()}
    chosen = {key: target for key, target in all_targets.items()
              if args.mode == 'all' or (target.operand is not None) == (args.mode == 'operands')}
    fingerprints = {
        'schemaVersion': '1.0.0',
        'mode': args.mode,
        'baselineTests': BASELINE_TESTS,
        'sourceSha256': {name: digest(raw) for name,raw in SOURCES.items()},
        'testSha256': {path.name: digest(raw) for path,raw in previous.TEST_SOURCES.items()},
        'runnerSha256': {path.parent.name: digest(raw) for path,raw in RUNNER_SOURCES.items()},
    }
    if args.reuse is None:
        cache_fixture_subprocesses()
        cache_ledger_parsing()
        baseline = unittest.TextTestRunner().run(unittest.TestSuite(tests))
        if not baseline.wasSuccessful() or baseline.skipped or baseline.testsRun != BASELINE_TESTS:
            return 1
        measured = execute(chosen,args.jobs)
    else:
        prior = json.loads(args.reuse.read_bytes())
        if any(prior.get(key) != value for key,value in fingerprints.items()):
            print('FAIL: completed sweep does not match current source, tests, runner or mode',file=sys.stderr)
            return 1
        measured = prior['results']
    try:
        results = execution_rows(measured,chosen,BASELINE_TESTS)
    except (KeyError, ValueError) as error:
        print(f'FAIL: {error}',file=sys.stderr)
        return 1
    execution_sha = digest(json.dumps(results,sort_keys=True,separators=(',',':')).encode())
    if args.reuse is not None and prior.get('executionRowsSha256') != execution_sha:
        print('FAIL: completed sweep execution results differ',file=sys.stderr)
        return 1

    snapshots = {STORY/name: raw for name, raw in SOURCES.items()} | previous.TEST_SOURCES | RUNNER_SOURCES
    if any(path.read_bytes() != raw for path, raw in snapshots.items()):
        print('FAIL: source or tests changed during the sweep', file=sys.stderr)
        return 1
    binding_file = HERE/'guard-bindings.json'
    binding_bytes = binding_file.read_bytes()
    bindings = json.loads(binding_bytes)
    if any(not entry['binding'].strip() for entry in bindings.values()):
        raise ValueError('every retained guard disposition must name its binding')
    applicable = {key: reason for key, reason in bindings.items()
                  if key in chosen or key not in all_targets}
    missing, stale = account(results, applicable, chosen)
    evidence = {
        **fingerprints,
        'executionRowsSha256': execution_sha,
        'bindingsSha256': digest(binding_bytes),
        'targets': len(results),
        'killed': sum(item['status'] == 'killed' for item in results),
        'survived': sum(item['status'] == 'survived' for item in results),
        'unrecordedSurvivors': missing,
        'staleBindings': stale,
        'results': results,
    }
    args.output.write_text(json.dumps(evidence, indent=2) + '\n')
    if missing or stale:
        print(f'FAIL: {len(missing)} unrecorded survivors, {len(stale)} stale bindings',file=sys.stderr)
        return 1
    print(f"PASS: {evidence['killed']} removals detected, {evidence['survived']} survivors independently accounted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
