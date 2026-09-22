---
title: "Rubric review: ARCHITECTURE-SPINE.md (Hexalith.McpCli)"
reviewed: 2026-09-22
subject: ../ARCHITECTURE-SPINE.md (status draft, updated 2026-09-22)
verdict: pass with fixes
---

# Rubric review — Hexalith.McpCli architecture spine

**Gate verdict: pass with fixes.** The spine fixes the right seams for a feature-altitude build substrate (one core, two translating heads, one executor, one call model, one settings resolver, generated manifest), and every technology and brownfield claim I could check against `references/` and the local package cache holds. Three gaps would let independently built stories diverge or block the first build: the Envelope merge is split between heads and executor (AD-9/AD-10), the v1 Contracts pins cannot carry the marker the Catalog needs so the exe cannot start as specified (AD-4/AD-15/Stack), and "byte-identical" results across heads are not achievable as written because the MCP SDK serializes `structuredContent` with its own options (AD-5/AD-12). These are one-sentence Rule fixes, not redesigns.

Checklist coverage: (1) divergence points, (2) Rule enforceability, (3) Deferred safety, (4) stack currency and consistency, (5) brownfield ratification, (6) PRD bind coverage, (7) dimension completeness, (8) terseness and validity, (9) AD shape and ids. Verification evidence is in the last section.

---

## Critical

### C-1 — AD-4, AD-15, Stack: the pinned v1 Contracts cannot be discovered, so the exe as specified cannot start

**Gap.** The Stack pins `Hexalith.Tenants.Contracts 5.7.0` and `Hexalith.Parties.Contracts 1.1.1`, and the AD-2 graph draws `Contracts --> Abs`; but those releases carry no `[HexalithModule]` marker and no Decoration Attribute (PRD extract §D: zero `[Description]`; `Hexalith.McpCli.Abstractions` does not exist yet, PRD §7 release order), so AD-4's generator emits an empty manifest, the Catalog is empty, and the conventions row "startup fails only on an empty Catalog" makes every verb, including `config`, exit 2 until an upstream Tenants release ships — and `tests/Hexalith.McpCli.Sample.Contracts` "is never referenced by `src/`", so neither unit tests nor the AD-16 harness can exercise the executor path through the real composition root before then.

**Fix (three sentences).**
- Stack rows for Tenants and Parties Contracts: replace the fixed versions with "first release carrying `[HexalithModule]` (≥ 5.7.0 / ≥ 1.1.1; not yet published, pinned by `HexalithTenantsVersion` / `HexalithPartiesVersion` in the Builds catalog when it lands)".
- AD-3 Rule, add: "`CatalogBuilder` takes its assembly list as a constructor argument (`IReadOnlyList<Assembly>`); the composition root passes `ModuleAssemblyManifest.Assemblies`; tests pass `Hexalith.McpCli.Sample.Contracts`. The exe never references the sample."
- Catalog diagnostics convention, amend: "startup fails on an empty Catalog for `modules`, `operations`, `describe`, `send`, `query`, and `mcp` (`configuration_missing`, exit 2); `config` verbs never build the Catalog." And add an explicit sequencing line to AD-16: "The Aspire tier is enabled in `ci.yml` only after the Tenants Contracts release carrying the marker is pinned; until then `aspire-test-project` is empty and the tier does not run."

---

## High

### H-1 — AD-9 / AD-10 / AD-5: Tenant, CorrelationId and Extensions live in two records and the head does the merge

**Gap.** `EnvelopeArguments(Tenant?, …, CorrelationId?, …, Extensions?)` (per call, AD-5) and `EnvelopeContext(Tenant?, CorrelationId?, UserId?, Extensions?)` (AD-10) overlap, and AD-10 says "the head builds [EnvelopeContext] per call from settings and arguments" — so precedence between a per-call `tenant` and the Profile Tenant is applied in each head, contradicting AD-1 ("the core decides") and leaving the two heads free to merge differently; `UserId` also has no consumer (`SubmitCommandRequest` has no such member and AD-10 forbids headers reaching the executor).

