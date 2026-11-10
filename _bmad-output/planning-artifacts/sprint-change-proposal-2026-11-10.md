---
title: Plan McpCli's side of the Folders migration
created: '2026-11-10'
status: applied
review_mode: incremental
source_action: 'Hexalith.Folders requests R1–R4 (Folders sprint-change-proposal-2026-11-10.md, Section 5, at Folders 4af40367d597d8f9b51a229401693401300e3f3d)'
baseline: 24ae42e6bbd37129c76d3932260539d985b1027d
approval: 'Product owner approved P1–P8 individually in conversation on 2026-11-10, including the P3 correction made while drafting P4, then approved the complete proposal ("yes")'
---

# Sprint Change Proposal: Folders Enrollment, Parity and Retirement in McpCli

## 1. Issue summary

On 2026-11-10 Hexalith.Folders adopted McpCli as its only CLI and MCP surface. Its decision record is `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10.md` at Folders `4af40367`. The owner's decisions are:

- **D1:** `Hexalith.Folders.Cli` and `Hexalith.Folders.Mcp` are frozen to safety and continuity fixes. They retire only after replacement or withdrawal plus parity evidence.
- **D2:** Folders' MVP CLI and MCP cells count only through McpCli heads. McpCli enrollment of Folders is therefore on the Folders MVP critical path.

Folders now owns gaps G1–G5 of the McpCli Folders inventory 1.0.0, in Folders Stories 5.12–5.14, and G6 in Folders Story 5.10. It also added two pending external nodes that McpCli must satisfy:

- **EXT-MCPCLI-FOLDERS-ENROLLMENT:** an owner-approved inventory naming a decorated type for every `replace` row; a McpCli release enrolling the exact Folders Contracts version that passes the AD-15 and AD-21 gates; and one execution vector per included operation, with loopback parity.
- **EXT-MCPCLI-FOLDERS-RETIREMENT-GATE:** an inventory in which every legacy tool, resource, CLI leaf and variant is either `replace` with evidence or `withdraw`, plus selected-environment shared-head parity, safety and rollback evidence.

It sent four requests:

- **R1:** Story 5.2 covers the Folders non-gateway classes.
- **R2:** Story 5.8 consumes Folders Story 5.12's eligibility decisions, named types and accepted losses.
- **R3:** add Folders stories analogous to the Parties chain 5.3 → 5.4 → 5.5.
- **R4:** record the retirement in a new AI.Tools migration-plan version.

Evidence at `24ae42e`:

- **No story covers the Folders work.** McpCli's Epic 5 has no Folders enrollment, parity or retirement story; Story 5.8 only re-dispositions the inventory (`epics.md`, Story 5.8). The 2026-11-08 refinement decision D2 reads "Parties is the only committed retirement" (`epics.md` frontmatter).
- **Story 5.2 covers Folders only implicitly.** Its first AC reaches the Folders classes through "Epic 4 inventories". The classes Folders depends on are not named: staged content above 262144 bytes, the R01/R02 resources, G6 provider egress, and V01/V02 freshness and paging.
- **Nothing is enrolled for Folders.** No Folders entry exists in `tools/dependency-policy.json` `modules`, `tools/inventory-coverage/v1/` or `tools/conformance-vectors/v1/modules/`. The test AppHost composes only EventStore, Tenants and Parties helpers.
- **The Folders gitlink is old.** It sits at Folders `e88c9400`, before the Folders decision record.

**Category:** a new requirement from a dependent module. No McpCli story failed.

## 2. Impact analysis

| Area | Impact |
| --- | --- |
| Epic 5 | Two stories amended: 5.2 (R1) and 5.8 (R2). Story 5.11 is decoupled from 5.8, so the Parties retirement record never waits on Folders. The Parties chain 5.3 → 5.4 → 5.5, the Epic 5 Entry and gate decision, the `epic-3-retro-item-1` release precondition and D2 are unchanged. Epic 5 can close only after 5.8, which now waits on Folders Story 5.12. |
| Epic 6 (new) | **Replace and Retire the Folders CLI and MCP Server**, Stories 6.1–6.4: enroll, prove, verify the retirement, record it. A new epic avoids a story-number collision with Folders' own 5.12–5.15 and keeps Epic 5's exit independent of Folders' longest chain. |
| Epics 1–4 | None. |
| PRD | None. §8.2 already routes deletions to "the approved successor migration epic". Resources, freshness and filter arguments stay deferred unless Story 5.2's own PRD change admits them. |
| Architecture | None now. The Deferred item "Composition of Projects and Folders in the test AppHost" becomes active through Story 6.1. Story 5.2 produces its own architecture decision. |
| UX | Not applicable. |
| Sprint status | The 5.8 line gets a comment and an Epic 6 block is added. Exact line edits only. |
| Code, CI, tools | Nothing in this pass. Story 6.1 later changes the Folders `PackageReference`, `dependency-policy.json` (`modules`, `testPackages`), inventory coverage, vectors, approvals and live plans together. |
| Cross-repository | Folders Stories 5.12, 5.13 and 5.14 are prerequisites of 6.1. Folders 5.8–5.11 are prerequisites of 6.2, and Folders 5.15 of 6.3. There is also a new Folders prerequisite: a published, server-code-free composition helper. |

