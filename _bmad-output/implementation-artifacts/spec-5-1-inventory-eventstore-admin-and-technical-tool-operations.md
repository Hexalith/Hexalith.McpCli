---
title: '5.1 Inventory EventStore Admin and technical-tool operations'
type: 'chore'
created: '2026-11-06'
status: 'in-review'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'ad7bf9ee415d09b16b47616740e2cc38fb3d6d9a'
context:
  - '_bmad-output/implementation-artifacts/epic-5-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The migration plan lacks an operation-level EventStore Admin inventory and a current technical-tool census. Infrastructure, compiler, resource and lifecycle behavior could disappear during cutover despite the earlier business-module inventories.

**Approach:** Produce versioned, source-pinned inventories for both Admin heads and the technical surfaces, with every operation's transport, behavior, security class, replacement gap and actual approval reference. Retain unsupported capabilities as proposed `defer / exclude` and obtain owner review before claiming completion.

## Boundaries & Constraints

**Always:** Follow the Epic 4 format. Separate registered operations, aliases, variants, unavailable stubs and unregistered helpers. Pin full revisions; identify maintainers as roles when no named owner exists. Separate destructive effects, confirmation and authenticated eligibility. Preserve Platform AD-14's public-client denial of UI-only and human-confirmation operations; `confirm: true` proves no human authority. Retain missing approval and replacement evidence.

**Never:** Change runtime code, dependencies, reference contents, package publication or enrollment. Execute legacy mutations, compiler migrations or live services. Invent decorated replacements, owner signatures, parity or retirement permission. Rewrite the historical inventories or the authoritative AI.Tools plan in its read-only checkout. An approved inventory remains documentation, never execution authority.

</frozen-after-approval>

## Code Map

