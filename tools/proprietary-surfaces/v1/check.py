#!/usr/bin/env python3
"""Census proprietary tool surfaces in committed root-declared reference trees."""
from __future__ import annotations

import argparse
import configparser
from datetime import date, datetime, timezone
import hashlib
import fnmatch
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shlex
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from evidence_redaction import sanitized

SCHEMA = 'mcpcli-proprietary-surface-census/v1'
PROJECT = re.compile(r'\.(?:cs|fs|vb)proj\Z', re.I)
IDENTITY = re.compile(r'(?:^|[./_-])(?:mcp|cli)(?:[./_-]|$)', re.I)
REGISTRATION = re.compile(r'\b(?:Add\w*Mcp\w*|Map\w*Mcp\w*|With(?:StdioServer|Http)Transport|McpServerTool\w*|McpServerResource\w*|McpServerPrompt\w*)\s*(?:\(|\]|<)')
COMMAND = re.compile(r'\bSystem\.CommandLine\b')
SHA = re.compile(r'[0-9a-f]{40}\Z')
HASH = re.compile(r'[0-9a-f]{64}\Z')


class CensusError(ValueError):
    """A coverage or metadata failure, safe to retain without source snippets."""


def require(condition, message):
    if not condition:
        raise CensusError(message)


def safe_path(value):
    require(isinstance(value, str) and bool(value) and not re.search(r'[\x00-\x1f\x7f\\]', value), 'unsafe-path')
    path = PurePosixPath(value)
    require(not path.is_absolute() and all(part not in ('', '.', '..') for part in value.split('/')), 'unsafe-path')
    return value


def nonblank(value):
    return isinstance(value, str) and bool(value.strip()) and not re.search(r'[\x00-\x1f\x7f]', value)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(raw, label):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f'duplicate-json-key:{label}')
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=unique)
    except (ValueError, UnicodeError) as error:
        if isinstance(error, CensusError):
            raise
        raise CensusError(f'malformed-json:{label}') from None


def git(repo, *args, raw=False, input=None):
    result = subprocess.run(['git', '-c', 'core.quotePath=false', '-C', str(repo), *args],
                            input=input, capture_output=True, check=False)
    require(result.returncode == 0, 'git-object-unavailable')
    return result.stdout if raw else result.stdout.decode('utf-8', errors='strict').strip()


class Tree:
    """Read only committed blobs, never files in an inspected worktree."""

    def __init__(self, repo, revision):
        self.repo, self.revision = Path(repo), revision
        self.entries, self.cache = {}, {}
        raw = git(repo, 'ls-tree', '-rz', '--full-tree', revision, raw=True)
        for row in raw.split(b'\0'):
            if not row:
                continue
            head, path = row.split(b'\t', 1)
            mode, kind, oid = head.decode().split()
            try:
                path = path.decode('utf-8')
            except UnicodeError:
                raise CensusError('unsafe-path') from None
            safe_path(path)
            self.entries[path] = (mode, kind, oid)

    def blob(self, path):
        require(path in self.entries and self.entries[path][0] in ('100644', '100755'), f'regular-committed-blob-required:{path}')
        if path not in self.cache:
            self.cache[path] = git(self.repo, 'cat-file', 'blob', self.entries[path][2], raw=True)
        return self.cache[path]

    def text(self, path):
        try:
            raw = self.blob(path)
            return raw.decode('utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig')
        except UnicodeError:
            raise CensusError(f'malformed-text:{path}') from None

    def preload(self, paths):
        paths = [p for p in paths if self.entries[p][0] in ('100644', '100755')]
        if not paths:
            return
        output = git(self.repo, 'cat-file', '--batch', raw=True,
                     input=('\n'.join(self.entries[p][2] for p in paths) + '\n').encode())
        offset = 0
        for path in paths:
            end = output.index(b'\n', offset)
            header = output[offset:end].split()
            require(len(header) == 3 and header[1] == b'blob', 'git-object-unavailable')
            size = int(header[2])
            offset = end + 1
            self.cache[path] = output[offset:offset + size]
            offset += size + 1


def declarations(parent):
    require('.gitmodules' in parent.entries, 'root-declarations-missing')
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    try:
        parser.read_string(parent.text('.gitmodules'))
    except configparser.Error:
        raise CensusError('malformed-root-declarations') from None
    roots = {}
    for section in parser.sections():
        require(re.fullmatch(r'submodule "[^"\r\n]+"', section) is not None, 'malformed-root-declarations')
        path = safe_path(parser.get(section, 'path', fallback=''))
        require(path not in roots and nonblank(parser.get(section, 'url', fallback='')), 'malformed-root-declarations')
        entry = parent.entries.get(path)
        require(entry is not None and entry[:2] == ('160000', 'commit'), f'root-gitlink-missing:{path}')
        require(not any(path.startswith(other + '/') or other.startswith(path + '/') for other in roots), 'overlapping-root-declarations')
        roots[path] = entry[2]
    require(bool(roots), 'root-declarations-empty')
    gitlinks = {p for p, entry in parent.entries.items() if entry[0] == '160000'}
    require(gitlinks == set(roots), 'undeclared-root-gitlink')
    return dict(sorted(roots.items()))


def descriptor(value):
    require(isinstance(value, dict) and set(value) == {'repository', 'path', 'kind', 'identity'}, 'invalid-surface-binding')
    safe_path(value['repository'])
    safe_path(value['path'])
    require(value['kind'] in ('project', 'publication', 'configuration', 'source'), 'invalid-surface-kind')
    require(nonblank(value['identity']), 'invalid-surface-identity')
    return tuple(value[k] for k in ('repository', 'path', 'kind', 'identity'))


