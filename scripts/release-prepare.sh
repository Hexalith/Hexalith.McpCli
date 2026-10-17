#!/usr/bin/env bash
set -euo pipefail

release_version="${1:?Release version is required}"
release_phase="${MCPCLI_RELEASE_PHASE:?Release phase is required}"
python3 scripts/release-request.py "$release_version" "$release_phase"
if [ "$#" -gt 2 ] || { [ "$#" -eq 2 ] && [ "$2" != --verify-source ]; }; then
  echo "Usage: release-prepare.sh VERSION [--verify-source]" >&2
  exit 1
fi

staging_directory="nupkgs/bootstrap"
receipt="nupkgs/bootstrap.sha256"
if [ -e "$staging_directory" ] || [ -L "$staging_directory" ] || [ -e "$receipt" ] || [ -L "$receipt" ]; then
  echo "Bootstrap staging or its receipt already exists; use a fresh checkout or preserve it elsewhere first." >&2
  exit 1
fi
source_provenance="$(python3 scripts/release-receipt.py capture)"
mkdir -p nupkgs
mkdir "$staging_directory"
prepared=false
consumer_root="$(mktemp -d)"
trap 'rm -rf "$consumer_root"; if [ "$prepared" = false ]; then rm -rf "$staging_directory"; fi' EXIT

project="src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj"
dotnet restore "$project" -p:Version="$release_version"
dotnet build "$project" --configuration Release --no-restore -warnaserror -p:Version="$release_version"
dotnet pack "$project" --configuration Release --no-build -p:Version="$release_version" --output "$staging_directory"
python3 scripts/validate-release-packages.py "$staging_directory" "$release_version" "$release_phase"
bash scripts/smoke-bootstrap-consumer.sh "$release_version" "$PWD/$staging_directory" "$consumer_root/consumer"
package_hash="$(sha256sum "$staging_directory/Hexalith.McpCli.Abstractions.$release_version.nupkg" | cut -d ' ' -f 1)"
if [ "${2:-}" = --verify-source ]; then
  python3 scripts/verify-release-source.py "${DISPATCH_SHA:?Exact release SHA is required}" \
    "${DISPATCH_REF:?Release dispatch ref is required}" "$release_phase"
fi
receipt_contents="$(python3 scripts/release-receipt.py record "$source_provenance" \
  "$staging_directory/Hexalith.McpCli.Abstractions.$release_version.nupkg")"
(set -o noclobber; printf '%s\n' "$receipt_contents" > "$receipt")
prepared=true
printf 'Prepared Hexalith.McpCli.Abstractions %s SHA-256 %s\n' "$release_version" "$package_hash"
