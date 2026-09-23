#!/usr/bin/env bash
set -euo pipefail

release_version="${1:?Release version is required}"
release_phase="${MCPCLI_RELEASE_PHASE:?Release phase is required}"
staging_directory="nupkgs"

mkdir -p "$staging_directory"
dotnet restore Hexalith.McpCli.slnx -p:Version="$release_version"
dotnet build Hexalith.McpCli.slnx --configuration Release --no-restore -p:Version="$release_version"
dotnet pack src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj \
  --configuration Release --no-build -p:Version="$release_version" --output "$staging_directory"

if [ "$release_phase" = paired ]; then
  dotnet pack src/Hexalith.McpCli/Hexalith.McpCli.csproj \
    --configuration Release --no-build -p:Version="$release_version" --output "$staging_directory"
fi

python3 scripts/validate-release-packages.py "$staging_directory" "$release_version" "$release_phase"