def validate_allowance(entry, roots):
    require(isinstance(entry, dict), 'invalid-allowance')
    descriptor(entry.get('surface'))
    require(entry['surface']['repository'] in roots, 'allowance-root-unapproved')
    require(all(nonblank(entry.get(k)) for k in ('row', 'classification', 'owner', 'reason')), 'invalid-allowance')
    require(isinstance(entry.get('signals'), list) and entry['signals'] and all(nonblank(s) for s in entry['signals']), 'invalid-allowance-signals')
    require(len(entry['signals']) == len(set(entry['signals'])), 'duplicate-allowance-signal')
    if 'sourcePrefix' in entry:
        prefix = safe_path(entry['sourcePrefix'])
        require(prefix == str(PurePosixPath(entry['surface']['path']).parent)
                and isinstance(entry.get('sources'), list) and bool(entry['sources']), 'invalid-source-closure')
        paths = [source.get('path') for source in entry['sources'] if isinstance(source, dict)]
        require(len(paths) == len(entry['sources']) and len(set(paths)) == len(paths)
                and all(isinstance(path, str) and (entry.get('compilationClosure') is True or path.startswith(prefix + '/')) for path in paths), 'invalid-source-closure')
    for source in entry.get('sources', []):
        require(isinstance(source, dict) and set(source) == {'path', 'sha256'}, 'invalid-source-binding')
        safe_path(source['path'])
        require(HASH.fullmatch(source['sha256']) is not None, 'invalid-source-binding')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def validate_approval_evidence(workspace, amendment, receipt):
    """Require an affirmative receipt bound to the exact mutation scope."""
    require(isinstance(receipt, dict) and receipt.get('decision') == 'approved'
            and receipt.get('owner') == amendment['approval']['owner'], 'amendment-evidence-not-approved')
    operations = ('addAllowances', 'removeAllowances', 'addExceptions', 'removeExceptions', 'addExclusions')
    if receipt.get('schema') == 'mcpcli-census-amendment-approval/v2':
        authorization = receipt.get('authorization')
        require(isinstance(authorization, dict) and set(authorization) == set(operations)
                and canonical(authorization) == canonical({key: amendment.get(key, []) for key in operations}), 'amendment-authorization-scope-mismatch')
        authorities = receipt.get('authority')
        require(isinstance(authorities, list) and bool(authorities), 'amendment-authority-missing')
        for binding in authorities:
            require(isinstance(binding, dict) and set(binding) == {'path', 'sha256'}, 'invalid-amendment-authority')
            safe_path(binding['path'])
            raw = (workspace / binding['path']).read_bytes()
            require(HASH.fullmatch(binding['sha256']) is not None and digest(raw) == binding['sha256'], 'amendment-authority-mismatch')
            authority = json_bytes(raw, binding['path'])
            require(isinstance(authority, dict) and authority.get('decision') == 'approved'
                    and (isinstance(authority.get('source_revisions'), dict)
                         or authority.get('schema') in ('mcpcli-census-amendment-approval/v1', 'mcpcli-census-amendment-approval/v2')),
                    'invalid-amendment-authority')
        return
    # The original receipt is retained byte-for-byte. Its historical format
    # authorizes only the named fixture and its exact inspected directory bytes.
    require(receipt.get('schema') == 'mcpcli-census-amendment-approval/v1'
            and isinstance(receipt.get('fixtures'), list) and bool(receipt['fixtures'])
            and all(not amendment.get(key, []) for key in operations[1:]), 'amendment-authorization-scope-mismatch')
    for entry in amendment['addAllowances']:
        surface = entry.get('surface', {})
        fixtures = [fixture for fixture in receipt['fixtures'] if fixture.get('repository') == surface.get('repository')
                    and fixture.get('project') == surface.get('path')]
        require(len(fixtures) == 1, 'amendment-authorization-scope-mismatch')
        fixture = fixtures[0]
        require(SHA.fullmatch(fixture.get('gitlink', '')) is not None, 'amendment-authorization-scope-mismatch')
        project = safe_path(fixture['project'])
        closure = fixture.get('sourceClosure', {})
        require(entry.get('sourcePrefix') == closure.get('prefix')
                and canonical(entry.get('sources')) == canonical(closure.get('sources'))
                and 'compilationClosure' not in entry, 'amendment-authorization-scope-mismatch')
        tree = Tree(workspace / safe_path(fixture['repository']), fixture['gitlink'])
        values, _, _, _ = project_metadata(tree, project, {p for p in tree.entries if p.endswith(('.props', '.targets'))})
        authorized = {('project', PurePosixPath(project).stem)}
        for name, prefix in [('PackageId', 'package:'), ('ToolCommandName', 'tool:'), ('ContainerRepository', 'container:')]:
            authorized.update(('publication', prefix + value) for value in values.get(name, set()))
        require((surface.get('kind'), surface.get('identity')) in authorized, 'amendment-authorization-scope-mismatch')


