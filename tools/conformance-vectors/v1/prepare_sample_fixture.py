"""Copy sample replay inputs to private outputs without altering the built host."""

import argparse
from pathlib import Path
import shutil

from verify_artifact import resolve_builds_props


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('target', type=Path)
    arguments = parser.parse_args()
    source, target = arguments.source, arguments.target
    for name in ('src', 'tests/Hexalith.McpCli.ConformanceHost', 'tests/Hexalith.McpCli.Core.Tests'):
        shutil.copytree(source / name, target / name, ignore=shutil.ignore_patterns('bin', 'obj', '.git', '__pycache__'))
    for name in ('Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props', 'global.json', '.editorconfig'):
        if (source / name).exists():
            shutil.copy2(source / name, target / name)
    shutil.copytree(resolve_builds_props(source), target.parent / 'Hexalith.Builds/Props')


if __name__ == '__main__':
    main()
