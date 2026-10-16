---
title: '4.3 Approve Projects and FrontComposer migration inventories'
type: 'chore'
created: '2026-10-16'
status: 'done'
baseline_commit: '228fdaa42e3b50d9c93fb07fe73bd329dc4f0b3c'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The September Projects draft is unapproved and stale; FrontComposer
has no companion inventory. Neither supports an agreed shared retirement gate.

**Approach:** Finalize two linked inventories outside `src/`, with source pins,
version, disposition, coverage, rationale, security class, contract/transport gaps
and actual approval references per row. Separate host and business behavior.

## Boundaries & Constraints

**Always:** Pin clean Projects revision
`3d256e632a7645bc2261e668ac7c74be81155f58` and FrontComposer revision
`81a440a8890a17edb39924bd0cf676eb6f6b5c25`. Account for Projects' 11 resources,
five tools, 18 CLI spellings and their variants; FrontComposer's lifecycle tool,
13 documentation resources, manifest-defined families and two developer CLI
leaves. Count shared Projects surfaces once.

Preserve task/actor/tenant authority, direct Gateway guard ownership, strict wire
schemas, replay, resolution/refresh, redaction, paging/freshness and preview
differences. Name unsupported stream/file/search variants. Included reads need
exact decorated Queries and routes. Projects remains post-v1 until slim published
Contracts, restored closure, Catalog and authorization/behavior gates pass.
Keep host and plug-in nondeletable until both inventories' retirement gates pass.

Record approval authority and limits honestly: session scope approval cannot
assert external owning-maintainer sign-off.

**Never:** Change runtime, upstream, enrollment, dependencies, publication or
retention. Add module-specific adapters, typed tools, dynamic plug-ins, retries,
resources/prompts, stream reading or v1 HTTP identity. Weaken canonical ULIDs,
trust payload identity, infer committed effects, execute migrations or authorize
withdrawal/deletion from inventory preparation.

**Approved decision (2026-10-16):** The requesting user answered "approve" to
the presented recommendation: all current rows in both inventories remain
`defer / exclude`, retaining legacy surfaces. Record this as the requesting
user's session scope approval for both source-pinned inventories. No external
Projects or FrontComposer owning-maintainer sign-off is asserted. Approval
authorizes finalizing this spec and both inventories under that scope; Gateway
readiness, exposure, publication, withdrawal and retirement remain unapproved.

</frozen-after-approval>

## Code Map

- The two candidate inventories contain per-row upstream paths/lines; reuse
  those maps without repeating investigation. All upstream paths resolve inside
  their pinned root-declared reference checkout.
- Projects `src/Hexalith.Projects.Mcp/ProjectsMcpDescriptors.cs:23` and CLI
  `ProjectsCliParser.cs:28` declare sets. Server `EventStoreProjectCommandSubmitter.cs:299`
  maps taskId; `Authorization/ProjectAuthorizationGate.cs:399` owns REST tenant
  guards; `ProjectsDomainProcessor.cs:43` rejects unknown payload fields.
- FrontComposer MCP `FrontComposerMcpServerOptionsConfigurator.cs:27` registers
  resources; `HttpFrontComposerMcpAgentContextAccessor.cs:79` owns identity.
  Ordinary corpus metadata supplies 12 documents plus one synthetic manifest.
  Its CLI `CliApplication.cs:19` owns separate inspect/migrate compiler tooling.
- Reuse Story 4.2's approval/evidence distinction. Leave runtime, README and
  dependency policy intact; no user-visible CLI/MCP behavior changes.

## Tasks & Acceptance

**Execution:**

All paths below are under `_bmad-output/implementation-artifacts/`.

- [x] `projects-migration-inventory-v1.md` and
  `frontcomposer-migration-inventory-v1.md` — finalize candidates with agreed
  scope, actual approval basis, prerequisites and shared retirement gate.
- [x] `evidence/story-4-3/verification.md` — preserve repeatable source-set,
  variant, row, reference and approval checks; distinguish static from live proof.
