---
title: "PRD review: spine alignment and downstream usability"
reviewed: 2026-09-22
inputs:
  - prd.md (updated 2026-09-22)
  - addendum.md (updated 2026-09-22)
  - ../../architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md
  - .memlog.md entries dated 2026-09-22
  - git diff of prd.md and addendum.md (working tree vs HEAD)
  - references/Hexalith.EventStore, references/Hexalith.Tenants, references/Hexalith.Parties, references/Hexalith.Projects, references/Hexalith.Folders (read-only source)
---

# Review: PRD alignment with the architecture spine

## Verdict

The amendment pass landed every bullet of the spine's "PRD Amendments" section, the FR ids are stable, the `[ASSUMPTION]` index in §11 matches the tags in the body, and every hunk in this morning's diff is traceable either to the amendments list or to the spine's conventions table. The PRD is usable for epics for the Decoration Package, Catalog, MCP head, CLI head, and profiles. It is not yet usable for the executor and coverage epics, because three brownfield claims that the amendment inherited from the spine are contradicted by the EventStore, Tenants, and Parties source: the Gateway rejects an empty query aggregate identifier (so the FR-16/OQ-3 assumption fails and no attribute member exists to declare the constant that list-style Queries need, which blocks the Tenants end-to-end half of the v1 gate); the closure rule as worded rejects both v1 Contracts Libraries because `Hexalith.EventStore.Contracts` itself depends on `Hexalith.Commons.UniqueIds`; and `run_query` cannot pass a correlation identifier or extensions through the pinned client because `SubmitQueryRequest` has no such members and the Gateway validator rejects any extension data. A fourth claim, that Tenants has its own projection actor and therefore needs `projectionActorType`, is stale: that actor is retired. Fixing these four is a small, well-bounded PRD change plus one spine correction; the remaining findings are consistency and wording.

Counts: 1 critical, 3 high, 8 medium, 7 low.

## Findings

### Critical

#### C-1. Aggregate-less Queries cannot reach the Gateway as specified; blocks the Tenants half of the v1 gate

- **Location:** PRD FR-16 (assumption), §10 OQ-3, §5.1 attribute table (`aggregateIdProperty`), §8.1 Tenants prerequisite; spine AD-19.
- **Quoted:** FR-16: "`[ASSUMPTION: a Query with none sends an empty aggregate identifier pending OQ-3.]`"; spine AD-19: "a Query resolving to nothing sends `string.Empty` [ASSUMPTION pending PRD OQ-3]".
- **Note:** The Gateway validator rejects it outright: `references/Hexalith.EventStore/src/Hexalith.EventStore/Validation/SubmitQueryRequestValidator.cs:37-39` has `RuleFor(x => x.AggregateId).NotNull()...NotEmpty().WithMessage("AggregateId cannot be empty")` with no `When` guard on the `NotEmpty` rule. The sibling clients answer OQ-3 de facto with a per-operation constant: `references/Hexalith.Parties/src/Hexalith.Parties.Client/HttpPartiesQueryClient.cs:22` `ListAggregateId = "parties"` is sent as both `AggregateId` and `EntityId` for list queries, and `QueriesController.cs:79-81` routes `EntityId = AggregateId` when the caller omits `EntityId`. The EventStore Rest layer already models this with `RestQueryBindingAttribute(RestQueryBindingSource.Constant, "global-administrators", ...)` (`references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Rest/RestQueryBindingAttribute.cs`), and Tenants uses it on `GetGlobalAdministratorsQuery`. Today `ListTenantsQuery` and `GetUserTenantsQuery` have no aggregate-identifier property at all, so after the amendment (`aggregateIdProperty` optional for Queries, accessor null) every `tenants.list-tenants` call would be `validation_failed` or Gateway-rejected. The Decoration Attribute has only `aggregateIdProperty` (a Payload property name); there is no way to declare a constant. This makes "Tenants covered end to end" (FR-20, §8) unreachable without an out-of-band per-call `aggregateId` that `describe_operation` cannot tell the agent about.
- **Fix:** Close OQ-3 in the PRD from source: add an attribute member `aggregateId` (constant, Query only, mutually exclusive with `aggregateIdProperty`) to §5.1 and FR-2; make the FR-16 rule "explicit argument, else accessor value, else the attribute constant; a Query resolving to nothing is `validation_failed`, never an empty string"; drop the FR-16 `[ASSUMPTION]` and its §11 entry; add to the §8.1 Tenants prerequisite "list-style Queries declare a constant aggregate identifier". Ask the spine owner to amend AD-19 accordingly and to add `AggregateIdConstant` to `OperationDescriptor`. Cite `SubmitQueryRequestValidator.cs:37-42` and `HttpPartiesQueryClient.cs:22` as the evidence so the EventStore owner only confirms rather than researches.

### High

#### H-1. The closure rule as written rejects both v1 Contracts Libraries

