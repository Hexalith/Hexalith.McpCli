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

if [ "$release_phase" = paired ]; then
  smoke_directory="$(mktemp -d)"
  trap 'rm -rf "$smoke_directory"' EXIT
  cat > "$smoke_directory/NuGet.Config" <<EOF
<?xml version="1.0" encoding="utf-8"?>
<configuration><packageSources><clear/><add key="staged" value="$(pwd)/$staging_directory" /></packageSources></configuration>
EOF
  dotnet tool install Hexalith.McpCli --tool-path "$smoke_directory/bin" \
    --version "$release_version" --configfile "$smoke_directory/NuGet.Config" --no-cache
  version_output="$("$smoke_directory/bin/hexalith" --version)"
  if [[ "$version_output" != "$release_version" && "$version_output" != "$release_version"+* ]]; then
    echo "Staged hexalith reported version $version_output, expected $release_version." >&2
    exit 1
  fi
  "$smoke_directory/bin/hexalith" config current > /dev/null
  "$smoke_directory/bin/hexalith" modules > /dev/null
fi
