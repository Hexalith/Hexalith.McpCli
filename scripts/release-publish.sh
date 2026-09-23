#!/usr/bin/env bash
set -euo pipefail

release_version="${1:?Release version is required}"
release_phase="${MCPCLI_RELEASE_PHASE:?Release phase is required}"
staging_directory="nupkgs"

python3 scripts/validate-release-packages.py "$staging_directory" "$release_version" "$release_phase"
dotnet nuget push "$staging_directory/Hexalith.McpCli.Abstractions.$release_version.nupkg" \
  --source https://api.nuget.org/v3/index.json --api-key "${NUGET_API_KEY:?NuGet publication key is required}"
if [ "$release_phase" = paired ]; then
  dotnet nuget push "$staging_directory/Hexalith.McpCli.$release_version.nupkg" \
    --source https://api.nuget.org/v3/index.json --api-key "$NUGET_API_KEY"
fi
