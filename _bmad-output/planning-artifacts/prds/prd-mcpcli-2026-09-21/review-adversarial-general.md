---
title: "Adversarial Review: Hexalith.McpCli PRD"
status: final
created: 2026-09-22
reviewed: prd.md (updated 2026-09-22), addendum.md (updated 2026-09-22)
---

# Adversarial Review: Hexalith.McpCli PRD

## Verdict

The PRD is well-structured and most of its mechanism is decided, but it is built on a tenancy model that the flagship v1 module does not follow, a dependency rule that excludes the two modules it names, and a read path that no existing code exercises. Tenants runs every command and query under the fixed envelope tenant `system` and demands a `system` tenant claim on the token; the PRD's one-default-tenant-per-profile model, its claim that global-administrator queries are tenant-less, and its FR-3 rationale are all wrong against the source. The closure rule in §4 forbids "any other Hexalith package" while `Hexalith.EventStore.Contracts` itself depends on `Hexalith.Commons.UniqueIds`, so a CI test written from the PRD rejects Tenants and Parties on day one. No code in Tenants or Parties submits a `SubmitQueryRequest`, the gateway requires a non-empty aggregate identifier on every query, and the PRD carries an assumption that list queries send an empty one; `run_query` therefore has no proven path for either v1 module. On security, the PRD lets an agent set the envelope tenant per call, pass arbitrary extensions, and write identity-bearing payload properties (`ActorPrincipalId`), which together are an impersonation path the guardrails do not cover. Six months out, the most likely failure is a tool that can write but not read, holds a platform-administrator token on a developer laptop, and exposes a Catalog whose upstream decoration work nobody scheduled. Ship only after the critical findings are resolved; the high findings should be decided before stories are cut.

Findings: 4 critical, 11 high, 12 medium, 6 low. Prior reviews (`review-rubric.md`, `review-downstream.md`) are not repeated where the rewrite fixed them; where a fix was partial, the residue is called out.

---

## Critical

### C-1. Tenants runs under the fixed envelope tenant `system`; the PRD's tenant model cannot drive it
**Location:** §3 "Tenant", §4 "Tenant", FR-3 consequence 3, FR-13 consequence 4, FR-18, UJ-1, UJ-2.
**Quoted:** "a Module whose identifiers are not ULIDs (Tenants, whose tenant identifier `system` is a plain string) declares `String`" (FR-3); "the only tenant-less Queries are the global-administrator ones, which are not decorated in v1" (FR-13); "sets its default Tenant" (UJ-1).
**Why it is a problem:** In `references/Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Identity/TenantIdentity.cs`, `ForTenant(managedTenantId) => new(DefaultTenantId /* "system" */, Domain, managedTenantId)`: every Tenants command and query travels with envelope `Tenant = "system"` and the managed tenant id as the *aggregate id*. `Hexalith.Tenants/Authorization/TenantsSystemTenantValidator.cs` rejects any tenant other than `system` and requires a `system` tenant claim on the token; `Validation/TenantSubmitCommandValidator.cs` line 43 rejects global-administrator commands whose `Tenant` is not `system`; `Queries/Handlers/GetGlobalAdministratorsQueryHandler.cs` returns `Forbidden` unless `envelope.TenantId == "system"`. Consequences: (a) FR-13's "tenant-less" claim is false; the global-administrator operations are the most tenant-bound ones. (b) FR-3's rationale conflates the envelope tenant (which §4 says is never ULID-validated anyway) with the Identifier Kind of payload identifiers; the sentence gives a module author the wrong reason to pick `String`. (c) UJ-1 and UJ-2 cannot both run in one session with one profile default tenant: `parties.*` needs Nadia's tenant, `tenants.*` needs `system`. The agent must know to pass `tenant: "system"` on every Tenants call, and nothing in `describe_operation` tells it. (d) A token that carries the `system` claim is a platform-administrator token; UJ-1 hands it to an agent session on a laptop (see C-3).
**Fix:** Add a Module marker member `fixedTenant` (or an Operation attribute member `tenant`) that the Catalog surfaces in `describe_operation` as an Envelope argument default and that the executor uses when no per-call tenant is given; make a per-call tenant that differs from a fixed tenant `validation_failed`. Rewrite FR-3 consequence 3 to cite a real non-ULID aggregate id (the managed tenant id, or the constant `global-administrators`). Delete the "tenant-less" sentence from FR-13. Add to §8.1 Tenants prerequisites: "every Tenants Operation declares `fixedTenant = system`; operators need a token carrying `eventstore:tenant = system`."

