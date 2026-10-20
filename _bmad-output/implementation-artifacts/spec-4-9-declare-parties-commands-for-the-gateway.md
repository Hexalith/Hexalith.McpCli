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
  Catalog, lint, validation and fresh-context description review; record
  outstanding C06–C08 and Query dependencies.
- [x] McpCli `evidence/story-4-9/review-pass-2/maintainer-vector-approval.json`
  — obtain explicit maintainer approval bound to the refreshed artifact and
  validator revision; the earlier approval applies to the preserved artifact.

**Acceptance Criteria:**
- Given the scratch Contracts package, when CatalogBuilder inspects it, then
  exactly the four approved Commands appear with valid examples and routing,
  zero diagnostics, and reviewed descriptions.
- Given four vectors naming that exact package version, when the shared
  validator checks artifact identity and command coverage, then all pass and
  maintainer approval records the artifact and validator revision.

## Implementation Notes

### Current review pass 2 implementation (2026-10-20)

G1–G9 and all seven subsequent review patch groups are resolved. Final Release
build passes with zero warnings/errors; required suites pass **2013/2013
Parties**, **315/315 Server** and **201/201 Contracts**, zero failures/skips.
The focused validation class passes **126/126**; both source-layout graph cases
pass. The candidate verifier passes **11/11** tests normally and under Python
optimization. Exact final commands, outputs and hashes are in
`evidence/story-4-9/review-pass-2-final-checks.json`.

The retained `0.0.0-story49` Contracts candidate passes Catalog, examples,
strict discovery, lint, exact artifact identity, four-vector coverage and
both-head routing/error parity. Production McpCli assets are unchanged.
Fresh-context description review returned **PASS**, with no wording changes.
`evidence/story-4-9/review-pass-2/description-delta.json` records seven source
wording deltas and nine Catalog PartyId descriptions; every other Catalog field
and all vector bytes match the prior approved artifact. That earlier artifact
and its approval remain intact. The requesting maintainer explicitly approved the refreshed artifact with
“I approve” after final verification and independent review. Approval-time exact
input preflight and four-vector validation pass; all Story 4.9 acceptance items
are complete.

Implementation started at Parties
`3608e121364198e2ea0643769e680df29bc8efe0`; an independent action committed the
initial fixes as `48bed0054dddca785dd0089d9cfc63384f9ad7c2`. Final verification
ran with Parties HEAD `3e4e6449fcafe511727913a390c411ba292576a5`, including the
working-tree graph tests. The implementation worker made no commits. Current source and
verifier manifests bind the final bytes. Concurrent release-publication edits
were preserved; `source-reconciliation.json` records the independently reviewed
CI documentation hash change without altering the historical receipt.

Current evidence is indexed in `evidence/story-4-9/review-pass-2/verification.md`.
D1–D3 are already tracked at `deferred-work.md:539`, `:542` and `:545`.
The existing production dependency-policy mismatch is already tracked at
`deferred-work.md:480`; this run does not claim that production Manifest gate
passed. Query/effect proof and C06–C08 remain downstream gates. No duplicate
ledger entry, reference edit, enrollment, publication or push was made.

### Earlier accepted implementation

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

### Resumed workflow review (2026-10-20)

All three review layers completed against `/tmp/bmad-4-9-review-z874a5cx.diff`.
The diff includes the preserved original McpCli evidence, the new candidate and
Parties changes from `3608e121364198e2ea0643769e680df29bc8efe0`.
Each finding is classified below before grouping. B = blind hunter,
E = edge-case hunter, V = verification-gap reviewer.

