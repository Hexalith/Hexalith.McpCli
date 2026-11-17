#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
task_dir="$(mktemp -d)"
trap 'rm -rf "$task_dir"' EXIT
cd "$repo_root"

artifact_dir="$task_dir/feed"
mkdir -p "$artifact_dir"
dotnet pack src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj \
    --configuration Release --no-build --no-restore -p:Version=1.0.0 --output "$artifact_dir" -m:1
dotnet pack tests/Hexalith.McpCli.Sample.Contracts/Hexalith.McpCli.Sample.Contracts.csproj \
    --configuration Release --no-build --no-restore -p:IsPackable=true -p:Version=1.0.0 --output "$artifact_dir" -m:1

# Compile only this distinct sample-mode fixture. Its copied sources, outputs
# and package cache cannot change the shared production host or its assets.
fixture_root="$task_dir/sample"
python3 - "$repo_root" "$fixture_root" <<'PYTHON'
from pathlib import Path
import shutil, sys
repo, target = map(Path, sys.argv[1:])
for name in ('src', 'tests/Hexalith.McpCli.ConformanceHost', 'tests/Hexalith.McpCli.Core.Tests'):
    shutil.copytree(repo / name, target / name, ignore=shutil.ignore_patterns('bin', 'obj', '.git', '__pycache__'))
for name in ('Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props', 'global.json', '.editorconfig'):
    if (repo / name).exists(): shutil.copy2(repo / name, target / name)
sys.path.insert(0, str(repo / 'tools/conformance-vectors/v1'))
from verify_artifact import resolve_builds_props
shutil.copytree(resolve_builds_props(repo), target.parent / 'Hexalith.Builds/Props')
PYTHON
host_project="$fixture_root/tests/Hexalith.McpCli.ConformanceHost/Hexalith.McpCli.ConformanceHost.csproj"
NUGET_PACKAGES="$task_dir/packages" NUGET_HTTP_CACHE_PATH="$task_dir/http-cache" dotnet restore "$host_project" \
    -p:ConformanceProduction=false -p:RestoreAdditionalProjectSources="$artifact_dir"
NUGET_PACKAGES="$task_dir/packages" NUGET_HTTP_CACHE_PATH="$task_dir/http-cache" dotnet build "$host_project" \
    --configuration Release --no-restore -m:1 -warnaserror -p:ConformanceProduction=false

artifact="$artifact_dir/Hexalith.McpCli.Sample.Contracts.1.0.0.nupkg"
vectors=(tools/conformance-vectors/v1/sample-command.json
         tools/conformance-vectors/v1/sample-query.json
         tools/conformance-vectors/v1/sample-rename.json)
python3 tools/conformance-vectors/v1/validate.py \
    --artifact "$artifact" \
    --expected-package-id Hexalith.McpCli.Sample.Contracts \
    --expected-package-version 1.0.0 "${vectors[@]}"
python3 tools/conformance-vectors/v1/run_loopback.py \
    --host "$fixture_root/tests/Hexalith.McpCli.ConformanceHost/bin/Release/net11.0/Hexalith.McpCli.ConformanceHost.dll" \
    --artifact "$artifact" \
    --expected-package-id Hexalith.McpCli.Sample.Contracts \
    --expected-package-version 1.0.0 "${vectors[@]}"
python3 tools/conformance-vectors/v1/run_packaged_process_fixture.py --artifact "$artifact"