### C-2. The closure rule as written excludes Tenants and Parties
**Location:** §4 "Dependency policy", FR-20, §8.1 Projects prerequisite; addendum §B; CLAUDE.md "Only two kinds of Hexalith dependency".
**Quoted:** "A Contracts Library is referenced only when its transitive closure contains no other Hexalith package and no framework reference beyond the base runtime (the closure rule, enforced by a CI test over the restored dependency graph; FR-20)".
**Why it is a problem:** `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Hexalith.EventStore.Contracts.csproj` has `<PackageReference Include="Hexalith.Commons.UniqueIds" />` in package mode, and that package references `ByteAether.Ulid`. So the transitive closure of *every* Contracts Library, including `Hexalith.Tenants.Contracts` and `Hexalith.Parties.Contracts`, contains a Hexalith package that is neither a `*.Contracts` package nor an `Hexalith.EventStore.*` package. The spine's AD-15 wording ("no Hexalith package other than `*.Contracts` packages and `Hexalith.EventStore.*` contract packages") has the same hole. A CI test written from either text fails on the first restore, and the first story will "fix" it by loosening the rule ad hoc, which is exactly how `Hexalith.Projects.Contracts` grew `Fluxor` and `FluentUI`. Separately, `Hexalith.Parties.Contracts` already ships service interfaces (`Security/IPartyKeyLifecycleService.cs`, `IKeyStorageBackend.cs`, `ITenantKeyRotationService.cs`) and `PartiesJsonOptions.cs`; "Contracts" is a package name, not a purity guarantee.
**Fix:** Replace the prose rule with an explicit allowlist in the PRD: "the closure may contain `Hexalith.EventStore.Contracts` and its own transitive closure at the pinned version (today `Hexalith.Commons.UniqueIds`, `ByteAether.Ulid`), other `*.Contracts` packages, and nothing else Hexalith; framework references limited to `Microsoft.NETCore.App`." State that additions to the allowlist are a PRD change, not a test change. Update CLAUDE.md's policy line to match.

### C-3. Identity can be set by the caller three ways; the tenant guardrail does not cover any of them
**Location:** §4 "Tenant", FR-9 argument table (`tenant`, `extensions`), FR-16, FR-21 consequence 2, §8.1 Projects prerequisite.
**Quoted:** "passes a caller-supplied correlation identifier and extensions through" (FR-16); "Task and actor context that Projects and ChatBot carry today travels as ordinary Payload properties or in Envelope extensions" (FR-21); "decide whether the server-side tenant guard in the Projects command submitter moves into the aggregate, since direct Gateway submission bypasses it" (§8.1).
**Why it is a problem:** Three paths. (1) **Per-call tenant.** The `tenant` tool argument is supplied by the LLM, the same untrusted channel as the payload. The gateway's `ClaimsTenantValidator` only checks that the token's `eventstore:tenant` claims include the requested tenant; a token with several claims lets the agent hop tenants per call with no operator consent. CLAUDE.md lists "profile, flag, or forwarded header" as tenant sources; the PRD silently added a fourth that the model controls. (2) **Identity in the payload.** `Hexalith.Projects.Contracts/Commands/IProjectCommand.cs` declares `string ActorPrincipalId`; FR-21 says actor context "travels as ordinary Payload properties". FR-7 puts every declared property in the Schema, so `send_command` lets the agent name any principal as the actor, and the audit trail records whatever it chose. The PRD notices the Projects tenant guard is bypassed and hands the decision to the Projects maintainer instead of closing it. (3) **Extensions.** The gateway has `ITrustedCommandExtensionPolicy` (`Hexalith.EventStore/Authorization/`) precisely because some extension keys carry trusted metadata; the PRD passes any `--extension key=value` through with no allowlist, relying on the gateway to reject reserved keys per policy. Where no policy claims a key, it is stored as trusted.
**Fix:** (1) Per-call `tenant` is honored only when the profile has no default tenant or the operator sets `--allow-tenant-override`; otherwise it is `validation_failed`. (2) Add `actorProperty` (or `userProperty`) to the Decoration Attribute table, filled by the executor from the session identity (v1: a fixed string naming the token owner or "mcpcli"; HTTP release: the forwarded user), marked `readOnly`, and add to §4: "no Payload property may carry a caller-chosen identity". (3) Extensions the caller may supply are an allowlist on the Operation attribute (`allowedExtensions`), empty by default. Record the Projects tenant-guard question as a blocker in OQ, owned by this PRD, not a maintainer's choice.

