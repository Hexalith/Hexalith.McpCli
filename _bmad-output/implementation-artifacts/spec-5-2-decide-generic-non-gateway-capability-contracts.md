---
title: '5.2 Decide generic non-gateway capability contracts'
type: 'chore'
created: '2026-11-12'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'f4bb819925d4fac5fa5afd262341692296a52042'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** About 525 approved inventory rows across eight inventories (EventStore Admin 1.0.1, technical-tools 1.0.2, and the Folders, Projects, FrontComposer, ChatBot, Memories and Parties inventories) carry capabilities that v1 cannot migrate as decorated Gateway Commands/Queries. No decision assigns them a generic path, a withdrawal or a named retention. Stories 5.7–5.10 and Epic 6 cannot re-disposition any row until one exists.

**Approach:** Adopt McpCli **AD-23**. It partitions every inventory row into exactly one capability class and gives each class exactly one outcome: decorated Gateway contract, named generic authenticated transport, exempt local tooling, confidential UI only, withdrawal, or continued deferral with a named gap. Use only outcomes inside v1, so that no Platform AD or PRD change is needed. Bind it with a machine-checkable class map, a stdlib verifier and exact-byte owner approval. Publish the exempt-tooling amendment upstream in Hexalith.AI.Tools.

## Boundaries & Constraints

**Always:**
- Keep the existing limits:
  - Platform AD-11/AD-14: McpCli is one public `agent` surface; UI-only and confirmation-required operations are denied, and `confirm: true` proves nothing.
  - PRD §8.2/§8.3: no MCP resources, prompts, event-stream reads, retries or plug-ins, and McpCli never calls a Module REST or Dapr API.
  - AD-20: paging stays Envelope-only.
  - MR4: task and actor context travel only as Payload properties, through `actorProperty`, or in allowed extensions.
- One class per row. An operation row takes the class of its primary capability, and a variant row takes the class of the variant it records. Any UI-only, confirmation-required or destructive row takes its restricted class, whose outcome is confidential UI, exempt (owner-held) local tooling, or withdrawal.
- Inline content up to 262144 bytes is an ordinary decorated Command Payload and needs no new class.
- Each admitted class states its versioned declaration, discovery, execution, error documents, authorization class, audit and conformance evidence, with no module-specific runtime branch.
- Each deferral names its gap and the owning role.
- Each restricted class and each Folders class names the positive and negative evidence a later parity proof collects.
- Record how each outcome maps to the `replace`/`withdraw`/`defer` dispositions that Stories 5.7–5.10 apply. `replace` still requires the decorated type to exist at the pin, and each Admin `replace` lists the G4 fixes as preconditions.
- Bind the decision, the class map and every input inventory by SHA-256. AD-23 is `ADOPTED` only after the owner approves the exact bytes. The approval names the roles it covers under the single-maintainer model.

**Never:**
- Change production `src/`, `tests/`, dependencies, CI, `references/`, the census baseline or any inventory file.
- Re-disposition a row on a draft decision.
- Admit a capability beyond v1 decorated Commands/Queries.
- Claim parity from name matching.
- Grant execution, enrollment or retirement authority.
- Push upstream without the owner's explicit approval.

## Owner Decisions (2026-11-12)

1. **Remote EventStore Admin rows** (the four Story 5.1 classes: infrastructure administration, operator diagnostics, stream/state reads, tenant reads; 46 rows): **confidential UI only**. This follows Platform AD-11's interim rule. The Admin heads retire only with UI coverage evidence.
2. **Lifecycle/status observation:** **withdraw**. Agents observe effects through the Gateway's accepted status and the module's decorated Queries. The synthetic `timed_out`/`needs_review` states are an accepted loss.
3. **Documentation resources:** **withdraw**. Documentation ships with the packages, README and AI.Tools.
4. **Streams, staged files, imports/exports and event streams** (including Folders V04/V05): **continued deferral**. The gap is a generic out-of-band staging/stream transport that needs a Platform AD and a PRD change. The owning role is the McpCli product/architecture owner. The Folders rows this class governs stay `defer` and keep EXT-MCPCLI-FOLDERS-RETIREMENT-GATE closed until the class is decided or Folders withdraws them.
5. **FrontComposer compiler CLI (FC01/FC02, PS03):** **exempt local tooling**. The AI.Tools rule and plan 1.2.0 amendment is committed upstream in this story and pushed only after explicit owner approval. Until it merges, the surface stays frozen in the census.
6. **Memories `MigrateEmbeddingVectors` (PS14):** **exempt local tooling**, owner-held, named in the same amendment. It is never placed on the agent surface. Story 5.10 still inventories its modes.
7. **Module erasure and key rotation:** **confidential UI only**.
8. **Spec size:** the owner kept the full spec (about 3,800 tokens).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Complete map | Map covers every row ID of the eight hash-bound inventories exactly once | Verifier exits 0 and prints per-inventory counts | N/A |
| Missing or duplicate row | A row ID absent from the map, or present twice | Nonzero exit naming the inventory and the ID | Damaged-input test |
| Unknown row or stale hash | A mapped ID not in the inventory, or an inventory hash mismatch | Nonzero exit naming it | Damaged-input test |
| Bad outcome | A class with zero, two, or an unlisted outcome | Nonzero exit | Damaged-input test |
| Restricted leak | A destructive, confirmation-required or UI-only row mapped to an admitted class | Nonzero exit naming the row | Damaged-input test |
| Deferral without gap | A deferred class with no gap or no owner role | Nonzero exit | Damaged-input test |

