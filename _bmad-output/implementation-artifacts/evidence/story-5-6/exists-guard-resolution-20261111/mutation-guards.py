"""Guard-removal controls for Exists() guard evaluation plus every retained prior control.

Prior controls are read as literal data, never executed: the 169 manifest-selector
controls, with the nested-pin packet's 8 anchor adaptations, and its 43 nested
controls. Both preserved runners are bound by SHA-256. GUARD controls remove each
new guard rule. Every control must make its covering fixture fail. Use
--guard-only for focused implementation checks.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path.cwd()
packet = Path(__file__).resolve().parent
RUNNERS = {
    'manifest': (packet.parent / 'manifest-selector-resolution-20261111' / 'mutation-guards.py',
                 '443ce011c63dcf48d07c9f29b07fd01479e597a5540446baddffc31a1e8a7ea3'),
    'nested': (packet.parent / 'nested-pin-resolution-20261111' / 'mutation-guards.py',
               '63f8c89c3b47eeb0bcfd5fa36e1a809947914dccab14b31ea23027d27f5cd962'),
}
source = (root / 'tools/proprietary-surfaces/v1/check.py').read_text()
source = source.replace("ROOT = Path(__file__).resolve().parents[3]", f'ROOT = Path({str(root)!r})')


def literals(name, wanted):
    path, expected = RUNNERS[name]
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise SystemExit('Preserved runner changed: ' + str(path))
    found = {}
    for node in ast.parse(raw.decode()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in wanted:
            found[node.targets[0].id] = ast.literal_eval(node.value)
    return found


# An absent Exists()-guarded import is now optional twice: the guard proof runs first
# and import_optional remains for committed but excluded paths. Removing the guard
# means removing both, so this prior control also disables the positive-absent proof.
GUARD_ADAPTED = {
    'Review-S07-optional': [
        ("if alternatives and all('$(' not in item and resolver.canonical_label(label_path(current, item)) == label",
         "if False and all('$(' not in item and resolver.canonical_label(label_path(current, item)) == label"),
        ('if not guard[1] and all(resolver.absent(label, resolver.substitution(current)) for label in labels):', 'if False:')],
}


def prior_controls():
    manifest = literals('manifest', {'prior_mutations', 'review_mutations', 'coverage_mutations', 'manifest_mutations'})
    nested = literals('nested', {'ADAPTED', 'NESTED'})
    controls = []
    for group in ('prior_mutations', 'review_mutations', 'coverage_mutations', 'manifest_mutations'):
        for name, replacements, test in manifest[group]:
            if name in GUARD_ADAPTED:
                controls.append((name, GUARD_ADAPTED[name], test, 'guard-adapted'))
            else:
                controls.append((name, nested['ADAPTED'].get(name, replacements), test,
                                 'adapted' if name in nested['ADAPTED'] else 'retained'))
    return controls + [(name, replacements, test, 'nested') for name, replacements, test in nested['NESTED']]


NEGATED = 'test_exists_guard_negated_present_fallback_import_is_not_visited'
CHAIN = 'test_exists_guard_self_referential_property_fallback_chain_drops_unreachable_alternatives'
GUARD = [
    ('E01-unreachable-definition', [('return  # An unreachable conditional definition contributes no alternative.', 'pass')], CHAIN),
    ('E02-unreachable-import', [('return  # An unreachable import is not visited.', 'pass')], NEGATED),
    ('E03-negated-present', [('if guard[1] and all(resolver.present(label) for label in labels):\n                        return True',
                              'if False:\n                        return True')], NEGATED),
    ('E04-positive-absent', [('if not guard[1] and all(resolver.absent(label, resolver.substitution(current)) for label in labels):',
                              'if False:')], NEGATED),
    ('E05-every-expansion-present', [('if guard[1] and all(resolver.present(label) for label in labels):',
                                      'if guard[1] and any(resolver.present(label) for label in labels):')], NEGATED),
    ('E06-every-expansion-absent', [('if not guard[1] and all(resolver.absent(label, resolver.substitution(current)) for label in labels):',
                                     'if not guard[1] and any(resolver.absent(label, resolver.substitution(current)) for label in labels):')], NEGATED),
    ('E07-nested-never-present', [('        else:\n            return False  # Non-recursive checkouts lack every path under a nested gitlink.',
                                   '        else:\n            return True')], NEGATED),
    ('E08-unresolved-property', [("if not alternatives or any('$(' in item for item in alternatives):\n                        continue  # An unresolved property proves nothing.",
                                  'if not alternatives:\n                        continue  # An unresolved property proves nothing.')], NEGATED),
    ('E09-outside-root-not-present', [('                return False  # Above the parent root or outside every root: never proven present.',
                                       '                return not self.escaping(target) and target in self.workspace.parent.entries')], NEGATED),
    ('E10-refused-not-absent', [('            return False  # A refused or unresolvable path proves nothing.', '            return True')], NEGATED),
    ('E11-local-directory-not-absent', [("            return label not in self.tree.entries and not any(p.startswith(label + '/') for p in self.tree.entries)",
                                         '            return label not in self.tree.entries')], NEGATED),
    ('E12-local-directory-present', [("        return entry is not None and entry[0] in REGULAR or any(p.startswith(inner + '/') for p in tree.entries)",
                                      '        return entry is not None and entry[0] in REGULAR')], NEGATED),
    ('E13-glob-not-absent', [("        if re.search(r'[*?]', label):\n            return False\n        if substitution is None and self.local(label):",
                              '        if substitution is None and self.local(label):')], NEGATED),
    ('E14-import-group-guards', [('            evaluated = guards + ((own,) if own is not None else ())',
                                  '            evaluated = (own,) if own is not None else ()')], NEGATED),
    ('E15-property-group-guards', [('            evaluated = guards + ((own,) if own is not None else ())',
                                    '            evaluated = (own,) if own is not None else ()')], CHAIN),
    ('E16-when-not-evaluated', [("name in ('propertygroup', 'importgroup') else ()),",
                                "name in ('propertygroup', 'importgroup', 'when') else ()),")], CHAIN),
    ('E17-choose-import-union', [("name in ('propertygroup', 'importgroup') else ()),",
                                 "name in ('propertygroup', 'importgroup', 'when') else ()),")], NEGATED),
    ('E18-target-not-static', [("name, static and name != 'target')", 'name, static)')], CHAIN),
    ('E19-property-group-only', [("if conditional and static and parent == 'propertygroup' and unreachable(evaluated):",
                                  'if conditional and static and unreachable(evaluated):')], CHAIN),
    ('E20-parenthesized', [("""guard = re.fullmatch(r'''\\s*(!\\s*)?Exists\\(\\s*(["'])(.*?)\\2\\s*\\)\\s*''', conjunct, re.I | re.S)""",
                            """guard = re.fullmatch(r'''\\s*\\(?\\s*(!\\s*)?Exists\\(\\s*(["'])(.*?)\\2\\s*\\)\\s*\\)?\\s*''', conjunct, re.I | re.S)""")], NEGATED),
    ('E21-negated-group', [("""guard = re.fullmatch(r'''\\s*(!\\s*)?Exists\\(\\s*(["'])(.*?)\\2\\s*\\)\\s*''', conjunct, re.I | re.S)""",
                            """guard = re.fullmatch(r'''\\s*(!\\s*\\(?\\s*)?Exists\\(\\s*(["'])(.*?)\\2\\s*\\)\\s*\\)?\\s*''', conjunct, re.I | re.S)""")], NEGATED),
    ('E22-disjunction', [("if any(match[1].lower() == 'or' for match in operators):\n        return []", 'if False:\n        return []')], NEGATED),
    ('E23-chain-disjunction', [("if any(match[1].lower() == 'or' for match in operators):\n        return []", 'if False:\n        return []')], CHAIN),
    ('E24-unbalanced', [('    if quote or depth:\n        return []', '    if False:\n        return []')], NEGATED),
]

RUNNER = '''import importlib.util,sys,unittest
sys.path.insert(0,sys.argv[1])
for name,path in [('tests',sys.argv[2]),('mutant',sys.argv[3])]:
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 if name=='tests':tests=module
 else:tests.census=module
result=unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite([tests.CensusTests(sys.argv[4])]))
sys.exit(0 if result.wasSuccessful() else 1)
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--guard-only', action='store_true')
    args = parser.parse_args()
    controls = [] if args.guard_only else prior_controls()
    controls += [(name, replacements, test, 'new') for name, replacements, test in GUARD]
    results = []
    with tempfile.TemporaryDirectory() as temporary:
        for name, replacements, test, origin in controls:
            changed = source
            for before, after in replacements:
                if before not in changed:
                    raise SystemExit('Missing mutation anchor ' + name + ': ' + before)
                if origin != 'retained' and changed.count(before) != 1:
                    raise SystemExit('Ambiguous mutation anchor ' + name + ': ' + before)
                changed = changed.replace(before, after, 1)
            mutant = Path(temporary) / (name + '.py')
            mutant.write_text(changed)
            process = subprocess.run([sys.executable, '-c', RUNNER, str(root / 'scripts'),
                                      str(root / 'tools/proprietary-surfaces/v1/test_census.py'), str(mutant), test],
                                     capture_output=True, text=True, timeout=600)
            if process.returncode != 1 or 'FAILED (' not in process.stderr:
                raise SystemExit(f'{name} mutation not caught: {process.returncode}\n{process.stdout}\n{process.stderr}')
            results.append(dict(patch=name, origin=origin, test=test, result='detected', exitCode=process.returncode))
    print(json.dumps(dict(schema='mcpcli-census-mutation-controls/v1', result='passed',
                          runners={key: value[1] for key, value in RUNNERS.items()}, mutationCount=len(results),
                          newCount=sum(r['origin'] == 'new' for r in results), origins={origin: sum(r['origin'] == origin for r in results)
                          for origin in ('retained', 'adapted', 'guard-adapted', 'nested', 'new')}, controls=results), indent=2))


if __name__ == '__main__':
    main()
