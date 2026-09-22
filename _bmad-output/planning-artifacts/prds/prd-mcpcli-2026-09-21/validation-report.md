# Validation Report — Hexalith.McpCli PRD

- **PRD:** `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md` (with `addendum.md`)
- **Rubric:** `.claude/skills/bmad-prd/assets/prd-validation-checklist.md`
- **Run at:** 2026-09-22T09:08:01+02:00
- **Grade:** Poor (blocker-driven: every rubric dimension is strong or adequate, but four source-verified critical findings stand)

## Overall verdict

The amended PRD is a sound spine: the thesis (CQRS uniformity through one Gateway makes one generic agent surface possible, and the Decoration Attribute turns that into a platform policy) still drives every feature, the four contradictions the 2026-09-21 review found are gone, and nearly every FR carries a consequence a story can test. What is at risk is one open question the PRD treats as safely deferred but is not: the Gateway's query validator rejects an empty `AggregateId`, so FR-16's interim rule for list-style Queries fails against the referenced code on the first Tenants query story; and one brownfield claim (`projectionActorType` for Tenants) is stale.

The adversarial and spine-alignment reviewers materially shift the picture, and their critical findings were spot-checked against the source under `references/` by the validating session. Three brownfield facts contradict the PRD as written: Tenants runs every Command and Query under the fixed Envelope tenant `system` (`TenantIdentity.ForTenant` puts the managed tenant in the aggregate id), so the one-default-tenant-per-Profile model and FR-13's "tenant-less global-administrator Queries" claim are wrong for the flagship Module; `Hexalith.EventStore.Contracts` package-references `Hexalith.Commons.UniqueIds`, so the §4 closure rule and its CI test reject both v1 Contracts Libraries on day one; and `SubmitQueryRequest` carries neither a correlation identifier nor extensions, so FR-16 and addendum §E promise a `run_query` pass-through the pinned client cannot make. A fourth critical is a design gap rather than a brownfield error: the LLM-controlled per-call `tenant` argument, identity-bearing Payload properties such as Projects' `ActorPrincipalId`, and unrestricted `extensions` are three caller-controlled identity paths the §4 tenant guardrail does not cover. The grade is Poor because of these blockers, not because of the document's craft; the PRD is usable now for the Decoration Package, Catalog, MCP head, CLI head, and Profile epics, and becomes usable for the executor and coverage epics once the four criticals and the OQ-3 decision land.

## Dimension verdicts
- Decision-readiness — strong
- Substance over theater — strong
- Strategic coherence — strong
- Done-ness clarity — adequate
- Scope honesty — strong
- Downstream usability — strong
- Shape fit — strong

## Findings by severity

Findings raised by more than one reviewer are merged and carry the highest severity assigned. Reviewer tags: R = rubric, A = adversarial, S = spine alignment.

### Critical (4)

**[Done-ness · R, A, S]** — Aggregate-less Queries cannot reach the Gateway as specified; OQ-3 is a v1 blocker, not a deferral (FR-16 c2 `[ASSUMPTION]`, §10 OQ-3, §5.1 `aggregateIdProperty`, §8.1 Tenants)
`SubmitQueryRequestValidator.cs` requires a non-empty `AggregateId`, so the FR-16 fallback "sends an empty aggregate identifier pending OQ-3" is a guaranteed 400 for `tenants.list-tenants`, `tenants.get-user-tenants`, and every Parties list read. No Tenants code constructs a `SubmitQueryRequest`, so "Tenants covered end to end" rests on a read path nothing exercises. Sibling clients send a per-operation constant (Parties `"parties"`, Rest `RestQueryBindingSource.Constant`) and the Decoration Attribute has no member for one.
Fix: Close OQ-3 from source now. Add a Query-only `aggregateId` constant member to §5.1 and FR-2 (mutually exclusive with `aggregateIdProperty`); make the FR-16 rule "explicit argument, else accessor value, else the attribute constant; a Query resolving to nothing is `validation_failed`, never empty". Add a spike deliverable before the Executor epic: `tenants.list-tenants` returns a page through `IEventStoreGatewayClient.SubmitQueryAsync` from a throwaway harness.

