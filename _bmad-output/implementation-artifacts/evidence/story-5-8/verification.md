# Story 5.8 verification (2026-11-14)

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

## Reproduction prerequisites

Run from the McpCli repository root with Python 3.9 or newer and Git. The unittest
suite and the lifecycle proof require a UTF-8 locale; both verifier entrypoints
also run under an ASCII locale (`-X utf8=0` with `LC_ALL=C`). The approved label
register requires the existing absolute owner checkout
`/home/administrator/projects/hexalith/folders`, with `origin` identifying
`Hexalith/Hexalith.Folders`; the register is unchanged. That checkout must contain
the committed README base `583d3d492f94217809a8efe00424b80ce3fdfa61`, delivery
`db40bda8a107fcb03405e074810be16c0d47c85f` and its local `origin/main` ref.
McpCli needs baseline `a92a2969db6903b8c6cca7e437446167e135ec9d`, published
inventory/approval revision `f3c8f5f7c37f2a03287fc41ecf2e7ca8c5f49091` and its
local `origin/main` ref. Both delivery revisions must be ancestors of the
respective local refs. The tests additionally use existing McpCli commits
`85a5437b98d0e126147460ca1ee1fa6a36041a21` and
`cab549c7b06fa4eef08e46cfcde038f62ea81fbf`, plus the published label-register
revision `c3bd5b9a49b538282db14c5ee9780f63fe70c8b9`. The graph fixtures and the
lifecycle proof also read the current McpCli `HEAD` and its first parent `HEAD^`,
so the clone must contain both. In the owner checkout the graph fixtures also read
the README base's parent `7eab70e9332c0573b50dce5b219e425b6a2d363c` (`583d3d49^`)
and grandparent `6a8cf4f9e28786176d26522b41bb921e18b922da` (`583d3d49^^`). A
shallow clone without these objects fails with a Git error; the tests have no
skip branches.

The root-declared `references/Hexalith.Folders` checkout must contain committed
source objects for `7eab70e9332c0573b50dce5b219e425b6a2d363c` and published
ancestor `2236855ee181bdeed2a103537c66316a1612c792`. The unpublished original
`e2252f29a2dba2b64786ee483eb59fbceaadd387` is optional. The verifiers read these
local objects and refs; they do not fetch or perform network operations.

## Final resumed pass-3 build verification (2026-11-14)

All eight code-review-pass-3 patch entries and all eight build-review patch
groups are complete. The parent's final verification passed **77 tests in
75.575 seconds** in the ordinary workspace and **77 tests in 75.638 seconds** in
the synthetic approved/integrated/done lifecycle workspace, with no skips. The
lifecycle proof computed unchanged real inputs.

The following also passed:

- both real completion gates, under the default UTF-8 locale and under an ASCII locale;
- AD-23 adoption;
- five focused tests with a symlinked temporary-directory root: label-path escapes,
  published-bytes halves, completion-mode owner drift, and the lifecycle candidate
  and workflow refusals;
- `git diff --check` against the baseline;
- a `--no-index --check` of all 58 untracked files.

The isolated-copy guard-removal report still detects all 27 mutations, and its
recorded inputs equal the current sources.

The [final command manifest](review-pass3-final-20261114/commands.json) binds all
eleven executable inputs, exact commands, environments, exit codes and both
stream hashes. The [closure audit](review-pass3-final-20261114/audit.json) was
computed after the last command. It verifies all ten command streams, the passing
tests for every matrix row, the protected bytes against `HEAD` and the frozen
intent against the baseline.

All three independent build-review layers completed. Their surviving findings
formed eight patch groups:

- two missing tests: the corrupt-predecessor guard and completion-mode drift;
- the guard-removal helper's in-place mutation, detection rule and individual
  encoding reverts;
- the lifecycle candidate check;
- the UTF-8 suite prerequisite;
- the closure audit's scope.

