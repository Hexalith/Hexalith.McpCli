---
review: tech-currency
target: ARCHITECTURE-SPINE.md (Hexalith.McpCli, 2026-09-22)
reviewer-brief: every committed decision web-researched or reality-checked, not asserted from training data
date: 2026-09-22
verdict: pass with one blocking contradiction (Projects.Contracts closure) and two catalog gaps that would fail restore
---

# Tech-currency review — Hexalith.McpCli architecture spine

Sources used, in order of authority: the memlog `(version)` and `REALITY` entries (not repeated here), the Hexalith.Builds catalog `references/Hexalith.Builds/Props/Directory.Packages.props`, reference code under `references/`, then nuget.org / Microsoft Learn / modelcontextprotocol.io / GitHub for anything not covered.

## 1. Item table

Status: **confirmed** (evidence found, statement correct), **corrected** (statement wrong or imprecise; fix given in section 2), **unconfirmed** (no evidence either way; low risk unless noted).

### Versions (Stack table)

| Item | Spine says | Status | Source |
| --- | --- | --- | --- |
| .NET SDK | 10.0.401, MTP runner | confirmed | `references/Hexalith.Builds/global.json`: `"version": "10.0.401"`, `"test": {"runner": "Microsoft.Testing.Platform"}` |
| C# | 14 | confirmed | .NET 10 default language version (memlog constraint; SDK 10.0.4xx) |
| ModelContextProtocol | 2.2.0, MCP 2026-07-28 | confirmed | nuget: 2.2.0 released 2026-08-13; csharp-sdk releases: 2.0.0 "stable alignment with the MCP 2026-07-28 specification", 2.2.0 hybrid 2025-11-25/2026-07-28 HTTP serving; catalog pin 2.2.0 |
| ModelContextProtocol.Core | 2.2.0 (listed as its own row) | **corrected** | nuget: package exists (2.2.0) but the catalog has no `PackageVersion` for it; CPM with `CentralPackageVersionOverrideEnabled=false` refuses an unpinned direct reference (NU1010). See H-1 |
| System.CommandLine | 2.0.12 | confirmed | catalog pin 2.0.12 (with ADR comment); memlog web check |
| Hexalith.EventStore.Client / .Contracts | 3.106.0 | confirmed | catalog `HexalithEventStoreVersion` 3.106.0; nuget 3.106.0 published 2026-09-16 |
| Hexalith.Tenants.Contracts | 5.7.0 | confirmed | catalog `HexalithTenantsVersion` 5.7.0; csproj depends only on `Hexalith.EventStore.Contracts` |
| Hexalith.Parties.Contracts | 1.1.1 | confirmed | catalog `HexalithPartiesVersion` 1.1.1; csproj depends only on `Hexalith.EventStore.Contracts` |
| Hexalith.Projects.Contracts (AD-2 diagram, not in Stack table) | 1.0.0 implied | **corrected** | catalog 1.0.0; nuget 1.0.0 (2026-09-20) has 22 dependencies incl. `Fluxor.Blazor.Web`, `Microsoft.FluentUI.AspNetCore.Components`, `Hexalith.FrontComposer.Shell`, `Microsoft.AspNetCore.Authentication.OpenIdConnect`, `System.IdentityModel.Tokens.Jwt`, `NUlid`; csproj has `<FrameworkReference Include="Microsoft.AspNetCore.App" />`. See C-1 |
| Hexalith.Folders.Contracts (AD-2 diagram, not in Stack table) | 1.0.0 implied | confirmed, with note | catalog 1.0.0; nuget 1.0.0 (2026-09-19) zero dependencies; csproj references nothing (not even EventStore.Contracts). See L-6 |
| ByteAether.Ulid | 1.4.1 | confirmed | catalog 1.4.1; nuget latest 1.4.1 (2026-09-14); README shows `Ulid.New(...)`, `Ulid.Parse(...)`, `Ulid.TryParse(string? s, ...)`. Ecosystem split noted in L-3 |
| JsonSchema.Net | 9.4.0, new central pin | confirmed | nuget latest 9.4.0 (2026-07-26); not in catalog (spine already says so); TFMs net8.0/net9.0/netstandard2.0, sole dependency JsonPointer.Net >= 7.0.2 (transitive, no pin needed) |
| Microsoft.Extensions.Hosting / .Http | 10.0.12 | confirmed | catalog 10.0.12 |
| Microsoft.Extensions.Logging | 10.0.12 | **corrected** | catalog pins only `Microsoft.Extensions.Logging.Abstractions`; no `Microsoft.Extensions.Logging` or `.Logging.Console` pin. See M-1 |
| Microsoft.CodeAnalysis.CSharp / .Analyzers | 5.9.0 | confirmed | catalog 5.9.0 both; nuget Analyzers 5.9.0 exists (2026-08-17); catalog comment ties Roslyn pin to the global.json compiler host; `Hexalith.EventStore.RestApi.Generators` builds netstandard2.0 against the same pin |
| xunit.v3 / Shouldly / NSubstitute | 4.0.1 / 4.3.0 / 6.2.0 | confirmed | catalog |
| Verify.XunitV3 | 33.x | confirmed, tighten | catalog 33.0.2 (depends on `xunit.v3.extensibility.core >= 4.0.1`, compatible); nuget latest 33.1.1 (2026-09-20). Write the catalog pin. See L-4 |
| Aspire.Hosting.Testing | 13.5.4 | confirmed | catalog 13.5.4 |
| Aspire.AppHost.Sdk | 13.5.x | confirmed, tighten | nuget latest 13.5.4 (2026-09-15); siblings use `<Project Sdk="Aspire.AppHost.Sdk/13.5.3">` (Tenants) and `/13.5.4` (others); SDK version is inline in the csproj, not in the catalog. See M-3 |
| CommunityToolkit.Aspire.Hosting.Dapr | 13.5.1-beta | confirmed | catalog `13.5.1-beta.757` |
| Hexalith.EventStore.Testing / .Testing.Integration / .Aspire | 3.106.0, tests only | confirmed | catalog; nuget: `.Testing.Integration` 3.106.0 (2026-09-16), `.Aspire` 3.106.0 (2026-09-16); both listed in `references/Hexalith.EventStore/tools/release-packages.json` |
| HexalithMcpCliVersion catalog property | to be added upstream | confirmed absent | catalog has no such property (spine already lists it as an open question) |
| Hexalith.McpCli package id | new | confirmed free | nuget.org returns 404 for `Hexalith.McpCli`; no sibling `ToolCommandName` is `hexalith` (siblings: `eventstore-admin`, `folders`, `memories`, `frontcomposer`, `hexalith-module`, `hexalith-evidence`) |

