---
title: "Downstream Review: Hexalith.McpCli PRD"
status: review
created: 2026-09-21
reviewed: prd.md (updated 2026-09-21), addendum.md, extract-references.md, CLAUDE.md
method: adversarial read from three downstream roles, plus verification of factual claims against extract-references.md and the reference sources under references/ (read-only)
---

# Downstream Review: Hexalith.McpCli PRD

## Verdict

The PRD is well structured and its vision, glossary, and non-goals are sound, but it is not yet safe to hand to architecture or to story cutting. Four problems block: (1) the query envelope is under-specified against the real `SubmitQueryRequest` (required `AggregateId`, `ProjectionActorType`, search/filter/order/freshness), so `run_query` as written cannot reach Tenants; (2) FR-7's exclusion of envelope-like payload fields collides with Projects' `IProjectCommand`, where those fields are required members, and with Open Question 3, which says the matter is undecided; (3) `send_command` is declared `idempotentHint: true` while FR-16 mandates a fresh idempotency key per call, which makes a client retry a duplicate write; (4) §9.1 understates what Parties, Projects, and Folders must do (Parties has no query records at all; Projects' reads are MCP resources; Folders is a REST server with no event-sourced contract), so no maintainer can act on it without a second conversation.

Severity counts: critical 6, high 18, medium 14, low 12 (see Part 5 index).

Tags: **[critical]** blocks architecture or a story; **[high]** forces a guess two teams would make differently; **[medium]** will be argued at "done"; **[low]** wording or hygiene.

---

## Part 0. Factual claims checked against ground truth

Each item cites the PRD location, the ground truth, and the fix. Ground truth is `extract-references.md` unless a file path is given; file paths were read in `references/` to confirm.

### 0.1 [critical] `run_query` cannot fill the query envelope — FR-9, FR-16, Glossary "Envelope"

Ground truth (`references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Queries/SubmitQueryRequest.cs`): `SubmitQueryRequest(string Tenant, string Domain, string AggregateId, string QueryType, string? ProjectionType, JsonElement? Payload, string? EntityId, string? ProjectionActorType)` plus `Paging`, `Search`, `Filters`, `OrderBy`, `Freshness`. `AggregateId` is non-nullable and required. `ProjectionActorType` is documented as: "domain services with their own projection actor (e.g., tenants) set this to their actor type."

PRD: `run_query` takes "an optional aggregate identifier"; FR-16's aggregate-id resolution chain is stated for Commands only; no FR, glossary entry, or attribute value mentions `ProjectionActorType`, `EntityId`, `Search`, `Filters`, `OrderBy`, or `Freshness`. The addendum lists these fields under B and says "to be re-verified"; the PRD never picked them up.

Consequence: an architect cannot route a Tenants query (the one module the PRD says "already has routing from the interfaces") because `IQueryContract` carries no `ProjectionActorType`, and cannot decide what `AggregateId` to send for list-style queries such as `ListTenantsQuery` or `GetUserTenantsQuery`.

Fix: add to FR-2 a query routing datum `projectionActorType` (attribute-only, since the interface lacks it) and a rule for the query `AggregateId` (for example: attribute-named payload property, else explicit argument, else a documented sentinel that the Gateway accepts for aggregate-less queries, confirmed with the EventStore owner). Add to FR-9 either explicit `entityId`, `search`, `filters`, `orderBy`, `freshness` arguments on `run_query` or an explicit statement that v1 exposes paging only and those fields are deferred, with the consequence that Folders-style freshness modes are not reachable in v1 (which then feeds FR-21 parity).

### 0.2 [critical] FR-7 schema exclusion breaks Projects and contradicts Open Question 3 — FR-7, FR-15, FR-16, §11 OQ-3

Ground truth (`references/Hexalith.Projects/src/Hexalith.Projects.Contracts/Commands/IProjectCommand.cs` and `CreateProject.cs`): every Projects command is a positional record with required `TenantId`, `ProjectId` (a `ProjectId` value-object type, not a string), `ActorPrincipalId`, `CorrelationId`, `TaskId`, `IdempotencyKey`, and an instance `CommandType => nameof(...)`. Parties' `CompletePartyErasure` also has `required string TenantId`.

PRD FR-7: "The Envelope-supplied fields (Tenant, message identifier, idempotency key, correlation identifier) are not part of the Schema even if the record declares like-named properties." OQ-3 says whether the Schema hides tenant-like properties is undecided. FR-15 validates the payload against the Schema. FR-16 says the tool generates the idempotency key and nobody supplies it.

Consequence: if the Schema hides `TenantId`, `CorrelationId`, `IdempotencyKey` and the executor forwards the payload as received, the Projects domain service deserialises a `CreateProject` with missing required members and rejects it. If the executor injects envelope values into the payload, that is a generic rule the PRD does not state (and it contradicts "the Decoration Package carries what the contract cannot express", since the mapping needs per-record knowledge). If the Schema declares `additionalProperties: false`, agents cannot send Projects commands at all; if it does not, a payload `tenantId` different from the envelope tenant is silently forwarded, which is a cross-tenant smuggling vector the PRD's own tenant rule (§6) exists to prevent.

Fix: decide OQ-3 in the PRD, not in architecture, because it changes module obligations. Recommended: (a) the Schema includes every property the record declares; (b) the executor, before submission, overwrites a payload property that the attribute names as `tenantProperty` with the envelope tenant and rejects a payload whose value differs; (c) `IdempotencyKey`/`CorrelationId`/`MessageId`-like payload properties are either dropped from Contracts by the module (named prerequisite for Projects in §9.1) or filled by the executor from the envelope through attribute-named properties. Whichever is chosen, FR-7's consequence and OQ-3 must agree.

### 0.3 [high] `idempotentHint: true` contradicts the per-call idempotency key — FR-9, FR-16, §6 "Idempotency"

FR-16: "Two identical calls produce two different message identifiers and idempotency keys." FR-9: `send_command` carries `idempotentHint: true` "because the tool generates an idempotency key per call and the Gateway honours it." §6: "a caller cannot supply either."

These three statements together mean: an MCP client that trusts the hint and retries a timed-out `send_command` creates a second, distinct command with a fresh idempotency key, and the Gateway (which honours keys) cannot deduplicate it. The hint is false as written.

Fix: set `idempotentHint: false` on `send_command`, or allow an optional caller-supplied `idempotencyKey` argument (ULID) so an agent can retry safely, and amend §6 accordingly. The second option is the one that makes UJ-1's "resubmit without asking" safe.

### 0.4 [high] Parties has no query contract records — §9.1 Parties prerequisite, FR-20, FR-21

Ground truth: `references/Hexalith.Parties/src/Hexalith.Parties.Contracts/` contains `Authorization`, `Commands` (24 records), `Events`, `Models`; there is no `Queries` folder. `Hexalith.Parties.Mcp` reads through `IPartiesQueryClient` in `Hexalith.Parties.Client`, which the dependency policy forbids referencing. Extract D lists Parties as "plain records with no routing interface" and names only commands.

PRD §9.1: "Parties: add descriptions, examples, and routing values on the attribute (no interface today)." That is complete for commands and silent on queries. The Parties Legacy Server's `get_party`-style reads cannot reach parity (FR-21) without new Query records that the Gateway's query path can serve.

Fix: add to §9.1 Parties: "create Query records in `Hexalith.Parties.Contracts` for every read the Legacy Server exposes, served by the Parties domain service's projection actor, and decorate them." Note in OQ-5 that Parties is therefore not "already on the Gateway" for reads.

### 0.5 [high] Projects' reads are MCP resources and its wire type is an instance property — §9.1 Projects prerequisite, FR-2, FR-21

Ground truth: `Hexalith.Projects.Mcp` exposes 5 commands and 11 resources (extract A). `IProjectCommand.CommandType` is an instance member returning `nameof(CreateProject)`; `ICommandContract` requires a static abstract, so Projects cannot implement the interface without changing every record. Projects.Server's `IProjectCommandSubmitter` (`references/Hexalith.Projects/src/Hexalith.Projects.Server/IProjectCommandSubmitter.cs`) wraps the gateway with a tenant guard, idempotent-replay detection, and safe-denial mapping.

PRD §9.1: "Projects: add descriptions and examples; decide how `IProjectCommand` context (task, actor) maps to the Envelope." Missing: the 11 reads have no Query records; the attribute must carry `wireType = nameof(...)` per record (or Projects migrates to the static interface); direct gateway submission bypasses the server-side tenant guard, which the Projects maintainer must accept or move into the aggregate.

Fix: rewrite the Projects prerequisite as a list: (1) Query records for the 11 resources; (2) attribute routing values (`domain`, `wireType`, `aggregateIdProperty = ProjectId`); (3) a decision, recorded in the PRD, on whether the server-side tenant guard is re-implemented in the aggregate handler; (4) resolution of OQ-2 as a module change, since the required fields are in the record shape.

### 0.6 [high] Folders is not an event-sourced module; "create records and route them through the Gateway" is a re-architecture — §9.1 Folders prerequisite, FR-20, SM-1

Ground truth: `Hexalith.Folders.Contracts` holds `FoldersContractMetadata.cs`, projection read-model records under `Projections/Audit/`, and OpenAPI YAML; `Hexalith.Folders.Mcp` has 49 tools plus 2 resources over an NSwag REST client with task scoping, freshness modes, dry-run gates, and redaction (extract A, F.2).

PRD: names Folders in v1 (FR-20 consequence 1: `list_modules` returns `folders`), calls the work "the largest prerequisite", gives no scope (which of 49 tools are agent-facing), no owner, no acceptance criterion, and no statement whether Folders must become an EventStore domain service or only expose a gateway façade.

Fix: either move Folders out of the v1 coverage list (FR-20 lists three; Folders is "first follow-up once Gateway-ready") or add a Folders section to §9.1 with: the subset of operations required for v1, the owner, the statement that Folders' server semantics (dry-run, redaction, freshness) either move into aggregate/projection handlers or are dropped, and the rule that v1 "done" does not wait on Folders. As written, FR-20 consequence 3 ("appears with zero Operations") and SM-1 ("Folders exposed") disagree on whether v1 can ship without it.

### 0.7 [high] The shared profile file is lossy in the admin CLI — FR-18, Glossary "Profile"

Ground truth (`references/Hexalith.EventStore/src/Hexalith.EventStore.Admin.Cli/Profiles/ConnectionProfile.cs`, `ProfileManager.cs`): `ConnectionProfile(string Url, string? Token, string? Format)` with no extension-data member; `ProfileManager.Save` rewrites the whole file from the typed store. The reserved-name set is `version, activeProfile, profiles, url, token, format`, and the shell completion scripts grep out those same keys to enumerate profile names.

PRD FR-18: adds an optional `tenant` field per Profile to the same file, "shared with the admin CLI."

Consequence: any admin CLI write (`config use`, `config profile add/remove`) drops every `tenant` value; the admin completion script would list `tenant` as a profile name. The "nothing new to learn" promise holds only until the user touches the admin CLI.

Fix: either (a) make the admin CLI's `ConnectionProfile` tolerant (a `[JsonExtensionData]` bag; an upstream change in Hexalith.EventStore, to be named as a prerequisite in §9.1), or (b) store this tool's tenant default outside the shared file (`~/.eventstore/mcpcli.json` keyed by profile name) and state so in FR-18. Do not leave the shared-file claim as is.

### 0.8 [medium] Default output format differs from the admin CLI — FR-13

Ground truth (`GlobalOptionsBinding.cs`): admin CLI default `--format` is `table` (`EVENTSTORE_ADMIN_FORMAT ?? "table"`), and the default URL `http://localhost:5002` is the Admin API, not the gateway. PRD FR-13 says `json` is the default and gives no default URL. The json default is a reasonable choice for this tool, but FR-13 is titled "Honour global options with the admin CLI's precedence" and the glossary calls the profile "shared", so a reader assumes the defaults are shared too.

Fix: state explicitly in FR-13 that defaults differ from the admin CLI (`json`, and a gateway default URL to be named) and that only the precedence order is copied.

### 0.9 [medium] "Six per-module MCP servers, each with its own transport" — §1 Vision, Glossary "Legacy Server", Addendum D

Ground truth (extract A): `Hexalith.Projects.Mcp` is a library with no `Program.cs`, hosted by `Hexalith.FrontComposer.Mcp`, which is itself a generic descriptor-driven host with no tools of its own. So two of the six are one host plus one plug-in, and one of them is a prior generic catalog-driven design the PRD never mentions as prior art. Deleting `FrontComposer.Mcp` deletes the runtime of `Projects.Mcp`.

Fix: correct the count to "four standalone servers plus one descriptor-driven host with one hosted module" in §1 and the glossary; add FrontComposer.Mcp to Addendum C as a comparable; note in FR-21 that FrontComposer.Mcp and Projects.Mcp are deleted together.

### 0.10 [medium] Tenants routes to two domains and its queries are classes — FR-2, FR-3, Glossary "Module"

Ground truth: `BootstrapGlobalAdmin.Domain => TenantIdentity.GlobalAdministratorsDomain` while other Tenants commands use `tenants`; `GetTenantUsersQuery` and siblings are `sealed class`, not records, and carry `TenantId`, `Cursor`, `PageSize` in the payload.

PRD: everything says "record"; FR-3 declares one Module Name per assembly and the glossary ties Module to "a Hexalith domain module", which a reader will equate with one Gateway domain. Tenants' `Cursor`/`PageSize` in the payload duplicates the envelope `Paging` FR-9 exposes.

Fix: say "class or record" throughout, state that Domain is a per-Operation routing value that may differ within a Module, and add to §9.1 Tenants: decide whether payload paging properties are removed in favour of envelope paging (otherwise `run_query`'s paging arguments and the payload can disagree).

### 0.11 [medium] Tenants is "already routed" only for commands and projection type — §9.1 Tenants

Ground truth: `IQueryContract` gives `QueryType`, `Domain`, `ProjectionType`; the `SubmitQueryRequest` doc says tenants needs `ProjectionActorType`. So Tenants must still add an attribute value.

Fix: amend §9.1 Tenants: "add descriptions, examples, and `projectionActorType` on query attributes."

### 0.12 [low] Extract counts are samples, not totals — Addendum D, FR-21

Ground truth: Tenants has 12 commands and 6 queries, Parties 24 commands; extract D lists five of each. Not a PRD error, but FR-21's migration plan needs full inventories.

Fix: state in FR-21 that the migration plan starts with a full inventory per module, since the extract is partial.

### 0.13 [low] Claims that check out

Exit codes 0/1/2 with 1 = "Degraded / partial success" match `ExitCodes.cs`. Profile file path and top-level schema (`version`, `activeProfile`, `profiles{name:{url,token,format}}`) match. `SubmitCommandRequest` fields and `EventStoreGatewayException` fields quoted in FR-11 match. "Zero `[Description]` attributes" and "only Tenants implements `ICommandContract`/`IQueryContract`" match. The header-forwarding handler description in Addendum B matches extract E. "Six replacement targets plus two admin-plane tools" matches extract A's seven-plus-one, subject to 0.9.

---

## Part 1. The Architect

### 1.1 [critical] FR-16 aggregate-id chain: undefined for queries, wrong order for conflicts, requires CLR deserialisation

Chain as written: "`ICommandContract` instance property, else attribute-named Payload property, else explicit `aggregateId` argument."

- `ICommandContract.AggregateId` is an instance property, so reading it means deserialising the JSON payload into the contract CLR type. That is an implementation prescription (schema validation could otherwise be pure JSON) and it forces the Catalog to hold constructible types with `required` members satisfied, which is exactly what FR-7's exclusion breaks (0.2).
- The explicit argument is last. So an agent that passes `aggregateId` while the payload contains a different `PartyId` is silently ignored. Two architects will choose differently between "argument wins", "payload wins", and "conflict is a validation error".
- Queries have no chain, yet the envelope requires one (0.1).
- For Projects the attribute-named property is `ProjectId`, a value-object type; the PRD has no rule for converting a non-string identifier to the envelope string.

Fix: rewrite FR-16's consequence as: for Commands and Queries alike, (1) explicit argument if present; (2) else attribute-named payload property, stringified by the rule "a record with a single string member is its member"; (3) else `ICommandContract.AggregateId` read through a JSON path the Catalog derives once at startup; a conflict between (1) and (2) is `validation_failed`. State whether the Catalog is allowed to instantiate contract types.

### 1.2 [high] FR-2 precedence and FR-6 diagnostics disagree

FR-2: "When both interface and attribute supply a value, the interface wins and a startup diagnostic reports the redundancy." FR-6: the closed list of diagnostics is missing description, missing routing, duplicate name, invalid example; `--strict` turns "any diagnostic" into failure.

So a Tenants maintainer who adds `domain: "tenants"` to the attribute for readability breaks every CI run under `--strict`. Also unclear: if a record implements `ICommandContract` and the attribute supplies only `projectionActorType` (which the interface lacks), is that "both supply a value"?

Fix: define precedence per field, not per record: for each routing field, interface if the interface defines it, else attribute; a redundant attribute value that equals the interface value is ignored silently; one that differs is a diagnostic. Add the diagnostic categories to FR-6 as an open list with a severity per category (`error` excludes the record; `warning` does not) and let `--strict` promote warnings only.

### 1.3 [high] FR-3/FR-5 assembly discovery has no enumeration rule and forbids the obvious one

FR-5: "add a package reference, rebuild. No source change." FR-3: "The Catalog scans only assemblies carrying the marker." FR-5 also forbids "a configuration file listing Modules."

A referenced assembly that no code touches is not loaded into the AppDomain at startup, and a trimmed global tool may drop it. The architect must choose between scanning the application directory for `*.Contracts.dll`, a generated source file listing module assemblies (source-generator or MSBuild item), or `AssemblyLoadContext` probing. The first two work; the PRD's wording ("no configuration file") reads as forbidding the generated list, and "scans only assemblies carrying the marker" implies the scan set is already known.

Fix: add to FR-5 a consequence: "the set of assemblies to scan is derived at build time from the project's package references (generated, not hand-written); a hand-maintained list is what is forbidden." Add NFR: "the tool is published untrimmed or with the Contracts assemblies rooted."

### 1.4 [high] FR-7: what is excluded, by what match, and what happens to extra payload properties

Beyond 0.2: the exclusion list names concepts ("Tenant, message identifier, idempotency key, correlation identifier"), not property names or a matching rule (`TenantId`? `Tenant`? case-insensitive? attribute-declared?). FR-15 says the payload is validated against the Schema but does not say whether unknown properties are rejected. FR-4 says every property with `[Description]` gets a `description`; a hidden property with a description would be a silent inconsistency.

Fix: make exclusion opt-in and explicit: the attribute names `tenantProperty`, `correlationProperty`, `idempotencyKeyProperty` when the record has them; the Schema marks them read-only or omits them (pick one); the executor fills them from the envelope; the Schema declares `additionalProperties: false`. Say all three in FR-7.

### 1.5 [high] FR-14 exit-code semantics are borrowed from health checks and do not map to submissions

"1 when the Operation was accepted with a warning" and the assumption "exit 1 = accepted with diagnostics, for example a Catalog that started with excluded records."

Open questions an architect must answer alone: does every `modules` call exit 1 while any record is excluded (that turns every CI invocation into "degraded" until all four upstream repos are clean)? Does a Gateway idempotent-replay (`SubmitCommandResponse` with replay) exit 0 or 1? Does `send` in read-only exit 2 (FR-19 says yes) while `--strict` catalog failure exits 2 too, indistinguishable from a validation error? What does `mcp --transport http` exit with (FR-12 says "rejected", no code)?

Fix: table in FR-14: 0 = result document produced, no diagnostics; 1 = result document produced and at least one diagnostic was written to stderr for *this invocation* (catalog exclusions count only for `modules`/`operations`/`describe`, not for `send`/`query`); 2 = no result document (validation, gateway rejection, read-only refusal, unsupported transport, startup failure). State that the structured error JSON goes to stdout only in the 2 case.

### 1.6 [high] FR-19 contradicts the Glossary on what Read-only Mode exposes

Glossary "Read-only Mode": "the Catalog exposes Queries only." FR-19: "`list_operations` still lists Commands, marked `write`." Which one is the Catalog filter that CLAUDE.md promises ("read-only mode is one filter")?

Also unspecified: what `describe_operation` returns for a Command in this mode ("states that submission is disabled" — a field name? a `readOnly: true` flag? a text note?), whether `EVENTSTORE_READ_ONLY` accepts `true`/`1`/`yes`, and what `--read-only` does on `query` or `modules` (FR-13 says every verb accepts it).

Fix: change the glossary to "a startup option under which write submission is refused and `send_command` is not advertised; discovery is unchanged." Add to FR-19: `describe_operation` and `describe` include `submittable: false` with `reason: read_only`; the environment variable follows .NET boolean parsing; `--read-only` on a read verb is accepted and has no effect.

### 1.7 [high] FR-21 parity is undefined in three places

- "Every agent-facing Operation the Legacy Server exposed": "agent-facing" is undefined. Folders.Mcp and Projects.Mcp expose MCP *resources* (2 and 11). §8 says this product never provides resources. Either resources are out of parity (say so) or those two servers can never be deleted.
- "The ChatBot catalog's feature set (kind flag, correlation, task, and Tenant arguments) is reachable through the Generic Tools": `task` is not an argument of any Generic Tool in FR-9. It is reachable only if `Extensions` is exposed, which FR-9 does not do, or if it is a payload property, which is module-specific.
- "The migration plan lists, per Legacy Server..." — no FR produces the migration plan; it is not in §9.1.

Fix: define "agent-facing Operation" as "a tool or resource of the Legacy Server whose effect is a Command or Query through the Gateway; resources that read event streams or module files are out of scope and listed as dropped in the migration plan." Add an optional `extensions` map argument to `send_command`/`run_query` (or remove `task` from the parity bar). Add the migration plan as a deliverable (FR-23 or §9.1 item) with an owner.

### 1.8 [high] FR-9 argument lists versus FR-12 verbs: gaps in both directions

| Item | MCP (FR-9) | CLI (FR-12/13) | Gap |
|---|---|---|---|
| Kind filter | `list_operations` optional kind | `operations <module>` — none | CLI missing `--kind` |
| Tenant override | per-call argument | global `--tenant` | different scope; per-call override is a 5th tenant source absent from Glossary and §6 |
| `--strict` on describe | none | FR-4 `describe --strict` | MCP has no way to lint descriptions |
| Paging | page size, offset, cursor | "the paging options" unnamed | option names unspecified |
| `entityId`, `projectionActorType`, search/filter/order/freshness, `extensions` | none | none | see 0.1, 1.7 |
| `send_command` "optional aggregate identifier" | optional | `--aggregate-id` | FR-16 makes it mandatory-if-underivable; say "optional when derivable" |
| "Same words wherever the two Heads overlap" | `list_modules`, `send_command` | `modules`, `send` | the consequence is already violated by the PRD's own names; it cannot be tested |

Fix: publish one argument table in FR-9 that both Heads implement, with the CLI option spelling in a second column; replace the "same words" consequence with "every argument in the table exists in both Heads under the spelling given."

### 1.9 [medium] FR-8 name derivation contradicts UJ-2

FR-8: the Operation Name is derived from the record type name unless overridden. `GetTenantUsersQuery` therefore becomes `tenants.get-tenant-users-query`, but UJ-2 shows `tenants.get-tenant-users`, and `IQueryContract.QueryType` is `get-tenant-users`. Two architects will pick "strip `Query`/`Command` suffix" versus "prefer the interface's wire value when it is kebab-case."

Fix: state the rule: "type name in kebab-case with a trailing `Command` or `Query` suffix removed; the attribute may override; the interface value is never used as the Operation Name" (or the opposite; pick one).

### 1.10 [medium] FR-15 "identifier fields" is undefined

"Identifier fields are validated with `Ulid.TryParse`." Which properties are identifiers: name ends in `Id`? declared type? attribute? Projects' `ActorPrincipalId` is a principal id and Tenants' `TenantId` may be a slug rather than a ULID; a name-suffix rule would reject valid payloads. `ProjectId` is a value object, not a string.

Fix: identifiers are the properties the attribute names as aggregate id, plus any property carrying a `[Ulid]`-style marker in the Decoration Package; everything else is validated by the Schema only. Confirm with each module which ids are ULIDs before FR-15 is implemented.

### 1.11 [medium] Two different `--strict` flags — FR-4, FR-6

FR-4 `describe --strict` reports undescribed properties; FR-6 `--strict` at startup turns diagnostics into failures. On `hexalith describe parties.create-party --strict` both apply. Fix: rename one (`--lint` for FR-4).

### 1.12 [medium] FR-20 consequence 3 contradicts FR-3

FR-3: an assembly without the marker "contributes nothing and produces no error." FR-20: "A Module that is not yet Gateway-ready appears with zero Operations and a startup diagnostic, rather than being silently absent." A not-yet-ready module (Folders today) has no marker, so under FR-3 it is silently absent; making it appear needs a hard-coded expected-module list, which is module-specific code. Fix: drop FR-20 consequence 3, or define it as "a marked assembly with zero decorated records produces a diagnostic."

### 1.13 [medium] Glossary drift

- "Tenant" lists Profile, flag, environment, forwarded header; FR-9 adds a per-call tool argument override. §6 repeats the four-source list. Add the fifth or remove it.
- "Command — changes the state of one aggregate" versus queries that target no aggregate but need an envelope `AggregateId` (0.1).
- "Gateway-ready — ... accepted by the Gateway": the Gateway accepts any well-formed envelope with 202; the meaningful test is that the module's domain service *handles* the wire type. Replace "accepted by" with "handled by the Module's domain service through".
- "Legacy Server — six" versus the host/plug-in reality (0.9).
- "Decoration Attribute — carries ... routing fallbacks" while FR-1 says the attribute carries "a required description and an optional example" and FR-2 introduces routing; harmless but the story writer will split them differently.

### 1.14 [medium] Prescribed implementation that belongs to architecture

- FR-16 reading `ICommandContract.AggregateId` at runtime (dictates deserialisation, 1.1).
- FR-1 "a Roslyn analyzer ships in the Decoration Package"; the Decoration Package "references no other package" — an analyzer is a build asset that references `Microsoft.CodeAnalysis`; say "no runtime dependency."
- NFR-4 "source-generated `LoggerMessage` methods" is a coding convention, not a requirement.
- FR-11 "nearest Operation Names by edit distance" — say "suggestions" and let architecture pick the metric and count.

### 1.15 [low] Who mints new aggregate identifiers

UJ-1 has the agent create a party then a project "with the aggregate identifier from the first result flowing into the second." `CreateParty` requires the caller to supply `PartyId`; `SubmitCommandResponse` returns `MessageId`, not an aggregate id. So the agent must mint a ULID itself, and nothing tells it so. Fix: `describe_operation` output states which property is the aggregate id and that the caller must supply a fresh ULID for creation commands; or `send_command` accepts `aggregateId: "new"` and returns the minted value.

### 1.16 [low] `list_operations` requires a Module Name

An agent looking for "anything about users" must call once per module. Fix: make the module argument optional (all modules) with an optional text filter; NFR-2 budget is unaffected.

### 1.17 [low] NFR-2 versus FR-11 output schemas

Five tool definitions under 2,000 tokens is tight once each carries an output schema (FR-11) and a "what to call next" description (FR-9). Fix: state whether output schemas count toward the budget.

---

## Part 2. The Story Writer

### 2.1 [high] FRs that are several stories each and need splitting before estimation

- **FR-1** = attribute types + analyzer (with its own [ASSUMPTION] fallback) + example validation at startup + zero-dependency packaging. Four stories, two of which depend on OQ-6.
- **FR-9** = five tools + annotations + agent-oriented descriptions + read-only variant. At least six stories; the annotations story depends on 0.3.
- **FR-12** = verbs + payload input modes (`--payload`, `@file`, stdin) + `mcp` verb + transport rejection + naming parity. Five stories.
- **FR-13** = global options + precedence per option + environment prefix + format handling. The precedence fixture alone is one story per option.
- **FR-16** = id generation + tenant placement + correlation validation + aggregate-id chain + wire routing. Five stories; the chain story is blocked by 1.1.
- **FR-18** = file schema extension + active-profile selection + `config` verbs + secret redaction. Four stories; blocked by 0.7.
- **FR-21** = parity definition + migration plan deliverable + Extensions decision. The plan has no owner.

### 2.2 [high] Consequences that are untestable as written

- FR-10 "works unmodified as a stdio server in Claude Code, Claude Desktop, and VS Code": a manual check in three GUI products. Replace with "conforms to MCP 2025-xx stdio transport as verified by the ModelContextProtocol client SDK in a test" and keep the three clients as a release checklist item.
- FR-9 "Every tool has a description written for an agent: what it does, when to use it, and what to call next": subjective. Replace with "each description contains the three labelled parts" so a test can assert structure.
- FR-12 "the same words wherever the two Heads overlap": violated by the PRD's own names (1.8). Replace with the argument table.
- NFR-8 / SM-5 "understandable by someone who has never seen the code": a review, not a test; fine as a metric, but no story can close it. Add SM-C4 ("does not restate the type name") as a testable lint: description must not equal the humanised type name.
- FR-22 "the rule applies from acceptance of this PRD, before v1 ships": a policy statement in another repository; the story is "open a PR in Hexalith.AI.Tools", and "done" is that PR merged. Say so.
- FR-20 consequence 1 "`list_modules` returns four names": depends on four upstream repositories shipping decorated packages. Without a fixture the story cannot be closed in this repository.
- NFR-1 "500 ms on a developer laptop": name a reference machine or a CI runner class.

### 2.3 [high] No test fixture module is defined, and the zero-module-code rule seems to forbid one

Every catalog, executor, and head story needs a Contracts assembly with known records. §6 and SM-1 say "zero module-specific code in this repository." Whether a `tests/Hexalith.McpCli.Fixtures.Contracts` sample module counts as module-specific code will be argued.

Fix: add to §6: "test projects may contain a synthetic sample Contracts Library; it is never referenced by the tool package." Add it to §9.1 as the first deliverable, because every other story depends on it.

### 2.4 [medium] Where "done" will be argued

- FR-6 "one diagnostic line each, naming the record type": format unspecified (structured? prefix? severity?). Define the line shape.
- FR-11 "nearest Operation Names by edit distance": how many, and what threshold? Say "up to three, distance at most N."
- FR-15 "all violations are reported together": is a payload that fails JSON parsing "one violation"? Say so.
- FR-14 exit 1 (1.5): a script author and a developer will disagree on whether catalog exclusions degrade `send`.
- FR-19 "states that submission is disabled": field or prose (1.6).
- FR-18 "`config profile|use|current` with the admin CLI's semantics": admin `config profile` has sub-verbs (add, remove, list); the PRD does not say which are in, nor how `tenant` is set (`config profile add --tenant`?). Enumerate.
- FR-13 `--tenant` with no value from any source: startup error, per-call error, or allowed for tenant-less operations (Tenants' global-administrator domain)? Decide.
- FR-17 "Command results include the message identifier": from the tool's generated id or the Gateway's response `MessageId` (nullable)? Say "the generated one, plus the Gateway's correlation id."
- FR-5 "byte-identical for the same build": across operating systems? Line endings and JSON property ordering must be fixed; say "with the tool's canonical JSON serializer options."

### 2.5 [medium] Epic boundaries the PRD implies but does not state

The natural cut is: E1 Decoration Package (FR-1..4), E2 Catalog (FR-5..8), E3 Executor (FR-15..17, FR-19), E4 MCP Head (FR-9..11), E5 CLI Head (FR-12..14, FR-18), E6 Coverage and migration (FR-20..22). E3 must precede E4 and E5, and E1 must precede everything, but E1's analyzer (OQ-6) should not gate E2. The PRD's §9.1 order (Decoration, Catalog, MCP, CLI, executor, read-only, coverage) lists the executor after both heads, which will mislead a sprint planner.

Fix: reorder §9.1 to the dependency order and mark the analyzer as a separable story.

### 2.6 [low] Requirements hiding in journeys and non-goals

UJ-3's "the build of the Contracts Library warns" and "logs it to stderr at startup" are the only place the analyzer and startup diagnostic are shown working together; UJ-1's "fixes the Payload and resubmits without asking" depends on 0.3. §8 "Not a second executor" is a testable negative (no `HttpClient` to any host but the gateway) that no FR states. Fix: add a consequence to FR-17: "the only outbound HTTP is through `IEventStoreGatewayClient`; a test asserts no other `HttpClient` registration."

---

## Part 3. The Module Maintainer

### 3.1 [critical] The attribute's contract is never specified — §4.1, §9.1

A maintainer of any module cannot decorate a record without knowing: the attribute type names; the constructor and named arguments (`description`, `example`, `domain`, `wireType`, `aggregateIdProperty`, `projectionType`, `projectionActorType`, `name` override, and per 1.4 `tenantProperty` and friends); which of them are required when the record does not implement the interface; whether the attribute applies to classes as well as records (Tenants queries are classes); whether events, projections, and value objects must never be decorated; and the package identifier to reference (OQ-7).

Fix: add a §4.1 table "Decoration Attribute members" with name, type, required-when, and example, and a sentence "only Command and Query types are decorated; events, read models, and value objects are not."

### 3.2 [critical] Parties: concrete routing values and the missing query records — §9.1

Ground truth: Parties' wire `CommandType` is not declared on the contract at all; `Hexalith.Parties.Client/HttpPartiesCommandClient.cs` sends `typeof(TCommand).FullName` and domain `"party"`. So the value the Parties *domain service* dispatches on is the full CLR type name, and the module name in the Catalog (`parties`) differs from the wire domain (`party`).

The PRD says only "routing values on the attribute (no interface today)." A Parties maintainer needs: `domain = "party"`, `wireType = "Hexalith.Parties.Contracts.Commands.CreateParty"` (or a decision to migrate the aggregate to kebab-case and implement `ICommandContract`, which is a breaking wire change for existing clients), `aggregateIdProperty = nameof(PartyId)`, plus the Query records from 0.4, plus a decision on which of the 24 commands are agent-facing (the GDPR erasure flow — `CompletePartyErasure`, `MarkErasureVerified`, `RotatePartyKey`, `MarkPartyEncryptionKeyDeleted` — is probably not).

Fix: in §9.1 Parties, list the three routing values with their present-day values, state that the choice between "attribute with FullName" and "migrate to `ICommandContract`" is the maintainer's, and require the maintainer to publish the agent-facing subset as the parity inventory for FR-21.

### 3.3 [critical] Projects: what happens to `IProjectCommand` fields — §9.1, OQ-2

A Projects maintainer reading "decide how `IProjectCommand` context (task, actor) maps to the Envelope" cannot act, because the PRD has already decided the parts that constrain the answer: FR-16 says the tool generates the idempotency key and message id and the caller cannot supply them; FR-7 hides tenant/idempotency/correlation from the Schema; §6 says tenant is never in the payload. Every Projects record requires all of these as positional constructor parameters. The only module-side outcomes are: (a) drop `TenantId`, `CorrelationId`, `IdempotencyKey` from the records and read them from the envelope in the aggregate (a breaking change for Projects.Server and its REST clients), or (b) keep them and have the tool fill them (needs 1.4's attribute-named properties). `TaskId` and `ActorPrincipalId` have no envelope home except `Extensions` (assumption in FR-21) or the payload.

Also: `ProjectId` is a value object; the Schema derivation (FR-7) needs a rule for it; `CommandType` is an instance `nameof` and must go on the attribute; the server-side tenant guard in `IProjectCommandSubmitter` is bypassed by direct gateway submission (0.5).

Fix: close OQ-2 in the PRD with option (b) as the default and (a) as the maintainer's choice; add `extensions` to FR-9 so `TaskId`/`ActorPrincipalId` can travel there when the module chooses; add "value-object identifiers serialise as their single string member" to FR-7; add the tenant-guard decision to the Projects prerequisite.

### 3.4 [high] Folders: no actionable scope — §9.1

See 0.6. A Folders maintainer has 49 tools, a REST server, and a Contracts package with read models and OpenAPI. "Create Command and Query records and route them through the Gateway" does not tell them whether Folders becomes an EventStore domain service (aggregates, projections, actors), which operations matter first, what happens to dry-run/redaction/freshness, or what "done" looks like for v1. There is no owner and no date.

Fix: either remove Folders from v1 or write a one-page Folders prerequisite with scope, owner, and acceptance ("`list_operations folders` shows these N operations and `send_command` on each is handled by the Folders domain service").

### 3.5 [high] Tenants: not as ready as stated — §9.1

"Routing already comes from the contract interfaces" is true for `Domain`, `CommandType`, `QueryType`, `ProjectionType`, and command `AggregateId`, and false for `ProjectionActorType` (0.1, 0.11) and for query `AggregateId` (0.1). Tenants also has `TenantId`, `Cursor`, `PageSize` in query payloads (0.10) and a second domain for global administrators. Which of 12 commands and 6 queries are agent-facing is not stated; `BootstrapGlobalAdmin` and `SetGlobalAdministrator` probably should not be exposed to an agent holding a dev token.

Fix: §9.1 Tenants: "add descriptions and examples; add `projectionActorType` and the query aggregate-id rule on query attributes; decide whether payload paging properties are removed; do not decorate global-administrator commands in v1."

### 3.6 [high] Missing obligations common to all four modules

- Publish the Contracts Library as a NuGet package that references the Decoration Package (FR-20 forbids project references; nothing says the packages exist on a feed today).
- Version bump and release so this tool can pin it (§7 "Module versions").
- Someone reviews descriptions against NFR-8/SM-5; the PRD names no reviewer and no place to record the review.
- Keep `Domain` and wire type stable, because renaming either silently breaks the Catalog mapping (FR-8 consequence 2) without any compile-time signal.

Fix: add a "Gateway-ready checklist" to §9.1 with these four items plus the module-specific ones, and say which repository's issue tracker holds the work.

### 3.7 [medium] Things asked of maintainers that contradict ground truth

- "decorate each Command and Query *record*" — Tenants queries are classes (0.10).
- "Tenants: routing already comes from the contract interfaces" — not for `ProjectionActorType` (0.11).
- "Parties: add ... routing values" — Parties also needs query records (0.4).
- "Projects: add descriptions and examples" — Projects needs query records for 11 resources and a wire-type value per record (0.5).
- FR-2 "A Parties record with no interface and no routing values on its attribute is excluded" — correct, but the PRD never tells Parties which values to put (3.2).
- Glossary "Contracts Library — the `*.Contracts` NuGet package ... The only Module artifact this product may reference": Tenants.Contracts transitively references `Hexalith.EventStore.Contracts` (for `ICommandContract`, `[RestRoute]`); state that transitive EventStore packages are allowed so the policy check in CI does not flag it.

### 3.8 [medium] FR-22 and OQ-4 disagree on CLIs

FR-22 states the rule covers "per-module agent CLI"; OQ-4 says whether the rule covers CLIs is open. A Folders or ChatBot maintainer with a `.Cli` project does not know if they may keep extending it. Fix: decide in the PRD (recommend: rule covers new CLIs; existing ones are frozen and listed as deletion candidates in the migration plan).

### 3.9 [low] Memories is a hosted per-user server today

`Hexalith.Memories.Mcp` is HTTP with JWT (extract A). Replacing it with a stdio tool that "acts as whoever owns the configured token" (§6) is an identity regression for that module until the HTTP release. Not a v1 module, but the Memories maintainer should be told the order in the migration plan depends on the HTTP transport. Fix: note in OQ-5 that Memories and any other JWT-fronted server are deleted only after the HTTP release.

---

## Part 4. Policy alignment with CLAUDE.md

- [low] §9.2 "Typed tools behind a module filter: first follow-up candidate" and SM-C2 "do not chase task success by adding typed tools" pull in opposite directions; CLAUDE.md says "out of version one, refuse if proposed." Consistent with v1, but make SM-C2 say "in v1" so the follow-up is not a metric failure.
- [low] CLAUDE.md "Tenant comes from the envelope (profile, flag, or forwarded header)": the PRD adds environment variable and per-call override; update CLAUDE.md when the PRD is accepted, via `AGENTS.md` and the sync script.
- [low] CLAUDE.md "Message ID and idempotency key are generated per call; correlation ID is optional pass-through" matches FR-16 but inherits the retry problem in 0.3; update together.
- [low] CLAUDE.md "The catalog distinguishes commands from queries so a read-only mode is one filter" matches §4.7 but not the glossary (1.6).
- [low] Vision §1 states "all of them travel through one EventStore Gateway" as fact; extract F says one of seven servers does. Rephrase as the target state.

---

## Part 5. Findings index

| # | Sev | Location | Title |
|---|---|---|---|
| 0.1 | critical | FR-9, FR-16, Glossary | `run_query` cannot fill `SubmitQueryRequest` (required `AggregateId`, `ProjectionActorType`, search/filter/order/freshness) |
| 0.2 | critical | FR-7, FR-15, FR-16, OQ-3 | Schema exclusion breaks Projects' required fields and contradicts OQ-3 |
| 1.1 | critical | FR-16 | Aggregate-id chain undefined for queries, wrong on conflicts, prescribes deserialisation |
| 3.1 | critical | §4.1, §9.1 | Decoration Attribute members never specified |
| 3.2 | critical | §9.1 Parties | Parties routing values and query records missing |
| 3.3 | critical | §9.1 Projects, OQ-2 | `IProjectCommand` fields have no viable outcome under FR-7/FR-16 |
| 0.3 | high | FR-9, FR-16, §6 | `idempotentHint: true` with per-call fresh keys makes retries duplicate writes |
| 0.4 | high | §9.1 Parties, FR-21 | Parties has no query contract records |
| 0.5 | high | §9.1 Projects, FR-2 | Projects reads are resources; wire type is an instance member; tenant guard bypassed |
| 0.6 | high | §9.1 Folders, FR-20, SM-1 | Folders prerequisite is a re-architecture with no scope, owner, or v1 exit rule |
| 0.7 | high | FR-18 | Admin CLI drops the added `tenant` field on save |
| 1.2 | high | FR-2, FR-6 | Interface/attribute precedence and diagnostic list disagree |
| 1.3 | high | FR-3, FR-5 | No assembly enumeration rule; obvious one is forbidden |
| 1.4 | high | FR-7 | Exclusion match rule and unknown-property policy undefined |
| 1.5 | high | FR-14 | Exit-code semantics do not map to submissions |
| 1.6 | high | FR-19, Glossary | Read-only Mode exposure contradicts the glossary |
| 1.7 | high | FR-21 | Parity undefined: "agent-facing", resources, `task`, migration plan owner |
| 1.8 | high | FR-9, FR-12, FR-13 | Argument lists incomplete and inconsistent across Heads |
| 2.1 | high | FR-1, 9, 12, 13, 16, 18, 21 | Multi-story FRs |
| 2.2 | high | FR-10, FR-9, FR-12, NFR-8, FR-22, FR-20, NFR-1 | Untestable consequences |
| 2.3 | high | §6, SM-1 | No test fixture module; policy seems to forbid one |
| 3.4 | high | §9.1 Folders | No actionable scope for Folders |
| 3.5 | high | §9.1 Tenants | Tenants not as ready as stated |
| 3.6 | high | §9.1 | Common obligations (publish, version, review, stability) missing |
| 0.8 | medium | FR-13 | Defaults differ from admin CLI without saying so |
| 0.9 | medium | §1, Glossary, Addendum D | Two of six "servers" are a host and its plug-in |
| 0.10 | medium | FR-2, FR-3, Glossary | Tenants has two domains and class-typed queries with payload paging |
| 0.11 | medium | §9.1 Tenants | `ProjectionActorType` still needed |
| 1.9 | medium | FR-8 | Name derivation contradicts UJ-2 |
| 1.10 | medium | FR-15 | "Identifier fields" undefined; ULID rule over-rejects |
| 1.11 | medium | FR-4, FR-6 | Two `--strict` flags |
| 1.12 | medium | FR-20, FR-3 | Zero-operation module cannot appear without a hard-coded list |
| 1.13 | medium | Glossary | Tenant sources, Gateway-ready, Legacy Server drift |
| 1.14 | medium | FR-1, FR-11, FR-16, NFR-4 | Implementation prescribed |
| 2.4 | medium | FR-5, 6, 11, 13, 14, 15, 17, 18, 19 | "Done" arguments |
| 2.5 | medium | §9.1 | Epic order misleads |
| 3.7 | medium | §9.1, FR-2, Glossary | Maintainer asks contradicting ground truth |
| 3.8 | medium | FR-22, OQ-4 | CLI coverage decided and undecided |
| 0.12 | low | Addendum D, FR-21 | Extract inventories are partial |
| 0.13 | low | — | Claims verified correct |
| 1.15 | low | UJ-1, FR-17 | Who mints new aggregate ids |
| 1.16 | low | FR-9 | `list_operations` requires a module |
| 1.17 | low | NFR-2, FR-11 | Output schemas versus token budget |
| 2.6 | low | UJ-1, UJ-3, §8 | Requirements hiding in journeys and non-goals |
| 3.9 | low | OQ-5 | Memories identity regression |
| 4.x | low | §9.2, SM-C2, §1, CLAUDE.md | Policy wording alignment (5 items) |