- **Location:** PRD §4 Dependency policy, FR-20 and its first consequence, §3 Contracts Library; spine AD-15.
- **Quoted:** §4: "A Contracts Library is referenced only when its transitive closure contains no other Hexalith package and no framework reference beyond the base runtime (the closure rule, enforced by a CI test over the restored dependency graph; FR-20)"; FR-20: "only the Contracts Libraries that satisfy the closure rule (§4), today Tenants and Parties".
- **Note:** `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Hexalith.EventStore.Contracts.csproj` has `<PackageReference Include="Hexalith.Commons.UniqueIds" />`. Both `Hexalith.Tenants.Contracts.csproj` and `Hexalith.Parties.Contracts.csproj` reference only `Hexalith.EventStore.Contracts`, so their closures contain `Hexalith.Commons.UniqueIds`, a Hexalith package that is neither a `*.Contracts` package nor a `Hexalith.EventStore.*` package. The PRD wording ("no other Hexalith package") and the spine wording (AD-15: "no Hexalith package other than `*.Contracts` packages and `Hexalith.EventStore.*` contract packages") both fail Tenants and Parties, so the CI test FR-20 mandates would block the v1 pin on day one. The PRD wording is also stricter than the spine's: it does not allow other `*.Contracts` packages in the closure (Projects depends on `Hexalith.Conversations.Contracts` and `Hexalith.FrontComposer.Contracts`), which the spine allows. §3 "its transitive EventStore contract packages are allowed" is the third, narrower phrasing of the same rule.
- **Fix:** State the rule once, in §4, as an allowlist: `*.Contracts` packages, `Hexalith.EventStore.Contracts` and its own transitive closure (today `Hexalith.Commons.UniqueIds`), no `FrameworkReference` beyond `Microsoft.NETCore.App`; make §3 and FR-20 point to §4 instead of restating it. Ask the spine owner to align AD-15 and the closure test with the same allowlist.

#### H-2. `run_query` cannot pass a correlation identifier or extensions through the pinned client and Gateway

- **Location:** PRD FR-16 sentence 1, FR-17, addendum §E rows `correlationId` and `extensions` (both listed for `run_query`); spine AD-9 assumption.
- **Quoted:** FR-16: "passes a caller-supplied correlation identifier and extensions through"; §E: "correlationId | `send_command`, `run_query` (optional)" and "extensions | `send_command`, `run_query` (optional)"; spine AD-9: "For a Query, `CorrelationId` and `Extensions` travel in `SubmitQueryRequest.AdditionalProperties` as `correlationId` and `extensions` [ASSUMPTION: the Gateway reads both; EventStore owner confirms before FR-16 is implemented]".
- **Note:** `SubmitQueryRequest` (`references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Queries/SubmitQueryRequest.cs`) has no `CorrelationId` or `Extensions` member; its only open slot is `[JsonExtensionData] AdditionalProperties`. The Gateway rejects that slot: `SubmitQueryRequestValidator.cs:142-145` `RuleFor(x => x.AdditionalProperties).Must(properties => properties is null || properties.Count == 0).WithMessage("Unknown query policy fields are not supported.")`. The query correlation identifier comes from the `X-Correlation-ID` request header via `CorrelationIdMiddleware.cs:8-28` and `QueriesController.cs:50`, and `EventStoreGatewayClient.cs` sets no such header (only `If-None-Match`, line 195). So the spine's assumption is already answered from source: no. Commands are fine: `CommandsController.cs:143` honors `request.CorrelationId` and lines 91-127 sanitize `request.Extensions`.
- **Fix:** In §E, make `correlationId` and `extensions` `send_command`-only rows in v1; in FR-16 say "passes a caller-supplied correlation identifier and extensions through for Commands; a Query gets the Gateway's correlation identifier in its result (FR-17)"; move query correlation and extensions to §8.2 as deferred pending an EventStore change (an `X-Correlation-ID` header on `SubmitQueryAsync`). Tell the spine owner AD-9's assumption is false per source and `RunQueryArguments` should drop `CorrelationId` and `Extensions` (or keep them and refuse them with `validation_failed` until the client supports them).

#### H-3. Tenants no longer has a projection actor; `projectionActorType` "required for Tenants" is stale in three places

- **Location:** PRD §5.1 attribute table row `projectionActorType`; FR-2 consequence 1; §8.1 Tenants prerequisite.
- **Quoted:** §5.1: "`projectionActorType` | query | Module has its own projection actor (Tenants)"; FR-2: "A Tenants Query still needs `projectionActorType`"; §8.1: "`projectionActorType` and `aggregateIdProperty` on Query attributes".
- **Note:** `references/Hexalith.Tenants/src/Hexalith.Tenants/Queries/Handlers/TenantQueryHandlerBase.cs:21-25`: "logic that used to live in the retired `TenantsProjectionActor`. Reads go through the platform `IReadModelStore` ... no DAPR actor host is involved." No file under `references/Hexalith.Tenants/src` mentions `ProjectionActorType`. The Gateway still accepts the optional field (`QueriesController.cs:96`, validator lines 79-88), so the member itself is harmless, but a story writer following FR-2 would make the Tenants Query decoration fail acceptance for want of a value that has no consumer.
- **Fix:** Change the §5.1 "Required when" cell to "optional; only for a Module whose projection is served by a named actor"; rewrite the FR-2 consequence as "A Tenants Query needs neither `projectionActorType` nor `aggregateIdProperty` unless it targets one aggregate (then `aggregateIdProperty`) or is list-style (then the constant of C-1)"; drop `projectionActorType` from the §8.1 Tenants prerequisite.

