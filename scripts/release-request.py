#!/usr/bin/env python3
"""Fail closed on unsupported release requests and uncertain registry state."""

import argparse
import json
import os
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
    from paired_release import module
    repository = os.environ['REPOSITORY']
    try:
        marker = module('verify-release-source').github_json(
            f'repos/{repository}/git/matching-refs/tags/mcpcli-paired-publication-started')
    except (ValueError, OSError, subprocess.CalledProcessError):
        raise ValueError('Could not confirm bootstrap publication line: uncertain repository response') from None
    if marker != []:
        raise ValueError('Independent bootstrap publication is closed after paired publication starts.')


def check_bootstrap_recovery_line(version, sha):
    from paired_release import module
    gate = module('verify-release-source')
    repository = os.environ['REPOSITORY']
    marker = 'mcpcli-paired-publication-started'
    endpoint = f'repos/{repository}/git/matching-refs/tags/'
    references = gate.github_json(endpoint + marker)
    if references == []:
        return  # No paired publication has ever started.
    if not isinstance(references, list):
        raise ValueError('Could not confirm historical bootstrap recovery: uncertain publication state.')
    global_markers = [item for item in references if item.get('ref') == 'refs/tags/' + marker]
    if (len(global_markers) != 1 or global_markers[0].get('object', {}).get('type') != 'commit'
            or re.fullmatch('[0-9a-f]{40}', global_markers[0]['object'].get('sha', '')) is None):
        raise ValueError('Could not confirm historical bootstrap recovery: first-pair marker is missing or invalid.')
    version_ref = 'refs/tags/' + marker + '-v' + version
    version_markers = gate.github_json(endpoint + marker + '-v' + version)
    if not isinstance(version_markers, list) or any(item.get('ref') == version_ref for item in version_markers):
        raise ValueError('Paired release versions cannot use bootstrap recovery.')
    first_pair = global_markers[0]['object']['sha']
    ancestor = subprocess.run(['git', 'merge-base', '--is-ancestor', sha, first_pair], capture_output=True)
    if sha == first_pair or ancestor.returncode != 0:
        raise ValueError('Bootstrap recovery is limited to historical versions preceding paired publication.')


def check_registry(version: str, phase='bootstrap') -> None:
    if not os.environ.get("NUGET_API_KEY", "").strip():
        raise ValueError("NuGet publication key is required")
    if phase == 'bootstrap':
        if version_is_published(version):
            raise ValueError(f"Hexalith.McpCli.Abstractions {version} is already published")
        if not os.environ.get('MCPCLI_RECOVERY_VERSION'):
            check_bootstrap_line()
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
    parser.add_argument("--registry", action="store_true")
    args = parser.parse_args()
    try:
        validate_request(args.version, args.phase)
        if args.registry:
            check_registry(args.version, args.phase)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
