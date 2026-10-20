---
title: '4.9 Declare Parties commands for the gateway'
type: 'feature'
created: '2026-10-20'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'b616db3092a9b1c5af196538a3de37a5c7f2d7ca'
parties_baseline_commit: '4d4be476687cff4210774ec62558131ff8659558'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The four approved Parties writes lack McpCli declarations. Composite
validation also lacks the bounded-input and empty-update protections assigned
by inventory C03/C04.

**Approach:** Decorate Commands upstream, complete validation, author four
vectors and verify declarations through a scratch McpCli host.

## Boundaries & Constraints

**Always:** Follow inventory A1: module `parties`, String identifiers, domain
`party`, full-type-name wire convention, root `PartyId` routing. Expose exactly
`create-party`, `update-party`, `reactivate-party`, `deactivate-party`; the first
two override their composite CLR names. Tenant remains envelope-owned. Add
Abstractions 1.0.0 through central versions and the existing package/source
reference pattern. Describe every exposed member, including nested types;
examples must validate. Preserve tighter domain rules, root/child equality,
the configured composite cap (default 100), lifecycle guards and safe repeated
soft deactivation. Reject unsupported empty updates before state access.

**Approved string policy (2026-10-20):** Raw UTF-16 length ≤512 per string and
≤4096 total, counting whitespace and every root, nested, child and removal
string occurrence, including repeated IDs. Preserve supplied values and the
tighter 128-character identifier rule. Enforce through both shared composite
validators for all callers. The total budget may bind before the operation cap;
document the stricter behavior versus legacy trimmed counting.

**Never:** Adopt `ICommandContract`, migrate wire names, decorate excluded
operations, introduce Queries or change McpCli runtime code. Do not edit
`references/`, publish, enroll, push, retire the legacy host, change authorization
or convert legacy IDs. C06–C08 remain explicit replacement/retirement gates.

## I/O & Edge-Case Matrix

| Scenario | Input / state | Expected behavior |
| --- | --- | --- |
| Routing | Valid String `PartyId`, configured tenant | Existing full CLR wire name; envelope tenant |
| Bounds | At / above approved field, total or operation limit | Accept valid boundary / reject excess before state access |
| Child IDs | Child `PartyId` differs from root | Existing validation rejection |
| Nulls | Explicit null collection or collection item | Validation rejection; omitted collections retain defaults |
| Empty update | PartyId only, or contact update with no mutable value | Validation rejection; no mutation events |
| Repeat deactivation | Already inactive, otherwise permitted | No additional deactivation event; no erasure |

</frozen-after-approval>

## Code Map

Paths below belong to `/home/administrator/projects/hexalith/parties`.

- `src/Hexalith.Parties.Contracts/Commands/` — four existing targets; nested
  `AddContactChannel`, `UpdateContactChannel`, `AddIdentifier` use enum converters.
  `../ValueObjects/{PersonDetails,OrganizationDetails}.cs` hold nested strings.
- `src/Hexalith.Parties/Validation/{CreatePartyCompositeValidator,UpdatePartyCompositeValidator}.cs`
  — reuse cap and child-ID checks; null lists currently throw during enumeration.
- `src/Hexalith.Parties/Domain/PartyDomainProcessor.cs:85` — validation precedes
  state unprotection; existing rejection path omits input values.
- `src/Hexalith.Parties/Domain/PartyAggregate.cs:274,884` — empty-update NoOp
  and safe inactive deactivation; preserve unrelated lifecycle behavior.

## Tasks & Acceptance

**Execution:**
- [x] `Directory.Build.props`, `src/Hexalith.Parties.Contracts/Hexalith.Parties.Contracts.csproj`
  — add the Abstractions package/source pair.
- [x] `src/Hexalith.Parties.Contracts/{Module.cs,Commands/{CreatePartyComposite,UpdatePartyComposite,ReactivateParty,DeactivateParty}.cs}`
  — add marker, routing, examples and descriptions; document nested members in
  the Code Map types and mark scalar identifiers.
