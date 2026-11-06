---
title: Reconcile platform scopes and isolated profile homes
created: '2026-11-06'
status: applied
review_mode: batch
source_action: epic-4-retro-item-3-reconcile-platform-scopes
approval: 'Product/architecture owner approved P1–P8 in conversation on 2026-11-06'
---

# Sprint Change Proposal — Platform Scopes and Profile Homes

## 1. Issue summary

Epic 4 retrospective F3 found shipped behavior without a corresponding McpCli planning decision. PR #3 and commits `1b369a9`, `06cfdf2`, `6e63ecc` and `4052803` introduced operation-level `PlatformScope`, public tenant canonicalization, reservation of `system`, and `MCPCLI_HOME`. The PRD, architecture and Story 4.8 still require Tenants to use fixed `system` tenancy. The code's AD-27 reference belongs to EventStore and does not constitute a McpCli architecture decision.

Adopt the existing generic behavior explicitly, update its normative documents and agent guidance together, and retain the historical record that implementation preceded this approval. This proposal does not retrospectively claim those changes were authorized by the frozen Story 4.18 spec or decide whether their release version was appropriate.

Evidence at `6725d953d160eafba85b8bf9e11eea2e665d3684`:

- `src/Hexalith.McpCli.Abstractions/HexalithCommandAttribute.cs:24` and `HexalithQueryAttribute.cs:24`: public `PlatformScope` declarations.
- `src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:199`: validate the declared scope and forbid its combination with `FixedTenant`; `RoutingResolver.cs:122`: canonical scope syntax.
- `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:114`: lowercase variable-scope tenant inputs before selection; `:125`: reserved public `system`; `:312`: platform, fixed and operator-gated variable resolution.
- `src/Hexalith.McpCli.Core/Settings/ProfileStore.cs:22`: explicit file path, then `MCPCLI_HOME`, then user-profile home; invalid overrides fail safely.
- `README.md:429,488,500,502` documents the deployed contracts. `PlatformScopeTests`, `PlatformScopeCommandTests`, `PlatformScopeProtocolTests` and `ProfileStoreTests` provide focused evidence and identify the appropriate verification lanes.
- Fresh built CLI descriptions: `tenants.list-tenants` reports `envelope.platformScope: platform:tenants` and omits `tenant` from its arguments; `tenants.get-tenant` has no platform/fixed scope and accepts `tenant`; `parties.create-party` accepts ordinary tenant input. Offline raw descriptions are retained in `/tmp/mcpcli-platform-proposal-jcb4yp_e/` and make no backend authorization claim.

## 2. Impact analysis

| Area | Required reconciliation |
| --- | --- |
| Epic 1 | Operation declarations, descriptors, discovery and invalid-routing diagnostics include `PlatformScope`; the generic module marker remains unchanged. |
| Epic 2 | FR-15/16 tenancy and FR-18 profile-location criteria describe current precedence, canonicalization, reserved input and isolated homes. |
| Epic 3 | Descriptions expose optional `envelope.platformScope`; the five generic tools and existing input records remain the public surface. |
| Epic 4 / Story 4.8 | Replace the fixed `system` requirement with current Tenants declaration and per-tenant read semantics. Preserve all immutable artifact, inventory, vector, live and release gates. |
| Epic 5 | No edits, status changes, new implementation or capability authorization. Its already stated dependence on Epic 4 acceptance remains. |
| PRD and addendum | Correct the tenant glossary, journey, declaration table, FR-3/9/15/16/18, §8.1 prerequisites, argument notes and result schemas/examples. |
| Architecture | Amend AD-3/5/9/11/14; record a local AD-22; clarify current executable version sources and update MCP/CLI version references. |
| UX | No separate UX artifact exists. CLI/MCP descriptions and profile setup are the affected machine-facing flows. |
| Agent guidance | Replace stale tenant/profile rules and the MCP/CLI version sentence in the three byte-identical entry points; retain the CI-pin prevention change. |
| Ownership records | Apply the separately accepted F11 single-maintainer model consistently to the planning wording. |

The first increment remains one generic gateway client, one shared executor and two heads. Declaring a platform scope grants no authority: the Gateway still validates operation, credential, surface and permission. Infrastructure administration, HTTP identity forwarding and legacy retirement remain separately gated. No new service, dependency or migration is needed for this reconciliation.

## 3. Recommended approach

**Direct adjustment** of existing requirements and acceptance criteria is recommended. Effort is low to moderate: one coordinated documentation change and focused verification, followed by the existing hosted gates. Scope classification is **moderate**, because product and architecture owners must approve a cross-artifact contract reconciliation even though implementation has already shipped. There is no supported basis for a calendar estimate beyond that bounded work and CI runtime.