| ID | Finding | Verdict | Evidence and route |
| --- | --- | --- | --- |
| B1 | Selected Builds defaults exceed production dependency-policy pins | medium | Props selects EventStore 3.126.0/Commons 2.30.3 while policy still pins 3.124.0/2.30.1. This gitlink advance predates this resumed run; no reference was changed here. **defer**, already tracked (`deferred-work.md:480`); no duplicate entry. The scratch checks do not claim the production Manifest gate passed. |
| B2 | Nested verifier's default root resolves to `_bmad-output` | low | Candidate `verify-scratch.py:149` retains `parents[4]` after moving down a directory. The documented explicit-root command works, but the default fails. **patch**, grouped with E1. |
| B3 | Optimization removes required integrity assertions | medium | Candidate optimized unittest reproduces artifact-drift acceptance and premature publication. **patch** the active candidate with explicit failures; preserve historical parent evidence. Grouped with E2. |
| B4 | Binding receipt's manifest/artifact hashes are unenforced | medium | `check_recorded_inputs` checks per-file manifests and validator identity but does not compare the manifests/artifact to the receipt's own hashes. A rehashed input could diverge from its binding. **patch** candidate checks and mismatch regressions. |
| B5 | Ignored artifact lacks a durable handoff or rebuild procedure | false | **carried** from pass-1 B4: verification documents the retained local artifact, exact pack command and new-candidate/rebinding requirement. This is an unpublished local increment, with no portable or byte-identical rebuild claim. **reject**. |
| B6 | Missing production assets prevent isolated verification | low | Candidate unconditionally reads `obj/project.assets.json` before its independent scratch restore. A clean checkout fails unnecessarily. **patch** preservation of original bytes or absence. |
| B7 | Python children can select a different interpreter/environment | low | Two commands use literal `python3`, so direct virtual-environment execution can select a different child. **patch** to `sys.executable` and assert the child choice. The recorded dependency prerequisite remains `jsonschema==4.26.0`; no differing installed-version failure was demonstrated. |
| B8 | Parties default path is machine-specific | low | The old local default is machine-specific, but the current candidate's documented reproduction command supplies `--parties-root`. Automatic checkout discovery adds branches to a local evidence helper; **reject** under the low-impact complexity rule. |
| B9 | External verifier processes have no timeouts | low | A tool could hang; none did in this run. A configurable timeout interface adds behavior to the local evidence helper without a demonstrated failing stage. **reject** under the low-impact complexity rule. |
| B10 | Captured subprocess diagnostics disappear on failure | low | `CalledProcessError` does not print its captured stdout/stderr. A stale revision/Catalog/vector failure therefore hides its useful explanation. **patch** diagnostics at the CLI boundary without publishing failed outputs. |
| E1 | Nested verifier default root is incorrect | low | Same verified path-depth defect as B2. **patch**, grouped with B2. |
| E2 | Optimized execution disables verification guards | medium | Same artifact-drift/publication reproduction as B3. **patch**, grouped with B3. |
| V1 | New source-root layouts lack repeatable evaluated-graph coverage | low | Temporary probes pass, but the existing tracked fitness test covers EventStore/Commons/Memories only. Removing either new fallback would silently select the package in that layout. **patch** minimal graph cases; the filed defer recommendation is superseded by the direct test correction. |

All seven patch groups were resolved by the original implementation worker and
passed root's final verification. Candidate guards survive optimization, bind
receipt hashes, preserve absent assets, use the current Python interpreter and
report captured failures; both source-layout graph regressions pass. No intent
gap or bad-spec loopback was identified. Existing D1–D3 and production
dependency-pin work remain in their original ledger entries.

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

### Review Findings

Code review 2026-10-20, pass 2 (Parties range `836b2ba4..e1db1b61`: the story commits `bec09f01` and `e1db1b61`, leaving out the independent `14ad39f8`; code-only scope excluding `references/`, `_bmad-output/`, `tests/conformance-vectors/`, `*.md` and the `PlatformApiPrerequisitesTests` pin reconciliation; 20 files, 989 diff lines; full mode; Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor). No layer failed. Parties HEAD is `e1db1b61` with a clean tree. 40 normalized findings: 23 survive as 9 patch and 3 defer entries, and 17 are rejected. Paths are Parties-relative unless prefixed `mcpcli:`.

The G6 and G7 patches change Contracts description text that the description review, `evidence/story-4-9/catalog.json` and `maintainer-vector-approval.json` (bound to the exact local package) recorded. Applying them needs a fresh scratch pack, Catalog and lint run, and a recorded wording delta, or they carry into the Story 4.10 artifact rebind. The other patches do not change the packed Contracts bytes.

