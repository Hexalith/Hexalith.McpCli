#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
task_dir="$(mktemp -d)"
trap 'rm -rf "$task_dir"' EXIT
cd "$repo_root"

artifact_dir="$task_dir/feed"
mkdir -p "$artifact_dir"
dotnet pack src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj \
    --configuration Release -p:Version=1.0.0 --output "$artifact_dir" -m:1
dotnet pack tests/Hexalith.McpCli.Sample.Contracts/Hexalith.McpCli.Sample.Contracts.csproj \
    --configuration Release -p:IsPackable=true -p:Version=1.0.0 --output "$artifact_dir" -m:1

host_project=tests/Hexalith.McpCli.ConformanceHost/Hexalith.McpCli.ConformanceHost.csproj
NUGET_PACKAGES="$task_dir/packages" dotnet restore "$host_project" \
    -p:RestoreAdditionalProjectSources="$artifact_dir" --force
NUGET_PACKAGES="$task_dir/packages" dotnet build "$host_project" \
    --configuration Release --no-restore -m:1

artifact="$artifact_dir/Hexalith.McpCli.Sample.Contracts.1.0.0.nupkg"
vectors=(tools/conformance-vectors/v1/sample-command.json
         tools/conformance-vectors/v1/sample-query.json
         tools/conformance-vectors/v1/sample-rename.json)
python3 -m unittest discover -s tools/conformance-vectors/v1 -p 'test_*.py'
python3 tools/conformance-vectors/v1/validate.py \
    --artifact "$artifact" \
    --expected-package-id Hexalith.McpCli.Sample.Contracts \
    --expected-package-version 1.0.0 "${vectors[@]}"
python3 tools/conformance-vectors/v1/run_loopback.py \
    --host tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll \
    --artifact "$artifact" \
    --expected-package-id Hexalith.McpCli.Sample.Contracts \
    --expected-package-version 1.0.0 "${vectors[@]}"
