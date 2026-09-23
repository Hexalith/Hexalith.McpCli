---
title: Architecture validation — good-spine rubric
date: '2026-09-23'
intent: validate
reviewer: rubric-walker
verdict: pass-with-follow-up
---

# Rubric validation

The current spine is a coherent implementation contract and agrees with the current PRD and story corrections. No Critical or High finding was identified by this lens. One Medium integration-contract gap should be settled before independently authored Module conformance vectors are accepted. Existing upstream prerequisites still block the affected implementation and release gates; this assessment does not declare v1 ready to ship.

**New finding counts:** 0 Critical, 0 High, 1 Medium, 0 Low. No spine, memlog, source requirement, or sprint file was changed.

## Evidence scope

Paths below are relative to `/home/administrator/projects/hexalith/mcpcli`; line references address the current files, not their older review snapshots.

| Alias | Exact file |
| --- | --- |
| Spine | `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md` |
| Memlog | `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/.memlog.md` |
| PRD | `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md` |
| Addendum | `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/addendum.md` |
| Epics | `_bmad-output/planning-artifacts/epics.md` |
| Proposal | `_bmad-output/planning-artifacts/sprint-change-proposal-2026-09-23.md` |
| Status | `_bmad-output/implementation-artifacts/sprint-status.yaml` |

The root `AGENTS.md` and declared root-submodule copy of `references/Hexalith.AI.Tools/hexalith-llm-instructions.md` were read. No agent skill under the repository-root `references/` directory was loaded. Root searches found no product solution, projects, build props, `.editorconfig`, or `.gitattributes`; Story 1.1 still owns that greenfield seed. The parent reports the deterministic spine lint passed with zero findings; this lens did not repeat it. Technology/API currency is assigned to the parallel technology reviewer; historical verification is evidence of prior work, not a fresh assertion that every package is current today.

## Medium finding

### RUB-20260923-01 — Freeze the shared vector contract before Module teams author it independently

**Criterion:** fixes real divergence points for the level below; enforceable integration rules. **Disposition:** discuss the contract owner and freeze gate, then record it as a bounded AD-16 prerequisite. **Severity:** Medium.

**Evidence:** AD-16 requires versioned, Module-owned vectors with Payload and Envelope inputs, generic prerequisite calls, and semantic assertions, and makes the McpCli runner reject missing, duplicate, or stale vectors (Spine:150). The PRD requires the same independently produced artifacts (PRD:398, :404, :465). Stories 4.8, 4.9, and 4.10 require upstream maintainers to produce approved vectors (Epics:1218–1221, :1253–1256, :1273–1276); Story 4.11 consumes them (Epics:1303–1306), and Story 4.13 runs their semantic assertions (Epics:1363–1371). None of those contracts names a shared vector schema/format, who owns its compatibility, or a gate requiring the generic contract to exist before the upstream vectors. The spine's Deferred and Open Questions lists do not cover that seam (Spine:311–329).

**Concrete incompatible outcomes:** the Tenants maintainer can supply JSON with declarative query assertions while the Parties maintainer supplies test-language callbacks or differently named prerequisite fields. Both artifacts can be versioned, approved, and contain every category AD-16 names; one generic runner cannot consume both without adapters or module-specific setup. Likewise, “stale” can mean absent canonical Operation Name to one author and mismatch to a pinned Contracts release to another. Merely matching the Catalog's names does not define that compatibility decision.

**Proposed disposition:** require one McpCli-owned, versioned vector contract and a generic schema/compatibility validator before Stories 4.8–4.10 accept vectors. Bind the representation of prerequisites and semantic checks, plus the identity used to match a vector set to the selected Contracts release. Keep concrete field layouts in a small test-contract artifact owned by the first runner/schema story; the spine need only name that authority, require all Modules to use it, and state the pre-authoring gate. This does not require embedding a full schema in the spine, adding module code, or reopening the approved split between loopback parity and one live semantic execution.

