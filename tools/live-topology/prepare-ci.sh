#!/usr/bin/env bash
# The reusable workflow initializes host Dapr before this bounded preparation hook.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
exec timeout --signal=TERM --kill-after=30s 2400 python3 tools/live-topology/ci.py prepare
