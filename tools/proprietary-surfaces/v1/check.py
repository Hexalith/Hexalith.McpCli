#!/usr/bin/env python3
"""Census proprietary tool surfaces in committed root-declared reference trees."""
from __future__ import annotations

import argparse
import configparser
from contextlib import contextmanager
from datetime import date, datetime, timezone
import hashlib
from functools import lru_cache
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
REGISTRATION = re.compile(r'\b(?:Add\w*Mcp\w*|Map\w*Mcp\w*|With(?:StdioServer|Http)Transport|McpServerTool\w*|McpServerResource\w*|McpServerPrompt\w*)\s*(?:\(|\]|<|>)|\bMcpServer\s*\.\s*Create\s*\(|\bnew\s+(?:[A-Za-z_][\w]*\s*\.\s*)*(?:StdioServerTransport|StreamableHttpServerTransport|SseServerTransport)\s*\(')
COMMAND = re.compile(r'\bSystem\.CommandLine\b')
DOTNET_INVOCATION = re.compile(r"(?<![\w])(?:[\"']dotnet[\"']|dotnet)[ \t]+(?:publish|pack|run)\b")
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
            if len(header) == 2 and header[1] == b'missing':
                offset = end + 1
                continue
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


def validate_approval_evidence(workspace, amendment, receipt, authorities):
    """Require an affirmative receipt bound to the exact mutation scope."""
    require(isinstance(receipt, dict) and receipt.get('decision') == 'approved'
            and receipt.get('owner') == amendment['approval']['owner'], 'amendment-evidence-not-approved')
    operations = ('addAllowances', 'removeAllowances', 'addExceptions', 'removeExceptions', 'addExclusions')
    if receipt.get('schema') == 'mcpcli-census-amendment-approval/v2':
        authorization = receipt.get('authorization')
        require(isinstance(authorization, dict) and set(authorization) == set(operations)
                and canonical(authorization) == canonical({key: amendment.get(key, []) for key in operations}), 'amendment-authorization-scope-mismatch')
        bindings = receipt.get('authority')
        require(isinstance(bindings, list) and bool(bindings), 'amendment-authority-missing')
        for binding in receipt['authority']:
            require(isinstance(binding, dict) and set(binding) == {'path', 'sha256'}, 'invalid-amendment-authority')
            safe_path(binding['path'])
            require(isinstance(binding['sha256'], str) and HASH.fullmatch(binding['sha256']) is not None,
                    'invalid-amendment-authority')
            # A receipt cannot nominate a new authority. Only immutable baseline
            # provenance and previously validated receipts belong to this lineage.
            require((binding['path'], binding['sha256']) in authorities, 'untrusted-amendment-authority')
            authority = authorities[(binding['path'], binding['sha256'])]
            require(authority.get('decision') == 'approved', 'invalid-amendment-authority')
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
        values, _, _, _ = project_metadata(tree, project, metadata_files(tree))
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
    authorities = {}
    for binding in policy['provenance']:
        raw = parent.blob(binding['path'])
        if not raw.lstrip().startswith(b'{'):
            continue
        source = json_bytes(raw, binding['path'])
        if isinstance(source, dict) and source.get('decision') == 'approved':
            revisions = source.get('source_revisions')
            require(isinstance(revisions, dict) and revisions
                    and revisions == {key: row['gitlink'] for key, row in roots.items()},
                    'invalid-inventory-authority-scope')
            authorities[(binding['path'], binding['sha256'])] = source
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
        receipt = json_bytes(evidence.read_bytes(), binding['path'])
        if isinstance(receipt, dict) and receipt.get('schema') == 'mcpcli-census-amendment-approval/v1':
            require(binding['path'] in parent.entries and digest(parent.blob(binding['path'])) == binding['sha256'],
                    'legacy-amendment-evidence-not-committed')
            registry_path = baseline_path.with_name('legacy-receipts.json')
            require(registry_path.is_file() and not registry_path.is_symlink(), 'legacy-receipt-registry-required')
            registry = json_bytes(registry_path.read_bytes(), 'legacy-receipts')
            require(isinstance(registry, dict) and set(registry) == {'schema', 'baselineSha256', 'receipts'}
                    and registry['schema'] == 'mcpcli-census-legacy-receipts/v1'
                    and registry['baselineSha256'] == digest(baseline_raw)
                    and isinstance(registry['receipts'], list), 'invalid-legacy-receipt-registry')
            for retained in registry['receipts']:
                require(isinstance(retained, dict) and set(retained) == {'path', 'sha256'}
                        and isinstance(retained['sha256'], str) and HASH.fullmatch(retained['sha256']) is not None,
                        'invalid-legacy-receipt-registry')
                safe_path(retained['path'])
            require(len({canonical(retained) for retained in registry['receipts']}) == len(registry['receipts']),
                    'invalid-legacy-receipt-registry')
            require(binding in registry['receipts'], 'untrusted-legacy-amendment-evidence')
        validate_approval_evidence(workspace, amendment, receipt, authorities)
        authorities[(binding['path'], binding['sha256'])] = receipt
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
    'ContainerRepository', 'ContainerRegistry', 'IsPackable', 'TargetName')}


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


@lru_cache(maxsize=2048)
def msbuild_glob_pattern(pattern):
    """MSBuild ** spans zero or more directories; * stays in one segment."""
    expression, index = '', 0
    while index < len(pattern):
        if pattern[index:index + 3] == '**/':
            expression += '(?:[^/]+/)*'
            index += 3
        elif pattern[index:index + 2] == '**':
            expression += '.*'
            index += 2
        elif pattern[index] == '*':
            expression += '[^/]*'
            index += 1
        elif pattern[index] == '?':
            expression += '[^/]'
            index += 1
        else:
            expression += re.escape(pattern[index])
            index += 1
    return re.compile(expression + r'\Z')


def msbuild_glob(path, pattern):
    return msbuild_glob_pattern(pattern).fullmatch(path) is not None


def metadata_files(tree):
    # Import extensions have no MSBuild semantics. The caller selects imports
    # from every committed blob, and only selected XML is parsed as metadata.
    return {path for path, entry in tree.entries.items() if entry[0] in ('100644', '100755')}


def expanded_values(value, properties, current, project, *, required=True):
    """Retain each local conditional property alternative without executing it."""
    def expand(text, seen):
        require(len(seen) < 128, f'property-expansion-depth:{current}')
        match = next((match for match in re.finditer(r'\$\(([A-Za-z_][\w.]*)\)', text)
                      if match[1].lower() in properties and match[1].lower() not in seen), None)
        if match is None:
            return {expand_msbuild(text, {}, current, project, required=required)}
        key = match[1].lower()
        result = set()
        for choice in sorted(properties[key]):
            expression = re.compile(r'\$\(' + re.escape(key) + r'\)', re.I)
            result.update(expand(expression.sub(lambda match: choice, text), seen | {key}))
            if len(result) > 256:
                require(not required, f'ambiguous-classification-metadata:{current}')
                return {value}
        return result
    return sorted(expand(value, set()))