### Medium

#### M-1. FR-7 "includes every declared property" contradicts the spine's removal of computed get-only members

- **Location:** PRD FR-7 lead sentence; spine AD-7.
- **Quoted:** FR-7: "derives a Schema from the Operation type that includes every declared property and rejects unknown properties"; AD-7: "removes get-only members that have neither a setter nor a constructor parameter (such as `ICommandContract.AggregateId`)".
- **Note:** Tenants Commands declare `public string AggregateId => TenantId;` (`references/Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Commands/CreateTenant.cs`). Under FR-7 as written, `AggregateId` appears in the Schema as a required string the caller must send; with `additionalProperties: false` and a value that must equal `TenantId`, this is either redundant or a new disagreement case the PRD does not define. The spine decided the opposite and did not list it under PRD Amendments.
- **Fix:** Add to FR-7: "Get-only members with neither a setter nor a constructor parameter (the `ICommandContract.AggregateId` getter) are not Schema properties; the executor reads them through the accessor (FR-16)." Ask the spine owner to add this to the PRD Amendments list for traceability.

#### M-2. Paging-is-Envelope-only (AD-20) and its lint did not land in the PRD

- **Location:** PRD FR-4, FR-9, FR-17, §8.1 Tenants prerequisite; spine AD-20 and the lint convention.
- **Quoted:** §8.1: "decide whether the `Cursor` and `PageSize` Payload members give way to Envelope paging"; spine AD-20: "A Query Payload member named `PageSize`, `Offset`, or `Cursor` is ordinary Payload and a `describe --lint` warning `unmarked_paging_member`".
- **Note:** `GetTenantUsersQuery` and `ListTenantsQuery` carry `Cursor` and `PageSize` (`references/Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Queries/*.cs`). The spine made the decision the PRD leaves to Tenants (Envelope paging wins, Payload members stay ordinary Payload) and added a lint the PRD never names, so a story writer reading only the PRD will not produce the lint story and may write a story that maps Payload `PageSize` to `SubmitQueryRequest.Paging`.
- **Fix:** In FR-9 or FR-17 add "paging travels only as `run_query` arguments (§E) and never from Payload members; a Payload member named `PageSize`, `Offset`, or `Cursor` is ordinary Payload"; extend the FR-4 lint list with "Payload paging members"; reword the Tenants prerequisite to "decide whether to remove the `Cursor` and `PageSize` Payload members now that paging is Envelope-only".

#### M-3. Both v1 Modules are `String`-kind; Parties is never told, and the `Ulid` kind has no v1 consumer

- **Location:** PRD FR-3 consequence 3, §8.1 Parties prerequisite, UJ-1.
- **Quoted:** FR-3: "a Module whose identifiers are not ULIDs (Tenants, whose tenant identifier `system` is a plain string) declares `String`"; §8.1 Parties: "`aggregateIdProperty = PartyId`".
- **Note:** `references/Hexalith.Parties/src/Hexalith.Parties.Contracts/ValueObjects/PartyIdentifier.cs` `IsValid` accepts any alphanumeric string with `.`, `_`, `-` up to 128 characters plus bracketed legacy GUID forms; nothing in Parties requires a ULID. So Parties must also declare `String`, and the `Ulid` kind is exercised in v1 only by the sample fixture (`sample-ulid`). The PRD reads as if Tenants is the exception. Separately, the Gateway applies its own aggregate-identifier pattern (`SubmitQueryRequestValidator.cs:41` and the command validator: alphanumeric, dots, hyphens, underscores), which a `String`-kind "non-empty" check does not pre-validate; that is acceptable because FR-11 surfaces the Gateway rejection, but the PRD should say so to stop a story writer from inventing a stricter local rule.
- **Fix:** FR-3: "today both v1 Modules declare `String` (Tenants: `system`; Parties: `PartyIdentifier.IsValid`)"; §8.1 Parties: add "declare `IdentifierKind = String`"; FR-15: add "the tool does not replicate the Gateway's aggregate-identifier character rules; a Gateway rejection is returned per FR-11".

#### M-4. §8.1 Tenants prerequisite still requires `aggregateIdProperty` on Query attributes after FR-2 made it optional

- **Location:** PRD §8.1 Tenants; FR-2 consequence 1.
- **Quoted:** §8.1: "`projectionActorType` and `aggregateIdProperty` on Query attributes"; FR-2: "`aggregateIdProperty` is optional for any Query".
- **Note:** A self-contradiction introduced by the amendment: the rule was updated in FR-2 and §5.1 but not in the prerequisite that module authors will actually read. Combined with C-1, the correct prerequisite is "`aggregateIdProperty` on aggregate-scoped Queries (`GetTenantQuery`, `GetTenantUsersQuery`, `GetTenantAuditQuery`); a constant aggregate identifier on list-style Queries".
- **Fix:** Rewrite the Tenants bullet as above once C-1 lands.

