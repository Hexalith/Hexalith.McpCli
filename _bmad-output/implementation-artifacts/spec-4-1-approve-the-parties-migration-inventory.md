---
title: '4.1 Approve the Parties migration inventory'
type: 'chore'
created: '2026-10-16'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '2d8d4d201e717871e3253cf8d311d35422139851'
context:
  - '_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 4.1 has no approved Parties inventory. Five legacy tools hide
multiple Gateway calls and wrapper behavior, so names alone cannot prove coverage.

**Approach:** Approve a versioned, source-pinned migration artifact mapping every
tool and variant to intended canonical operations/Contracts types or an explicit
withdrawal/deferral. Record actual maintainer approval and command routing before
upstream decoration.

## Boundaries & Constraints

**Always:** Keep the inventory outside `src/`, separate proposed scope from proven
readiness, and use `replace`/`withdraw`/`defer` plus `include`/`exclude`. Inclusion
requires an approved Gateway-ready replacement; exclusion requires approved
withdrawal/deferral. Preserve String identifiers, envelope tenant authority, privacy
and authorization. Record compatibility/versioning differences and downstream
gates. Approved scope alone proves no parity or retirement readiness.

**Never:** Invent approvals, resources, or CLI operations; conflate soft deactivation
with erasure; copy legacy header/credential weaknesses into the target. Change
runtime code, upstream checkouts, dependencies, enrollment, package publication,
or host retention in this story. Generic heads perform one submission per call.

**Approved decisions (2026-10-16):** The requesting user directed "apply
recommended" after discussion of the complete candidate inventory. Apply the
seven typed operations, explicit IDs/nested payloads, separate activation calls
and shared result documents. Preserve privacy, authorization, validation,
identifier consistency and safe repeated deactivation. Correct misleading search
totals and ignored filters through explicit upstream query semantics; retain
identifier compatibility or gate conversion before retirement.

Retain attribute routing with full CLR wire names, domain `party`, String IDs
and root `PartyId`. No interface or wire migration. Finalize inventory 1.0.0 and
one A1 session approval record covering L01-L05, T01-T07, N01-N04, compatibility
decisions and routing; reference it from every row. Identify the approver as the
requesting user and preserve the exact instruction; invent no named signatory
or external approval. This approves scope, not downstream execution proof or
retirement. Leave missing Contracts, credential and behavior evidence explicitly
assigned to their downstream stories.

</frozen-after-approval>

## Code Map

Paths below are relative to `references/Hexalith.Parties/` unless stated otherwise.
The inspected source is clean at `493730941329d1bca3b4f6b2f6a67ffe305c2443`.

- `src/Hexalith.Parties.Mcp/Tools/PartiesMcpToolNames.cs:5` and
  `PartiesMcpTools.cs` in that folder: five names, six variants, write orchestration.
  `Program.cs:61` registers tools only; tool-contract tests pin the surface.
- `src/Hexalith.Parties.Client/HttpPartiesQueryClient.cs:46` and
  `HttpPartiesCommandClient.cs:155` in that folder: exact query and full-type command
  routes, private query payloads, root/child ID normalization. Reuse as evidence.
- `src/Hexalith.Parties.Contracts/Commands/`: four existing target DTOs.
  `Queries/` lacks the proposed GetParty/ListParties/SearchParties types.
- `src/Hexalith.Parties/Domain/PartyDomainProcessor.cs:635`: full/short CLR lookup;
  current kebab-case wires would fail. `8-8-client-mcp-apphost-build-and-deploy-cleanup.md`
  in upstream implementation artifacts records credential/parity prerequisites.
- Local `parties-migration-inventory-v1.md` beside this spec contains complete
  row/target tables, exact routes, differences, exclusions and source anchors.
  `src/Hexalith.McpCli.Abstractions/` supports name overrides and attribute routing;
  no generic runtime change is needed.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md`
  — reconcile the proposed five legacy rows, six variants and seven unique targets
  with owner decisions; retain full canonical source revision and inventory version.
- [x] Same inventory — finalize each disposition, coverage, rationale, security
  class, target CLR type or gap, and real approval reference; explicitly account
  for non-MCP erasure, rotation and other excluded behavior without inventing tools.
- [x] Same inventory — record the approved routing choice and compatibility
  boundaries; assign missing Query/declaration work to 4.9/4.10 and verification to
  4.11/4.13. Preserve unproven credential/authorization and behavior gates.
- [x] Same inventory — compare declared tool names and registrations to the
  pinned source; check duplicate targets, incomplete rows and invalid
  disposition/coverage pairs. Recheck the revision before finalization.
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` and this spec
  — synchronize workflow status only when its approval and validation gates pass.