Rollback would remove behavior required by the currently enrolled Tenants release, require another public compatibility transition and new package qualification, and would not repair the historical planning gap. MVP reduction would leave the shipped contract undocumented. Neither is recommended. No new epic, artificial retrospective Story 2.14, or epic resequencing is proposed; the existing retrospective action is the reconciliation work item.

Main risks are accidentally treating a scope declaration as authorization, normalizing exact fixed/platform values, interpreting profile relocation as a settings-precedence change, or treating this approval as acceptance of unrelated retrospective findings. The edits and verification below distinguish those cases explicitly.

## 4. Detailed change proposals

### P1 — PRD tenant vocabulary, journey and declarations

**File:** `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md`; §2.3 UJ-1, §3 Tenant/Profile, §4 Tenant, §5.1 tables and FR-3, FR-9, §8.1 Tenants prerequisite.

**Before:** UJ-1 says the description identifies `system` as the fixed Envelope Tenant; FR-3 says “Tenants declares `system`”; the marker table names Tenants as the fixed-tenant example; §8.1 starts with `fixedTenant = "system"`.

**After:**

> An Operation may declare an exact `platformScope`, independently of its routing domain. Its scope is `platform:` followed by a nonempty lowercase ASCII name made of letters, digits and single hyphens, starting and ending with a letter or digit. It cannot coexist with a Module's `fixedTenant`; malformed or conflicting declarations are excluded with `invalid_routing_value`. The Gateway must recognize and authorize the exact cataloged scope. Fixed tenants remain supported for compatible Modules and are never inferred from a Module name.
>
> Current Tenants Commands and the cross-tenant reads `tenants.list-tenants` and `tenants.get-user-tenants` declare `platform:tenants`. Single-tenant reads `tenants.get-tenant`, `tenants.get-tenant-users`, and `tenants.get-tenant-audit` use the selected public tenant and the matching managed-tenant aggregate identifier. Tenants has no fixed `system` scope. These are enrolled Contracts facts, not module-specific executor branches.

Add `platformScope` to both operation-attribute member contracts. In UJ-1, have Nadia describe the per-tenant read, supply the session `acme` tenant, and then create a party under `acme`; use a platform-scoped list read as the separate discovery example. The Profile glossary points to FR-18 for home relocation. FR-9 includes optional `envelope.platformScope` alongside optional `fixedTenant`.

### P2 — PRD FR-15/16 scope and tenant selection

**Before:** FR-15 requires every Tenant to match the ordinary tenant pattern; FR-16 starts with Module `fixedTenant`, then gated per-call tenant, then session tenant. Case normalization and reserved public `system` are unspecified.

**After — replace the tenant-validation/selection clauses:**

> Resolve the Envelope tenant from declaration and trusted context, never from Payload. First use a valid Operation `platformScope`; otherwise use Module `fixedTenant`; otherwise select between the public session and per-call MCP tenant. Platform and fixed declarations ignore the session tenant and require any per-call value to match the declaration exactly using ordinal equality. The override gate cannot replace a declaration.
>
> For variable-scope calls, lowercase the session and per-call inputs invariantly without trimming before selection and override comparison. Matching canonical values need no override. A different per-call value may replace a configured session tenant only when `allowTenantOverride` is true; when no session tenant exists, the canonicalized per-call value is used without that gate. CLI `--tenant` remains a session setting. A missing tenant fails validation.
>
> The resolved ordinary tenant must contain 1–64 lowercase ASCII letters, digits or hyphens and start and end with a letter or digit. Public variable-scope `system`, including case variants after canonicalization, fails at `/tenant`. Exact historical `FixedTenant` declarations retain their existing compatibility behavior. A declared platform scope uses its separate scope grammar and cannot be supplied to an ordinary operation through `--tenant` or the MCP argument to acquire platform authority.
>
> A mapped payload tenant is filled from the resolved request scope, including a declared platform scope; a supplied value must be a JSON string exactly equal to that resolved value. No payload value supplies authority or overrides the trusted envelope. Conflicts fail with `validation_failed` and no Gateway call.

This reconciliation records the existing normalization order. It does **not** close F7: refusal of non-ASCII input before lowercasing is a separately assigned upstream/local fix. The intended tenant vocabulary remains ASCII; the known Unicode-folding gap is not an approved exception.

### P3 — PRD FR-18 and profile location

