#!/usr/bin/env python3
"""Build the isolated analyzer consumer from the verified package source."""

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit
from xml.etree import ElementTree

from product_packages import bootstrap_target_framework, validate_version


SOURCES = {
    'Module.cs': """using Hexalith.McpCli.Abstractions;
[assembly: HexalithModule("sample", "Consumer sample", IdentifierKind.Ulid)]
""",
    'CreateItemCommand.cs': """using Hexalith.McpCli.Abstractions;
[HexalithCommand("Create a sample item.", Domain = "sample", WireType = "create-item", AggregateIdProperty = nameof(Id))]
public sealed record CreateItemCommand([property: HexalithIdentifier] string Id);
""",
    'GetItemQuery.cs': """using Hexalith.McpCli.Abstractions;
[HexalithQuery("Read a sample item.", Domain = "sample", WireType = "get-item", AggregateIdProperty = nameof(Id), ProjectionType = "items")]
public sealed record GetItemQuery([property: HexalithIdentifier] string Id);
""",
    'MissingDescriptionQuery.cs': """using Hexalith.McpCli.Abstractions;
[HexalithQuery(" ")]
public sealed record MissingDescriptionQuery;
""",
}


def smoke(version, source, directory):
    validate_version(version)
    if urlsplit(source).scheme not in ('http', 'https'):
        source = str(Path(source).resolve())
    directory = directory.resolve()
    directory.mkdir()
    shutil.copyfile('global.json', directory / 'global.json')

    configuration = ElementTree.Element('configuration')
    sources = ElementTree.SubElement(configuration, 'packageSources')
    ElementTree.SubElement(sources, 'clear')
    ElementTree.SubElement(sources, 'add', key='verified', value=source)
    fallback = ElementTree.SubElement(configuration, 'fallbackPackageFolders')
    ElementTree.SubElement(fallback, 'clear')
    config = directory / 'NuGet.Config'
    ElementTree.ElementTree(configuration).write(config, encoding='utf-8', xml_declaration=True)

    framework = bootstrap_target_framework(version)
    project = directory / 'Bootstrap.Consumer.Contracts.csproj'
    project.write_text(
        f'<Project Sdk="Microsoft.NET.Sdk">\n'
        f'  <PropertyGroup><TargetFramework>{framework}</TargetFramework></PropertyGroup>\n'
        f'  <ItemGroup><PackageReference Include="Hexalith.McpCli.Abstractions" Version="[{version}]" /></ItemGroup>\n'
        f'</Project>\n', encoding='utf-8', newline='\n')
    for name, contents in SOURCES.items():
        (directory / name).write_text(contents, encoding='utf-8', newline='\n')

    packages = directory / 'packages'
    os.environ.update(NUGET_PACKAGES=str(packages), NUGET_FALLBACK_PACKAGES='',
                      NUGET_HTTP_CACHE_PATH=str(directory / 'http-cache'), DOTNET_CLI_UI_LANGUAGE='en')
    properties = (
        f'-p:RestoreSources={source}', f'-p:RestorePackagesPath={packages}',
        '-p:RestoreAdditionalProjectSources=', '-p:RestoreFallbackFolders=',
        '-p:RestoreAdditionalProjectFallbackFolders=', '-p:ImportDirectoryBuildProps=false',
        '-p:ImportDirectoryBuildTargets=false', '-p:ImportDirectoryPackagesProps=false',
    )
    restore = subprocess.run(['dotnet', 'restore', project, '--configfile', config, '--no-cache', '-tl:off', *properties])
    if restore.returncode:
        return 128 - restore.returncode if restore.returncode < 0 else restore.returncode
    log = directory / 'build.log'
    with log.open('wb') as output, subprocess.Popen(
            ['dotnet', 'build', project, '--configuration', 'Release', '--no-restore', '-tl:off', *properties],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as build:
        for line in build.stdout:
            output.write(line)
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
        status = build.wait()
    if status:
        return 128 - status if status < 0 else status

    contents = log.read_bytes()
    if re.search(rb'CS8032|CS9057', contents):
        raise ValueError('The packaged analyzer could not load in the consumer.')
    if not re.search(rb'MissingDescriptionQuery\.cs\([^)\r\n]*\): warning MCPCLI001:', contents):
        raise ValueError('The packaged analyzer did not report MCPCLI001 on MissingDescriptionQuery.cs.')
    if not any(re.fullmatch(rb'[ \t]*1 Warning\(s\)', line) for line in contents.splitlines()):
        raise ValueError('The packaged consumer must report exactly one warning.')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version')
    parser.add_argument('source')
    parser.add_argument('directory', type=Path)
    arguments = parser.parse_args()
    return smoke(arguments.version, arguments.source, arguments.directory)


if __name__ == '__main__':
    raise SystemExit(main())