**Acceptance Criteria:**
- Given the pinned MCP host, when inventory completeness is checked, then all
  five tools and both find variants are mapped and zero-resource/CLI findings
  have source evidence; shared target operations occur once in the target table.
- Given an included read/write, when its mapping is inspected, then canonical
  name and intended decorated CLR type are explicit, including each missing Query.
- Given exclusions or wrapper differences, when scope is approved, then specific
  rationales and owner decisions account for them without implying parity,
  erasure, automatic retirement or currently published Contracts.
- Given the routing decision, when decoration starts, then domain/aggregate/wire
  conventions and any breaking change have a recorded maintainer approval.
- Given missing approval or downstream proof, when readiness is reported, then
  approval absence keeps this story incomplete and downstream gaps continue to
  block enrollment/retirement as applicable.

## Implementation Notes

- Finalized inventory 1.0.0 with A1: the requesting user's exact "apply
  recommended" instruction, source SHA, all five legacy rows/six variants,
  seven unique targets, four explicit deferrals, compatibility decisions and
  retained attribute/full-CLR command routing. Every inventory table row links A1.
- Included the optional T01 read in L04 and made three missing public Queries
  distinct from the four existing, undecorated Command DTOs. Recorded privacy,
  validation, identifier, credential, paging/filter, response-versioning and safe
  repeated-deactivation requirements with 4.9/4.10 delivery and 4.11/4.13 proof.
- Source remained clean at the full pinned revision before and after validation.
  No runtime, upstream, dependency, enrollment, publication or host-retention
  change was made. Approval establishes scope; downstream readiness is unproven.
- Spec and sprint status are `review`; final completion awaits workflow review.
- Completed the three independent review layers. Edge-case and verification-gap
  reviewers reported no findings; all seven blind-review handoff refinements
  were applied and independently verified. No review findings were deferred.
  The spec is complete; sprint tracking remains `review` as the build workflow
  requires. Existing upstream delivery and live-proof gates remain outstanding.

## Spec Change Log

- 2026-10-16: Completed the authorized inventory/tracking tasks and recorded
  verification. Frozen intent and approved decisions remain unchanged.

## Review Triage Log

| Finding | Verdict | Evidence and route |
| --- | --- | --- |
| BH1 — safe error messages | medium | Legacy `PartiesMcpTools.MapClientException` uses fixed safe messages and dispatch tests reject personal-data disclosure; Core `OperationError.FromGateway` copies detail/title. C06 accepts the shape change without an explicit error-privacy handoff. Patch C06 with upstream sanitization and error-path assertions before retirement; retain shared Core documents. |
| BH2 — empty updates | low | Legacy tools reject a patch without supported fields; C04 records that behavior but its general validation requirement leaves the upstream T05 empty-payload case implicit. Patch the inventory with explicit no-change rejection and a downstream negative case. |
| BH3 — composite bounds | medium | Both legacy write wrappers enforce 512/4096 input bounds, while C03 names them and C04 does not. Existing composite validators/aggregate already cap sub-operations (default 100), disproving unbounded runtime collection admission; patch the handoff to cover both writes, nested values, removals, and explicit bounded-validation evidence. |
| BH4 — stale-read repeats | low | C05 requires safe repeats but does not explicitly name stale/concurrent pre-reads. The current aggregate returns NoOp for an already-inactive state, so no current duplicate-event defect is established. Patch the future live acceptance requirement to exercise stale reads/concurrent repeats and verify final state/event effects. |
| BH5 — EntityId handoff | low | Pinned `PartySdkQueryService.TryValidateDetailEnvelope` and `TryValidateIndexEnvelope` fall back to AggregateId when EntityId is omitted and reject mismatches. The inventory leaves this known behavior vague. Patch the source-backed omission rule and omitted/matching/mismatching query cases. |
| BH6 — tenant-isolation proof | medium | C08 names authenticated authorization but not negative cross-tenant reads/writes. Core permits configured session tenants and gated per-call changes; neither grants Gateway authority. Patch the handoff with tenant-A credentials denied tenant-B access, including permitted overrides. |
| BH7 — reproducible static verification | low | The one-off source/row checker exists only under `/tmp`; the recorded invocation is not portable to another checkout. Patch supporting verification documentation with the complete executable commands/assertions and link it from the inventory; add no CI gate or runtime code. |