- [x] `projects-migration-inventory-draft.md` — add a successor notice,
  preserving the historical body.
- [x] This spec and `sprint-status.yaml` — synchronize after applicable
  approval, implementation, review and verification gates pass.

**Acceptance Criteria:**

- Given pinned sources, when completeness is checked, then every concrete
  surface/spelling has one row, dynamic families are explicit, and none is doubled.
- Given a row, when assessed, then disposition, coverage, rationale, security,
  replacement/gap and actual approval are explicit; missing approval blocks completion.
- Given context/variants, when parity is proposed, then payload/actorProperty/
  extension handoffs and authenticated tenant guard ownership remain explicit.
- Given retirement evaluation, when dependencies or coverage/security/behavior/
  release evidence is missing, then host and plug-in remain together, including
  other host consumers' unresolved capabilities.

## Implementation Notes

- 2026-10-16: The requesting user approved the presented spec and recommended
  deferred scope with the exact instruction "approve". The approval is a session
  scope decision for both inventories, with external owner sign-off unasserted.
  The approved frozen decision above resolves the planning question; continue
  implementation and required review without seeking the same approval again.

- 2026-10-16 implementation: finalized both inventories as version 1.0.0 with
  A1 references on all 82 rows. Metadata identifies requesting-user session
  authority and explicitly leaves external owning-maintainer approval
  unasserted. All concrete surfaces, manifest-defined families and compatibility
  variants remain `defer / exclude`; ten prerequisite rows remain unresolved.
  The host and Projects plug-in remain nondeletable together, including other
  host consumers' unresolved capabilities. The September draft body is preserved
  verbatim beneath a linked successor notice. Runtime, upstream, dependency,
  enrollment, publication and retention are unchanged. Required workflow review
  and final spec/sprint synchronization remain parent-session gates; both
  tracking states remain `in-progress` at this implementation checkpoint.

## Spec Change Log

## Review Triage Log

2026-10-16: All three independent layers completed before triage. Edge-case
review returned no findings. Verification-gap review found no gap in this
story's artifact checks and reported one pre-existing dependency-policy issue.
Each blind-hunter finding was checked against the pinned source before any
grouping. The nine survivors are independent direct documentation corrections;
none changes a disposition, operation set, approval authority or runtime.