</frozen-after-approval>

## Code Map

- **Inputs (read, never edit):**
  - `_bmad-output/implementation-artifacts/eventstore-admin-migration-inventory-v1.md` (1.0.1, `7e1beb2f…`)
  - `technical-tools-migration-inventory-v1.md` (1.0.2, `8cca31f2…`)
  - `folders-` (1.0.0), `projects-`, `frontcomposer-`, `chatbot-` and `memories-` (1.0.0; the last four are session-scope approval only), and `parties-migration-inventory-v1.md` (the file is 1.2.0, pending; 1.1.0 is the latest approved version).
  - The row tables are the Markdown tables whose first cell is an ID such as `AC01`, `G3` or `V05`. ChatBot and Memories head their gap tables `Gate` and `Gap`, and Parties heads its C table `ID / legacy rows`. Folders C/Q candidate rows are not legacy operations.
- **`evidence/story-5-1/verification.md:1341-1352`:** the approved Admin class partition (eight classes). Reuse it verbatim as the Admin classes; the 5.1 gate checks it at `:1066-1076`. Also `:1353-1450`: the technical classes and the behavior inputs (FV01 limits, FH02 admission, AV04 disclosure).
- **`_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md`:**
  - Entry format `### AD-N — Title [ADOPTED date]` with Binds/Prevents/Rule/Provenance/Evidence (AD-22 at `:191-199`).
  - Frontmatter `updated:`/`sources` at `:11-14`.
  - Design Paradigm at `:34`.
- **Platform rules:** `references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md:185` (AD-11, new surfaces) and `:206-216` (AD-14). The pin is `38402bc7`.
- **AI.Tools:**
  - The local clone `/home/administrator/projects/hexalith/aitools` is clean on `main` at `8a3885d`, the same commit as the gitlink.
  - Exemption sentence: `hexalith-llm-instructions.md:78-80`.
  - Plan: `hexalith-mcpcli-migration-instructions.md:2-4` (`plan_version 1.1.0`) and `:16-18`; versioning rule at `:47-48`.
  - Upstream work follows Story 5.5's practice: a scratchpad worktree from `origin/main`, a commitlint-validated `docs` commit on a branch, and a push only on approval.
- **Folders positions** (`references/Hexalith.Folders` at `6a8cf4f9`, `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10.md`):
  - `:177` and `:213`: staging per 5.2, otherwise `defer`.
  - `:196`: G6 authorized module-side.
  - `:294-296`: a single freshness value per Query.
- **Do not touch:**
  - `tools/proprietary-surfaces/v1/baseline.json`, which binds technical 1.0.2.
  - `tests/Hexalith.McpCli.Cli.Tests/PartiesRetirementSafetyTests.cs:156`, which parses the Admin AC/AM names.
  - Story 5.1's `approval.json` and verification text.

## Tasks & Acceptance

**Execution:**
- [ ] `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md` -- write the decision. It covers:
  - the class table and its outcomes;
  - the one-class precedence rule;
  - each admitted class's declaration, discovery, execution, errors, authorization, audit and conformance;
  - a Folders section giving, for V04/V05, R01/R02, G6 and V01/V02, the governed rows plus their positive and negative evidence;
  - the treatment and negative evidence for restricted operations;
  - each deferral's gap and owner role;
  - the outcome-to-disposition rule, including the G4 preconditions;
  - an explicit "no Platform AD or PRD change required" statement.

  Its status stays `proposed` until approved -- this is the single decision Stories 5.7–5.10 consume.