### C-4. `run_query` has no proven path for either v1 module, and the PRD's fallback is rejected by the gateway
**Location:** FR-16 assumption, OQ-3, §5.1 table (`projectionActorType`), §8.1 Tenants and Parties prerequisites, FR-20 "covered end to end".
**Quoted:** "[ASSUMPTION: a Query with none sends an empty aggregate identifier pending OQ-3.]"; "`projectionActorType` ... Module has its own projection actor (Tenants)".
**Why it is a problem:** `Hexalith.EventStore/Validation/SubmitQueryRequestValidator.cs` lines 37-39: `AggregateId` `NotNull().NotEmpty()`. `QueriesController.cs` line 78-81 routes the read to `AggregateId` when `EntityId` is omitted. An empty aggregate identifier is a 400 before any handler runs, so the FR-16 assumption ships a known failure for `tenants.list-tenants`, `tenants.get-user-tenants`, and every Parties list read. Further, no file under `references/Hexalith.Tenants/src` constructs a `SubmitQueryRequest`, and the string `ProjectionActorType` does not appear anywhere in Tenants source; the Tenants query handlers are reached today through `Hexalith.Tenants.Api` REST routes (`[RestRoute]` on every query class). The PRD's statement that Tenants "has its own projection actor" and needs `projectionActorType` is unverified, and the only module that reaches the gateway at all (Parties) has no query types. "Tenants and Parties covered end to end" therefore rests on a read path that nothing exercises.
**Fix:** Promote OQ-3 to a v1 blocker with a named owner and a spike deliverable: "`tenants.list-tenants` returns a page through `IEventStoreGatewayClient.SubmitQueryAsync` from a throwaway harness before FR-9/FR-16 stories are estimated." Add a `fixedAggregateId` attribute member for list-style queries (Tenants already uses the constant `global-administrators` for one aggregate). Replace the `projectionActorType` row's "Tenants" example with "verified with the EventStore owner; value TBD" until the spike lands.

---

## High

### H-1. Sharing `~/.eventstore/profiles.json` with the admin CLI makes one profile name unusable by both tools
**Location:** FR-18, §5.6 description, addendum §B and §E.
**Quoted:** "the tool reads URL, token, and format from `~/.eventstore/profiles.json`"; "`config use`, `config current`, and `config profile list|add|remove` behave as in the admin CLI".
**Why it is a problem:** A profile is `ConnectionProfile(Url, Token, Format)` (`Hexalith.EventStore.Admin.Cli/Profiles/ConnectionProfile.cs`). The admin CLI's `url` is the admin API (default `http://localhost:5002`, `EVENTSTORE_ADMIN_URL`); this tool's `url` is the gateway (spine: `http://localhost:8080`). The token is also a different credential (admin API token vs gateway JWT with `eventstore:tenant` claims). So a profile named `dev` cannot be correct for both tools; the operator ends up with `dev` and `dev-admin`, which defeats the "shared" rationale. Also, `Format` may be `csv` in an admin profile (`Formatting/CsvOutputFormatter.cs` exists) and this tool accepts `json|table` only; behavior is unspecified. And if this tool's `config profile add` writes the file, two writers with different typed models share one file (the PRD already noticed the lossy rewrite and moved the tenant out; it did not follow the thought through).
**Fix:** Make `~/.eventstore/mcpcli.json` the sole store for this tool (`url`, `token`, `format`, `tenant` per profile) and drop the "shared with the admin CLI" claim; or keep the shared file read-only and add `gatewayUrl`/`gatewayToken` to `mcpcli.json`, documenting that `profiles.json` supplies nothing but the active profile name. State what happens with an unknown `format` value.

### H-2. FR-14 exit code 1 fires for reasons unrelated to the invocation, and the migration period makes that the normal state
**Location:** FR-14 row 1, FR-6, UJ-3 edge case.
**Quoted:** "1 | Result document produced, and a diagnostic was written to stderr for this invocation (discovery verbs and `describe --lint` only ...)".
**Why it is a problem:** FR-6 writes every Catalog diagnostic at startup, for every verb. Is a startup diagnostic "for this invocation" of `hexalith modules`? Row 1 says discovery verbs get exit 1 when a diagnostic was written, so yes: while any upstream record lacks a description (UJ-3 calls this expected), every `modules` and `operations` call exits 1 and every `set -e` script breaks. The rubric review flagged this; the rewrite narrowed the verbs but not the trigger.
**Fix:** Exit 1 only when `describe --lint` finds a problem in the described Operation. Catalog diagnostics are stderr-only unless `--strict`, in which case they are exit 2 before any result. Say so in FR-6 and FR-14.

### H-3. The Schema is derived with the tool's serializer options, but Parties and Tenants ship their own converters
**Location:** FR-5 consequence 3, FR-7, FR-16 accessor, FR-1 consequence 3 (example validation).
**Quoted:** "JSON is written with the tool's canonical serializer options"; "The Catalog derives a Schema from the Operation type".
**Why it is a problem:** `Hexalith.Parties.Contracts/PartiesJsonOptions.cs` and `Hexalith.Tenants.Contracts/Serialization/TenantStatusJsonConverter.cs` exist because the wire encoding of those types depends on options, not only on attributes (enum-as-string versus integer, value-object shapes). If the Catalog derives the Schema and the executor validates the Payload with the tool's options, a Payload that validates may still be deserialized differently by the module's aggregate, or the `example` may validate here and be rejected there. FR-16's "accessor compiled once at startup" that reads `ICommandContract.AggregateId` requires deserializing the Payload into the CLR type with the *right* options, which the tool does not know. Nothing in the attribute table lets a Module name its options.
**Fix:** Either require in the Gateway-ready checklist that every decorated type is attribute-complete (`[JsonConverter]`, `[JsonStringEnumConverter]` at type level) so serialization is options-independent, and add a Catalog diagnostic when a property's converter comes from options; or add a Module marker member naming a static `JsonSerializerOptions` provider. Add a consequence to FR-1: "the example round-trips through the Schema and through the Gateway serializer with identical JSON".