def project_metadata(tree, path, metadata_paths, errors=None):
    """Read props, project and targets in order, retaining conditional branches."""
    documents, visited, values, references, item_records = [], set(), {}, [], []
    properties = {'assemblyname': {PurePosixPath(path).stem}}
    declared_properties, copy_sources = set(), {}
    parents = list(reversed(list(PurePosixPath(path).parents)))
    props = [(ancestor / 'Directory.Build.props').as_posix() for ancestor in parents]
    targets = [(ancestor / 'Directory.Build.targets').as_posix() for ancestor in parents]
    props = [p for p in props if p in metadata_paths][-1:]
    targets = [p for p in targets if p in metadata_paths][-1:]
    initial = [p for p in props if p in metadata_paths] + [path] + [p for p in targets if p in metadata_paths]

    def visit(current, inherited_condition=False):
        if (current, inherited_condition) in visited:
            return
        visited.add((current, inherited_condition))
        document = xml(tree.text(current), current)
        documents.append(current)

        def inspect(element, conditional=False):
            name = local_name(element).lower()
            conditional = conditional or attribute(element, 'Condition') is not None or name in ('when', 'otherwise')
            text = (element.text or '').strip()
            if not list(element) and (text or name in properties or name in PROPERTY_NAMES):
                declared_properties.add(name)
                possibilities = set(expanded_values(text, properties, current, path, required=False))
                # Any conditional definition can be selected by a build; preserve
                # it even when another branch appears later in the document.
                if conditional:
                    properties.setdefault(name, set()).update(possibilities)
                else:
                    properties[name] = possibilities
                if name in PROPERTY_NAMES:
                    values.setdefault(PROPERTY_NAMES[name], set()).update(possibilities)
            if name in ('packagereference', 'projectreference'):
                raw = attribute(element, 'Include') or attribute(element, 'Update') or ''
                for value in expanded_values(raw, properties, current, path, required=False):
                    references.append(('PackageReference' if name == 'packagereference' else 'ProjectReference', value, current))
            if attribute(element, 'Include') is not None or attribute(element, 'Remove') is not None:
                item_records.append((name, element, current, conditional))
            if name == 'copy':
                for output in element:
                    if local_name(output).lower() == 'output' and (attribute(output, 'TaskParameter') or '').lower() == 'destinationfiles':
                        copy_sources[id(output)] = attribute(element, 'SourceFiles')
            if name == 'output' and attribute(element, 'ItemName'):
                item_records.append((attribute(element, 'ItemName').lower(), element, current, conditional))
            if name == 'import':
                raw = attribute(element, 'Project') or ''
                require(bool(raw), f'malformed-project-metadata:{current}')
                if attribute(element, 'Sdk'):
                    return  # SDK imports are resolved outside this committed tree.
                for value in expanded_values(raw, properties, current, path, required=False):
                    if '$(' not in value:
                        relative = (posixpath.normpath(value.removeprefix('@repo/').replace('\\', '/')) if value.startswith('@repo/')
                                    else posixpath.normpath(posixpath.join(str(PurePosixPath(current).parent), value.replace('\\', '/'))))
                        require(relative != '..' and not relative.startswith('../'), f'unsafe-import-path:{current}')
                        target = metadata_path(current, raw, value)
                        if any(entry[0] == '160000' and (target == nested or target.startswith(nested + '/'))
                               for nested, entry in tree.entries.items()):
                            continue  # Nested gitlinks are reported, never opened.
                        matches = ([target] if target in metadata_paths else []) if not re.search(r'[*?]', target) else sorted(
                            candidate for candidate in metadata_paths if msbuild_glob(candidate, target))
                        if not matches and not re.search(r'[*?]', target):
                            condition = attribute(element, 'Condition') or ''
                            exists = re.fullmatch(r'''\s*Exists\(\s*(["'])(.*?)\1\s*\)\s*''', condition, re.I)
                            optional = False
                            if exists:
                                alternatives = expanded_values(exists[2], properties, current, path, required=False)
                                optional = bool(alternatives) and all('$(' not in item and metadata_path(current, exists[2], item) == target
                                                                      for item in alternatives)
                            require(optional, f'unavailable-local-import:{current}')
                        for candidate in matches:
                            visit(candidate, conditional)
                    else:
                        names = set(re.findall(r'[A-Za-z0-9_.-]+\.[A-Za-z0-9]+', value))
                        for candidate in sorted(metadata_paths):
                            if PurePosixPath(candidate).name in names and PurePosixPath(candidate).name not in ('Directory.Build.props', 'Directory.Build.targets'):
                                visit(candidate, True)
                        suffix = re.search(r'\)/([^$()]+)\Z', value.replace('\\', '/'))
                        if suffix and re.search(r'[*?]', suffix[1]):
                            safe_path(suffix[1])
                            for candidate in sorted(metadata_paths):
                                if (msbuild_glob(candidate, suffix[1]) or msbuild_glob(candidate, '**/' + suffix[1])):
                                    visit(candidate, True)
            for child in element:
                inspect(child, conditional)
        inspect(document, inherited_condition)

    for current in initial:
        visit(current)
    values = {canonical: {expanded for value in sorted(properties[name])
                          for expanded in expanded_values(value, properties, path, path)}
              for name, canonical in PROPERTY_NAMES.items() if name in properties}
    # SDK package identity defaults to the effective assembly name, then project.
    values['_DeclaredIdentity'] = {value for name in ('PackageId', 'AssemblyName')
                                   if name.lower() in declared_properties for value in values.get(name, set())}
    values.setdefault('AssemblyName', {PurePosixPath(path).stem})
    sdks = sdk_identities(tree, path) if PROJECT.search(path) else set()
    if sdks and {value.lower() for value in values.get('IsPackable', set())} != {'false'}:
        if not values.get('PackageId') or '' in values['PackageId']:
            values['PackageId'] = (values.get('PackageId', set()) - {''}) | set(values['AssemblyName'])
    if sdks and any(value.lower() == 'true' for value in values.get('PackAsTool', set())):
        if not values.get('ToolCommandName') or '' in values['ToolCommandName']:
            defaults = values.get('TargetName', set()) - {''} or values['AssemblyName']
            values['ToolCommandName'] = (values.get('ToolCommandName', set()) - {''}) | defaults
    expanded_references = []
    for name, value, current in references:
        for expanded in expanded_values(value, properties, current, path, required=False):
            identity = expanded.replace('\\', '/').rsplit('/', 1)[-1]
            literal = re.search(r"'([A-Za-z0-9_.-]+\.(?:cs|fs|vb)proj)'\)\)\Z", expanded, re.I)
            if '$(' in expanded and name == 'ProjectReference' and literal and re.match(r'\$\(\[MSBuild\]::NormalizePath\(', expanded, re.I):
                expanded = identity = literal[1]
            require('$(' not in expanded or name == 'ProjectReference' and '$(' not in identity
                    and PROJECT.search(identity) is not None, f'unresolved-classification-metadata:{current}')
            expanded_references.extend((name, item.strip(), current) for item in expanded.split(';') if item.strip())
    linked = compile_provenance(tree, path, properties, item_records, copy_sources, errors)
    return values, expanded_references, documents, linked