**Fix.** AD-10 Rule, replace the first sentence with: "`EnvelopeContext(Tenant?)` carries only the settings-resolved Tenant from `ResolvedSettings`; `EnvelopeArguments` carries only caller-supplied values; the executor alone merges with `EnvelopeArguments.Tenant ?? EnvelopeContext.Tenant`, and a head never copies a value between the two." Drop `CorrelationId`, `UserId`, `Extensions` from `EnvelopeContext` (the HTTP release adds `UserId` when a consumer exists).

### H-2 — AD-5 / AD-12: "byte-identical" results across heads are not achievable as specified

**Gap.** `McpServerTool.Create` serializes the return value into `structuredContent` with the SDK's default options unless `McpServerToolCreateOptions.SerializerOptions` is set, and `structuredContent` is embedded in a JSON-RPC envelope where `WriteIndented` is lost; so a coding agent following AD-5 literally either cannot make the SM-4 equality test pass or writes it against a shape the MCP head cannot produce.

**Fix.** AD-12 Rule, add: "`McpServerToolCreateOptions.SerializerOptions = McpCliJson.Result`, so `structuredContent` and `OutputSchema` are produced with the same options the CLI writes with." AD-5 Rule, replace "byte-identical" with: "structurally identical: the SM-4 test compares the CLI stdout document and `structuredContent` with `JsonElement.DeepEquals` after parsing; byte identity is asserted only for CLI output across runs and operating systems (FR-5)."

### H-3 — AD-13 vs FR-12/FR-13/FR-19: "the MCP head has no flags" contradicts the `mcp` verb's options

**Gap.** `mcp` is a CLI verb that accepts `--transport`, `--read-only`, `--profile`, `--url`, `--token` (FR-13 "every verb"), so AD-13's "The MCP head has no flags; it resolves from environment and Profile at startup" leaves it undecided whether `Hexalith.McpCli.Mcp` re-resolves settings itself, which is the second resolver AD-13 exists to prevent.

**Fix.** AD-13 Rule, replace the last sentence with: "`mcp` is a CLI verb: the CLI head resolves `ResolvedSettings` once (flags, environment, Profile) and passes it to `AddMcpCliMcpServer(ResolvedSettings)`; `Hexalith.McpCli.Mcp` reads no environment variable, flag, or file; tool arguments are its only per-call source."

### H-4 — Error codes convention / AD-9: `configuration_missing` is never assigned and unexpected exceptions have no code

**Gap.** The convention lists `configuration_missing` but no AD raises it (AD-9 maps a missing Tenant to `validation_failed`; a missing URL or token is unassigned), and nothing says what a head emits when an exception escapes the executor (stack trace is forbidden by FR-11), so the two heads will pick different codes and shapes for the same failure.

**Fix.** Error codes convention, add: "`configuration_missing` is raised by `SettingsResolver` when `Url` or `Token` is unresolved after AD-13 precedence, before any Catalog or Gateway work (exit 2); a missing Tenant is `validation_failed` (FR-13). Any other exception escaping `OperationExecutor` is `internal_error` with the exception type name as `Detail` and no stack trace; the MCP head sets `isError: true`, the CLI exits 2." Add `internal_error` to the code list.

### H-5 — AD-15 / AD-16 / Open Questions: the "Tenants composition" question is answered by the referenced code and the answer strains AD-15

**Gap.** `Hexalith.Tenants.Aspire.AddHexalithTenantsServer` and `Hexalith.EventStore.Aspire.AddHexalithEventStorePlatformProjects` add source projects located through `RepositoryProjectPaths.GetReferencedModuleProjectPath` (candidate 5: `references/<repo>/src/...`), so the test AppHost builds the EventStore host, Admin server, and the `Hexalith.Tenants` server from the `references/` submodules in this repository's CI; AD-15's "never a Module ... server package" neither permits nor forbids Module server *source* entering the `tests/` build graph, and the CI checkout of those submodules (top-level only, never recursive, per `AGENTS.md`) is undecided.