- [x] `src/Hexalith.Parties/Validation/CompositeInputPolicy.cs` and both composite
  validators — implement approved bounds, null guards and supported-change checks.
- [x] `tests/Hexalith.Parties.Contracts.Tests/McpCliDecorationTests.cs` — pin
  exact declarations, examples, routing and nonempty descriptions.
- [x] `tests/Hexalith.Parties.Tests/Domain/PartyDomainProcessorValidationTests.cs`
  — test the matrix, rejection events and no state access; retain lifecycle tests.
- [x] `tests/Hexalith.Parties.Tests/FitnessTests/ArchitecturalFitnessTests.cs`,
  `tests/Hexalith.Parties.Contracts.Tests/Package/ContractsPackageTests.cs` —
  admit exactly the new Abstractions dependency, preserving other boundaries.
- [x] `tests/conformance-vectors/mcpcli-v1/*.json`, `README.md`,
  `docs/api-contracts.md` — four vectors, prerequisite writes and semantic
  `parties.get-party` postconditions; document limits and explicit typed payloads.
- [x] McpCli `evidence/story-4-9/` beside this spec — record scratch-package hash,
  Catalog, lint, validation, fresh-context description review and maintainer
  vector approval; record outstanding C06–C08 and Query dependencies.

**Acceptance Criteria:**
- Given the scratch Contracts package, when CatalogBuilder inspects it, then
  exactly the four approved Commands appear with valid examples and routing,
  zero diagnostics, and reviewed descriptions.
- Given four vectors naming that exact package version, when the shared
  validator checks artifact identity and command coverage, then all pass and
  maintainer approval records the artifact and validator revision.

## Implementation Notes

Implemented in the owning Parties working tree, starting from clean
`836b2ba4aa41cdf8a7812b97a5da7c08896c0c7c`; the approved baseline above is
preserved. The intervening commit was CI-only. Concurrent AppHost, publish,
CI, documentation and references changes belong to other work and were
preserved. Story-owned paths are listed in
`evidence/story-4-9/source-files.sha256.json`.

Final full Release restore/build passed with zero warnings/errors. The three
required project suites pass: Parties.Tests **2004/2004**, Server.Tests
**315/315**, Contracts.Tests **201/201**, zero failures/skips. The focused
validation class passes 119/119; verifier unit checks pass 7/7. Exact commands
and logs are in `evidence/story-4-9/accepted-checks.json` and
`evidence/story-4-9/final-checks.json`. Every matrix row is mapped to executed
passing evidence in `evidence/story-4-9/matrix-test-audit.md`.

The final isolated artifact passes Catalog, examples, strict discovery, lint,
exact package identity, four-command coverage and CLI/MCP routing. Original
vectors retain their Query postconditions; temporary routing-smoke copies omit
only unavailable postconditions. Full semantic execution remains downstream.
Fresh-context description review initially failed, then returned PASS WITH
NOTES; all notes were corrected with exact wording deltas and no domain change.
The final evidence index is `evidence/story-4-9/verification.md`.

An independent commit advanced Parties to
`14ad39f85eae152c7a7e22ff261cc534ff5dab1e` during this work. Two stale
current-selection receipt failures were reconciled to that committed graph;
historical approvals and exact checks were preserved. The complete verification
then passed. `selection-reconciliation.json` records the facts and focused checks.

The requesting maintainer explicitly approved the final vector/artifact record
with “I approve” on 2026-10-20. `maintainer-vector-approval.json` binds that
approval to the exact local package, vector hashes and validator revision; the
same bytes passed an approval-time manifest and vector recheck. All acceptance
tasks are complete. The approved routing and raw-string policy are unchanged.

## Spec Change Log

## Review Triage Log

Pass 1 (2026-10-20): blind hunter B, edge-case hunter E, verification-gap reviewer V.
Every finding is recorded before grouping. E returned no findings.

