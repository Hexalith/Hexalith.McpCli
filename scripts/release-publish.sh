#!/usr/bin/env bash
set -euo pipefail
script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [ "$#" -ne 1 ]; then
  echo "Usage: release-publish.sh VERSION" >&2
  exit 1
fi
release_version="${1:?Release version is required}"
release_phase="${MCPCLI_RELEASE_PHASE:?Release phase is required}"
if [ "$release_phase" = paired ]; then
  python3 "$script_directory/publish-paired-release.py" publish --version "$release_version"
  exit
fi
# Direct invocation must enforce the same request, credential and registry checks.
bash "$script_directory/release-preflight.sh" "$release_version"

staging_directory="nupkgs/bootstrap"
receipt="nupkgs/bootstrap.sha256"
python3 "$script_directory/validate-release-packages.py" -- "$staging_directory" "$release_version" "$release_phase"
# Snapshot before validating/hash checking, then push precisely those checked bytes.
publication_directory="$(mktemp -d)"
trap 'rm -rf "$publication_directory"' EXIT
package_name="Hexalith.McpCli.Abstractions.$release_version.nupkg"
cp "$staging_directory/$package_name" "$publication_directory/$package_name"
python3 "$script_directory/validate-release-packages.py" -- "$publication_directory" "$release_version" "$release_phase"
actual_hash="$(python3 "$script_directory/release-receipt.py" verify -- "$receipt" "$publication_directory/$package_name" \
  "${DISPATCH_SHA:?Exact release SHA is required}")"
# Ambient recovery variables never select historical source policy for a publisher.
python3 "$script_directory/verify-release-source.py" -- "${DISPATCH_SHA:?Exact release SHA is required}" \
  "${DISPATCH_REF:?Release dispatch ref is required}" "$release_phase"
printf 'Publishing %s SHA-256 %s\n' "$package_name" "$actual_hash"
dotnet nuget push "$publication_directory/$package_name" \
  --source https://api.nuget.org/v3/index.json --api-key "$NUGET_API_KEY"