### API names and members

| Item | Where | Status | Source |
| --- | --- | --- | --- |
| `McpServerTool.Create(Delegate, McpServerToolCreateOptions)` | AD-12 | confirmed | csharp-sdk `main` `McpServerTool.cs`: `Create(Delegate method, McpServerToolCreateOptions? options = null)` plus MethodInfo and AIFunction overloads |
| `McpServerToolCreateOptions.{ReadOnly, Destructive, Idempotent, UseStructuredContent, OutputSchema}` | AD-12 | confirmed | `McpServerToolCreateOptions.cs`: `ReadOnly bool?`, `Destructive bool?`, `Idempotent bool?`, `OpenWorld bool?`, `UseStructuredContent bool`, `OutputSchema JsonElement?`, `Title`, `Icons`, `Meta` |
| `WithStdioServerTransport()`, `WithListToolsHandler` | AD-12 | confirmed | `Hexalith.EventStore.Admin.Mcp/Program.cs` uses `WithStdioServerTransport()`; `Hexalith.Parties.Mcp` uses `.WithListToolsHandler(ListToolsAsync)` |
| `LogToStandardErrorThreshold = Trace` after `ClearProviders()` | AD-12 | confirmed | `Admin.Mcp/Program.cs`: `builder.Logging.ClearProviders(); builder.Logging.AddConsole(options => options.LogToStandardErrorThreshold = LogLevel.Trace);` |
| `Host.CreateApplicationBuilder` | AD-11 | confirmed | same file |
| `JsonSchemaExporter.GetJsonSchemaAsNode(options, type)` + `TransformSchemaNode` | AD-7 | confirmed | Microsoft Learn "JSON schema exporter": `options.GetJsonSchemaAsNode(typeof(T), exporterOptions)`; `JsonSchemaExporterOptions.TransformSchemaNode` delegate; description added via transform (not native) |
| `UnmappedMemberHandling = Disallow` yields `additionalProperties: false` | AD-6/AD-7 | confirmed | same page, `CustomExtraction()` sample output shows `"additionalProperties": false` with `JsonUnmappedMemberHandling.Disallow`; the transform in AD-7 that also adds it is therefore redundant but harmless |
| JsonSchema.Net `List` output mode, `InstanceLocation` | AD-7 | confirmed, wording | docs.json-everything.net: `OutputFormat` = `Flag`, `List`, `Hierarchical`; results carry `instanceLocation` as a **JSON Pointer** (RFC 6901), not a JSON path. See L-1 |
| `Ulid.New()`, `Ulid.TryParse` | conventions | confirmed | ByteAether.Ulid README; `Hexalith.Commons.UniqueIds` calls `BaUlid.New(...)` and `BaUlid.Parse(ulid.ToUpperInvariant(), ...)`. See L-3 on case handling |
| `IEventStoreGatewayClient.SubmitCommandAsync/SubmitQueryAsync/GetCommandStatusAsync`, `EventStoreGatewayException`, `SubmitCommandRequest`, `SubmitQueryRequest`, `api/v1/commands`, `api/v1/queries` | AD-9, Deferred, runtime view | confirmed | `Hexalith.EventStore.Client/Gateway/*.cs`, `Hexalith.EventStore.Contracts/Commands|Queries/*.cs`, `EventStoreGatewayClientOptions.CommandPath/QueryPath` |
| `FakeEventStoreGatewayClient` | AD-16 | confirmed | `Hexalith.EventStore.Testing/Fakes/FakeEventStoreGatewayClient.cs` |
| `AspireTopologyFixtureBase<TAppHost>` | AD-16 | confirmed | `Hexalith.EventStore.Testing.Integration/AspireTopologyFixtureBase.cs` (`IAsyncLifetime`) |
| `Projects.Hexalith_McpCli_AppHost` marker naming | AD-16 | confirmed by pattern | Tenants: `AspireTopologyFixtureBase<Projects.Hexalith_Tenants_AppHost>`; Aspire generates `Projects.<AssemblyName with '.'→'_'>` from a `ProjectReference` to the AppHost plus `Aspire.Hosting.Testing` |
| "standard Dapr prerequisite check" | AD-16 | confirmed | `DaprFactAttribute` (`SkipUnless = nameof(DaprTestPrerequisites.IsAvailable)`) |
| `[Trait("Category", "Integration")]` | conventions | confirmed | used in Tenants/EventStore tests |
| `compilation.SourceModule.ReferencedAssemblySymbols` | AD-4 | confirmed | `RestApiMessageParser.cs:55` |
| `ProjectReference OutputItemType="Analyzer" ReferenceOutputAssembly="false"` | AD-4 | confirmed | same pattern in `Hexalith.Projects.Contracts.csproj` (FrontComposer.SourceTools) |
| Profile schema `version: 1`, `activeProfile`, `profiles.{name}.{url,token,format}`, 600/700, `^[a-zA-Z0-9_-]{1,64}$`, `MaskToken` | AD-14, conventions | confirmed | `Admin.Cli/Profiles/ProfileManager.cs`, `ProfileStore.CurrentVersion = 1` |
| Default URL `http://localhost:8080` | AD-13 | confirmed | `Hexalith.EventStore/Properties/launchSettings.json` `applicationUrl: http://localhost:8080`; admin CLI's own default is `http://localhost:5002` (admin API, different surface) |
| `EVENTSTORE_*` env names | AD-13 | unconfirmed (new) | admin CLI uses `EVENTSTORE_ADMIN_*`; no collision; the plain `EVENTSTORE_*` family is this tool's own, from the PRD |