**Before:** §5.6 and the Profile glossary specify only `~/.eventstore/mcpcli.json`.

**After — add to FR-18:**

> The default profile file is `<user-profile>/.eventstore/mcpcli.json`. An absolute `MCPCLI_HOME` relocates it to `<MCPCLI_HOME>/.eventstore/mcpcli.json` on every supported OS. An explicit constructor file path takes precedence; an unset override retains the default. Empty, whitespace-only, relative, control-character-containing or existing-file overrides fail as `configuration_invalid` without exposing the supplied path or falling back to the real user's home. This is a store-location selector, not a per-call identity value or another setting-precedence source. Atomic writes, permissions, ACLs, link rejection and isolation from the admin CLI's `profiles.json` remain required.

### P4 — Normative addendum E/G and mechanism notes

**File:** `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/addendum.md`.

**Before:** §B describes one ordinary tenant grammar; §D presents historical `system` tenancy as current; §E's per-call tenant note says “fixed tenant, then operator gate”; §G allows only `envelope.fixedTenant`, omits `tenant` only for fixed Modules, and shows `system` in Tenants examples.

**After:**

- §B distinguishes ordinary public tenants from declaration-only platform scopes and links FR-15/16. Label §D's original Tenants survey as historical and point to current §8.1 behavior.
- §E references “declared platform scope, else fixed tenant, else canonical public tenant under the operator gate.” Add the FR-18 home-location paragraph outside the session-setting table so `MCPCLI_HOME` is not mistaken for an identity override.
- §G adds optional `envelope.platformScope`; its scope grammar is the P1 grammar. `envelope.fixedTenant` and `envelope.platformScope` are mutually exclusive. `arguments` omits `tenant` for either declaration. Success `tenant` is the resolved ordinary/fixed tenant or the exact declared platform scope, with corresponding validation rules.
- Replace the `tenants.get-tenant-users` describe example with a variable-scope envelope that includes `tenant` in `arguments` and has no fixed/platform member. Replace the list-tenants result's `tenant: system` with `tenant: platform:tenants` and include a separate platform-scope description example.
- §B's current package references become ModelContextProtocol **2.3.1** and System.CommandLine **2.0.14**, with the catalog and root overrides as version authority; AspNetCore remains a future HTTP dependency.

These are public-document contract edits. Do not change unrelated §G schema acceptance gaps or claim they have been repaired by text reconciliation.

### P5 — Local architecture decision and aligned records

**File:** `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md`.

**Before:** AD-3 omits platform scope from descriptors; AD-5's description omits it; AD-9 has only fixed/gated/session precedence and one tenant pattern; AD-11/14 and the State convention fix the profile location; AD-12 and Stack name older MCP/CLI versions.

**After:**

1. Add `PlatformScope` to the Operation descriptor and description-envelope contract in AD-3/5. Catalog validation and exclusion remain shared Core responsibilities.
2. Replace AD-9's tenant clauses with P2, preserving its existing validation pipeline, actor rules, extensions, idempotency and once-only submission.
3. Amend AD-11/14, State and the profile node in the runtime diagram with P3's store-location precedence. No component or dependency-direction change is needed.
4. Add **AD-22 — Declared execution scopes and public tenants**, binding FR-2/3/9/15/16/18. It adopts P1–P3, names the code/tests as evidence, dates this reconciliation, and records that upstream EventStore AD-27 is background rather than this repository's authority. A follow-up implementation replaces the ambiguous code comment's local reference with AD-22.
5. Update MCP and System.CommandLine references to 2.3.1/2.0.14. Clarify that effective versions come from `global.json`, root `Directory.Build.props`, the root-declared Builds catalog and `tools/dependency-policy.json`; historical architecture Stack rows cannot instruct a downgrade of the qualified build. No dependency update is authorized by this proposal.

### P6 — Existing epic and story criteria

**File:** `_bmad-output/planning-artifacts/epics.md`; requirement summaries and Stories 1.1, 1.4–1.5, 2.1–2.3, 2.5–2.6, 2.8, 3.1 and 4.8. Retain story IDs and completion history.

**Before:** FR16 summary and Story 2.5 use fixed/gated/session precedence; Story 4.8 requires `fixedTenant: system`; FR18 and Stories 2.1–2.3 assume only the default profile home. Declaration/discovery stories do not name platform scope.

**After:** update those summaries and add these acceptance clauses to the corresponding existing stories:

- **Given** a valid operation platform scope, **when** its Catalog descriptor is described, **then** the exact scope is exposed, `tenant` is omitted from envelope arguments, and conflicting scope/fixed declarations are excluded with `invalid_routing_value`.
- **Given** a platform or fixed declaration and any session tenant, **when** an MCP per-call tenant is omitted or equals that declaration exactly, **then** the declaration supplies the Envelope; a conflicting value fails before any Gateway call regardless of the override gate.
- **Given** variable session/per-call tenants differing only in ASCII case, **when** they resolve without override permission, **then** they compare canonically and produce one lowercase tenant; whitespace is not trimmed, a disallowed different tenant fails, and public `system` fails before submission.
- **Given** valid and invalid `MCPCLI_HOME` inputs or an explicit store path, **when** configuration is read or mutated, **then** P3 precedence, safe refusal, isolation and existing file protections hold on every supported OS.
- **Given** current Tenants 7.0.4 Contracts, **when** Story 4.8's declaration is checked, **then** its Commands/cross-tenant reads use declared `platform:tenants`, per-tenant reads use the selected matching tenant, and no `FixedTenant` is declared. Keep all existing audit/paging semantics and full vector gates.

Replace the Additional Requirements instruction to pin historical architecture versions with consumption/verification of the effective tracked version sources. Do not add or change Epic 5 stories, freeze a nonexistent Story 2.14, or rewrite frozen implementation specs to suggest prior authorization.

### P7 — Synchronized agent entry points

**Files:** `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`.

**Before:** the stack sentence names MCP 2.2.0 / System.CommandLine 2.0.12; the tenant rule omits platform scope and says a per-call value without a session is “used as supplied”; the profile convention names only the default path.

**After — replace the tenant rule:**

> Tenant comes from the envelope, never from payload: an operation's exact declared `PlatformScope` first, else the Module's exact `FixedTenant`, else the canonical public session/per-call tenant. A platform scope cannot coexist with `FixedTenant`; any per-call value must exactly match either declaration, and the session tenant is ignored for that operation. For variable-scope operations, lowercase session and MCP per-call input invariantly without trimming before selection and override comparison. A differing per-call tenant replaces a configured session only under `allow-tenant-override`; with no session, use the canonicalized per-call value. Refuse public variable-scope `system`. The Gateway independently authorizes the cataloged scope and credential. Forwarded headers become a source only with the future HTTP transport.

Update the stack sentence to MCP 2.3.1 / System.CommandLine 2.0.14. Extend the profile convention with the P3 `MCPCLI_HOME` location and safe-refusal rule. Edit AGENTS.md, copy it byte-identically to the other two entry points, then run `scripts/check-agent-instructions-sync.sh`. Preserve the Builds workflow-pin pitfall added by the CI repair.

### P8 — Already accepted approval model

**Files:** PRD §8.1 checklist item 6 and SM-5; matching description-review criteria in Stories 4.8 and 4.10.

**Before:** review must be “recorded in the Module's pull request.”

**After:** review and owning-maintainer approval are recorded in an owning-module PR **or** a versioned McpCli evidence record. Under the single-maintainer model explicitly accepted in retrospective F11 on 2026-11-06, the requesting owner may supply that approval. Cite the accepted retrospective decision and preserve exact artifact/vector bindings. This reconciles an existing human decision; it grants no new approval for operations or artifacts and does not close unrelated legacy tracking automatically.

## 5. Implementation handoff and acceptance

**Product/architecture owner:** approve or revise P1–P8 as one batch. **McpCli maintainer:** apply the approved text, update document dates and input provenance, verify concrete claims against the built tool and current package bindings, synchronize entry points, and retain the decision link in the retrospective action record. No upstream source edit is required. Any later change in runtime semantics gets its own story/proposal.

Use the existing retrospective item as the work tracker. Proposal approval alone permits recording an approved reconciliation decision; mark the full item done only when its document and guidance updates are applied and verified. Do not change the retrospective verdict or mark Epic 5 entry authorized automatically. Item 1 needs hosted main CI success; item 2 needs its separate bootstrap guard and owner decision about 1.1.0/2.0.0.

Acceptance for applying this proposal:

1. Every current-tenancy reference in the named PRD/addendum/architecture/Epics 1–4 sections agrees with P1–P4; historical survey statements are labeled historical. Exact scoped/fixed matching remains distinct from canonical public tenant comparison.
2. Built `describe` output for a platform operation, a per-tenant Tenants read and an ordinary Parties operation agrees with the normative envelope fields and arguments. No declaration grants Gateway permission or widens the generic transport.
3. Focused existing Core, CLI and MCP scope/profile tests pass. Verify each changed CLI claim using the built CLI with a task-owned profile home; use controlled gateways or existing fixtures for execution claims. The known F7 and §G schema findings stay separately tracked.
4. The three instruction files remain byte-identical and pass `bash scripts/check-agent-instructions-sync.sh`; `git diff --check` passes. Validate any exact commit message with the pinned commitlint CLI and recheck HEAD before committing.
5. No Epic 5 file/section/status, root gitlink, package pin, bootstrap release policy or frozen story intent is changed by this reconciliation.