**Fix.** Replace the open question with a decision in AD-16 Rule: "The AppHost composes from source: `references/Hexalith.EventStore` and `references/Hexalith.Tenants` are top-level submodules that `ci.yml` checks out (`submodules: true`, never recursive); the Tenants server and EventStore host enter the build only through the Aspire helpers' `IProjectMetadata`, never as a `ProjectReference` or `PackageReference` of any `src/` or `tests/` project." Name `Hexalith.Tenants.Aspire` explicitly in the AD-15 test allow-list.

---

## Medium

### M-1 — Operational envelope: log level, timeouts/cancellation, and CI gate inputs are silent

**Gap.** Observability decides channel and `LoggerMessage` but not the default level or how an operator raises it; the gateway `HttpClient` timeout, Ctrl+C/cancellation propagation and its exit code, and the `ci.yml` inputs (`unit-test-projects`, `coverage-minimum-line`, `aspire-test-project`) that `domain-ci.yml` requires are all undecided, so each story picks its own.

**Fix.** Add three conventions rows: "Log level: `--verbosity <level>` / `EVENTSTORE_LOG_LEVEL`, default `Warning`; Catalog diagnostics log at `Warning`/`Error` so they show by default." "Timeouts and cancellation: gateway `HttpClient.Timeout` 30 s, `EVENTSTORE_TIMEOUT_SECONDS` override, set in `AddMcpCliCore`; the host's `IHostApplicationLifetime` token flows into every executor call; a cancelled call is `OperationError(cancelled)`, exit 2." AD-17 Rule, add: "`ci.yml` passes `unit-test-projects` (every `tests/*.Tests`), `aspire-test-project: tests/Hexalith.McpCli.IntegrationTests`, `coverage-minimum-line: 80`, `coverage-line-scope: src/`, matching `Hexalith.Tenants`."

### M-2 — Open Questions / Stack: the Builds catalog is missing more than two entries