All eight were applied. One pre-existing approved-byte omission, the G3/G4 gate
narrowing, is assigned to the K12 successor under its own ledger heading. The
remaining findings were rejected with reasons in the spec triage log. Approved
inventory, receipts, labels, production, dependencies, census and gitlinks are
unchanged. This build session performed no commit or push, and no .NET build or
live acceptance is claimed.

Final scan command:
`python3 -B scripts/scan-evidence-secrets.py _bmad-output/implementation-artifacts/evidence/story-5-8 --receipt _bmad-output/implementation-artifacts/evidence/story-5-8/secret-scan-review-pass3-final-20261114.json`.
The [final receipt](secret-scan-review-pass3-final-20261114.json) is clean over
266 files. Earlier captures and scans are historical.

## Historical code-review pass 3 patch verification (2026-11-14)

All eight pass-3 patch entries are implemented. The ordinary suite passed
**75 tests in 81.438 seconds**, and the fresh synthetic approved/integrated/done
lifecycle run passed **75 tests in 82.982 seconds**, with no skips. The
lifecycle proof computed `realInputsUnchanged: true`. Both real completion
verifiers, AD-23 adoption and the full-baseline whitespace check passed.

New exact-stream refusal cases and removal controls cover:

- an unknown approval decision, through the real entrypoint and in-process;
  without the guard, `decision: "rejected"` reaches the pending PASS;
- an unknown label-register state, through both entrypoints;
- a standalone `verify_labels.py` run where only `state` is `integrated`. It
  fails with the owner-approval diagnostic; deleting the integrated-state trigger
  from the copied entrypoint yields the pending PASS;
- inventory or receipt bytes rewritten at `origin/main` or at `inventoryRevision`.
  Each half of the published-bytes condition is disabled separately, so each is
  shown to be necessary.

Each of the eleven backstopped guard sites that pass 3 listed now has a refusal
case and a removal control:

- inventory verifier: amendment columns; legacy disposition, coverage and
  combined cells; relative and absolute anchor escapes; the source anchor;
  frontmatter; and duplicate metadata;
- label verifier: a missing artifact path, whose removal leaves only the
  non-actionable `FAIL: 'path'`; absolute and relative path escapes that name the
  exact approved bytes; and the technical-authority, gate and successor-hash text.

The lifecycle proof now snapshots the fixture spec and sprint bytes after
setting both to done and requires them unchanged after the child. A child that
rewrites only one status, which still satisfies `completion_requested`, is
refused. Stream sidecars are written only after every check passes. All three
negative lifecycle tests require an empty delivery folder.

All six verifier and builder text reads decode UTF-8 explicitly. A new test runs
both entrypoints with `-X utf8=0` and `LC_ALL=C`, an ASCII locale, and requires
the pending PASS. Both real completion gates also pass under that locale. Before
the fix, both failed with `'ascii' codec can't decode byte 0xe2`. Two tests now
use full commit SHAs, and the prerequisites above list every parent commit the
graph tests read.

The retained [guard-removal helper](review-pass3-20261114/guard-removal.py) applies
27 mutations, each in a fresh isolated workspace copy, and never writes the real
packet sources. They delete each new guard and the historical-predecessor
inspection guard, revert each of the six encoding fixes individually and all of
them together, and revert the three lifecycle fixes. An unmutated copy first
passes all 15 selected tests. A mutation counts as detected only if at least one
test ran and the run ends in a failures-only summary with an `AssertionError`;
all 27 are detected. Its [report](review-pass3-20261114/guard-removal.json)
records each result and shows the real source hashes unchanged.

The [command manifest](review-pass3-20261114/commands.json) binds each command to
the executable input hashes it ran with, plus its exact command, environment,
exit code and both stream hashes. Three focused tests also passed with a
symlinked temporary-directory root: the label-path escapes, the published-bytes
halves and the lifecycle workflow refusal.