#### M-5. Addendum §E is normative for FR-9 and FR-12 but the addendum disclaims requirement status; two addendum cross-references dangle

- **Location:** PRD FR-9, FR-12; addendum preamble, §D last paragraph, §F bullet 2.
- **Quoted:** FR-9: "their arguments are defined by the argument table in `addendum.md` §E, which both Heads implement"; addendum preamble: "Material that informs the PRD but belongs to architecture, solution design, or implementation rather than to the requirements themselves"; addendum §D: "Hence the 'Gateway-ready' prerequisite in PRD §4.8 and §9.1"; §F: "(PRD §9.2)".
- **Note:** The PRD has no §4.8, §9.1, or §9.2 (§4 is Constraints, §8 is MVP Scope with 8.1/8.2/8.3, §9 is Success Metrics); the numbers predate the polish pass that moved constraints before features (memlog 2026-09-21, "constraints moved before features"). The §E table is the acceptance source for two FRs and for the spine's AD-5 kebab-case test, so its status must be stated.
- **Fix:** Add one line to the addendum preamble: "§E is normative; FR-9 and FR-12 are accepted against it." Replace "§4.8 and §9.1" with "§4 and §8.1" and "§9.2" with "§8.2".

#### M-6. UJ-1 and NFR-1 still assume Projects is in v1

- **Location:** PRD UJ-1, NFR-1, SM-2.
- **Quoted:** UJ-1: "She asks the agent to create a party and then a project owned by it"; NFR-1: "The Catalog for four Modules builds in under 500 ms".
- **Note:** After the FR-20 amendment, v1 references only Tenants and Parties; Projects arrives when `Hexalith.Projects.Contracts` is slimmed (verified: `references/Hexalith.Projects/src/Hexalith.Projects.Contracts/Hexalith.Projects.Contracts.csproj` references `Microsoft.AspNetCore.App`, `Fluxor.Blazor.Web`, `Microsoft.FluentUI.AspNetCore.Components`, `Hexalith.FrontComposer.Shell`, `Hexalith.Conversations.Contracts`). The headline journey and the startup benchmark cannot be exercised as written in v1; SM-2 needs a Tenants-plus-Parties task (for example create a tenant, add a user, create a party).
- **Fix:** Rewrite UJ-1's task over Tenants and Parties; state NFR-1 as "the v1 Modules plus the two sample Modules" or keep "four" and say it is measured with the sample fixture.

#### M-7. FR-20 "covered end to end" has no observable definition in the PRD

- **Location:** PRD FR-20, §8 lead sentence.
- **Quoted:** "v1 is done when the tool is released and Tenants and Parties are covered end to end."
- **Note:** The spine defines it (AD-16: every Operation in `list_operations` for both Modules accepted by the Gateway in the Aspire harness, with AD-5 equality across heads), but the PRD, which owns the v1 gate, does not. A story writer cannot write the closing acceptance test from the PRD alone.
- **Fix:** Add a FR-20 consequence: "Covered end to end means: for every Operation of the Module in `list_operations`, both Heads submit it against a running EventStore in the test harness, the Gateway accepts it, and the two Heads' documents are equal (NFR-7, SM-4)."

#### M-8. FR-6 category list is presented as exhaustive but misses `no_operations`, which FR-20 relies on

- **Location:** PRD FR-6 consequence 1; FR-20 consequence 2; spine AD-4 and the diagnostics convention.
- **Quoted:** FR-6: "Warning categories (type kept): conflicting attribute value, undescribed property"; FR-20: "A referenced Module that is not yet Gateway-ready appears in `list_modules` with zero Operations and a startup diagnostic".
- **Note:** The FR-20 diagnostic is the spine's `no_operations` warning on a marked assembly with zero decorated types; FR-6 does not list it, and its subject is an assembly, not a type, so "type kept" does not describe it. A story writer implementing FR-6 from its list would not emit the diagnostic FR-20 tests for.
- **Fix:** Add "empty Module (assembly kept, listed with zero Operations)" to the FR-6 warning list.

### Low

#### L-1. NFR-7's `[ASSUMPTION]` is resolved by the spine but still tagged and indexed

- **Location:** PRD NFR-7, §11.
- **Quoted:** "`[ASSUMPTION: architecture picks the harness, Aspire or a container.]`"
- **Note:** Spine AD-16 picked Aspire (`tests/Hexalith.McpCli.AppHost`, `Aspire.AppHost.Sdk/13.5.4`). The tag says the decision belongs to architecture, and architecture has decided.
- **Fix:** Replace the tag with "(harness: Aspire, per the architecture spine AD-16)" and remove NFR-7 from §11.

#### L-2. Addendum §B tells the reader to copy the admin MCP's static tool classes, which the spine forbids

