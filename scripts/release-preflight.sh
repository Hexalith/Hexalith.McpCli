#!/usr/bin/env bash
set -euo pipefail

release_version="${1:?Release version is required}"
release_phase="${MCPCLI_RELEASE_PHASE:?Release phase is required}"
: "${NUGET_API_KEY:?NuGet publication key is required}"

case "$release_phase" in
  bootstrap) ;;
  paired)
    echo "Paired release is deferred until the tool, FR-22, and live gates are implemented." >&2
    exit 1
    ;;
  *) echo "Unknown release phase: $release_phase" >&2; exit 1 ;;
esac

if [[ ! "$release_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]]; then
  echo "Invalid release version: $release_version" >&2
  exit 1
fi

python3 - "$release_version" <<'PY'
import json
import sys
from urllib.error import HTTPError
from urllib.request import urlopen

version = sys.argv[1]
url = "https://api.nuget.org/v3-flatcontainer/hexalith.mcpcli.abstractions/index.json"
try:
    with urlopen(url, timeout=30) as response:
        if response.status != 200:
            raise ValueError(f"Unexpected NuGet registry status: {response.status}")
        index = json.load(response)
except HTTPError as error:
    if error.code == 404:
        sys.exit(0)  # The package ID has not been published yet.
    raise SystemExit(f"Could not confirm the NuGet version is free: HTTP {error.code}") from error
except Exception as error:
    raise SystemExit(f"Could not confirm the NuGet version is free: {error}") from error

versions = index.get("versions") if isinstance(index, dict) else None
if not isinstance(versions, list) or not all(isinstance(item, str) for item in versions):
    raise SystemExit("Could not confirm the NuGet version is free: invalid version index")
if version.lower() in {item.lower() for item in versions}:
    raise SystemExit(f"Hexalith.McpCli.Abstractions {version} is already published")
PY
