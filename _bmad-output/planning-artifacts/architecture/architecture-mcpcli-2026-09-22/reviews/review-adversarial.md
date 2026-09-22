---
title: Adversarial review — ARCHITECTURE-SPINE.md (Hexalith.McpCli)
reviewed: _bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md
lens: adversarial — two units one level down, each obeying every AD to the letter, that still build incompatibly
date: '2026-09-22'
status: findings
---

# Adversarial review of the Architecture Spine

## Brief and method

The brief: construct pairs of units one level down (the epics and stories a small coding agent would build from the spine alone: Decoration Package, Catalog builder, Schema derivation, Executor and read-only mode, MCP head, CLI head and profiles, Generator, Test AppHost and integration tests, Release pipeline) that each obey every AD literally yet build incompatibly. Every pair is a hole; each hole closes with one tightened Rule sentence or one new AD.

Each finding was checked against the reference repositories, not only the prose. Facts that carry weight:

- `ICommandContract` (`references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Commands/ICommandContract.cs`) declares `string AggregateId { get; }` as an instance getter; every Tenants command implements it as `public string AggregateId => TenantId;`. The interface never names a Payload property.
- `IQueryContract` declares `QueryType`, `Domain`, `ProjectionType` only; no aggregate member.
- `SubmitQueryRequest` (`.../Contracts/Queries/SubmitQueryRequest.cs`) has `Tenant, Domain, AggregateId, QueryType, ProjectionType?, Payload?, EntityId?, ProjectionActorType?`, `Paging`, and a `[JsonExtensionData] AdditionalProperties` bag. It has no `CorrelationId` and no `Extensions`. Only `SubmitCommandRequest` has them.
- `GetUserTenantsQuery` (`references/Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Queries/GetUserTenantsQuery.cs`) carries `string? Cursor` and `int PageSize` as Payload members.
- `TenantIdentity.DefaultTenantId = "system"` and `GlobalAdministratorsAggregateId = "global-administrators"`; neither is a ULID.
- `ProjectId` (`references/Hexalith.Projects/src/Hexalith.Projects.Contracts/Identifiers/ProjectId.cs`) is a single-member record with `[JsonConverter(typeof(ProjectIdJsonConverter))]`; `JsonSchemaExporter` emits an unconstrained schema for a type with a custom converter.
- `AddEventStoreGatewayClient` returns the `IHttpClientBuilder` of a typed `AddHttpClient<IEventStoreGatewayClient, EventStoreGatewayClient>` registration.
- The admin CLI's `ProfileManager` rejects the profile names `version`, `activeProfile`, `profiles`, `url`, `token`, `format` on top of the regex the spine quotes.
- MCP `structuredContent` is a JSON object by schema; a top-level array is not a legal value.

## Verdict

Not build-ready as a substrate for independent stories. Three entities have two owners (the Tenant, the aggregate-identifier path, the discovery and error document shape), one registration is claimed by two ADs (the auth handler), and two Gateway shapes the spine assumes do not exist on the client (`CorrelationId`/`Extensions` on a Query). Each hole closes with one sentence; the sentences are given below and collected in the final table.

---

## Critical

### C1. The Tenant has three homes and no precedence — CLI head vs MCP head vs Executor

**Pair.** CLI head story; MCP head story; Executor story.

**What each obeys.**
- AD-5: `OperationCall(OperationName, Payload, EnvelopeArguments)` with `EnvelopeArguments(Tenant?, AggregateId?, CorrelationId?, IdempotencyKey?, EntityId?, Paging?, Extensions?)`.
- AD-10: "the executor receives an `EnvelopeContext(Tenant?, CorrelationId?, UserId?, Extensions?)` value that the head builds per call from settings and arguments."
- AD-13: `ResolvedSettings(..., Tenant?, ...)` with precedence "per-call argument, flag, environment variable, Profile, default."
- AD-9: "resolve Tenant (else `validation_failed`)" — from what, unstated.

**Clash.** `Tenant`, `CorrelationId`, and `Extensions` appear in both `EnvelopeArguments` (AD-5) and `EnvelopeContext` (AD-10), and `Tenant` a third time in `ResolvedSettings` (AD-13). The CLI story, reading AD-10 ("from settings and arguments"), puts `--tenant` into `EnvelopeContext.Tenant` and leaves `EnvelopeArguments.Tenant` null. The MCP story, reading AD-5, puts the tool argument `tenant` into `EnvelopeArguments.Tenant` and the startup tenant into `EnvelopeContext.Tenant`. The Executor story, reading AD-9's sequence diagram (`OperationCall + EnvelopeContext`), picks one field to read. If it reads `EnvelopeContext.Tenant` only, a per-call MCP `tenant` argument is ignored and the addendum §E promise "per-call argument wins over flag" is broken silently. If it reads `EnvelopeArguments.Tenant ?? EnvelopeContext.Tenant`, the CLI's `--tenant` still works, but `extensions` supplied per call and `Extensions` in the context have no merge rule, and a `CorrelationId` in both is a coin toss. AD-1 says a head may only "parse its input into the core call model (AD-5)"; AD-10 adds a second input the call model does not mention. Also unstated: the executor's signature — `Execute(OperationCall)` or `Execute(OperationCall, EnvelopeContext)`.