Two prerequisites do not appear in the Folders request:

1. **A published, server-code-free Folders composition helper.** The live lane is blocking (Story 4.14), and every enrolled vector needs a companion live plan. Enrollment therefore needs the Folders domain service in the test AppHost under AD-15's test-composition rule, plus a provider double for the G6 operations. Folders has a `Hexalith.Folders.Aspire` project, but it has not been confirmed as server-code-free or published.
2. **The enrollment release is bound by an open action item,** `epic-4-retro-item-6-bind-release-acceptance`. The `epic-3-retro-item-1` precondition is already `done`.

## 3. Recommended approach

**Direct adjustment (selected).** Effort medium, risk medium; the risk is the cross-repository dependency. Rollback is not applicable, because nothing completed is undone. An MVP review is not applicable either: McpCli v1 (2.0.1) has shipped, and PRD §8.1 places Folders after v1.

Decisions made in review:

- **Epic placement:** a new Epic 6 rather than McpCli Stories 5.12–5.15 (P1).
- **Story 5.8 timing, Option A:** 5.8 waits for Folders Story 5.12, exactly as R2 asks, and Story 5.11 no longer waits on 5.8 (P3). The rejected Option B ran 5.8 now with every candidate left `defer` and added a type-naming story to Epic 6.
- **G6 ordering:** G6 is proven by Folders Story 5.10, which follows enrollment in the Folders graph. G6 is a retirement prerequisite, and G1–G5 are enrollment prerequisites. This P3 correction removes a cycle.

Risks:

- **McpCli enrollment waits on Folders' chain** (1.17 → Epic 12 → 5.12–5.14). It is visible as the Epic 6 Entry and the sprint-status comments, and Folders tracks it as graph nodes.
- **AD-21 fails extra Catalog operations,** and the Catalog lists every decorated type in a package. So every type Folders publishes must be an included row with a vector. Story 6.1's composition AC covers the provider double for the G6 operations up front.
- **A Story 5.2 class that stays deferred** keeps its Folders rows `defer` and the retirement gate closed. This is intended; McpCli never gains a legacy fallback.
- **Parties may stay retirement-blocked** by G01–G06, so Folders could become the first Legacy Server deletion for SM-3. Story 6.3 records this explicitly.

## 4. Detailed change proposals

All edits apply to `_bmad-output/planning-artifacts/epics.md` unless another file is named. Throughout, Folders stories are written "Hexalith.Folders Story 5.x".

### P1: Put the Folders chain in a new Epic 6

**A. Epic List.** Insert after the Epic 5 entry, before `## Epic 1: Module Authors Can Publish Discoverable Operations`:

```markdown
### Epic 6: Replace and Retire the Folders CLI and MCP Server

Operators and agents reach every supported Folders operation through McpCli's two heads, and the frozen `Hexalith.Folders.Cli` and `Hexalith.Folders.Mcp` retire with verified replacement evidence. McpCli enrolls the exact decorated Folders Contracts release, proves shared-head parity and safety on a selected environment, verifies the deletion that Folders performs, and records it in the migration plan.

**FRs covered:** FR20, FR21. **Entry:** McpCli Stories 5.2 and 5.8 done; Hexalith.Folders Stories 5.12, 5.13 and 5.14 released (cross-repository prerequisites). MR1–MR9 and MR11 apply as written. MR10 applies to Epic 6 stories: the 2026-11-08 decision covers the Epic 1–4 verdicts, and a rejected Epic 5 verdict recorded before an Epic 6 story starts needs its own recorded decision. The Epic 5 gate decision and its release precondition are unchanged. **Exit:** McpCli evidence satisfies the Folders nodes EXT-MCPCLI-FOLDERS-ENROLLMENT and EXT-MCPCLI-FOLDERS-RETIREMENT-GATE; Hexalith.Folders Story 5.15 has removed the legacy surfaces and McpCli has verified it; a new AI.Tools migration-plan version records the retirement. **Out of scope:** Folders code, adapters or error mapping in McpCli; Folders source edits from this repository; any class Story 5.2 leaves deferred.

**Implementation notes:** Mirrors the Parties chain 5.3 → 5.4 → 5.5 as enroll (6.1), prove (6.2), verify the retirement (6.3), then record it (6.4). Folders stories are always written "Hexalith.Folders Story 5.x".
```

**B. FR Coverage Map.** Append to the end of each line:

- FR20: `; Epic 6 — Enroll Folders vectors and prove Folders replacement parity and safety.`
- FR21: `; Epic 6 — Replace the Folders legacy surfaces, verify their retirement and record it in the migration plan.`

**C. New section** at the end of the file, after Story 5.11. It holds the heading `## Epic 6: Replace and Retire the Folders CLI and MCP Server`, the first paragraph of the Epic List entry, and then Stories 6.1–6.4 (P4–P7).

**D. Frontmatter `changeProposals`:** append `  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10.md`.

**Rationale:** The two repositories keep distinct story numbers, and Epic 5's exit stays independent of Folders' chain.

### P2: Story 5.2 covers the Folders classes explicitly (R1)

**A. Requirements/Dependencies line.**

Before:

> **Requirements:** FR21, FR22; MR1, MR2, MR3, MR9. **Dependencies:** Story 5.1 (Admin inventory G2/G3, technical inventory G2); the Epic 5 entry gate (MR10).

After:

> **Requirements:** FR21, FR22; MR1, MR2, MR3, MR9. **Dependencies:** Story 5.1 (Admin inventory G2/G3, technical inventory G2); the Folders inventory 1.0.0 classes V01, V02, V04, V05, R01, R02 and G6, raised by Hexalith.Folders on 2026-11-10 (`sprint-change-proposal-2026-11-10.md` at Folders `4af40367`, Section 5, R1); the Epic 5 entry gate (MR10).

**B. Two new ACs,** inserted directly after the first AC (the one that begins "**Given** the gap classes recorded by the EventStore Admin 1.0.1…"):

```markdown
**Given** the four Folders classes raised on 2026-11-10 against inventory 1.0.0: content above the inclusive 262144-byte inline boundary, up to the inclusive 1048576-byte per-file maximum, that requires out-of-band staging and `PutFileStream` (V04, V05); the R01 `audit-trail` and R02 `folder-tree` MCP resources; provider egress before external effects (G6); and per-operation freshness (V01) with paging and filter inputs (V02) mapped onto the Query envelope,
**When** the decision is adopted,
**Then** each of the four classes has exactly one outcome from the list above, within the binding limits: McpCli never calls a Module's REST or Dapr API (PRD §8.3), paging stays envelope-only (AD-20), and a resource, stream, freshness argument or filter argument is admitted only with the PRD change the next criterion requires,
**And** the decision records that inline content up to 262144 bytes is an ordinary decorated Command Payload that needs no new class, and for each class it names the Folders inventory rows the class governs and the positive and negative evidence that the Folders parity proof collects.

**Given** a Folders class whose outcome is continued deferral,
**When** the decision records it,
**Then** it names the gap and its owning role, and every row the class governs stays `defer`,
**And** those rows keep the Folders retirement gate (Folders node EXT-MCPCLI-FOLDERS-RETIREMENT-GATE) closed until the class is decided or the Folders owner withdraws them; McpCli gains no legacy fallback and no module-specific path.
```

**Rationale:**

- The four classes are now named explicitly. The ACs restate existing limits instead of choosing the outcomes.
- The deferral clause matches Folders' own rule (its E4 and Story 5.9): a class McpCli cannot carry blocks the retirement gate and never falls back to a legacy binary.
- G6's Folders side stays with Hexalith.Folders Story 5.10.
- There is no forward reference to Story 6.2.

### P3: Story 5.8 consumes Folders Story 5.12, and Story 5.11 is decoupled from it (R2, Option A)

**A. Story 5.8, "I want" line.**

Before: `I want the Folders inventory re-pinned to current source and amended with the Story 5.2 outcomes and an explicit owner approval,`

After: `I want the Folders inventory re-pinned to current source and amended with the Story 5.2 outcomes, the Folders owner's eligibility decisions and named decorated types, and an explicit owner approval,`

**B. Story 5.8 Dependencies.**

Before: `**Dependencies:** Story 5.2.`

After: ``**Dependencies:** Story 5.2; Hexalith.Folders Story 5.12 (cross-repository prerequisite): the owner-recorded eligibility decision for each candidate, the decorated types merged on Folders `main`, and the accepted behavior losses.``

**C. Story 5.8 AC1, When line.**

Before: `**When** it is re-pinned to its current root-declared reference,`

After: `**When** it is re-pinned to its current root-declared reference at a Folders revision that contains the Hexalith.Folders Story 5.12 types,`

**D. Story 5.8 AC2, replaced.**

Before:

```markdown
**Given** the Story 5.2 outcomes and the 48 roadmap candidates C01–C13 and Q01–Q35,
**When** rows are re-dispositioned,
**Then** each becomes `replace` with decorated contract type, exact Gateway route, and eligibility, `withdraw` with owner rationale, or `defer` with a named gap,
**And** `include` appears only with `replace`, and a roadmap candidate counts as a replacement only once its decorated contract is named.
```

After:

```markdown
**Given** the Story 5.2 outcomes, the 48 roadmap candidates C01–C13 and Q01–Q35, and Hexalith.Folders Story 5.12's eligibility record,
**When** rows are re-dispositioned,
**Then** each eligible candidate becomes `replace` with its decorated CLR type as merged at the re-pin, the explicit `Hexalith.Folders.Commands.*` wire name for a Command, its exact Gateway route, and its eligibility, and each other candidate becomes `withdraw` with owner rationale or `defer` with a named gap,
**And** `include` appears only with `replace`, and a candidate counts as `replace` only once its decorated type exists in Folders source at the re-pin; a type named only in a plan or a draft does not count.
```

**E. Story 5.8, three new ACs,** inserted after AC3 (the identifier AC that begins "**Given** Folders legacy lowercase identifiers"). The second AC includes the correction approved with P4.

