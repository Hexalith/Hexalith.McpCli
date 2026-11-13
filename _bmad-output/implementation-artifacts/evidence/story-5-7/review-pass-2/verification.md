# Story 5.7 review pass 2 implementation verification

All eleven accepted patch groups are implemented. The approved inventories,
owner receipt, AD-23 authority, historical evidence, production/dependency
configuration, census and reference gitlinks are unchanged by these fixes.
The two accepted deferrals remain assigned to their recorded follow-up work.
[preservation.json](preservation.json) records the approved hash bindings and
clean protected-path comparison against the current committed inputs.

## Historical gates and current drift

The amendments gate reads source-pin coverage from the original baseline
`.gitmodules` blob. A changed working `.gitmodules` emits an exact `reported:`
line on stderr and succeeds. Current owner compatibility sections that change,
disappear or become malformed likewise report drift and succeed. Git read
failures remain blocking. Completion still rejects damaged recorded README
bytes, ancestry, non-README delivery, commit hashes, or immutable published
inventory/receipt blobs, including their current McpCli main copies.

Both gates return their effective completion state to their CLI entry points.
The default amendments command therefore confirms completion when an integrated
register or workflow status requires and verifies it. The test module also runs
directly when Python supplies no bytecode-cache path.

## Focused verification

[checks.json](checks.json) binds exact commands, exit codes and separate stdout
and stderr files. Both ordinary and explicit approved-completion gates pass,
AD-23 remains adopted, `git diff --check` passes, and all **34 tests** pass through
both unittest discovery and direct-file execution. No production or .NET code
changed, so these fixes require no solution restore, build or live operation.

| Review gap | Isolating coverage |
| --- | --- |
| Workflow and integrated-register completion triggers | Candidate registers isolate spec/sprint `done`; a forged integrated register is tested through the amendments CLI; explicit completion with approved but undelivered labels fails with exact stderr. |
| Exact label semantics | Rehashed candidates isolate technical citation/hash, Admin citation/hash and no-replacement rule, independent module citation, compiler exemption, four-mode safety, paired retirement, forwarded authority, Parties blocked verdict, unsupported replacement and compatibility intro. Every case asserts exit and both streams exactly. |
| Recorded delivery read-backs | Damaged integrated README, non-README diff and each recorded inventory blob fail independently; receipt, ancestry and commit-hash checks remain covered. |
| Preserved authorities | Damaged predecessor, preserved authority, exemption integration, AD-23 adoption and required role/source fail with exact diagnostics. |
| Current drift | New root-submodule bytes and changed/absent/duplicate current sections report exact diagnostics with exit 0. Actual child processes exercise both gates with drift injected only in memory; normal subprocess assertions derive the exact permitted report lines from baseline/current bytes. |
| Origin and Admin inventory citation | A non-GitHub host with the same owner/path is rejected; PS01 and PS02 reverting to the original Admin citation fail the protected-field check. |

[guard-controls.json](guard-controls.json) records **29/29 detected one-guard
removals**, in addition to the twelve controls retained in the focused suite.
These controls mutate functions only in memory and execute the isolating tests;
they never edit verifier source files, approved inputs or owner repositories.

## Delivery housekeeping and CI observations

[worktree-cleanup.json](worktree-cleanup.json) records all seven clean merged
delivery worktrees and branches removed without force, with unchanged original
owner checkout HEAD/status snapshots. Large original-checkout status output is retained by matching before/after byte length and SHA-256, avoiding unrelated path listings. Historical creation records are retained.

[owner-ci-final.json](owner-ci-final.json) records terminal owner CI outcomes and
parent comparisons beside the existing bypass disclosure in
[delivery verification](../delivery/verification.md). EventStore CI and ChatBot
ci/release failed on inherited build or runtime prerequisites; Parties CI was
cancelled after inherited job failures. FrontComposer, Memories, Projects and
Folders passed. EventStore's separate Integration Tests was still running at the
observation time. No all-green CI or legacy-retirement claim is made.

Parent workflow verification, review, final status transition and fresh complete
packet/principal-input secret scans follow this implementation handoff. Existing
scan receipts remain historical and are not represented as scans of these new
bytes.