- [x] [Review][Patch] G1 — medium. No test shows that an `update-party` payload carrying only `AddContactChannels`, only `RemoveContactChannelIds` or only `AddIdentifiers` passes the new empty-update rule. Deleting any of those three `HaveSupportedChange` terms keeps every test green while rejecting such updates, including the remove-only and add-only commands the legacy MCP `update_party` tool builds (`src/Hexalith.Parties.Mcp/Tools/PartiesMcpTools.cs:835-848`). Add a validator theory with one valid payload per list (VG, BH). [src/Hexalith.Parties/Validation/UpdatePartyCompositeValidator.cs:151]
- [x] [Review][Patch] G2 — medium. The command `Example` payloads are never run through production deserialization and validation. The only check deserializes them with ad-hoc options and asserts `PartyId`, so an `update-party` example of `{"PartyId":"party-49"}` would pass it and Catalog, then be rejected with `CompositeEmptyUpdate`. In Parties.Tests, deserialize each decorated type's `Example` with `PartiesJsonOptions.Default` and assert its registered validator accepts it. The examples omit the lists, so the same test covers the matrix's "omitted collections retain defaults" over JSON, which no test exercises today (VG, AA, BH). [tests/Hexalith.Parties.Contracts.Tests/McpCliDecorationTests.cs:42]
- [x] [Review][Patch] G3 — low. A null collection, or a null item, also emits "Child PartyId must match PartyId." (`PredicateValidator`, empty property name) beside `NotNullValidator`. That failure cannot be told apart from a real root/child mismatch or the operation cap, and the null rows assert with `ShouldContain`, so it goes unseen. Treat null collections and items as matching in `HaveMatchingChildPartyIds`, since the `NotNull` rules own them, and assert the exact failure list for the null rows (BH, AA, EC). [src/Hexalith.Parties/Validation/CreatePartyCompositeValidator.cs:119; src/Hexalith.Parties/Validation/UpdatePartyCompositeValidator.cs:168]
- [x] [Review][Patch] G4 — low. The package test pins `Hexalith.McpCli.Abstractions` to the literal `1.0.0`, while the line above resolves EventStore through `ResolveMsbuildProperty(..., "HexalithEventStoreVersion")`. The version comes from `HexalithMcpCliVersion` in the Builds catalog, so the next Builds bump of that property turns Contracts.Tests red. Resolve `HexalithMcpCliVersion` the same way (BH, EC). [tests/Hexalith.Parties.Contracts.Tests/Package/ContractsPackageTests.cs:87]
- [x] [Review][Patch] G5 — low. `HexalithMcpCliRoot` probes only Parties' own `references\Hexalith.McpCli`. Every other Hexalith root also probes `..\Hexalith.X` and `..\references\Hexalith.X`, the "existing package/source reference pattern" this spec names. Hexalith.Agents builds Parties from source at `references/Hexalith.Parties`, beside `references/Hexalith.McpCli` (`agents/Directory.Build.props:44-58`), where nested submodules stay uninitialized. In that layout source mode silently compiles Parties.Contracts against the 1.0.0 package while EventStore and the other roots come from source. This reverses pass-1 B7: the Agents layout is the supported layout B7 lacked. Add the two sibling probes (AA, EC, VG). [Directory.Build.props:20]
- [x] [Review][Patch] G6 — low. Every `PartyId` description says legacy braced, parenthesized and X-format GUID IDs have "unproven" McpCli/Gateway reachability, but McpCli always refuses them. `mcpcli:src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:219-227` applies `RoutingResolver.IsAggregateId`, which requires an ASCII letter or digit first and last (`mcpcli:src/Hexalith.McpCli.Core/Catalog/RoutingResolver.cs:127-130`), and child `PartyId` values must equal the root. Only `ContactChannelId` and `IdentifierId` stay plausibly reachable, because String identifiers get no schema pattern. State the refusal in the seven `PartyId` descriptions and keep the child-ID wording (AA). [src/Hexalith.Parties.Contracts/Commands/CreatePartyComposite.cs:17; UpdatePartyComposite.cs:16; ReactivateParty.cs:14; DeactivateParty.cs:14; AddContactChannel.cs:13; UpdateContactChannel.cs:13; AddIdentifier.cs:13]
- [x] [Review][Patch] G7 — low. `ReactivateParty` and `DeactivateParty` reuse the `PartyId` text "shared by the root and every child operation", but those commands have no child operations. Give them their own wording (BH). [src/Hexalith.Parties.Contracts/Commands/ReactivateParty.cs:14; src/Hexalith.Parties.Contracts/Commands/DeactivateParty.cs:14]
- [x] [Review][Patch] G8 — low. The decoration test pins routing but not `CorrelationProperty`, `IdempotencyKeyProperty`, `ActorProperty` or the module's `SerializerOptionsProvider`. Adding an idempotency binding would make McpCli require a key for that operation while the "existing routing" test stays green. Assert all four are null (BH, EC). [tests/Hexalith.Parties.Contracts.Tests/McpCliDecorationTests.cs:35]
- [x] [Review][Patch] G9 — low. `HaveSupportedChange` repeats the per-entry "Type, Value or IsPreferred" predicate. An update whose only entry is empty fails twice (`CompositeEmptyUpdate` and `CompositeEmptyContactUpdate`), and a new mutable member would need edits in both places, or updates carrying only that member would be rejected as empty. Count a non-empty `UpdateContactChannels` list as a change and let the entry rule reject empty entries (BH). [src/Hexalith.Parties/Validation/UpdatePartyCompositeValidator.cs:157]
- [x] [Review][Defer] D1 — medium. Changing a preferred channel's `Type` without `IsPreferred` leaves two preferred channels of the target type [src/Hexalith.Parties/Domain/PartyAggregate.cs:554] — deferred: pre-existing aggregate behavior, also on the standalone path (`:1228`); the apply step keeps the old flag (`:1697`). The new descriptions document the `IsPreferred=true` workaround, and a domain change is outside this story (BH, EC).
- [x] [Review][Defer] D2 — medium. A validation rejection carries one failure per invalid list item, with no cap [src/Hexalith.Parties/Domain/PartyDomainProcessor.cs:610] — deferred: pre-existing, since empty-string removal IDs already produce one failure each. The story's per-item `NotNull` adds null items as a second route, with two failures per null removal ID. A long list of nulls or empty IDs persists a rejection event that grows with the request (EC).
- [x] [Review][Defer] D3 — medium. Parties CI never builds McpCli's Catalog over the Contracts, so an example that the case-sensitive schema enum rejects (for example `"Type":"person"`, which the case-insensitive STJ enum read accepts) ships green [tests/Hexalith.Parties.Contracts.Tests/McpCliDecorationTests.cs:42] — deferred: needs a cross-repository harness, and binding vectors to the complete artifact belongs to Story 4.10 (VG).

