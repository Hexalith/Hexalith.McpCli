# Story 5.8 verification (2026-11-13)

The Folders 1.1.0 inventory and exact-byte owner approval were published at
McpCli `f3c8f5f7c37f2a03287fc41ecf2e7ca8c5f49091`. The separately authorized PS10/PS11
README-only update was published at Folders `db40bda8a107fcb03405e074810be16c0d47c85f`.
Both revisions were read back from their remote `main` branches. Both approved
completion verifiers pass against the real published artifacts and README bytes.

The approved inventory SHA-256 remains
`54a6f61d4f0d83876d8113c7c9d8775dc73190ecdbd8a3beb34cda10946d6407`.
Its pending metadata/A2 heading are immutable approved bytes; effective owner
approval is recorded in [approval.json](approval.json). The receipt covers the
listed Folders roles, supersedes A1 and grants disposition authority only.
The user's separate `authorize` message is retained in [labels.json](labels.json).
The label commit changes only README.md; unrelated owner work remains outside it.
No enrollment, module execution, parity or retirement is claimed. The K12
reconciliation remains an Epic 6 catalog hold.

The pending-state tests now run against isolated copies so they preserve their
exact refusal streams and live-global guard controls after real approval and
integration. All 31 tests passed both from the pending source (29.830 seconds)
and from an isolated approved/integrated/done source view (28.138 seconds).
The proof and raw output are retained in [delivery/](delivery/). This lifecycle
fixture is test evidence only; real delivery is established by the published
revision/blob/README checks, recorded in [integration.json](delivery/integration.json).

## Final delivery verification

The focused follow-up review completed all three independent layers. Eight direct
patch groups improved fixture scope and evidence reproduction; one finding was
rejected because the synthetic lifecycle source never claims real acceptance.
No new review work was deferred. The original K12 catalog hold remains open.

The final suite passed **36 tests in 24.761 seconds** with the real spec
marked done and the published approval/labels present. The saved lifecycle proof
also passed **36 tests in 25.477 seconds** and confirmed that real
candidate, receipt and workflow bytes were unchanged. Five new tests protect
owner-only observation substitution, unrelated-repository pass-through, duplicate
workflow status rejection and capture/replay bindings.

| Captured check | Result |
| --- | --- |
| [Final suite](delivery/final-tests.json) | exit 0; 36 tests, no skips |
| [Saved lifecycle proof](delivery/final-lifecycle-proof.json) | exit 0; synthetic lifecycle metadata only; 36 tests |
| [Default inventory verifier](delivery/final-default-completion.json) | exit 0; spec-done trigger enforces approved completion |
| [Default label verifier](delivery/final-default-labels.json) | exit 0; integrated delivery verified |
| [AD-23](delivery/final-ad23.json) | exit 0; exact-byte adoption retained |
| [McpCli remote main readback](delivery/remote-main-mcpcli.json) | published inventory/approval revision retained |
| [Folders remote main readback](delivery/remote-main-folders.json) | exact README-only delivery revision retained |

Every command record binds full stdout/stderr bytes. The lifecycle summary uses
relative sidecars and a repository-relative helper command; the pending run has
its own [command manifest](delivery/lifecycle-pending.json). The retained
[review snapshot and summary](delivery/review-followup.json) record the scope and
triage. The story spec is done; sprint tracking is review, as required by the
build workflow. All user-authorized publication and label delivery are complete.

Final scan command:
`python3 scripts/scan-evidence-secrets.py _bmad-output/implementation-artifacts/evidence/story-5-8 --receipt _bmad-output/implementation-artifacts/evidence/story-5-8/secret-scan-delivery-final.json`.
Its result and exact packet file hashes are recorded in the
[final receipt](secret-scan-delivery-final.json). No .NET build or live acceptance
is claimed for these documentary and Python-test changes.

## Historical pre-approval candidate evidence

The following records describe the reviewed pending candidate before the user
approved its exact bytes. References to pending approval/delivery in this section
are historical; the publication and completion evidence above supersedes them.

Three independent review layers produced 14 findings: 12 were addressed in 11
patch groups, two low findings were rejected, and no review findings were deferred.
The final full run passed all 31 tests in 29.635 seconds. The repaired checks cover
optional ownerFileId drift, actual client/upload-kind links, property-specific
required keys, malformed/duplicate JSON, automatic done triggers and real Git
ancestry. The pending candidate, approval receipt and label patch were regenerated.
No new commits or commit messages were created by the graph fixtures; they use
existing objects and temporary local refs. The original command and scan captures
remain historical; the `review-1-*` captures are the final verification evidence.

The source pin is `7eab70e9332c0573b50dce5b219e425b6a2d363c`; the predecessor's
`e2252f29a2dba2b64786ee483eb59fbceaadd387` is read as an independent historical
pin. Every source read uses committed Git objects. The README patch base is the
previously delivered Story 5.7 Folders commit
`583d3d492f94217809a8efe00424b80ce3fdfa61`, because the root gitlink predates its
PS10/PS11 labels. No fetch, checkout, branch, index, owner-file or remote mutation
was needed. Current owner README section differences are report-only.