- **Location:** Addendum §B bullets 3 and 8; spine AD-12.
- **Quoted:** §B: "Stdio host pattern to copy: `Hexalith.EventStore.Admin.Mcp` (static `[McpServerToolType]` classes, logging forced to stderr)"; AD-12: "Prevents: static `[McpServerToolType]` classes that cannot honor Read-only Mode".
- **Note:** Verified: `references/Hexalith.EventStore/src/Hexalith.EventStore.Admin.Mcp/Program.cs` uses `WithToolsFromAssembly()` over ten static tool classes and `LogToStandardErrorThreshold = LogLevel.Trace`. The logging half is the pattern to copy; the tool-registration half is not, as §B's own SDK bullet already says.
- **Fix:** Reword to "logging pattern to copy (stderr threshold); tool registration is runtime `McpServerTool.Create` per the SDK note below".

#### L-3. Addendum §C repeats three paragraphs verbatim

- **Location:** Addendum §C, lines 88-107 and 108-125.
- **Quoted:** "`Hexalith.FrontComposer.Mcp` is a prior generic, descriptor-driven MCP host" (twice); "CLI + MCP sharing one catalog: Azure `azmcp`" (twice); "Landscape research for this PRD" (twice, once as bullets, once as prose).
- **Note:** Left over from the polish pass ("landscape bullet split", memlog 2026-09-21). Harmless but doubles the section.
- **Fix:** Delete the prose duplicate (lines 108-125).

#### L-4. Duplicate Module Name: FR-3 says startup error, FR-6 says an excluded type

- **Location:** PRD FR-3 consequence 2; FR-6 consequence 1.
- **Quoted:** FR-3: "Two assemblies declaring the same Module Name is a startup error"; FR-6: "Error categories (type excluded): ... duplicate Module Name".
- **Note:** The subject is an assembly, not a type, and "startup error" reads as process failure, which FR-6 reserves for an empty Catalog or `--strict`. Which assembly wins, or whether both are dropped, is undefined.
- **Fix:** Pick one: "the second assembly in manifest order is excluded with `duplicate_module_name`; the first is kept" and say it in FR-6 only.

#### L-5. Glossary "Routing Values" still names an aggregate identifier property

- **Location:** PRD §3 Routing Values.
- **Quoted:** "domain, Wire Type, aggregate identifier property, and, for Queries, projection type and projection actor type".
- **Note:** After AD-19 an interface-routed Command has no aggregate identifier property; it has an accessor over the contract getter. With C-1 a Query may have a constant.
- **Fix:** "aggregate identifier source (a Payload property, the contract getter, or a constant)".

#### L-6. FR-6 lists `mcp` among the verbs that need the Catalog; the spine exempts `mcp --transport http`

- **Location:** PRD FR-6 consequence 2, FR-12 consequence 3; spine AD-3.
- **Quoted:** FR-6: "fails only the verbs that need it (the discovery verbs, `send`, `query`, and `mcp`)"; AD-3: "`config`, `--version`, and `mcp --transport http` never touch it".
- **Note:** Only matters for which error wins when both apply; the spine's answer (`unsupported_transport` before any Catalog build) is the useful one.
- **Fix:** FR-6: "and `mcp` over stdio"; FR-12: "exits 2 with `code: unsupported_transport` before building the Catalog".

#### L-7. Minor story-writer friction

- **Location:** PRD §5.5/§5.6 ordering; FR-11 consequence 3; FR-16.
- **Quoted:** FR-11: "up to three nearest Operation Names"; FR-16 lead sentence lists five concerns.
- **Note:** FR-18 sits after FR-19 in reading order (ids are stable, so no action beyond a note). "Nearest" has no metric; the spine does not fix one either, so the story must. FR-16 bundles message identifier, idempotency key, Tenant, correlation and extensions pass-through, and aggregate-identifier resolution; each consequence is separately testable, so it splits cleanly into three stories (identifiers and idempotency; Tenant and envelope-filled properties; aggregate identifier), which the epics writer should do rather than treat FR-16 as one story.
- **Fix:** Add "nearest by case-insensitive edit distance over Operation Names" to FR-11; add a one-line "suggested split" note to FR-16 or leave it to the epics writer.

## Question 1: amendment fidelity

Every bullet of the spine's "PRD Amendments" landed:

| Spine amendment | PRD landing | Status |
| --- | --- | --- |
| FR-7 and §3 (AD-8): explicit marking and Identifier Kind; value-object converter; ULID rule narrowed to Envelope identifiers | §3 Identifier and Identifier Kind terms; §4 Identifiers; FR-7 bullets 2-4 | Complete |
| FR-3 (AD-8): marker gains Identifier Kind | FR-3 lead sentence and consequence 3 | Complete |
| §5.1 and FR-2 (AD-19): `aggregateIdProperty` optional for Query and interface-routed Command | §5.1 row; FR-2 consequence 1 | Complete in FR-2 and §5.1; §8.1 Tenants not updated (M-4) |
| FR-16 (AD-19): accessor compiled once | FR-16 consequence 2 | Complete |
| FR-20 (AD-15): closure rule; Tenants and Parties today; Projects slimming prerequisite | §4, FR-20, §8.1 Projects | Landed in a different form: PRD's "no other Hexalith package" is stricter than AD-15's allowlist, and both wordings fail on `Hexalith.Commons.UniqueIds` (H-1) |
| FR-6 and FR-14 (AD-3): empty Catalog fails only Catalog verbs | FR-6 consequence 2; FR-14 row 2 | Complete; `mcp --transport http` nuance missing (L-6) |
| FR-13 (AD-13): `EVENTSTORE_STRICT` | FR-13 lead and consequence 3; addendum §E | Complete |
| Resolved OQ-2, OQ-4, OQ-7 | §10 items 2, 4, 7 and preamble; FR-1; §3; §7; addendum §B | Complete |