#### Rejected

- `low` `Hexalith.McpCli.Abstractions` dependencies and analyzers are not checked transitively (BH, EC). The restored 1.0.0 nuspec has an empty dependency group and no `analyzers/` folder, and NuGet's default `PrivateAssets` keeps analyzers and build assets from flowing. This guards only future versions, and the fix adds a test.
- `low` Length failures carry an empty property name, and their messages hard-code 512 and 4096 (BH). `PartyValidationFailure` drops messages, oversize input is rare, and per-path reporting needs a custom rule.
- `low` `CompositeInputPolicy` lists string members by hand (BH). The list covers every string member of all seven payload types today. This guards only future drift, and the fix adds a reflection test.
- `low` The long identifier description is copied across seven files (BH). The duplication affects developers only, and XML `<summary>` text cannot share a constant, so the refactor would only halve the copies.
- `low` The description test hard-codes its nine types (BH). The list matches every type reachable from the four commands today, and a graph walk adds code against future drift.
- `low` Required names accept empty or null values (BH, EC). This predates the story: no party validator checks names, and `DerivePersonNames` explicitly tolerates empty names. Adding the rules is a domain change outside this story's boundary.
- `low` `DateOfBirth` without an offset takes the host's offset (BH, EC). Verified: STJ reads `1815-12-10` as `-04:57` under `TZ=America/New_York`. The parsing behavior predates the story, the description already asks for an explicit offset, and enforcement needs a converter.
- `low` An `UpdateContactChannel` empty string clears the value, unlike the non-empty rule for additions (BH). The description documents existing aggregate behavior accurately, and forbidding it is a domain change.
- `low` The standalone `UpdateContactChannel` and `AddIdentifier` validators lack the composite guards (BH, EC ×2). The standalone commands are not exposed through McpCli and their validators predate the story. `[Description]` is read only by McpCli, which shows `AddIdentifier` only nested in composites, where the 512-unit bound holds.
- `low` The repeat-deactivation test duplicates a lifecycle test (BH). This is a placement issue, not a defect. An empty event list means NoOp here, because a rejection always carries events.
- `false` Descriptions omit the duplicate-skip behavior and per-member limits (AA). "Must be unique" states what callers must do, and the command descriptions give the 512 and 4096 limits for every string.
- `false` The aggregate's empty-update NoOp branch is now unreachable (EC, deletion). Direct `PartyAggregate.Handle` callers still reach it, and rejecting empty updates in the validator is what the spec requires.