Review follow-up (2026-11-14): new cases cover a corrupt original predecessor
object (rev-parse exit 128), whose removal control shows the historical tree
binding would otherwise be skipped, and completion-mode owner drift, which
reports `differ from delivered candidate` and still passes. The lifecycle proof
now also compares the fixture candidate bytes after the child, and a child that
rewrites the candidate is refused with no files written. The guard-removal
helper was rewritten to use isolated copies and the stricter detection rule; its
earlier in-place capture is replaced. Only the 8 tests covering the edited files
were rerun (all passed) together with the helper. The 75-test ordinary and
lifecycle captures above predate this follow-up, which adds two tests, so the
full suite now has 77 tests. Its full rerun belongs to the coordinator's
verification. The [closure audit](review-pass3-20261114/audit.json) states which
records ran with the current inputs.

This session added no ledger entry; the resumed pass-3 build review then
recorded the G3/G4 deferral above. The three pass-3 approved-byte and builder
defers remain under their own ledger heading. Approved inventory, receipt, label
register, label-patch and delivered README bytes are unchanged, as are
production, dependencies, census and gitlinks. This session performed no commit
or push. No .NET build or live acceptance is claimed for these documentary and
Python-test changes.

Pass-3 scan command:
`python3 -B scripts/scan-evidence-secrets.py _bmad-output/implementation-artifacts/evidence/story-5-8 --receipt _bmad-output/implementation-artifacts/evidence/story-5-8/secret-scan-review-pass3-followup-20261114.json`.
The [receipt](secret-scan-review-pass3-followup-20261114.json) binds the packet
after the review follow-up; the first pass-3
[receipt](secret-scan-review-pass3-20261114.json) and earlier scans are historical.

## Historical resumed pass-2 build verification (2026-11-14)

All ten pass-2 patch entries and four follow-up build-review patch groups are
complete. Final verification passed **65 tests in 75.261 seconds** in the ordinary
workspace and **65 tests in 78.173 seconds** in the synthetic approved/integrated/done
lifecycle workspace, with no skips. The lifecycle proof computed unchanged real
inputs and now preserves both real-input and synthetic-state checks under Python
optimization. Its negative child-mutation case runs optimized helper code and
requires refusal without a success summary. Blank and malformed duplicate status
keys are refused through both actual entrypoints, and a copied-entrypoint mutation
proves the owner verifier calls its declaration checks.

Three focused tests also passed with a symlinked temporary-directory root
(14.229 seconds), covering workspace copies, protected-JSON fixtures and published
owner graphs. Both real completion verifiers, AD-23 adoption and the full-baseline
whitespace check passed. The [final command manifest](review-pass2-final-20261114/commands.json)
binds all ten executed repository helpers and exact commands, streams and hashes.
The [closure audit](review-pass2-final-20261114/audit.json) checks protected bytes,
frozen intent, matrix coverage and the final done/review workflow state.

All three independent review layers completed. Four direct patch groups were
applied; one new approved-byte omission (Q08 optional task context in V03) is
assigned to the K12 successor, and six prior deferrals were carried without
duplicates. The catalog hold remains open. Approved inventory, receipts, labels,
production, dependencies, census and gitlinks are unchanged. This build session
performed no commit or push; no .NET or live acceptance is claimed.

Final scan command:
`python3 -B scripts/scan-evidence-secrets.py _bmad-output/implementation-artifacts/evidence/story-5-8 --receipt _bmad-output/implementation-artifacts/evidence/story-5-8/secret-scan-review-pass2-final-20261114.json`.
The [final receipt](secret-scan-review-pass2-final-20261114.json) covers the completed
packet after review and workflow closure; earlier captures and scans are historical.

## Historical code-review pass 2 patch verification (2026-11-14)

All ten accepted patch entries are implemented. The retained ordinary suite passed
**63 tests in 63.186 seconds**, and the fresh synthetic approved/integrated/done
lifecycle run passed **63 tests in 63.013 seconds**, with no skips. The lifecycle
proof computed `realInputsUnchanged: true`; a negative control supplies a changed
second snapshot and requires an exception without a success summary. Its real-input
comparison now remains active under Python optimization.

