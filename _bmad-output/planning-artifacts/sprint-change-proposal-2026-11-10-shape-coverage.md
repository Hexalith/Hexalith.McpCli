---
title: Cover enrolled modules by operation shape, not by operation
created: '2026-11-10'
status: proposed
review_mode: batch
source_action: 'Product-owner question on 2026-11-10 ("is this over-engineered? It creates a dependency between mcpcli and all other modules. Does this requirement give a real ROI?"), refined in party mode and advanced elicitation (P1–P6 applied by the product owner); correct-course invoked with "apply recommended"'
baseline: d6f7ffb
approval: pending
---

# Sprint Change Proposal: Cover Enrolled Modules by Operation Shape

## 1. Issue summary

McpCli's enrollment gates require one approved conformance vector and one live plan per decorated operation, bind every vector to the exact Contracts package version, and fail when an enrolled package contains any decorated operation that its release inventory does not list. The rule is stated in:

- PRD FR-20 (`prd.md:420`, `:426`, `:427`), NFR-7 (`:455`), the module-author checklist item 9 (`:489`) and SM-4 (`:533`);
- architecture AD-16 (`ARCHITECTURE-SPINE.md:155`: "matched by canonical Operation Name to every decorated Operation") and AD-21 (`:189`: "Missing, extra, mismatched, duplicate, or unapproved rows fail");
- the Folders plan (`sprint-change-proposal-2026-11-10.md:73`: "every type Folders publishes must be an included row with a vector") and Story 6.1.

It is enforced in CI by `EnrolledModuleCoverageTests` (`tests/Hexalith.McpCli.Core.Tests/EnrolledModuleCoverageTests.cs`) and `tools/conformance-vectors/v1/check_enrolled.py`. Nothing is rejected at runtime: a released McpCli exposes every decorated type in an enrolled package.

**Problem.** The rule couples McpCli's green build to every module's exact operation set and version. Every module release, including a patch that changes no operation, needs a McpCli change: version-rebound vectors, a re-hashed `approval.json` and a fresh approval. Every new decorated operation also needs an inventory row, a vector and a live plan before the pin can move. Most of that work re-tests McpCli's generic code rather than anything module-specific.

**Evidence.**

