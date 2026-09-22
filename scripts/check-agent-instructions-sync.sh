#!/usr/bin/env sh
# Fails when the three agent instruction entry points are not byte-identical.
# Edit AGENTS.md, then copy it to CLAUDE.md and .github/copilot-instructions.md.
set -eu
cd "$(dirname "$0")/.."
status=0
for f in CLAUDE.md .github/copilot-instructions.md; do
  if ! cmp -s AGENTS.md "$f"; then
    echo "agent instructions out of sync: $f differs from AGENTS.md" >&2
    status=1
  fi
done
exit $status
