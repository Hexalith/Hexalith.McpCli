# Story 4.15 code-review patches (2026-10-29)

This packet applies review patches P1–P5 and decision D1 from the
[spec's review findings](../../../spec-4-15-publish-the-no-new-server-rule.md#review-findings-code-review-2026-10-28).
It supersedes [parent-final](../parent-final/README.md) for the current
AI.Tools revision.

- **Upstream:** owning AI.Tools commit `70dbf73e80787299c832d30d911b16b105ab194d`
  (parent `5be77fc`) changes `README.md`, `hexalith-llm-instructions.md` and
  `hexalith-mcpcli-migration-instructions.md`.
  - It is published on authoritative `main`; `git ls-remote` and the GitHub
    commit API both resolve it.
  - Its exact message passed the pinned AI.Tools commitlint 21.2.2 on Node
    v26.4.0, and a malformed control was rejected.
  - The [patch](upstream-review-patch.patch) and
    [message](upstream-commit-message.txt) are retained.
- **Changes:**
  - **D1/P5:** the rule and plan exempt Hexalith.Builds build and workspace
    tooling that never invokes module operations (currently `hexalith-module`
    and `hexalith-evidence`).
  - **P1:** retained implementations receive only safety and continuity fixes.
  - **P2:** only operation-surface changes force an inventory update.
  - **P3:** every plan change gets a new `plan_version`, now 1.1.0.
  - **P4:** gateway-ready rows carry FR-21's include/exclude coupling.
  - Dispositions, inventories and `inventory_revision` are unchanged.
- **Root baseline:** the `references/Hexalith.AI.Tools` reference is
  fast-forwarded to `70dbf73`, which contains `68e6037` and `5be77fc`. No nested
  submodule exists. The gitlink move lands in the next McpCli root commit.
- **Synchronization:** `scripts/check-agent-instructions-sync.sh` exits 0, and
  the three entry points are byte-identical. A temporary copy with a modified
  `CLAUDE.md` fails with exit 1.

Exact results, hashes and the UTC capture time are in
[verification.json](verification.json). No .NET, live or hosted run applies to
this documentation and reference change.