### MSBuild properties, packaging, CI, release

| Item | Where | Status | Source |
| --- | --- | --- | --- |
| `PackAsTool`, `ToolCommandName` | AD-17 | confirmed | `Admin.Cli.csproj` and five other sibling tools |
| `CreateRidSpecificToolPackages = false` + `UseAppHost = false` | AD-17 | confirmed | Microsoft Learn breaking change "dotnet-tool-pack-publish" (.NET 10): to keep framework-dependent, platform-agnostic tools "add `<CreateRidSpecificToolPackages>false</CreateRidSpecificToolPackages>` and `<UseAppHost>false</UseAppHost>`". Both only matter when `RuntimeIdentifiers` is set; no sibling tool sets either. See L-7 |
| `ToolPackageRuntimeIdentifiers`, `PublishTrimmed`, `PublishAot`, `TrimmerRootAssembly` | AD-17, Deferred | confirmed | Microsoft Learn "rid-specific-tools" names the first three; `TrimmerRootAssembly` is a standard ILLink item |
| `IsRoslynComponent`, `EnforceExtendedAnalyzerRules`, `PrivateAssets="all"`, `analyzers/dotnet/cs` | AD-4, AD-18 | confirmed | `Hexalith.EventStore.RestApi.Generators.csproj` (netstandard2.0, both properties, `PackagePath="analyzers/dotnet/cs"`) |
| Three-path import of the catalog, `HexalithVersionsLoaded` | conventions, seed | confirmed | `Hexalith.Tenants/Directory.Build.props` |
| `tests/Directory.Build.props` injecting xunit.v3/Shouldly/NSubstitute | conventions | confirmed | Tenants copy also adds `Microsoft.NET.Test.Sdk`, `xunit.runner.visualstudio`, `Microsoft.Testing.Extensions.CodeCoverage`, `<Using Include="Xunit" />` |
| `ci.yml` → `Hexalith/Hexalith.Builds/.github/workflows/domain-ci.yml@main`, `aspire-test-project` tier, ubuntu-latest, `-warnaserror`, dapr-init | AD-16, AD-17, runtime view | confirmed | `Hexalith.Tenants/.github/workflows/ci.yml`; `domain-ci.yml` inputs `aspire-test-project`, `dapr-version`, `runs-on: ubuntu-latest`, `dotnet build ... -warnaserror`, `dapr-init` action |
| semantic-release, `tagFormat v${version}`, `dotnet build <slnx> -p:Version=${nextRelease.version}`, `tools/release-packages.json`, push to nuget.org, `workflow_dispatch` | AD-17 | confirmed, incomplete | `Hexalith.Tenants/.releaserc.json`; prepareCmd also runs `scripts/pack-release-packages.py ./nupkgs ${nextRelease.version}` and two validation scripts, and verify/publish run `scripts/validate-release-secrets.sh` / `validate-publication-preflight.sh`. See L-5 |
| `.slnx` | seed | confirmed | siblings build `Hexalith.Tenants.slnx` |
| MCP protocol facts behind AD-12 (fixed list, per-process read-only, stderr logging) | AD-12 | confirmed, with new obligations | modelcontextprotocol.io 2026-07-28 changelog: `tools/list` "no longer vary per-connection"; results of `tools/list` require `ttlMs` and `cacheScope`; servers SHOULD return tools in deterministic order; Logging feature deprecated, "log to stderr (stdio)"; csharp-sdk 2.x: "Require `Tool.inputSchema` during deserialization". See M-2 |