def load_policy(workspace, parent, baseline_path, index_path, today):
    baseline_raw = baseline_path.read_bytes()
    policy = json_bytes(baseline_raw, 'baseline')
    require(isinstance(policy, dict) and set(policy) == {'schema', 'version', 'roots', 'allowances', 'exclusions', 'exceptions', 'provenance', 'toolIdentities'} and policy.get('schema') == SCHEMA and policy.get('version') == '1.0.0', 'invalid-baseline-version')
    for field in ('roots', 'allowances', 'exclusions', 'exceptions', 'provenance', 'toolIdentities'):
        require(isinstance(policy.get(field), list), f'invalid-baseline-{field}')
    roots = {}
    for row in policy['roots']:
        require(isinstance(row, dict) and nonblank(row.get('classification')) and nonblank(row.get('owner')), 'invalid-root-provenance')
        path = safe_path(row.get('repository'))
        require(path not in roots and SHA.fullmatch(row.get('gitlink', '')) is not None, 'invalid-root-provenance')
        roots[path] = row
    require(bool(roots), 'invalid-root-provenance')
    require(bool(policy['provenance']), 'missing-source-provenance')
    for source in policy['provenance']:
        require(isinstance(source, dict) and set(source) == {'path', 'sha256'}, 'invalid-source-provenance')
        safe_path(source['path'])
        require(HASH.fullmatch(source['sha256']) is not None and digest(parent.blob(source['path'])) == source['sha256'], 'source-provenance-mismatch')
    amendments = json_bytes(index_path.read_bytes(), 'amendment-index')
    require(isinstance(amendments, list), 'invalid-amendment-index')
    previous, version = digest(baseline_raw), policy['version']
    applied = []
    for item in amendments:
        require(isinstance(item, dict) and set(item) == {'path', 'sha256'}, 'invalid-amendment-index')
        safe_path(item['path'])
        require(HASH.fullmatch(item['sha256']) is not None, 'invalid-amendment-hash')
        file = baseline_path.parent / item['path']
        require(not file.is_symlink() and file.is_file(), 'amendment-file-missing')
        raw = file.read_bytes()
        require(digest(raw) == item['sha256'], 'amendment-hash-mismatch')
        amendment = json_bytes(raw, item['path'])
        require(isinstance(amendment, dict) and set(amendment) in ({
            'schema', 'fromVersion', 'toVersion', 'previousSha256', 'approval', 'addAllowances', 'removeAllowances', 'addExceptions', 'removeExceptions'}, {
            'schema', 'fromVersion', 'toVersion', 'previousSha256', 'approval', 'addAllowances', 'removeAllowances', 'addExceptions', 'removeExceptions', 'addExclusions'}), 'invalid-amendment')
        target = amendment['toVersion']
        require(amendment['schema'] == SCHEMA and amendment['fromVersion'] == version
                and re.fullmatch(r'1\.0\.[1-9][0-9]*', str(target)) is not None
                and int(target.split('.')[-1]) == int(version.split('.')[-1]) + 1
                and amendment['previousSha256'] == previous, 'amendment-chain-mismatch')
        approval = amendment['approval']
        require(isinstance(approval, dict) and all(nonblank(approval.get(k)) for k in ('owner', 'reason', 'decision', 'date'))
                and approval['decision'] in ('approved', 'approved option A'), 'invalid-amendment-approval')
        try:
            require(date.fromisoformat(approval['date']).isoformat() == approval['date'], 'invalid-amendment-approval')
        except ValueError:
            raise CensusError('invalid-amendment-approval') from None
        binding = approval.get('evidence')
        require(isinstance(binding, dict) and set(binding) == {'path', 'sha256'}, 'invalid-amendment-approval')
        safe_path(binding['path'])
        evidence = workspace / binding['path']
        require(not evidence.is_symlink() and evidence.is_file()
                and HASH.fullmatch(binding['sha256']) is not None
                and digest(evidence.read_bytes()) == binding['sha256'], 'amendment-approval-mismatch')
        require(all(isinstance(amendment[k], list) for k in ('addAllowances', 'removeAllowances', 'addExceptions', 'removeExceptions')), 'invalid-amendment')
        validate_approval_evidence(workspace, amendment, json_bytes(evidence.read_bytes(), binding['path']))
        for removed in amendment['removeAllowances']:
            key = descriptor(removed)
            matches = [a for a in policy['allowances'] if descriptor(a.get('surface')) == key]
            require(len(matches) == 1, 'amendment-removal-not-exact')
            policy['allowances'].remove(matches[0])
        for removed in amendment['removeExceptions']:
            key = descriptor(removed)
            matches = [e for e in policy['exceptions'] if descriptor(e.get('surface')) == key]
            require(len(matches) == 1, 'amendment-exception-removal-not-exact')
            policy['exceptions'].remove(matches[0])
        policy['allowances'].extend(amendment['addAllowances'])
        policy['exceptions'].extend(amendment['addExceptions'])
        require(isinstance(amendment.get('addExclusions', []), list), 'invalid-amendment')
        policy['exclusions'].extend(amendment.get('addExclusions', []))
        applied.append({'path': item['path'], 'sha256': item['sha256'], 'version': target})
        previous, version = item['sha256'], target
    tool_names = set()
    for tool in policy['toolIdentities']:
        require(isinstance(tool, dict) and set(tool) == {'identity', 'classification', 'row', 'owner', 'reason'}
                and all(nonblank(tool[k]) for k in tool), 'invalid-tool-identity')
        require(tool['identity'].lower() not in tool_names, 'duplicate-tool-identity')
        tool_names.add(tool['identity'].lower())
    allowed = {}
    for entry in policy['allowances']:
        validate_allowance(entry, roots)
        key = descriptor(entry['surface'])
        require(key not in allowed, 'duplicate-allowance')
        allowed[key] = entry
    exclusions = []
    for item in policy['exclusions']:
        require(isinstance(item, dict) and set(item) in ({'repository', 'prefix', 'row', 'classification', 'owner', 'reason'},
                {'repository', 'prefix', 'row', 'classification', 'owner', 'reason', 'scope', 'sha256'},
                {'repository', 'prefix', 'row', 'classification', 'owner', 'reason', 'scope', 'sha256', 'additionalSha256'}), 'invalid-exclusion')
        if 'scope' in item:
            require(item['scope'] == 'file' and HASH.fullmatch(item['sha256']) is not None, 'invalid-exclusion')
            extra_hashes = item.get('additionalSha256', [])
            require(isinstance(extra_hashes, list) and all(isinstance(value, str) and HASH.fullmatch(value) for value in extra_hashes)
                    and len(set([item['sha256'], *extra_hashes])) == len(extra_hashes) + 1, 'invalid-exclusion')
        require(item['repository'] in roots and all(nonblank(item[k]) for k in ('row', 'classification', 'owner', 'reason')), 'invalid-exclusion')
        safe_path(item['prefix'])
        require(item not in exclusions, 'duplicate-exclusion')
        exclusions.append(item)
    exceptions = {}
    for entry in policy['exceptions']:
        require(isinstance(entry, dict) and set(entry) == {'surface', 'owner', 'reason', 'expires'}, 'invalid-exception')
        key = descriptor(entry['surface'])
        require(key[0] in roots and key not in exceptions and nonblank(entry['owner']) and nonblank(entry['reason']), 'invalid-exception')
        try:
            expiry = date.fromisoformat(entry['expires'])
            require(expiry.isoformat() == entry['expires'], 'invalid-exception-expiry')
        except (TypeError, ValueError):
            raise CensusError('invalid-exception-expiry') from None
        require(today <= expiry, 'expired-exception')
        exceptions[key] = entry
    return policy, roots, allowed, exclusions, exceptions, {'baselineSha256': digest(baseline_raw), 'version': version, 'amendments': applied}