```markdown
**Given** the behavior losses the Folders owner accepted through Hexalith.Folders Story 5.12, which are V04 local-file input (`--file` path and stdin), V07 `--allow-auto-key`, V09 credential precedence, and the R01 and R02 resources under the Story 5.2 resource outcome,
**When** the amendment records them,
**Then** each loss is an owner-approved variant change that names its rationale, the replacement experience, and the rows it affects, and the rest of V09 (legacy exit codes 64–77 and human output) is either accepted the same way or kept as a named gap,
**And** a loss the owner has not accepted keeps its variant and rows `defer`.

**Given** gaps G1–G6,
**When** the amendment is produced,
**Then** each names its owning Hexalith.Folders story (G1: 5.12; G2 and G3: 5.13; G4 and G5: 5.14; G6: 5.10) and its status at the re-pin,
**And** an open gap does not prevent `replace`, which records intended scope (migration plan "Approval limits"); G1–G5 remain enrollment prerequisites for the rows they govern, and G6 remains a retirement prerequisite, because Hexalith.Folders Story 5.10 proves it through the enrolled McpCli.

**Given** Story 5.11 has already published a plan version that indexes Folders 1.0.0,
**When** this amendment is approved,
**Then** a new AI.Tools `plan_version` indexes it with a moved `inventory_revision` (MR7),
**And** otherwise Story 5.11 indexes it.
```

Story 5.8 ACs 3 (identifiers), 4 (labels) and 5 (owner approval; enrolls nothing) are unchanged.

**F. Story 5.11 Dependencies.**

Before: `**Dependencies:** Stories 5.2–5.10.`

After: `**Dependencies:** Stories 5.2–5.7, 5.9 and 5.10; Story 5.8 when it is done (it waits on Hexalith.Folders Story 5.12).`

**G. Story 5.11 AC1, Then line.**

Before: ``**Then** it is published under a new `plan_version` with a moved `inventory_revision`, indexes the Story 5.1 inventories and every amended inventory, and records `Parties.Mcp` as retired or states why SM-3 slipped,``

After: ``**Then** it is published under a new `plan_version` with a moved `inventory_revision`, indexes the Story 5.1 inventories and every amended inventory, keeps Folders 1.0.0 indexed with its pending amendment named when Story 5.8 is not yet done, and records `Parties.Mcp` as retired or states why SM-3 slipped,``

**Rationale:**

- R2 is met, and "counts only once named" now means merged source, not a plan.
- The map from each gap to its owning Folders story makes ownership checkable.
- V09's exit codes and human output cannot disappear silently.
- The Parties record in 5.11 stays independent of Folders. The new plan clause uses the 2026-11-08 "whichever finishes first" pattern.
- The G6 wording removes a cycle: Folders 5.10 follows EXT-MCPCLI-FOLDERS-ENROLLMENT.

### P4: New Story 6.1, Enroll the Folders Contracts Release (R3)

```markdown
### Story 6.1: Enroll the Folders Contracts Release

As the Folders owner,
I want McpCli to enroll the exact decorated Folders Contracts release named by the approved inventory, with one approved vector for each included operation,
So that every included Folders operation works through both McpCli heads with no Folders code in McpCli.

**Requirements:** FR5, FR16, FR18, FR20, FR21; MR3, MR4, MR5, MR11. **Dependencies:** Stories 5.2 and 5.8; Hexalith.Folders Stories 5.12, 5.13 and 5.14 done, with the 5.12 types in a published `Hexalith.Folders.Contracts` version; a published, server-code-free Folders composition helper (cross-repository prerequisites). Hexalith.Folders Stories 5.8–5.10 follow this story.

**Acceptance Criteria:**

**Given** the approved Story 5.8 Folders inventory and a published `Hexalith.Folders.Contracts` version that contains every named type,
**When** McpCli enrolls it,
**Then** the versionless `PackageReference` marked `HexalithContracts="true"`, its exact version under `modules` in `tools/dependency-policy.json`, `tools/inventory-coverage/v1/folders-approved.json`, the vectors with an `approval.json` binding the artifact, inventory and vector hashes, and the companion live plans change together under the README enrollment rules,
**And** the AD-15 package and closure gate passes with `Hexalith.McpCli.Abstractions` as the only identity Folders adds, and the AD-21 gate finds every `replace`/`include` row exactly once in `list_operations folders` with a matching contract type and an approved `withdraw` or `defer` for every excluded row.

**Given** every included operation,
**When** its vector is approved,
**Then** it has exactly one execution vector, and `check_enrolled.py` shows equal canonical documents and captured Gateway requests from both heads against the reset loopback Gateway,
**And** the captured requests carry canonical uppercase ULID message, correlation and idempotency identifiers, the explicit `Hexalith.Folders.Commands.*` wire type for each Command, domain `folders`, and task and workspace context only in Payload properties, `actorProperty` or allowed Envelope extensions (MR4).

**Given** Folders' identifier kind, key admission and metadata-only results,
**When** the enrollment change is reviewed,
**Then** `src/` gains no Folders name, module-specific error mapping, content filter, validator change or new production dependency, and the `tools/live-topology/` runners stay generic,
**And** any legacy format the contract cannot accept stays as the approved inventory records it (SM-1).

**Given** the blocking live lane and AD-15's test-composition rule,
**When** the new vectors run,
**Then** the test AppHost composes the Folders domain service, and any provider double that G6-governed operations need, only through a published, server-code-free composition helper pinned exactly under `testPackages`, never a Folders source project, and each live Command is submitted once with its persisted semantic check,
**And** if no such helper is published, enrollment stops and names the missing helper as an upstream prerequisite.

**Given** an operator moving from `Hexalith.Folders.Cli` or `Hexalith.Folders.Mcp`,
**When** the README documents the Folders setup,
**Then** McpCli never reads `~/.hexalith/credentials.json`, `HEXALITH_TOKEN`, `HEXALITH_TENANT` or `HEXALITH_FOLDERS_AUTH_TOKENFILE`, and each Profile binds one Gateway URL, token and tenant,
**And** the README documents the manual move and the V04, V07 and V09 changes recorded in the approved inventory.

**Given** the enrollment passes every gate,
**When** the owner dispatches the release,
**Then** the paired packages are published at one version from a green source SHA through the AD-17 paired path, and the release notes list the enrolled Folders operations without claiming any Folders retirement,
**And** while `epic-4-retro-item-6-bind-release-acceptance` is open, the release waits for it to close or for a recorded owner decision; the Epic 5 release precondition is unchanged.

**Given** the published release,
**When** its evidence is committed,
**Then** the evidence passes the shared redactor and secret scan and binds the McpCli version, the Folders Contracts version, the Catalog digest, the inventory, the vectors and the live plans by hash,
**And** it is the McpCli evidence for the Folders node EXT-MCPCLI-FOLDERS-ENROLLMENT, which the Folders owner accepts in the Folders manifest.
```

