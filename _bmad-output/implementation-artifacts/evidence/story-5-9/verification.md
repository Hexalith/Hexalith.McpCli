# Story 5.9 verification — owner-approved documentary successors

Prepared 2026-11-16 against McpCli baseline `fbe4b6bd5502741ff8006abedac5c9bb27a4df3c`. Candidate
checks pass; exact-byte owner approval, separate delivery authorization and upstream integration
were completed on 2026-11-16. The story is **done**. The approved inventories and both
owner README updates are on their owning main branches. No enrollment, live execution,
parity acceptance or retirement is claimed.

## Candidate accounting and exact bytes

| Module | Successor | Entries | Replace/include | Withdraw/exclude | Defer/exclude |
| --- | --- | --- | --- | --- | --- |
| Projects | 2.1.0 from 2.0.0 | 56 (T4/R11/M5/L18/V12/G6) | 17 | 19 | 20 |
| FrontComposer | 1.1.0 from 1.0.0 | 30 (H3/D13/C2/V8/G4) | 0 | 20 | 10 |

- [Projects 2.1.0](../../projects-migration-inventory-v2.1.0.md): SHA-256 `c4667069ab37cc495fc49a07ae2fdececd75a8c0e9201f3e6cdf6b562aa7d1af`.
- [FrontComposer 1.1.0](../../frontcomposer-migration-inventory-v1.1.0.md): SHA-256 `60c44b5c7c67ca315bfe4f7582ea7e50526dc2cfeebbf12838f4b0c71543ff63`.
- [Owner approval receipt](approval.json) binds all predecessor/authority and
  successor hashes, per-row deltas, exact source revisions and pinned source/package
  hashes. The user's exact `approve` instruction covers all nine explicitly named roles
  under the single-maintainer model and supersedes A1 plus the Projects 2.0.0 session decision
  for these successors. The approved inventory bytes retain their original proposal headings;
  the receipt establishes their effective approval state.
- [Label register](labels.json) chains to Story 5.8, binding the old PS03/PS04/PS08/PS09
  rows from Story 5.7 and two exact README-only patches. PS03's retained compiler
  gate is unchanged; PS04/PS09 restate the coupled consumer/UI/cutover gate and PS08
  cites the amended Projects prerequisites.

## Source observations and preserved boundaries

Approval-time source pins were rechecked against root gitlinks:

| Repository | Exact pin | Observed upstream ancestry |
| --- | --- | --- |
| Projects | `bf9f98969efa036fd60700c627e712b4375e654a` | `git merge-base --is-ancestor <pin> origin/main`: exit 0 |
| FrontComposer | `33e71036c04f2b99955376e9c90cbb1fc3a81e64` | `git merge-base --is-ancestor <pin> origin/main`: exit 0 |

These ancestry observations use existing local refs, without fetching or writing
upstream. All module sources, package/closure evidence and anchors are read from
Git objects. Projects 2.0.0 baseline `ce71717a` is an ancestor; FrontComposer's
historical pin is compared through merge-base `b06f86d554363ea5b8192cbc149a75c820dab2b8`.
Independent source checks confirm the claimed unchanged legacy paths and current
lifecycle ownership, /mcp authentication, identity conflict, trace authorization,
request preamble and supported-handler premises.

The Projects candidate is **Hexalith.Projects.Contracts/2.0.0-story66.3**, already
present in the root enrollment. Its pinned nuspec and owner-recorded closure
contain only EventStore.Contracts 5.1.0, McpCli.Abstractions 2.0.1,
ByteAether.Ulid 1.4.2 and Commons.UniqueIds 3.0.0, all fitting the unchanged policy.
No fresh restore or package enrollment was performed. Source decoration at the
new pin does not prove equality with the candidate artifact, live readiness or parity.

The 17 approval-time gitlinks were scanned for live root registrations and
project/package consumers, excluding archived evidence and namespace/assertion
strings. FK01 is Projects registration, FK02 is Counter.Web, FK03 is Parties.UI,
and FK04 covers the three direct-reference FrontComposer test projects plus the
Shell.Tests Counter sample fixture. All must move before host and plug-in retire
together. K12 Web/Chatbot UI evidence (Projects 7.6–7.14), 6.7 cutover, DW-82,
independent live safety, release and rollback remain prerequisites. K13 compiler
inspect/migrate stays retained, exempt and never counted retired.

**Corrected paging premise:** Projects ListProjectsQuery declares Payload
cursor/pageSize (default 50/max 200); the executor forwards that Payload and
constructs separate Envelope Paging from the call's paging options. Adopted
AD-23 K03/AD-20 requires Envelope paging. The intended owner-accepted Envelope
paging difference has not been established. G1/G3/V01 and the source section
retain this named gap; no conversion, conformity, readiness or parity is claimed.
The ledger records the owner handoff. T01–T04 need no task context; V09 keeps the
no-Query-extension-channel gap for Commands/M05 context.