### H-4. Nothing stops `tenantProperty` from naming the aggregate identifier, and on Tenants that is the natural mistake
**Location:** §5.1 table (`tenantProperty`), FR-16 consequence 3.
**Quoted:** "`tenantProperty` | both | record declares a tenant member | Payload property the executor fills from the Envelope Tenant"; "the properties named by `tenantProperty` ... are overwritten from the Envelope before submission".
**Why it is a problem:** Every Tenants command is `record X(string TenantId, ...) : ICommandContract { AggregateId => TenantId; }`. A maintainer reading "record declares a tenant member" sets `tenantProperty = nameof(TenantId)`. The executor then overwrites the managed tenant id with the envelope tenant `system` and the command targets aggregate `system`. The check "a Payload tenant value that differs from the Envelope Tenant is validation_failed" turns every Tenants command into a validation failure at best, and a wrong-aggregate write if the caller passes `system`. The PRD has no Catalog error for the overlap.
**Fix:** Add an FR-6 error category: "`tenantProperty` names the aggregate identifier source (via `aggregateIdProperty` or the `ICommandContract` getter)". Rename the "Required when" cell to "record declares a member that must equal the Envelope Tenant" and add a note that Tenants' `TenantId` is an aggregate id, not a tenant.

### H-5. Success metric SM-4 cannot pass as written, and several other acceptance statements are unobservable
**Location:** SM-4, FR-9 consequence 4, FR-11 consequence 3, NFR-1, NFR-8, SM-5, SM-6.
**Quoted:** "A test runs both Heads against one EventStore and gets identical Catalog data and results for every Operation" (SM-4); "Each tool description has three labeled parts" (FR-9); "up to three nearest Operation Names" (FR-11); "the CI runner class used for this repository" (NFR-1); "understandable by someone who has never seen the code" (NFR-8).
**Why it is a problem:** SM-4: Command results include a fresh message identifier and idempotency key per call (FR-16), so two submissions never produce identical results; "identical results for every Operation" is false by construction for writes, and for reads it depends on projection freshness between the two calls. FR-9: the three labels are not named, so two implementers will write different descriptions and the NFR-2 budget cannot be checked. FR-11: "nearest" by what metric, over which string? NFR-1: no runner class is named. NFR-8 and SM-5: "a reviewer who has never seen the code" is not a repeatable test; SM-C4's humanized-name lint is the only mechanical part. SM-6: 15 minutes "using only the README" is unmeasured and unowned.
**Fix:** SM-4: compare Catalog data and *error* documents for identical inputs, and for Commands compare the result shape with volatile fields masked. FR-9: name the labels ("Purpose:", "Use when:", "Then call:"). FR-11: "by Damerau-Levenshtein distance over the full Operation Name, ties broken alphabetically". NFR-1: name the runner (`ubuntu-latest`, per the spine). NFR-8: keep the lint, and make the review a checklist item in the Module's pull request (already in §8.1) rather than an NFR of this tool.

### H-6. The result document shapes are not specified anywhere, yet both Heads must agree on them
**Location:** FR-11, FR-17, FR-9 consequence 2, SM-4, addendum §E (inputs only).
**Quoted:** "Every tool returns structured content with a declared output schema"; "Command results include the message identifier and idempotency key used, plus the Gateway's correlation identifier".
**Why it is a problem:** The addendum §E table pins every *argument* spelling for both Heads; nothing pins the *result* field names, nesting, or the error document keys beyond `code`. `describe_operation` "returns description, kind, Schema, example, the Envelope arguments the caller may supply, and `submittable`" without a shape. The MCP output schema and the CLI JSON will drift on the first story, and SM-4 has nothing to compare against. §7 makes result shapes part of the versioned public surface ("result shapes"), so this is a public contract with no definition.
**Fix:** Add addendum §G: one JSON example per tool result and per error document, with field names, and state that both Heads serialize the same record types.