def xml(text, path):
    require('<!DOCTYPE' not in text.upper() and '<!ENTITY' not in text.upper(), f'unsafe-xml:{path}')
    try:
        return ET.fromstring(text)
    except ET.ParseError:
        raise CensusError(f'malformed-project-metadata:{path}') from None


def local_name(element):
    return element.tag.rsplit('}', 1)[-1]


def resolve_path(base, value):
    require(nonblank(value) and not re.search(r'[\x00-\x1f\x7f]', value), 'unsafe-metadata-path')
    value = value.replace('\\', '/')
    require(not value.startswith('/') and re.match(r'^[A-Za-z]:', value) is None, 'unsafe-metadata-path')
    result = posixpath.normpath(posixpath.join(str(PurePosixPath(base).parent), value))
    safe_path(result)
    return result


PROPERTY_NAMES = {name.lower(): name for name in (
    'OutputType', 'PackAsTool', 'ToolCommandName', 'PackageId', 'AssemblyName',
    'ContainerRepository')}


def attribute(element, name):
    return next((value for key, value in element.attrib.items() if key.lower() == name.lower()), None)


def expand_msbuild(value, properties, current, project, *, required=True):
    """Expand local/context properties without invoking an MSBuild evaluator."""
    context = dict(properties)
    context.update({
        'msbuildprojectname': PurePosixPath(project).stem,
        'msbuildprojectdirectory': '@repo/' + str(PurePosixPath(project).parent) + '/',
        'msbuildprojectfullpath': '@repo/' + project,
        'msbuildprojectextension': PurePosixPath(project).suffix,
        'msbuildthisfiledirectory': '@repo/' + (str(PurePosixPath(current).parent) + '/').removeprefix('./'),
        'msbuildthisfilefullpath': '@repo/' + current,
        'msbuildthisfilename': PurePosixPath(current).stem,
    })
    def substitute(text, seen):
        def replace(match):
            key = match[1].lower()
            if key not in context or key in seen:
                return match[0]
            return substitute(context[key], seen | {key})
        return re.sub(r'\$\(([A-Za-z_][\w.]*)\)', replace, text)
    value = substitute(value, set())
    # NormalizePath with literal arguments is path spelling, never invocation
    # of arbitrary property-function code from the inspected repository.
    def normalize(match):
        arguments = re.findall(r"'([^']*)'", match[1])
        remainder = re.sub(r"'[^']*'", '', match[1]).replace(',', '').strip()
        return posixpath.normpath(posixpath.join(*arguments)) if arguments and not remainder else match[0]
    value = re.sub(r"\$\(\[MSBuild\]::NormalizePath\((.*?)\)\)", normalize, value, flags=re.I)
    value = re.sub(r"\$\(\[System\.IO\.Path\]::GetFullPath\('([^']*)'\)\)",
                   lambda match: posixpath.normpath(match[1]), value, flags=re.I)
    if required:
        require('$(' not in value, f'unresolved-classification-metadata:{current}')
    return value


def metadata_path(current, raw, expanded):
    if expanded.startswith('@repo/'):
        target = posixpath.normpath(expanded.removeprefix('@repo/').replace('\\', '/'))
        safe_path(target)
        return target
    return resolve_path(current, expanded)