The published-graph fixtures read the integrated register at McpCli
`c3bd5b9a49b538282db14c5ee9780f63fe70c8b9` and the approval at its recorded
inventory revision, using committed objects. Their temporary owner `origin/main`
points to Folders delivery `db40bda8a107fcb03405e074810be16c0d47c85f`, so synthetic
lifecycle state and later owner relabels do not change the fixture. Temp roots are
resolved before comparisons with verifier roots.

New exact-stream refusal and removal controls cover duplicate spec/sprint statuses
through both real entrypoints; label schema, repository/base, README hashes, patch
scope, retention and canonical delivery commits; legacy identity and disposition
inheritance; complete pinned surface sets, registration and module declarations;
missing replacement targets; source drift and transport/default/query premises;
preserved authority, AD-23 adoption and candidate prose. Removing the prose guard
is shown to reach the independent receipt hash-chain refusal.

The [command manifest](review-pass2-20261114/commands.json) binds all ten executable
repository inputs, exact commands, working directories, exit codes and both complete
stream hashes. It includes the explicit invocation that redirects the lifecycle proof
to this new packet; the older delivery captures remain historical. Both real default
completion verifiers, AD-23 and whitespace checks pass. The ledger now has current
builder anchors, a separate resumed-review heading, and the full client/server/domain
scope of the 23-file end-anchor tightening, all assigned to the K12 successor.
All eight preserved authorities are listed below. Approved inventory, receipt,
register, label-patch and delivered README bytes remain unchanged. This session
performed no commit or push. No .NET build or live acceptance is claimed for these
documentary and Python-test changes.

Pass-2 scan command:
`python3 -B scripts/scan-evidence-secrets.py _bmad-output/implementation-artifacts/evidence/story-5-8 --receipt _bmad-output/implementation-artifacts/evidence/story-5-8/secret-scan-review-pass2-20261114.json`.
The [receipt](secret-scan-review-pass2-20261114.json) binds the packet at this
implementation handoff; subsequent build-review and workflow closure evidence
requires its own final scan.

## Historical code-review pass 1 patch verification (2026-11-14)

All nine accepted patch entries and five review follow-up patch groups are implemented.
The final suite passed **50 tests in 46.608 seconds**, with no skips. Its new cases protect the published predecessor tree binding and
missing-original-object path, committed-baseline route evidence, both required
fence attributes, integrated-label completion and builder refusal, and real
publication/delivery failures. The latter read actual Git blobs and commits:
pre-inventory revision `85a5437b98d0e126147460ca1ee1fa6a36041a21`, pending-receipt
revision `cab549c7b06fa4eef08e46cfcde038f62ea81fbf`, the older README-only label
commit, a fork origin and a damaged commit hash. Refusal checks assert the exit
code and complete stdout/stderr; guard-removal controls prove the relevant
failures depend on their guards. The final additions refuse an existing successor
with either receipt missing, permit pristine initialization, and prove that the
real owner entrypoint invokes the source-drift checks through a caller-deletion control.

The [final command manifest](review-final-20261114/commands.json) binds all executed
repository Python helpers, exact commands, root working directory, results and both stream
hashes for the suite, both real default completion verifiers, AD-23 verification
and `git diff --check`. All pass. The approved inventory, approval receipt,
delivered label register and other authorities remain byte-identical. Existing
K12 deferrals remain open; their approved inventory text needs a separately
approved successor. Review also recorded two pre-existing source-drift omissions
for that successor: SDK end-anchor tightening and disabled automatic redirects.
The spec is done and sprint tracking is review. All five follow-up patch groups
passed final verification; the edge-case review returned no findings. That build
session performed no commit or push. The user later committed its work as
`edd15cfe372ba7ecdd0c835966fa93073a072fae`.