**Rationale:**

- The enrollment rule matches Story 5.3's. The release and the AD-21 set/type match are what the Folders node adds.
- The composition AC deals with AD-21's extra-operation rule up front.
- The genericity AC is SM-1.
- McpCli reads only `MCPCLI_HOME` and `EVENTSTORE_*`, so the legacy `HEXALITH_*` names stay unread.
- There is no cycle: Folders 5.8–5.10 follow this story.

### P5: New Story 6.2, Prove Folders Shared-Head Parity and Safety (R3)

```markdown
### Story 6.2: Prove Folders Shared-Head Parity and Safety

As the Folders release owner,
I want positive, negative and rollback evidence that McpCli covers every Folders legacy tool, resource, CLI leaf and variant on the selected environment,
So that Folders can retire its CLI and MCP server without breaking supported access or weakening authorization.

**Requirements:** FR20, FR21; NFR4, NFR5, NFR7; MR2, MR3, MR5, MR6, MR10, MR11. **Dependencies:** Story 6.1; Hexalith.Folders Stories 5.8–5.11 done. Their McpCli-path evidence, including the G6 proof in 5.10, is the Folders-side behavior oracle.

**Acceptance Criteria:**

**Given** the owner-named selected environment and the approved Folders vectors,
**When** the evidence runs,
**Then** every Folders `replace` row succeeds through the CLI head against that environment with its persisted semantic check, and both heads produce equal canonical documents and captured requests against the reset loopback Gateway,
**And** live MCP-head execution is included, or the owner re-accepts and records the CLI-only live-lane deviation for this retirement.

**Given** V01–V10 and the losses accepted in the approved inventory,
**When** the evidence is reviewed,
**Then** each variant is preserved or matches an owner-approved change recorded in the inventory. This includes freshness and paging under the Story 5.2 outcome, the inclusive 262144-byte inline boundary and the staged-content outcome above it, caller-key replay and changed-input conflict, and task and workspace context,
**And** each variant row cites a McpCli test, a loopback or live receipt, or a Folders upstream test at the enrolled revision; a matching operation name proves nothing, and an unrecorded behavior difference blocks retirement.

**Given** authorized and unauthorized reads, including file-range reads, and failing writes,
**When** their results and errors leave either head,
**Then** no content bytes, inline content, stream descriptor, secret or unauthorized path appears in stdout, stderr, MCP `Content` or `StructuredContent` (V06, G5),
**And** McpCli adds no content filter; a leak is a Folders defect that blocks retirement.

**Given** G2 and the REST-equivalent safe denials of Hexalith.Folders Story 5.13,
**When** negative cases run,
**Then** each of these fails closed with the documented error document and no mutation, proven by an authorized persisted end-state read: missing or invalid credentials, an unauthorized principal, a revoked ACL entry, cross-tenant reads and writes, a forged Payload tenant or actor, a task or workspace mismatch, a disallowed tenant override, reserved public `system`, and non-ASCII look-alike tenant input,
**And** while `epic-4-retro-item-9-ascii-tenant-input` is open, the owner records acceptance of the F7 limitation for Folders, or the story stays blocked.

**Given** every row the approved inventory keeps `withdraw` or `defer`, including the adjacent exclusions N01–N04, and the Admin, UI-only and confirmation-required rows,
**When** McpCli discovery and execution are probed,
**Then** none of them appears in `list_operations` or can be submitted, including with a caller-supplied `confirm: true`,
**And** no parity is claimed from operation-name matching alone.

**Given** the last published `Hexalith.Folders.Cli` and `Hexalith.Folders.Mcp` versions,
**When** rollback is exercised on the selected environment,
**Then** both install and complete an owner-chosen smoke set against that environment, and the evidence records their versions and reinstall commands,
**And** a failed rollback blocks retirement.

**Given** the evidence,
**When** the Folders owner reviews it,
**Then** a versioned, owner-approved Folders inventory amendment records every legacy tool, resource, CLI leaf and variant as `replace` with its passing evidence or as `withdraw` with owner rationale, and prior versions stay byte-identical with hash-chained approvals,
**And** every row still `defer` is named and keeps retirement blocked.

**Given** the evidence set,
**When** it is committed,
**Then** it passes the shared redactor and secret scan and binds by hash the McpCli candidate, the Folders Contracts version, the Catalog digest, the environment, the vectors, the live plans and the amended inventory,
**And** the Folders owner approves it under the single-maintainer model; it is the McpCli evidence for the Folders node EXT-MCPCLI-FOLDERS-RETIREMENT-GATE and claims no retirement.
```

