#!/usr/bin/env python3
"""Recheck committed FR-22 integration, containing baseline and synchronized entry points."""

import argparse
import json
import sys
import subprocess
from paired_release import digest, git, module, run, source, write_new

REQUIRED = '70dbf73e80787299c832d30d911b16b105ab194d'
BASELINE = 'references/Hexalith.AI.Tools'


def committed_baseline():
    declarations = git('config', '--blob', 'HEAD:.gitmodules', '--get-regexp', r'^submodule\..*\.path$')
    declared_paths = [line.split(None, 1)[1] for line in declarations.splitlines() if len(line.split(None, 1)) == 2]
    if declared_paths.count(BASELINE) != 1:
        raise ValueError('The committed root .gitmodules must declare the baseline exactly once.')
    entry = git('ls-tree', 'HEAD', '--', BASELINE)
    metadata, separator, path = entry.partition('\t')
    fields = metadata.split()
    if not separator or path != BASELINE or len(fields) != 3 or fields[:2] != ['160000', 'commit']:
        raise ValueError('The committed baseline must be a root submodule gitlink, not an ordinary file or directory.')
    return fields[2]


def verify():
    gate = module('verify-release-source')
    baseline = committed_baseline()
    if git('-C', BASELINE, 'rev-parse', 'HEAD') != baseline:
        raise ValueError('The baseline checkout differs from the committed root gitlink.')
    run(['git', '-C', BASELINE, 'merge-base', '--is-ancestor', REQUIRED, baseline])
    upstream = gate.github_json('repos/Hexalith/Hexalith.AI.Tools/git/ref/heads/main')['object']['sha']
    for revision in (REQUIRED, baseline):
        comparison = gate.github_json(f'repos/Hexalith/Hexalith.AI.Tools/compare/{revision}...{upstream}')
        if comparison.get('status') not in ('ahead', 'identical'):
            raise ValueError('Authoritative upstream main does not contain the required rule and committed baseline.')
    run(['bash', 'scripts/check-agent-instructions-sync.sh'])
    entries = ['AGENTS.md', 'CLAUDE.md', '.github/copilot-instructions.md']
    hashes = {path: digest(path) for path in entries}
    if len(set(hashes.values())) != 1:
        raise ValueError('Agent entry points differ.')
    return {'required_revision': REQUIRED, 'baseline_revision': baseline, 'upstream_main': upstream,
            'synchronization': hashes, **source()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        write_new(args.output, verify())
        return 0
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f'Paired prerequisite gate failed: {module("verify-release-source").failure_detail(error)}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
