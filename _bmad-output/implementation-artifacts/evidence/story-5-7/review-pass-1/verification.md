# Story 5.7 parent review and verification

The three independent review layers completed on 2026-11-13. Each finding and
its verified disposition is recorded in the specification's Review Triage Log.
All nine surviving patch groups are fixed; three negligible findings were
rejected and none deferred. The initial packet and its command logs remain
historical evidence of the pre-review candidate.

The parent's initial rerun reproduced the status-dependent test failure when
the workflow moved the specification from in-progress to in-review. The corrected
fixture mutates the status independently of that starting state. Both quoted
and commented YAML done values now trigger completion validation.

Standalone label completion now reuses the complete owner/role/artifact/delta
validation. It binds the approved receipt at the integrated inventory revision
and current local origin/main, checks the current owner compatibility sections,
owner origin identities and displayed surface names, and retains both ancestry
checks. Temporary real Git graphs demonstrate rejection of unmerged owner and
inventory commits, including controls that fail when those ancestry checks are
removed. This is verification of existing local tracking refs; no fetch or
fresh remote-state attestation occurred.

[commands.json](commands.json) records the parent's exact commands, expected and
actual exits, and separate output files. Both candidate verifiers pass for 159
rows, 382 historical anchors and 14 labels. All **27 tests pass**, and unchanged
AD-23 verification still reports adopted. Both approved-completion commands
exit **1** with empty stdout because exact-byte owner approval remains pending;
these are expected refusals, not passed completion gates. The whitespace check
passes. [test-fixture-commitlint.json](test-fixture-commitlint.json) retains pinned
commitlint validation of the five messages used only in temporary test Git
objects; no owning repository commit was created.

The inventory candidate hashes remain:

- Admin 1.0.2: `ec388eae1b2c17cf1634f7b9b422b50124d2281bd0dfc445bfa11c9ad7a03cc2`
- Technical-tools 1.0.3: `7f2810174ae929e569d9affaccabe745565dcfe4f0487b71847806f3eda1ef8c`

[preservation.json](preservation.json) records the final protected-path and owner
worktree checks, including exact patch bytes. The original inventories, approval
receipts, AD-23, historical evidence, production, dependencies, census and gitlinks
remain unchanged. Seven README-only patches remain prepared and undelivered.

The first expanded approval-input scan flagged copied prose describing the
authentication scheme, not an actual credential. Its refusal is preserved in
[approval-input-secret-scan-initial.json](approval-input-secret-scan-initial.json).
The unapproved Admin successor now formats the literal scheme as `Bearer` in
code, with no word or factual change. The generator and verifier require this
exact normalization and a regression rejects other factual changes. The pending
Admin receipt/delta and EventStore label hash references were refreshed. The
technical inventory and every approved predecessor remain byte-identical; the
initial candidate hash remains in the historical verification document.

A final packet attempt found generated Python bytecode, which the text-only
scanner correctly refused. Its receipt is retained in
[packet-secret-scan-before-bytecode-fix.json](packet-secret-scan-before-bytecode-fix.json).
The label verifier now disables bytecode output before dynamically loading the
owner checker. Only this task's generated cache was removed; the final full
verification leaves no binary cache in the evidence packet.

The three principal approval inputs (both inventories and the specification)
are copied byte-for-byte to a task-owned temporary directory. Their source/copy
paths, sizes and SHA-256 values are recorded in
[approval-input-bindings.json](approval-input-bindings.json), and the independent
shared scanner receipt is [approval-input-secret-scan.json](approval-input-secret-scan.json).
Source and copied hashes are checked before and after that scan. The new final
packet scan receipt is [packet-secret-scan.json](packet-secret-scan.json); it
includes those input bindings and scan evidence, and excludes itself by being
copied into the packet only after scanning. The initial scan receipts are retained.

The story remains **in-progress**. Owner approval of the exact candidates and
separate commit/push/merge authorization are still needed before publishing the
inventory/approval packet and integrating the seven label updates. No execution,
enrollment, parity or retirement authority is granted. No task work is committed
or pushed.
