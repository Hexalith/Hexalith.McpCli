#!/usr/bin/env bash
set -euo pipefail

configuration="${1:-Debug}"
if (( $# > 1 )) || [[ "$configuration" != Debug && "$configuration" != Release ]]; then
    echo "Usage: bash tools/conformance-vectors/v1/run-sample-validation.sh [Debug|Release]" >&2
    exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
task_dir="$(mktemp -d)"
trap 'rm -rf "$task_dir"' EXIT
cd "$repo_root"

artifact_dir="$task_dir/feed"
dotnet pack tests/Hexalith.McpCli.Sample.Contracts/Hexalith.McpCli.Sample.Contracts.csproj \
    --configuration "$configuration" --artifacts-path "$task_dir/artifacts" \
    -p:IsPackable=true -p:Version=1.0.0 --output "$artifact_dir" -m:1

python3 -m unittest discover -s tools/conformance-vectors/v1 -p 'test_*.py'
artifact="$artifact_dir/Hexalith.McpCli.Sample.Contracts.1.0.0.nupkg"
python3 tools/conformance-vectors/v1/validate.py \
    --artifact "$artifact" \
    --expected-package-id Hexalith.McpCli.Sample.Contracts \
    --expected-package-version 1.0.0 \
    tools/conformance-vectors/v1/sample-command.json \
    tools/conformance-vectors/v1/sample-query.json \
    tools/conformance-vectors/v1/sample-rename.json
sha256sum "$artifact"
