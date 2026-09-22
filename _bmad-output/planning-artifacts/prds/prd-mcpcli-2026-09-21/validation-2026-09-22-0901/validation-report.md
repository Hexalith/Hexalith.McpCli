# Validation Report — Hexalith.McpCli

- **PRD:** `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md`
- **Rubric:** `.agents/skills/bmad-prd/assets/prd-validation-checklist.md`
- **Run at:** 2026-09-22T10:50:12Z
- **Grade:** Fair
- **Findings:** 0 critical, 3 high, 6 medium, 1 low (10 distinct)

## Overall verdict

The PRD is a usable basis for architecture and story preparation: its catalog thesis, two-head execution boundary, security decisions, and release prerequisites are explicit and mostly testable. Remaining weaknesses are bounded contract ambiguities, especially identifier schema typing, settings applicability, and the Parties command subset; these need clarification in their owning stories, but do not justify restarting discovery or blocking all work. No critical or high finding is established by this rubric review; the explicitly timed upstream decisions remain gates for their named phases.

The consistency review changes the consolidated grade to Fair (3 high, 6 medium, 1 low; 10 distinct findings). The current PRD and architecture disagree on the required Decoration Package dependency, public result records, and Tenants Payload casing. Reconcile those contracts before implementing the affected dependency checks, serialization, and heads; generic catalog and other independent preparation can continue. No critical finding was established. The SM-1/Folders issue appears in both reviews and is counted once, at medium severity.

## Dimension verdicts

- Decision-readiness — adequate
- Substance over theater — strong
- Strategic coherence — adequate
- Done-ness clarity — adequate
- Scope honesty — adequate
- Downstream usability — adequate
- Shape fit — strong

The rubric alone found no high findings. The consolidated grade also incorporates the independent consistency review.

## Findings by severity

### Critical (0)

None.

### High (3)

**C1 [Decision and architecture consistency]** — The allowlist rejects the Decoration Package every exposed Contracts Library must acquire (§4 Dependency allowlist; §8.1 Gateway-ready checklist item 1; architecture AD-2 and AD-15)

The PRD says a Contracts Library's "own transitive closure stays inside that allowlist", whose exhaustive entries are the EventStore client, exposed `*.Contracts`, and the EventStore.Contracts closure. The same PRD requires every Module to "Reference the Decoration Package", named `Hexalith.McpCli.Abstractions` in §3 and §7. That package is neither a Module Contracts package nor part of the pinned EventStore.Contracts closure. AD-2 explicitly draws `Contracts --> Abs`, but AD-15 repeats an "exactly" allowlist without Abstractions. Thus a previously allowed Tenants/Parties package becomes disallowed as soon as it satisfies the first decoration prerequisite. Independently, PRD §4's unqualified "tool package references exactly" excludes the non-Hexalith runtime packages the spine explicitly allows; the intended domain-dependency boundary needs explicit scope.

Fix: Enumerate this repository's Decoration Package as an allowed Contracts dependency, distinguish the domain/Hexalith boundary from the tool's own implementation and pinned third-party dependencies, and align AD-15 and the eventual closure test with that exact policy.

**C2 [Decision and architecture consistency]** — The architecture's document records cannot emit the normative public results (§0; FR-9, FR-11, FR-12; addendum §G; architecture AD-5 and AD-12)

The PRD makes §G "normative" and requires both Heads to serialize "the same result and error record types". Its command document has `operation`, `tenant`, `aggregateId`, `status`, and `result`; AD-5 instead specifies `CommandResult(MessageId, IdempotencyKey, CorrelationId, ResultPayload?)`, omitting four of those fields and naming the result `ResultPayload`. The query example requires `operation` and `tenant`, whereas AD-5 has only `QueryResult(Document?, Paging?)`. §G's gateway error puts `status`, `reason`, `detail`, `retryable`, `retryAfter`, `clientAction`, and `correlationId` directly under `error`; AD-5 groups gateway information under `OperationError(..., Gateway?)`. AD-12 returns Core records directly and derives output schemas from them, so these differences become public schema differences, not private implementation choices. Both Heads agreeing with each other would not prove conformity to §G.

Fix: Reconcile AD-5 with the normative §G field names and nesting, explicitly identify required and optional members, and bind the head/schema contract checks to those documents. Keep the unresolved duplicate flag conditional on OQ-9.