**Rationale:**

- The story mirrors Story 5.4's five ACs.
- The Folders node adds three things: metadata-only output, rollback evidence, and the final inventory that is entirely `replace` with evidence or `withdraw`. Story 5.4's Parties outcome showed why the final amendment must give a binary result.
- The Folders-side behavior oracles come from Folders 5.8–5.11, which avoids duplicated work.
- The Parties acceptance of F7 does not carry over to Folders.

### P6: New Story 6.3, Verify the Folders Legacy Retirement and Update Its Labels (R3)

```markdown
### Story 6.3: Verify the Folders Legacy Retirement and Update Its Labels

As a platform maintainer,
I want McpCli to verify that Hexalith.Folders removed `Hexalith.Folders.Cli` and `Hexalith.Folders.Mcp` from every publication and routing point, and that their compatibility labels now record the retirement,
So that McpCli is the only supported Folders CLI and MCP path, and no retired binary is mistaken for a supported surface.

**Requirements:** FR21, FR22; MR6, MR8, MR11. **Dependencies:** Story 6.2; Hexalith.Folders Story 5.15 merged and released (cross-repository prerequisite; the deletion happens there, never from this repository).

**Acceptance Criteria:**

**Given** the Folders release from Hexalith.Folders Story 5.15, with the root-declared Folders and Platform references moved to revisions that contain it,
**When** retirement is verified,
**Then** a source search at those gitlinks finds nothing that builds, packs, routes or advertises `Hexalith.Folders.Cli` or `Hexalith.Folders.Mcp`: no project, test project, shared adapter core, `.slnx` entry, NuGet release or trusted-publishing entry, CI reference, container, sample, Platform composition or operator document, and no routing point listed in technical inventory G4,
**And** a surviving surface fails verification and is named by repository, path and detection signal.

**Given** the Folders retirement record,
**When** it is verified,
**Then** the Folders README "Legacy compatibility surfaces" section records the retirement, the last published legacy package versions and the rollback path to them, and both package IDs are deprecated on NuGet with McpCli named as the alternative,
**And** the recorded rollback versions match the ones Story 6.2's rollback evidence exercised.

**Given** the Story 5.5 compatibility labels on the Folders surfaces,
**When** retirement is verified,
**Then** the Story 5.5 label evidence is regenerated so the Folders surfaces read as retired, not as missing labels,
**And** no other module's label or count changes.

**Given** the Story 5.6 census baseline,
**When** the census check runs at the moved gitlinks,
**Then** it reports the removed Folders surfaces as stale baseline entries, and a versioned census amendment retires them,
**And** if Story 5.6 is not yet done, the amendment is still produced, and Story 5.6 adopts it as its baseline.

**Given** SM-3 and MR8,
**When** the retirement is recorded,
**Then** the evidence states the retirement date and whether it satisfies SM-3 (deadline 2027-02-05), given the Parties retirement status on that date,
**And** it claims nothing about any other surface.

**Given** the verification evidence,
**When** it is committed,
**Then** it passes the shared redactor and secret scan and binds the Folders release revision, the moved gitlinks and the search results by hash,
**And** this repository changes no Folders file: only gitlinks, evidence and census data change here.
```

**Rationale:**

- The story mirrors Story 5.5, but here the deletion belongs to Folders 5.15 and McpCli only verifies it (R3).
- The search scope copies Folders 5.15's removal list and adds Platform and technical inventory G4.
- The census AC follows Story 5.6's versioned-amendment rule and stays independent of 5.6's timing.
- Gitlink moves are pin bumps; nothing inside `references/` is edited.

### P7: New Story 6.4, Record the Folders Retirement in the Migration Plan (R4)

```markdown
### Story 6.4: Record the Folders Retirement in the Migration Plan

As a product owner,
I want the Hexalith.AI.Tools migration plan to record the Folders retirement and index the final Folders inventory,
So that the authoritative plan no longer lists `Hexalith.Folders.Cli` and `Hexalith.Folders.Mcp` as retained compatibility implementations.

**Requirements:** FR21, FR22; MR7, MR8. **Dependencies:** Story 6.3. The plan change merges upstream in Hexalith.AI.Tools; this repository only moves its gitlink.

**Acceptance Criteria:**

**Given** Story 6.3's verified retirement and Story 6.2's approved final Folders inventory,
**When** the Hexalith.AI.Tools migration plan is updated,
**Then** it is published under a new `plan_version` that follows the latest published one, with a moved `inventory_revision`; it indexes the final Folders inventory and records `Hexalith.Folders.Mcp` and `Hexalith.Folders.Cli` as retired, naming McpCli as the replacement, the Folders release and the rollback versions,
**And** every other plan entry is unchanged, whichever story published the previous version.

**Given** the merged plan revision,
**When** this repository takes it,
**Then** the root-declared `references/Hexalith.AI.Tools` reference contains that revision and `scripts/check-agent-instructions-sync.sh` passes,
**And** the evidence records the integrated revision, its containment and the exact check result.

**Given** any McpCli release published after the retirement,
**When** its release notes are written,
**Then** they list Folders as retired with its rollback path and still list each remaining compatibility binary with its removal gate,
**And** they do not claim that ecosystem migration is finished.

**Given** every Epic 6 deferral recorded in `deferred-work.md`,
**When** the epic closes,
**Then** each has a recorded disposition: resolved, already tracked, or accepted.
```