## 2. Findings

### Critical

**C-1 — `Hexalith.Projects.Contracts` 1.0.0 cannot be referenced under AD-15 / NFR-6 as published.**
AD-2 puts `Projects` in the exe's `*.Contracts` package set and FR-20 counts it as a v1 Module, but the live package (nuget 1.0.0, 2026-09-20, and `references/Hexalith.Projects/src/Hexalith.Projects.Contracts/Hexalith.Projects.Contracts.csproj`) carries `<FrameworkReference Include="Microsoft.AspNetCore.App" />`, `Fluxor.Blazor.Web`, `Microsoft.FluentUI.AspNetCore.Components`, `Hexalith.FrontComposer.Shell`, `Hexalith.Conversations.Contracts`, `Microsoft.AspNetCore.Authentication.OpenIdConnect`, the `Microsoft.IdentityModel.*` set, `System.IdentityModel.Tokens.Jwt`, `System.Reactive`, and both `NUlid` and `ByteAether.Ulid`. Referencing it breaks AD-15's closure rule ("from Hexalith, only `Hexalith.EventStore.Client`, the referenced `*.Contracts` packages, and their transitive EventStore contract packages") the moment it is added, and the ASP.NET Core framework reference makes the framework-dependent global tool require the ASP.NET Core shared runtime on every developer and agent machine (NFR-6).
*Correction:* (a) In AD-15 add the enforcement: "A test walks the tool project's resolved package closure and fails on any `FrameworkReference` other than `Microsoft.NETCore.App` and on any Hexalith package outside `Hexalith.EventStore.Client`, `Hexalith.EventStore.Contracts`, `Hexalith.McpCli.Abstractions`, and `*.Contracts`." (b) In AD-2 and the Capability map, scope FR-20's v1 set to Tenants and Parties, and move `Projects` (and `Folders`, see L-6) to Deferred with the entry: "`Hexalith.Projects.Contracts` joins when upstream ships a Contracts package with no ASP.NET, UI, or identity dependencies; tracked as an upstream issue (FR-22)." (c) Add the Stack rows `Hexalith.Projects.Contracts 1.0.0 (blocked, see AD-15)` and `Hexalith.Folders.Contracts 1.0.0`.