def compile_provenance(tree, project, properties, records, copy_sources, errors=None):
    """Resolve finite committed item aliases; runtime task output never supplies bytes."""
    items, linked = {}, set()
    for name, element, current, conditional in records:
        if local_name(element).lower() == 'output':
            items.setdefault(name, []).append((copy_sources.get(id(element)), current, True))
            continue
        raw = attribute(element, 'Include')
        if raw is not None:
            items.setdefault(name, []).append((raw, current, False))

    def resolve(raw, current, seen):
        result = set()
        for expanded in expanded_values(raw, properties, current, project, required=False):
            for value in expanded.split(';'):
                value = value.strip()
                if not value:
                    continue
                alias = re.fullmatch(r'@\(([A-Za-z_][\w.-]*)\)', value)
                if alias:
                    key = alias[1].lower()
                    require(key not in seen and len(seen) < 32, f'cyclic-compile-item:{current}:{key}')
                    require(key in items, f'unresolved-compile-item:{current}:{key}')
                    for included, origin, task_output in items[key]:
                        require(included is not None, f'dynamic-generated-compile-source:{origin}:{key}')
                        try:
                            result.update(resolve(included, origin, seen | {key}))
                        except CensusError:
                            if task_output:
                                raise CensusError(f'dynamic-generated-compile-source:{origin}:{key}') from None
                            raise
                else:
                    require('@(' not in value and '%(' not in value and '$' not in value,
                            f'unresolved-compile-source:{current}')
                    try:
                        target = metadata_path(project, value, value)
                        require(not any(target == p or target.startswith(p + '/') for p, e in tree.entries.items()
                                        if e[0] == '160000'), 'nested')
                    except CensusError:
                        raise CensusError(f'unsafe-or-nested-compile-source:{current}') from None
                    matches = {candidate for candidate, entry in tree.entries.items()
                               if entry[0] in ('100644', '100755') and msbuild_glob(candidate, target)}
                    require(bool(matches), f'unavailable-committed-compile-source:{current}')
                    result.update(matches)
                require(len(result) <= 4096, f'unbounded-compile-items:{current}')
        return result

    for name, element, current, conditional in records:
        if name != 'compile' or attribute(element, 'Include') is None:
            continue
        try:
            # Include all conditional/removed alternatives conservatively: no
            # item operation can hide a potentially compiled committed source.
            linked.update(resolve(attribute(element, 'Include'), current, {'compile'}))
        except CensusError as error:
            if errors is None:
                raise
            entry = {'path': current, 'rule': str(error)}
            if entry not in errors:
                errors.append(entry)
    return linked

def sdk_identities(tree, path):
    document = xml(tree.text(path), path)
    identities = (attribute(document, 'Sdk') or '').split(';')
    for element in document:
        if local_name(element).lower() == 'sdk':
            identities.append(attribute(element, 'Name') or '')
    return {identity.split('/', 1)[0].lower() for identity in identities if identity}


def image_repository(reference):
    """Retain the complete registry/namespace/repository, without tag or digest."""
    name = reference.split('@', 1)[0]
    return name.rsplit(':', 1)[0] if ':' in name.rsplit('/', 1)[-1] else name


def declared_container_repositories(metadata):
    values = metadata['values']
    return {image_repository((registry.rstrip('/') + '/' if registry else '') + repository.lstrip('/'))
            for registry in values.get('ContainerRegistry', {''})
            for repository in values.get('ContainerRepository', set())}


def json_documents(document, path):
    """Inspect nested manifest objects in finite JSON arrays and wrappers."""
    require(isinstance(document, (dict, list)), f'malformed-publication:{path}')
    if isinstance(document, list):
        require(all(isinstance(value, (dict, list)) for value in document), f'malformed-publication:{path}')
    pending, count = [(document, 0, True)], 0
    while pending:
        value, depth, structural = pending.pop()
        count += 1
        require(depth <= 32 and count <= 4096, f'unbounded-publication-json:{path}')
        if isinstance(value, dict):
            yield value
            schema = isinstance(value.get('$schema'), str) and value['$schema'] in {'https://json-schema.org/draft/2020-12/schema',
                'https://json-schema.org/draft/2019-09/schema', 'http://json-schema.org/draft-07/schema#',
                'http://json-schema.org/draft-06/schema#', 'http://json-schema.org/draft-04/schema#'}
            schema_keywords = {'$defs', 'definitions', 'properties', 'patternProperties', 'dependentSchemas',
                               'items', 'prefixItems', 'additionalProperties', 'allOf', 'anyOf', 'oneOf', 'not', 'if', 'then', 'else'}
            pending.extend((child, depth + 1, False) for key, child in reversed(list(value.items()))
                           if isinstance(child, (dict, list)) and not (schema and key in schema_keywords))
        elif isinstance(value, list):
            if structural:
                require(all(isinstance(child, (dict, list)) for child in value), f'malformed-publication:{path}')
            pending.extend((child, depth + 1, structural) for child in reversed(value) if isinstance(child, (dict, list)))


def compilation_closure(tree, project):
    """Bind fixture files, inherited/imported metadata and linked local sources."""
    metadata_paths = metadata_files(tree)
    _, _, documents, linked = project_metadata(tree, project, metadata_paths)
    prefix = str(PurePosixPath(project).parent) + '/'
    paths = {path for path in tree.entries if path.startswith(prefix)} | set(documents) | linked
    return [{'path': path, 'sha256': digest(tree.blob(path))} for path in sorted(paths)]


def workflow_matrix_values(text):
    """Collect literal matrix scalars, flow lists and include-map values."""
    matrices = {}
    matrix_indent = None
    active_key = None
    def literals(raw):
        raw = raw.strip().strip('[]')
        return [next(value for value in groups if value) for groups in re.findall(r'''"([^"]*)"|'([^']*)'|([^,\s]+)''', raw)
                if any(value and PROJECT.search(value) and '$' not in value for value in groups)]
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        indent = len(line) - len(line.lstrip())
        if re.match(r'^[ \t]*matrix:[ \t]*(?:#.*)?$', line):
            matrix_indent, active_key = indent, None
            continue
        if matrix_indent is None:
            continue
        if indent <= matrix_indent:
            matrix_indent = None
            continue
        match = re.match(r'^[ \t]*(?:-[ \t]*)?([\w.-]+):[ \t]*(.*)$', line)
        if match:
            key, raw = match.groups()
            if key in ('include', 'exclude'):
                continue
            active_key = key
            for value in literals(raw):
                matrices.setdefault(key, []).append(value)
        elif active_key:
            match = re.match(r'^[ \t]*-[ \t]*(.*)$', line)
            if match:
                matrices.setdefault(active_key, []).extend(literals(match[1]))
    return matrices