### H-7. `--format table` is required for every verb but undefined for nested JSON documents
**Location:** FR-13, FR-12, addendum §E "Global CLI options".
**Quoted:** "Every verb accepts ... `--format json|table`".
**Why it is a problem:** `send` returns a small flat record; `query` returns an arbitrary projection document with nested objects and arrays; `describe` returns a JSON Schema. A table rendering of these is a design task with no acceptance criteria, and the admin CLI's `TableOutputFormatter` is column-definition-driven, which presumes a known shape. The implementer will either invent a flattening or restrict `table` to discovery verbs; both are hidden decisions.
**Fix:** State: `table` applies to `modules`, `operations`, `config`; on `describe`, `send`, and `query` it is accepted and falls back to `json` with a stderr note, or is rejected with exit 2. Pick one.

### H-8. FR-20 and FR-3 disagree on what a referenced-but-undecorated Module looks like
**Location:** FR-3 consequence 1, FR-20 consequence 2.
**Quoted:** "The Catalog scans only assemblies carrying the marker; an undecorated assembly contributes nothing and produces no diagnostic" (FR-3); "A referenced Module that is not yet Gateway-ready appears in `list_modules` with zero Operations and a startup diagnostic" (FR-20).
**Why it is a problem:** A Module that is "not yet Gateway-ready" and has no marker is invisible by FR-3, but listed with a diagnostic by FR-20. A Module with a marker and no decorated types is listed by FR-20 but FR-6 has no "empty module" category. The downstream review raised this (1.12); the rewrite kept both sentences.
**Fix:** Define two states: unmarked assembly (invisible, no diagnostic) and marked assembly with zero exposed Operations (listed, warning category `empty_module`). Amend FR-6's category list and FR-20.

### H-9. The build-time assembly list generator has no rule for which package references are Contracts Libraries
**Location:** FR-5, addendum §B "Assembly enumeration".
**Quoted:** "the assembly list is generated at build time from the project's package references and never hand-maintained".
**Why it is a problem:** The tool's package references include `Hexalith.EventStore.Client`, `ModelContextProtocol`, `System.CommandLine`, and the Contracts Libraries. The generator runs before anything is loaded, so it cannot see the Module marker; it must decide by package name pattern (`*.Contracts`) or by an MSBuild item flag. A name pattern is a naming convention that also matches `Hexalith.EventStore.Contracts` (which carries no Module marker and must be scanned or skipped deliberately). This is a hidden choice with a zero-module-specific-code implication if someone hard-codes the list.
**Fix:** Specify the mechanism: a `HexalithContracts="true"` metadata on the `PackageReference` item, read by an MSBuild target that emits the scan list; a test that the list equals the set of flagged references.

### H-10. Upstream decoration work has no owner, date, or gate, and it is on the v1 critical path
**Location:** §8.1 Gateway-ready checklist, Tenants and Parties prerequisites, §7 release order, SM-1, SM-3.
**Quoted:** "Work is tracked in each Module's own repository"; "Query types do not exist; create one per read the Legacy Server exposes" (Parties); "v1 is done when the tool is released and Tenants and Parties are covered end to end".
**Why it is a problem:** v1 cannot be "done" until Tenants ships descriptions and examples on 12 commands and 6 queries, Parties ships attribute routing on 24 commands and *creates* a query surface that does not exist today (plus a projection actor to serve it), and both republish. None of that is in this repository, none has an owner beyond "the maintainer chooses (OQ-5)", and the closure rule (C-2) may force further upstream changes. The PRD's own release order says the Decoration Package must publish first, so the earliest upstream start is after story 2 here; the tool's integration tests (NFR-7, spine AD-16) need the decorated packages, so stories 3 to 5 cannot close end to end until upstream lands. The critical path runs through repositories this PRD does not control, and SM-1 additionally depends on Projects slimming and a Folders rewrite.
**Fix:** Add a §8.1 table: per Module, owner, target version, and the earliest tool release that can pin it; add to §8 a fallback: "if Parties queries are not published by <date>, v1 ships with Tenants only and `parties.*` writes." Add an assumption tag on the Parties projection actor (does one exist to serve gateway queries? no code found).

### H-11. The `Ulid` CLR-type rule and the Decoration Package's zero-dependency rule conflict
**Location:** FR-7 consequence 2, FR-1 consequence 4, §3 "Decoration Package".
**Quoted:** "A property whose CLR type is `Ulid` gets the pattern regardless of the kind"; "The Decoration Package has no package references".
**Why it is a problem:** There is no `Ulid` in the BCL. The Hexalith stack uses `ByteAether.Ulid` (via `Hexalith.Commons.UniqueIds`; spine pins 1.4.1). The tool can recognize the type only by full name string match, which is an unstated convention, and a Contracts Library that uses a different ULID library (Cysharp `Ulid`, `NUlid`) gets a plain-string schema silently. Meanwhile the analyzer packed into the same package needs `Microsoft.CodeAnalysis` as a private asset, which is a package reference in every practical sense.
**Fix:** Name the recognized type(s) by full name in FR-7 (`ByteAether.Ulid.Ulid`, plus any others) and state that others are plain strings unless marked. Reword FR-1: "the Decoration Package's runtime assembly has no dependencies; the packed analyzer's dependencies are private assets".

