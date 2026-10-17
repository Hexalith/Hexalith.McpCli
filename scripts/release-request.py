#!/usr/bin/env python3
"""Fail closed on unsupported release requests and uncertain registry state."""

import argparse
import json
import os
import re
from urllib.error import HTTPError
from urllib.request import urlopen


def validate_request(version: str, phase: str) -> None:
    if phase == "paired":
        raise ValueError("Paired release is deferred until the tool, FR-22, and live gates are implemented.")
    if phase != "bootstrap":
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


def version_is_published(version: str) -> bool:
    url = "https://api.nuget.org/v3-flatcontainer/hexalith.mcpcli.abstractions/index.json"
    try:
        with urlopen(url, timeout=30) as response:
            if response.status != 200:
                raise ValueError(f"unexpected HTTP {response.status}")
            index = json.load(response)
    except HTTPError as error:
        if error.code == 404:
            return False
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
    return version.lower() in {item.lower() for item in versions}


def check_registry(version: str) -> None:
    if not os.environ.get("NUGET_API_KEY", "").strip():
        raise ValueError("NuGet publication key is required")
    if version_is_published(version):
        raise ValueError(f"Hexalith.McpCli.Abstractions {version} is already published")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("phase")
    parser.add_argument("--registry", action="store_true")
    args = parser.parse_args()
    try:
        validate_request(args.version, args.phase)
        if args.registry:
            check_registry(args.version)
    except ValueError as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