def expand_workflow_projects(text, path):
    """Resolve only project-target expressions within their own workflow job."""
    lines = text.splitlines(keepends=True)
    boundaries = [index for index, line in enumerate(lines) if re.match(r'^  [A-Za-z_][\w-]*:[ \t]*(?:#.*)?$', line)]
    boundaries = sorted(set([0, *boundaries, len(lines)]))
    output = []
    for begin, end in zip(boundaries, boundaries[1:]):
        block = ''.join(lines[begin:end])
        matrices = workflow_matrix_values(block)
        expressions = []
        prefix = '@census-expression'
        while prefix in block:
            prefix = '@' + prefix
        def placeholder(match):
            expressions.append(match[1].strip())
            return f'{prefix}-{len(expressions) - 1}@'
        masked = re.sub(r'\$\{\{(.*?)\}\}', placeholder, block, flags=re.S)
        targets = set()
        for script, _ in script_blocks(masked, path):
            for invocation in dotnet_invocations(script):
                suffix = script[invocation.end():].split('\n', 1)[0]
                try:
                    arguments = shlex.split(suffix, comments=True)
                except ValueError:
                    arguments = suffix.split()
                skip_value = False
                for index, value in enumerate(arguments):
                    if skip_value:
                        skip_value = False
                        continue
                    if value in ('--project',):
                        if index + 1 < len(arguments):
                            targets.add(arguments[index + 1])
                        break
                    if value.startswith('--project='):
                        targets.add(value.partition('=')[2])
                        break
                    if value in ('--configuration', '-c', '--framework', '-f', '--runtime', '-r', '--output', '-o', '--verbosity', '-v', '--property', '-p'):
                        skip_value = True
                        continue
                    if value.startswith('-'):
                        continue
                    targets.add(value)
                    break
        required = set()
        for target in sorted(targets):
            for match in re.finditer(re.escape(prefix) + r'-(\d+)@', target):
                key = expressions[int(match[1])]
                require(key.startswith('matrix.') and key[7:] in matrices, f'unresolved-publication-target:{path}')
                require(target == match[0], f'unresolved-publication-target:{path}')
                required.add(key)
        alternatives = [masked]
        for key in sorted(required):
            require(len(alternatives) * len(matrices[key[7:]]) <= 256, f'unresolved-publication-target:{path}')
            expanded = []
            for alternative in alternatives:
                for value in matrices[key[7:]]:
                    literal = shlex.quote(value)
                    candidate = alternative
                    for index, expression in enumerate(expressions):
                        if expression != key:
                            continue
                        marker = f'{prefix}-{index}@'
                        candidate = candidate.replace('"' + marker + '"', literal).replace("'" + marker + "'", literal)
                        candidate = candidate.replace(marker, literal)
                    expanded.append(candidate)
            alternatives = expanded
        for alternative in alternatives:
            for index, expression in enumerate(expressions):
                alternative = alternative.replace(f'{prefix}-{index}@', '${{ ' + expression + ' }}')
            output.append(alternative)
    return ''.join(output)


def build_action_images(lines):
    """Inspect literal tags in each build-push-action step's own inputs."""
    images = set()
    for index, line in enumerate(lines):
        if not re.search(r'uses:[ \t]*["\']?docker/build-push-action@', line, re.I):
            continue
        indent = len(line) - len(line.lstrip())
        block = []
        for following in lines[index + 1:]:
            if following.strip() and len(following) - len(following.lstrip()) < indent:
                break
            if re.match(r'^[ \t]*-[ \t]+(?:name|uses|run):', following):
                break
            block.append(following)
        tags_indent = None
        for input_line in block:
            match = re.match(r'^(\s*)tags:[ \t]*(.*)$', input_line)
            if match:
                tags_indent = len(match[1])
                raw = match[2]
            elif tags_indent is not None and len(input_line) - len(input_line.lstrip()) > tags_indent:
                raw = input_line.strip()
            else:
                tags_indent = None
                continue
            for identity in re.split(r'[ ,\t]+', raw.strip('"\'')):
                if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./:@-]*', identity) and not identity.endswith(':'):
                    images.add(identity)
    return images


def logical_commands(text):
    """Join supported shell, PowerShell and batch continuation lines."""
    return re.sub(r'(?:\\|`|\^)[ \t]*\r?\n[ \t]*', ' ', text)


def heredoc_operator(line):
    """Recognize a literal heredoc operator outside comments and quoted data."""
    quote, escaped, stack, index = None, False, [], 0
    while index < len(line):
        char = line[index]
        if escaped:
            escaped = False
        elif char == '\\' and quote != "'":
            escaped = True
        elif line[index:index + 2] == '$(' and quote != "'":
            stack.append(quote)
            quote = None
            index += 1
        elif char == ')' and stack and quote is None:
            quote = stack.pop()
        elif quote:
            if char == quote:
                quote = None
        elif char in ('"', "'"):
            quote = char
        elif char == '#' and (index == 0 or line[index - 1].isspace() or line[index - 1] in ';|&('):
            break
        elif line[index:index + 2] == '<<' and line[index:index + 3] != '<<<':
            return re.match(r'''<<-?\s*(["']?)([A-Za-z_][\w]*)\1''', line[index:])
        index += 1
    return None


def dotnet_invocations(text):
    """Find executable commands, preserving quoted arguments and substitutions.

    Comments and diagnostic strings are source text, not command invocations.
    A quoted executable is still executable when it occupies command position.
    """
    # Literal heredoc contents do not participate in the surrounding shell's
    # quote state. Unquoted substitutions are refused by the target resolver.
    lexical_lines, delimiter = [], None
    for line in text.splitlines(keepends=True):
        if delimiter:
            lexical_lines.append(''.join('\n' if char == '\n' else ' ' for char in line))
            if line.strip() == delimiter:
                delimiter = None
            continue
        lexical_lines.append(line)
        heredoc = heredoc_operator(line)
        if heredoc:
            delimiter = heredoc[2]
    lexical = ''.join(lexical_lines)
    positions, quote, escaped, comment, stack = set(), None, False, False, []
    index = 0
    while index < len(lexical):
        char = lexical[index]
        if comment:
            if char == '\n':
                comment = False
        elif escaped:
            escaped = False
        elif char == '\\' and quote != "'":
            escaped = True
        elif char == '`' and quote != "'":
            if stack and stack[-1][1] == '`' and quote is None:
                quote, _ = stack.pop()
            else:
                stack.append((quote, '`'))
                quote = None
        elif lexical[index:index + 2] == '$(' and quote != "'":
            stack.append((quote, ')'))
            quote = None
            index += 1
        elif char == ')' and stack and stack[-1][1] == ')' and quote is None:
            quote, _ = stack.pop()
        elif quote:
            if char == quote:
                quote = None
        elif char == '#' and (index == 0 or text[index - 1].isspace() or text[index - 1] in ';|&('):
            comment = True
        else:
            positions.add(index)
            if char in ('"', "'"):
                quote = char
        index += 1
    for match in DOTNET_INVOCATION.finditer(lexical):
        if match.start() not in positions:
            continue
        yield match


