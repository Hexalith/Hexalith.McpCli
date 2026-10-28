#!/usr/bin/env bash
set -euo pipefail
bash -n tools/live-topology/prepare-ci.sh tools/live-topology/run-ci.sh
actionlint .github/workflows/ci.yml
git diff --check -- README.md tools/live-topology/README.md tools/live-topology/ci.py tools/live-topology/test_ci.py