**[Adversarial · A]** — Tenants runs under the fixed Envelope tenant `system`; the PRD's tenant model cannot drive it (§3 Tenant, §4 Tenant, FR-3 c3, FR-13 c4, FR-18, UJ-1, UJ-2)
`TenantIdentity.ForTenant(managedTenantId)` yields Envelope tenant `system` with the managed tenant as aggregate id; `TenantsSystemTenantValidator` and `GetGlobalAdministratorsQueryHandler` reject anything else. So FR-13's "tenant-less" claim is false, FR-3's rationale for `String` conflates Envelope tenant with Identifier Kind, UJ-1 and UJ-2 cannot share one Profile default tenant, and `describe_operation` never tells the agent to pass `tenant: "system"`.
Fix: Add a Module marker member `fixedTenant` (or an Operation member `tenant`) surfaced by `describe_operation` as the Envelope default and used by the executor when no per-call tenant is given; a differing per-call tenant is `validation_failed`. Rewrite FR-3 c3 to cite a real non-ULID aggregate id and fix FR-13 c4 and the two journeys.

**[Adversarial · A, S]** — The closure rule as written excludes Tenants and Parties themselves (§4 Dependency policy, FR-20, §3 Contracts Library, §8.1 Projects; spine AD-15)
`Hexalith.EventStore.Contracts.csproj` package-references `Hexalith.Commons.UniqueIds`, which references `ByteAether.Ulid`. "No other Hexalith package" therefore fails for every Contracts Library, the mandated CI test blocks the first v1 pin, and the first story will loosen the rule ad hoc.
Fix: State the rule once in §4 as an allowlist: `*.Contracts` packages, `Hexalith.EventStore.Contracts` and its own transitive closure at the pinned version (today `Hexalith.Commons.UniqueIds`, `ByteAether.Ulid`), no framework reference beyond `Microsoft.NETCore.App`; additions are a PRD change. Point §3 and FR-20 at §4; ask the spine owner to align AD-15.

**[Adversarial · A]** — Identity can be set by the caller three ways; the tenant guardrail covers none of them (§4 Tenant, FR-9 argument table `tenant` and `extensions`, FR-16, FR-21 c2, §8.1 Projects)
(1) The per-call `tenant` argument is chosen by the LLM; a token with several tenant claims lets the agent hop tenants with no operator consent, a fourth tenant source the repository policy does not list. (2) Projects' `IProjectCommand.ActorPrincipalId` is an ordinary Schema property, so `send_command` lets the agent name any principal as the actor. (3) `--extension key=value` passes through with no allowlist against a Gateway that stores unclaimed extension keys as trusted.
Fix: Honor per-call `tenant` only when the Profile has no default or the operator sets `--allow-tenant-override`, else `validation_failed`. Add an `actorProperty` attribute member the executor fills from session identity and marks `readOnly`. Add an extension-key allowlist per Profile, default empty.

### High (14)

**[Spine · S]** — `run_query` cannot pass a correlation identifier or extensions through the pinned client (FR-16 sentence 1, FR-17, addendum §E rows `correlationId` and `extensions`; spine AD-9)
`SubmitQueryRequest` has no such members and the validator rejects `AdditionalProperties`; query correlation comes from an `X-Correlation-ID` header the client never sets.
Fix: Make `correlationId` and `extensions` `send_command`-only rows in §E; in FR-16 say Queries get the Gateway's correlation identifier in the result (FR-17); move query correlation and extensions to §8.2.

**[Shape fit · R, A, S]** — Tenants no longer has a projection actor; `projectionActorType` "required for Tenants" is stale in three places (§5.1 table, FR-2 c1, §8.1 Tenants)
`TenantQueryHandlerBase.cs` describes the retired `TenantsProjectionActor`; reads go through `IReadModelStore` via handler routing; the string `ProjectionActorType` appears nowhere in Tenants.
Fix: Make the member "optional; only for a Module whose projection is served by a named actor"; rewrite FR-2 c1 and the Tenants prerequisite accordingly, after confirming with the Tenants owner.

**[Adversarial · A]** — Sharing `~/.eventstore/profiles.json` with the admin CLI makes one profile name unusable by both tools (FR-18, §5.6, addendum §B and §E)
Admin `url` and token target the admin API, not the Gateway; `csv` format is unsupported here.
Fix: Make `~/.eventstore/mcpcli.json` the sole store (`url`, `token`, `format`, `tenant` per profile), or keep `profiles.json` read-only for the active profile name only. State what happens with an unknown `format`.