def script_blocks(text, path):
    """Separate YAML run scopes so shell state never leaks between steps."""
    if not path.endswith(('.yml', '.yaml')):
        return [(text, '.')]
    lines, blocks = text.splitlines(), []
    stack, contexts, defaults = [], [], {}
    for line in lines:
        key = re.match(r'^(\s*)(?:-\s+)?([A-Za-z_][\w.-]*):(?:[ \t]*(.*))?$', line)
        if key:
            indent = len(key[1]) + (2 if line.lstrip().startswith('- ') else 0)
            while stack and stack[-1][0] >= indent:
                stack.pop()
            ancestry = [entry[1] for entry in stack]
            job = ancestry[ancestry.index('jobs') + 1] if 'jobs' in ancestry and len(ancestry) > ancestry.index('jobs') + 1 else None
            if key[2] == 'working-directory' and ancestry[-2:] == ['defaults', 'run']:
                defaults[job] = (key[3] or '').strip('"\'')
            stack.append((indent, key[2]))
        ancestry = [entry[1] for entry in stack]
        contexts.append(ancestry[ancestry.index('jobs') + 1] if 'jobs' in ancestry and len(ancestry) > ancestry.index('jobs') + 1 else None)
    for index, line in enumerate(lines):
        match = re.match(r'^(\s*)(?:-\s+)?run:[ \t]*(.*)$', line)
        if not match:
            continue
        indent, raw = len(match[1]) + (2 if line.lstrip().startswith('- ') else 0), match[2].strip()
        begin = index
        while begin and not re.match(r'^\s*-\s+\w+:', lines[begin]):
            begin -= 1
        end = index + 1
        while end < len(lines) and (not lines[end].strip() or len(lines[end]) - len(lines[end].lstrip()) > indent):
            end += 1
        step_end = end
        while step_end < len(lines) and not re.match(r'^\s*-\s+\w+:', lines[step_end]):
            if lines[step_end].strip() and len(lines[step_end]) - len(lines[step_end].lstrip()) < indent:
                break
            step_end += 1
        directory = defaults.get(contexts[index], defaults.get(None, '.'))
        for setting in lines[begin:step_end]:
            value = re.match(r'^\s*working-directory:[ \t]*(.*?)\s*$', setting)
            if value:
                directory = value[1].strip('"\'')
        if raw.startswith(('|', '>')):
            body = lines[index + 1:end]
            base = min((len(row) - len(row.lstrip()) for row in body if row.strip()), default=0)
            script = '\n'.join(row[base:] for row in body)
            if raw.startswith('>'):
                script = ' '.join(row.strip() for row in body)
        else:
            script = raw
            if script[:1] in ('"', "'") and script[-1:] == script[:1]:
                script = script[1:-1]
        blocks.append((script, directory))
    return blocks


def shell_segments(text):
    """Split literal command separators, preserving quotes and substitutions."""
    result, start, quote, depth, escaped = [], 0, None, 0, False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == '\\' and quote != "'":
            escaped = True
        elif quote:
            if char == quote:
                quote = None
        elif char in ('"', "'"):
            quote = char
        elif char == '(':
            depth += 1
        elif char == ')' and depth:
            depth -= 1
        elif char in (';', '&', '|') and not depth:
            if text[start:index].strip():
                result.append(text[start:index].strip())
            start = index + 1
    if text[start:].strip():
        result.append(text[start:].strip())
    return result