**C3 [Decision and architecture consistency]** — The normative Tenants example uses Payload casing rejected by the selected serialization policy (addendum §G `describe_operation`; FR-7 and FR-15; architecture AD-6 and AD-7)

The example declares a Schema property and required member `tenantId`, then gives `"example": { "tenantId": "acme" }`. AD-6 deliberately sets Payload `PropertyNamingPolicy = null` to preserve "CLR property names verbatim", with `UnmappedMemberHandling = Disallow`; AD-7 derives the Schema with those Module Payload options. The current primary source, `references/Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Queries/GetTenantUsersQuery.cs:12`, declares `public string TenantId { get; init; }` and has no `JsonPropertyName` override. Under the accepted architecture its Payload Schema therefore uses `TenantId`, and the normative lower-case example fails the Schema. Camel-casing the outer result document does not change the keys inside an embedded Schema or Payload.

Fix: Correct the normative example to the contract's actual Payload property spelling and state that outer result casing and Payload casing are distinct. Alternatively, document an explicit upstream contract naming amendment before relying on the lower-case example; do not silently change the Gateway-facing serializer.

### Medium (6)

**R1 [Done-ness clarity]** — The unmarked identifier rule contradicts schema derivation (FR-7, `prd.md:231–237`)

FR-7 first derives schema from the operation type, then says an unmarked property ending in `Id` “is a plain string in the Schema,” immediately followed by “the name suffix never types a property.” For an otherwise ordinary numeric or object-valued `ExternalId`, those instructions cannot both hold: forcing a string types by suffix; preserving the CLR representation violates the plain-string sentence. The explicitly recognized ULID type also needs its existing exception preserved.

Fix: Say an unmarked property retains its normal serializer-derived schema and only receives a lint finding; use “plain string” solely for a property whose declared serialization is already a string. Reconcile the same wording in architecture AD-8 when updating the requirement.

**R2 [Done-ness clarity]** — Missing-URL validation has no verb applicability rule (FR-6 `prd.md:227`; FR-13 `prd.md:298–302`; addendum §E settings table)

FR-6 says `config` and `--version` “always run,” while FR-13 applies settings resolution to every verb and says a missing URL is `configuration_invalid`. Neither scopes URL validation to verbs that submit work or explains whether offline discovery and bootstrap configuration require connection settings. Accepting a global option is not itself the problem; the unconditional missing-value rule is. A conforming implementation could reject the first profile-management command before an operator has configured a URL.

Fix: State which verbs require a resolved URL, exempt bootstrap/config/version as intended, and decide whether catalog-only discovery works offline. This is an applicability clarification, not evidence that an implementation currently fails.

**R3 [Scope honesty]** — The v1 Parties command subset remains a tentative scope statement (§8.1, `prd.md:471`; FR-20)

The requirement says “Publish the agent-facing subset; the erasure and key-rotation Commands are probably not in it.” FR-20 then accepts every operation that happens to be decorated, which cannot establish whether the intended command coverage or exclusions were delivered. OQ-5 assigns the wire-routing decision, but does not explicitly assign this inclusion/exclusion decision or its acceptance inventory.

Fix: Record an owner-approved included/excluded command inventory before Parties decoration, or add a bounded open item with that owner and revisit condition. Keep it upstream; no module-specific runtime configuration is needed here. This is a gate for defining Parties coverage, not a blocker to building the generic catalog.

**R4 [Downstream usability]** — The normative result documents omit the lint outcome (FR-4; FR-12; FR-14 `prd.md:315`; addendum §E lint row and §G `addendum.md:258–328`)

`describe --lint` must list three classes of findings and return a result document with exit 1 when any exist. §G specifies the shared `describe_operation` document but supplies no lint field/document or location for those findings. Two CLI implementations could both “list” them while emitting incompatible JSON or mixing non-JSON text into the JSON-default surface.

Fix: Define the lint result's location and minimum fields in §G, including the empty result case and whether its findings supplement the ordinary describe document. Leave presentation details to the CLI story.

**C4 [Strategic coherence / Decision and architecture consistency]** — SM-1 no longer requires the prerequisite that the PRD repeatedly says gates it (§1 Status; §8.1 Upstream decoration schedule and Folders prerequisite; §9 SM-1; PRD `.memlog.md`)