---

## Medium

### M-1. Tenants reads pagination from the Payload, not from Envelope `Paging`; the agent will see two paging models
**Location:** FR-17 consequence 2, addendum §E (`pageSize, offset, cursor`), §8.1 Tenants prerequisite.
**Quoted:** "Query results include the document and, when paging applies, page size, offset, next cursor, total count, and has-more"; "decide whether the `Cursor` and `PageSize` Payload members give way to Envelope paging".
**Why it is a problem:** `GetGlobalAdministratorsQueryHandler.cs` calls `DeserializePaginationPayload(envelope.Payload)`; `GetTenantUsersQuery` and `ListTenantsQuery` carry `Cursor` and `PageSize` as properties. The PRD's `run_query` paging arguments map to `SubmitQueryRequest.Paging`, which Tenants ignores. Until Tenants changes, an agent must put the cursor in the Payload for Tenants and in the arguments for everyone else, and `describe_operation` does not say which.
**Fix:** Add a `pagingProperties` attribute member (cursor, page size) so the executor maps the generic paging arguments into the Payload when declared and into Envelope `Paging` otherwise; mark those properties `readOnly` like the other envelope-filled ones.

### M-2. Parties Wire Types as full CLR type names are 24 hand-typed strings with no drift test
**Location:** §3 "Wire Type", FR-2, §8.1 Parties prerequisite, Gateway-ready checklist.
**Quoted:** "keep domain and Wire Type stable, because renaming either silently breaks the Catalog mapping".
**Why it is a problem:** Confirmed: `HttpPartiesCommandClient.cs` sends `CommandType: typeof(TCommand).FullName`. With attribute routing, each of the 24 Parties commands carries `wireType = "Hexalith.Parties.Contracts.Commands.CreateParty"` as a literal that must equal `typeof(CreateParty).FullName`. The PRD warns about drift but prescribes no check; a namespace move breaks every Parties operation at runtime with a gateway "unknown command" error.
**Fix:** Add a Module marker member `wireTypeConvention = FullTypeName | KebabCase | Explicit` so the Catalog derives the value; add a Catalog warning when an explicit `wireType` equals what a convention would have produced (redundant literal).

### M-3. `EVENTSTORE_READ_ONLY` with ".NET boolean parsing" rejects `1` and `0`
**Location:** FR-19.
**Quoted:** "`EVENTSTORE_READ_ONLY` (.NET boolean parsing)".
**Why it is a problem:** `bool.Parse` accepts only `true`/`false` (case-insensitive). Every CI system sets flags as `1`. The PRD does not say whether `EVENTSTORE_READ_ONLY=1` is an error (exit 2) or silently not read-only; the second is a safety failure for the one feature whose purpose is safety.
**Fix:** "Accepted values: `true`, `false`, `1`, `0`; any other value is `configuration_invalid`, exit 2, before the Catalog builds."

### M-4. Read-only refusal of a "hand-crafted `send_command`" is untestable where the PRD puts it
**Location:** FR-19.
**Quoted:** "the executor refuses a hand-crafted `send_command` request over stdio with the same code".
**Why it is a problem:** If `send_command` is omitted from the tool list, the MCP SDK answers `tools/call` for an unknown tool before any executor code runs; the observable result is the SDK's error, not `code: read_only`. The sentence describes a defense-in-depth intent but as an acceptance criterion it cannot pass.
**Fix:** Split: "the MCP head does not register `send_command`; a `tools/call` for it yields the SDK's unknown-tool error" and "the executor, called directly with a write under Read-only Mode, returns `read_only` (unit test)".

### M-5. NFR-2's 8,000-character budget probably excludes the output schemas FR-11 requires
**Location:** NFR-2, FR-11.
**Quoted:** "The five Generic Tool definitions together stay under 8,000 characters"; "Every tool returns structured content with a declared output schema".
**Why it is a problem:** `describe_operation`'s output schema embeds a JSON Schema for a JSON Schema plus example plus envelope arguments; `run_query`'s includes paging metadata; the error union appears on all five. Output schemas are part of the tool definition a client receives. 8,000 characters for five input schemas, five output schemas, five three-part descriptions, and annotations is tight to impossible, and the PRD does not say whether output schemas count.
**Fix:** State whether the budget includes `outputSchema`; if yes, raise it or make the output schema for `run_query` and `describe_operation` a loose object; add a snapshot test that measures.