### High

**H-1 — `ModelContextProtocol.Core` is listed as a stack pin but is not in the Hexalith.Builds catalog.**
The catalog pins `ModelContextProtocol` 2.2.0 and `ModelContextProtocol.AspNetCore` 2.2.0 only. With `ManagePackageVersionsCentrally=true` and `CentralPackageVersionOverrideEnabled=false`, a direct `<PackageReference Include="ModelContextProtocol.Core" />` fails restore (NU1010). `AddMcpServer`, `WithStdioServerTransport`, and the hosting extensions live in `ModelContextProtocol`, which depends on Core; nothing in the spine needs Core directly.
*Correction:* Stack row becomes `ModelContextProtocol | 2.2.0 (MCP 2026-07-28; brings ModelContextProtocol.Core transitively)`. In AD-1's rule, keep "Core references no MCP package" as is. If a direct Core reference is ever wanted, add it to the Open Question "Hexalith.Builds catalog additions" next to `JsonSchema.Net`.

### Medium

**M-1 — `Microsoft.Extensions.Logging` 10.0.12 is not a catalog pin.**
Only `Microsoft.Extensions.Logging.Abstractions`, `Hosting`, `Http` are pinned. `Hosting` brings `Logging` and `Logging.Console` transitively, which is all AD-12 needs (`AddConsole`, `LogToStandardErrorThreshold`).
*Correction:* Stack row `Microsoft.Extensions.Hosting, .Http, .Logging.Abstractions | 10.0.12` and a conventions note: "Core references `Microsoft.Extensions.Logging.Abstractions` only; the console provider comes through `Microsoft.Extensions.Hosting` in the exe. No direct `Microsoft.Extensions.Logging` reference (not catalogued)."

**M-2 — AD-12's custom list-tools handler has three obligations under MCP 2026-07-28 / csharp-sdk 2.x that the spine does not state.**
(1) csharp-sdk 2.x requires `Tool.inputSchema` on every tool it deserializes; the fixed set must carry the input schema for each of the five tools (an empty object schema is acceptable for `list_modules`). (2) `tools/list` results must carry `ttlMs` and `cacheScope`, and the spec now says tools "no longer vary per-connection": omitting `send_command` is allowed only because Read-only Mode is a process-level startup setting, never per call. (3) Deterministic order is now a spec SHOULD, which the spine already satisfies. Also note the 2.x behavior change: with `UseStructuredContent = true`, non-object return types are emitted raw; the AD-5 records are objects, so unaffected.
*Correction:* Append to AD-12's rule: "The list handler returns each tool with its `inputSchema` (required by the SDK) and sets the 2026-07-28 `ttlMs`/`cacheScope` fields (`cacheScope: private`, `ttlMs` equal to the process lifetime hint the SDK defaults to); Read-only Mode is resolved once at startup, so the list is identical for every client of a process, as the 2026-07-28 revision requires."

**M-3 — `Aspire.AppHost.Sdk` "13.5.x" should be an exact inline pin, and it is not catalogued.**
The AppHost SDK version lives in the csproj `Sdk="Aspire.AppHost.Sdk/<version>"` attribute, outside the catalog; siblings drift (Tenants 13.5.3, others 13.5.4). Latest is 13.5.4 (2026-09-15), matching the catalogued `Aspire.Hosting.Testing` 13.5.4.
*Correction:* Stack row `Aspire.AppHost.Sdk | 13.5.4 (inline `Sdk="Aspire.AppHost.Sdk/13.5.4"` in `tests/Hexalith.McpCli.AppHost`, kept equal to the `Aspire.Hosting.Testing` catalog pin)`.

### Low

**L-1 — `InstanceLocation` is a JSON Pointer, not a JSON path.** AD-7 says "reports `InstanceLocation` as the JSON path". JsonSchema.Net returns an RFC 6901 pointer (`/Name`, `/Items/0/Id`). *Correction:* "reports `InstanceLocation` (an RFC 6901 JSON Pointer) as the violation path" and state that `OperationError.Violations[].Path` carries that pointer verbatim so both heads print the same string.