def static_project_targets(tree, text, path, errors):
    """Bounded shell dataflow for literal variables, loops, calls and directories.

    This is an overapproximation of source paths, never a shell interpreter:
    no command, condition, substitution, external file or nested tree is run.
    """
    targets, functions, called, budget = set(), {}, set(), [0]
    if not DOTNET_INVOCATION.search(text):
        return []
    require('\x00' not in text, f'unsafe-script-text:{path}')
    # Supported literal substitutions cannot synthesize a NUL absent from source.
    # This marker therefore carries path provenance rather than source authority.
    repository_marker = '\x00repo'
    locators_proven = not re.search(r'^\s*(?:alias|shopt|enable|eval|source|\.)(?:\s|$)|'
        r'^\s*(?:function\s+)?(?:cd|dirname|pwd)\s*(?:\(\)|\{)|'
        r'\b(?:unset|read|declare|typeset)\b[^\n]*\bBASH_SOURCE\b|\bBASH_SOURCE\s*\[',
        text.replace('${BASH_SOURCE[0]}', ''), re.M)

    def problem(rule, target=None):
        error = {'path': path, 'rule': rule + ':' + path}
        if target is not None:
            error['target'] = target
        if error not in errors:
            errors.append(error)

    def expand(value, environment):
        # Only simple parameter references have a finite committed meaning.
        result = {value}
        for _ in range(32):
            next_result, changed = set(), False
            for item in result:
                match = re.search(r'\$\{([A-Za-z_][\w]*|[1-9][0-9]*)\}|\$([A-Za-z_][\w]*|[1-9][0-9]*)', item)
                if not match:
                    next_result.add(item)
                    continue
                key = match[1] or match[2]
                choices = environment.get(key)
                if choices is None:
                    return None
                changed = True
                next_result.update(item[:match.start()] + choice + item[match.end():] for choice in choices)
                if len(next_result) > 256:
                    return None
            result = next_result
            if not changed:
                return None if any(re.search(r'[$`*?\[\]{}\x00-\x1f]', item.removeprefix(repository_marker)) for item in result) else result
        return None

    def words(raw):
        try:
            return shlex.split(raw, comments=True)
        except ValueError:
            return []

    def normalized(directory, value):
        if directory is None or value.startswith('/') or re.match(r'^[A-Za-z]:', value):
            problem('unsafe-publication-path' if directory is not None else 'unresolved-publication-directory')
            return None
        base = '.' if value == repository_marker or value.startswith(repository_marker + '/') else directory
        value = value.removeprefix(repository_marker).lstrip('/') if base == '.' and value.startswith(repository_marker) else value
        target = posixpath.normpath(posixpath.join(base, value.replace('\\', '/')))
        try:
            if target != '.':
                safe_path(target)
        except CensusError:
            problem('unsafe-publication-path')
            return None
        return target

    def register_target(target):
        nested = next((p for p, entry in tree.entries.items() if entry[0] == '160000'
                       and (target == p or target.startswith(p + '/'))), None)
        if nested:
            problem('nested-publication-target', target)
            return
        if PROJECT.search(target):
            targets.add(target)
            return
        if target.lower().endswith('.slnx') and target in tree.entries:
            try:
                document = xml(tree.text(target), target)
                projects = [attribute(element, 'Path') for element in document.iter() if local_name(element).lower() == 'project']
                require(bool(projects) and len(projects) <= 4096, 'unresolved-solution')
                for project in projects:
                    require(nonblank(project) and '$' not in project and PROJECT.search(project), 'unresolved-solution')
                    resolved = normalized(str(PurePosixPath(target).parent), project)
                    if resolved is not None:
                        register_target(resolved)
            except CensusError:
                problem('unresolved-publication-solution', target)
            return
        members = [p for p in tree.entries if (PROJECT.search(p) or p.lower().endswith('.slnx'))
                   and str(PurePosixPath(p).parent) == target]
        if len(members) == 1:
            register_target(members[0])
        else:
            problem('unresolved-publication-target', target)

    def invoke(raw, environment, directory, unbounded=False):
        invocation = next(dotnet_invocations(raw), None)
        if invocation is None:
            return
        prefix = re.split(r'[;|&()`]', raw[:invocation.start()])[-1].strip()
        prefix = re.sub(r'^\$[A-Za-z_][\w]*\s*=\s*', '', prefix)
        prefix = re.sub(r'^(?:[A-Za-z_][\w]*=(?:[^\s\'"]+|\'[^\']*\'|"[^"]*")(?:\s+|$))+', '', prefix)
        if prefix and not re.fullmatch(r'(?:(?:if|then|else|elif|do|!|command|exec|env)\s*)+', prefix):
            problem('unsupported-publication-wrapper')
        if unbounded:
            problem('unbounded-publication-control-flow')
        try:
            arguments = shlex.split(raw[invocation.end():], comments=True)
        except ValueError:
            problem('unresolved-publication-target')
            return
        selected, skip = [], False
        for index, token in enumerate(arguments):
            if skip:
                skip = False
                continue
            if token == '--':
                break
            if token == '--project':
                selected = arguments[index + 1:index + 2]
                break
            if token.startswith('--project='):
                selected = [token.partition('=')[2]]
                break
            if token in ('--configuration', '-c', '--framework', '-f', '--runtime', '-r', '--output', '-o', '--verbosity', '-v', '--property', '-p', '--os', '--arch'):
                skip = True
                continue
            if token.startswith(('-', '/t:', '/p:')):
                continue
            if not selected or PROJECT.search(token):
                selected.append(token)
        if not selected:
            if directory is None:
                problem('unresolved-publication-directory')
            else:
                register_target(directory)
            return
        for value in selected:
            quoted_literal = any('$' in part and value in part for part in re.findall(r"'([^']*)'", raw[invocation.end():]))
            possibilities = None if quoted_literal else expand(value, environment)
            if possibilities is None:
                problem('unresolved-publication-target')
                continue
            for possibility in possibilities:
                target = normalized(directory, possibility)
                if target is not None:
                    register_target(target)

    def execute(lines, environment, directory, depth=0, unbounded=False, conditional=0):
        if depth > 16:
            problem('unbounded-publication-control-flow')
            return directory
        index, directory_stack = 0, []
        while index < len(lines):
            raw = lines[index].strip()
            index += 1
            budget[0] += 1
            if budget[0] > 8192:
                problem('unbounded-publication-control-flow')
                return None
            heredoc = heredoc_operator(raw)
            if heredoc:
                body = []
                while index < len(lines) and lines[index].strip() != heredoc[2]:
                    body.append(lines[index])
                    index += 1
                if not heredoc[1] and re.search(r'\$\(|`', '\n'.join(body)):
                    problem('unresolved-heredoc-substitution')
                index += 1
            if re.match(r'^(?:for|while|until)\b', raw) and re.search(r';\s*do\s+\S', raw):
                problem('unsupported-inline-publication-control-flow')
                continue
            function = re.match(r'^(?:function\s+)?([A-Za-z_][\w]*)\s*\(\)\s*\{\s*$', raw)
            loop = re.match(r'^(for\s+([A-Za-z_][\w]*)\s+in\s+(.+?)(?:;\s*do)?|(?:while|until)\b.*)\s*$', raw)
            if function or loop:
                body, nesting = [], 1
                while index < len(lines):
                    row = lines[index].strip()
                    index += 1
                    if loop and re.match(r'^(?:for|while|until)\b', row):
                        nesting += 1
                    if (row == '}' if function else re.match(r'^done(?:\s*(?:[<>].*)?)?$', row)):
                        if not function and re.search(r'\$\(|`|[<>]\(', row[4:]):
                            problem('unresolved-loop-redirection')
                        nesting -= 1
                        if not nesting:
                            break
                    body.append(row)
                if nesting:
                    if DOTNET_INVOCATION.search('\n'.join(body)):
                        problem('unbounded-publication-control-flow')
                    continue
                if function:
                    functions[function[1]] = body
                    continue
                choices = []
                if loop[2]:
                    for value in words(loop[3]):
                        expanded = expand(value, environment)
                        if expanded is None or len(expanded) != 1:
                            choices = None
                            break
                        choices.extend(sorted(expanded))
                else:
                    choices = None
                if choices is None or len(choices) > 256:
                    nested_environment = dict(environment)
                    if loop[2]:
                        nested_environment[loop[2]] = None
                    nested_directory = execute(body, nested_environment, directory, depth + 1, True, conditional)
                    if nested_directory != directory:
                        directory = None
                    environment.update({key: None for key in nested_environment if nested_environment[key] != environment.get(key)})
                else:
                    for value in choices:
                        environment[loop[2]] = {value} if not conditional else None
                        directory = execute(body, environment, directory, depth + 1, unbounded, conditional)
                continue
            if raw == '(':
                directory_stack.append((directory, dict(environment)))
                continue
            if raw.startswith(')') and directory_stack:
                directory, previous = directory_stack.pop()
                environment.clear()
                environment.update(previous)
                continue
            segments = shell_segments(raw)
            short_circuit = len(segments) > 1 and ('&&' in raw or '||' in raw)
            for command in segments:
                if re.match(r'^(?:if|case)\b', command):
                    conditional += 1
                if re.match(r'^(?:fi|esac)\b', command):
                    conditional = max(0, conditional - 1)
                command = re.sub(r'^(?:then|else|do)\s+', '', command)
                assignment = re.match(r'^(?:(?:local|export|readonly)\s+)?([A-Za-z_][\w]*)=(.*)$', command)
                if assignment:
                    if DOTNET_INVOCATION.search(command) and len(words(assignment[2])) > 1:
                        invoke(command, environment, directory, unbounded)
                        continue
                    value = words(assignment[2])
                    for item in value[1:]:
                        assigned = re.match(r'([A-Za-z_][\w]*)\+?=', item)
                        if assigned:
                            environment[assigned[1]] = None
                    choices = expand(value[0], environment) if len(value) == 1 else None
                    # Recognize this exact source-relative locator as spelling,
                    # without running dirname, cd or pwd from inspected code.
                    locator = re.fullmatch(r'"?\$\((?:CDPATH= )?cd (?:-- )?"(.*?)" && pwd(?: -P)?\)"?', assignment[2])
                    if locator and locators_proven and not path.endswith(('.yml', '.yaml')):
                        source_relative = re.fullmatch(r'\$\(dirname (?:-- )?"\$\{BASH_SOURCE\[0\]\}"\)(/[.\/]+)?', locator[1])
                        if source_relative:
                            base = repository_marker + '/' + str(PurePosixPath(path).parent)
                            paths = {base + (source_relative[1] or '')}
                        else:
                            paths = expand(locator[1], environment)
                        if paths and all(value == repository_marker or value.startswith(repository_marker + '/') for value in paths):
                            roots = {posixpath.normpath(value.removeprefix(repository_marker + '/')) if value != repository_marker else '.' for value in paths}
                            if all(root != '..' and not root.startswith('../') for root in roots):
                                choices = {repository_marker + ('/' + root if root != '.' else '') for root in roots}
                    if re.search(r"'[^']*\$[^']*'", assignment[2]):
                        choices = None
                    if conditional or short_circuit:
                        old = environment.get(assignment[1])
                        choices = None if choices is None or old is None else old | choices
                    environment[assignment[1]] = choices
                elif command.startswith('cd '):
                    value = words(command[3:])
                    if value[:1] == ['--']:
                        value = value[1:]
                    choices = expand(value[0], environment) if len(value) == 1 else None
                    directory = normalized(directory, next(iter(choices))) if choices and len(choices) == 1 and not conditional and not short_circuit else None
                    if directory and directory != '.' and not any(p.startswith(directory + '/') or p == directory for p in tree.entries):
                        directory = None
                else:
                    tokens = words(command)
                    writes = tokens[1:] if tokens and tokens[0] in ('builtin', 'command') else tokens
                    if writes[:1] == ['printf']:
                        for write_index, option in enumerate(writes[1:], 1):
                            if option == '--' or not option.startswith('-'):
                                break
                            if option.startswith('-v'):
                                destination = writes[write_index + 1] if option == '-v' and write_index + 1 < len(writes) else option[2:]
                                name = re.fullmatch(r'([A-Za-z_][\w]*)(?:\[.*\])?', destination)
                                if name:
                                    environment[name[1]] = None
                                else:
                                    environment.update({key: None for key in environment})
                                break
                    if tokens and tokens[0] in ('read', 'unset', 'declare', 'typeset', 'local'):
                        for token in tokens[1:]:
                            name = token.partition('=')[0]
                            if re.fullmatch(r'[A-Za-z_][\w]*', name):
                                environment[name] = None
                    if tokens and tokens[0].lower() in ('pushd', 'popd', 'eval', 'source', '.', 'set-location', 'push-location', 'pop-location', 'chdir'):
                        directory = None
                        environment.update({key: None for key in environment})
                    if tokens and tokens[0] in functions:
                        name = tokens[0]
                        called.add(name)
                        parameters = {key: values for key, values in environment.items() if not key.isdigit()}
                        for position, value in enumerate(tokens[1:], 1):
                            literal = any('$' in part and value in part for part in re.findall(r"'([^']*)'", command))
                            parameters[str(position)] = None if literal else expand(value, environment)
                        local_names = set()
                        for statement in functions[name]:
                            declaration = re.match(r'^local\s+([A-Za-z_][\w]*)', statement)
                            if declaration:
                                local_names.add(declaration[1])
                        changed_directory = execute(functions[name], parameters, directory, depth + 1, unbounded, conditional or short_circuit)
                        directory = None if (conditional or short_circuit) and changed_directory != directory else changed_directory
                        for key, values in parameters.items():
                            if not key.isdigit() and key not in local_names:
                                if conditional or short_circuit:
                                    old = environment.get(key)
                                    values = None if old is None or values is None else old | values
                                environment[key] = values
                    else:
                        invoke(command, environment, directory, unbounded)
        return directory

    for script, directory in script_blocks(text, path):
        environment = {}
        functions.clear()
        called.clear()
        directories = expand(directory, {})
        directory = normalized('.', next(iter(directories))) if directories and len(directories) == 1 else None
        if directory and directory != '.' and not any(p.startswith(directory + '/') or p == directory for p in tree.entries):
            directory = None
        execute(logical_commands(script).splitlines(), environment, directory)
        for name, body in list(functions.items()):
            if name not in called:
                execute(body, dict(environment), directory)
    return sorted(targets)