### M-6. CLAUDE.md still says "Identifiers are ULIDs"; the PRD has moved on
**Location:** §4 "Identifiers", FR-3 Identifier Kind; CLAUDE.md "Identifiers are ULIDs; validate with `Ulid.TryParse`, never `Guid.TryParse`".
**Why it is a problem:** The 2026-09-22 amendment (AD-8) introduced `String` identifiers precisely because Tenants' aggregate ids are not ULIDs. The repository policy every agent reads first still states the old rule. An implementer following CLAUDE.md validates every identifier with `Ulid.TryParse` and breaks Tenants; one following the PRD violates the stated policy.
**Fix:** Update the CLAUDE.md/AGENTS.md/copilot-instructions line (via the sync script) to: "Envelope identifiers are ULIDs validated with `Ulid.TryParse`; payload identifiers follow the Module's Identifier Kind."

### M-7. The Tenants module is the admin plane the PRD says it excludes
**Location:** §2.2 Non-Users, §8.3 Non-Goals, FR-20 (Tenants as v1 module).
**Quoted:** "Platform administrators (the admin plane stays with `Hexalith.EventStore.Admin.Cli` and `.Admin.Mcp`)"; "Not the admin plane".
**Why it is a problem:** Every Tenants operation (create, enable, disable tenants; add users; set global administrators) is platform administration performed under the `system` tenant, and the admin CLI already exposes `tenant list|detail|users|verify`. v1's flagship module contradicts the non-user statement, and the PRD does not say which tool an operator should use for tenant reads.
**Fix:** Either narrow the Tenants decorated subset to what a tenant-scoped operator may do (probably nothing, given the `system` requirement) and choose a different second v1 module, or amend §2.2 to say the admin plane exclusion is about EventStore infrastructure (streams, replay, storage), not tenant management, and note the overlap with the admin CLI as accepted.

### M-8. UJ-1's retry story asserts gateway deduplication that the PRD does not verify
**Location:** UJ-1 edge case, FR-16, FR-17, §4 Idempotency.
**Quoted:** "the agent retries with the idempotency key from its first attempt and the Gateway deduplicates it".
**Why it is a problem:** On retry the executor generates a *new* message identifier (FR-16) and reuses the caller's idempotency key. Whether the gateway deduplicates on idempotency key alone, or on (tenant, aggregate, key), or requires the same message id, is an EventStore behavior the PRD asserts without a reference; `SubmitCommandRequestValidator` only checks the key's size. If dedup is keyed on message id, the journey's edge case double-writes.
**Fix:** Add an assumption tag and an OQ item: "EventStore owner confirms idempotency-key deduplication semantics and scope; the result document states whether the Gateway reported a duplicate."

### M-9. The addendum §E resolution order omits the Profile selection paradox and the per-call precedence for `tenant` only
**Location:** FR-13, addendum §E.
**Quoted:** "each value resolves as per-call argument, then flag, then environment variable, then Profile, then default".
**Why it is a problem:** `--profile` is itself resolved through the chain (`EVENTSTORE_PROFILE`, then the active profile in the file), so "Profile" as a source depends on a value resolved by the same chain; the PRD does not say which is evaluated first, and the fixture "that sets every source" cannot be written without that. Only `tenant` has a per-call argument, yet the sentence is written as if every option had one.
**Fix:** State: "`--profile` resolves first (flag, `EVENTSTORE_PROFILE`, active profile); the remaining options then resolve per the chain against the selected Profile. Only `tenant` has a per-call source."

### M-10. Gateway input constraints are not pre-validated, so the agent gets a gateway 400 for tool-side mistakes
**Location:** §4 "Identifiers" ("The Tenant is a non-empty string"), FR-15, FR-16.
**Why it is a problem:** `SubmitCommandRequestValidator.cs`: Tenant and Domain must match `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$` and be at most 64 characters; AggregateId at most 256 with a limited character set; CorrelationId at most 128 alphanumeric-plus-hyphen; extensions may not contain `< > & ' "`. The PRD treats the tenant as any non-empty string and extensions as free text; an agent that passes a tenant with an uppercase letter learns it only from a mapped gateway exception, which FR-14 classes with real gateway failures. Cheap to pre-check.
**Fix:** Add to FR-15: "the executor pre-validates Tenant, aggregate identifier, correlation identifier, and extensions against the Gateway's published patterns and reports them as `validation_failed`".

### M-11. FR-22's deliverable is a pull request in another repository with no fallback
**Location:** FR-22, §8.1 item 6.
**Quoted:** "the story closes when the pull request adding the rule is merged upstream and this repository's `AGENTS.md` references it".
**Why it is a problem:** A story whose closing condition is a merge decision by another repository's maintainers is not a story this team can finish. `Hexalith.AI.Tools` is a read-only submodule here (§4 references policy).
**Fix:** Close the story on the pull request being *opened* and linked from `AGENTS.md`; track the merge as an external dependency.

