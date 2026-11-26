#!/usr/bin/env python3
"""Remove one guard at a time and run the complete Story 5.11 suite."""
import argparse
import ast
import hashlib
import io
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import time
from types import CodeType
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
STORY = HERE.parent
sys.path.insert(0, str(STORY))

import test_offline_cli
import test_verify_reconciliation

MODULES = {
    'verify_reconciliation.py': test_verify_reconciliation.V,
    'check_offline_cli.py': test_offline_cli.C,
}
TEST_MODULES = (test_verify_reconciliation, test_offline_cli)
PRIORITY = {}
SOURCES = {name: (STORY / name).read_bytes() for name in MODULES}
TEST_SOURCES = {Path(module.__file__): Path(module.__file__).read_bytes() for module in TEST_MODULES}
GIT_RESULTS = {}
RUN = subprocess.run
SCRATCH = Path(os.environ['TMPDIR']).resolve() if 'TMPDIR' in os.environ else None


def cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item


def suite():
    loader = unittest.TestLoader()
    return [case for module in TEST_MODULES for case in cases(loader.loadTestsFromModule(module))]


def guard_kind(node):
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return None
    call = node.value
    if isinstance(call.func, ast.Name) and call.func.id == 'require':
        return 'require'
    if (isinstance(call.func, ast.Attribute) and call.func.attr == 'git' and
            any(isinstance(arg, ast.Constant) and arg.value == '--is-ancestor' for arg in call.args)):
        return 'ancestry'
    return None


def guards():
    for filename in MODULES:
        tree = ast.parse(SOURCES[filename])
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                functions = [((node.name,), node)]
            elif isinstance(node, ast.ClassDef):
                functions = [((node.name, member.name), member) for member in node.body
                             if isinstance(member, ast.FunctionDef)]
            else:
                continue
            for names, function in functions:
                for statement in sorted(ast.walk(function), key=lambda item: getattr(item, 'lineno', 0)):
                    kind = guard_kind(statement)
                    if kind:
                        yield (filename, names, statement.lineno, statement.col_offset, kind, ast.unparse(statement))


class BaselineResult(unittest.TextTestResult):
    """Prioritize tests that reached the guard in the passing baseline."""

    def startTest(self, test):
        super().startTest(test)
        self.lines = set()
        self.refusals = set()
        self.started = time.monotonic()
        sys.settrace(self.trace)

    def stopTest(self, test):
        sys.settrace(None)
        duration = time.monotonic() - self.started
        for line in self.lines:
            PRIORITY.setdefault(line, {})[test.id()] = (0 if line in self.refusals else 1, duration)
        super().stopTest(test)

    def trace(self, frame, event, argument):
        name = frame.f_code.co_filename
        if name in SOURCE_FILES:
            line = (SOURCE_FILES[name], frame.f_lineno)
            if event == 'line':
                self.lines.add(line)
            elif event == 'exception' and issubclass(argument[0], ValueError):
                self.refusals.add(line)
            return self.trace
        return None


SOURCE_FILES = {str(STORY / filename): filename for filename in MODULES}


def remove_guard(filename, line, column):
    source = STORY / filename

    class Remove(ast.NodeTransformer):
        removed = 0

        def visit_Expr(self, node):
            if (node.lineno, node.col_offset) == (line, column) and guard_kind(node):
                self.removed += 1
                return ast.copy_location(ast.Pass(), node)
            return self.generic_visit(node)

    modifier = Remove()
    tree = modifier.visit(ast.parse(SOURCES[filename]))
    if modifier.removed != 1:
        raise ValueError(f'{filename}:{line}:{column} removed {modifier.removed} guards')
    return compile(ast.fix_missing_locations(tree), str(source), 'exec')


def mutate(guard):
    filename, names, line, column, kind, statement = guard
    target = MODULES[filename]
    changed = remove_guard(filename, line, column)
    for name in names:
        target = getattr(target, name)
        changed = next(code for code in changed.co_consts if isinstance(code, CodeType) and code.co_name == name)
    original = target.__code__
    target.__code__ = changed
    try:
        executed = suite()
        priority = PRIORITY.get((filename, line), {})
        executed.sort(key=lambda case: priority.get(case.id(), (2, float('inf'))))
        captured = io.StringIO()
        run = unittest.TextTestRunner(stream=captured, failfast=True).run(unittest.TestSuite(executed))
    finally:
        target.__code__ = original

    failures = [case.id() for case, _ in run.failures + run.errors]
    return {
        'file': filename,
        'function': '.'.join(names),
        'line': line,
        'column': column,
        'kind': kind,
        'statement': statement,
        'status': 'killed' if failures else 'survived',
        'testsRun': run.testsRun,
        'failures': failures,
    }


def run_cached_git(command, *args, **kwargs):
    # Test fixtures replay the same committed owner objects and locally observed
    # refs repeatedly. Cache those reads after the baseline and leave all scratch
    # repositories and any command with other process options to real Git.
    if (not isinstance(command, list) or len(command) < 5 or command[:2] != ['git', '-C'] or
            command[3] not in {'show', 'merge-base', 'rev-parse', 'rev-list', 'ls-tree', 'remote', 'diff', 'cat-file'} or
            kwargs != {'capture_output': True} or args or not SCRATCH or Path(command[2]).is_relative_to(SCRATCH)):
        return RUN(command, *args, **kwargs)
    key = tuple(command)
    if key not in GIT_RESULTS:
        GIT_RESULTS[key] = RUN(command, **kwargs)
    return GIT_RESULTS[key]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=min(8, os.cpu_count() or 1))
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    subprocess.run = run_cached_git
    baseline = unittest.TextTestRunner(resultclass=BaselineResult).run(unittest.TestSuite(suite()))
    if not baseline.wasSuccessful():
        return 1

    targets = list(guards())
    evidence = {
        'schemaVersion': '1.0.0',
        'baselineTests': baseline.testsRun,
        'sourceSha256': {name: hashlib.sha256(contents).hexdigest() for name, contents in SOURCES.items()},
        'testSha256': {path.name: hashlib.sha256(contents).hexdigest() for path, contents in TEST_SOURCES.items()},
        'runnerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'targets': len(targets),
        'removedGuards': json.loads((HERE / 'removed-guards.json').read_bytes()),
        'results': [],
    }
    with multiprocessing.get_context('fork').Pool(args.jobs) as workers:
        for result in workers.imap_unordered(mutate, targets):
            if result['status'] == 'killed':
                result.pop('statement')
            evidence['results'].append(result)
            remaining = len(targets) - len(evidence['results'])
            print(f"{result['status']}: {result['file']}:{result['line']} ({remaining} remaining)", flush=True)

    evidence['results'].sort(key=lambda row: (row['file'], row['line'], row['column']))
    evidence['killed'] = sum(row['status'] == 'killed' for row in evidence['results'])
    evidence['survived'] = len(targets) - evidence['killed']
    snapshotted_files = {STORY / name: contents for name, contents in SOURCES.items()} | TEST_SOURCES
    if any(path.read_bytes() != contents for path, contents in snapshotted_files.items()):
        print('FAIL: source or tests changed during the sweep', file=sys.stderr)
        return 1
    args.output.write_text(json.dumps(evidence, indent=2) + '\n')
    return int(evidence['survived'] != 0)


if __name__ == '__main__':
    raise SystemExit(main())