Final scan after review and workflow closure:
`python3 scripts/scan-evidence-secrets.py _bmad-output/implementation-artifacts/evidence/story-5-8 --receipt _bmad-output/implementation-artifacts/evidence/story-5-8/secret-scan-review-final-20261114.json`.
The [final receipt](secret-scan-review-final-20261114.json) binds the complete
updated evidence packet. The preceding [47-test capture](review-patches-20261114/commands.json)
and its [scan](secret-scan-review-patches-20261114.json) remain historical. No .NET build or live acceptance is claimed for these
documentary and Python-test changes.

## Historical delivery evidence

The pending-state tests run against isolated copies so they preserve their
exact refusal streams and live-global guard controls after real approval and
integration. The historical pre-delivery 31-test runs passed both from the
pending source (29.830 seconds) and from an isolated approved/integrated/done
source view (28.138 seconds); the later delivery suite contained 36 tests.
The proof and raw output are retained in [delivery/](delivery/). This lifecycle
fixture is test evidence only; real delivery is established by the published
revision/blob/README checks, recorded in [integration.json](delivery/integration.json).

## Historical final-delivery verification (2026-11-13)

The focused follow-up review completed all three independent layers. Eight direct
patch groups improved fixture scope and evidence reproduction; one finding was
rejected because the synthetic lifecycle source never claims real acceptance.
No new review work was deferred. The original K12 catalog hold remains open.

The delivery suite passed **36 tests in 24.761 seconds** with the real spec
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
triage. At that delivery checkpoint the story spec was done and sprint tracking
was review, as required by the build workflow. All user-authorized publication
and label delivery were complete.

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

The source pin is `7eab70e9332c0573b50dce5b219e425b6a2d363c`; the original
predecessor was `e2252f29a2dba2b64786ee483eb59fbceaadd387`. The review patch
reads its source via the published ancestor
`2236855ee181bdeed2a103537c66316a1612c792`, whose `src` tree must match the
recorded predecessor tree `d0f81f0f00570c2d8ba1f34af2fcdf7bccb9d7e0`.
The original commit's tree is also compared when that object is present; its
absence no longer prevents verification. McpCli route evidence comes from
baseline `a92a2969db6903b8c6cca7e437446167e135ec9d`. Every source read uses
committed Git objects. The README patch base is the
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

Preserved authority hashes, enforced against the baseline commit and bound by
[approval.json](approval.json):

| Artifact | SHA-256 |
| --- | --- |
| Folders 1.0.0 | `57cf556b8051921bf2bf8a17abe3b82b7d0a3ba8ba5593072f52c12f85650e0b` |
| AD-23 decision | `f47b64c7772ed9d9763e4438a176cb7bea01e8e0793f7217c6bd1f3274545560` |
| AD-23 map | `21cb3643ef3e652031bf13f02e237b2cfadb2be24bcbf2d02e879a584ac8a4c3` |
| Story 5.2 approval.json | `7c43dbec5b09e231852f2bb6410cf70846ce440ac06265e8faa8ddd2ef8aa498` |
| Story 5.2 main-integration.json | `be51f67f9f3036bb328ceb7c72125777964138d537e96875f4c887286432430d` |
| Technical 1.0.3 | `7f2810174ae929e569d9affaccabe745565dcfe4f0487b71847806f3eda1ef8c` |
| Story 5.7 approval.json | `5b0044a505f6cdcb95c5ceaa087f79dd705da54de3225ea9358f2b50f48e3b90` |
| Story 5.7 labels.json | `06d018c0c1aac60b4b19fcafd4fabfa23bd274c1433089311513320343ec10e6` |

The approved Folders 1.1.0 successor is SHA-256
`54a6f61d4f0d83876d8113c7c9d8775dc73190ecdbd8a3beb34cda10946d6407`.
It did not exist at the baseline: deterministic regeneration, the exact-byte
approval receipt and the published-artifact checks bind its bytes.

The named K12 gap was added under its own source-spec heading in
[deferred-work.md](../../deferred-work.md), after grep found no equivalent Folders
entry. The pre-existing Parties entry was retained. Epic 6 cannot catalog
Contracts 1.4.0 until the separate owner resolution exists. The approved receipt
names the covered Folders roles and supersedes A1 for this successor.
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