All 161 entries are accounted for exactly once: M49, R2, L42, C13, Q35, V10,
N4, G6. The candidate has 123 replace/include, 33 defer/exclude and 5
withdraw/exclude entries; 39 of its 48 unique Command/Query candidates are
replacement targets. These counts describe documentary rows, never enrollment.
The 41 decorated owner declarations include C01/C10, which remain deferred
under the named AD-23 K12 reconciliation with eight linked legacy rows.
Seven diagnostics remain deferred. N01/N02 and V04/V09/V10 are withdrawn from
the migration target. Every G row names its Folders story and pinned status.

[commands.json](commands.json) binds each command's full stdout, stderr and exit
code by SHA-256. The `review-1-*` entries record the final checks after repairs;
the original entries record the initial 21-test candidate. All commands ran from
the McpCli root:

| Command | Result |
| --- | --- |
| `python3 -I _bmad-output/implementation-artifacts/evidence/story-5-8/verify_amendment.py` | exit 0; all 161 entries and pending receipt verified |
| `python3 -I _bmad-output/implementation-artifacts/evidence/story-5-8/verify_labels.py` | exit 0; chained PS10/PS11 README-only patch verified |
| `python3 -I _bmad-output/implementation-artifacts/evidence/story-5-8/verify_amendment.py --approved-completion` | expected exit 1; empty stdout; exact stderr below |
| `python3 -I -m unittest discover -v -s _bmad-output/implementation-artifacts/evidence/story-5-8 -p 'test_*.py'` | exit 0; 31 tests passed, no skips |
| `python3 -I _bmad-output/implementation-artifacts/evidence/story-5-2/verify_class_map.py` | exit 0; adopted AD-23 remains exact-byte valid, including Folders 103 rows + 58 records |
| `git -c core.commitGraph=false diff --check` | exit 0; stdout and stderr empty (the option suppresses an existing incomplete commit-graph warning) |

Expected completion stderr:

```text
FAIL: completion requires exact-byte owner approval and covered Folders roles
```

The generator deterministically reproduces the candidate and bound README patch
from the immutable predecessor and pinned sources, and refuses an approved or
unknown-state packet before any write. The tests cover each matrix scenario,
replace/include equivalence, all disposition branches, K12, diagnostics,
owner/gap/loss completeness, duplicate/damaged rows, exact anchors, both-pin model
drift, G-story status, decorated type/eligibility/wire/domain/aggregate/projection/
caller-key declarations, approval/hash/delta/role limits, pending/approved owner
fixtures, separate delivery authorization, README-only integration and published
artifact bindings. Corrupted input also runs through real isolated verifier
processes. Every refusal asserts exit and both complete output streams.

Guard-removal controls rebind the functions' actual live module globals, verify
that corrupt input becomes accepted only when the applicable guard is disabled,
and leave production files and receipts unchanged. Later owner README drift is
explicitly tested as a stderr report with success. Completion fixtures are
synthetic test evidence only and do not claim owner approval or a delivery commit.

The both-pin source checks compare exact Name/URI/leaf sets and prove the actual
client/target links at the refreshed pin. They prove newly added optional
FileMutationRequest.ownerFileId and its owner-incarnation semantics, required
expectedFileVersion/expectedLockFence, FileMetadataItem.fileId/version and LockLeaseMetadata.lockFence
against their actual generated class blocks. Affected rows carry their refreshed
model-field anchors. The current three internal query handlers and configured
file defaults do not establish live behavior for the 28 declared Queries; the
commit executor remains unavailable. No services or module operations ran.

Preserved authority hashes (also enforced against the baseline commit and bound
by [approval.json](approval.json)):

| Artifact | SHA-256 |
| --- | --- |
| Folders 1.0.0 | `57cf556b8051921bf2bf8a17abe3b82b7d0a3ba8ba5593072f52c12f85650e0b` |
| AD-23 decision | `f47b64c7772ed9d9763e4438a176cb7bea01e8e0793f7217c6bd1f3274545560` |
| AD-23 map | `21cb3643ef3e652031bf13f02e237b2cfadb2be24bcbf2d02e879a584ac8a4c3` |
| Technical 1.0.3 | `7f2810174ae929e569d9affaccabe745565dcfe4f0487b71847806f3eda1ef8c` |
| Folders 1.1.0 pending candidate | `54a6f61d4f0d83876d8113c7c9d8775dc73190ecdbd8a3beb34cda10946d6407` |

The named K12 gap was added under its own source-spec heading in
[deferred-work.md](../../deferred-work.md), after grep found no equivalent Folders
entry. The pre-existing Parties entry was retained. Epic 6 cannot catalog
Contracts 1.4.0 until the separate owner resolution exists. The pending receipt
names the Folders roles it must cover and supersedes A1 only once approved.
The PS10/PS11 patch changes the Folders citation and adds its exact hash; it
preserves the technical 1.0.3 citation and removal gate. Technical inventory bytes
and the AI.Tools migration plan remain unchanged for their later successors.

Final secret scan command: `python3 scripts/scan-evidence-secrets.py _bmad-output/implementation-artifacts/evidence/story-5-8 --receipt _bmad-output/implementation-artifacts/evidence/story-5-8/secret-scan-review-2.json`.
The first post-review scan [receipt](secret-scan-review-1.json) recorded scan-error
because three review-generated Python bytecode caches are unsupported binary
evidence. Those generated caches were removed; no evidence source was removed.
The task-owned [final receipt](secret-scan-review-2.json) binds the reviewed packet,
including both historical receipts. Only the final
receipt's own bytes are excluded from its scan. New Python checks and documentary evidence are the
only implementation here, so no .NET build or live acceptance was claimed.