**Fix (tighten AD-5 and AD-10).** "`EnvelopeArguments` carries only values the caller supplied on this call; `EnvelopeContext` carries only session values (`Tenant` from `ResolvedSettings.Tenant`, `UserId`, `Extensions` from settings); `IOperationExecutor.ExecuteAsync(OperationCall call, EnvelopeContext context, CancellationToken ct)` resolves `Tenant = call.EnvelopeArguments.Tenant ?? context.Tenant`, `CorrelationId = call.EnvelopeArguments.CorrelationId` (the context has no `CorrelationId`), and `Extensions` as the context map overlaid by the per-call map key by key; no other component reads `ResolvedSettings.Tenant`."

### C2. Nobody can derive `AggregateIdPath` for an `ICommandContract` implementer — Catalog builder vs Executor

**Pair.** Catalog builder story (routing resolver); Executor story.

**What each obeys.**
- AD-3: `OperationDescriptor(..., AggregateIdPath, ...)`; reflection only inside `Core.Catalog`.
- Convention "Routing per field": "contract interface value when the interface defines the field, else the attribute member; ... differing values a `conflicting_value` warning with the interface winning."
- PRD FR-2: "A Tenants Command implementing `ICommandContract` needs no `domain`, `wireType`, or `aggregateIdProperty` on its attribute."
- AD-9: "resolve aggregate identifier as explicit argument, else `AggregateIdPath` value."
- PRD FR-16: "else the `ICommandContract` aggregate identifier read through a JSON path derived once at startup."