def project_metadata(tree, path, metadata_paths):
    """Conservatively retain conditional values and committed local imports."""
    documents, visited, values, references, compile_items = [], set(), {}, [], []
    properties = {'assemblyname': PurePosixPath(path).stem, 'packageid': PurePosixPath(path).stem}
    pending_values = []
    initial = []
    for ancestor in reversed(list(PurePosixPath(path).parents)):
        for filename in ('Directory.Build.props', 'Directory.Build.targets'):
            candidate = (ancestor / filename).as_posix()
            if candidate in metadata_paths:
                initial.append(candidate)
    initial.append(path)

    def visit(current):
        if current in visited:
            return
        visited.add(current)
        document = xml(tree.text(current), current)
        documents.append(current)
        for element in document.iter():
            name = local_name(element).lower()
            text = (element.text or '').strip()
            if text and not list(element):
                expanded = expand_msbuild(text, properties, current, path, required=False)
                if name in PROPERTY_NAMES:
                    pending_values.append((PROPERTY_NAMES[name], expanded, current))
                properties[name] = expanded
            if name in ('packagereference', 'projectreference'):
                value = attribute(element, 'Include') or attribute(element, 'Update') or ''
                references.append(('PackageReference' if name == 'packagereference' else 'ProjectReference', value, current))
            if name == 'compile' and attribute(element, 'Include'):
                compile_items.append((attribute(element, 'Include'), current))
            if name == 'import':
                raw = attribute(element, 'Project') or ''
                require(bool(raw), f'malformed-project-metadata:{current}')
                value = expand_msbuild(raw, properties, current, path, required=False)
                if '$(' not in value:
                    # Imports outside this repository belong to the permitted
                    # SDK/sibling boundary; no outside object is opened.
                    relative = (posixpath.normpath(value.removeprefix('@repo/').replace('\\', '/')) if value.startswith('@repo/')
                                else posixpath.normpath(posixpath.join(str(PurePosixPath(current).parent), value.replace('\\', '/'))))
                    if relative == '..' or relative.startswith('../'):
                        continue
                    target = metadata_path(current, raw, value)
                    matches = [candidate for candidate in metadata_paths if fnmatch.fnmatchcase(candidate, target)]
                    for candidate in sorted(matches):
                        visit(candidate)
                else:
                    # Property functions are never evaluated. Literal filenames
                    # inside them still identify committed local metadata.
                    names = set(re.findall(r'[A-Za-z0-9_.-]+\.(?:props|targets)', value, re.I))
                    for candidate in sorted(metadata_paths):
                        if PurePosixPath(candidate).name in names and PurePosixPath(candidate).name not in ('Directory.Build.props', 'Directory.Build.targets'):
                            visit(candidate)
    for current in initial:
        visit(current)
    for name, value, current in pending_values:
        values.setdefault(name, set()).add(expand_msbuild(value, properties, current, path))
    expanded_references = []
    for name, value, current in references:
        expanded = expand_msbuild(value, properties, current, path, required=False)
        # An unresolved directory does not obscure a literal project identity.
        identity = expanded.replace('\\', '/').rsplit('/', 1)[-1]
        literal = re.search(r"'([A-Za-z0-9_.-]+\.(?:cs|fs|vb)proj)'\)\)\Z", expanded, re.I)
        if '$(' in expanded and name == 'ProjectReference' and literal and re.match(r'\$\(\[MSBuild\]::NormalizePath\(', expanded, re.I):
            expanded = identity = literal[1]
        require('$(' not in expanded or name == 'ProjectReference' and '$(' not in identity
                and PROJECT.search(identity) is not None, f'unresolved-classification-metadata:{current}')
        expanded_references.append((name, expanded, current))
    references = expanded_references
    linked = set()
    for raw, current in compile_items:
        expanded = expand_msbuild(raw, properties, current, path)
        for value in expanded.split(';'):
            relative = (posixpath.normpath(value.removeprefix('@repo/').replace('\\', '/')) if value.startswith('@repo/')
                        else posixpath.normpath(posixpath.join(str(PurePosixPath(current).parent), value.replace('\\', '/'))))
            if relative == '..' or relative.startswith('../'):
                continue
            target = metadata_path(current, raw, value)
            linked.update(candidate for candidate in tree.entries
                          if fnmatch.fnmatchcase(candidate, target) and tree.entries[candidate][0] != '160000')
    return values, references, documents, linked


def compilation_closure(tree, project):
    """Bind fixture files, inherited/imported metadata and linked local sources."""
    metadata_paths = {path for path, entry in tree.entries.items()
                      if entry[0] != '160000' and path.endswith(('.props', '.targets'))}
    _, _, documents, linked = project_metadata(tree, project, metadata_paths)
    prefix = str(PurePosixPath(project).parent) + '/'
    paths = {path for path in tree.entries if path.startswith(prefix)} | set(documents) | linked
    return [{'path': path, 'sha256': digest(tree.blob(path))} for path in sorted(paths)]


