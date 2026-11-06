#!/usr/bin/env python3
"""Fail closed on unsupported release requests and uncertain registry state."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError
from urllib.request import urlopen


def validate_request(version: str, phase: str) -> None:
    if phase not in ("bootstrap", "paired"):
        raise ValueError(f"Unknown release phase: {phase}")
    validate_version(version)


def validate_version(version: str) -> None:
    # NuGet drops build metadata from package identity; semantic-release emits none.
    numeric = r"(?:0|[1-9][0-9]*)"
    identifier = rf"(?:{numeric}|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    if re.fullmatch(rf"{numeric}\.{numeric}\.{numeric}(?:-{identifier}(?:\.{identifier})*)?", version) is None:
        raise ValueError(f"Invalid release version: {version}")
    if any(len(component) > 10 or int(component) > 2_147_483_647
           for component in version.split('-', 1)[0].split('.')):
        raise ValueError(f"Invalid release version: {version}; numeric components exceed the NuGet limit")


def registry_versions(package_id='Hexalith.McpCli.Abstractions', allow_first_absence=False):
    url = f"https://api.nuget.org/v3-flatcontainer/{package_id.lower()}/index.json"
    try:
        with urlopen(url, timeout=30) as response:
            if response.status != 200:
                raise ValueError(f"unexpected HTTP {response.status}")
            index = json.load(response)
    except HTTPError as error:
        error.close()
        if error.code == 404 and allow_first_absence:
            # A new package ID has no version index. Independently require the
            # registration identity to be absent too; any other response is uncertain.
            registration = f'https://api.nuget.org/v3/registration5-gz-semver2/{package_id.lower()}/index.json'
            try:
                with urlopen(registration, timeout=30):
                    pass
            except HTTPError as registration_error:
                registration_error.close()
                if registration_error.code == 404:
                    return []
            except Exception:
                pass
            raise ValueError(f'Could not confirm first-ever package absence for {package_id}') from None
        raise ValueError(f"Could not confirm the NuGet version is free: HTTP {error.code}") from None
    except Exception:
        raise ValueError("Could not confirm the NuGet version is free: uncertain registry response") from None

    versions = index.get("versions") if isinstance(index, dict) else None
    if not isinstance(versions, list) or not versions or not all(isinstance(item, str) for item in versions):
        raise ValueError("Could not confirm the NuGet version is free: invalid version index")
    try:
        for item in versions:
            validate_version(item)
    except ValueError:
        raise ValueError("Could not confirm the NuGet version is free: invalid version index") from None
    return versions


def version_is_published(version: str) -> bool:
    return version.lower() in {item.lower() for item in registry_versions()}


def check_bootstrap_line():
    if registry_versions('Hexalith.McpCli', allow_first_absence=True):
        raise ValueError('Independent bootstrap publication is closed: Hexalith.McpCli is already public on NuGet.')
    from paired_release import module
    try:
        marker = module('verify-release-source').github_json(
            f"repos/{os.environ['REPOSITORY']}/git/matching-refs/tags/mcpcli-paired-publication-started")
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError):
        raise ValueError('Could not confirm bootstrap publication line: uncertain repository response') from None
    if marker != []:
        raise ValueError('Independent bootstrap publication is closed after paired publication starts.')


def historical_sha(version):
    validate_version(version)
    try:
        history = json.loads(Path(__file__).with_name('bootstrap-history.json').read_text())
        if history['schema'] != 'mcpcli-bootstrap-history/v1' or not isinstance(history['releases'], dict):
            raise ValueError('Bootstrap history is missing or invalid.')
        release = history['releases'].get(version)
        if release is None:
            raise ValueError(f'Bootstrap recovery version {version} is not in the fixed historical allowlist.')
        if (release['tag'] != 'v' + version
                or re.fullmatch('[0-9a-f]{40}', release['source_sha']) is None):
            raise ValueError('Bootstrap history is missing or invalid.')
        return release['source_sha']
    except (KeyError, TypeError, OSError, json.JSONDecodeError):
        raise ValueError('Bootstrap history is missing or invalid.') from None


def validate_dispatch(version, phase):
    if phase == 'paired':
        if version:
            raise ValueError('Paired recovery is unsupported; preserve outcomes for evidence-based recovery.')
        return
    if phase != 'bootstrap':
        raise ValueError(f'Unknown release phase: {phase}')
    if not version:
        raise ValueError('Ordinary bootstrap dispatch is closed; an explicit historical recovery version is required.')
    sha = historical_sha(version)
    from paired_release import module
    gate = module('verify-release-source')
    repository = os.environ['REPOSITORY']
    live_main = gate.github_json(f'repos/{repository}/git/ref/heads/main')['object']['sha']
    gate.verify_recovery_tag(version, sha, repository, live_main)
    if not version_is_published(version):
        raise ValueError(f'Historical bootstrap recovery requires already-public Hexalith.McpCli.Abstractions {version}; publication is forbidden.')


def check_registry(version: str, phase='bootstrap') -> None:
    if not os.environ.get("NUGET_API_KEY", "").strip():
        raise ValueError("NuGet publication key is required")
    if phase == 'bootstrap':
        check_bootstrap_line()
        if version_is_published(version):
            raise ValueError(f"Hexalith.McpCli.Abstractions {version} is already published")
        return
    # Check both identities before the first push, including a confirmed first-ever tool absence.
    for identity in ('Hexalith.McpCli.Abstractions', 'Hexalith.McpCli'):
        versions = registry_versions(identity, allow_first_absence=True)
        if version.lower() in {item.lower() for item in versions}:
            raise ValueError(f'{identity} {version} is already published')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("phase")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--registry", action="store_true")
    mode.add_argument("--dispatch", action="store_true")
    mode.add_argument("--historical-sha", action="store_true")
    args = parser.parse_args()
    try:
        if args.dispatch:
            validate_dispatch(args.version, args.phase)
        else:
            validate_request(args.version, args.phase)
        if args.historical_sha:
            print(historical_sha(args.version))
        elif args.registry:
            check_registry(args.version, args.phase)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        from paired_release import module
        error = module('verify-release-source').failure_detail(error)
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