**L-2 — `additionalProperties: false` is emitted natively.** AD-7's transform lists it as something the transform adds; the exporter already emits it under `UnmappedMemberHandling = Disallow` (Microsoft Learn sample). Harmless; *correction:* drop it from the transform's list or say "confirms".

**L-3 — ULID case handling.** `Hexalith.Commons.UniqueIds` upper-cases before `ByteAether.Ulid.Parse`, indicating the parser expects canonical uppercase. Half the ecosystem uses `NUlid` (Tenants.UI, FrontComposer, Agents); wire format is identical (26-char Crockford base32), so interoperability holds. *Correction:* conventions row "Identifier generation": add "validation upper-cases the input before `Ulid.TryParse`, as `Hexalith.Commons.UniqueIds` does, and the Schema `pattern` is `^[0-9A-HJKMNP-TV-Z]{26}$` (case-insensitive flag not available in JSON Schema; document that lower-case ids are accepted by the validator after normalization or rejected consistently in both heads — pick one)."

**L-4 — Verify.XunitV3 pin.** Write the catalog pin `33.0.2` (latest 33.1.1 exists; the catalog decides).

**L-5 — Release prepareCmd is more than `dotnet build -p:Version`.** Siblings run `scripts/pack-release-packages.py ./nupkgs ${nextRelease.version}`, `validate-nuget-packages.py`, `validate-consumer-package-references.py`, and the `validate-release-secrets.sh` / `validate-publication-preflight.sh` gates. *Correction:* AD-17: "`.releaserc.json` copied from `Hexalith.Tenants` with the container-publisher steps removed; prepareCmd builds, then packs through `scripts/pack-release-packages.py` over `tools/release-packages.json`."

**L-6 — `Hexalith.Folders.Contracts` 1.0.0 has no dependencies at all**, not even `Hexalith.EventStore.Contracts`, so it cannot implement `ICommandContract` today and yields nothing to discover until it references `Hexalith.McpCli.Abstractions`. Consistent with Deferred ("added when each becomes Gateway-ready") but inconsistent with AD-2's diagram naming it as a v1 Contracts package. *Correction:* same scoping as C-1(b).

**L-7 — `UseAppHost=false` / `CreateRidSpecificToolPackages=false` are correct but idle.** They only change behavior when `RuntimeIdentifiers` is set; no sibling tool sets them. Keep them (they guard against a future RID addition) and add "no `RuntimeIdentifiers`" to the AD-17 rule so the guard's purpose is explicit.

**L-8 — Integration test project needs the ASP.NET shared framework.** `Hexalith.EventStore.Testing.Integration` references `Hexalith.EventStore.Server`, `.DomainService`, and `Dapr.Actors.AspNetCore`; `Hexalith.Tenants.IntegrationTests` adds `<FrameworkReference Include="Microsoft.AspNetCore.App" />` and a `ProjectReference` to the AppHost. *Correction:* AD-16 seed note: "IntegrationTests carries `FrameworkReference Microsoft.AspNetCore.App` and a `ProjectReference` to `tests/Hexalith.McpCli.AppHost` (the Aspire `Projects.*` marker source); this is the test closure, not the tool closure (AD-15)."

**L-9 — `Hexalith.EventStore.Aspire` carries prerelease Aspire integrations** (`Aspire.Hosting.Keycloak` 13.5.4-preview, `CommunityToolkit.Aspire.Hosting.Dapr` 13.5.1-beta) and suppresses NU5104 locally. The test AppHost will need the same `NoWarn` or it fails under `TreatWarningsAsErrors`. *Correction:* AD-16: "`tests/Hexalith.McpCli.AppHost` sets `<NoWarn>$(NoWarn);NU5104</NoWarn>` as `Hexalith.EventStore.Aspire` does."

## 3. Not re-verified (already in memlog and consistent with what was found)

.NET SDK/MTP runner, System.CommandLine 2.0.12, xunit.v3/Shouldly/NSubstitute versions, Aspire 13.5.4, Dapr toolkit pin, Roslyn 5.9.0, Microsoft.Extensions 10.0.12, JsonSchema.Net 9.4.0, `McpServerTool.Create` shape, `StdioServerTransport` stdout behavior, JsonSchemaExporter 2020-12 behavior, gateway client records and options, EventStore serialization facts, sibling CI/release shape, `TenantIdentity.DefaultTenantId = "system"`.