#### Pass 2 patch resolution (2026-10-20)

G1–G9 are resolved by the code and checks indexed in
`evidence/story-4-9/review-pass-2/verification.md`. G1 pins all three sole-list
positive branches; G2 exercises all four examples with production options and
registered validators; G3 pins the complete null failure lists; G4 resolves the
central McpCli version; G5 verifies both sibling layouts; G6/G7 record the exact
repacked wording delta; G8 pins the four null routing/serializer bindings; G9
pins the single empty-contact rejection. Fresh-context description review has
passed. Refreshed-artifact maintainer approval is recorded; all acceptance
items are complete.

### Refreshed artifact approval

The requesting maintainer approved the presented refreshed artifact with
“I approve”. `evidence/story-4-9/review-pass-2/maintainer-vector-approval.json`
binds the explicit approval to the retained package hash, exact vector/source/
verifier manifests and validator revision. Approval-time input preflight and
four-vector validation pass. Prior approval and its artifact remain historical.

The complete source manifest now matches committed Parties revision
`836c315269b196a49455aacf7534c48fba3cb834`, recorded in
`evidence/story-4-9/review-pass-2/completion.json`. This independent commit
includes the final graph tests; approval applies to those exact verified bytes.

### Review Findings (pass 3)

Code review 2026-10-20, pass 3. Scope: the Parties story code from `836b2ba4` to `836c3152`, covering story commits `bec09f01`, `e1db1b61`, `48bed005`, `f48d5b9d` and `836c3152`.

- **Left out:** the files of the independent commits `14ad39f8`, `b776849c`, `3608e121` and `3e4e6449`, and the `e1db1b61` `PlatformApiPrerequisitesTests` pin reconciliation. The `836c3152` layout tests are kept.
- **Code-only scope:** excludes `references/`, `_bmad-output/`, `tests/conformance-vectors/` and `*.md`.
- **Size and mode:** 21 files, 1,199 diff lines, full mode.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed.
- **Parties HEAD:** it has since moved to `a5102784`, which changes CI accessibility only; the reviewed files are identical.
- **Result:** 35 normalized findings. 7 survive as 3 patch and 4 defer entries, 3 of the defers already tracked; 28 are rejected.

Paths are Parties-relative unless prefixed `mcpcli:`.

G10 and G11 change Contracts description text, so the packed Contracts bytes change. Applying them needs a fresh scratch pack, a Catalog and lint run, a recorded wording delta and refreshed maintainer approval. The alternative is to carry them into the Story 4.10 artifact rebind. G12 changes tests only.

- [x] [Review][Patch] G10 — low. The `create-party` description gives a 128-character limit to "PartyId, ContactChannelId, IdentifierId and removal ID entries", but `CreatePartyComposite` has no removal lists; the sentence was copied from `update-party`. Drop "and removal ID entries" from the summary and the `[HexalithCommand]` text (BH). [src/Hexalith.Parties.Contracts/Commands/CreatePartyComposite.cs:9]
- [x] [Review][Patch] G11 — low. `AddContactChannel.Value` and `AddIdentifier.Value` are described as "nonempty", but the composite child rules use FluentValidation `NotEmpty`, which also rejects whitespace-only strings. An agent that sends `" "` gets a rejection the description does not predict. Say the value must contain a non-whitespace character, in both the summary and the `[Description]` (BH). [src/Hexalith.Parties.Contracts/Commands/AddContactChannel.cs:27; src/Hexalith.Parties.Contracts/Commands/AddIdentifier.cs:27]
- [x] [Review][Patch] G12 — low. The spec task says to "pin exact declarations, examples, routing", but `McpCliDecorationTests` only deserializes each `Example` and checks `PartyId`. Any edit that keeps an example valid passes Parties CI, yet it changes the Catalog bytes the vectors and maintainer approval are bound to. Assert each command's `Example` against its literal (AA). [tests/Hexalith.Parties.Contracts.Tests/McpCliDecorationTests.cs:46]
- [x] [Review][Defer] D4 — medium. `update-party` and `deactivate-party` act on a never-created party when its stream holds only rejection events [src/Hexalith.Parties/Domain/PartyDomainProcessor.cs:427; src/Hexalith.Parties/Domain/PartyAggregate.cs:232,870] — deferred: pre-existing aggregate behavior, now reachable through McpCli. New ledger entry (`deferred-work.md:548`) (EC).
- [x] [Review][Defer] Changing a preferred channel's `Type` without `IsPreferred` leaves two preferred channels [src/Hexalith.Parties/Domain/PartyAggregate.cs:554] — deferred: already tracked (`deferred-work.md:539`), pass-2 D1 (EC).
- [x] [Review][Defer] A null removal ID gets two failures (`NotNullValidator` and `NotEmptyValidator`) [src/Hexalith.Parties/Validation/UpdatePartyCompositeValidator.cs:31,37] — deferred: already tracked (`deferred-work.md:542`). Pass-2 D2 names this second route, and G3 pinned both failures (BH).
- [x] [Review][Defer] An `Example` that McpCli's case-sensitive schema enum rejects (`"Type":"person"` or `1`) passes Parties CI [tests/Hexalith.Parties.Contracts.Tests/McpCliDecorationTests.cs:46] — deferred: already tracked (`deferred-work.md:545`), pass-2 D3. VG suggests a cheaper Parties-only check: re-serialize each example with McpCli-equivalent payload options (`JsonStringEnumConverter(allowIntegerValues: false)`) and compare (VG).