**[Adversarial · A; Done-ness · R]** — FR-14 exit code 1 fires for reasons unrelated to the invocation, and the migration period makes that the normal state (FR-14 row 1, FR-6, FR-7 c4, UJ-3)
Tenants and Parties Contracts carry zero `[Description]` attributes today, so every discovery verb exits 1 under `set -e` until the last property is described, while FR-7's unmarked-`Id` case is lint-only.
Fix: Property-level findings are lint-only, surfaced by `describe --lint`; Catalog diagnostics are stderr-only unless `--strict` (then exit 2 before any result). Say so in FR-6 and FR-14.

**[Adversarial · A]** — The Schema is derived with the tool's serializer options, but Parties and Tenants ship their own converters (FR-5 c3, FR-7, FR-16 accessor, FR-1 c3)
Fix: Require attribute-complete decorated types in the Gateway-ready checklist and add a Catalog diagnostic when a property's converter comes from options; or add a marker member naming a static `JsonSerializerOptions` provider.

**[Adversarial · A]** — Nothing stops `tenantProperty` from naming the aggregate identifier, and on Tenants that is the natural mistake (§5.1 `tenantProperty`, FR-16 c3)
Fix: Add an FR-6 error category for `tenantProperty` naming the aggregate identifier source; note that Tenants' `TenantId` is an aggregate id, not a tenant.

**[Adversarial · A]** — SM-4 cannot pass as written, and several acceptance statements are unobservable (SM-4, FR-9 c4, FR-11 c3, NFR-1, NFR-8, SM-5, SM-6)
Fix: SM-4 compares Catalog data and error documents for identical inputs, with volatile Command result fields masked. Name the three FR-9 labels, the FR-11 distance metric, and the NFR-1 runner (`ubuntu-latest` per the spine).

**[Adversarial · A]** — The result document shapes are not specified anywhere, yet both Heads must agree on them (FR-11, FR-17, FR-9 c2, SM-4)
Fix: Add addendum §G with one JSON example per tool result and per error document; both Heads serialize the same record types.

**[Adversarial · A]** — `--format table` is required for every verb but undefined for nested JSON documents (FR-13, FR-12, addendum §E)
Fix: `table` applies to `modules`, `operations`, `config`; on `describe`, `send`, `query` it either falls back to `json` with a stderr note or is rejected with exit 2. Pick one.

**[Adversarial · A; Spine · S]** — FR-20 and FR-3 disagree on what a referenced-but-undecorated Module looks like (FR-3 c1, FR-20 c2, FR-6 categories)
Fix: Define two states: unmarked assembly (invisible, no diagnostic) and marked assembly with zero exposed Operations (listed, warning `empty_module`/`no_operations`). Amend FR-6 and FR-20.

**[Adversarial · A]** — The build-time assembly list generator has no rule for which package references are Contracts Libraries (FR-5, addendum §B)
Fix: `HexalithContracts="true"` metadata on the `PackageReference` item, read by an MSBuild target; a test that the list equals the flagged set.

**[Adversarial · A]** — Upstream decoration work has no owner, date, or gate, and it is on the v1 critical path (§8.1 checklist, Tenants and Parties prerequisites, §7, SM-1, SM-3)
Fix: Per-Module table with owner, target version, and earliest pinnable tool release; a fallback in §8 if Parties Queries are not published by a date.

**[Adversarial · A]** — The `Ulid` CLR-type rule and the Decoration Package's zero-dependency rule conflict (FR-7 c2, FR-1 c4, §3)
Fix: Name the recognized type by full name (`ByteAether.Ulid.Ulid`); reword FR-1 so the analyzer's dependencies are private assets.

**[Adversarial · A]** — The Tenants Module is the admin plane the PRD says it excludes (§2.2 Non-Users, §8.3 Non-Goals, FR-20)
Every Tenants operation requires the `system` tenant claim, a platform-administrator token.
Fix: Either narrow the decorated Tenants subset (and pick a different second v1 Module) or amend §2.2 to say the exclusion covers EventStore infrastructure only and accept the admin-CLI overlap.

### Medium (17)

**[Decision-readiness · R; A; S]** — Tenants paging decision is still shown as open although spine AD-20 decided it; two paging channels are visible to the agent (§8.1 Tenants, FR-7, FR-17, FR-4, addendum §E)
Fix: Record AD-20 in FR-16 or FR-17 (paging travels only as `run_query` arguments; Payload paging members are ordinary Payload or lint-flagged); extend the FR-4 lint list; turn the §8.1 bullet into a prerequisite.

