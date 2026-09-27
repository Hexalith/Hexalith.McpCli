#!/usr/bin/env python3
"""Validate exact staged IDs, versions, and bootstrap dependency closure."""

import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


def main() -> int:
    if len(sys.argv) != 4:
        raise ValueError("Usage: validate-release-packages.py STAGING VERSION PHASE")

    staging = Path(sys.argv[1])
    version = sys.argv[2]
    phase = sys.argv[3]
    packages = json.loads(Path("tools/release-packages.json").read_text())["packages"]
    expected_ids = [package["id"] for package in packages]
    if expected_ids != ["Hexalith.McpCli.Abstractions", "Hexalith.McpCli"]:
        raise ValueError("The release manifest must declare exactly the paired package IDs")
    if phase not in {"bootstrap", "paired"}:
        raise ValueError(f"Unknown release phase: {phase}")

    active_ids = expected_ids[:1] if phase == "bootstrap" else expected_ids
    expected_names = {f"{package_id}.{version}.nupkg" for package_id in active_ids}
    actual_names = {path.name for path in staging.glob("*.nupkg")}
    if actual_names != expected_names:
        raise ValueError(f"Expected {sorted(expected_names)}, found {sorted(actual_names)}")

    for package_id in active_ids:
        path = staging / f"{package_id}.{version}.nupkg"
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            if package_id.endswith(".Abstractions") and (
                "lib/net10.0/Hexalith.McpCli.Abstractions.dll" not in names
            ):
                raise ValueError("Abstractions package is missing its net10.0 compile DLL")
            if package_id.endswith(".Abstractions") and (
                "analyzers/dotnet/cs/Hexalith.McpCli.Analyzers.dll" not in names
            ):
                raise ValueError("Abstractions package is missing its C# analyzer DLL")
            nuspec_names = [name for name in names if name.endswith(".nuspec")]
            if len(nuspec_names) != 1:
                raise ValueError(f"{path} must contain one nuspec")
            root = ElementTree.fromstring(archive.read(nuspec_names[0]))
            metadata = root.find("{*}metadata")
            if metadata is None or metadata.findtext("{*}id") != package_id:
                raise ValueError(f"Unexpected package ID in {path}")
            if metadata.findtext("{*}version") != version:
                raise ValueError(f"Unexpected package version in {path}")
            if package_id.endswith(".Abstractions") and metadata.findall(".//{*}dependency"):
                raise ValueError("Abstractions must have no consumer-visible package dependencies")
            if package_id == "Hexalith.McpCli":
                validate_tool_package(archive, names, metadata)

    print(f"Validated {phase} packages at version {version}")
    return 0


def validate_tool_package(archive: ZipFile, names: set[str], metadata: ElementTree.Element) -> None:
    prefix = "tools/net10.0/any/"
    required = {
        "README.md",
        prefix + "DotnetToolSettings.xml",
        prefix + "Hexalith.McpCli.dll",
        prefix + "Hexalith.McpCli.deps.json",
        prefix + "Hexalith.McpCli.runtimeconfig.json",
    }
    missing = required - names
    if missing:
        raise ValueError(f"McpCli tool package is missing {sorted(missing)}")
    if metadata.find(".//{*}packageType[@name='DotnetTool']") is None:
        raise ValueError("McpCli package is not marked as a .NET tool")
    command = ElementTree.fromstring(archive.read(prefix + "DotnetToolSettings.xml")).find(".//Command")
    if command is None or command.attrib != {
        "Name": "hexalith", "EntryPoint": "Hexalith.McpCli.dll", "Runner": "dotnet"
    }:
        raise ValueError("McpCli tool command is not hexalith")

    manifest = Path("src/Hexalith.McpCli/obj/Release/net10.0/ModuleAssemblyManifest.g.cs")
    if not manifest.is_file():
        raise ValueError("The generated Contracts assembly manifest is missing")
    entries = re.findall(r'\("([^"]+)", "([^"]+)"\)', manifest.read_text(encoding="utf-8"))
    if not entries:
        raise ValueError("The paired tool release has no enrolled Contracts assemblies")
    for package_id, assembly_name in entries:
        if not package_id.endswith(".Contracts") or not assembly_name.endswith(".Contracts"):
            raise ValueError(f"Invalid Contracts assembly manifest entry: {package_id}, {assembly_name}")
        if prefix + assembly_name + ".dll" not in names:
            raise ValueError(f"McpCli tool package is missing {assembly_name}.dll")


if __name__ == "__main__":
    raise SystemExit(main())