#### Rejected (pass 3)

- `false` — The McpCli root misses the `..\..` layout used when McpCli holds Parties in `references/` (BH, AA, EC). McpCli never builds its `references/Hexalith.Parties` from source: no McpCli project or script references it, and module enrollment is PackageReference-only by policy. Source mode is also opt-in, because `UseHexalithProjectReferences` defaults to false in every configuration (`Directory.Build.props:23-27`). FrontComposer's `..\..` probe serves a repository that builds Parties; McpCli does not.
- `low` — The repo's own `references\Hexalith.McpCli` candidate and its precedence are never evaluated, and `HexalithMcpCliRoot` is fetched but not asserted (VG, BH). The claim holds. However, source mode is opt-in, deleting or reordering `Directory.Build.props:20` is unlikely, and the fix restructures the layout test (its nested-absence assertion plus a two-location case).
- `low` — `Hexalith.McpCli.Abstractions` transitive dependencies are not checked (VG, BH, EC). Carried from pass 2: the restored 1.0.0 nuspec has no dependencies, and McpCli's own dependency gate rejects any unapproved direct package on Abstractions (`mcpcli:tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:586`). The check would guard only a future version, and the fix adds a test. The nuget.org point is `false`: an unpublished pinned version fails restore loudly.
- `low` — Descriptions on shared child types fit only the composite path, and the standalone validators lack the new bounds, empty-update and enum rules (BH ×2, EC). Carried from pass 2: the standalone commands are not exposed through McpCli. The summaries state a stricter limit than the standalone path enforces, so a caller who follows them is never rejected. The fix needs validator changes or repacked wording.
- `low` — Each description appears in both `<summary>` and `[Description]`, with seven `PartyId` copies (BH). Carried from pass 2: drift would affect developers only, and an XML summary cannot reference a constant.
- `low` — Required names accept blank, empty or null values, and the boundary test uses a 512-space `FirstName` (BH, EC). Carried from pass 2: this predates the story, and name rules are a domain change outside its boundary.
- `false` — The duplicate-ID behavior is described wrongly (BH). The description states the caller's obligation ("must be unique ignoring case"). A caller who follows it never reaches the aggregate's exact-duplicate skip or case-variant rejection. Same verdict as pass 2.
- `low` — An exact duplicate `ContactChannelId` within one composite is silently skipped (EC). Real, but it is pre-existing aggregate behavior (`src/Hexalith.Parties/Domain/PartyAggregate.cs:151-157`), compliant callers never hit it, and rejecting it is a domain change.
- `low` — An update carrying both detail blocks passes validation and is rejected only after state access (BH). This is pre-existing aggregate behavior, and the descriptions already say such an update is rejected. The spec requires rejection before state access only for empty updates, and the fix adds a domain rule.
- `low` — The operation cap, the child-ID match and the 128-character ID guards share the generic `PredicateValidator` code (BH). These rules predate the story, and new error codes would be public surface.
- `false` — The personal-data leak check exercises only one marker row (BH). Every rejection passes through the single mapping at `src/Hexalith.Parties/Domain/PartyDomainProcessor.cs:610` into `PartyValidationFailure { PropertyName, ErrorCode }`. The exact-record assertions would fail if a field carrying values were added, and the marker row covers the shared serialization path.
- `low` — `OversizedCompositeStrings` rows do not carry the mutated path, and the string lists are hand-coded (BH). The missing path only affects diagnostics when the test fails; the hand-coded lists are carried from pass 2.
- `low` — The deactivation guard order ("unchanged only after these checks") is not pinned for an already-inactive party (BH). The claim holds: `tests/Hexalith.Parties.Server.Tests/Aggregates/PartyAggregateRestrictionTests.cs:127` and `PartyAggregateErasureTests.cs:148` use active states. But the aggregate order predates the story, a reorder is unlikely, and the fix adds tests.
- `false` — The exposed names `reactivate-party` and `deactivate-party` are not asserted (BH). `Name` is pinned to null and the CLR type names are fixed, so McpCli's kebab-case derivation makes the names deterministic. A rename would also break compilation of the typed tests.
- `false` — The examples omit child lists and `Type` strings (BH). The spec only requires valid examples. The schema carries the enum names, and the descriptions state the child `PartyId` rule.
- `false` — The update-contact `IsInEnum` rule is outside the approved scope (AA). It mirrors the existing `AddContactChannels` rule (`src/Hexalith.Parties/Validation/UpdatePartyCompositeValidator.cs:75-77`), only tightens validation and breaks no "Never" item. Its only fixes would be a spec edit or removing a correct guard.
- `false` — The envelope-tenant matrix row has no Parties-side test (AA). Parties controls only the absence of `TenantProperty`, `FixedTenant` and any tenant member, which `McpCliDecorationTests` pins. Using the envelope tenant is McpCli and Gateway behavior.
- `false` — `UpdateContactChannel.Value = ""` stores an empty value (EC). This is documented, intended clearing behavior; carried from pass 2.
- `low` — AdminPortal shows root-level `Composite*` failures as "required" on the Type field (EC). Real: `src/Hexalith.Parties.AdminPortal/Components/CreateEditPartyPage.razor:543-573` maps an empty property name to `TypeValue`. But only a name over 512 units, or input over 4,096 units in total, from an admin form triggers it, and the fix adds an AdminPortal mapping branch.
- `low` — Per-item rules still iterate oversized lists (EC). The cost is linear, a constant factor over the existing per-item rules; the growing failure count is already tracked as D2.
- `false` — Commit `e1db1b61` overclaims the gateway safeguards (EC). Its safeguards are the spec's composite-scoped C03/C04 protections. The phantom-party path is deferred separately as D4.

