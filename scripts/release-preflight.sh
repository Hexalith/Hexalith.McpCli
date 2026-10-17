#!/usr/bin/env bash
set -euo pipefail

release_version="${1:?Release version is required}"
release_phase="${MCPCLI_RELEASE_PHASE:?Release phase is required}"
python3 scripts/release-request.py "$release_version" "$release_phase" --registry