- **Shapes vs. operations.** A survey on 2026-11-10 grouped the 21 enrolled operations by the routing and envelope fields that McpCli's generic code branches on. They reduce to **6 shapes**: 3 for Parties and 3 for Tenants. The public `describe` envelopes from the Release build give 5; the decorations in the reference source split one Parties Query group into two. The 21 existing vectors therefore exercise 6 code paths. Folders would add up to 48 vectors and 48 live plans under the current rule (`sprint-change-proposal-2026-11-10.md:57`, `:73`).
- **Cost.** In Epic 4, production `src/` changed by +235/−43 lines. Vectors, plans and fixtures grew by +11,123 lines, C# tests by +10,452, Python tests by +10,216 and Python tooling by +6,103, plus about 1.04M lines of evidence (`epic-4-retro-2026-11-06.md:16-23`). Today `tools/` holds about 11.8k lines of Python against about 6.5k lines of C# in `src/`.
- **Rebind churn.** Parties' 7 vectors were rebound mechanically to a new version, and Tenants' 14 were refreshed for 7.0.4 with only version metadata changed (`tools/conformance-vectors/v1/README.md`).
- **Live-lane noise.** Epic 4 ended red: all 21 vectors failed in the live lane after a gitlink move. The failures came from mismatched dependency versions, not from McpCli defects (retro F1). The EventStore 4.0.4 query-selector break affected all three Parties queries, which a single Query smoke would also have caught.
- **What the veto actually protects (the steelman).** `Hexalith.McpCli.Abstractions` has no destructive or confirmation-required marker, and the MCP head marks every send as `Destructive = !readOnly`. The "extra fails" rule is therefore currently the only McpCli-side review of whether a new operation is safe for an agent. This proposal replaces that review with an explicit consent rule rather than removing it silently.
- **P6 precondition (exhaustive check for operation-specific catches).** No defect in the Epic 4 record was caught first and only by a per-operation vector. The search did expose two gaps in the drafted shape rule: projection selectors and a keyed second-Command scenario. Both are now part of the proposal; see [§2.5](#25-p6-precondition-result).

**Issue type:** a failed approach that needs a different solution. The over-specified per-operation gate does not scale beyond two modules.

## 2. Impact analysis

### 2.1 Epic impact

| Epic | Impact |
| --- | --- |
| 1–4 (done) | None. v1 coverage evidence produced under the per-operation rule remains valid. No completed story text changes. |
| 5 (in progress) | Adds **Story 5.12, Gate Enrolled Modules by Operation Shape**. Approving this proposal is the MR10 product-owner decision that lets 5.12 become `ready-for-dev`. Stories 5.3–5.5 (Parties) are unchanged; their vectors stay. |
| 6 (backlog) | Story 6.1 needs shape vectors and one live vector per operation kind, not one vector and plan per included operation. A provider double is needed only if a chosen live vector requires one. Story 6.2 keeps per-row retirement checks, which a Folders upstream test that drives a McpCli head may supply. 6.1 now also depends on 5.12. |

No epic becomes obsolete. Epic order is unchanged; 5.12 must finish before 6.1 starts.

### 2.2 Artifact conflicts

| Artifact | Change |
| --- | --- |
| PRD `prd.md` | FR-1 (consent bullet), FR-20 (paragraph and two consequences), NFR-7, author checklist item 9, SM-4. The FR-20 Tenants bullet and the "Before the v1 release gate" sequencing (`:561`) are v1 history and stay unchanged. |
| Architecture `ARCHITECTURE-SPINE.md` | AD-16 (Prevents and five rule segments), AD-21 (rule sentence), plus a new "PRD Amendments" bullet. |
| Epics `epics.md` | FR-map clause, Story 6.1 (five segments plus a dependency), Story 6.2 (one AC), new Story 5.12, a `changeProposals` frontmatter entry. |
| Sprint status | New `5-12` row; updated `6-1` comment. |
| UX | Not applicable: no user-facing CLI or MCP behavior changes. |

### 2.3 Secondary artifacts (changed by Story 5.12, not by this proposal)

- `README.md`: Gateway boundary, enrollment (`:458`, `:481`) and live-lane wording (`:628`).
- `tools/conformance-vectors/v1/README.md` and `tools/inventory-coverage/v1/README.md`.
- `AGENTS.md:84`, copied to `CLAUDE.md` and `.github/copilot-instructions.md`.
- Abstractions XML docs on `HexalithCommandAttribute` and `HexalithQueryAttribute`.
- Gate code: `EnrolledInventoryCoverageGate`/`InventoryCoverageGate`, `check_enrolled.py`, `verify_artifact.py`, `validate.py --operations-file`, the `approval.json` contract (artifact-hash binding removed), and their tests.
- `.github/workflows/ci.yml` `topology-vector-discovery`: still lists the exact approved cases.

Production `src/` behavior is unchanged; only XML documentation changes.

### 2.4 Platform compliance

This was checked against Hexalith.Platform at the pinned reference `01e5b653`. The change touches no module manifest, run/debug entry point, checkout `bin`/`obj`, or submodule. Platform's README and `docs/domain-module-enrollment.md` contain no vector or per-operation coverage rule; their "inventory" is a hosting inventory. The AI.Tools baseline (`hexalith-llm-instructions.md` "Hexalith MCP and CLI ownership" and `hexalith-mcpcli-migration-instructions.md`) requires only owner-approved inventories before retirement. It does not require per-operation vectors, so no upstream change is required.

### 2.5 P6 precondition result

On 2026-11-10 an exhaustive search covered the Epic 4 retrospective, `deferred-work.md:473-820`, specs 4-5 and 4-8 to 4-18, the retro-item specs and the `evidence/story-4-1*` Markdown files, and confirmed the fixes from CI job logs. It found **no defect that a per-operation vector detected first and that a vector for another operation of the same shape would have missed.** No dedicated per-operation vector is required.

What the vectors did catch, and what that implies for the shape rule:

| Finding | First detected | Implication |
| --- | --- | --- |
| The Parties host's broad string-enum converter dropped projection acknowledgements (Parties `d83fec24`) | 4.13 live lane: `update-party`, `deactivate-party` and `reactivate-party` failed; `create-party` and all three queries passed (spec-4-13:52, :80) | The defect affected the whole host, but showed only in vectors that send a **second Command to an existing aggregate and read it back**. A shape scheme that picked `create-party` would have missed it. → The live Command vector must follow that scenario (C2, C7). |
| Legacy Parties projection selectors were refused by the EventStore 4.0.4 native catalog (HTTP 503) | Live lane: all 7 Parties vectors failed (spec-4-18:264-271) | This was a cohort-wide defect, and one Query smoke catches it. But the presence of a **projection selector** is a code path the drafted shape key did not include. → Added to the shape tuple. |
| McpCli `bd2f8ee` dropped `projectionActorType` from the query request | Loopback replay, alongside 7 failing unit tests (CI 41647054451) | Generic; any Parties Query vector catches it. This is the selector path again. |
| Keyed idempotency admission returned 503 | A human Claude Desktop session (spec-4-17:93-97); **no vector in either module sends an idempotency key** | Neither per-operation nor per-shape coverage caught it. → The live Command vector supplies a caller idempotency key. |
| The `GetTenant` handler read a rejection-only checkpoint as a real tenant; the same flaw exists in `GetTenantUsers` | The independent smoke and code review; the `get-tenant` vector passed (spec-4-18:262-264; `deferred-work.md:780`) | Happy-path vectors miss handler state defects. This supports P2: handler tests belong in the module repo. The independent smoke stays. |

All other failures were infrastructure, runner or dependency-cohort problems with no dependence on a particular operation: Abstractions version skew, Dapr port collisions, bootstrap 500/503 flakes, closure drift and runner bugs.

**Refinements adopted from P6 (shown in C2, C7, C11 and C12):**
- The shape tuple gains the **query projection selector** (`projectionType`, `projectionActorType`, or none).
- For new enrollments, each module's live Command vector **creates an aggregate in a prerequisite, then submits a second Command to it with a caller-supplied idempotency key and reads the effect back with a postcondition Query.** This is an authoring and approval rule. The CI gate checks only that at least one live vector exists per declared kind, so the existing Parties and Tenants sets are not invalidated. They adopt the keyed scenario at their next vector amendment.

## 3. Recommended approach

**Option 1, direct adjustment (selected).**
- Amend the PRD and architecture text.
- Add Story 5.12 to implement the gates.
- Reword Stories 6.1 and 6.2.

Effort: Medium, mostly Story 5.12 (one C# gate, three Python gates, docs and tests). Risk: Low to Medium. Timeline: it removes roughly 48 vectors, 48 live plans and possibly the G6 provider double from Epic 6.

**Option 2, rollback (not viable).** Deleting the existing Parties and Tenants vectors gains nothing: they are cheap in loopback, and the shape gate needs them. No existing vector, plan or inventory is deleted.

**Option 3, MVP review (not applicable).** v1 has shipped; neither scope nor goals change.

**Trade-offs accepted:**
- McpCli no longer blocks a module's newly decorated operations; the owner's decoration is the consent, and the Gateway still authorizes every call (AD-22).
- A routing-string typo (`Domain`, `WireType`, `ProjectionType`, `ProjectionActorType`) in an operation without a McpCli vector is caught by the module's own tests rather than by McpCli CI.
- The consent rule is documented but not mechanically enforced. Name-based heuristics such as linting on "delete" or "purge" were rejected as guesswork.

**Alternatives rejected:**
- Per-operation vectors without version binding (Option A in the ADR): McpCli would still have to change with every module release.
- Moving all module evidence into module repos (Option C): nothing would then cover the generic translation unless every module adopted it.

## 4. Detailed change proposals

Each block replaces its OLD text exactly once.

### C1. PRD FR-1: decoration is consent

File `prds/prd-mcpcli-2026-09-21/prd.md`, FR-1 consequences.

OLD:
```
- A type with the command attribute enters the Catalog with kind `write`; with the query attribute, kind `read`.
```
NEW:
```
- A type with the command attribute enters the Catalog with kind `write`; with the query attribute, kind `read`.
- Decorating a type is the owning maintainer's consent to expose that Operation to agents and operators through the Gateway without human confirmation; UI-only and human-confirmation operations are never decorated (§1). The Gateway still authorizes every call (AD-22). McpCli does not re-approve decorated Operations: one that no FR-21 inventory row mentions is reported, not refused (AD-21).
```
Rationale: P1. This replaces the implicit review that AD-21's "extra" failure provided.

### C2. PRD FR-20: vector coverage paragraph

OLD:
```
Each Operation in `list_operations` has one versioned, maintainer-approved conformance vector in its owning Module repository.
```
NEW:
```
Versioned, maintainer-approved conformance vectors in the owning Module repository cover every Operation Shape in `list_operations`: the combination of kind, Identifier Kind, Wire Type convention, tenant source (exact `platformScope`, Module `fixedTenant`, or public), aggregate-identifier source (property, constant, or none), query projection selector (`projectionType`, `projectionActorType`, or none), and required idempotency key that the Catalog derives from the decorations (AD-16). Per-Operation handler semantics are tested in the owning Module repository. v1 coverage evidence produced under the earlier one-vector-per-Operation rule remains valid.
```
OLD:
```
Separately, a blocking Aspire test executes each vector once against a running EventStore and asserts Gateway acceptance or a returned Query document plus the vector's semantic checks (NFR-7).
```
NEW:
```
Separately, a blocking Aspire test executes each approved live vector once against a running EventStore and asserts Gateway acceptance or a returned Query document plus the vector's semantic checks (NFR-7). Each Module has at least one live vector per Operation kind it declares; for a new enrollment, its live Command vector creates an aggregate in a prerequisite, then submits a second Command to it with a caller-supplied idempotency key and reads the effect back with a postcondition Query.
```
Rationale: P2 and P3.

### C3. PRD FR-20 consequences

OLD:
```
- A generic runner rejects a missing, duplicate, or stale vector for any listed Operation.
```
NEW:
```
- A generic runner rejects an Operation Shape without an approved vector and a duplicate or stale vector. A vector is stale when its Operation is absent from the restored Catalog or the Catalog rejects its inputs.
```
OLD:
```
Each vector names its owning Contracts package ID and exact version. The shared validator compares these with the owning immutable Contracts release artifact before Module maintainer approval; the runner compares them with the flagged restored production package before loopback or live execution, rejecting vectors for another package version even when the Operation Name matches.
```
NEW:
```
Each vector names its owning Contracts package ID and the version it was authored against. The shared validator compares the package ID with the owning Contracts release artifact before Module maintainer approval; the runner validates every vector against the flagged restored production package before loopback or live execution. A version difference alone is reported, not failed, and needs no re-approval.
```
Rationale: P3 and P5.

### C4. PRD NFR-7

OLD:
```
while a blocking Aspire test runs each approved Module vector once against EventStore
```
NEW:
```
while a blocking Aspire test runs each Module's approved live vectors (at least one per declared Operation kind) once against EventStore
```

### C5. PRD module-author checklist item 9

OLD:
```
9. Version and approve one conformance vector for every exposed Operation; pass the generic vector-to-Catalog and live semantic gates (FR-20).
```
NEW:
```
9. Version and approve conformance vectors that cover every Operation Shape the Module uses, with at least one live vector per declared Operation kind; test each Operation's handler semantics in the Module repository; pass the generic shape-coverage and live gates (FR-20). Decorate only Operations you consent to expose to agents without human confirmation (FR-1).
```

### C6. PRD SM-4

OLD:
```
- **SM-4 Heads agree.** For every Operation, tests run
```
NEW:
```
- **SM-4 Heads agree.** For every approved vector, together covering every Operation Shape, tests run
```
OLD:
```
The separate FR-20 live lane executes every approved vector once against EventStore and checks its semantic outcome.
```
NEW:
```
The separate FR-20 live lane executes each approved live vector once against EventStore and checks its semantic outcome.
```

### C7. Architecture AD-16

File `architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md`.

OLD:
```
- **Prevents:** raw equality assertions across two state-changing live calls; schema-shaped but invalid domain inputs; a non-blocking or unbuildable Aspire release gate.
```
NEW:
```
- **Prevents:** raw equality assertions across two state-changing live calls; schema-shaped but invalid domain inputs; a non-blocking or unbuildable Aspire release gate; a per-Operation vector set that turns every Module release into a McpCli change.
```
OLD:
```
Each v1 Module owns vectors in its repository, matched by canonical Operation Name to every decorated Operation.
```
NEW:
```
Each enrolled Module owns vectors in its repository that together cover every Operation Shape in its Catalog: the tuple of kind, Identifier Kind, Wire Type convention, tenant source (exact `platformScope`, Module `fixedTenant`, or public), aggregate-identifier source (property, constant, or none), query projection selector (`projectionType`, `projectionActorType`, or none), and required idempotency key, derived from Catalog descriptors.
```
OLD:
```
Each vector declares its owning Contracts package ID and exact version; the shared validator compares these with the owning immutable Contracts release artifact before maintainer approval and with the flagged restored production package before both runner lanes, so a reused Operation Name under a changed package version is stale.
```
NEW:
```
Each vector declares its owning Contracts package ID and the version it was authored against; the shared validator compares the package ID with the owning Contracts release artifact before maintainer approval, and the runner validates every vector against the flagged restored production package before both lanes. A vector is stale only when its Operation is absent or the restored Catalog rejects its inputs; a version change alone is reported, not failed, and needs no re-approval.
```
OLD:
```
The generic runner in this repository rejects missing, duplicate, or stale vectors and contains no Module branches or domain setup code.
```
NEW:
```
The generic runner in this repository rejects an uncovered Operation Shape and duplicate or stale vectors, and contains no Module branches or domain setup code.
```
OLD:
```
asserting AD-5 document equality for discovery, execution, and error cases for every Operation after masking only generated message/correlation identifiers.
```
NEW:
```
asserting AD-5 document equality for discovery, execution, and error cases for every vector after masking only generated message/correlation identifiers.
```
OLD:
```
A separate live lane runs each vector once against one Aspire topology,
```
NEW:
```
A separate live lane runs each approved live vector once against one Aspire topology (at least one per Operation kind each Module declares; for a Module enrolled after 2026-11-10, the live Command vector creates an aggregate in a prerequisite, then submits a second, caller-keyed Command to it and reads the effect back with a postcondition Query; vectors and companion plans approved before 2026-11-10 keep running until their owning maintainer retires them; per-Operation handler semantics are tested in the owning Module's repository),
```
Rationale: P2, P3 and P5.

### C8. Architecture AD-21

OLD:
```
Missing, extra, mismatched, duplicate, or unapproved rows fail the Module's Gateway-ready and v1 release gates.
```
NEW:
```
Missing, mismatched, duplicate, or unapproved rows, and any cataloged contract that a `withdraw` or `defer` row names, fail the Module's Gateway-ready and release gates. The inventory gates retirement, not exposure: a cataloged Operation that no row mentions is reported, never failed, because decorating a type is the owning maintainer's consent to expose it to agents without human confirmation; UI-only and confirmation-required Operations are never decorated.
```
Rationale: P1 and P4.

### C9. Architecture "PRD Amendments"

Insert after the line that begins `- **FR-20 and §8.1 (AD-16/20):**`:
```
- **FR-1, FR-20, NFR-7 and SM-4 (AD-16/21, 2026-11-10):** vectors cover Operation Shapes instead of every Operation; the live lane needs at least one vector per declared Operation kind per Module; vector package versions are informational; a cataloged Operation with no inventory row is reported, not failed; decoration is the owning maintainer's consent to expose (sprint-change-proposal-2026-11-10-shape-coverage).
```

### C10. Epics FR map

File `epics.md`, FR-map line for FR20.

OLD:
```
Epic 6 — Enroll Folders vectors and prove Folders replacement parity and safety.
```
NEW:
```
Epic 6 — Enroll Folders vectors and prove Folders replacement parity and safety; Epic 5 (Story 5.12) — Replace per-Operation vectors with Operation Shape coverage for later enrollments.
```

### C11. New Story 5.12, inserted after Story 5.11

```
### Story 5.12: Gate Enrolled Modules by Operation Shape

As a McpCli maintainer,
I want enrollment gates that cover each operation shape once, report operations that no inventory row mentions, and treat a Contracts version change that alters no vector as informational,
So that a module can add or release decorated operations without a lockstep McpCli change while McpCli's generic translation stays proven.

**Requirements:** FR1, FR20, FR21; NFR7; SM-4; AD-16 and AD-21 as amended on 2026-11-10. **Dependencies:** none. Story 6.1 waits on this story. Approval of `sprint-change-proposal-2026-11-10-shape-coverage.md` is the MR10 product-owner decision that lets this story become `ready-for-dev`.

**Acceptance Criteria:**

**Given** the enrolled production Catalog,
**When** the shape-coverage gate runs,
**Then** it derives each Operation Shape from Catalog descriptors (kind, Identifier Kind, Wire Type convention, tenant source as exact `platformScope`, Module `fixedTenant` or public, aggregate-identifier source as property, constant or none, query projection selector as `projectionType`, `projectionActorType` or none, and required idempotency key) and fails, naming every shape that has no approved vector,
**And** with the existing Parties and Tenants vectors it reports the computed shapes (six expected from the 2026-11-10 survey) as covered and passes, and removing the only vector of one shape fails with that shape named.

**Given** an enrolled module and its release inventory,
**When** the inventory gate runs,
**Then** every `include` row still appears exactly once publicly and internally with its recorded contract type, every `withdraw` or `defer` row's name and type stays absent, and a cataloged operation that no row mentions produces a reported finding that does not fail,
**And** tests fail when either remaining guard is removed, asserting the complete finding text.

**Given** a vector whose recorded package version differs from the restored package,
**When** `check_enrolled.py`, `verify_artifact.py` and the live preflight run,
**Then** the difference is reported and the vector still runs, `approval.json` binds the inventory and vector hashes but no artifact hash, and re-approval is needed only when vector bytes or the inventory change,
**And** restored-package integrity checks (NuGet content hash against `project.assets.json`) and the AD-17 release package validation are unchanged.

**Given** the live lane,
**When** a module is enrolled after this story,
**Then** the gate requires at least one approved live vector, with a companion plan, for each Operation kind it declares, and the vector README's approval rules require its live Command vector to create an aggregate in a prerequisite, then submit a second Command to it with a caller-supplied idempotency key and read the effect back with a postcondition Query,
**And** the existing Parties and Tenants vectors, plans and inventories keep running unchanged; none is deleted. Adopting the keyed scenario for them is recorded as one deferred entry, to be picked up at their next vector amendment.

**Given** the `HexalithCommandAttribute` and `HexalithQueryAttribute` XML documentation and the README "Gateway boundary" section,
**When** a module author reads them,
**Then** both state that decorating a type is the owning maintainer's consent to expose it to agents and operators through the Gateway without human confirmation, and that UI-only and confirmation-required operations are never decorated.

**Given** the README, `tools/conformance-vectors/v1/README.md`, `tools/inventory-coverage/v1/README.md` and `AGENTS.md`,
**When** the change lands,
**Then** they describe shape coverage, reported uninventoried operations and informational vector versions, and `CLAUDE.md` and `.github/copilot-instructions.md` stay byte-identical to `AGENTS.md` with `scripts/check-agent-instructions-sync.sh` passing,
**And** the Release build, the Core and Manifest tests, the conformance-vector and live-topology Python suites, `check_enrolled.py`, the live preflight and CI's `topology-vector-discovery` job pass.
```

### C12. Story 6.1 changes

OLD:
```
I want McpCli to enroll the exact decorated Folders Contracts release named by the approved inventory, with one approved vector for each included operation,
```
NEW:
```
I want McpCli to enroll the exact decorated Folders Contracts release named by the approved inventory, with approved vectors covering every operation shape Folders uses,
```
OLD:
```
**Dependencies:** Stories 5.2 and 5.8;
```
NEW:
```
**Dependencies:** Stories 5.2, 5.8 and 5.12;
```
OLD:
```
the vectors with an `approval.json` binding the artifact, inventory and vector hashes, and the companion live plans change together under the README enrollment rules,
```
NEW:
```
the shape vectors with an `approval.json` binding the inventory and vector hashes, and their companion live plans change together under the README enrollment rules,
```
OLD:
```
and an approved `withdraw` or `defer` for every excluded row.
```
NEW:
```
and an approved `withdraw` or `defer` for every excluded row whose contract is absent from the Catalog; a cataloged Folders operation that no row mentions is reported, not failed (AD-21).
```
OLD:
```
**Given** every included operation,
**When** its vector is approved,
**Then** it has exactly one execution vector, and `check_enrolled.py` shows equal canonical documents and captured Gateway requests from both heads against the reset loopback Gateway,
```
NEW:
```
**Given** every operation shape in the enrolled Folders Catalog,
**When** the shape vectors are approved,
**Then** each shape has at least one execution vector, and `check_enrolled.py` shows equal canonical documents and captured Gateway requests from both heads against the reset loopback Gateway for every vector,
```
OLD:
```
the explicit `Hexalith.Folders.Commands.*` wire type for each Command,
```
NEW:
```
the explicit `Hexalith.Folders.Commands.*` wire type for each vectored Command (Folders' own tests at the enrolled revision cover every other Command's wire type),
```
OLD:
```
**When** the new vectors run,
**Then** the test AppHost composes the Folders domain service, and any provider double that G6-governed operations need,
```
NEW:
```
**When** the Folders live vectors run (at least one Command and one Query chosen by the owner, the Command vector following the AD-16 keyed second-Command scenario),
**Then** the test AppHost composes the Folders domain service, and a provider double only if a chosen live vector needs one,
```
Rationale: P2, P3 and P5. The 2026-11-10 Folders proposal's reasoning at `:73` ("every type Folders publishes must be an included row with a vector") is superseded; that applied record stays unchanged.

### C13. Story 6.2 changes

OLD:
```
**Given** the owner-named selected environment and the approved Folders vectors,
**When** the evidence runs,
**Then** every Folders `replace` row succeeds through the CLI head against that environment with its persisted semantic check, and both heads produce equal canonical documents and captured requests against the reset loopback Gateway,
```
NEW:
```
**Given** the owner-named selected environment, the approved Folders shape vectors and Folders' per-row checks,
**When** the evidence runs,
**Then** every Folders `replace` row succeeds through the CLI head against that environment with its persisted semantic check, run by McpCli or by a Folders upstream test that drives a McpCli head at the enrolled revision, and the shape vectors show both heads producing equal canonical documents and captured requests against the reset loopback Gateway,
```
Rationale: P4. Retirement keeps per-row evidence, and the module may supply it.

### C14. Bookkeeping

- **`epics.md` frontmatter:** append `- _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10-shape-coverage.md` to `changeProposals`. `approvedStories` and the 2026-11-08 `refinement` block stay as they are, following the 2026-11-10 precedent.
- **`sprint-status.yaml`:**
  - After the `5-11-…` row, add `5-12-gate-enrolled-modules-by-operation-shape: backlog # 2026-11-10 shape-coverage proposal; precedes Story 6.1.`
  - In the `6-1-…` comment, change `Waits on McpCli 5.2 and 5.8` to `Waits on McpCli 5.2, 5.8 and 5.12`.
  - Edit by hand; the generator drops comments.

## 5. Implementation handoff

**Scope: Moderate.** The PRD and architecture text change, but neither MVP scope nor goals do. The backlog gains one story, and two stories are reworded.

| Role | Responsibility |
| --- | --- |
| Product owner (single-maintainer model) | Approve this proposal; that approval also serves as the MR10 decision for Story 5.12. |
| Developer agent | Apply C1–C14 verbatim. Then build Story 5.12 through `bmad-build`, with a spec and review. |
| Folders owner (handoff) | Folders Stories 5.12–5.14 no longer need one McpCli vector per operation. Folders owns per-operation handler, routing-string and wire-type tests, and must not decorate UI-only or confirmation-required operations. The McpCli test AppHost needs the G6 provider double only if a chosen live vector requires it. |
| AI.Tools (optional, upstream) | Mirror the consent sentence in the "Hexalith MCP and CLI ownership" rule. Not required by this proposal. |

**Success criteria:**
1. Story 5.12 is done, and CI is green with the existing 21 vectors passing the shape gate.
2. A Contracts version bump that changes no operation needs no vector, plan or approval change.
3. A newly decorated operation with an existing shape needs no McpCli change beyond the package pin.
4. Story 6.1 enrolls Folders with shape vectors and per-kind live vectors.

**Ledger note.** Entries that assume "the usual McpCli artifact/vector rebind" (for example `deferred-work.md:781`) keep their substance, but a version-only rebind becomes a reported difference. The Story 5.12 review records which entries this affects in its `[Review]` rows, following the ledger's grep-first rule.

## Checklist record

| Item | Status | Note |
| --- | --- | --- |
| 1.1 Trigger | [x] | Product-owner ROI question, 2026-11-10; no failing story. |
| 1.2 Problem | [x] | Failed approach: per-operation lockstep gate. |
| 1.3 Evidence | [x] | §1, including the shape survey and the Epic 4 cost data. |
| 2.1–2.5 Epics | [x] | §2.1; no resequencing beyond 5.12 before 6.1. |
| 3.1 PRD | [x] | C1–C6; MVP unaffected. |
| 3.2 Architecture | [x] | C7–C9. |
| 3.3 UX | [N/A] | No user-facing behavior change. |
| 3.4 Other artifacts | [x] | §2.3, delivered by Story 5.12. |
| 4.1–4.4 Path | [x] | Option 1 selected (§3). |
| 5.1–5.5 Proposal | [x] | This document. |
| 6.1–6.2 Review | [x] | Batch mode; recommended options pre-approved ("apply recommended"). |
| 6.3 Approval | [!] | Pending explicit product-owner "yes". |
| 6.4 Sprint status | [!] | C14, applied on approval. |
| 6.5 Handoff | [x] | §5. |