#### Pass 3 patch resolution (2026-10-20)

G10–G12 are committed and pushed as Parties `e3e25fd144cec0f67623dec5c311310ee5f08d8c`, which changes only these four files:

- **G10:** the `create-party` summary and `[HexalithCommand]` text now read "PartyId, ContactChannelId and IdentifierId have a tighter 128-character limit".
- **G11:** both `Value` summaries and `[Description]`s now require "at least one non-whitespace character".
- **G12:** `McpCliDecorationTests` pins all four `Example` literals. A mutation that changed the `create-party` example to `"LastName":"Byron"` failed the test, which then passed again once the file was restored.

**Checks:**

- `dotnet build tests/Hexalith.Parties.Contracts.Tests -c Release -warnaserror` and the same build for `tests/Hexalith.Parties.Tests` both pass with 0 warnings and 0 errors.
- `dotnet test tests/Hexalith.Parties.Contracts.Tests --no-build -c Release` passes **201/201**.
- `PartyDomainProcessorValidationTests` passes **126/126**.

The full solution build and the Server.Tests and Parties.Tests suites were not rerun. Those projects only consume the description text.

**Packed artifact:** G10 and G11 change the packed Contracts description bytes, so the approved `0.0.0-story49` artifact and its maintainer approval still describe the earlier wording. Neither was refreshed. The wording delta goes into the Story 4.10 artifact rebind, which repacks from current source.

Concurrent Parties working-tree changes from DW-77 were left untouched.