def scan_tree(tree, repository, exclusions):
    excluded = [e for e in exclusions if e['repository'] == repository]
    def omitted(path):
        for entry in excluded:
            if path == entry['prefix'] or entry.get('scope') != 'file' and path.startswith(entry['prefix'] + '/'):
                if entry.get('scope') == 'file':
                    require(digest(tree.blob(path)) in [entry['sha256'], *entry.get('additionalSha256', [])], f'excluded-fixture-source-drift:{path}')
                return True
        return False
    paths = [p for p, entry in tree.entries.items() if entry[0] != '160000' and not omitted(p)]
    interesting = [p for p in paths if PROJECT.search(p) or p.endswith(('.props', '.targets', '.cs', '.fs', '.vb', '.json', '.toml', '.yml', '.yaml', '.ps1', '.sh', '.cmd', '.bat')) or PurePosixPath(p).name.startswith('Dockerfile')]
    tree.preload(interesting)
    candidates, projects, identities = {}, {}, {}

    def add(path, kind, identity, signal, source=None):
        safe_path(path)
        require(nonblank(identity), 'invalid-surface-identity')
        key = (repository, path, kind, identity)
        candidate = candidates.setdefault(key, {'surface': dict(zip(('repository', 'path', 'kind', 'identity'), key)), 'signals': set(), 'sources': set()})
        candidate['signals'].add(signal)
        candidate['sources'].add(source or path)

    for path in sorted(p for p in paths if PROJECT.search(p)):
        values, references, documents, linked = project_metadata(tree, path, {p for p in paths if p.endswith(('.props', '.targets'))})
        text = tree.text(path)
        project_id = PurePosixPath(path).stem
        signals = set()
        if IDENTITY.search(project_id):
            signals.add('project-identity')
        for prop in ('PackageId', 'AssemblyName'):
            if any(IDENTITY.search(value) for value in values.get(prop, set())):
                signals.add('package-identity')
        if any(value.lower() == 'true' for value in values.get('PackAsTool', set())):
            signals.add('packed-tool')
        if values.get('ToolCommandName'):
            signals.add('tool-command')
        if any(IDENTITY.search(value) for value in values.get('ContainerRepository', set())):
            signals.add('container-identity')
        executable = any(value.lower() in ('exe', 'winexe') for value in values.get('OutputType', set()))
        web = 'Microsoft.NET.Sdk.Web' in text
        apphost = 'Aspire.AppHost.Sdk' in text
        if executable and not web and not apphost or (web and not path.startswith('src/')):
            signals.add('executable-project')
        for kind, value, source in references:
            if kind == 'PackageReference' and value.lower() == 'system.commandline':
                signals.add('command-line-dependency')
            if kind == 'PackageReference' and (re.search(r'ModelContextProtocol', value, re.I) or IDENTITY.search(value)):
                signals.add('mcp-or-cli-dependency')
            elif kind == 'ProjectReference' and IDENTITY.search(PurePosixPath(value.replace('\\', '/')).stem):
                signals.add('mcp-or-cli-dependency')
        projects[path] = {'signals': signals, 'values': values, 'documents': documents, 'linked': linked}
        for identity in {project_id, *values.get('PackageId', set()), *values.get('ToolCommandName', set()), *values.get('ContainerRepository', set())}:
            if '$(' not in identity:
                identities.setdefault(identity.lower(), set()).add(path)
        for signal in signals:
            add(path, 'project', project_id, signal)

    consumed = {document for metadata in projects.values() for document in metadata['documents']}
    for path in paths:
        if path.endswith(('.props', '.targets')) and path not in consumed:
            document = xml(tree.text(path), path)
            for element in document.iter():
                name, value = local_name(element).lower(), (element.text or '').strip()
                reference = attribute(element, 'Include') or attribute(element, 'Update') or ''
                if (name == 'outputtype' and value.lower() in ('exe', 'winexe')
                        or name == 'packastool' and value.lower() == 'true'
                        or name == 'toolcommandname' and value
                        or name == 'containerrepository' and IDENTITY.search(value)
                        or name == 'packagereference' and (reference.lower() == 'system.commandline'
                            or re.search(r'ModelContextProtocol', reference, re.I) or IDENTITY.search(reference))
                        or name == 'projectreference' and IDENTITY.search(PurePosixPath(reference.replace('\\', '/')).stem)):
                    add(path, 'source', path, 'unresolved-tool-metadata')

    # Source registrations belong to the nearest enclosing project(s). Linked
    # Compile items are also inspected; a source without a project is a candidate.
    def associated(path):
        directories = [str(PurePosixPath(project).parent) for project in projects
                       if path.startswith(str(PurePosixPath(project).parent) + '/')]
        if not directories:
            return []
        nearest = max(directories, key=len)
        return [p for p in projects if str(PurePosixPath(p).parent) == nearest]

    source_paths = [p for p in paths if p.endswith(('.cs', '.fs', '.vb'))]
    for path in source_paths:
        text = tree.text(path)
        signals = []
        if REGISTRATION.search(text):
            signals.append('mcp-registration')
        if COMMAND.search(text):
            signals.append('command-line-source')
        for signal in signals:
            owners = associated(path)
            if owners:
                for owner in owners:
                    add(owner, 'project', PurePosixPath(owner).stem, signal, path)
                    projects[owner]['signals'].add(signal)
            else:
                add(path, 'source', path, signal)

    # Linked Compile items, including committed glob matches, belong to
    # their declaring project even when the source is outside its directory.
    for project, metadata in projects.items():
        for target in metadata['linked']:
            text = tree.text(target)
            for signal, pattern in [('mcp-registration', REGISTRATION), ('command-line-source', COMMAND)]:
                if pattern.search(text):
                    add(project, 'project', PurePosixPath(project).stem, signal, target)
                    metadata['signals'].add(signal)

    # Publishing names are separate exact identities: an approved project is
    # never authority to rename its package, executable command or container.
    for project, metadata in projects.items():
        if metadata['signals']:
            for property_name, prefix, signal in [('PackageId', 'package:', 'package-metadata'),
                    ('ToolCommandName', 'tool:', 'tool-metadata'), ('ContainerRepository', 'container:', 'container-metadata')]:
                for identity in metadata['values'].get(property_name, set()):
                    if '$(' not in identity:
                        add(project, 'publication', prefix + identity, signal)

    def publication(path, identity, project=None, signal='publication-entry'):
        require(nonblank(identity), f'malformed-publication:{path}')
        if project:
            project = resolve_path('_root_', project)
            require(PROJECT.search(project) is not None, f'malformed-publication:{path}')
            if project in projects and not projects[project]['signals']:
                return
        else:
            matches = identities.get(identity.lower(), set())
            if not matches and signal == 'container-image':
                image_name = identity.rsplit('/', 1)[-1].split(':', 1)[0].split('@', 1)[0]
                matches = identities.get(image_name.lower(), set())
            if matches and not any(projects[p]['signals'] for p in matches):
                return
        add(path, 'publication', identity, signal)

    for path in interesting:
        if PROJECT.search(path) or path.endswith(('.cs', '.fs', '.vb', '.props', '.targets')):
            continue
        text = tree.text(path)
        if path.endswith('.json'):
            # Only publication/tool/server metadata is parsed as JSON. Arbitrary
            # schemas, localization and documentation data are not publications.
            relevant = bool(re.fullmatch(r'(?:.*(?:release|publish)(?:[-_].*)?|\.?mcp|dotnet-tools|package)\.json', PurePosixPath(path).name, re.I)
                            or re.search(r'"mcpServers"\s*:|"servers"\s*:\s*\{|"(?:packages|containers|images)"\s*:\s*\[', text))
            if not relevant:
                continue
            document = json_bytes(text, path)
            if not isinstance(document, dict) and not re.search(r'release|publish|mcp|dotnet-tools|^package\.json$', PurePosixPath(path).name, re.I):
                continue  # A retained runtime observation array is not a manifest.
            require(isinstance(document, dict), f'malformed-publication:{path}')
            if 'mcpServers' in document or 'servers' in document:
                servers = document.get('mcpServers', document.get('servers'))
                require(isinstance(servers, dict), f'malformed-server-configuration:{path}')
                for identity, config in servers.items():
                    require(nonblank(identity) and isinstance(config, dict) and bool(config), f'malformed-server-configuration:{path}')
                    # Exact binding includes command/URL/arguments via the hash.
                    add(path, 'configuration', identity + ':' + digest(json.dumps(config, sort_keys=True, separators=(',', ':')).encode()), 'developer-server-configuration')
            if 'bin' in document and PurePosixPath(path).name == 'package.json':
                binaries = document['bin']
                require(isinstance(binaries, (dict, str)) and bool(binaries), f'malformed-publication:{path}')
                if isinstance(binaries, str):
                    require(nonblank(document.get('name')), f'malformed-publication:{path}')
                    publication(path, document['name'], signal='tool-manifest')
                else:
                    for identity, target in binaries.items():
                        require(nonblank(target), f'malformed-publication:{path}')
                        publication(path, identity + ':' + target, signal='tool-manifest')
            if 'tools' in document and 'dotnet-tools' in path:
                require(isinstance(document['tools'], dict), f'malformed-publication:{path}')
                for identity in document['tools']:
                    publication(path, identity, signal='tool-manifest')
            for collection in ('packages', 'containers', 'images'):
                if collection not in document:
                    continue
                require(isinstance(document[collection], list), f'malformed-publication:{path}')
                for entry in document[collection]:
                    require(isinstance(entry, dict), f'malformed-publication:{path}')
                    project = entry.get('project')
                    identity = entry.get('packageId') or entry.get('package_id') or entry.get('id') or entry.get('image') or entry.get('repository') or entry.get('name') or project
                    publication(path, identity, project)
        elif path.endswith('.toml') and 'config' in PurePosixPath(path).name:
            try:
                document = tomllib.loads(text)
            except tomllib.TOMLDecodeError:
                raise CensusError(f'malformed-server-configuration:{path}') from None
            servers = document.get('mcp_servers', {})
            require(isinstance(servers, dict), f'malformed-server-configuration:{path}')
            for identity, config in servers.items():
                require(nonblank(identity) and isinstance(config, dict) and bool(config), f'malformed-server-configuration:{path}')
                add(path, 'configuration', identity + ':' + digest(json.dumps(config, sort_keys=True, separators=(',', ':')).encode()), 'developer-server-configuration')
        elif path.endswith(('.yml', '.yaml', '.sh', '.ps1', '.cmd', '.bat')) or PurePosixPath(path).name.startswith('Dockerfile'):
            if path.endswith(('.yml', '.yaml')) and not (path.startswith('.github/workflows/') or re.search(r'(?m)^\s*(?:image|kind|container)\s*:|\b(?:dotnet|docker|podman)\s', text)):
                continue
            # Every literal project invocation and proprietary package/container
            # identity is checked, including orphan entries after source removal.
            text = re.sub(r'\$\{\{.*?\}\}', '', text, flags=re.S)
            for match in re.finditer(r'(?<![\w$])([\w./\\-]+\.(?:cs|fs|vb)proj)\b', text, re.I):
                value = match[1].replace('\\', '/')
                line = text[text.rfind('\n', 0, match.start()) + 1:text.find('\n', match.end()) if '\n' in text[match.end():] else len(text)]
                if not re.search(r'release|publish|container|deploy|startup', path, re.I) and not re.search(r'dotnet\s+(?:run|publish|pack)\b', line, re.I):
                    continue
                if '$' in value or value.startswith(('../', '/')):
                    continue
                target = posixpath.normpath(value)
                if target in projects:
                    publication(path, target, target, 'project-publication-reference')
                else:
                    publication(path, value, target, 'orphan-project-reference')
            # Keep image scalars on their own line. A mapping's repository
            # belongs to that image block, never to a following YAML key.
            lines = text.splitlines()
            for index, line in enumerate(lines):
                match = re.match(r'^(\s*)(?:-\s*)?image:[ \t]*(.*)$', line)
                if not match:
                    continue
                try:
                    scalar_tokens = shlex.split(match[2], comments=True)
                except ValueError:
                    scalar_tokens = []
                scalar = scalar_tokens[0] if scalar_tokens else ''
                if scalar and not scalar.startswith('#'):
                    if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./:@-]*', scalar) and not scalar.endswith(':'):
                        publication(path, scalar, signal='container-image')
                else:
                    indent = len(match[1])
                    for child in lines[index + 1:]:
                        if not child.strip() or child.lstrip().startswith('#'):
                            continue
                        if len(child) - len(child.lstrip()) <= indent:
                            break
                        repository_match = re.match(r'^[ \t]+repository:[ \t]*["\']?([A-Za-z0-9][A-Za-z0-9_./:@-]*)', child)
                        if repository_match:
                            publication(path, repository_match[1], signal='container-image')
                            break
            for line in lines:
                try:
                    command = shlex.split(line, comments=True)
                except ValueError:
                    continue  # Multiline shell fragments are inspected on their literal lines.
                for index, token in enumerate(command):
                    following = command[index + 1:]
                    if token == 'dotnet' and following[:2] == ['tool', 'install']:
                        arguments = iter(following[2:])
                        for value in arguments:
                            if value in ('--version', '--tool-path', '--configfile', '--add-source', '--framework'):
                                next(arguments, None)
                            elif value.startswith('-'):
                                continue
                            else:
                                if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', value):
                                    publication(path, value, signal='tool-install')
                                break
                    if token in ('docker', 'podman') and following:
                        if following[0] == 'push' and len(following) > 1:
                            value = following[1]
                            if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./:@-]*', value):
                                publication(path, value, signal='container-image')
                        elif following[0] == 'build' or following[:2] == ['buildx', 'build']:
                            for offset, value in enumerate(following[:-1]):
                                if value in ('-t', '--tag'):
                                    identity = following[offset + 1]
                                    if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./:@-]*', identity):
                                        publication(path, identity, signal='container-image')
            tokens = set(re.findall(r'(?<![\w.])([A-Za-z][A-Za-z0-9_.-]*(?:[.-](?:mcp|cli)))(?![\w.])', text, re.I))
            for token in tokens:
                publication(path, token, signal='package-or-container-reference')
    return candidates, sorted(p for p, entry in tree.entries.items() if entry[0] == '160000'), excluded