**Scope of impact:** integration authoring and later release evidence. It does not prevent the Decoration Package, Catalog, settings, executor, or heads from being implemented under the existing AD set. This is a new contract seam, distinct from the already tracked absence of decorated packages, the Parties Aspire helper, or the Builds source-build path.

## Complete rubric walk

| Good-spine criterion | Judgment | Current evidence |
| --- | --- | --- |
| Fixes the real divergence points at feature altitude | Pass with one Medium follow-up | The named hexagonal paradigm and project boundaries allocate shared behavior to Core and carriage to heads (Spine:29–38, :42–66). AD-3 through AD-14 bind Catalog, schemas, public documents, Envelope resolution, settings, and profiles. The Module-vector producer/consumer seam is RUB-20260923-01. |
| Every AD Rule is enforceable and prevents its stated divergence | Pass with that follow-up | AD-1/2/10/11 have dependency and DI boundaries; AD-3/4 have immutable Catalog and manifest equivalence checks; AD-5/12 explicitly bind the exhaustive Addendum §G schemas; AD-6/7/8/9/19/20 define serialization, validation, ID resolution, and request behavior; AD-13/14 define precedence and transactional profile updates; AD-15/17/18 define restored-assets, packaging, and release checks; AD-21 separates inventory coverage from execution vectors. AD-16's cross-repository artifact compatibility needs the gate above. |
| Deferred choices cannot cause v1 units to diverge | Pass | HTTP has a host-owned handler seam and explicit unsupported behavior (Spine:114, :313); query extras are outside the v1 call model (:316); the shipped tool is explicitly untrimmed (:156, :319); config argument/mutation semantics are fixed by AD-14, leaving only presentation deferred (:138, :323). No still-required v1 runtime behavior is delegated to an unbounded future copy of a sibling CLI. |
| Named technology is verified-current and fit | Await parallel technology verdict; no independent currency claim | Exact pins are supplied (Spine:203–219), and Memlog:100, :115, :119, :131 record prior verification and corrections. The absent Parties helper is now expressly a prerequisite, not a fabricated released package (Spine:219, :326). This rubric review does not substitute the previous day's review for today's technology check. |
| Ratifies rather than contradicts existing implementation | Pass at this lens's scope | The owning repository is still greenfield: product stories are backlog (Status:37–86), and root solution/build files belong to Story 1.1. The spine uses sibling patterns as seed while explicitly identifying new helper/build work (Spine:144–156, :326–329), rather than claiming those prerequisites already exist. Detailed gateway/SDK fit belongs to the technology lens. |
| Covers binding source capabilities | Pass | FR-1–22 have explicit ownership in the capability map (Spine:289–309); the public result/error contract is imported exactly through AD-5, and Addendum §E/§G owns its detail (PRD:13; Spine:84). NFR-3 is realized by the determinism convention even though it is not a separate map row (Spine:195; PRD:427). NFR-1/2, channels/secrets, portability, testability, and description quality are assigned. FR-22 is an upstream completion commitment, correctly represented as such (:302; PRD:419–421; Epics:1398 onward). |
| Does not weaken inherited parent-spine constraints | Not applicable | No inherited parent spine or parent AD namespace is declared. The PRD and normative addendum are binding source inputs; their current contracts are aligned. Stable AD-1–AD-21 IDs and final adopted decisions are preserved (Memlog:127–131). |
| Every owned dimension is decided, deferred, or open | Pass | Boundaries, dependency direction, mutable-state ownership, validation and security, profiles, local deployment, CI, release, transport operations/channels, and future HTTP ownership all have explicit homes. Runtime/environment tables and diagrams cover the operational envelope (Spine:251–286); absence of a hosted-infrastructure plan is appropriate because v1 runs locally with no hosted infrastructure (PRD:106). Upstream helper, source build, catalog, and package-pin gaps are named, with revisit conditions (Spine:325–329). |

## Current PRD and 2026-09-23 story alignment

The sprint proposal states that it changes acceptance criteria without changing scope or the architecture (Proposal:17–23). That is consistent with the current sources:

| Item | Assessment and evidence |
| --- | --- |
| Structural seed | Story 1.1 now assigns root build, central packages, version pin, tests build props, release manifest, semantic-release, commitlint, and workflows (Epics:227–244); this implements the existing Structural Seed and AD-17 (Spine:156, :221–249). Status:91–98 keeps implementation and the upstream package catalog additions open. It is not a new missing architecture dimension. |
| Early query spike | Story 2.5 now uses the existing EventStore AppHost before the future McpCli test AppHost, calls the pinned client directly, records setup/routing evidence, and treats `index` as a tested candidate for the maintainer's later decision (Epics:615–623). This implements PRD:450 without silently declaring the final Contracts constant. Proposal:20, :27, :34 and Status:99–102 preserve that ownership. |
| Destructive write-tool annotation | AD-12 already requires `Destructive = true` (Spine:126); Story 3.1 now requires `destructiveHint: true` with the other write hints (Epics:889–892). Proposal:35 describes the correction; Status:111–114 correctly leaves implementation open. |
| Bootstrap order | The Abstractions-only bootstrap exception is already fixed in AD-17 (Spine:156) and Story 4.6 (Epics:1138–1156). Status:103–106 explicitly schedules it after Epic 1 so upstream decoration can proceed; its nominal Epic 4 position is not an unrecognized dependency cycle. |
| Live gates and external owners | Story 4.12 owns the published Parties helper (Epics:1333–1351); Story 4.14 owns the Builds source-build seam and blocking inputs (Epics:1383–1396). These implement already open architecture prerequisites (Spine:326–327), and Status:107–110 identifies the external owners/approval evidence. |

## Previously fixed findings — do not reopen

The older `VALIDATION-REPORT-2026-09-22.md` describes a former draft. Memlog:127–131 records the user decisions, reconciliation, and final gate closure. Current text supports those closures:

| Old issue | Current closure |
| --- | --- |
| Generated idempotency keys and incompatible public results | Only caller-supplied keys are accepted/echoed, one message ID is generated, and omitted correlation uses that ID (Spine:84, :108, :196). AD-5 binds the exhaustive Addendum §G, including required null Query documents and exact error variants (:84). |
| Offline discovery fails or advertises false execution readiness | AD-3/13 define one availability value with read-only precedence and permit startup/discovery without URL (Spine:72, :132). |
| Impossible live cross-head equality | Approved reset-loopback parity is separate from once-per-vector live semantics; method, path, routing, Envelope, Payload, and paging are compared against each other and the vector (Spine:150; PRD:398, :509). |
| Unknown or empty Module arguments lack a stable document contract | Non-empty lookup misses use `unknown_module`; absent/empty arguments fail Head binding with the specified CLI/MCP distinction (Spine:72, :84; Addendum:201–205, :378–399). |
| Fictitious Parties helper pin and assumed CI source building | Both are explicit, owner-bound prerequisites (Spine:326–327); corresponding stories and status actions exist. Their continued absence is release readiness, not a fresh unacknowledged architecture defect. |
| Dependency gate rejects required client transitives | AD-15 admits the exact locked client/Contracts/Stack baseline and the first-party Decoration Package while limiting Module additions (Spine:144; PRD:99). |
| Sample contaminates the shipped tool or declares two Modules | One sample Module is test-only; the built production tool uses only the manifest, and the benchmark combines production assemblies with the sample separately (Spine:144, :150, :200). |
| Pre-initialization stdout corruption, unsafe profiles, missing bootstrap | AD-12 binds stderr/zero stdout failure behavior (:126); AD-14 binds locking, flush/atomic replacement, permissions, and symlink rejection (:138); AD-17 defines bootstrap publication (:156). |

## Gate recommendation

Keep the current approved decisions. Resolve RUB-20260923-01 before Module vector authoring, or record an explicit prerequisite with a responsible owner and freeze point. Carry existing upstream gates forward without treating their open implementation status as evidence that the architecture's previous fixes failed. Combine this rubric result with the independent technology and adversarial findings for the final validation verdict.