This story preserves its exact predecessor inputs and does not rewrite AD-23,
technical 1.0.3, prior receipts, enrollment, dependencies, census, gitlinks,
the AI.Tools plan or any `references/` checkout. The independent Projects 2.0.0
editorial update on main is recorded in the authorized-delivery section below.
Existing C# CRLF checkouts are compared as canonical LF Git blobs
under the tracked `.gitattributes`; immutable documentary artifacts are compared
byte for byte. Story 5.11 owns indexing the successors.

## Pre-approval commands and results

Pre-approval command arrays, exit codes and both streams are retained in [checks.json](checks.json).
Current approved-state results are retained separately in [approval-checks.json](approval-checks.json).
All verification jobs creating scratch directories ran beneath `run-with-temp`;
test fixtures also have their own reliable cleanup. An initial scan detected the
unittest importer's disposable bytecode cache; the verification job removed only
that generated test-module cache after the exact command exited. The test module
sets `sys.dont_write_bytecode = True`; it has no persistent cache-deletion behavior.
The final scan covers text evidence only.

| Command | Result |
| --- | --- |
| `python3 -I _bmad-output/implementation-artifacts/evidence/story-5-9/verify_amendment.py` | Exit 0; 56 + 30 entries, declarations/routes/anchors/drift/classes and complete hash chains pass |
| `python3 -I _bmad-output/implementation-artifacts/evidence/story-5-9/verify_labels.py` | Exit 0; four labels in two README-only candidate patches pass |
| Candidate verifier with `--approved-completion` | Expected exit 1, empty stdout; exact stderr: `FAIL: completion requires exact-byte owner approval and covered roles` |
| `python3 -I -m unittest discover -v -s _bmad-output/implementation-artifacts/evidence/story-5-9 -p 'test_*.py'` | Exit 0; 29 tests pass |
| `python3 -I _bmad-output/implementation-artifacts/evidence/story-5-2/verify_class_map.py` | Exit 0; AD-23 remains adopted |
| `git diff --check` | Exit 0 |
| `python3 scripts/scan-evidence-secrets.py _bmad-output/implementation-artifacts/evidence/story-5-9 --receipt _bmad-output/implementation-artifacts/evidence/story-5-9/secret-scan.json` | See exact [secret-scan receipt](secret-scan.json) |

Tests exercise every entry's accounting and every disposition branch, duplicate/
missing IDs and JSON, absent/undecorated types, wire/domain/aggregate/projection
mismatches, class drift, missing loss/gap/owner/channel, source anchors/drift,
coupled gates, immutable predecessors, pending/approved receipt validation,
deterministic generation and refusal to write an approved/authorized packet.
Approved-refusal tests snapshot every successor/receipt/label/patch byte and
prove rejection happens before packet derivation. Each missing covered role and
each missing label independently blocks completion. Seven guard-removal controls detect disabled accounting, approval, anchor, delivery,
owner ancestry, inventory ancestry and duplicate-workflow-status checks.

Real isolated-process entrypoints assert exit code and both streams. A synthetic
approved/authorized fixture exercises successful completion, including both
upstream README bytes, canonical commits, ancestry, README-only changes, current
origin/main labels, published inventory bytes and receipt bindings. That fixture
has no real approval or delivery authority. A separate control rejects stale
current origin/main labels even when an historical integrated commit matches.

## Build review and final rerun

All three review layers completed before triage. The spec records all 17 findings
individually: 16 verified findings were fixed in nine patch groups; the proposed
current-gitlink check was rejected because approval-time source snapshots must
retain their historical pins. No new work was deferred by review. The existing
K03/AD-20 conformity gap remains tracked.

Corrections preserve FrontComposer V01–V03 behavior while updating ownership,
authentication and identity conflicts. Projects drift now follows actual REST
callers, including diagnostic reloads, and excludes static R05. The unchanged
`Directory.Build.props` version pin is hash-bound and checked. Pending labels use
the root-declared reference origins; delivery still verifies owner repositories.
Approval and delivery require independent affirmative `approve` and `authorize`
tokens. The generator rechecks receipt snapshots after derivation, before writes.

The full 29-test suite passed after the spec moved to `in-review`. New cases cover
retained facts, actual call paths, version disagreement, portable pending checks,
negated/combined decisions, receipt changes during derivation, separate off-main
owner/inventory histories, and duplicate statuses through both entrypoints.
No final result relies on the earlier pre-review 20-test run. Both standalone
`--approved-completion` entrypoints returned the expected refusal while approval
was pending. Those pre-approval streams are retained in `checks.json`.

A separate root README-only commit `baa20ef23fe05091301acfc8d8121b1d1388be16`
landed during this session. It was preserved and is not attributed to Story 5.9.
Before delivery authorization, no Story 5.9 commit, push, upstream write or production change was performed.

