# PRD Quality Review — Hexalith.McpCli

Reviewed the complete current `prd.md` and `addendum.md`, both updated 2026-09-22, against `.agents/skills/bmad-prd/assets/prd-validation-checklist.md`. Calibration: internal developer tooling, with architecture and implementation stories downstream. Consulted the recent decision log; the earlier Poor report predates substantial amendments and is not evidence of current defects.

## Overall verdict

The PRD is a usable basis for architecture and story preparation: its catalog thesis, two-head execution boundary, security decisions, and release prerequisites are explicit and mostly testable. Remaining weaknesses are bounded contract ambiguities, especially identifier schema typing, settings applicability, and the Parties command subset; these need clarification in their owning stories, but do not justify restarting discovery or blocking all work. No critical or high finding is established by this rubric review; the explicitly timed upstream decisions remain gates for their named phases.

## Decision-readiness — adequate

Sections 1, 4, and 8 state consequential choices directly: a single generic surface, no hosted infrastructure in v1, token-owner identity for dev/test, and no release-scope fallback if Tenants or Parties slips. Addendum §A records what was sacrificed by rejecting permanent coexistence, shared profile storage, and unconditional per-call tenant precedence.

The five open questions in §10.2 have owner roles and revisit conditions. OQ-1 belongs to HTTP; OQ-5 to Parties decoration; OQ-8 to publication scheduling; OQ-9 to FR-17. Their presence in a final PRD does not imply all catalog or fixture work is blocked. The current architecture consistency reviewer should determine which §10.1 handoff items still remain; the PRD's historical handoff sentence is not proof they remain unimplemented.

## Substance over theater — strong

The vision describes an actual platform constraint: six legacy packages encode incompatible operation surfaces while module contracts lack runtime descriptions. The proposed catalog, decoration, routing fallback, and migration plan each address that problem. User roles drive concrete decisions: module authors get one decoration dependency, agents get discovery tools, and shell users share the executor.

NFRs predominantly have product-specific consequences: 500 ms catalog startup, 8,000 characters for tool definitions, clean stdio, three-platform support, and reviewable descriptions. The numerical assumptions are disclosed. There is no need to invent market positioning, additional personas, or enterprise SLA sections for this internal tool.

## Strategic coherence — adequate

The central bet—one contract declaration should expose a capability to both agents and scripts—connects §1 to FR-1–FR-20 and to SM-1, SM-2, SM-4, and SM-7. Counter-metrics explicitly prevent apparent progress through new typed tools, dependency creep, or hollow descriptions. Replacement is a longer-term objective; FR-21 makes the migration plan a v1 deliverable and §8.2 correctly places deletions later.

### Findings

- **[low] R5: Folders is called an SM-1 gate, but SM-1 permits any additional module** (§1 line 28; §8.1 lines 466 and 473; §9 line 494) — The status and prerequisite text say Folders “gates SM-1.” SM-1 instead requires Tenants, Parties, every module that became Gateway-ready, and “one further Module”; Projects or another module can satisfy that condition while Folders remains unready. This changes how the three-month success assessment treats a Folders delay. *Fix:* Either make Folders explicitly mandatory in SM-1 or describe it as one candidate for demonstrating extensibility, without calling it a gate.

## Done-ness clarity — adequate

All 22 FRs carry observable consequences, and the strongest ones name refusal behavior, error codes, precedence, or test boundaries rather than adjectives. The startup diagnostic table, executor-enforced read-only guarantee, explicit aggregate handling, and source-precedence fixtures are particularly useful for story acceptance. A few literal statements still allow incompatible implementations.

### Findings

- **[medium] R1: The unmarked identifier rule contradicts schema derivation** (FR-7, `prd.md:231–237`) — FR-7 first derives schema from the operation type, then says an unmarked property ending in `Id` “is a plain string in the Schema,” immediately followed by “the name suffix never types a property.” For an otherwise ordinary numeric or object-valued `ExternalId`, those instructions cannot both hold: forcing a string types by suffix; preserving the CLR representation violates the plain-string sentence. The explicitly recognized ULID type also needs its existing exception preserved. *Fix:* Say an unmarked property retains its normal serializer-derived schema and only receives a lint finding; use “plain string” solely for a property whose declared serialization is already a string. Reconcile the same wording in architecture AD-8 when updating the requirement.