**Rationale:**

- This story is the successor that R4 allows. It has no dependency on Story 5.11, which will almost certainly close first, so the two can complete in either order (MR7).
- Its ACs reuse Story 5.11's structure and the plan's integrated-revision proof.

### P8: Tracker and frontmatter bookkeeping

**A. `_bmad-output/implementation-artifacts/sprint-status.yaml`,** edited line by line. `sprint_plan.py generate` is not used because it drops comments. The concurrent Story 5.5 edit already in the working tree is preserved.

1. `last_updated` is set to the time of application.
2. The Story 5.8 line gets a comment:
   - Before: `  5-8-refresh-and-re-disposition-the-folders-inventory: backlog`
   - After: `  5-8-refresh-and-re-disposition-the-folders-inventory: backlog # 2026-11-10: waits on Hexalith.Folders Story 5.12 (sprint-change-proposal-2026-11-10).`
3. After `  epic-5-retrospective: optional`, a blank line and then this block:

```yaml
  epic-6: backlog
  6-1-enroll-the-folders-contracts-release: backlog # Waits on McpCli 5.2 and 5.8, Hexalith.Folders 5.12–5.14, and a published Folders composition helper; evidence for EXT-MCPCLI-FOLDERS-ENROLLMENT.
  6-2-prove-folders-shared-head-parity-and-safety: backlog # Waits on 6.1 and Hexalith.Folders 5.8–5.11; evidence for EXT-MCPCLI-FOLDERS-RETIREMENT-GATE.
  6-3-verify-the-folders-legacy-retirement-and-update-its-labels: backlog # Waits on 6.2 and Hexalith.Folders 5.15.
  6-4-record-the-folders-retirement-in-the-migration-plan: backlog
  epic-6-retrospective: optional
```

Each key comes from its story title through `sprint_plan.py`'s 60-character `_slug` rule.

**B. `epics.md` frontmatter:** only the P1-D `changeProposals` entry changes. The top-level `approvedStories` list and the 2026-11-08 `refinement` block stay as they are; this proposal records the approval of Stories 6.1–6.4, following the 2026-11-08 precedent.

## 5. Implementation handoff

**Scope: Moderate.** The backlog is reorganized, a new epic is added, two stories are amended, one dependency is decoupled, and cross-repository prerequisites are named. No code, CI or tool changes in this pass.

| Role | Responsibility |
| --- | --- |
| Developer agent (this session) | Apply P1–P8 exactly. Run the validation below. Leave every edit uncommitted. |
| Product owner (Jerome, single-maintainer model) | Commit when satisfied. Decide when Story 5.2 starts; it is unblocked now. |
| Story 5.2 author | Cover the four Folders classes under P2, including any PRD change an admitted class needs. |
| Folders owner (cross-repository) | Deliver Hexalith.Folders Stories 5.12–5.14 before Story 6.1, Stories 5.8–5.11 before Story 6.2, and Story 5.15 before Story 6.3. Apply the follow-ups below in the Folders repository. |

**Cross-repository prerequisites:**

| McpCli story | Hexalith.Folders prerequisite |
| --- | --- |
| 5.8 | Story 5.12: eligibility record, decorated types merged on `main`, accepted losses |
| 6.1 | Stories 5.12, 5.13 and 5.14 done; 5.12 types in a published `Hexalith.Folders.Contracts`; a published, server-code-free composition helper with a provider double for the G6 operations |
| 6.2 | Stories 5.8–5.11 done (Folders-side oracles, including G6 in 5.10) |
| 6.3 | Story 5.15 merged and released |

**Follow-ups for the Folders repository** (not applied here):

1. **Name the McpCli source work in the Folders manifest.** EXT-MCPCLI-FOLDERS-ENROLLMENT maps to McpCli 5.2, 5.8 and 6.1. EXT-MCPCLI-FOLDERS-RETIREMENT-GATE maps to McpCli 6.2. McpCli 6.3 and 6.4 follow Folders 5.15.
2. **Assign an owning story for the published, server-code-free Folders composition helper.** It must include a provider double for the G6 operations; no Folders story owns it yet.
3. **G6 placement.** G6 is proven after enrollment, by Folders 5.10. It is a retirement prerequisite, not an enrollment prerequisite.

**Validation for this pass:**