| ID | Finding | Verdict | Evidence and route |
| --- | --- | --- | --- |
| B1 | Scratch discovery inherits operator profiles/environment | medium | `verify-scratch.py:65` invokes the host without an isolated profile/env; `run_loopback.py:220` demonstrates the existing isolation convention. Configured sessions can affect discovery. **patch** |
| B2 | Scratch verifier does not check recorded vector/source hashes | medium | It reads live vectors at line 76 but never loads the manifests, so changed valid inputs can pass against stale receipts. **patch**, grouped with B3 |
| B3 | Scratch host/validator are not bound to the recorded revision/hash | medium | Current source is copied at line 31 and current validator run at line 86 without checking the receipt's revision/hash. **patch**, grouped with B2 |
| B4 | Ignored nupkg lacks an acquisition/rebuild procedure | false | `verification.md` already records restore/build, the exact local pack command and retained artifact path. This approved increment is local/unpublished; portable byte-identical rebuilds or artifact publication are not claimed. **reject** |
| B5 | Scratch evidence is overwritten before all gates finish | medium | Catalog/check outputs are written at lines 58–73 before routing and vector validation. A failed run can leave mixed receipts. Collect outputs and publish after successful checks. **patch** |
| B6 | Create vector omits child creation assertions | medium | The invocation adds a contact and identifier but the Query fixture/assertions check only root/person/lifecycle fields. Lost child effects would escape that vector. **patch** |
| B7 | McpCli source discovery lacks sibling/workspace fallbacks | low | The root-declared `references/Hexalith.McpCli` path works; callers can explicitly set `HexalithMcpCliRoot`. No failing supported layout was demonstrated, and additional auto-detection branches exceed a direct correction. **reject** |
| B8 | ID descriptions omit existing syntax restrictions | low | Length alone does not communicate `PartyIdentifier.IsValid` / `RoutingResolver.IsAggregateId` character and endpoint rules. Correct wording, distinguishing legacy reachability, without changing validators. **patch** |
| B9 | Contains-code assertions can hide removed guards | false | New guard codes are unique to their predicates; removing a guard removes its asserted code. Existing generic-predicate fixtures isolate the invalid cap/ID condition while other predicates pass. No concrete masking mutation was supplied; V independently found a different positive-branch gap. **reject** |
| B10 | Description-review metadata still has a null reviewer/pending text | low | `description-review.json` has a null reviewer despite the recorded round-2 PASS WITH NOTES and exact wording delta. Reconcile the receipt and prose. **patch** |
| V1 | Organization-only supported-change branch has no positive validator/processor test | medium | Pre-verified gap: removing the OrganizationDetails term rejects valid organization replacements, while the positive boundary case supplies both detail blocks and the existing aggregate test bypasses validation. **patch** |

Patch groups: B1; B2+B3; B5; B6; B8; B10; V1. No intent gap,
bad-spec loopback or new deferred item was identified.

All seven patch groups are resolved and covered by the final passing checks.
No review finding remains open. Final package/Catalog identity and direct
wording deltas and explicit maintainer vector approval are recorded.

## Design Notes

Pack locally as `0.0.0-story49`; no release is authorized. Query postconditions
use the approved 4.10 routing and remain unexecuted until those Queries exist.
4.10 rebinds vectors to the complete artifact; 4.11/4.13 prove parity and effects.

## Verification

- In Parties: `dotnet restore Hexalith.Parties.slnx`, then
  `dotnet build Hexalith.Parties.slnx --no-restore -c Release -warnaserror`.
- Run Contracts.Tests, Server.Tests and Parties.Tests individually with
  `dotnet test tests/<Project> --no-build -c Release`; use the documented fallback
  ladder for environment blockers.
- Pack Contracts, build an isolated generic host against it, and check discovery,
  lint and `--strict`. Run McpCli `tools/conformance-vectors/v1/validate.py` with
  the artifact, exact identity and four operation names. Do not change McpCli's
  production enrollment or restored assets.