**[Substance · R]** — Overlength persists; §0's "stated once" promise is not quite met (6,284 words vs 2,500–4,000 target)
Fix: Keep §5.1 as the only description of attribute members; reduce FR-2 and FR-16 c2 to a precedence sentence and pointer; drop the §8.3 dependency bullet. Target a 600–900 word cut without cutting testable consequences.

**[Spine · S]** — FR-7 "includes every declared property" contradicts the spine's removal of computed get-only members (FR-7 lead; spine AD-7)
Fix: "Get-only members with neither a setter nor a constructor parameter are not Schema properties; the executor reads them through the accessor."

**[Spine · S]** — Both v1 Modules are `String`-kind; Parties is never told, and the `Ulid` kind has no v1 consumer (FR-3 c3, §8.1 Parties, UJ-1)
Fix: FR-3 "today both v1 Modules declare `String`"; §8.1 Parties adds "declare `IdentifierKind = String`".

**[Spine · S]** — §8.1 Tenants prerequisite still requires `aggregateIdProperty` on Query attributes after FR-2 made it optional
Fix: Rewrite once the OQ-3 fix lands.

**[Spine · S]** — Addendum §E is normative for FR-9 and FR-12 but the addendum disclaims requirement status (FR-9, FR-12, addendum preamble)
Fix: One preamble line: "§E is normative; FR-9 and FR-12 are accepted against it."

**[Spine · S]** — UJ-1 and NFR-1 still assume Projects is in v1 (UJ-1, NFR-1, SM-2)
Fix: Rewrite UJ-1 over Tenants and Parties; state NFR-1 as the v1 Modules plus the two sample Modules.

**[Spine · S]** — FR-20 "covered end to end" has no observable definition (FR-20, §8 lead)
Fix: "For every Operation in `list_operations`, both Heads submit it against a running EventStore in the harness, the Gateway accepts it, and the two documents are equal (NFR-7, SM-4)."

**[Adversarial · A]** — Parties Wire Types as full CLR type names are 24 hand-typed strings with no drift test (§3 Wire Type, FR-2, §8.1 Parties)
Fix: Marker member `wireTypeConvention = FullTypeName | KebabCase | Explicit`; Catalog warning on a redundant explicit literal.

**[Adversarial · A]** — `EVENTSTORE_READ_ONLY` with ".NET boolean parsing" rejects `1` and `0` (FR-19)
Fix: Accept `true`, `false`, `1`, `0`; anything else is `configuration_invalid`, exit 2.

**[Adversarial · A]** — Read-only refusal of a "hand-crafted `send_command`" is untestable where the PRD puts it (FR-19)
Fix: Split into "the MCP head does not register `send_command`" and "the executor called directly returns `read_only`".

**[Adversarial · A]** — NFR-2's 8,000-character budget probably excludes the output schemas FR-11 requires (NFR-2, FR-11)
Fix: State whether `outputSchema` counts; add a snapshot test that measures.

**[Adversarial · A]** — CLAUDE.md still says "Identifiers are ULIDs"; the PRD has moved to Identifier Kind (§4 Identifiers, FR-3)
Fix: Update the line in `AGENTS.md` via the sync script: Envelope identifiers are ULIDs; payload identifiers follow the Module's Identifier Kind.

**[Adversarial · A]** — UJ-1's retry story asserts Gateway deduplication that the PRD does not verify (UJ-1, FR-16, FR-17, §4 Idempotency)
Fix: Assumption tag plus an OQ item for the EventStore owner; the result document states whether the Gateway reported a duplicate.

**[Adversarial · A]** — Addendum §E resolution order omits `--profile` selection and per-call precedence for `tenant` only (FR-13, addendum §E)
Fix: "`--profile` resolves first; the remaining options resolve per the chain against the selected Profile. Only `tenant` has a per-call source."

**[Adversarial · A]** — Gateway input constraints are not pre-validated, so tool-side mistakes surface as Gateway 400s (§4 Identifiers, FR-15, FR-16)
Fix: FR-15 pre-validates Tenant, aggregate identifier, correlation identifier, and extensions against the Gateway's published patterns as `validation_failed`.

**[Adversarial · A]** — FR-22's deliverable is a pull request in another repository with no fallback; §8.2 pre-commits to "typed tools" while SM-C2 forbids chasing them (FR-22, §8.1 item 6, §8.2, SM-C2)
Fix: Close FR-22 on the pull request being opened and linked; list typed tools under parked and keep the HTTP transport as the only committed next release.

### Low (12)

