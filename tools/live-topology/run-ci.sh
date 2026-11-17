#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
exec timeout --signal=TERM --kill-after=30s 13800 python3 tools/live-topology/ci.py run