| ID | Verdict | Route | Verified finding and evidence |
| --- | --- | --- | --- |
| BH01 | medium | patch | The resource inventory default describes the nullable Projects helper, not the registered host path. FrontComposer `FrontComposerMcpProjectionReader.cs:76` supplies its configured default (50 by default); Projects dispatcher `ProjectsMcpResourceReader.cs:48` forwards it, whereas audit dispatch at `:52` fixes 25. Distinguish effective host defaults from helper limits to avoid incorrect paging parity. |
| BH02 | medium | patch | H01's “Identity-bound” claim exceeds the source. `FrontComposerMcpLifecycleStore.cs:17` indexes handles, and its entry constructor `:307` stores descriptor/correlation/message without tenant/user. Tracker `:54` only rechecks current tool admission. State the ownership limitation and require explicit caller/tenant-binding evidence. |
| BH03 | medium | patch | Projects also conflates task with MCP message identity: `ProjectsMcpCommandService.cs:38` assigns accepted TaskId to MessageId and lifecycle callbacks. V08 currently covers caller key as Gateway MessageId only. Record both independent mappings and lifecycle/audit/replay migration implications. |
| BH04 | medium | patch | A successful API key overrides HTTP claims and calls `Create(..., claimsSource: null)` at `HttpFrontComposerMcpAgentContextAccessor.cs:96`; `:184` preserves original policy claims only on the claims path. V03 must identify this difference so future authority parity does not assume roles survive key authentication. |
| BH05 | medium | patch | R03 overstates diagnostic fields. `ProjectsMcpResourceReader.cs:147` emits identity/name/lifecycle, reference/audit counts and freshness/watermark, with a descriptive explanation string. Actual task/correlation/audit entries and reasons are on the separate audit resource (`:188`), not this summary. Correct the current output description. |
| BH06 | medium | patch | The strict-wire gap is real but lacks operation-level payload evidence. `EventStoreProjectCommandSubmitter.cs:116` through `:257` adds v1 schema, archive/restore intents, set/link/unlink operations and unlink intent absent from the named source DTOs. Record these fields and owning handoff without treating the source records as ready. |
| BH07 | medium | patch | V07 omits material local migration outcomes. `MigrationApplier.cs:12` rechecks canonical targets, `:28` source hash, then writes files sequentially (`:33`); failures/cancellation preserve earlier writes and `:51` reports applied=false. Describe drift protection and partial-write semantics before any future compiler-tool replacement. |
| BH08 | medium | patch | FrontComposer parser semantics are missing. `CommandOptions.cs:32` accepts equals syntax, `:91` rejects repeats, and `:99` checks presence; `MigrationCommand.cs:13` therefore treats --apply=false as apply. Document this existing behavior and its compatibility decision without executing or changing migration tooling. |
| BH09 | medium | patch | Erasure and key rotation need explicit unsupported accounting. The inspected Projects descriptor/parser sets contain neither operation; FrontComposer's fixed tool is lifecycle plus dynamic manifest families, and its CLI dispatch is inspect/migrate. Add explicit deferred exclusions for these unsupported variants; host API-key configuration is not an agent-facing rotation operation. |
| VG01 | medium | defer | The earlier committed Builds bump predates this approved implementation: commit `1a6d725fb89545bce56b7be1e16683461cf9cfe7` moved the gitlink. Current Builds props `:242`/`:244` pin Hosting/Http 10.0.13 while local dependency policy `:51`/`:53` pins 10.0.12; existing assets still contain 10.0.12. `DependencyPolicyTests.cs:137` rejects a restored mismatch. Track fresh-restore/policy reconciliation separately; no dependency edits belong to this artifact finalization. |

Completion: BH01–BH09 were corrected and the parent reran the complete revised
evidence block successfully (exit 0). Both inventories identify these additions
as post-approval prerequisite clarifications; all 82 rows retain A1's approved
deferred scope, authority and source pins. VG01 is tracked at
`deferred-work.md:477` after checking for an existing matching entry. The frozen
approval block's SHA-256 is unchanged. All build tasks and the accepted session
scope are complete; the sprint entry is `review` for the separate story-review
transition required by this workflow. External owner and execution/retirement
gates remain open.

## Verification

- Execute `evidence/story-4-3/verification.md`'s Bash block: exact source sets,
  pins, valid references and honest approval state. Pending is not final readiness.
- Run `git diff --check`; inspect local Markdown/YAML changes and upstream
  HEAD/status. No .NET build applies; static checks prove no Gateway behavior.

- 2026-10-16 implementation validation: executed the evidence document's entire
  Bash block through Python `subprocess.run(['bash','-e'], input=block,
  text=True)`; exit 0. Exact pins and clean checkouts, 34 Projects surfaces,
  two host families, lifecycle tool, 13 documents, two compiler leaves,
  20 variants, 82 A1 row references, local references/source anchors and the
  preserved historical body passed. In-memory duplicate/missing rows, swapped
  CLI associations, pending approval and invented external approval were
  rejected. `git diff --check` passed. Existing commit-graph warnings did not
  change the exit code. These checks supply static scope evidence only.

- 2026-10-16 parent completion validation: the full revised evidence block
  passed after all nine review corrections, including effective host/helper
  take values and the seven emitted payload shapes matched against strict
  processor DTOs. Final spec/sprint states are `done` / `review`. The approval
  block hash remains `627de046e93b439723d754f102bb1beba61773c0584b472f05f35acc836c8eca`.
  `git diff --check` passed; no .NET build applies to this artifact-only change.
  The exact local commit message passed the repository's pinned commitlint CLI
  with zero problems and zero warnings after `npm ci`; the full evidence is in
  `evidence/story-4-3/verification.md`.