def scan_tree(tree, repository, exclusions):
    candidates, projects, identities, errors = {}, {}, {}, []
    @contextmanager
    def inspection(path):
        try:
            yield
        except (CensusError, OSError, UnicodeError) as error:
            errors.append({'path': path, 'rule': str(error) if isinstance(error, CensusError) else 'source-read-failed'})

    excluded = [e for e in exclusions if e['repository'] == repository]
    def omitted(path):
        for entry in excluded:
            if path == entry['prefix'] or entry.get('scope') != 'file' and path.startswith(entry['prefix'] + '/'):
                if entry.get('scope') == 'file':
                    require(digest(tree.blob(path)) in [entry['sha256'], *entry.get('additionalSha256', [])], f'excluded-fixture-source-drift:{path}')
                return True
        return False
    paths = []
    for path, entry in tree.entries.items():
        if entry[0] == '160000':
            continue
        with inspection(path):
            if not omitted(path):
                paths.append(path)
    shell_scripts = set()
    for path in paths:
        if tree.entries[path][0] == '100755':
            with inspection(path):
                if re.match(rb'#![^\r\n]*(?:/|\s)(?:bash|sh|dash|zsh|ksh)(?:[ \t\r\n]|$)', tree.blob(path)):
                    shell_scripts.add(path)
    interesting = [p for p in paths if p in shell_scripts or PROJECT.search(p) or p.endswith(('.props', '.targets', '.cs', '.fs', '.vb', '.json', '.toml', '.yml', '.yaml', '.ps1', '.sh', '.cmd', '.bat')) or PurePosixPath(p).name.startswith('Dockerfile')]
    tree.preload(interesting)

    def add(path, kind, identity, signal, source=None):
        safe_path(path)
        require(nonblank(identity), 'invalid-surface-identity')
        key = (repository, path, kind, identity)
        candidate = candidates.setdefault(key, {'surface': dict(zip(('repository', 'path', 'kind', 'identity'), key)), 'signals': set(), 'sources': set()})
        candidate['signals'].add(signal)
        candidate['sources'].add(source or path)

    for path in sorted(p for p in paths if PROJECT.search(p)):
        with inspection(path):
            values, references, documents, linked = project_metadata(tree, path, set(paths), errors)
            sdks = sdk_identities(tree, path)
            project_id = PurePosixPath(path).stem
            signals = set()
            if IDENTITY.search(project_id):
                signals.add('project-identity')
            if any(IDENTITY.search(value) for value in values['_DeclaredIdentity']):
                signals.add('package-identity')
            if any(value.lower() == 'true' for value in values.get('PackAsTool', set())):
                signals.add('packed-tool')
            if values.get('ToolCommandName'):
                signals.add('tool-command')
            if any(IDENTITY.search(value) for value in values.get('ContainerRepository', set())):
                signals.add('container-identity')
            executable = any(value.lower() in ('exe', 'winexe') for value in values.get('OutputType', set()))
            web = 'microsoft.net.sdk.web' in sdks
            apphost = 'aspire.apphost.sdk' in sdks
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
        with inspection(path):
            if path.lower().endswith(('.props', '.targets')) and path not in consumed:
                document = xml(tree.text(path), path)
                local_properties = {}
                for element in document.iter():
                    if (element.text or '').strip() and not list(element):
                        local_properties.setdefault(local_name(element).lower(), set()).update(
                            expanded_values(element.text.strip(), local_properties, path, path, required=False))
                for element in document.iter():
                    name, value = local_name(element).lower(), (element.text or '').strip()
                    reference = attribute(element, 'Include') or attribute(element, 'Update') or ''
                    choices = expanded_values(value, local_properties, path, path, required=name in PROPERTY_NAMES)
                    reference_choices = expanded_values(reference, local_properties, path, path, required=name == 'packagereference')
                    if name == 'projectreference':
                        require(all('$(' not in PurePosixPath(choice.replace('\\', '/')).name for choice in reference_choices), f'unresolved-classification-metadata:{path}')
                    if (name == 'outputtype' and any(choice.lower() in ('exe', 'winexe') for choice in choices)
                            or name == 'packastool' and any(choice.lower() == 'true' for choice in choices)
                            or name == 'toolcommandname' and any(choices)
                            or name == 'containerrepository' and any(IDENTITY.search(choice) for choice in choices)
                            or name == 'packagereference' and any(choice.lower() == 'system.commandline' or re.search(r'ModelContextProtocol', choice, re.I) or IDENTITY.search(choice) for choice in reference_choices)
                            or name == 'projectreference' and any(IDENTITY.search(PurePosixPath(choice.replace('\\', '/')).stem) for choice in reference_choices)):
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
        with inspection(path):
            text = tree.text(path)
            signals = []
            if re.search(REGISTRATION.pattern, text, re.I if path.lower().endswith('.vb') else 0):
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
        for target in sorted(metadata['linked']):
            with inspection(target):
                text = tree.text(target)
                for signal, pattern in [('mcp-registration', REGISTRATION), ('command-line-source', COMMAND)]:
                    if re.search(pattern.pattern, text, re.I if target.lower().endswith('.vb') else 0):
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
            matches = ({project for project, metadata in projects.items() if image_repository(identity) in declared_container_repositories(metadata)}
                       if signal == 'container-image' else identities.get(identity.lower(), set()))
            if matches and not any(projects[p]['signals'] for p in matches):
                return
        add(path, 'publication', identity, signal)

    for path in interesting:
        with inspection(path):
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
                for document in json_documents(document, path):
                    if 'project' in document:
                        identity = document.get('packageId') or document.get('package_id') or document.get('id') or document.get('name') or document['project']
                        publication(path, identity, document['project'])
                    elif 'image' in document and isinstance(document['image'], str):
                        publication(path, document['image'], signal='container-image')
                    for section in ('mcpServers', 'servers'):
                        if section not in document:
                            continue
                        servers = document[section]
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
            elif path in shell_scripts or path.endswith(('.yml', '.yaml', '.sh', '.ps1', '.cmd', '.bat')) or PurePosixPath(path).name.startswith('Dockerfile'):
                if path.endswith(('.yml', '.yaml')) and not (path.startswith('.github/workflows/') or re.search(r'''(?m)\b(?:image|images|newName|kind|container|containers|services)["']?\s*:|\b(?:dotnet|docker|podman)\s''', text)):
                    continue
                # Every literal project invocation and proprietary package/container
                # identity is checked, including orphan entries after source removal.
                text = logical_commands(text)
                if path.startswith('.github/workflows/'):
                    text = expand_workflow_projects(text, path)
                for target in static_project_targets(tree, text, path, errors):
                    if target in projects:
                        publication(path, target, target, 'project-publication-reference')
                    else:
                        publication(path, target, target, 'orphan-project-reference')
                text = re.sub(r'\$\{\{.*?\}\}', '', text, flags=re.S)
                # Keep image scalars on their own line. A mapping's repository
                # belongs to that image block, never to a following YAML key.
                lines = text.splitlines()
                # YAML flow mappings share the same image/newName keys as block
                # mappings. Limit values to literal scalars and keep exact identity.
                for match in re.finditer(r'''(?:^|[\n{,])[ \t]*(?:-[ \t]*)?["']?(?:image|newName)["']?[ \t]*:[ \t]*["']?([A-Za-z0-9][A-Za-z0-9_./:@-]*)''', text):
                    identity = match[1]
                    if not identity.endswith(':'):
                        publication(path, identity, signal='container-image')
                for match in re.finditer(r'''["']?image["']?[ \t]*:[ \t]*\{[^{}\n]*?["']?repository["']?[ \t]*:[ \t]*["']?([A-Za-z0-9][A-Za-z0-9_./:@-]*)''', text):
                    publication(path, match[1], signal='container-image')
                if path.endswith(('.yml', '.yaml')):
                    for identity in build_action_images(lines):
                        publication(path, identity, signal='container-image')

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
                            while following and following[0].startswith('-'):
                                option = following.pop(0)
                                if option in ('--context', '-c', '--host', '-H', '--config', '--log-level', '-l') and following:
                                    following.pop(0)
                            if following[:1] == ['image']:
                                following = following[1:]
                            if not following:
                                continue
                            if following[0] == 'push' and len(following) > 1:
                                value = next((value for value in following[1:] if not value.startswith('-')), '')
                                if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./:@-]*', value):
                                    publication(path, value, signal='container-image')
                            elif following[0] == 'build' or following[:2] == ['buildx', 'build']:
                                for offset, value in enumerate(following):
                                    identity = (following[offset + 1] if value in ('-t', '--tag') and offset + 1 < len(following)
                                                else value.partition('=')[2] if value.startswith(('--tag=', '-t=')) else '')
                                    if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./:@-]*', identity):
                                        publication(path, identity, signal='container-image')
                tokens = set(re.findall(r'(?<![\w.])([A-Za-z][A-Za-z0-9_.-]*(?:[.-](?:mcp|cli)))(?![\w.])', text, re.I))
                for token in tokens:
                    publication(path, token, signal='package-or-container-reference')
    errors.sort(key=lambda error: (error['path'], error['rule'], error.get('target', '')))
    return candidates, sorted(p for p, entry in tree.entries.items() if entry[0] == '160000'), excluded, errors


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
            candidates, nested, scoped, source_errors = scan_tree(tree, repository, exclusions)
            if source_errors:
                summary['status'] = 'failed'
                summary['inspectionComplete'] = False
                report['errors'].extend({'repository': repository, 'gitlink': gitlink, **error} for error in source_errors)
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
                elif (key[2] == 'publication' and set(candidate['signals']) <= {'tool-install', 'tool-manifest', 'package-or-container-reference'}
                      and not (PurePosixPath(key[1]).name == 'package.json' and 'tool-manifest' in candidate['signals'])
                      and any(t['identity'].lower() == key[3].lower() for t in policy['toolIdentities'])):
                    tool = next(t for t in policy['toolIdentities'] if t['identity'].lower() == key[3].lower())
                    entry.update(status='approved', classification=tool['classification'], row=tool['row'])
                elif allowance:
                    extra = set(candidate['signals']) - set(allowance['signals'])
                    try:
                        source_changes = [source['path'] for source in allowance.get('sources', [])
                                          if source['path'] not in tree.entries or digest(tree.blob(source['path'])) != source['sha256']]
                        if 'sourcePrefix' in allowance:
                            prefix = allowance['sourcePrefix'] + '/'
                            expected_paths = {source['path'] for source in allowance['sources']}
                            actual_paths = ({source['path'] for source in compilation_closure(tree, allowance['surface']['path'])}
                                            if allowance.get('compilationClosure') else {path for path in tree.entries if path.startswith(prefix)})
                            source_changes = sorted(set(source_changes) | (expected_paths ^ actual_paths))
                    except (CensusError, OSError, UnicodeError) as error:
                        source_changes = None
                        summary['status'] = 'failed'
                        summary['inspectionComplete'] = False
                        report['errors'].append({'repository': repository, 'gitlink': gitlink, 'path': key[1],
                            'rule': str(error) if isinstance(error, CensusError) else 'source-read-failed'})
                    if source_changes is None:
                        entry.update(status='rejected', classification=allowance['classification'], row=allowance['row'],
                                     reason='allowance-source-inspection-failed')
                    elif extra or source_changes:
                        entry.update(status='rejected', classification=allowance['classification'], row=allowance['row'],
                                     reason='allowance-signal-or-source-drift', unexpectedSignals=sorted(extra), changedSources=source_changes)
                    else:
                        entry.update(status='approved', classification=allowance['classification'], row=allowance['row'])
                else:
                    entry.update(status='rejected', classification='unapproved', reason='new-proprietary-surface')
                report['surfaces'].append(entry)
                if entry['status'] == 'rejected':
                    summary['status'] = 'failed'
            if summary.get('inspectionComplete', True):
                inspected.add(repository)
        except (CensusError, OSError, UnicodeError) as error:
            summary['status'] = 'failed'
            summary['inspectionComplete'] = False
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