**Clash.** The interface does not define a field name; it defines a computed instance getter `AggregateId => TenantId`. Reflection sees a get-only property named `AggregateId` and nothing about `TenantId`. The Catalog story, obeying "interface wins", sets `AggregateIdPath = "/AggregateId"`. The Executor story reads that pointer from the caller's `JsonElement` Payload, where no such member exists (callers send `{ "TenantId": "..." }`), and returns `validation_failed` for every Tenants Command that is not sent with `--aggregate-id`. A Catalog story that instead notices the problem has two forbidden escapes: deserialize the Payload into the CLR type at call time and call the getter (reflection outside `Core.Catalog`, breaks AD-3), or guess by name. A Module author who adds `aggregateIdProperty = nameof(TenantId)` to be safe triggers the convention's `conflicting_value` warning ("differs from the interface value `AggregateId`") and loses: the interface wins. In addition, `JsonSchemaExporter` with `McpCliJson.Payload` emits the get-only `AggregateId` (and Projects' instance `CommandType`) as Schema properties, so `describe_operation` advertises a property the executor never reads. AD-9 also drops the FR-16 rule that an explicit argument disagreeing with the Payload is `validation_failed`; a literal Executor story lets the explicit value win silently while the CLI story documents the error from addendum §E.

**Fix (new AD-19, amends FR-2 and AD-9).** "`AggregateIdPath` is an RFC 6901 JSON Pointer to one string-valued member of the Payload (a value-object identifier counts as a string), taken from `aggregateIdProperty` on every Operation; an `ICommandContract` implementer without `aggregateIdProperty` is excluded with `missing_routing_values`, and the interface getter is used only at Catalog build to check, against the deserialized `example` when one exists, that the named member's value equals `AggregateId` (a `conflicting_value` warning otherwise). The Schema transform removes get-only members that have no setter and no constructor parameter. The executor takes the explicit argument, else the value at `AggregateIdPath`; when both exist and differ, `validation_failed` with instance location `AggregateIdPath`."

### C3. A Query without `aggregateIdProperty`: the Catalog excludes it, the Executor tolerates it

**Pair.** Catalog builder story; Executor story (and the MCP head, which renders `submittable`).

**What each obeys.**
- PRD §5.1 table: `aggregateIdProperty` required "no contract interface, or always for a Query"; FR-2: "a Tenants Query still needs `projectionActorType` and `aggregateIdProperty`"; FR-6: "missing Routing Values" is an error category that excludes the type.
- AD-9: "... else `validation_failed` for a Command and empty string for a Query."
- Open Question OQ-3: "AD-9 sends an empty aggregate identifier for a Query with none."

**Clash.** The Catalog story, obeying the PRD it is told to bind, excludes every Query whose attribute lacks `aggregateIdProperty`, so the executor's "empty string for a Query" branch is unreachable, `ListTenantsQuery` and `GetUserTenantsQuery` (whose natural key is an index, not an aggregate) never enter the Catalog, and OQ-3 can never be answered by observation. The Executor story, obeying AD-9, writes and tests the empty-string branch with a hand-built descriptor whose `AggregateIdPath` is null, a state the real Catalog never produces. The two stories' tests pass; the product cannot list tenants.

**Fix (tighten AD-9; amend PRD §5.1 and FR-2).** "`aggregateIdProperty` is optional for a Query; a Query without it has `AggregateIdPath = null`, enters the Catalog without a diagnostic, and the executor sends the explicit `aggregateId` argument when supplied, else `string.Empty` [ASSUMPTION pending OQ-3]; a Command without it is excluded with `missing_routing_values`."

---

## High

### H1. Discovery documents have no owner, and a top-level array cannot be `structuredContent`

**Pair.** CLI head story (`modules`, `operations`, `describe`); MCP head story (`list_modules`, `list_operations`, `describe_operation`).

**What each obeys.**
- AD-5 defines `CommandResult`, `QueryResult`, `OperationError` only; "The MCP head returns them as `structuredContent`; the CLI writes them to stdout."
- AD-1: heads "render the returned records" from `ICatalog`.
- PRD FR-9: `describe_operation` returns "the Envelope arguments the caller may supply."

**Clash.** For the three discovery tools there is no Core record. The CLI story renders `ICatalog.Modules` as a JSON array `[{ "name": ..., "description": ... }]`. The MCP story cannot: `structuredContent` must be an object, so it wraps `{ "modules": [...] }`. The two documents differ in shape for every discovery call, and the AD-16 equality test either fails or is written to compare only `send`/`query`. The "Envelope arguments the caller may supply" list is then typed twice: the MCP story writes `["tenant", "aggregateId", "correlationId", "idempotencyKey", "extensions"]`, the CLI story writes `["--tenant", "--aggregate-id", ...]`, both correct for their surface. The same applies to the tool argument sets: with no Core argument record, the MCP story hand-writes the `run_query` input schema (`pageSize`) while the CLI story declares `--page-size`; nothing ties the two spellings together but a table in a PRD addendum.

**Fix (tighten AD-5).** "Core also owns `ListModulesResult(Modules)`, `ListOperationsResult(Module, Operations)`, `DescribeOperationResult(Name, Kind, Description, Schema, Example, EnvelopeArguments, Submittable, Reason?)`, and the argument records `ListOperationsArguments`, `DescribeOperationArguments`, `SendCommandArguments`, `RunQueryArguments`; every document either head emits is one of these records serialized as a JSON object, never a top-level array; `DescribeOperationResult.EnvelopeArguments` lists argument-record property names in camelCase; the MCP input schemas are derived from the argument records with `McpCliJson.Result`, the CLI binds flags to the same records, and a test asserts that every argument-record property has a CLI option whose kebab-case name equals the property name."

### H2. How an `OperationError` travels over MCP is undefined, and `OutputSchema` cannot describe it

**Pair.** MCP head story; CLI head story; integration-test story.

**What each obeys.**
- AD-5: "a CLI error shape that differs from the MCP one" is prevented; the CLI writes `OperationError` to stdout with exit 2.
- AD-12: `UseStructuredContent = true`, `OutputSchema` from the AD-5 records.
- PRD FR-11: "failures return a structured error, never a stack trace."

**Clash.** The MCP story has three literal-compliant options: throw `McpException` (the client receives a JSON-RPC error whose only payload is a message string — no `OperationError` record at all), return `CallToolResult { IsError = true, StructuredContent = error }` (the error does not conform to the declared `OutputSchema`, which describes `CommandResult`, so a validating client rejects it), or return the error as text content only (no structured content). None reproduces the CLI's document. The CLI story meanwhile prints `OperationError` bare. The AD-16 test cannot compare "both heads' documents for equality" on the error path, which is the path SM-4 most needs.

**Fix (tighten AD-12).** "Each of the five tools declares one `OutputSchema` of `type: object` whose properties are the success record's properties plus an optional `error: OperationError`, with `additionalProperties: false`; on success both heads emit the success record, on failure both emit `{ "error": <OperationError> }` and nothing else, the MCP head with `IsError = true` and the same JSON in `Content[0].Text`; the MCP head never throws past the tool boundary."

### H3. The bearer-token handler is registered by two ADs — Hosting story vs Core story

**Pair.** Core story (`AddMcpCliCore`); CLI head / composition root story (`Hexalith.McpCli.Hosting`).

**What each obeys.**
- AD-10: "Authentication is a `DelegatingHandler` chained on the `IHttpClientBuilder` returned by `AddEventStoreGatewayClient`, registered by the composition root ... Core never reads a token."
- AD-11: "Core exposes `AddMcpCliCore(ResolvedSettings)` (catalog, schema, executor, `AddEventStoreGatewayClient` + auth handler, ULID generation, clock)."

**Clash.** The Core story, reading AD-11, calls `AddEventStoreGatewayClient(...)` and adds `StaticBearerTokenHandler` from `ResolvedSettings.Token`. The Hosting story, reading AD-10, adds `StaticBearerTokenHandler` again on the builder it thinks it owns — except Core swallowed the builder and returned `IServiceCollection`, so Hosting calls `AddEventStoreGatewayClient` a second time to get one. Result: either two handlers on one client (two `Authorization` headers, or an `InvalidOperationException` from `HttpRequestHeaders`), or two named registrations of the typed client, which is the exact condition the AD-11 "exactly one `HttpClient` registration" test exists to catch — and that test now fails for a reason neither story can see in its own project. AD-10's "Core never reads a token" is also violated the moment `ResolvedSettings.Token` enters `AddMcpCliCore`.

**Fix (tighten AD-10 and AD-11 together).** "`AddMcpCliCore(IServiceCollection, ResolvedSettings, Action<IHttpClientBuilder> configureGateway)` calls `AddEventStoreGatewayClient(o => o.BaseAddress = settings.Url)` exactly once and passes the returned builder to `configureGateway`; only `Hexalith.McpCli.Hosting` adds `StaticBearerTokenHandler` inside that callback; `ResolvedSettings.Token` is never read in Core, and `Core.Tests` asserts that `AddMcpCliCore` with a no-op callback registers no `DelegatingHandler`."

### H4. Paging travels twice — Schema derivation vs Executor, and Payload vs Envelope

**Pair.** Schema derivation story; Executor story (with both heads as accomplices).

**What each obeys.**
- AD-7: the Schema is the exporter's output for the type, `additionalProperties: false`, every declared property included.
- AD-5/AD-9 and addendum §E: `pageSize`, `offset`, `cursor` are Envelope arguments that the executor maps to `SubmitQueryRequest.Paging`.
- PRD §8.1 Tenants prerequisite: "decide whether the `Cursor` and `PageSize` Payload members give way to Envelope paging" — undecided, and the spine says nothing.

**Clash.** `GetUserTenantsQuery` declares `string? Cursor` and `int PageSize`. The Schema story exposes both as ordinary Payload properties (and `PageSize`, a non-nullable `int` constructor-less property, appears without `required`, so a Payload omitting it validates and sends `0`). The Executor story copies `EnvelopeArguments.Paging` into `SubmitQueryRequest.Paging` and forwards the Payload untouched. An agent reading `describe_operation` fills `PageSize: 20` in the Payload; a shell user passes `--page-size 20`; the two reach the Tenants projection through different fields, and which one the projection honors is a Tenants decision no story here can make. `run_query` in one head and `query` in the other are then "compatible" only for callers who guess the same channel.

**Fix (new AD-20).** "Paging is Envelope-only: `EnvelopeArguments.Paging` always maps to `SubmitQueryRequest.Paging`; the Decoration Attribute gains `pageSizeProperty`, `offsetProperty`, and `cursorProperty`, each treated exactly like `tenantProperty` (`readOnly: true` and not `required` in the Schema, overwritten from `EnvelopeArguments.Paging` before submission, a differing Payload value is `validation_failed`); a Query Payload member named `PageSize`, `Offset`, or `Cursor` that is not so declared is a `describe --lint` warning `unmarked_paging_member`."

### H5. `correlationId` and `extensions` on a Query have nowhere to go

**Pair.** CLI head story (`query --correlation-id`, `--extension`); MCP head story (`run_query` arguments); Executor story.

**What each obeys.**
- Addendum §E (which FR-9 and FR-12 make binding for both heads): `correlationId` and `extensions` on `run_query` / `query`.
- AD-9: "build `SubmitCommandRequest` or `SubmitQueryRequest` from the descriptor's Routing Values ... passes a caller-supplied correlation identifier and extensions through."

**Clash.** `SubmitQueryRequest` has no `CorrelationId` and no `Extensions` parameter; only `SubmitCommandRequest` does. The Executor story, unable to place them, either drops both silently (the CLI and MCP heads still accept and echo the argument, so a script believes its correlation id was sent), or stuffs them into the `[JsonExtensionData] AdditionalProperties` bag under invented keys the Gateway may ignore or reject, or returns `validation_failed`. Three literal readings, three different behaviors, and both heads have already committed to the argument.

**Fix (tighten AD-9).** "For a Query the executor writes `CorrelationId` into `SubmitQueryRequest.AdditionalProperties["correlationId"]` and `Extensions` into `AdditionalProperties["extensions"]` [ASSUMPTION: EventStore owner confirms the Gateway reads both before FR-16 is implemented; until confirmed, `describe_operation` on a `read` Operation lists neither in `EnvelopeArguments` and a supplied value is `validation_failed` at `/correlationId` or `/extensions`]." Add the confirmation to Open Questions beside OQ-3.

### H6. "First decorated type" is empty for a Module with zero Operations — Generator vs Catalog vs FR-20

**Pair.** Generator story; Catalog builder story.

**What each obeys.**
- AD-4: "keeps assemblies carrying the assembly-level Module marker, and emits `ModuleAssemblyManifest.Assemblies` as `typeof(<first decorated type>).Assembly` entries."
- PRD FR-20: "A referenced Module that is not yet Gateway-ready appears in `list_modules` with zero Operations and a startup diagnostic."
- PRD FR-3: "The Catalog scans only assemblies carrying the marker."

**Clash.** `Hexalith.Folders.Contracts` carries the marker (once Folders adopts it) and, per PRD §8.1, holds read models and OpenAPI only — zero decorated types. The Generator story has no "first decorated type" to name, emits no entry, and the Catalog story never sees the assembly; `list_modules` omits Folders, FR-20's consequence is false, and no diagnostic explains why. Two further ambiguities: "first" (ordinal by full name, or source order?) changes the manifest text between builds and defeats the byte-identical claim of FR-5; and the generator cannot reference `Hexalith.McpCli.Abstractions` (`netstandard2.0` generator, `net10.0` attribute assembly), so it matches the marker by a string the Decoration Package story chose independently.

**Fix (tighten AD-4).** "The manifest entry for a marked assembly is `typeof(T).Assembly` where `T` is the ordinally-first public type by full metadata name in that assembly, decorated or not; a marked assembly with no public type yields generator diagnostic `MCPCLI001` and no entry; the generator recognizes the marker by the constant `Hexalith.McpCli.Abstractions.HexalithModuleAttribute`, and `Abstractions.Tests` asserts the attribute's full name equals that constant."

### H7. Identifier kind is enforced in different places for the same value — Sample fixture vs real Tenants vs Executor

**Pair.** Test fixture story (`Sample.Contracts`) and integration-test story; Executor story; Schema derivation story.

**What each obeys.**
- AD-8: ULID pattern and `Ulid.TryParse` only for `[HexalithIdentifier]` properties or the `aggregateIdProperty` of a Module with `IdentifierKind = Ulid`.
- PRD §4: "Identifiers. ULIDs, validated with `Ulid.TryParse`."
- AD-9: "resolve aggregate identifier as explicit argument, else `AggregateIdPath` value."
- PRD FR-7: "A value-object identifier with a single string member serializes as that member."

**Clash.** Three sub-clashes. (a) The explicit `aggregateId` argument bypasses the Schema, so AD-8's rule never touches it; the Executor story, reading PRD §4, validates it with `Ulid.TryParse` and rejects `--aggregate-id global-administrators` and any Tenants id such as `system`, while the same value inside the Payload passes because Tenants declares `IdentifierKind = String`. (b) The fixture story declares its one Module with `IdentifierKind = Ulid` (the interesting case to test), the integration tests run only against Tenants (`String`), and the ULID branch is never exercised end to end; nothing says the fixture must cover both kinds. (c) `ProjectId` has a custom `JsonConverter`; `JsonSchemaExporter` emits `{}` for it, so the Schema story produces "accept anything" for the one property that matters most, while a fixture author who models a value-object id as a bare single-member record without a converter gets an object schema; the two disagree and neither matches FR-7. `[HexalithIdentifier]` on that property has no defined effect on a non-string CLR type.

**Fix (tighten AD-8).** "The explicit `aggregateId` argument and the value at `AggregateIdPath` are validated by the executor with one rule keyed on the Module's `IdentifierKind` (`Ulid.TryParse` for `Ulid`, non-empty string for `String`); `tenant` is a non-empty string and never ULID-validated; a property carrying `[HexalithIdentifier]` or named by `aggregateIdProperty` gets Schema `{ type: string, pattern? }` whatever its CLR type, which must serialize as a JSON string under `McpCliJson.Payload` (else `invalid_identifier_type` excludes the Operation); `tests/Hexalith.McpCli.Sample.Contracts` declares two Modules, `sample-ulid` (`IdentifierKind = Ulid`) and `sample-opaque` (`IdentifierKind = String`), and one converter-backed value-object identifier."

### H8. The two heads under test may load two different Catalogs — Harness story vs Core story

**Pair.** Integration-test / AppHost story; Core story (`CatalogBuilder` API); MCP head story.

**What each obeys.**
- AD-4: "`CatalogBuilder` scans exactly that list" (the generated manifest in the exe).
- AD-16: "drives the CLI as a process and the MCP Server through the ModelContextProtocol client over stdio against the same running topology ... compares both heads' documents for equality."
- AD-15: `Sample.Contracts` "is never referenced by `src/`."
- AD-11: "The MCP project exposes `AddMcpCliMcpServer()`."

**Clash.** Unit tests need a Catalog built from `Sample.Contracts`, so the Core story gives `CatalogBuilder` an `IEnumerable<Assembly>` parameter; the exe passes the manifest. The MCP story's tests, and quite plausibly the integration story, then host the MCP server in-process over an in-memory transport with `AddMcpCliMcpServer()` and the Sample assemblies (cheap, no process), while the CLI must be a process — the built `Hexalith.McpCli` exe, which references the real Contracts packages and cannot see `Sample.Contracts`. The "equality" test compares a Sample catalog against a Tenants catalog, or is quietly narrowed to whichever Operation Names both happen to share. Nothing in the spine says how the integration project finds the CLI executable either (no tool install in CI; a `ProjectReference` to an exe with `ReferenceOutputAssembly=false` and `$(TargetPath)` is the usual answer, but a story has to guess it).

**Fix (tighten AD-16).** "`CatalogBuilder.Build(IReadOnlyList<Assembly> assemblies)` is the only entry point; the composition root passes `ModuleAssemblyManifest.Assemblies`, unit tests pass `Sample.Contracts`; `Hexalith.McpCli.IntegrationTests` drives both heads through the same built `Hexalith.McpCli` executable (path supplied by an `<ProjectReference ReferenceOutputAssembly="false">` plus a `RuntimeHostConfigurationOption` `McpCli.ToolPath`), never in-process, so both heads load the manifest Catalog; the equality assertion runs over every Operation Name in `list_operations tenants` and both discovery and error documents."

---

## Medium

### M1. `hexalith mcp --read-only` — "the MCP head has no flags" vs FR-19

**Pair.** MCP head story; CLI head story (which owns the `mcp` verb).

**What each obeys.** AD-13: "The MCP head has no flags; it resolves from environment and Profile at startup and from tool arguments per call." PRD FR-19: "starts with `--read-only` or `EVENTSTORE_READ_ONLY`." FR-13: every verb, `mcp` included, accepts the global options.

**Clash.** The MCP story builds its own `SettingsResolver` call at startup from environment and Profile, as told, and never sees `--read-only`, `--tenant`, or `--profile` given on the `mcp` verb; the CLI story parses them and expects the container to honor them. `claude mcp add hexalith -- hexalith mcp --read-only` runs writable.

**Fix (tighten AD-13).** "`SettingsResolver` runs exactly once per process, in `Hexalith.McpCli.Hosting` after System.CommandLine has parsed the global options of the invoked verb (including `mcp`) and before the container is built; every head reads `ResolvedSettings` from DI and never calls the resolver, the environment, or the Profile store."

### M2. Serializer ownership leaks through the MCP SDK — MCP head vs the byte-identical claim

**Pair.** MCP head story; CLI head story; integration-test story.

**What each obeys.** AD-6: "No other `JsonSerializerOptions` is constructed in the solution"; AD-5: results "serialized with the result options of AD-6, the two are byte-identical"; AD-12: `OutputSchema` "from the AD-5 records."

**Clash.** `McpServerTool.Create` serializes a delegate's return value with the SDK's own options (`McpJsonUtilities.DefaultOptions`) unless `McpServerToolCreateOptions.SerializerOptions` is set; a literal MCP story sets `UseStructuredContent` and stops. The SDK's options differ (no indentation, its own enum handling). `OutputSchema` "from the AD-5 records" invites the MCP story to call the SDK's `AIJsonUtilities.CreateJsonSchema`, a second schema generator with a second set of options — AD-7 confines schema derivation to `Core.Schema` but only for Payloads. Finally, `structuredContent` is embedded in a JSON-RPC frame, so indentation never survives transit; "byte-identical" is undefined until someone says what is compared.

**Fix (tighten AD-12 and AD-5).** "The five tools are created with `SerializerOptions = McpCliJson.Result` and return the Core record itself, never a string or `JsonNode`; their `OutputSchema` and input schemas are produced by `Core.Schema.SchemaDeriver.ForResult(Type)` using `McpCliJson.Result`; byte-identity is asserted after each head's document is parsed and re-serialized with `McpCliJson.Result`."

### M3. Envelope-filled properties: name inference, `required`, and the Tenants `TenantId` trap

**Pair.** Schema derivation story; Executor story; Decoration Package / analyzer story.

**What each obeys.** AD-7: `readOnly: true` for envelope-filled properties; AD-9: "overwrite envelope-filled properties from the Envelope"; PRD FR-16: "A Payload tenant value that differs from the Envelope Tenant is `validation_failed`"; FR-7: "a caller may omit them."

**Clash.** (a) The set "envelope-filled properties" is never defined as exactly the members named by `tenantProperty`, `correlationProperty`, `idempotencyKeyProperty`. A helpful story infers `TenantId` by name. Every Tenants Command has `TenantId` — the managed tenant, which is the aggregate id, not the Envelope tenant (`system`); inference makes every `CreateTenant` `validation_failed` or, worse, overwrites the target tenant with `system`. (b) Projects' `CorrelationId` and `IdempotencyKey` are non-nullable constructor parameters; the exporter marks them `required`; "a caller may omit them" is false unless the transform removes them from `required`, which AD-7 does not list. (c) The Payload is an immutable `JsonElement`; "overwrite" means rebuilding through `JsonNode`, and whether the rebuilt Payload or the original is what the Gateway receives is what a Module's own validator sees.

**Fix (tighten AD-7 and AD-9).** "`EnvelopeFilledProperties` is exactly the set named by `tenantProperty`, `correlationProperty`, `idempotencyKeyProperty` (and the AD-20 paging members); no name-based inference exists, and a property named `TenantId` that is not named by `tenantProperty` is ordinary Payload; the transform sets `readOnly: true` and removes each from `required`; the executor rebuilds the Payload as a `JsonObject`, sets each envelope-filled member, and submits the rebuilt element."

### M4. `submittable` has no computing owner, and the descriptor cannot know Read-only Mode

**Pair.** Catalog builder story (owns the frozen `OperationDescriptor.Submittable`); MCP head and CLI head stories (render `describe_operation` / `describe`).

**What each obeys.** AD-3: `Submittable` on the immutable descriptor frozen at startup; PRD FR-19: "`describe_operation` on a Command returns `submittable: false, reason: read_only`"; FR-9: "`submittable`, with a reason when it is false."

**Clash.** Excluded types are absent from the Catalog, so every descriptor that exists is submittable on its own terms; the only false case is Read-only Mode, a settings fact. The Catalog story therefore freezes `Submittable = true` everywhere; each head story then computes `submittable = descriptor.Submittable && !(readOnly && kind == write)` on its own, one of them spelling the reason `read_only`, the other `read-only` or `ReadOnly`. Two heads, two computations of one flag.

**Fix (tighten AD-3).** "`OperationDescriptor` has no `Submittable`; `ICatalog.Describe(string operationName)` in Core returns `DescribeOperationResult` with `Submittable` and `Reason` computed from the descriptor and `ResolvedSettings.ReadOnly` (`Reason = "read_only"` when `ReadOnly && Kind == write`, else `Submittable = true`), and both heads render that record verbatim."

### M5. Exit code 1 on discovery verbs with startup warnings — CLI head vs MCP head vs CI scripts

**Pair.** CLI head story; MCP head story.

**What each obeys.** Conventions: Catalog diagnostics "written once to stderr at startup"; Exit codes: "1 result plus a diagnostic for this invocation"; PRD FR-14: exit 1 applies to "discovery verbs and `describe --lint` only; Catalog diagnostics never degrade `send` or `query`."

**Clash.** Startup diagnostics are written on every invocation, so they are "for this invocation" of `modules`. The CLI story exits 1 from `modules` whenever any referenced Module carries a warning (`conflicting_value`, `undescribed_property`), which is the normal state of a Module mid-migration; the MCP `list_modules` result carries nothing about it. One head reports degradation, the other cannot; a CI script keyed on exit 0 flaps on an unrelated Module's warning.

**Fix (tighten the Exit codes convention).** "Exit 1 is produced only by `describe --lint` with at least one finding, and by discovery verbs when the Catalog holds at least one diagnostic of severity `error` or `--strict` is set; warnings never change the exit code; `ListModulesResult` carries `diagnostics: { errors, warnings }` so the MCP head exposes the same fact."

---

## Low

### L1. Profile names and orphaned tenant entries — `config` verbs vs the admin CLI

**Pair.** CLI head / profiles story; the admin CLI (external, but the shared file makes it a peer).

**Clash.** AD-14 quotes the regex but not the admin CLI's reserved-name list (`version`, `activeProfile`, `profiles`, `url`, `token`, `format`); this tool accepts `config profile add profiles ...`, the admin CLI refuses to read it back. `config profile remove` (profiles.json) leaves `mcpcli.json` with an entry for a name that no longer exists; the admin CLI removing a profile leaves the same orphan and nothing reads it.

**Fix (tighten AD-14).** "Profile names also exclude, case-insensitively, `version`, `activeProfile`, `profiles`, `url`, `token`, `format`; `config profile remove` deletes the `mcpcli.json` entry of the same name; an `mcpcli.json` entry with no matching profile is ignored and reported by `config current` as `orphaned_tenant`."

### L2. Kebab-case is not one algorithm

**Pair.** Catalog builder story; fixture and Verify-snapshot authors; the analyzer story (duplicate-name warning).

**Clash.** `GetTenantUsersQuery` is easy; `SetTLSConfigCommand` is `set-tls-config` or `set-t-l-s-config`; `Party2Address` is `party-2-address` or `party2-address`. Two implementations (Catalog at runtime, analyzer at compile time) with two answers create a duplicate-name warning in one place and not the other.

**Fix (tighten the Operation Name convention).** "Kebab-case splits before each upper-case letter that follows a lower-case letter or digit, and before the last upper-case letter of a run that precedes a lower-case letter (`TLSConfig` → `tls-config`); digits stay attached to the preceding word; the result is ASCII lower-case; one implementation lives in `Hexalith.McpCli.Abstractions` as a `public static` helper so Catalog and analyzer share it."

### L3. `--strict` is unreachable from the MCP head

**Pair.** MCP head story; Settings story.

**Clash.** `ResolvedSettings.Strict` exists, the addendum's environment list has no `EVENTSTORE_STRICT`, and AD-13 says the MCP head has no flags, so an agent-hosted server can never fail fast on a bad Catalog; a CI job that starts the server through stdio and expects `--strict` semantics gets none.

**Fix (tighten AD-13).** "Add `EVENTSTORE_STRICT` to the environment variables; `Strict` resolves like every other setting, and M1's rule makes `hexalith mcp --strict` work."

### L4. `QueryResult.Document` vs the client's `Payload`, and `Metadata.Paging`

**Pair.** Executor story; MCP head story (`OutputSchema`).

**Clash.** `EventStoreQueryResult` exposes `Payload` and `Metadata` (`QueryResponseMetadata`), the spine names `Document` and `Metadata.Paging`; a story that mirrors the client type produces `payload` in one head's document and `document` in the other's `OutputSchema`.

**Fix (tighten AD-5).** "`QueryResult(CorrelationId?, Document?, Paging?)` maps `Document = result.Payload` and `Paging = result.Metadata?.Paging` mapped to `QueryPagingMetadata` fields `pageSize, offset, nextCursor, totalCount, hasMore`; the client type names never appear in a head document."

---

## Closing sentences, collected

| # | Tier | Where | Rule sentence (abridged; full text in the finding) |
| --- | --- | --- | --- |
| C1 | Critical | AD-5, AD-10 | `EnvelopeArguments` = per-call caller values; `EnvelopeContext` = session values; `ExecuteAsync(call, context, ct)`; `Tenant = args.Tenant ?? context.Tenant`; context has no `CorrelationId`; extensions overlaid key by key. |
| C2 | Critical | new AD-19 | `AggregateIdPath` is a JSON Pointer from `aggregateIdProperty` on every Operation; `ICommandContract` implementers without it are excluded; the getter only verifies against the example; get-only members are dropped from the Schema; explicit vs Payload disagreement is `validation_failed`. |
| C3 | Critical | AD-9, PRD §5.1/FR-2 | `aggregateIdProperty` optional for a Query; absent means `AggregateIdPath = null`, no diagnostic, empty string sent. |
| H1 | High | AD-5 | Core owns `ListModulesResult`, `ListOperationsResult`, `DescribeOperationResult` and the four argument records; every document is an object; input schemas derive from the argument records; a test ties CLI option names to record properties. |
| H2 | High | AD-12 | One `type: object` `OutputSchema` per tool = success fields + optional `error`; failure emits `{ "error": ... }` only, `IsError = true`; the head never throws. |
| H3 | High | AD-10, AD-11 | `AddMcpCliCore(services, settings, configureGateway)` registers the client once and hands the builder out; only Hosting adds the token handler; Core never reads `Token`. |
| H4 | High | new AD-20 | Paging is Envelope-only; `pageSizeProperty`/`offsetProperty`/`cursorProperty` behave like `tenantProperty`; undeclared paging members lint. |
| H5 | High | AD-9, OQ | Query `CorrelationId`/`Extensions` go to `AdditionalProperties` once the Gateway confirms; until then `validation_failed` and not advertised for `read`. |
| H6 | High | AD-4 | Manifest entry = ordinally-first public type of a marked assembly, decorated or not; empty assembly is generator diagnostic `MCPCLI001`; marker matched by a tested constant name. |
| H7 | High | AD-8 | One identifier rule keyed on `IdentifierKind` for both the explicit argument and the Payload value; `tenant` never ULID-validated; `[HexalithIdentifier]` forces `type: string`; fixture declares two Modules and a converter-backed value-object id. |
| H8 | High | AD-16 | `CatalogBuilder.Build(assemblies)` is the only entry point; integration tests drive both heads through the built executable, never in-process; equality covers discovery and errors. |
| M1 | Medium | AD-13 | `SettingsResolver` runs once in Hosting after parsing the invoked verb's global options; heads read `ResolvedSettings` from DI only. |
| M2 | Medium | AD-12, AD-5 | Tools use `SerializerOptions = McpCliJson.Result` and return records; result schemas come from `SchemaDeriver.ForResult`; byte-identity is asserted after re-serialization. |
| M3 | Medium | AD-7, AD-9 | `EnvelopeFilledProperties` is exactly the attribute-named set; no name inference; removed from `required`; Payload rebuilt as `JsonObject`. |
| M4 | Medium | AD-3 | Drop `Submittable` from the descriptor; `ICatalog.Describe` computes it with `ResolvedSettings.ReadOnly`; heads render verbatim. |
| M5 | Medium | Exit codes | Exit 1 only for lint findings, error-severity diagnostics, or `--strict`; `ListModulesResult` carries diagnostic counts. |
| L1 | Low | AD-14 | Reserved profile names; `config profile remove` cascades to `mcpcli.json`; orphans ignored and reported. |
| L2 | Low | Conventions | One kebab-case algorithm, shared through Abstractions. |
| L3 | Low | AD-13 | Add `EVENTSTORE_STRICT`. |
| L4 | Low | AD-5 | `QueryResult` field mapping from `EventStoreQueryResult.Payload` / `Metadata.Paging` stated once. |

## What is sound

Not every seam was breakable. Read-only enforcement (AD-9 plus AD-12's list handler) has one owner and one code; error codes are a closed set with one discriminator; the two serializer options are named and their uses enumerated; the dependency graph (AD-2) and packaging (AD-17, AD-18) leave no room for a second composition root or a second release path; ULID generation has one source. Those stories can be built from the spine as written.