The status and Folders row both say Folders "gates SM-1". The current metric instead requires Tenants, Parties, "every Module that became Gateway-ready since", and "one further Module". It can pass with Projects alone while Folders remains unready. The decision log records the earlier deliberate release/metric split: "Projects and Folders follow as they become Gateway-ready; SM-1 checked at three months for all four." A later entry says the metric was "made observable" without recording that relaxation. The v1 cut to two Modules was accepted and is not a finding; the surviving Folders gate and the metric's pass condition disagree.

Fix: Choose and record the actual three-month acceptance rule: explicitly retain Projects and Folders in SM-1, or remove the Folders-gates-SM-1 claims and log the relaxed post-release target. Keep v1's two-Module release gate unchanged.

**C5 [Decision and architecture consistency]** — The sample test plan violates the accepted one-Module fixture boundary (§4 Dependency allowlist; §6 NFR-1; architecture AD-15, Consistency Conventions/Tests, and Structural Seed)

The PRD permits "one synthetic sample Contracts Library (the sample Module)" and measures startup for the v1 Modules "plus the sample Module"; the latest decision log explicitly says "Sample Module count is one." AD-15 likewise calls Sample.Contracts "the only synthetic Module", but the architecture's Tests convention says that same assembly "declares two Modules, sample-ulid ... and sample-opaque", and its Structural Seed repeats "two synthetic Modules". This changes both the agreed fixture scope and the benchmark population. It also needs reconciliation with FR-3's assembly-level Module identity before implementers can construct the fixture.

Fix: Keep one declared synthetic Module in the production-like fixture and cover the other Identifier Kind through isolated test construction, or explicitly amend the fixture allowance and assembly arrangement. Update the benchmark definition to match the chosen fixture.

### Low (1)

**C6 [Decision and architecture consistency]** — The handoff status still lists amendments that are already present (§1 Status; §10.1 Handoff to architecture)

The PRD says the spine "must be updated before the executor epic" for AD-7, AD-9, AD-11, AD-15, and AD-19. The current spine already includes Actor among envelope-filled properties (AD-7), the fixed-tenant and operator gate with Command-only extensions (AD-9), the exclusive mcpcli.json store and new settings (AD-11/AD-14), the expanded EventStore.Contracts closure (AD-15), and the Query constant plus nonempty aggregate rule (AD-19). This historical handoff is not evidence that the prior criticals remain open. Residual differences are identified above.

Fix: Mark the listed amendment handoff completed, link its verification, and replace its pending work with any remaining concrete reconciliation items.

## Dimension judgments

### Decision-readiness — adequate

Sections 1, 4, and 8 state consequential choices directly: a single generic surface, no hosted infrastructure in v1, token-owner identity for dev/test, and no release-scope fallback if Tenants or Parties slips. Addendum §A records what was sacrificed by rejecting permanent coexistence, shared profile storage, and unconditional per-call tenant precedence.

The five open questions in §10.2 have owner roles and revisit conditions. OQ-1 belongs to HTTP; OQ-5 to Parties decoration; OQ-8 to publication scheduling; OQ-9 to FR-17. Their presence in a final PRD does not imply all catalog or fixture work is blocked. The current architecture consistency reviewer should determine which §10.1 handoff items still remain; the PRD's historical handoff sentence is not proof they remain unimplemented.

### Substance over theater — strong

The vision describes an actual platform constraint: six legacy packages encode incompatible operation surfaces while module contracts lack runtime descriptions. The proposed catalog, decoration, routing fallback, and migration plan each address that problem. User roles drive concrete decisions: module authors get one decoration dependency, agents get discovery tools, and shell users share the executor.

NFRs predominantly have product-specific consequences: 500 ms catalog startup, 8,000 characters for tool definitions, clean stdio, three-platform support, and reviewable descriptions. The numerical assumptions are disclosed. There is no need to invent market positioning, additional personas, or enterprise SLA sections for this internal tool.

### Strategic coherence — adequate

The central bet—one contract declaration should expose a capability to both agents and scripts—connects §1 to FR-1–FR-20 and to SM-1, SM-2, SM-4, and SM-7. Counter-metrics explicitly prevent apparent progress through new typed tools, dependency creep, or hollow descriptions. Replacement is a longer-term objective; FR-21 makes the migration plan a v1 deliverable and §8.2 correctly places deletions later.

### Done-ness clarity — adequate