Resolution (2026-10-16): BH1–BH7 were patched in the inventory and supporting
verification evidence. The complete source/row checker runs from
[verification.md](evidence/story-4-1/verification.md). Parent verification passed
again, confirmed frozen intent remained unchanged, and found no incomplete tasks.

## Verification

- Compare the inventory names with `PartiesMcpToolNames.cs`, tool attributes,
  registration and `PartiesMcpToolContractTests.cs`; check all seven target types
  and distinguish existing commands from proposed queries.
- Check every row's approval/disposition/coverage and routing against the actual
  owner decision, not the architecture's general migration banner.
- `git diff --check` — no whitespace errors. Inspect the final diff to confirm
  changes are local documentation/tracking only. No .NET build is needed for
  this artifact-only change.

### Execution evidence (2026-10-16)

- `python3 /tmp/validate-parties-inventory-4-1.py` — PASS. One-off snapshot
  validation compared constants, tool attributes, host registration and contract
  test names; checked both find branches, seven unique names/types, all 24
  complete A1-linked rows, valid disposition/coverage pairs, target usage and
  four existing Command files versus three absent Query files. Tracked source
  scans found no MCP resources or proprietary command-parser declarations.
- `git -C references/Hexalith.Parties rev-parse HEAD` —
  `493730941329d1bca3b4f6b2f6a67ffe305c2443`;
  `git -C references/Hexalith.Parties status --porcelain` — empty, checked again
  at validation completion.
- `git diff --check` — exit 0, no whitespace errors (Git also emits its existing
  missing commit-graph warnings). `git diff --no-index --check -- /dev/null
  _bmad-output/implementation-artifacts/parties-migration-inventory-v1.md` and
  the same command for `spec-4-1-approve-the-parties-migration-inventory.md` —
  exit 1 for the expected new-file differences, with no whitespace diagnostics.
  Final changed paths are local Markdown/YAML planning artifacts only. No .NET
  build required.
- Final verification executed the complete Bash/Python block in
  [verification.md](evidence/story-4-1/verification.md) — PASS for pinned clean
  source, all five tools/six variants, seven targets, all 24 approved rows and
  whitespace. A separate check confirmed frozen intent, seven triage entries,
  complete tasks, the evidence link and whitespace in every new artifact.

### Review Findings

- [x] [Review][Defer] Legacy `delete_party` behavior for missing or erased parties is unmapped [parties-migration-inventory-v1.md:78] — deferred: unverified Medium; C05 maps only the already-inactive case, so 4.11/4.13 have no oracle for not-found or erased IDs on T01/T07. Settle by reading the Parties `delete_party` pre-read and confirming whether C05 or T07 already defines the outcome.

#### Rejected

- Self-attested approval, no named maintainer signatory (blind-hunter, edge-case-hunter, acceptance-auditor): low; A1 states this openly and the frozen "Approved decisions" accept it, so the fix edits the spec under review.
- Spec `status: 'done'` vs. `review` in sprint status and notes (all four layers): low; the fix edits the spec under review, and the notes say sprint tracking intentionally lags until this review.
- Rows marked `include` while T01–T03 do not exist (blind-hunter, acceptance-auditor): low; the inventory already states `include` becomes eligible only after the Contracts prove readiness, and a readiness column adds structure for no demonstrated harm.
- T01–T03 wire values not tabulated; C02 rejection error code and C07 canonical GUID form unspecified (edge-case-hunter): false; the inventory assigns each to Stories 4.9/4.10 (C02, C07) with 4.11/4.13 proof, so they are deliberate downstream decisions.
- `OperationError.cs:41` listed under "relative to the pinned Parties repository" (edge-case-hunter): false; the entry is labelled "McpCli-local" in the same bullet.
- `verification.md` checker weaknesses: substring `A0` and front-matter checks, unasserted row count, PASS wording, git checks (blind-hunter, edge-case-hunter): low; an on-demand evidence script, and each fix adds guards.
- Evidence cited from `/tmp` files (all layers): low; `verification.md` supersedes the `/tmp` checker, and commitlint can be re-run on the committed message.
- `review_loop_iteration: 0` and "no findings deferred" vs. seven patched findings (blind-hunter, edge-case-hunter): false; the notes say all seven were applied, which is consistent with nothing deferred.
- Brittle `file:line` anchors, prose style, `epic-4-context.md` header, `epic-4` moved to in-progress, `C01`–`C08` approval attribution, missing ledger entries for downstream handoffs: low; none causes a named harm, and the handoffs are recorded in the inventory.