## Owner approval transition — 2026-11-16

The user replied exactly `approve` to the request to accept the exact Projects 2.1.0
and FrontComposer 1.1.0 bytes and the receipt's covered roles. The receipt records
that instruction, its conversation source, date and all nine named roles. The
inventory hashes above and every label/README patch byte are unchanged. The label
register retains its generated pre-delivery state name; approval is established
by `approval.json`, with no delivery authorization or integration asserted.

The existing test suite used the real pending receipt as its negative fixture.
Pending scenarios now use disposable receipt copies; actual entrypoint tests
still validate the real approved receipt. Deterministic-generation checks compare
all artifact bytes and the approval-independent receipt content without rewriting
the approved packet. All 29 tests pass in the approved state. The adopted AD-23,
candidate, label and whitespace checks also pass. Both completion entrypoints
return exit 1, empty stdout and the exact stderr:
`FAIL: completion requires integrated PS03/PS04/PS08/PS09 labels`.
All current commands and both streams are retained in `approval-checks.json`.

The pre-approval scan is preserved byte for byte in
[secret-scan-before-approval.json](secret-scan-before-approval.json); the current
[secret scan](secret-scan.json) covers the updated approval evidence.

## Independent retirement gates

Exact-byte owner approval, named role coverage, separate delivery authorization
and upstream README-only integration/readback on both owner origin/main branches
are complete. The receipt below binds the delivered commits and exact bytes.
K03 conformity, DW-82 publication, live acceptance, Projects 6.7 cutover,
K12 UI evidence and release/rollback gates remain independent retirement prerequisites.

## Authorized delivery preparation — 2026-11-16

The user separately replied exactly `authorize` to committing/pushing the approved
packet and both upstream README-only updates. [delivery-authorization.json](delivery-authorization.json)
binds this instruction to the approved receipt, inventory hashes and two prepared
patches. [delivery-commitlint.json](delivery-commitlint.json) retains validation of
each exact commit message using its owning repository's pinned tooling after
`npm ci`. The owner README changes preserve existing line endings and touch two
labels in each repository; unrelated Projects planning work is excluded.

McpCli remote commit `1ffbdd2de19532fe2aca05ecf043f7c2e9084e9c` independently
corrected one Projects 2.0.0 prose paragraph after exact-byte approval. Its table
rows are unchanged. The approved successor and receipt hashes remain unchanged:
derivation now explicitly reads the predecessor snapshot from the canonical
implementation baseline. Verification additionally requires the current 2.0.0
file to match its committed HEAD bytes and every row to match the approved
snapshot; uncommitted modifications or committed row changes still fail. The
remote editorial correction is retained, rather than overwritten by this story.

The expanded suite has 31 passing tests, including committed prose correction
and row-change refusal. Pending fixtures also isolate workflow and delivery
metadata from the real receipt, while real entrypoints validate its actual state.
[delivery-preflight.json](delivery-preflight.json) retains the publication checks.

## Delivered integration and final verification — 2026-11-16

| Repository | Integrated commit | Verified scope |
| --- | --- | --- |
| McpCli | `4fbe3e2c356ca6911d8387218dade9a881d8c902` | Approved Projects 2.1.0 and FrontComposer 1.1.0 inventories and exact approval receipt |
| Projects | `9452fcc104c3e3a41e849037c51439673cd3e209` | README-only PS08/PS09 successor citations and gate text |
| FrontComposer | `f26304dabf7153c7075fa8c4a82dc8fc537c5ed0` | README-only PS03/PS04 successor citations and gate text |

[delivery.json](delivery.json) records the full revisions, raw-commit hashes,
origin/main observations, exact README hashes and successful push outputs.
[labels.json](labels.json) now records integrated state, the separate authorization
and the canonical publication revision. Both successor hashes and the approved
receipt remain byte-identical to the user's approval. Neither owner commit
contains a file other than `README.md`; concurrent Projects planning and test
changes were preserved and excluded. All root reference checkouts and gitlinks
remain unchanged.

[completion-checks.json](completion-checks.json) retains exit codes and both
streams for both approved-completion verifiers, both default entrypoints, all
31 tests, adopted AD-23 verification and the whitespace check. Every command
exited 0 with the real integrated receipts and done workflow statuses. Both
current owner origin/main READMEs contain the exact prepared successor labels,
and McpCli origin/main contains the exact approved inventory and receipt bytes.
The final [secret scan](secret-scan.json) covers the completed evidence packet;
the publication scan is retained unchanged in
[secret-scan-publication.json](secret-scan-publication.json).

The final documentation commit records these verified integrations and done
statuses. Its canonical revision is reported at delivery rather than embedded
in its own hash-bound files. No retirement prerequisite is closed by this delivery.