## Checklist record

| Checklist | Status | Result |
| --- | --- | --- |
| 1.1–1.3 trigger, issue, evidence | [x] Done | Retrospective F3 and shipped code/built descriptions identify the planning gap; F11 supplies an already accepted wording decision. |
| 2.1–2.5 epic completion, scope, future dependencies, order | [x] Done | Existing first-increment plan remains viable with amended criteria; no new epic or resequencing; Epic 5 unchanged. |
| 3.1–3.2 PRD and architecture | [x] Done | P1–P6 identify exact affected contracts and decisions. |
| 3.3 separate UX artifact | [N/A] Skip | No separate UX specification; machine-facing discovery and setup are covered in P3/P4/P7. |
| 3.4 secondary artifacts | [x] Done | Guidance, current versions, tests and existing action tracker identified; no infrastructure edit required. |
| 4.1 direct adjustment | [x] Viable | Adopt and verify the already shipped generic behavior. |
| 4.2 rollback | [N/A] Not selected | Would disrupt current enrolled Contracts and add another compatibility transition. |
| 4.3 MVP reduction | [N/A] Not selected | Does not reconcile the actual shipped contract. |
| 4.4 recommendation | [x] Done | Direct adjustment with moderate product/architecture coordination. |
| 5.1–5.5 proposal and handoff | [x] Done | Issue, impact, before/after edits, scope, risks, verification and named responsibilities recorded. |
| 6.1–6.2 accuracy/completeness | [x] Done | Source, tests, full primary planning documents and built offline descriptions inspected. |
| 6.3 explicit approval | [x] Done | Product/architecture owner approved the complete P1–P8 batch in conversation on 2026-11-06. |
| 6.4 sprint status | [x] Done | Item 3 marked done after application and verification; story IDs and completion history preserved. |
| 6.5 final handoff | [x] Done | Approved batch applied by the McpCli maintainer; product/architecture approval and verification evidence recorded below. |

## Approval record

On 2026-11-06, the requesting product/architecture owner answered **approve** to the complete P1–P8 batch and its application. The McpCli maintainer applied and verified the approved clauses in this session. This approval does not decide item 2's bootstrap/publication-history deviations or authorize Epic 5 entry.

## Execution and handoff record

P1–P8 are applied to the PRD, normative addendum, architecture (including local AD-22), existing Epic 1–4 criteria and synchronized agent entry points. The executor's source change is limited to its decision-reference comment. The moderate-scope product/architecture decision was approved by the requesting owner, and the McpCli maintainer completed the developer handoff and verification; no backlog creation, removal or resequencing was needed.

- Solution restore and Release build with warnings as errors passed.
- Existing focused tests: 150 passed; three Windows-only ProfileStore ACL cases skipped on Linux. Core scopes/profile store: 105 passed and 3 platform skips; CLI scopes: 7 passed; CLI profile-home/process checks: 4 passed; MCP scope protocol checks: 34 passed. A first combined class/method CLI selector discovered zero cases and was discarded; corrected separate invocations produced the counts above.
- 31 real CLI invocations verified relocated profile CRUD, selection, discovery, exact example Envelope metadata, invalid-home refusal and stdout/stderr discipline. Raw task-owned receipts are in `/tmp/mcpcli-scope-reconciliation-7iduet6r/`; retained summary: `_bmad-output/implementation-artifacts/evidence/epic-4-retro-item-3/verification.json`.
- Both Epic 5 sections, all story IDs, AD-17, Stories 4.6/4.18, package pins, native source selection and workflow pins compare unchanged with pre-approval baseline `57659318911f5071b2c74cc8005fe0965c6a1379`. The Builds workflow-pin pitfall is retained.
- `bash scripts/check-agent-instructions-sync.sh` and `git diff --check` pass. Three agent entry points are byte-identical.

The retrospective action is complete. Item 2, F7 and unrelated §G schema findings remain separate; the rejected retrospective verdict and Epic 5 statuses are not changed. This reconciliation has local verification; the previously recorded hosted green run 42213303320 qualifies the CI repair source, not this later documentation commit.