Spine decisions that change PRD behavior but were not listed under PRD Amendments and did not land: AD-7 removal of computed get-only members (M-1); AD-20 Envelope-only paging and the `unmarked_paging_member` lint (M-2); the `no_operations` diagnostic (M-8).

PRD changes not traceable to the amendments list, all traceable elsewhere: FR-4 lint extension (spine lint convention `unmarked_identifier`, memlog 2026-09-22); FR-14 "missing configuration" (spine error code `configuration_missing`); addendum §D pointer fix "Open Question 4" to FR-22/FR-21 (memlog: stale since the reviewer gate, not a spine change; correct housekeeping). No untraceable change found.

## Question 2: consistency

PRD versus spine: H-1 (closure rule wording), H-2 (query correlation and extensions), H-3 (Tenants projection actor), M-1, M-2, M-8, L-2, L-6. Naming, package names (`Hexalith.McpCli`, `Hexalith.McpCli.Abstractions`, command `hexalith`), layout, analyzer packaging, tenant handling (envelope-only, non-empty string, never ULID-validated), idempotency (one key per call, caller-supplied or generated, never retried, `idempotentHint: false`), transport (stdio only, `--transport http` exits 2), identity (token owner, HTTP next release), and scope (§8.2 and the spine's Deferred list) agree.

PRD versus itself after the amendment: M-4 (§8.1 Tenants versus FR-2), M-6 (UJ-1 and NFR-1 versus FR-20), L-4 (FR-3 versus FR-6), L-5 (glossary versus FR-16). The §11 index matches the body exactly: tags exist at FR-13 (three), FR-16, FR-18, NFR-1, NFR-2, NFR-7, §7, SM-6 and nowhere else; the FR-1 removal is correct. NFR-7's tag is now stale in substance (L-1). Open questions: §10 and the memlog agree that OQ-1, OQ-3, OQ-5, OQ-6 remain open and OQ-2, OQ-4, OQ-7 are resolved; no question is resolved in the memlog but still listed open or vice versa. The spine attached a second question to OQ-3 (whether the Gateway reads `AdditionalProperties`) that the PRD's OQ-3 text does not carry; source answers it (H-2).

## Question 3: downstream usability

Stories can be derived independently for FR-1 to FR-15, FR-17 to FR-19, and FR-21 to FR-22; each has a testable consequence and a stable id. Blockers and friction:

- FR-16 and FR-20 cannot be closed as written (C-1, H-1, H-2, M-7).
- FR-9 and FR-12 are accepted against addendum §E, whose status is disclaimed (M-5).
- FR-6's category list is incomplete relative to what FR-20 tests (M-8).
- FR-16 is a bundle of five concerns; suggested split in L-7.
- FR-3 versus FR-6 duplicate-Module handling is ambiguous (L-4); FR-11 "nearest" is unspecified (L-7).
- FR-22 closes on an upstream merge in Hexalith.AI.Tools; the epic must mark it as an external dependency.
- Dangling references: addendum §D "PRD §4.8 and §9.1" and §F "PRD §9.2" (M-5). All FR ids FR-1 to FR-22, NFR-1 to NFR-8, SM-1 to SM-7, SM-C1 to SM-C4, and OQ-1 to OQ-7 resolve; the spine's `binds` list matches. No dangling FR id found in the PRD body.

## Question 4: remaining open questions

| OQ | Blocks architecture? | Blocks epics? | Spine answers de facto? |
| --- | --- | --- | --- |
| OQ-1 HTTP authentication | No. AD-10 fixes the seam (`EnvelopeContext.UserId`, auth handler inside the gateway client builder callback, `unsupported_transport` until then). | No v1 epic; blocks only the HTTP-release story. | Partly: the seam and the error code are decided; issuer, validation, and header forwarding are not, and the PRD correctly leaves them open. |
| OQ-3 aggregate-less Queries | Yes for AD-19, which rests on a falsified assumption. | Yes: the executor story and the Tenants end-to-end half of the v1 gate (C-1). | Yes, wrongly: AD-19 sends `string.Empty`, which `SubmitQueryRequestValidator.cs:37-39` rejects. Source gives the real answer (a per-operation constant, as Parties' `"parties"` and the Rest `RestQueryBindingSource.Constant` binding). Resolve in the PRD now; the EventStore owner only needs to confirm the reading. |
| OQ-5 Parties routing | No. FR-2's per-field precedence supports both paths; AD-19 handles both. | Not this repository's epics; blocks the upstream Parties decoration epic and therefore the Parties half of the v1 gate. | No. The spine pins "first decorated release (≥ 1.1.1)" and composes Parties in the AppHost, neutral on routing. Verified today's values match the PRD: `PartyDomain = "party"`, `CommandType: typeof(TCommand).FullName` (`HttpPartiesCommandClient.cs:21,174`). |
| OQ-6 deletion order | No. | No v1 epic; blocks only the content of the FR-21 plan. | No, and FR-21 already fixes the two hard constraints (FrontComposer plus Projects together; Memories after the HTTP release). |

## Checked claims

| # | Claim (PRD or addendum location) | Verdict | Source file |
| --- | --- | --- | --- |
| 1 | `SubmitCommandRequest(MessageId, Tenant, Domain, AggregateId, CommandType, JsonElement Payload, CorrelationId?, Extensions?, IdempotencyKey?)` (addendum §B) | Accurate | `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Commands/SubmitCommandRequest.cs` |
| 2 | `SubmitQueryRequest(Tenant, Domain, AggregateId, QueryType, ProjectionType?, Payload?, EntityId?, ProjectionActorType?)` plus `Paging`, `Search`, `Filters`, `OrderBy`, `Freshness` (addendum §B, §F) | Accurate; also has `[JsonExtensionData] AdditionalProperties`, not mentioned | `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Queries/SubmitQueryRequest.cs` |
| 3 | `ICommandContract` supplies static `CommandType`, static `Domain`, instance `AggregateId` getter (FR-2, FR-16, AD-19) | Accurate | `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Commands/ICommandContract.cs` |
| 4 | `IQueryContract` supplies `QueryType`, `Domain`, `ProjectionType` and "does not carry" projection actor type (§5.1) | Accurate | `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Queries/IQueryContract.cs` |
| 5 | Tenants is the only v1 Module implementing the contract interfaces; Projects uses an instance `CommandType => nameof(...)` (addendum §D) | Accurate | `references/Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Commands/*.cs`; `references/Hexalith.Projects/src/Hexalith.Projects.Contracts/Commands/UnlinkFileReference.cs:32` |
| 6 | Tenants Wire Type is kebab-case (`create-tenant`) (§3 Wire Type) | Accurate | `references/Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Commands/CreateTenant.cs` |
| 7 | Tenants tenant identifier `system` is a plain string, not a ULID (FR-3) | Accurate | `references/Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Identity/TenantIdentity.cs:6` |
| 8 | Tenants routes global-administrator Commands to a second domain (FR-2) | Accurate (`global-administrators`) | `references/Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Commands/SetGlobalAdministrator.cs`; `Identity/TenantIdentity.cs:15` |
| 9 | Tenants Queries carry `Cursor` and `PageSize` Payload members (§8.1) | Accurate | `references/Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Queries/GetTenantUsersQuery.cs`, `ListTenantsQuery.cs` |
| 10 | Tenants "has its own projection actor", so its Queries need `projectionActorType` (§5.1, FR-2, §8.1) | Inaccurate: actor retired, no `ProjectionActorType` reference in Tenants | `references/Hexalith.Tenants/src/Hexalith.Tenants/Queries/Handlers/TenantQueryHandlerBase.cs:21-25` |
| 11 | Parties: `domain = "party"`, Wire Type is the full CLR type name (§8.1, §3) | Accurate | `references/Hexalith.Parties/src/Hexalith.Parties.Client/HttpPartiesCommandClient.cs:21,174` |
| 12 | Parties has no Query types in its Contracts Library (§8.1) | Accurate (Commands, Events, Models, Results, ValueObjects; no Queries) | `references/Hexalith.Parties/src/Hexalith.Parties.Contracts/` |
| 13 | `Hexalith.Parties.Mcp` reaches the Gateway but hand-rolls HTTP instead of `IEventStoreGatewayClient` (addendum §D) | Accurate | `references/Hexalith.Parties/src/Hexalith.Parties.Mcp/Program.cs:24-59` |
| 14 | `McpContextForwardingHandler` forwards bearer token, `X-Tenant-Id`, `X-User-Id` (addendum §B) | Accurate | `references/Hexalith.Parties/src/Hexalith.Parties.Mcp/McpContextForwardingHandler.cs` |
| 15 | Zero `[Description]` attributes in the four v1 Contracts Libraries (addendum §D) | Accurate (0 files in each) | `references/Hexalith.{Tenants,Parties,Projects,Folders}/src/*.Contracts/` |
| 16 | `EventStoreGatewayException` exposes status, reason code, detail, retryable, retry-after, client action, correlation identifier (FR-11, §F) | Accurate | `references/Hexalith.EventStore/src/Hexalith.EventStore.Client/Gateway/EventStoreGatewayException.cs` |
| 17 | Client has `GetCommandStatusAsync`; `SubmitQueryAsync` takes `ifNoneMatch`; `EventStoreQueryResult` has `ETag`, `IsNotModified`, `Payload`, `Metadata` (§F) | Accurate | `references/Hexalith.EventStore/src/Hexalith.EventStore.Client/Gateway/IEventStoreGatewayClient.cs`, `EventStoreQueryResult.cs` |
| 18 | Paging result fields page size, offset, next cursor, total count, has-more (FR-17) | Accurate | `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Queries/QueryPagingMetadata.cs`; `QueryResponseMetadata.cs` (`Paging`) |
| 19 | `ConnectionProfile(Url, Token, Format)` has no extension-data member; `ProfileManager.Save` rewrites the whole file; path `~/.eventstore/profiles.json` with `version` and `activeProfile` (addendum §B, §E) | Accurate | `references/Hexalith.EventStore/src/Hexalith.EventStore.Admin.Cli/Profiles/ConnectionProfile.cs`, `ProfileManager.cs:45,95-107`, `ProfileStore.cs` |
| 20 | Admin CLI exit codes 0/1/2 (addendum §B, FR-14) | Accurate (`Success=0`, `Degraded=1`, `Error=2`) | `references/Hexalith.EventStore/src/Hexalith.EventStore.Admin.Cli/ExitCodes.cs` |
| 21 | Admin CLI globals `--url --token --format --output --profile`; env prefix `EVENTSTORE_ADMIN_` (FR-13) | Accurate | `references/Hexalith.EventStore/src/Hexalith.EventStore.Admin.Cli/GlobalOptionsBinding.cs` |
| 22 | Admin CLI has `config use`, `config current`, `config profile list|add|remove` (FR-18) | Accurate | `references/Hexalith.EventStore/src/Hexalith.EventStore.Admin.Cli/Commands/Config/` |
| 23 | Admin MCP logs to stderr only, stdio transport, static `[McpServerToolType]` classes (addendum §B) | Accurate | `references/Hexalith.EventStore/src/Hexalith.EventStore.Admin.Mcp/Program.cs`, `Tools/*.cs` |
| 24 | `Hexalith.Projects.Contracts` carries web framework and UI packages (FR-20, §8.1) | Accurate (`Microsoft.AspNetCore.App`, `Fluxor.Blazor.Web`, `Microsoft.FluentUI.AspNetCore.Components`, `Hexalith.FrontComposer.Shell`, `Hexalith.Conversations.Contracts`) | `references/Hexalith.Projects/src/Hexalith.Projects.Contracts/Hexalith.Projects.Contracts.csproj` |
| 25 | `Hexalith.Folders.Contracts` holds OpenAPI YAML and read models only (§8.1, addendum §D) | Accurate | `references/Hexalith.Folders/src/Hexalith.Folders.Contracts/` |
| 26 | Tenants and Parties Contracts "satisfy the closure rule" today (FR-20, §4) | Inaccurate under either wording: their closure includes `Hexalith.Commons.UniqueIds` through `Hexalith.EventStore.Contracts` | `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Hexalith.EventStore.Contracts.csproj`; `Hexalith.Tenants.Contracts.csproj`; `Hexalith.Parties.Contracts.csproj` |
| 27 | `run_query` passes a caller correlation identifier and extensions through (FR-16, §E; spine AD-9) | Inaccurate: no such members; `AdditionalProperties` rejected; correlation comes from the `X-Correlation-ID` header, which the client never sets | `SubmitQueryRequestValidator.cs:142-145`; `Controllers/QueriesController.cs:50`; `Middleware/CorrelationIdMiddleware.cs:8-28`; `Client/Gateway/EventStoreGatewayClient.cs` (all under `references/Hexalith.EventStore/src/`) |
| 28 | `send_command` correlation identifier and extensions are honored by the Gateway (FR-16, FR-17) | Accurate (`CorrelationId` defaults to `MessageId`; extensions sanitized) | `references/Hexalith.EventStore/src/Hexalith.EventStore/Controllers/CommandsController.cs:91-143` |
| 29 | A Query with no aggregate identifier can send an empty one (FR-16 assumption, AD-19) | Inaccurate: Gateway rejects empty; sibling clients send a constant | `SubmitQueryRequestValidator.cs:37-42`; `references/Hexalith.Parties/src/Hexalith.Parties.Client/HttpPartiesQueryClient.cs:22,95-99`; `QueriesController.cs:79-81` |
| 30 | Parties party identifiers are ULIDs (implied by the pre-amendment §4 and by `aggregateIdProperty = PartyId` with no kind stated) | Inaccurate: `PartyIdentifier.IsValid` accepts alphanumeric plus `.`, `_`, `-` up to 128 characters and legacy GUID forms; Parties must declare `String` | `references/Hexalith.Parties/src/Hexalith.Parties.Contracts/ValueObjects/PartyIdentifier.cs` |
| 31 | `AddEventStoreGatewayClient` returns an `IHttpClientBuilder` the composition root can extend with a handler (spine AD-10, PRD §4 identity) | Accurate | `references/Hexalith.EventStore/src/Hexalith.EventStore.Client/Registration/EventStoreServiceCollectionExtensions.cs:29` |
| 32 | The Rest layer already expresses a constant aggregate identifier per Query (evidence for the C-1 fix) | Accurate (`RestQueryBindingSource.Constant`) | `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Rest/RestQueryBindingAttribute.cs`; `references/Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Queries/GetGlobalAdministratorsQuery.cs` |