**Gap.** Central package management fails restore (NU1010) for any package without a `PackageVersion`; the catalog has no `JsonSchema.Net` (listed), no `Microsoft.Extensions.Logging.Console` (needed by AD-12's `AddConsole`; only `Logging.Abstractions` 10.0.12 is pinned), and no `Microsoft.Extensions.Logging` (Stack lists it), so the first restore fails on more than the two named additions.

**Fix.** Open question "Hexalith.Builds catalog additions": list `JsonSchema.Net 9.4.0`, `Microsoft.Extensions.Logging 10.0.12`, `Microsoft.Extensions.Logging.Console 10.0.12`, and `HexalithMcpCliVersion`; Stack row "Microsoft.Extensions.Hosting, .Http, .Logging" becomes "…, .Logging, .Logging.Console".

### M-3 — AD-2 / AD-18: no rule keeps a Contracts package built against a newer Abstractions from breaking restore or discovery

**Gap.** "Both packages share one version" under semantic-release means `Hexalith.McpCli.Abstractions` bumps on every tool release; a Module whose Contracts references a newer Abstractions than the tool's Core produces an NU1605 downgrade (an error under `TreatWarningsAsErrors`) or, across a major, attribute types the Catalog cannot bind, and PRD §7's "a Contracts Library builds unchanged across minor versions" has no enforcing rule.

**Fix.** AD-18 Rule, add: "`Hexalith.McpCli.Abstractions` is additive-only within a major (a public-API snapshot test guards it); the coverage story bumps the Abstractions pin to at least the highest version any referenced Contracts package was built against before adding the reference; a Contracts assembly compiled against a different Abstractions major is excluded with a `decoration_version` diagnostic."

### M-4 — AD-1 Rule overstates what lives in Core

**Gap.** "Every rule in FR-13 to FR-19 is implemented once, in Core" conflicts with the conventions that put exit codes (FR-14) and option parsing (FR-13) in the CLI head and `config` verbs' file writes in the CLI, so an agent reading AD-1 literally moves exit-code mapping into Core.

**Fix.** Replace with: "FR-15 to FR-17 and FR-19, the precedence of FR-13, and the file formats of FR-18 are implemented once, in Core; option parsing (FR-13), exit codes (FR-14) and `config` verbs live in the CLI head."

### M-5 — Deferred "Table column layouts per verb" lets verbs diverge

**Gap.** Column layouts are per verb and story-level, so verbs built by different agents will differ in header casing, nested-value rendering, and null rendering — a visible divergence in the one place the conventions say only the columns are declared per verb.

**Fix.** Table output convention, add: "`TableFormatter` takes `IReadOnlyList<TableColumn(Header, JsonPath)>`; headers are the camelCase result property names; nested objects and arrays render as compact `McpCliJson.Result` JSON; null renders as empty; only the column list is per verb."

### M-6 — Capability map omits NFR-3 and NFR-8, and NFR-8's lint categories are undefined

**Gap.** `binds` lists NFR-3 and NFR-8 but the map has no row for either, and the `hollow_description` check the Deferred section says "the runtime lint in `describe --lint` covers first" has no category in the diagnostics convention, so the lint's code set is open.

**Fix.** Add map rows "NFR-3 Determinism → conventions (determinism)" and "NFR-8 Description quality → `Core.Catalog` lint, conventions (diagnostics)"; extend the diagnostics convention with the lint category list: `undescribed_property`, `hollow_description`, `unmarked_identifier`.

### M-7 — AD-5 / AD-9: query metadata beyond paging is dropped without a decision

**Gap.** `EventStoreQueryResult.Metadata` carries `WarningCodes`, `IsStale`, `Provenance`, `Lifecycle` besides `Paging`; `QueryResult(CorrelationId?, Document?, Paging?)` silently discards them, and FR-14's exit 1 ("result plus a diagnostic") invites one agent to surface `WarningCodes` on stderr while another does not.

**Fix.** AD-5 Rule: `QueryResult(CorrelationId?, Document?, Paging?, Warnings?)` with `Warnings = Metadata.WarningCodes`; FR-14 convention: "Query `Warnings` are part of the result document and never change the exit code."

---

## Low

### L-1 — Stack: loose or mismatched pins

**Gap.** `Verify.XunitV3 33.x` (catalog: 33.0.2), `Aspire.AppHost.Sdk 13.5.x` (sibling: 13.5.3), `CommunityToolkit.Aspire.Hosting.Dapr 13.5.1-beta` (catalog: 13.5.1-beta.757) are the only non-exact rows in a table that is otherwise exact.

**Fix.** Write `33.0.2`, `13.5.3`, `13.5.1-beta.757`.

### L-2 — Identifier generation convention: two ULID libraries in the closure

**Gap.** `Hexalith.EventStore.Client` transitively brings `NUlid 1.7.3`, whose `NUlid.Ulid` type name collides with `ByteAether.Ulid.Ulid`; Core references both, so an agent adding `using NUlid;` gets an ambiguous `Ulid` and may switch libraries in one file.

**Fix.** Convention row, add: "`ByteAether.Ulid.Ulid` only, imported through one `global using`; `NUlid` is never imported in this solution."

### L-3 — AD-4: `typeof(<first decorated type>)` assumes a public type

**Gap.** An `internal` decorated type makes the generated manifest fail to compile in the exe.

**Fix.** AD-4 Rule: "emits `typeof(<first public decorated type>).Assembly`; a marked assembly with no public decorated type is generator diagnostic `MCPCLI001`."

### L-4 — AD-14: file permissions named for one of the two files

**Gap.** Mode 600/700 is stated for `profiles.json` only; `mcpcli.json` holds no secret but the omission reads as a decision.

**Fix.** "…file mode 600 and directory 700 on non-Windows for both files".

### L-5 — AD-17 / Structural Seed: release tooling files the sibling `.releaserc.json` calls are not in the seed

**Gap.** The sibling `.releaserc.json` invokes `tools/pack-release-packages.py`, `tools/validate-release-packages.py`, and `scripts/validate-release-secrets.sh`; the seed lists only `tools/release-packages.json`, so the first release story guesses which to copy.

**Fix.** Seed: add `tools/pack-release-packages.py  tools/validate-release-packages.py  scripts/validate-release-secrets.sh  # copied from Hexalith.Tenants`.

### L-6 — AD-9 title carries `[ADOPTED]`; no other AD has a status tag

**Gap.** Inconsistent metadata reads as template residue.

**Fix.** Remove the tag, or tag every AD.

### L-7 — AD-3: `Submittable` shape and reasons are unstated

**Gap.** FR-19 requires `submittable: false, reason: read_only`; the descriptor has a bare `Submittable`.

**Fix.** `Submittable(bool Value, string? Reason)`; v1 reasons: `read_only`.

### L-8 — NFR-2 test: what is counted is unspecified

**Gap.** "the five definitions total under 8,000 characters (a test counts)" does not say which serialization is measured.

**Fix.** "…measured on the `tools/list` result serialized with `McpCliJson.Result` without indentation".

---

## Checklist pass/fail summary

| # | Criterion | Result |
| --- | --- | --- |
| 1 | Fixes the real divergence points, misses none | Mostly; H-1, H-3, H-4, M-1, M-5 are missed seams |
| 2 | Every Rule enforceable and preventive | Mostly; AD-5 (H-2), AD-10 (H-1), AD-13 (H-3), AD-1 (M-4) not as written |
| 3 | Deferred cannot let units diverge | One item (M-5); the rest are additive ports/adapters or single stories |
| 4 | Technology verified-current, internally consistent | Yes (see evidence); L-1 loose pins; M-2 missing catalog pins |
| 5 | Ratifies the brownfield ecosystem | Yes; H-5 is a decision the ecosystem already made that the spine leaves open |
| 6 | Covers the PRD capabilities in `binds` | Yes, except NFR-3/NFR-8 rows (M-6) |
| 7 | Every owned dimension decided/deferred/open | Deployment, environments, provider, security, configuration, error handling, testing: decided. Observability and operations partly silent (M-1) |
| 8 | Terse, no placeholders, valid mermaid, no empty sections | Yes; three mermaid blocks parse; `[ADOPTED]` tag (L-6) |
| 9 | Binds/Prevents/Rule on every AD; ids unique ascending | Yes, AD-1..AD-18 |

## Verification evidence (read-only, `references/` and local caches)

- `IEventStoreGatewayClient`: `SubmitCommandAsync`, `GetCommandStatusAsync`, `SubmitQueryAsync`, `ReadStreamAsync`; `AddEventStoreGatewayClient` returns `IHttpClientBuilder` via `AddHttpClient<IEventStoreGatewayClient, EventStoreGatewayClient>` — AD-9, AD-10, AD-11 ratified.
- `SubmitCommandRequest(MessageId, Tenant, Domain, AggregateId, CommandType, Payload, CorrelationId?, Extensions?, IdempotencyKey?)`; `SubmitCommandResponse(CorrelationId, ResultPayload?, MessageId?)`; `SubmitQueryRequest(Tenant, Domain, AggregateId, QueryType, ProjectionType?, Payload?, EntityId?, ProjectionActorType?){Paging, Search, Filters, OrderBy, Freshness}`; `EventStoreQueryResult(CorrelationId?, Payload, IsNotModified, ETag){Metadata}` with `QueryResponseMetadata.Paging` — AD-5/AD-9 mapping exists (M-7 notes the dropped members).
- `ICommandContract`: static `CommandType`, `Domain`, instance `AggregateId`; `IQueryContract`: static `QueryType`, `Domain`, `ProjectionType` — routing convention ratified.
- `EventStorePayloadSerialization`: readers `JsonSerializerDefaults.Web` (case-insensitive), writers keep PascalCase — AD-6 `Payload` policy ratified.
- Admin CLI `ProfileManager`: `version` 1, `activeProfile`, `profiles`, `UnixFileMode` 600/700, `^[a-zA-Z0-9_-]{1,64}$` — AD-14 ratified.
- Admin MCP `Program.cs`: `Host.CreateApplicationBuilder`, `ClearProviders()`, `LogToStandardErrorThreshold = LogLevel.Trace`, `WithStdioServerTransport()` — AD-12 ratified.
- `Hexalith.EventStore.RestApi.Generators`: `netstandard2.0`, `IsRoslynComponent`, `EnforceExtendedAnalyzerRules`, `compilation.SourceModule.ReferencedAssemblySymbols` — AD-4/AD-18 recipe ratified.
- `AspireTopologyFixtureBase<TAppHost>` (abstract `Resources`, `SkipIfUnavailable`, Dapr placement/scheduler checks); `FakeEventStoreGatewayClient` in `Hexalith.EventStore.Testing` — AD-16 ratified.
- `Hexalith.Tenants.AppHost` + `Hexalith.Tenants.Aspire.TenantsServerProjectMetadata` → `RepositoryProjectPaths.GetReferencedModuleProjectPath` (source checkout under `references/`) — basis of H-5.
- Tenants and Parties Contracts reference only `Hexalith.EventStore.Contracts`; `net10.0` from `Directory.Build.props` — AD-15 closure and the attribute convention hold for real packages.
- Builds catalog (`Props/Directory.Packages.props`): ModelContextProtocol 2.2.0, System.CommandLine 2.0.12, ByteAether.Ulid 1.4.1, NUlid 1.7.3, Microsoft.Extensions.Hosting/Http/Configuration 10.0.12, Logging.Abstractions 10.0.12 (no `Logging`, no `Logging.Console`, no `JsonSchema.Net`), Microsoft.CodeAnalysis.CSharp/Analyzers 5.9.0, xunit.v3 4.0.1, Shouldly 4.3.0, NSubstitute 6.2.0, Verify.XunitV3 33.0.2, Aspire.Hosting(.Testing) 13.5.4, CommunityToolkit.Aspire.Hosting.Dapr 13.5.1-beta.757, HexalithEventStoreVersion 3.106.0, HexalithTenantsVersion 5.7.0, HexalithPartiesVersion 1.1.1; `global.json` 10.0.401 with `Microsoft.Testing.Platform` — Stack rows match except L-1 and M-2.
- SDK 10.0.401 bundles Roslyn 5.9.0-1.26423.113, so a generator/analyzer built against Microsoft.CodeAnalysis 5.9.0 loads under the pinned compiler.
- `ModelContextProtocol.Core 2.2.0` assembly contains protocol revision `2026-07-28` and the `UseStructuredContent`, `OutputSchema`, `ReadOnly`, `Destructive`, `Idempotent`, `WithListToolsHandler`, `WithStdioServerTransport` members AD-12 names.
- `domain-ci.yml`: `aspire-test-project` input, `dapr-init` before the Aspire tier, `-warnaserror` build; sibling `ci.yml` passes `unit-test-projects`, `coverage-minimum-line`, `coverage-line-scope` — basis of M-1's CI item.
- `.releaserc.json` (EventStore): `tagFormat v${version}`, `tools/pack-release-packages.py`, `tools/validate-release-packages.py`, `scripts/validate-release-secrets.sh` — basis of L-5.