- [ ] `.../AD-23-capability-class-map.json` -- for each class: `id`, `outcome` and `gap`/`ownerRole`; for each inventory: path, version, SHA-256 and `rows` mapped to class IDs; plus explicit `records` for non-operation rows (AU, AX, FK, PE, PN, candidates C/Q, G rows, and PS rows governed by companion inventories) -- this keeps the map complete and mechanically checkable.
- [ ] `_bmad-output/implementation-artifacts/evidence/story-5-2/verify_class_map.py` and `test_verify_class_map.py` -- a stdlib verifier that has no module names or counts in code, plus one damaged-input test for each matrix row -- the verifier proves the "exactly one class" and restricted-row rules, and each test proves its guard.
- [ ] `.../ARCHITECTURE-SPINE.md` -- add the AD-23 entry with Binds FR-21/FR-22, MR1–MR3 and MR9, and update `updated`/`sources` -- this adopts the decision as a McpCli AD.
- [ ] Upstream AI.Tools worktree -- amend the exemption sentence and the plan to 1.2.0 for each exempted surface, then validate with commitlint -- AC6 requires the amendment; it is pushed only after the owner approves.
- [ ] `evidence/story-5-2/verification.md` and `approval.json` -- record the verifier output, the hashes, the owner's words, the roles covered and the limits -- adoption evidence.
- [ ] `sprint-status.yaml` and this spec -- update the workflow state.

**Acceptance Criteria:**
- Given the approved AD-23, when it is read, then every class has exactly one listed outcome, and every row of the eight bound inventories maps to exactly one class or to an explicit non-operation record.
- Given the restricted rows (AC13, AC20, AC21, AC25, AC28, AM01, AM03, AM06, AM12–AM15, FC02 and the PS14 live/rollback/abort modes), when their treatment is checked, then each is assigned to confidential UI, exempt local tooling or withdrawal, and its negative evidence is named.
- Given the whole change, when it is diffed against the baseline, then `src/`, `tests/`, `tools/`, `references/`, CI and all inventory bytes are unchanged.
- Given an exempt-tooling outcome, when 5.2 completes, then the AI.Tools amendment is committed upstream, or recorded as pending with the surface still frozen in the census.

## Design Notes

**Classes.** A tag in the form D# cites the Owner Decision that set the outcome. Implementation may split or rename classes when a row's primary capability requires it, but it may not change an outcome.

**Decorated Gateway contract (admitted; v1 already defines all seven facets):**
- K01: ordinary module operations awaiting module-side decoration or handlers, including the FH02/H02 manifest families per consumer.
- K02: module-state resource reads (Folders R01/R02, Projects R-data, FH03) become module Queries; the URI and subscription are not preserved.
- K03: freshness, paging and filter inputs (Folders V01/V02). Freshness is fixed per Query or declared as a Payload property, filters are Payload properties, and paging is Envelope-only.
- K04: context, idempotency-key and identifier format. Values are canonical uppercase ULIDs, and the module accepts them (Folders G3).
- K05: provider egress and pre-submit effects, authorized module-side (Folders G6, ChatBot V07/V08).
- K06: module diagnostics. These are exposed only if the owner decorates them.

**Withdrawal:**
- K07: documentation delivery (D3).
- K08: lifecycle/status (D2).
- K15: legacy session context, stubs, local profile/config, completion, wizards and CLI conventions. This includes Admin AM16–AM18, AC22–AC24 and AC25–AC31, Memories S01–S04, L02 and L06, and Projects L12/L13.

**Continued deferral:**
- K09: streams, staging and files (D4).
- K10: forwarded per-user identity and HTTP caller authority (MR9; owner: McpCli product owner).

**Confidential UI only:**
- A1–A4: the four remote Admin classes from Story 5.1 (D1).
- K12: module confirmation-required or destructive operations, including erasure and key rotation (D7).

**Exempt local tooling:**
- K13: the compiler CLI (D5).
- K14: PS14 (D6).

**Outcome-to-disposition rule.** Decorated contract → `replace` only when the decorated type exists at the pin, otherwise `defer` naming the module gap. Confidential UI → `withdraw`; the head retires only with UI coverage evidence. Exempt → `withdraw` from migration scope; the surface is retained and not counted as retired. Withdrawal → `withdraw` with the accepted loss. Deferral → `defer` with the gap.

## Verification

**Commands:**
- `python3 -I _bmad-output/implementation-artifacts/evidence/story-5-2/verify_class_map.py` -- expected: exit 0, with per-inventory counts.
- `python3 -I -m unittest discover -v -s _bmad-output/implementation-artifacts/evidence/story-5-2 -p 'test_*.py'` -- expected: every damaged input is rejected.
- `git diff --stat f4bb819925d4fac5fa5afd262341692296a52042 -- src tests tools references .github _bmad-output/implementation-artifacts/*-migration-inventory-v1.md` -- expected: empty.
- `git diff --check` -- expected: clean.

## Implementation Notes

- 2026-11-12: The user approved the specification with "approve and stop". The intent and Owner Decisions D1–D8 are frozen. Implementation has not started. This approves the spec only: AD-23 still needs exact-byte owner approval before adoption, and the AI.Tools push needs its own explicit approval.

## Spec Change Log

## Review Triage Log