1. `epics.md` changes only in the approved places. FR1–FR22 and NFR1–NFR8 stay byte-identical, apart from the two appended FR-map clauses. The Parties Stories 5.3–5.5, the Epic 5 Entry and gate decision, and every other story stay byte-identical.
2. `sprint-status.yaml` parses as YAML and passes `uv run .claude/skills/bmad-sprint-planning/scripts/sprint_plan.py validate`. `git diff` shows only the P8 changes, and every comment survives.
3. SHA-256 before and after is recorded for both files. Before: `epics.md` `8c467107f1c414241e6f7332ec184de073c3bbfa23c96f9faf2934b680466e60`; `sprint-status.yaml` `56ecc0f84f6eda12a458c29a7efd9aef5121e430c6407edba5ad703b7ba052fb`.

**Success criteria:**

- Every McpCli-side requirement of the two Folders nodes has exactly one owning McpCli story. EXT-MCPCLI-FOLDERS-ENROLLMENT is covered by 5.2, 5.8 and 6.1, and EXT-MCPCLI-FOLDERS-RETIREMENT-GATE by 6.2. 6.3 and 6.4 close the retirement.
- No McpCli story waits on a Folders story that itself waits on that McpCli story.
- The Parties retirement record (5.11) and Epic 5's Parties track never wait on Folders.
- McpCli stays generic: no Folders code, adapter, error mapping, content filter or production dependency, and no edit under `references/`.

## Checklist record

| Item | Status | Note |
| --- | --- | --- |
| 1.1 Trigger | [x] | Hexalith.Folders requests R1–R4, 2026-11-10, Folders `4af40367`. |
| 1.2 Core problem | [x] | New requirement from a dependent module (D1/D2). |
| 1.3 Evidence | [x] | Section 1. |
| 2.1 Current epic | [!] | Epic 5: 5.2 and 5.8 amended, 5.11 decoupled (P2, P3). |
| 2.2 Epic-level changes | [!] | New Epic 6 (P1). |
| 2.3 Remaining epics | [x] | Epics 1–4 unaffected. |
| 2.4 Obsolete or new epics | [x] | None obsolete; Epic 6 added. |
| 2.5 Order and priority | [!] | 5.8 waits on Folders 5.12; 5.11 no longer waits on 5.8; G6 ordering corrected. |
| 3.1 PRD | [x] | No change. |
| 3.2 Architecture | [x] | No change now; 5.2 produces its own decision. |
| 3.3 UX | [N/A] | No UX artifact. |
| 3.4 Other artifacts | [!] | Sprint status and frontmatter (P8); tools and CI change later in 6.1. |
| 4.1 Direct adjustment | Viable | Medium effort, medium risk. |
| 4.2 Rollback | Not viable | Nothing completed is undone. |
| 4.3 MVP review | Not needed | McpCli v1 shipped; Folders is post-v1. |
| 4.4 Selected path | [x] | Direct adjustment. |
| 5.1–5.5 Proposal components | [x] | Sections 1–5. |
| 6.1–6.2 Review | [x] | P1–P8 approved individually; the P3 correction was approved with P4. |
| 6.3 Final approval | [x] | Product owner, 2026-11-10: "yes". |
| 6.4 sprint-status update | [x] | P8 applied and validated (Section 6). |
| 6.5 Handoff | [x] | Section 5. |

## 6. Application record (2026-11-10)

All edits are in the working tree and uncommitted. The Story 5.5 edits that another session had left uncommitted in `sprint-status.yaml`, `spec-5-5-…md`, `deferred-work.md` and `evidence/story-5-5/` are preserved untouched.

| Artifact | SHA-256 before | SHA-256 after |
| --- | --- | --- |
| `_bmad-output/planning-artifacts/epics.md` | `8c467107f1c414241e6f7332ec184de073c3bbfa23c96f9faf2934b680466e60` | `4eb120342ead6c283a0a5bf70158ec422867c8e3fd36bac30ca9f8c7febe2210` |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `56ecc0f84f6eda12a458c29a7efd9aef5121e430c6407edba5ad703b7ba052fb` | `714bf461c12768379006f3493993c4c0dcef059534bea5e18813789f31e946a2` |

**How it was applied.** The approved blocks were taken verbatim from this document by a one-off script, and every replacement was asserted to match exactly once. The Story 5.2, 5.8 and 5.11 edits were matched only inside their own story sections.

**Validation:**

- **`epics.md` scope.** Only the frontmatter, the FR20/FR21 coverage-map lines, Stories 5.2, 5.8 and 5.11, and the new Epic 6 Epic List entry, section and Stories 6.1–6.4 changed.
  - All 52 `FR`/`NFR` lines are present, and only the two coverage-map lines differ.
  - Every other story and epic section is byte-identical with HEAD `24ae42e`. This includes Stories 5.3–5.5, the Epic 5 Entry and the gate decision.
- **Sprint-status validation.** `sprint_plan.py validate` reports `valid: true` with no problems, and the YAML parses.
- **Tracker sync.** `sprint_plan.py generate --dry-run`, run on a copy, reports `in_sync: true`: 6 epics, 55 stories, no new entries, no orphans. Its four warnings are pre-existing non-story headings.
- **Tracker diff.** Against the working tree, `sprint-status.yaml` differs only in `last_updated`, the Story 5.8 comment and the Epic 6 block, and every comment survives.
- **Whitespace.** `git diff --check` is clean for both files.
