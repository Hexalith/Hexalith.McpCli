"""Guard-removal controls for nested-pin resolution plus every retained prior control.

The 169 prior controls are read as literal data from the preserved
manifest-selector runner (bound by SHA-256; never executed). Eight prior
anchors moved into the cross-tree resolver; each adaptation removes the same
guard at its new location and is listed in ADAPTED. NESTED controls remove
each new refusal or reporting guard. Every control must make its covering
fixture fail. Use --nested-only for focused implementation checks.
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
prior_runner = packet.parent / 'manifest-selector-resolution-20261111' / 'mutation-guards.py'
PRIOR_SHA256 = '443ce011c63dcf48d07c9f29b07fd01479e597a5540446baddffc31a1e8a7ea3'
source = (root / 'tools/proprietary-surfaces/v1/check.py').read_text()
source = source.replace("ROOT = Path(__file__).resolve().parents[3]", f'ROOT = Path({str(root)!r})')


def prior_controls():
    raw = prior_runner.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != PRIOR_SHA256:
        raise SystemExit('Preserved prior runner changed: ' + actual)
    lists = {}
    for node in ast.parse(raw.decode()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id.endswith('_mutations'):
            lists[node.targets[0].id] = ast.literal_eval(node.value)
    return [control for name in ('prior_mutations', 'review_mutations', 'coverage_mutations', 'manifest_mutations')
            for control in lists[name]], actual


# Same guard, new anchor: the import/Compile resolution moved into Resolver.
ADAPTED = {
    'P3': [('values, references, documents, linked = project_metadata(tree, path, set(paths), errors, resolver)',
            "values, references, documents, linked = project_metadata(tree, path, {p for p in paths if "
            "p.endswith(('.props', '.targets'))}, errors, resolver)")],
    'P12': [('label = resolver.canonical_label(label_path(project, value))',
             'label = resolver.canonical_label(label_path(current, value))')],
    'S17': [('                    if resolver.local(label):\n                        # Project-relative sources stay',
             '                    if not resolver.escaping(label):\n                        # Project-relative sources stay')],
    'S22': [("except (CensusError, OSError, UnicodeError) as error:\n            entry = {'path': path",
             "except (CensusError, OSError, UnicodeError) as error:\n            raise\n            entry = {'path': path")],
    'Review-S07-required': [("require(import_optional(element, label), f'unavailable-local-import:{current}')", 'pass')],
    'Review-S07-optional': [("if alternatives and all('$(' not in item and resolver.canonical_label(label_path(current, item)) == label",
                             "if False and all('$(' not in item and resolver.canonical_label(label_path(current, item)) == label")],
    'Review-S07-nested': [('if substitution is None and resolver.local(label):',
                           'if substitution is None and not resolver.escaping(label):')],
    'Review-S07-escape': [("Refusal('unsafe-import-path', current, label).require(import_optional(element, label))", 'pass')],
}

NESTED = [
    ('N01-above-parent-root', [("refusal.require(not self.escaping(target))  # Above the parent root.", 'pass')],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
    ('N02-parent-glob', [("refusal.require(wildcard is None)  # Parent-tree directories are never listed.", 'pass')],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
    ('N03-parent-blob', [("refusal.require(inner not in self.workspace.parent.entries)  # Parent-tree blobs are never read.", 'pass')],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
    ('N04-parent-directory', [("refusal.require(not any(p.startswith(inner + '/') for p in self.workspace.parent.entries))", 'pass')],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
    ('N05-root-directory', [("refusal.require(bool(inner) and not any(p.startswith(inner + '/') for p in tree.entries))  # Directory.",
                             "refusal.require(bool(inner))  # Directory.")],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
    ('N06-root-itself', [("refusal.require(bool(inner) and not any(p.startswith(inner + '/') for p in tree.entries))  # Directory.",
                          "refusal.require(not any(p.startswith(inner + '/') for p in tree.entries) if inner else True)  # Directory.")],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
    ('N07-regular-blob', [('refusal.require(entry[0] in REGULAR)', 'pass')],
     'test_nested_pin_substituted_links_are_not_regular_blobs'),
    ('N08-substituted-gitlink', [("refusal.require(not any(entry[0] == '160000' and (inner == p or inner.startswith(p + '/'))\n"
                                  "                                for p, entry in tree.entries.items()))", 'pass')],
     'test_nested_pin_second_hop_escapes_and_substituted_gitlinks_refuse'),
    ('N09-glob-gitlink', [("refusal.require(not any(entry[0] == '160000' and (not inner or p.startswith(inner + '/'))\n"
                           "                                    for p, entry in tree.entries.items()))", 'pass')],
     'test_nested_pin_compile_sources_and_globs_resolve_with_provenance'),
    ('N10-second-hop', [('raise refusal()  # The single permitted hop is already used.',
                         'return self.locate(label, None, refusal)')],
     'test_nested_pin_second_hop_escapes_and_substituted_gitlinks_refuse'),
    ('N11-workspace-object', [("raise refusal('workspace-object-unavailable') from None", 'raise')],
     'test_nested_pin_unavailable_workspace_root_object_refuses'),
    ('N12-root-uninitialized', [("require(not git(location, 'rev-parse', '--show-prefix'), 'reference-root-uninitialized')", 'pass')],
     'test_nested_pin_unavailable_workspace_root_object_refuses'),
    ('N13-nested-ambiguous', [("refusal.require(len(roots) == 1, 'nested-pin-unresolvable')",
                               "refusal.require(len(roots) >= 1, 'nested-pin-unresolvable')")],
     'test_nested_pin_ambiguous_and_relative_root_identities_refuse'),
    ('N14-nested-unresolvable', [("refusal.require(len(roots) == 1, 'nested-pin-unresolvable')", 'pass')],
     'test_nested_pin_url_identity_requires_one_exact_absolute_declaration'),
    ('N15-relative-url', [("if not nonblank(url) or url in ('.', '..') or url.startswith(('./', '../')):",
                           'if not nonblank(url):')],
     'test_nested_pin_ambiguous_and_relative_root_identities_refuse'),
    ('N16-trim-slash', [("url = url[:-1] if url.endswith('/') else url", 'url = url')],
     'test_nested_pin_url_identity_requires_one_exact_absolute_declaration'),
    ('N17-trim-git', [("url = url[:-4] if url.endswith('.git') else url", 'url = url')],
     'test_nested_pin_url_identity_requires_one_exact_absolute_declaration'),
    ('N18-trim-one-git', [("url = url[:-4] if url.endswith('.git') else url", "url = re.sub(r'(?:\\.git)+\\Z', '', url)")],
     'test_nested_pin_url_identity_requires_one_exact_absolute_declaration'),
    ('N19-trim-one-slash', [("url = url[:-1] if url.endswith('/') else url", "url = url.rstrip('/')")],
     'test_nested_pin_url_identity_requires_one_exact_absolute_declaration'),
    ('N20-host-case', [('return match[1] + userinfo + at + host.lower() + match[3]', 'return match[1] + userinfo + at + host + match[3]')],
     'test_nested_pin_url_identity_requires_one_exact_absolute_declaration'),
    ('N21-path-case', [('return match[1] + userinfo + at + host.lower() + match[3]',
                        'return match[1] + userinfo + at + host.lower() + match[3].lower()')],
     'test_nested_pin_url_identity_requires_one_exact_absolute_declaration'),
    ('N22-malformed-declarations', [('    except (CensusError, configparser.Error):\n        return {}', '    finally:\n        pass')],
     'test_nested_pin_url_identity_requires_one_exact_absolute_declaration'),
    ('N23-nested-object', [("raise refusal('nested-object-unavailable') from None", 'raise')],
     'test_nested_pin_missing_nested_commit_is_unavailable'),
    ('N24-no-lazy-fetch', [("env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'})", 'env={**os.environ})')],
     'test_nested_pin_partial_clone_objects_are_never_fetched'),
    ('N25-exists-disjunction', [("if any(match[1].lower() == 'or' for match in operators):\n        return []",
                                 "if False:\n        return []")],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
    ('N26-exists-local-disjunction', [("if any(match[1].lower() == 'or' for match in operators):\n        return []",
                                       "if False:\n        return []")],
     'test_nested_pin_local_exists_conjunction_is_optional_and_disjunction_is_required'),
    ('N27-exists-parentheses', [("            masked.append(' ' if depth else char)", '            masked.append(char)')],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
    ('N28-exists-quotes', [("            quote = None if char == quote else quote\n            masked.append(' ')",
                            "            quote = None if char == quote else quote\n            masked.append(char)")],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
    ('N29-exists-unbalanced-quote', [('    if quote or depth:\n        return []', '    if depth:\n        return []')],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
    ('N30-exists-negative-depth', [('            if depth < 0:\n                return []', '            if False:\n                return []')],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
    ('N31-exists-negation', [("""exists = re.fullmatch(r'''\\s*Exists\\(""", """exists = re.fullmatch(r'''\\s*!?\\s*Exists\\(""")],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
    ('N32-exists-exact-path', [("if alternatives and all('$(' not in item and resolver.canonical_label(label_path(current, item)) == label",
                                "if alternatives and all('$(' not in item")],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
    ('N33-provenance', [('self.reads[canonical(record)] = record', 'pass')],
     'test_nested_pin_workspace_import_reads_sibling_root_at_its_pin'),
    ('N34-nested-provenance', [("record['nestedGitlink'] = substitution.gitlink", 'pass')],
     'test_nested_pin_import_reads_same_url_root_at_the_nested_commit'),
    ('N35-error-targets', [("if isinstance(error, CensusError) and error.target:\n                entry['target'] = error.target",
                            "if False:\n                entry['target'] = error.target")],
     'test_nested_pin_url_identity_requires_one_exact_absolute_declaration'),
    ('N36-compile-error-targets', [("**({'target': error.target} if error.target else {})}", '}')],
     'test_nested_pin_compile_sources_and_globs_resolve_with_provenance'),
    ('N37-local-closure', [('path for path in set(documents) | linked if path in tree.entries}', 'path for path in set(documents) | linked}')],
     'test_nested_pin_local_closure_and_context_free_api'),
    ('N38-context-free-refusal', [('refusal.require(self.workspace is not None)', 'pass')],
     'test_nested_pin_local_closure_and_context_free_api'),
    ('N39-compile-second-hop', [("found, _ = resolver.matches(label, resolver.substitution(current), 'unsafe-or-nested-compile-source', current)",
                                 "found, _ = resolver.matches(label, None, 'unsafe-or-nested-compile-source', current)")],
     'test_nested_pin_second_hop_escapes_and_substituted_gitlinks_refuse'),
    ('N40-substituted-import-hop', [('                substitution = resolver.substitution(current)\n                for value in expanded_values(raw',
                                     '                substitution = None\n                for value in expanded_values(raw')],
     'test_nested_pin_second_hop_escapes_and_substituted_gitlinks_refuse'),
    ('N41-pin-not-head', [("self.trees[key] = Tree(location, commit)", "self.trees[key] = Tree(location, 'HEAD')")],
     'test_nested_pin_workspace_import_reads_sibling_root_at_its_pin'),
    ('N42-nested-commit', [('tree = self.workspace.tree(roots[0], commit)',
                            'tree = self.workspace.tree(roots[0], self.workspace.roots[roots[0]])')],
     'test_nested_pin_import_reads_same_url_root_at_the_nested_commit'),
    ('N43-root-directory-label', [('return label if target == self.repository or self.escaping(target) else',
                                   'return label if self.escaping(target) else')],
     'test_nested_pin_exists_guarded_absent_escapes_are_optional_only_when_required'),
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
    parser.add_argument('--nested-only', action='store_true')
    args = parser.parse_args()
    prior, prior_sha = prior_controls()
    names = {name for name, _, _ in prior}
    if set(ADAPTED) - names:
        raise SystemExit('Unknown adapted controls: ' + ', '.join(sorted(set(ADAPTED) - names)))
    controls = [] if args.nested_only else [(name, ADAPTED.get(name, replacements), test, 'adapted' if name in ADAPTED else 'retained')
                                            for name, replacements, test in prior]
    controls += [(name, replacements, test, 'new') for name, replacements, test in NESTED]
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
    print(json.dumps(dict(schema='mcpcli-census-mutation-controls/v1', result='passed', priorRunnerSha256=prior_sha,
                          mutationCount=len(results), newCount=sum(r['origin'] == 'new' for r in results),
                          adaptedCount=sum(r['origin'] == 'adapted' for r in results), controls=results), indent=2))


if __name__ == '__main__':
    main()