### M-12. §8.2 pre-commits the roadmap to "typed tools" while SM-C2 forbids chasing them
**Location:** §8.2, SM-C2, CLAUDE.md v1 exclusions.
**Quoted:** "Typed tools behind a module filter: first follow-up candidate"; "SM-C2 Five tools in v1. Do not chase SM-2 by adding typed tools."
**Why it is a problem:** Not a v1 violation, but "first follow-up candidate" invites the first story after v1 to be the thing the counter-metric guards against, before the HTTP transport that §1 calls essential. A roadmap statement in a PRD is a decision people will cite.
**Fix:** Remove "first follow-up candidate"; list it under parked with the others, and state that the HTTP transport is the only committed next release.

---

## Low

### L-1. Addendum §C is duplicated
**Location:** addendum §C.
**Why:** The FrontComposer, `azmcp`/`scw`, and landscape-research paragraphs appear twice (lines 88-107 and 108-125). Harmless but signals the polish pass did not re-read the file.
**Fix:** Delete the second copy.

### L-2. Legacy Server counts disagree
**Location:** §1 ("six handwritten per-module MCP servers"), §3 "Legacy Server" (four standalone plus the FrontComposer host), addendum §D (six named, including `Hexalith.Projects.Mcp`).
**Fix:** One count, one list; say whether `Hexalith.Projects.Mcp` is a standalone server or the FrontComposer plug-in.

### L-3. `mcp --transport http` "names the release in which it arrives"
**Location:** FR-12.
**Why:** A release name baked into a binary is wrong the first time the plan slips.
**Fix:** "exits 2 with `code: unsupported_transport` and a link to the roadmap".

### L-4. §7 versioning cannot signal Module-driven breaking changes
**Location:** §7 "Breaking changes".
**Why:** Operation Names derive from Module type names; a Module renaming a command type renames the Operation an agent has learned, but the tool's version only bumps the pin. Agents get `unknown_operation` with no versioning signal.
**Fix:** State that Operation Name stability is a Module obligation in the Gateway-ready checklist, and that `describe_operation` may carry `deprecatedAlias` in a later minor.

### L-5. NFR-6 "no native dependencies" is true, but the tool will carry the Dapr SDK
**Location:** NFR-6, FR-17.
**Why:** `Hexalith.EventStore.Client.csproj` references `Dapr.Client`, `Microsoft.AspNetCore.DataProtection.Abstractions`, and `Microsoft.Extensions.Hosting.Abstractions`. Managed, so NFR-6 holds, but a "thin CLI" ships gRPC and Dapr assemblies it never calls, and `AddEventStoreGatewayClient` registration paths may register more than one `HttpClient` (the FR-17 assertion should be run against the real registration early).
**Fix:** Note the size cost in §7 or ask the EventStore owner for a gateway-only client package as a follow-up.

### L-6. The `list_operations` example in UJ-2 and the FR-8 rule agree; the glossary's "Wire Type" example does not name Tenants queries
**Location:** §3 "Wire Type".
**Why:** "today `create-tenant` for Tenants" is the command wire type; Tenants queries use `get-tenant-users`-style `QueryType`. Fine, but the sentence reads as if Tenants had one wire naming scheme and Parties another; Parties queries have no scheme yet at all.
**Fix:** "today kebab-case for Tenants commands and queries, full CLR type name for Parties commands; Parties queries do not exist".

---

## Pre-mortem: v1 shipped six months ago and is unused or broken

1. **Agents can write but not read.** `run_query` never worked for Tenants because no gateway query path existed for it (C-4), Parties never published query types (H-10), and list queries were rejected for an empty aggregate id. Every UJ-2 session reports "I can act but not look", the inverse of what Read-only Mode was designed for, and the Agents/ChatBot/Conversations modules (SM-7) never adopted a tool that cannot answer a question.
2. **Security review stopped it at the laptop.** The stdio server acts as a token that must carry the `system` tenant claim to do anything with Tenants (C-1), the agent can pick the tenant per call and name any actor in a Projects payload (C-3), and the HTTP transport that fixes identity still has no auth design owner (OQ-1). The tool stayed a personal developer utility; nobody with production data was allowed near it.
3. **The Catalog stayed almost empty.** The Decoration Package shipped, but the closure test rejected the first decorated Contracts packages (C-2), Parties' 24 wire-type literals and new query surface were never scheduled (H-10, M-2), Projects slimming and the Folders rewrite were "tracked upstream" with no owner, and the first Legacy Server deletion (SM-3) never happened because the one deletable server, Parties, was also the only one that already worked.

## Policy check against CLAUDE.md "Hexalith.McpCli"

- Two dependency kinds: PRD complies in intent; the closure rule as written excludes the two v1 modules (C-2).
- Zero module-specific code: complied; but the build-time assembly list generator needs a non-module rule to be written down (H-9).
- Tenant from envelope, never payload: PRD complies for the payload, but adds a model-controlled per-call tenant source not in the policy (C-3).
- ULID identifiers: PRD has moved to Identifier Kind; CLAUDE.md is stale (M-6).
- v1 exclusions: none violated; §8.2 "first follow-up candidate" pre-commits to one of them (M-12).
