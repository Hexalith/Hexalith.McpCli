#!/usr/bin/env bash
set -euo pipefail
script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [ "$#" -ne 1 ]; then
  echo "Usage: release-publish.sh VERSION" >&2
  exit 1
fi
release_version="${1:?Release version is required}"
release_phase="${MCPCLI_RELEASE_PHASE:?Release phase is required}"
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
printf 'Publishing %s SHA-256 %s\n' "$package_name" "$actual_hash"
source_args=()
if [ -n "${MCPCLI_RECOVERY_VERSION:-}" ]; then
  if [ "$MCPCLI_RECOVERY_VERSION" != "$release_version" ]; then
    echo "Recovery version does not match the prepared package." >&2
    exit 1
  fi
  source_args+=(--tagged-recovery "$release_version")
fi
python3 "$script_directory/verify-release-source.py" "${source_args[@]}" -- "${DISPATCH_SHA:?Exact release SHA is required}" \
  "${DISPATCH_REF:?Release dispatch ref is required}" "$release_phase"
dotnet nuget push "$publication_directory/$package_name" \
  --source https://api.nuget.org/v3/index.json --api-key "$NUGET_API_KEY"