- **[medium] R2: Missing-URL validation has no verb applicability rule** (FR-6 `prd.md:227`; FR-13 `prd.md:298–302`; addendum §E settings table) — FR-6 says `config` and `--version` “always run,” while FR-13 applies settings resolution to every verb and says a missing URL is `configuration_invalid`. Neither scopes URL validation to verbs that submit work or explains whether offline discovery and bootstrap configuration require connection settings. Accepting a global option is not itself the problem; the unconditional missing-value rule is. A conforming implementation could reject the first profile-management command before an operator has configured a URL. *Fix:* State which verbs require a resolved URL, exempt bootstrap/config/version as intended, and decide whether catalog-only discovery works offline. This is an applicability clarification, not evidence that an implementation currently fails.

The shared-head result comparison in FR-20/SM-4 needs equivalent initial state for stateful commands, but “one EventStore” does not forbid restoring fixtures between executions. That is a test-design obligation, not a separate PRD blocker. Likewise, OQ-9 explicitly gates deduplication claims before FR-17 implementation; no unsupported retry guarantee should be inferred now.

## Scope honesty — adequate

Sections 8.2–8.3 clearly exclude the admin plane, identity-server work, executor retries, typed tools, and direct module API execution. HTTP is explicitly the only committed next release. The dependency allowlist and zero-module-specific-code requirement make the scope boundary inspectable. There are nine substantive inline assumptions with matching index entries, and five unresolved OQs; several are low-risk defaults while the dependency-sensitive ones have phase gates. Their count alone is not a reason to withhold architecture work.

### Findings

- **[medium] R3: The v1 Parties command subset remains a tentative scope statement** (§8.1, `prd.md:471`; FR-20) — The requirement says “Publish the agent-facing subset; the erasure and key-rotation Commands are probably not in it.” FR-20 then accepts every operation that happens to be decorated, which cannot establish whether the intended command coverage or exclusions were delivered. OQ-5 assigns the wire-routing decision, but does not explicitly assign this inclusion/exclusion decision or its acceptance inventory. *Fix:* Record an owner-approved included/excluded command inventory before Parties decoration, or add a bounded open item with that owner and revisit condition. Keep it upstream; no module-specific runtime configuration is needed here. This is a gate for defining Parties coverage, not a blocker to building the generic catalog.

## Downstream usability — adequate

The glossary and feature/FR index make extraction straightforward. Stable identifiers are preserved despite FR-18/FR-19 placement. §0 explicitly promotes addendum §E and §G to normative status, which prevents readers from treating the argument and result contracts as optional explanatory examples. The remaining gap is that not all promised machine-consumable outcomes have a defined representation.

### Findings

- **[medium] R4: The normative result documents omit the lint outcome** (FR-4; FR-12; FR-14 `prd.md:315`; addendum §E lint row and §G `addendum.md:258–328`) — `describe --lint` must list three classes of findings and return a result document with exit 1 when any exist. §G specifies the shared `describe_operation` document but supplies no lint field/document or location for those findings. Two CLI implementations could both “list” them while emitting incompatible JSON or mixing non-JSON text into the JSON-default surface. *Fix:* Define the lint result's location and minimum fields in §G, including the empty result case and whether its findings supplement the ordinary describe document. Leave presentation details to the CLI story.

## Shape fit — strong

A capability specification is appropriate for this internal platform tool. Three compact journeys illustrate cross-module execution, discovery, and module onboarding without overwhelming the functional contract. The PRD's length is high, but its recent decision log explicitly accepts keeping testable consequences in the main document; this review does not relitigate that choice. Mechanism detail and deferred-module depth are largely kept in the addendum, and a separate architecture spine exists for implementation decisions.

## Mechanical notes

- Severity totals: **0 critical, 0 high, 4 medium, 1 low**. R1–R5 are the counted findings; the notes below are editorial observations, not additional severity findings.
- The 22 FR definitions are unique; FR-18 and FR-19 are deliberately ordered by feature and explicitly explained. UJ-1–UJ-3, NFR-1–NFR-8, SM-1–SM-7, and SM-C1–SM-C4 are present. Stable OQ numbering is split between open and resolved sections intentionally.
- All nine substantive inline assumption tags round-trip to §11. Literal mentions of the tag in explanatory text are not additional assumptions.
- UJ-2 has an agent session rather than a named human protagonist. That is suitable for this tool's actual consumer role; adding a fictional name solely for the rubric would not improve the document.
- Addendum §D line 171 still says “four v1 Contracts libraries”; the amended PRD has two v1 modules. Update that inherited survey wording or date it explicitly.
- Addendum §G's Parties ULID error example is misleading now that Parties declares `String`; use a synthetic ULID-module example or a String-kind gateway-pattern violation.
- Addendum §G says absent optional fields are omitted, but the gateway-error example uses `retryAfter: null`. Clarify the canonical omitted/null convention when formalizing record schemas.
- No source files or product planning documents were changed by this review. Only this review artifact was written.