All 22 FRs carry observable consequences, and the strongest ones name refusal behavior, error codes, precedence, or test boundaries rather than adjectives. The startup diagnostic table, executor-enforced read-only guarantee, explicit aggregate handling, and source-precedence fixtures are particularly useful for story acceptance. A few literal statements still allow incompatible implementations.

The shared-head result comparison in FR-20/SM-4 needs equivalent initial state for stateful commands, but “one EventStore” does not forbid restoring fixtures between executions. That is a test-design obligation, not a separate PRD blocker. Likewise, OQ-9 explicitly gates deduplication claims before FR-17 implementation; no unsupported retry guarantee should be inferred now.

### Scope honesty — adequate

Sections 8.2–8.3 clearly exclude the admin plane, identity-server work, executor retries, typed tools, and direct module API execution. HTTP is explicitly the only committed next release. The dependency allowlist and zero-module-specific-code requirement make the scope boundary inspectable. There are nine substantive inline assumptions with matching index entries, and five unresolved OQs; several are low-risk defaults while the dependency-sensitive ones have phase gates. Their count alone is not a reason to withhold architecture work.

### Downstream usability — adequate

The glossary and feature/FR index make extraction straightforward. Stable identifiers are preserved despite FR-18/FR-19 placement. §0 explicitly promotes addendum §E and §G to normative status, which prevents readers from treating the argument and result contracts as optional explanatory examples. The remaining gap is that not all promised machine-consumable outcomes have a defined representation.

### Shape fit — strong

A capability specification is appropriate for this internal platform tool. Three compact journeys illustrate cross-module execution, discovery, and module onboarding without overwhelming the functional contract. The PRD's length is high, but its recent decision log explicitly accepts keeping testable consequences in the main document; this review does not relitigate that choice. Mechanism detail and deferred-module depth are largely kept in the addendum, and a separate architecture spine exists for implementation decisions.

## Additional reviewer assessment

The amended PRD preserves the main accepted product direction and resolves the former tenant, actor, profile-store, and aggregate-less-query conflicts. It is not yet consistent enough to use with the current architecture spine as a single implementation contract: the dependency allowlist still rejects a dependency required by decoration itself, and the normative result examples disagree with the architecture's records and Payload serialization. These are current cross-document conflicts, not requests to design intentionally deferred features. Findings: 0 critical, 3 high, 2 medium, 1 low.

## Mechanical notes

- The 22 FR definitions are unique; FR-18 and FR-19 are deliberately ordered by feature and explicitly explained. UJ-1–UJ-3, NFR-1–NFR-8, SM-1–SM-7, and SM-C1–SM-C4 are present. Stable OQ numbering is split between open and resolved sections intentionally.
- All nine substantive inline assumption tags round-trip to §11. Literal mentions of the tag in explanatory text are not additional assumptions.
- UJ-2 has an agent session rather than a named human protagonist. That is suitable for this tool's actual consumer role; adding a fictional name solely for the rubric would not improve the document.
- Addendum §D line 171 still says “four v1 Contracts libraries”; the amended PRD has two v1 modules. Update that inherited survey wording or date it explicitly.
- Addendum §G's Parties ULID error example is misleading now that Parties declares `String`; use a synthetic ULID-module example or a String-kind gateway-pattern violation.
- Addendum §G says absent optional fields are omitted, but the gateway-error example uses `retryAfter: null`. Clarify the canonical omitted/null convention when formalizing record schemas.
- Mechanical checks: 22 unique FR definitions; no undefined FR references or broken explicit Markdown file links in the PRD/addendum.
- Scope: current PRD, addendum, decisions, original brief, architecture spine, and cited local Contracts source. No implementation tests or live Gateway verification were performed.
- The earlier Poor report predates the amendments. Historical reports were preserved; this report covers the current documents.

## Reviewer files

- [review-rubric.md](review-rubric.md)
- [review-consistency.md](review-consistency.md)

Rubric R5 and consistency C4 describe the same SM-1 conflict; C4 is the consolidated finding. Reviewer files retain their original assessments.

## Validation scope and source fingerprints

The PRD and addendum were not modified. Source SHA-256 fingerprints:

- `prd.md`: `64cfc9fd87d985994c97429b957960174772e7071d83b39e1024f2f4bcb4c929`
- `addendum.md`: `b5966e212dd28f1c7c1a679f8184badcfe2d57f49456af5abd5fbf367208699c`

This is document validation, not certification of implementation or upstream readiness. Existing OQ phase gates still apply.

