#!/usr/bin/env bash
set -euo pipefail
script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

release_version="${1:?Release version is required}"
release_phase="${MCPCLI_RELEASE_PHASE:?Release phase is required}"
if [ "$release_phase" = paired ]; then
  if [ -n "${MCPCLI_RECOVERY_VERSION:-}${RECOVERY_VERSION:-}" ]; then
    echo "Paired recovery is unsupported; preserve outcomes for evidence-based recovery." >&2
    exit 1
  fi
  python3 "$script_directory/verify-paired-publication.py" verify \
    --candidate "${MCPCLI_PAIRED_CANDIDATE:?Authenticated staging candidate is required}" \
    --operator "${MCPCLI_OPERATOR_ACCEPTANCE:?Candidate-specific operator acceptance is required}" \
    --actor "${GITHUB_ACTOR:?Authenticated operator decision actor is required}" \
    --staging-run "${MCPCLI_STAGING_RUN_ID:?Exact staging run is required}" \
    --source-sha "${DISPATCH_SHA:?Exact release SHA is required}" --version "$release_version" \
    --output "${MCPCLI_PAIRED_PREFLIGHT:?Fresh preflight receipt path is required}"
  exit
fi
python3 "$script_directory/release-request.py" --registry -- "$release_version" "$release_phase"
