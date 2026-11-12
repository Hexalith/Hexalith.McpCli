"""Guard-removal controls for the Exists() guard excuse and nested-pin review fixes.

Prior controls are read as literal data, never executed: the 169 manifest-selector
controls with the nested-pin packet's 8 anchor adaptations, and its 43 nested
controls. Both preserved runners are bound by SHA-256. The superseded
exists-guard-resolution runner is not used: the pruning code its 24 controls
removed was reverted by review loop 1.

ADAPTED lists each prior control whose anchor or covering fixture this change
moved; it removes the same guard. EXCUSE, REVIEW and SECOND (second review)
controls remove each new rule.
Every control must make its covering fixture fail. Use --new-only for focused
implementation checks.
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


EXCLUDED = 'test_guard_excuse_committed_excluded_import_keeps_the_exact_exists_rule'
ALLOW = "    environment['GIT_ALLOW_PROTOCOL'] = ''  # An empty allow list overrides protocol.<name>.allow and inheritance.\n"
PARENT_ABSENT = 'refusal.require(self.workspace.parent.absent(inner))'
TREE_ABSENT = 'refusal.require(tree.absent(inner))'
NESTED_FETCH = 'test_nested_pin_partial_clone_objects_are_never_fetched'
# name: (replacements, covering test or None to keep it, reason)
ADAPTED = {
    'Review-S07-required': ([("require(import_optional(element, label) or excused(element, enclosing, raw, value),\n"
                              "                                        f'unavailable-local-import:{current}')", 'pass')], None,
                            'The required local import check now also accepts the excuse; the same refusal is removed.'),
    'Review-S07-escape': ([("Refusal('unsafe-import-path', current, label).require(\n"
                            "                                    import_optional(element, label) or excused(element, enclosing, raw, value))",
                            'pass')], None,
                          'The absent cross-tree refusal now also accepts the excuse; the same refusal is removed.'),
    'Review-S07-optional': ([("if alternatives and all('$(' not in item and resolver.canonical_label(label_path(current, item)) == label",
                              "if False and all('$(' not in item and resolver.canonical_label(label_path(current, item)) == label")],
                            EXCLUDED, 'An absent exact-Exists() target is also excused, so only a committed but excluded '
                                      'target, present to the guard model, isolates the exact-path rule (VG1).'),
    'N24-no-lazy-fetch': ([("environment.update({'GIT_NO_LAZY_FETCH': '1', 'GIT_NO_REPLACE_OBJECTS': '1'})",
                            "environment.update({'GIT_NO_REPLACE_OBJECTS': '1'})"),
                           ("'-c', 'protocol.allow=never', ", ''), (ALLOW, '')], NESTED_FETCH,
                          'protocol.allow=never and an empty GIT_ALLOW_PROTOCOL also block the lazy fetch, so the fetch '
                          'guard is removed only with all three.'),
    'N03-parent-blob': ([(PARENT_ABSENT, 'pass')], None,
                        'Parent-tree blob, directory, case-variant, link and root checks are now one Tree.absent() check.'),
    'N04-parent-directory': ([(PARENT_ABSENT, 'pass')], None,
                             'Parent-tree blob, directory, case-variant, link and root checks are now one Tree.absent() check.'),
    'N05-root-directory': ([(TREE_ABSENT, 'pass')], None,
                           'A substituted literal miss is absent only through Tree.absent(), which refuses directories and roots.'),
    'N06-root-itself': ([(TREE_ABSENT, 'pass')], None,
                        'A substituted literal miss is absent only through Tree.absent(), which refuses directories and roots.'),
    'N08-substituted-gitlink': ([("refusal.require(not any(entry[0] == '160000' and (inner == p or inner.startswith(p + '/'))\n"
                                  "                                for p, entry in tree.entries.items()))", 'pass'),
                                 ('                and not self.opaque(inner))', ')')], None,
                                'Tree.absent() now also treats a gitlink prefix as unknown, so the substituted-gitlink refusal '
                                'is removed only with both.'),
    'N31-exists-negation': ([('if exists and not exists[1]:', 'if exists:')], None,
                            'The exact rule now parses conjuncts with EXISTS_GUARD; the same negation check is removed.'),
}


def prior_controls():
    manifest = literals('manifest', {'prior_mutations', 'review_mutations', 'coverage_mutations', 'manifest_mutations'})
    nested = literals('nested', {'ADAPTED', 'NESTED'})
    controls = [(name, nested['ADAPTED'].get(name, replacements), test, 'adapted' if name in nested['ADAPTED'] else 'retained')
                for group in ('prior_mutations', 'review_mutations', 'coverage_mutations', 'manifest_mutations')
                for name, replacements, test in manifest[group]]
    controls += [(name, replacements, test, 'nested') for name, replacements, test in nested['NESTED']]
    names = {name for name, _, _, _ in controls}
    if set(ADAPTED) - names:
        raise SystemExit('Unknown adapted controls: ' + ', '.join(sorted(set(ADAPTED) - names)))
    return [(name, ADAPTED[name][0], ADAPTED[name][1] or test, 'excuse-adapted') if name in ADAPTED else (name, replacements, test, origin)
            for name, replacements, test, origin in controls]


OWN = 'test_guard_excuse_own_and_import_group_conditions_excuse_absent_targets'
PRESENT_GUARD = "if guard[1] and all(resolver.present(label, substitution,"
UNPROVEN = 'test_guard_excuse_unproven_guards_keep_the_refusal'
CARRIED = 'test_guard_excuse_carried_property_guard_requires_every_producing_definition_refuted'
CHAINS = 'test_guard_excuse_generic_fallback_chains_end_with_zero_errors'
NEVER = 'test_guard_excuse_never_skips_present_imports_or_classification_alternatives'
BASES = 'test_guard_excuse_condition_paths_resolve_from_declaring_import_or_entry_project'
HOPS = 'test_guard_excuse_substituted_guards_stay_within_their_one_hop_tree'
EXCUSE = [
    ('X01-local-excuse', [('require(import_optional(element, label) or excused(element, enclosing, raw, value),',
                           'require(import_optional(element, label),')], OWN),
    ('X02-cross-tree-excuse', [('import_optional(element, label) or excused(element, enclosing, raw, value))',
                                'import_optional(element, label))')], OWN),
    ('X03-own-condition', [("conditions = [condition for condition in (attribute(element, 'Condition'),",
                            'conditions = [condition for condition in (None,')], OWN),
    ('X04-import-group', [("enclosing[1] if enclosing[0] == 'importgroup' else None) if condition is not None]",
                           'None) if condition is not None]')], OWN),
    ('X05-import-group-only', [("enclosing[1] if enclosing[0] == 'importgroup' else None) if condition is not None]",
                                'enclosing[1]) if condition is not None]')], UNPROVEN),
    ('X06-carried', [('return bool(proofs) and all(proofs)', 'return False')], CARRIED),
    ('X06-carried-chain', [('return bool(proofs) and all(proofs)', 'return False')], CHAINS),
    ('X07-carried-every', [('return bool(proofs) and all(proofs)', 'return bool(proofs) and any(proofs)')], CARRIED),
    ('X08-carried-exact', [(r"carried = re.fullmatch(r'\s*\$\(([A-Za-z_][\w.]*)\)\s*', raw)",
                            r"carried = re.match(r'\s*\$\(([A-Za-z_][\w.]*)\)', raw)")], CARRIED),
    ('X09-exists-absent', [('if not guard[1] and all(resolver.absent(label, substitution) for label in labels):', 'if False:')], OWN),
    ('X10-not-exists-present', [(PRESENT_GUARD, 'if False and all(resolver.present(label, substitution,')], OWN),
    ('X10-not-exists-present-chain', [(PRESENT_GUARD, 'if False and all(resolver.present(label, substitution,')], CHAINS),
    ('X11-every-absent', [('all(resolver.absent(label, substitution)', 'any(resolver.absent(label, substitution)')], UNPROVEN),
    ('X12-every-present', [('all(resolver.present(label, substitution,', 'any(resolver.present(label, substitution,')], UNPROVEN),
    ('X13-quote-span', [("""EXISTS_GUARD = re.compile(r'''\\s*(!\\s*)?Exists\\(\\s*(["'])([^"']*)\\2\\s*\\)\\s*''', re.I)""",
                         """EXISTS_GUARD = re.compile(r'''\\s*(!\\s*)?Exists\\(\\s*(["'])(.*?)\\2\\s*\\)\\s*''', re.I | re.S)""")], UNPROVEN),
    ('X14-excuse-disjunction', [("if any(match[1].lower() == 'or' for match in operators):\n        return []",
                                 'if False:\n        return []')], UNPROVEN),
    ('X15-unresolved-text', [("re.search(r'[$@%]\\(', item)", "re.search(r'[@%]\\(', item)")], UNPROVEN),
    ('X16-item-text', [("re.search(r'[$@%]\\(', item)", "re.search(r'[$%]\\(', item)")], UNPROVEN),
    ('X17-escape', [("return items[0] if len(items) == 1 and not re.search(r'%[0-9A-Fa-f]{2}', items[0]) else None",
                     'return items[0] if len(items) == 1 else None')], UNPROVEN),
    ('X18-conditional-only', [('(name in certain if name in properties else name in CONTEXT_PROPERTIES)',
                               '(True if name in properties else name in CONTEXT_PROPERTIES)')], UNPROVEN),
    ('X19-undefined-reference', [('(name in certain if name in properties else name in CONTEXT_PROPERTIES)',
                                  '(name in certain if name in properties else True)')], UNPROVEN),
    ('X20-target-defined', [('else name in CONTEXT_PROPERTIES) and name not in target_defined', 'else name in CONTEXT_PROPERTIES)')],
     UNPROVEN),
    ('X21-target-prescan', [('target_defined.update(local_name(item).lower()', 'set().update(local_name(item).lower()')], UNPROVEN),
    ('X22-conditional-incomplete', [('if not complete:\n                        certain.discard(name)',
                                     'if False:\n                        certain.discard(name)')], UNPROVEN),
    ('X23-unconditional-incomplete', [('(certain.add if complete else certain.discard)(name)', 'certain.add(name)')], UNPROVEN),
    ('X24-static-property-group', [("static = enclosing[0] == 'propertygroup' and not in_target", 'static = not in_target')], UNPROVEN),
    ('X24-static-property-group-carried', [("static = enclosing[0] == 'propertygroup' and not in_target", 'static = not in_target')],
     CARRIED),
    ('X25-static-target', [("static = enclosing[0] == 'propertygroup' and not in_target", "static = enclosing[0] == 'propertygroup'")],
     CARRIED),
    ('X26-definition-group-guard', [("or refuted([enclosing[1] or ''], current))", 'or False)')], CARRIED),
    ('X27-definition-base', [("refuted([attribute(element, 'Condition') or ''], path)", "refuted([attribute(element, 'Condition') or ''], current)")],
     BASES),
    ('X28-import-base', [('if refuted(conditions, current):', 'if refuted(conditions, path):')], BASES),
    ('X29-guard-hop', [('substitution = resolver.substitution(current)\n            for condition in conditions:',
                        'substitution = None\n            for condition in conditions:')], HOPS),
    ('X30-present-import-visited', [('for candidate in matches:\n                            visit(candidate, conditional)',
                                     'for candidate in ([] if excused(element, enclosing, raw, value) else matches):\n'
                                     '                            visit(candidate, conditional)')], NEVER),
    ('X31-alternative-retained', [('                if conditional:\n                    properties.setdefault(name, set()).update(possibilities)',
                                   '                if proof:\n                    pass\n                elif conditional:\n'
                                   '                    properties.setdefault(name, set()).update(possibilities)')], NEVER),
    ('X32-glob-not-present', [('"""Prove Exists() true: a committed regular blob or directory at this exact spelling."""\n'
                               "        if re.search(r'[*?]', label):\n            return False\n",
                               '"""Prove Exists() true: a committed regular blob or directory at this exact spelling."""\n')], UNPROVEN),
    ('X33-glob-not-absent', [('"""Prove Exists() false: no case-insensitive match in any tree a build could read there."""\n'
                              "        if re.search(r'[*?]', label):\n            return False\n",
                              '"""Prove Exists() false: no case-insensitive match in any tree a build could read there."""\n')], UNPROVEN),
    ('X34-nested-substitution-not-present', [("return (substitution.resolution == 'workspace' and label.startswith(",
                                              'return (label.startswith(')], HOPS),
    ('X35-present-hop', [("            return (substitution.resolution == 'workspace' and label.startswith(substitution.base + '/')",
                          "            if not label.startswith(substitution.base + '/'):\n                return self.present(label, None)\n"
                          "            return (substitution.resolution == 'workspace' and label.startswith(substitution.base + '/')")], HOPS),
    ('X36-absent-hop', [("            return label.startswith(substitution.base + '/') and substitution.tree.absent(label[len(substitution.base) + 1:])",
                         "            return (substitution.tree.absent(label[len(substitution.base) + 1:]) if label.startswith(substitution.base + '/')\n"
                         '                    else self.absent(label, None))')], HOPS),
    ('X37-nested-never-present', [('        if not self.escaping(label) or self.workspace is None:\n'
                                   '            return False  # Paths under a nested gitlink are absent from non-recursive checkouts.',
                                   '        if not self.escaping(label) and self.workspace is not None:\n'
                                   "            tree, inner, _ = self.locate(label, None, Refusal('unsafe-import-path', '', label))\n"
                                   '            return tree.present(inner)\n        if self.workspace is None:\n            return False')],
     UNPROVEN),
    ('X38-parent-tree-not-present', [('        if self.escaping(target) or root is None:\n'
                                      '            return False  # Above the parent root, a tree root itself, or outside every root.',
                                      '        if self.escaping(target):\n            return False\n'
                                      '        if root is None:\n            return self.workspace.parent.present(target)')], UNPROVEN),
    ('X39-present-exact-case', [('        entry = self.entries.get(inner)\n        return entry[0] in REGULAR',
                                 '        entry = next((value for key, value in self.entries.items() if key.lower() == inner.lower()), None)\n'
                                 '        return entry[0] in REGULAR')], UNPROVEN),
    ('X40-present-regular', [('return entry[0] in REGULAR if entry is not None else', 'return True if entry is not None else')], UNPROVEN),
    ('X41-present-directory', [('else inner in self.index()[0]', 'else False')], OWN),
    ('X42-absent-case', [('        lowered = inner.lower()\n', '        lowered = inner\n')], UNPROVEN),
    ('X43-absent-empty-root', [("return (bool(inner) and lowered != '.' and", "return (lowered != '.' and")], UNPROVEN),
    ('X44-absent-dot-root', [("return (bool(inner) and lowered != '.' and", 'return (bool(inner) and')], UNPROVEN),
    ('X45-absent-below-gitlink', [('                and not self.opaque(inner))', ')')], UNPROVEN),
    ('X46-absent-above-parent', [('        if self.escaping(target):\n            return False  # Above the parent root.\n', '')], UNPROVEN),
    ('X47-absent-nested-commit', [('            return tree.absent(inner)\n        if self.workspace is None:',
                                   '            return False\n        if self.workspace is None:')], OWN),
]

REVIEW = [
    ('R01-substituted-unresolved-import', [("elif substitution is not None:\n                        # A substituted file's unresolved import",
                                            "elif False:\n                        # A substituted file's unresolved import")],
     'test_nested_review_substituted_unresolved_import_is_refused_without_name_matching'),
    ('R02-submodule-sections', [("""require(re.fullmatch(r'submodule "[^"\\r\\n]+"', section) is not None, 'malformed-nested-declarations')""",
                                 'pass')], 'test_nested_review_nested_declarations_need_valid_submodule_sections'),
    ('R03-submodule-paths', [("path = safe_path(parser.get(section, 'path', fallback=''))\n            modules.setdefault(",
                              "path = parser.get(section, 'path', fallback='')\n            modules.setdefault(")],
     'test_nested_review_nested_declarations_need_valid_submodule_sections'),
    ('R04-missing-substituted-blob', [("raise CensusError(f'{substitution.resolution}-object-unavailable:{label}', target=label) from None",
                                       'raise')], 'test_nested_review_missing_substituted_blobs_name_their_requested_labels'),
    ('R05-closure-members', [('for path in sorted(paths | substituted)]', 'for path in sorted(paths)]')],
     'test_nested_review_closure_allowance_binds_cross_tree_members_by_label'),
    ('R06-closure-labels-compared', [("if (closure.get(source['path']) != source['sha256'] if closure is not None else",
                                      "if (source['path'] not in tree.entries or closure.get(source['path']) != source['sha256'] "
                                      'if closure is not None else')],
     'test_nested_review_closure_allowance_binds_cross_tree_members_by_label'),
    ('R07-closure-label-validation', [("(safe_label if 'sourcePrefix' in entry and entry.get('compilationClosure') is True else safe_path)"
                                       "(source['path'])", "safe_path(source['path'])")],
     'test_nested_review_closure_allowance_binds_cross_tree_members_by_label'),
    ('R08-closure-label-scope', [("(safe_label if 'sourcePrefix' in entry and entry.get('compilationClosure') is True else safe_path)"
                                  "(source['path'])", "safe_label(source['path'])")],
     'test_nested_review_closure_allowance_binds_cross_tree_members_by_label'),
    ('R09-context-free-validation', [('values, _, _, _ = project_metadata(tree, project, metadata_files(tree))',
                                      "values, _, _, _ = project_metadata(tree, project, metadata_files(tree), resolver=Resolver(Workspace("
                                      "workspace, Tree(workspace, git(workspace, 'rev-parse', 'HEAD')), declarations(Tree(workspace, "
                                      "git(workspace, 'rev-parse', 'HEAD')))), fixture['repository'], tree))")],
     'test_nested_review_amendment_fixture_validation_refuses_cross_tree_metadata'),
    ('R10-protocol-never', [("'-c', 'protocol.allow=never', ", '')], 'test_nested_review_git_reads_ignore_inherited_repository_state'),
    ('R11-no-lazy-fetch-variable', [("environment.update({'GIT_NO_LAZY_FETCH': '1', 'GIT_NO_REPLACE_OBJECTS': '1'})",
                                     "environment.update({'GIT_NO_REPLACE_OBJECTS': '1'})")],
     'test_nested_review_git_reads_ignore_inherited_repository_state'),
    ('R12-no-replace-objects', [("environment.update({'GIT_NO_LAZY_FETCH': '1', 'GIT_NO_REPLACE_OBJECTS': '1'})",
                                 "environment.update({'GIT_NO_LAZY_FETCH': '1'})")],
     'test_nested_review_git_reads_ignore_inherited_repository_state'),
    ('R13-repository-variables', [('environment = {key: value for key, value in os.environ.items() if key not in repository_variables()}',
                                   'environment = dict(os.environ)')], 'test_nested_review_git_reads_ignore_inherited_repository_state'),
    ('R14-malformed-text-label', [("raise CensusError(f'malformed-text:{label}') from None", "raise CensusError('malformed-text') from None")],
     'test_nested_review_invalid_substituted_text_names_its_label_and_keeps_provenance'),
    ('R15-refused-read-provenance', [('        self.reads[canonical(record)] = record\n        return raw', '        return raw')],
     'test_nested_review_invalid_substituted_text_names_its_label_and_keeps_provenance'),
    ('R16-allowance-error-target', [("**({'target': error.target} if isinstance(error, CensusError) and error.target else {})})", '})')],
     'test_nested_review_allowance_closure_refusal_carries_its_target'),
    ('R17-pin-commit-type', [("require(git(location, 'cat-file', '-t', commit) == 'commit', 'reference-pin-not-commit')", 'pass')],
     'test_nested_review_linked_root_checkout_and_tree_pin_refuse_cross_tree_reads'),
    ('R18-linked-root', [("require(location.is_dir() and not any(p.is_symlink() for p in [location, *list(location.parents)"
                          "[:len(PurePosixPath(repository).parts) - 1]]), 'reference-root-unavailable-or-linked')",
                          "require(location.is_dir(), 'reference-root-unavailable-or-linked')")],
     'test_nested_review_linked_root_checkout_and_tree_pin_refuse_cross_tree_reads'),
    ('R19-scp-host-case', [("return (match[1] or '') + match[2].lower() + ':' + match[3]", "return (match[1] or '') + match[2] + ':' + match[3]")],
     'test_nested_review_scp_identity_matches_and_drive_letters_keep_case'),
    ('R20-drive-letter', [('if match and len(match[2]) > 1:', 'if match:')], 'test_nested_review_scp_identity_matches_and_drive_letters_keep_case'),
    ('R21-scp-userinfo', [("return (match[1] or '') + match[2].lower() + ':' + match[3]", "return match[2].lower() + ':' + match[3]")],
     'test_nested_review_scp_identity_matches_and_drive_letters_keep_case'),
]

SECOND = [
    ('S01-import-literal-item', [('if item is None and value.strip():', 'if False:')],
     'test_guard_review_escaped_import_values_are_refused_with_their_label'),
    ('S02-import-list', [('return items[0] if len(items) == 1 and not', 'return items[0] if items and not')],
     'test_guard_review_import_lists_are_refused_and_values_trimmed'),
    ('S03-item-trim', [("items = [item.strip() for item in value.split(';') if item.strip()]",
                        "items = [item for item in value.split(';') if item.strip()]")],
     'test_guard_review_import_lists_are_refused_and_values_trimmed'),
    ('S04-exact-rule-items', [('alternatives = [literal_item(item) for item in expanded_values(argument, properties, current, path, required=False)]',
                               'alternatives = expanded_values(argument, properties, current, path, required=False)')], EXCLUDED),
    ('S05-guard-items', [('alternatives = [literal_item(item) for item in expanded_values(guard[3], properties, current, path, required=False)]',
                          'alternatives = expanded_values(guard[3], properties, current, path, required=False)')], OWN),
    ('S06-exact-rule-parser', [('exists = EXISTS_GUARD.fullmatch(conjunct)',
                                "exists = re.fullmatch(r'''\\s*(!\\s*)?Exists\\(\\s*([\"'])(.*?)\\2\\s*\\)\\s*''', conjunct, re.I | re.S)")],
     'test_guard_review_exact_exists_rule_arguments_cannot_span_quotes'),
    ('S07-sdk-pair', [("identities.extend(explicit['Sdk.props'] & explicit['Sdk.targets'])",
                       "identities.extend(explicit['Sdk.props'] | explicit['Sdk.targets'])")],
     'test_explicit_sdk_imports_preserve_apphost_classification_without_granting_other_imports_authority'),
    ('S08-allow-protocol', [(ALLOW, '')], 'test_nested_review_git_reads_ignore_inherited_repository_state'),
    ('S09-git-unavailable', [("require(result.returncode == 0, 'git-unavailable')", "require(result.returncode == 0, 'git-object-unavailable')")],
     'test_guard_review_unavailable_git_is_reported_as_git_unavailable'),
    ('S10-link-prefix', [("if entry[0] in ('160000', '120000'):", "if entry[0] == '160000':")],
     'test_guard_review_link_traversing_targets_are_never_absent'),
    ('S11-local-link', [("Refusal('unavailable-local-import', current, label).require(not resolver.tree.opaque(label))", 'pass')],
     'test_guard_review_link_traversing_targets_are_never_absent'),
    ('S12-directory-only', [('        if directory:\n            return inner in self.index()[0]', '        if False:\n            return inner in self.index()[0]')],
     UNPROVEN),
    ('S13-trailing-separator', [("item.endswith(('/', '\\\\')))", 'False)')], UNPROVEN),
    ('S14-enclosing-group-base', [("refuted([enclosing[1] or ''], current)", "refuted([enclosing[1] or ''], path)")], BASES),
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
    parser.add_argument('--new-only', action='store_true')
    args = parser.parse_args()
    controls = [] if args.new_only else prior_controls()
    controls += [(name, replacements, test, 'new') for name, replacements, test in EXCUSE + REVIEW + SECOND]
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
                          newCount=sum(r['origin'] == 'new' for r in results),
                          origins={origin: sum(r['origin'] == origin for r in results)
                                   for origin in ('retained', 'adapted', 'nested', 'excuse-adapted', 'new')},
                          adaptations={name: reason for name, (_, _, reason) in sorted(ADAPTED.items())}, controls=results), indent=2))


if __name__ == '__main__':
    main()