**[Done-ness · R]** — A Query with no Tenant has no stated outcome (FR-13 c4). Fix: "A Command or Query with no Tenant from any source is a validation failure."
**[Done-ness · R, A, S]** — Duplicate Module Name is a "startup error" in FR-3 and an excluded type in FR-6; which assembly survives is unstated. Fix: one clause in FR-6 naming the survivor rule.
**[Downstream · R, A, S]** — Addendum cross-references point at PRD sections that no longer exist (§D "§4.8 and §9.1"; §F "§9.2", "§6"). Fix: §D → "§4 and §8.1"; §F → "§8.2" and "§4 Idempotency".
**[Mechanical · R, A, S]** — Addendum §C repeats three paragraphs verbatim (lines 88–107 and 108–125). Fix: delete the prose duplicate.
**[Adversarial · A]** — Legacy Server counts disagree: "six" in §1, four plus the FrontComposer host in §3, six named in addendum §D. Fix: one count, one list.
**[Adversarial · A; Spine · S]** — `mcp --transport http` "names the release in which it arrives" (FR-12); FR-6 lists `mcp` among Catalog-needing verbs but the spine exempts the HTTP transport. Fix: exit 2 with `code: unsupported_transport` before building the Catalog.
**[Adversarial · A]** — §7 versioning cannot signal Module-driven breaking changes. Fix: Operation Name stability is a Module obligation in the Gateway-ready checklist.
**[Adversarial · A]** — NFR-6 "no native dependencies" is true, but the tool carries the Dapr SDK. Fix: note the size cost or request a gateway-only client package.
**[Adversarial · A]** — Glossary "Wire Type" example does not say Parties Queries do not exist. Fix: one clause.
**[Spine · S]** — NFR-7's `[ASSUMPTION]` is resolved by the spine (AD-16, Aspire harness) but still tagged and indexed in §11. Fix: replace the tag with a pointer and remove from §11.
**[Spine · S]** — Addendum §B tells the reader to copy the admin MCP's static tool classes, which spine AD-12 forbids. Fix: "logging pattern to copy; tool registration is runtime `McpServerTool.Create`."
**[Spine · S]** — Glossary "Routing Values" still names an aggregate identifier property only; FR-11 lacks the nearest-name metric. Fix: "a Payload property, the contract getter, or a constant"; "nearest by case-insensitive edit distance".

## Open questions assessment (spine reviewer)
- OQ-1 HTTP authentication: does not block architecture or v1 epics; seam and error code are decided, issuer and header forwarding correctly left open.
- OQ-3 aggregate-less Queries: blocks architecture (AD-19 rests on a falsified assumption) and the executor epic; answerable from source now.
- OQ-5 Parties routing: blocks only the upstream Parties decoration epic; today's values `PartyDomain = "party"` match the PRD.
- OQ-6 deletion order: blocks only the FR-21 plan content.

## Mechanical notes
- Word counts: `prd.md` 6,284 (previous 6,037; target 2,500–4,000); `addendum.md` 1,521.
- `[ASSUMPTION]` tags: 10 inline, §11 roundtrip clean both ways; FR-13 c4 and SM-6 carry bare tags with no rationale; NFR-7's tag is already resolved by the spine.
- `[NOTE FOR PM]`: 2 (§8.1 Folders, §8.2 HTTP transport).
- Open Questions: 7 numbered, 4 open (OQ-1, OQ-3, OQ-5, OQ-6), 3 resolved with source and date.
- IDs: FR-1..22, NFR-1..8, SM-1..7, SM-C1..4, UJ-1..3 contiguous; FR-19 precedes FR-18 by design. Every in-PRD cross-reference resolves.
- Dangling cross-references: four in `addendum.md` into stale PRD section numbers (§4.8, §9.1, §9.2, §6).
- Addendum §C duplicated block; Legacy Server count (six vs four plus host) reconciles only if the Projects plug-in counts as a server.
- FR-22's rule is not yet in `hexalith-llm-instructions.md`; expected, since FR-22 adds it.
- Brownfield claims checked: rubric found all spot-checks accurate except the Tenants projection actor; spine reviewer checked 32 claims, 27 accurate, 5 inaccurate (table in `review-spine-alignment.md`).
- Prior review (2026-09-21): 4 of 5 high findings resolved; overlength persists at medium; the Query aggregate-id item became this run's critical.

## Reviewer files
- `review-rubric.md`
- `review-adversarial-general.md`
- `review-spine-alignment.md`
- `review-downstream.md` (2026-09-21 run, kept for history)