def scan(workspace, revision, baseline_path, index_path, today):
    revision = git(workspace, 'rev-parse', '--verify', '--end-of-options', revision + '^{commit}')
    require(SHA.fullmatch(revision) is not None, 'invalid-parent-revision')
    parent = Tree(workspace, revision)
    roots = declarations(parent)
    policy, baseline_roots, allowed, exclusions, exceptions, provenance = load_policy(workspace, parent, baseline_path, index_path, today)
    report = {'schema': SCHEMA, 'status': 'passed', 'parentRevision': revision, 'utcDate': today.isoformat(),
              'policy': provenance, 'repositories': [], 'surfaces': [], 'stale': [], 'errors': []}
    observed, inspected = set(), set()
    for repository, gitlink in roots.items():
        summary = {'repository': repository, 'gitlink': gitlink, 'nestedGitlinks': [], 'exclusions': [], 'status': 'passed'}
        report['repositories'].append(summary)
        try:
            require(repository in baseline_roots, 'unapproved-root')
            location = workspace / repository
            require(location.is_dir() and not any(p.is_symlink() for p in [location, *list(location.parents)[:len(PurePosixPath(repository).parts) - 1]]), 'reference-root-unavailable-or-linked')
            # Refuse Git's upward repository discovery for an uninitialized root.
            gitdir = git(location, 'rev-parse', '--show-prefix')
            require(not gitdir, 'reference-root-uninitialized')
            require(git(location, 'cat-file', '-t', gitlink) == 'commit', 'reference-pin-not-commit')
            tree = Tree(location, gitlink)
            candidates, nested, scoped = scan_tree(tree, repository, exclusions)
            inspected.add(repository)
            summary['nestedGitlinks'] = nested
            summary['exclusions'] = scoped
            summary['committedEntries'] = len(tree.entries)
            summary['classification'] = baseline_roots[repository]['classification']
            for key, candidate in sorted(candidates.items()):
                observed.add(key)
                entry = {**candidate, 'gitlink': gitlink, 'signals': sorted(candidate['signals']), 'sources': sorted(candidate['sources'])}
                allowance = allowed.get(key)
                exception = exceptions.get(key)
                if exception:
                    entry.update(status='exception', classification='migration-exception', owner=exception['owner'], expires=exception['expires'])
                elif key[2] == 'publication' and any(t['identity'].lower() == key[3].lower() for t in policy['toolIdentities']):
                    tool = next(t for t in policy['toolIdentities'] if t['identity'].lower() == key[3].lower())
                    entry.update(status='approved', classification=tool['classification'], row=tool['row'])
                elif allowance:
                    extra = set(candidate['signals']) - set(allowance['signals'])
                    source_changes = [source['path'] for source in allowance.get('sources', [])
                                      if source['path'] not in tree.entries or digest(tree.blob(source['path'])) != source['sha256']]
                    if 'sourcePrefix' in allowance:
                        prefix = allowance['sourcePrefix'] + '/'
                        expected_paths = {source['path'] for source in allowance['sources']}
                        actual_paths = ({source['path'] for source in compilation_closure(tree, allowance['surface']['path'])}
                                        if allowance.get('compilationClosure') else {path for path in tree.entries if path.startswith(prefix)})
                        source_changes = sorted(set(source_changes) | (expected_paths ^ actual_paths))
                    if extra or source_changes:
                        entry.update(status='rejected', classification=allowance['classification'], row=allowance['row'],
                                     reason='allowance-signal-or-source-drift', unexpectedSignals=sorted(extra), changedSources=source_changes)
                    else:
                        entry.update(status='approved', classification=allowance['classification'], row=allowance['row'])
                else:
                    entry.update(status='rejected', classification='unapproved', reason='new-proprietary-surface')
                report['surfaces'].append(entry)
                if entry['status'] == 'rejected':
                    summary['status'] = 'failed'
        except (CensusError, OSError, UnicodeError) as error:
            summary['status'] = 'failed'
            report['errors'].append({'repository': repository, 'gitlink': gitlink, 'rule': str(error) if isinstance(error, CensusError) else 'reference-read-failed'})
    for key, entry in sorted(allowed.items()):
        if key not in observed and (key[0] in inspected or key[0] not in roots):
            report['stale'].append({'surface': entry['surface'], 'row': entry['row'], 'classification': entry['classification']})
    for repository in sorted(set(baseline_roots) - set(roots)):
        report['stale'].append({'repository': repository, 'classification': baseline_roots[repository]['classification'], 'reason': 'root-removed'})
    if report['errors'] or any(s['status'] == 'rejected' for s in report['surfaces']):
        report['status'] = 'failed'
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    parser.add_argument('--revision', default='HEAD')
    parser.add_argument('--baseline', type=Path, default=Path(__file__).with_name('baseline.json'))
    parser.add_argument('--amendments', type=Path, default=Path(__file__).with_name('amendments.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = scan(args.workspace.resolve(), args.revision, args.baseline, args.amendments, datetime.now(timezone.utc).date())
    except (CensusError, OSError, UnicodeError, TypeError, KeyError, AttributeError) as error:
        report = {'schema': SCHEMA, 'status': 'failed', 'errors': [{'rule': str(error) if isinstance(error, CensusError) else 'invalid-policy-or-source'}]}
    rendered = sanitized(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + '\n')
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding='utf-8')
    except OSError:
        print('Proprietary surface census failed: report-write-failed', file=sys.stderr)
        return 1
    print(rendered, end='')
    for entry in report.get('surfaces', []):
        if entry['status'] == 'rejected':
            surface = entry['surface']
            print(sanitized(f"rejected: {surface['repository']}@{entry['gitlink']} {surface['path']} [{surface['identity']}] signals={','.join(entry['signals'])}"), file=sys.stderr)
    for error in report.get('errors', []):
        print(sanitized('error: ' + json.dumps(error, sort_keys=True)), file=sys.stderr)
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