- `evidence/story-5-1/planning/README.md` beside this spec indexes the unapproved row-ready findings and exact source census.
- `references/Hexalith.EventStore/` at `3d4ba67db99f2f0bcd64b7d353609b555870cc9b`: Admin CLI `Program.cs:32` and command factories determine reachable actions; `Commands/Backup/BackupCommand.cs:16` registers three stubs. Admin MCP `Program.cs:56`, `Tools/`, clients and Admin controllers establish registrations, routes, roles and human gates.
- `references/Hexalith.FrontComposer/` at `fbb9c3822dfa407e72739238cd472567f45f1e82`: CLI command/path-safety files and MCP descriptor/configuration, invocation and skill-resource providers define fixed and manifest-dependent surfaces. Read resource metadata, never agent skills under `references/`.
- Local `frontcomposer-migration-inventory-v1.md` and five companion inventories preserve historical pins and limited session approvals. Keep them immutable.
- Root `.gitmodules` bounds the census. Inspect tracked projects, packaging, registrations and ownership; exclude nested references, fixtures and exempt Builds tooling. The authoritative AI.Tools migration plan and Platform architecture AD-14 constrain approval and eligibility.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/implementation-artifacts/eventstore-admin-migration-inventory-v1.md` — enumerate both reachable Admin surfaces and their variants, current routes, security/confirmation/destructive classifications, observed limitations and proposed dispositions; retain unregistered helpers separately.
- [x] `_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md` — reconcile current FrontComposer compiler, resource, skill-resource and lifecycle behavior with the historical pin; inventory manifest host consumers and all remaining proprietary packages with owning maintainers and removal gates.
- [ ] Both inventories — obtain concrete-row review; bind actual approval instructions, authority and versions. Session approval alone leaves owning-maintainer acceptance pending; unapproved rows block completion.
- [x] `_bmad-output/implementation-artifacts/evidence/story-5-1/verification.md` — retain reproducible static source/registration/row checks and their results, full pins, census scope and compatibility handoffs to Stories 5.2–5.5. Verify every source anchor and retain unresolved gaps without duplicating earlier ledger entries.
- [x] This spec and `_bmad-output/implementation-artifacts/sprint-status.yaml` — record verification and workflow state; leave completion open while an owner approval or completeness check is missing.

**Acceptance Criteria:**
- Given pinned Admin registrations, when checked, then every reachable action/tool has one row with transport, behavior, security class, disposition, replacement gap, owner and approval; stubs and absent resources have separate evidence.
- Given current FrontComposer registrations, when the technical inventory is checked, then both compiler commands, every concrete resource/skill resource and lifecycle call are covered, and dynamic families name their inspected consumers without claiming a finite ecosystem-wide catalog.
- Given destructive, confirmation-required or UI-only behavior, when its row is read, then effects, current guards and missing authority are explicit and no row authorizes public McpCli execution.
- Given root-declared checkouts, when scanned, then every proprietary CLI/MCP project has an owner; absent surfaces and exempt/test tooling have evidence and scope limits.
- Given pending owner decisions or unsupported equivalents, when readiness is reported, then missing approvals block completion and deferred capabilities keep compatibility binaries and downstream contract, conformance and retirement gates.

## Implementation Notes

- 2026-11-06: User approved the specification with "approve and stop". Intent is frozen; implementation has not started. This approves the spec, not owning-maintainer inventory decisions.
- 2026-11-06 (build): Prepared candidate inventories `eventstore-admin-migration-inventory-v1.md` and `technical-tools-migration-inventory-v1.md` at `1.0.0-candidate.1`. The Admin candidate has 31 registered CLI operations (21 remote, 7 local, 3 stubs), 6 unregistered helpers, 28 MCP tools, 13 variants, 7 absent-surface rows and 6 gates; the technical candidate has 3 host surfaces, 13 resources, 2 compiler leaves, 9 variants, 4 manifest consumers, 13 census surfaces, 7 exempt/test rows, 9 surface-free roots and 5 gates. Every concrete row proposes `defer / exclude`; all 156 rows reference A0 (approval pending). Source reading also found that the pinned Admin server denies `GET /api/v1/admin/health` without an `X-Hexalith-Scope` header that neither legacy head sends (AV10), that both stream-list clients request an unregistered root route (AV11), and that the FrontComposer historical pin is not an ancestor of current source while its `Mcp/` and corpus trees are identical. No runtime code, dependency, reference, enrollment, publication or ledger entry changed; no legacy tool, migration or service ran.
- 2026-11-06 (blocker): The concrete-row review task stays open. Neither the EventStore/platform-operator maintainers nor the FrontComposer and census owners have approved any row, and this build instruction authorizes preparation only. Replace A0 with an approval record binding the instruction, authority, inventory version and revisions before completion; a session approval would still leave owning-maintainer acceptance pending.

- 2026-11-07 (resumed review): Earlier P1–P18 corrections were already present. Three independent review layers produced 11 findings: nine patch groups (P19–P27), one carried rejection (BH2/earlier EC6), and the duplicate pin finding grouped into P19. Refreshed Builds, Platform and Tenants census pins, corrected CLI redaction, MCP paging/normalization/input/error variants, profile failure/overwrite behavior and inspect's shared path canonicalization. Both inventories are now `1.0.0-candidate.2`; all 156 A0 approval references remain pending. Added a damaged-input case for stale exempt-tool pins. The complete static block exits 0 with 386 source anchors (52 content-checked), 23 damaged inputs rejected and `git diff --check` passing. No runtime, dependency, reference, historical inventory or ledger changed; no .NET or live command ran. The concrete-row approval task stays open, spec `in-review`, sprint `in-progress`.

## Spec Change Log

## Review Triage Log

Pass 1, 2026-11-06. Layers: blind (BH), edge case (EC), verification gap (VG; no gap blocks filed, three other findings).

| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| VG1, BH1 — "completion while pending" damage replaces only `status: 'in-progress'` | medium | patch (P1) | Two layers reran the block with spec `in-review`: the replace is a no-op, `('in-review', 'in-progress')` is accepted, exit 1. Recorded output and exit 0 are stale. |
| VG2, BH2, EC1 — changed-path check needs a dirty tree | medium | patch (P2) | `verification.md:738` asserts `changed and …` from `git status`; a clean post-commit tree fails, and the recorded 12 paths include the unrelated `epic-4-retro-2026-11-06.md`. |
| VG3, BH3 — whitespace gate scope | low | patch (P3) | `git diff --check` skips untracked files; the LF check names five files and omits `epic-5-context.md` and `planning/*` (clean today). |
| BH4, EC14 — Admin G3 omits AC11, AC12, AC19 | medium | patch (P4) | Those rows cite G3 for confirmation safety; G3 (`eventstore-admin…:283`) lists only AC13, AC20, AC21, AM14 and six MCP writes. AC25/AC28 cite G6, which does not mention their destructive overwrite/deletion. |
| BH5 — PS04, PS09 cite G3 for retire-together | low | patch (P5) | Technical G3 is the re-pin gate; the retire-together rule is G4. |
| BH6 — census definition admits Parties.UI | low | patch (P6) | The written rule counts any `src/` project referencing `Hexalith.FrontComposer.Mcp`; FK03 meets it but is not a PS row, and the exception is stated only in FK03 and the verifier. |
| BH7 — anchors checked only for non-blank lines | false | reject | `verification.md` claims exactly "resolve to a non-blank line" plus 16 content checks; 30 sampled inventory anchors (HealthCommand, ProfileAdd, ToolHelper, Program, AdminApiClient, backup service) all land on the described code. Planning-JSON disagreement is P7. |
| BH8, EC18 — planning evidence stale, unverified and not marked superseded | low | patch (P7) | `planning/README.md:37` still lists the inventories as remaining work; `admin-cli-source-findings.json` has set-policy `destructive: false` against AC20; planning anchors such as `ProfileShowCommand.cs:49` (a brace) are never checked. |
| BH9 — cross-head table pairs AC23, AC24 with AM01 | low | patch (P8) | `backup restore`/`backup list` stubs have no MCP counterpart; only AC22 corresponds to AM01. |
| BH10 — AX06 cites three of eight controllers | low | patch (P9) | The 39 actions span Backups, Dapr, DeadLetters, Health, Storage, Streams, Tenants and Traces; only three controllers are anchored. |
| BH11 — frontmatter departs from Epic 4 keys | low | patch (P10) | FrontComposer/Projects 1.0.0 use `approval_authority` and `external_maintainer_approval`; the candidates use `owning_maintainer_approval` and omit `approval_authority`. |
| BH12 — AD-11/AD-14, AI.Tools plan 1.1.0 and EventStore AD-22 unanchored | low | patch (P11) | Every disposition depends on them; they are cited by name only, so owners cannot locate the governing clauses. |
| BH13 — preservation properties absent from gates | low | patch (P12) | `epic-5-context.md:26` requires preserving freshness, redaction, task context, actor attribution, paging, token budgets and idempotency before retirement; Admin G5, technical G4 and "Evidence still absent" name only authorization, audit, output and exit codes. |
| BH14 — Builds revision and composition/deploy routing omitted | low | patch (P13) | PE01/PE02 carry no Builds revision; `Parties.AppHost.csproj:18`, `Memories.AppHost.csproj:14` and Memories `deploy/kubernetes/base/mcp-deployment.yaml` route MCP projects but appear nowhere in the census or 5.5 handoff. |
| BH15 — FH table lacks effect/confirmation | low | patch (P14) | Admin and FC tables carry them; FH02's open family can hold consumer writes and the table does not say who classifies them. |
| BH16 — spec Code Map anchor `BackupCommand.cs:16` | low | reject | Fix would edit this build's spec; the inventory anchors lines 15–17 correctly. |
| BH17 — AC31 effect "local read" | low | patch (P15) | `config completion` reads no state; it writes a generated script to stdout. |
| EC2 — historical immutability only against HEAD | low | reject | Hypothetical later commit; the fix adds a hash guard for a state not demonstrated. |
| EC3 — AV dispositions unchecked | low | reject | All 13 AV rows read `defer / exclude`; adding a guard for a hypothetical edit. |
| EC4 — damage cases accept any exception | low | reject | All 22 cases fail at their targeted assertions today; per-case labels add complexity. |
| EC5 — `pending=False` branch unreachable | low | reject | Approval will replace A0 and require a verifier update anyway; no current failure. |
| EC6 — AM routes matched against all client routes | low | reject | No row cites another tool's route; resolver work for a hypothetical. |
| EC7 — overstated policies pass | low | reject | Every security cell names exactly the derived policy; a new guard for a hypothetical. |
| EC8, EC16 — AM06 tenant filter is inert | medium | patch (P16) | `AdminTenantAuthorizationFilter.cs:25` forwards when the action has no `tenantId` and no admission; `TriggerCheck` (`AdminConsistencyController.cs:100`) takes only a body, and `TryResolveTenantScopeForBody` admits any tenant for Admin-role callers. It is the only such action; the verifier derives the filter from the attribute alone. |
| EC9, EC17 — `.codex/config.toml` channel unclassified | low | patch (P17) | 11 roots track `.codex/config.toml`; Memories and Projects register `fluent-ui-blazor`/`microsoft-learn` there. PE06 and its check cover only JSON configs and omit Memories. |
| EC10 — drift regex on deletion-only stats | low | reject | Current stats all have insertions; future re-pin handling adds branches. |
| EC11 — anchors with other extensions skipped | false | reject | The only unmatched backticked `:digits` token in either inventory is the URL `http://localhost:5002`; no anchor is skipped. |
| EC12 — porcelain rename parsing | low | reject | No rename in the tree; hypothetical. |
| EC13 — nested tool files missed | false | reject | No `[McpServerTool]` file exists outside top-level `Mcp/Tools/` at the pin. |
| EC15 — Story 5.2 handoff partition | medium | patch (P18) | `verification.md:843` omits AM01 and AC22–AC30 and lists AC14–AC17 under both infrastructure administration and tenant reads. |

Pass 2, 2026-11-07. Layers: blind (BH), edge case (EC), verification gap (VG; no findings for static documentation). The earlier P1–P18 corrections are already present; they are not reapplied.

| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| BH1 — stale census pins and recorded execution | medium | patch (P19) | The documented `bash -e` block exits 1 at `check_technical`'s PN revision comparison: Builds, Tenants and Platform moved in subsequent commits. Refresh the three pins and rerun; preserve the earlier observation as history. |
| BH2 — MCP route checked against combined client source | low | reject (carried) | Carried from pass 1 EC6: the checker still accepts another tool's valid route in a deliberately altered row, but no current row cites that route. A method resolver would add complexity for the same hypothetical edit; retain the prior verdict and route. |
| BH3 — CLI output described as raw | medium | patch (P20) | `StreamStateCommand.Columns` selects `State`, table/CSV use safe descriptors, and `JsonOutputFormatter` drops raw fields when companion descriptors exist. The correspondence table and AC06 overstate raw output, which could misdirect redaction parity. |
| BH4 — MCP timeline cursor unavailable | medium | patch (P21) | `StreamTools.GetStreamEvents` and `AdminApiClient.GetStreamTimelineAsync` take sequence bounds and count but no continuation token; `ToolHelper` redacts returned tokens. AM22 must state the cursor-paging limitation without denying sequence-bounded follow-up requests. |
| BH5 — normalization precedes session fallback | medium | patch (P22) | The five optional-filter tools call `NormalizeOptionalScope`, trimming nonblank input and turning whitespace-only input into null before session fallback. AV08's unconditional "explicit values win" would misstate tenant selection. |
| BH6 — MCP input guards omitted | medium | patch (P23) | Session tenant, backup/check tenant and projection writes use `ValidateTenantId`; projection writes and consistency cancellation use `ValidatePathSegments`. Record the exact applicability and `invalid-input` behavior before preview/dispatch. Read tools do not all use these guards. |
| BH7 — corrupt profile replacement omitted | medium | patch (P24) | `ProfileManager.Load` returns an empty store after JSON corruption, and profile add saves that store. AC25 and G6 omit possible whole-store replacement, beyond a same-name overwrite. |
| BH8 — profile load failure paths omitted | medium | patch (P25) | `GlobalOptionsBinding.ResolveInternal` warns and skips a profile after I/O/access failure, skips an unavailable default home, but rethrows missing named-profile and unsupported-version failures. AV02 must retain their environment/credential-selection implications. |
| BH9 — inspect shares changed canonicalization | low | patch (P26) | `InspectCommand` is unchanged, but it calls `ProjectSelection.Resolve`, which uses the changed ancestor-resolving `PathUtilities.Canonical`. Qualify FC01/FV06 and include that effect in FV09. |
| BH10 — ordinary MCP error cases omitted | low | patch (P27) | `ToolHelper.HandleException`/`HandleHttpException` implement the listed status categories, malformed-JSON handling and a timeout document for every caught `TaskCanceledException`, including caller cancellation. Add these observable variants to AV06. |
| EC1 — stale pins invalidate the reproducibility claim | medium | patch (P19) | Independently confirmed the same three full revision mismatches and the resulting verifier failure; shared root cause with BH1. |

## Verification

- Reconcile source-derived registration sets against inventory row identities, rejecting omissions, extras, duplicates, incomplete fields and unsupported approval claims.
- Recheck full revisions and clean source status for every inspected root checkout. Verify referenced files and line anchors at those pins.
- Run the reproducible Python source/row check documented in the evidence file, then `git diff --check` and inspect the changed-path set. This documentation-only change needs no .NET build or live topology.

**Result (2026-11-07):** the block in [evidence/story-5-1/verification.md](evidence/story-5-1/verification.md) exited 0 against both `1.0.0-candidate.2` inventories, with all PASS lines, 386 resolved source anchors (52 content-checked), 23 rejected damaged inputs and `git diff --check` passing. It ends with `BLOCKED: 156 rows carry A0`, so completion remains open; spec `in-review`, sprint `in-progress`.
