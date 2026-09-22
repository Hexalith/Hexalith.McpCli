---
title: "Validation reviewer: technology and reality"
target: ARCHITECTURE-SPINE.md
date: '2026-09-22'
lens: technology-reality
intent: validate
verdict: needs-update
findings:
  critical: 0
  high: 2
  medium: 2
  low: 1
---

# Technology and reality review

## Verdict

**Needs update: 2 High, 2 Medium, and 1 Low finding.** The platform and package stack is largely real, current, and compatible with `net10.0`; the two material gaps are the live ModelContextProtocol tool-registration behavior and a second EventStore gateway extension-metadata validation layer that AD-9 does not model. No Critical finding was found.

Status terms in this report:

- **Verified** — confirmed against official current documentation/package metadata and/or the checked-in source that owns the behavior.
- **Stale** — a stated version or behavior no longer matches the authority it cites.
- **Unverified** — no landed local authority exists yet; the spine must keep it open rather than presenting it as implemented reality.
- **Internally inconsistent** — two statements or a statement and its cited runtime behavior cannot both hold without an additional decision.

## Findings

### TR-001 — High — MCP tool registration and the custom list handler are not wired to a compatible SDK model

- **Status:** Internally inconsistent with live SDK behavior
- **Spine:** `ARCHITECTURE-SPINE.md:121-125`, especially line 125
- **Disposition:** **Discuss**

AD-12 says five tools are constructed as `McpServerTool` instances and a custom list-tools handler returns their full `Tool` records, omitting `send_command` in Read-only Mode. ModelContextProtocol 2.2.0 does not treat a custom handler as a replacement for a registered `ToolCollection`: it invokes the custom handler and then appends every registered tool to its result. The SDK also uses that collection for call dispatch. See the official 2.2.0 sources for [`McpServerImpl.ConfigureTools`](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerImpl.cs#L1464-L1527), [`McpServerOptions.ToolCollection`](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerOptions.cs#L145-L156), and [`WithListToolsHandler`](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol/McpServerBuilderExtensions.cs#L600-L630).

If the five constructed tools are registered in `ToolCollection` and also returned by the custom handler, `tools/list` contains duplicates. More seriously, the SDK appends the registered `send_command` after a Read-only handler has omitted it, so the advertised list violates AD-12. If the tools are kept out of `ToolCollection`, automatic call dispatch is absent and AD-12 must bind a custom `WithCallToolHandler` that resolves and invokes the same instances; it currently does not.

Choose and bind one compatible model:

1. Populate `ToolCollection` once with the already-filtered four-or-five tools, preserve insertion order, and use the SDK's built-in list and call dispatch with no custom list handler; or
2. Keep `ToolCollection` null, make the custom list handler the sole advertiser, and add a custom call handler that dispatches to the exact same tool map.

The first is simpler. Add a test that requests `tools/list` in both modes and asserts unique names, fixed order, and absence of `send_command` under Read-only Mode.

### TR-002 — High — AD-9 models only one of the gateway's two extension-validation layers

- **Status:** Stale/incomplete reality model
- **Spine:** `ARCHITECTURE-SPINE.md:103-107`, especially line 107
- **Disposition:** **Discuss**

AD-9 copies the structural `SubmitCommandRequestValidator` limits: 50 entries, 100 characters per key, 1,000 per value, and 65,536 combined UTF-8 bytes. Those constants are real in both the current checkout and the exact `v3.106.0` tag (`references/Hexalith.EventStore/src/Hexalith.EventStore/Validation/SubmitCommandRequestValidator.cs:17-20,81-91`). They are not the complete effective gateway contract.

`CommandsController` then invokes `ExtensionMetadataSanitizer` (`references/Hexalith.EventStore/src/Hexalith.EventStore/Controllers/CommandsController.cs:90-110`). Its defaults are configuration-bound and are 32 entries and 4,096 total bytes (`references/Hexalith.EventStore/src/Hexalith.EventStore/Configuration/ExtensionMetadataOptions.cs:7-28`); it also applies a key grammar plus control-character, XSS, SQL, LDAP, and path-traversal checks (`references/Hexalith.EventStore/src/Hexalith.EventStore/Validation/ExtensionMetadataSanitizer.cs:28-100,117-135`). The `v3.106.0` tag has the same 32-entry/4,096-byte defaults. Therefore a request with 33 allowed entries or 4,097 bytes passes AD-9's proposed Core checks and is still rejected by the default gateway. A configured gateway may be stricter again.

Do not describe the structural constants as the complete “pinned Gateway” rules. Decide whether McpCli owns a fixed, intentionally stricter public extension contract, whether these limits become operator settings that must match the gateway, or whether sanitizer rejections remain ordinary `gateway_error` responses. If the goal is zero gateway calls for all predictable default-policy failures, bind the effective default intersection (32 entries, 100-character keys, 1,000-character values, 4,096 total UTF-8 bytes, and the sanitizer grammar/pattern checks) and state how configuration drift is handled.

### TR-003 — Medium — EventStore does not establish the claimed case-sensitive PascalCase payload baseline

- **Status:** Internally inconsistent reality rationale
- **Spine:** `ARCHITECTURE-SPINE.md:85-89`, especially line 89
- **Disposition:** **Discuss**

AD-6 may deliberately choose `PropertyNamingPolicy = null`, but the claim that this reflects EventStore writer/reader behavior is too broad. EventStore's shared payload readers use `new JsonSerializerOptions(JsonSerializerDefaults.Web)`, explicitly to accept both PascalCase persisted bytes and camelCase normal API input (`references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Serialization/EventStorePayloadSerialization.cs:5-17,30-43`). The generated REST command adapter writes its payload with `JsonSerializerDefaults.Web` (`references/Hexalith.EventStore/src/Hexalith.EventStore.RestApi.Generators/RestApiControllerEmitter.cs:236,266-272`). Other persistence writers use default options and produce PascalCase, so there is no single live EventStore writer convention.

Retain the case-sensitive PascalCase baseline only as an explicit McpCli wire decision, with its compatibility cost stated and tested. Otherwise align the baseline with the EventStore reader behavior or let the Module provider opt into its actual naming policy. The architecture should not justify a stricter input contract by asserting that EventStore requires it.

### TR-004 — Medium — The Dapr Aspire package version is not the catalog pin

- **Status:** Stale/imprecise version
- **Spine:** `ARCHITECTURE-SPINE.md:196-212`, especially line 211
- **Disposition:** **Autofix**

The Stack says `CommunityToolkit.Aspire.Hosting.Dapr | 13.5.1-beta (catalog pin)`. The checked-in catalog pins `13.5.1-beta.757` at `references/Hexalith.Builds/Props/Directory.Packages.props:151`, and NuGet lists that exact prerelease package ([NuGet](https://www.nuget.org/packages/CommunityToolkit.Aspire.Hosting.Dapr/13.5.1-beta.757)). `13.5.1-beta` is not the exact central pin and is not an independently published version shown by the package catalog.

Change the Stack entry to `13.5.1-beta.757`. This is a documentation-only correction; restore remains safe because the actual central catalog is exact.

### TR-005 — Low — The pinned ULID package has no two-argument `TryParse` convenience overload

- **Status:** API notation is underspecified
- **Spine:** `ARCHITECTURE-SPINE.md:97-101` and `:189`
- **Disposition:** **Autofix**

ByteAether.Ulid 1.4.1 exists and `Ulid.New()` is valid, but its string parsing shape is `Ulid.TryParse(string?, IFormatProvider?, out Ulid)`, not the common `TryParse(string?, out Ulid)` shape. The official package documentation lists the provider-bearing overload ([ByteAether.Ulid repository](https://github.com/ByteAether/Ulid#parsing), [NuGet 1.4.1](https://www.nuget.org/packages/ByteAether.Ulid/1.4.1)). Local API inspection confirmed it, and a compile probe of the two-argument form failed with `CS1501`.

Spell the implementation convention as `Ulid.TryParse(value, provider: null, out _)` (or use the package's `Ulid.IsValid(value)` where only validation is required). This does not change the identifier policy.

## Version and fit audit

| Spine item | Result | Evidence and note |
| --- | --- | --- |
| .NET SDK `10.0.401` | **Verified-current** | Exact local pin in `references/Hexalith.Builds/global.json`; Microsoft's current .NET 10 download page lists SDK 10.0.401 ([official download](https://dotnet.microsoft.com/en-us/download/dotnet/10.0)). |
| C# `14` | **Verified-current** | .NET 10 defaults to C# 14 ([Microsoft language-version table](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/language-versioning)). |
| ModelContextProtocol `2.2.0`, revision `2026-07-28` | **Verified-current, fit issue TR-001** | Exact local catalog pin at `references/Hexalith.Builds/Props/Directory.Packages.props:264`; 2.2.0 is the current stable package and brings Core transitively ([NuGet](https://www.nuget.org/packages/ModelContextProtocol/2.2.0)); the revision and cacheable list-result behavior are official ([MCP release](https://blog.modelcontextprotocol.io/posts/2026-07-28/)). |
| System.CommandLine `2.0.12` | **Verified-current stable** | Exact local catalog pin at `references/Hexalith.Builds/Props/Directory.Packages.props:318`; official package exists and is the latest stable 2.x release ([NuGet](https://www.nuget.org/packages/System.CommandLine/2.0.12)). |
| Hexalith.EventStore.Client / Contracts `3.106.0` | **Verified repository pin** | `HexalithEventStoreVersion` is 3.106.0 and both packages use it (`references/Hexalith.Builds/Props/Directory.Packages.props:9,47-48`). The local EventStore source checkout is ahead of that tag, so tag `v3.106.0` was also checked for behavior relied on by TR-002. |
| ByteAether.Ulid `1.4.1` | **Verified-current, API precision TR-005** | Exact local catalog pin at `references/Hexalith.Builds/Props/Directory.Packages.props:149`; official package exists ([NuGet](https://www.nuget.org/packages/ByteAether.Ulid/1.4.1)). |
| JsonSchema.Net `9.4.0` | **Verified upstream; unlanded locally as declared** | 9.4.0 exists, supports net10.0, and depends on JsonPointer.Net ([NuGet](https://www.nuget.org/packages/JsonSchema.Net/9.4.0)). It is absent from the checked-in central catalog; the spine correctly keeps that prerequisite open at line 319 rather than pretending restore already works. |
| Microsoft.Extensions.Hosting / Http / Logging.Abstractions `10.0.12` | **Verified-current stable** | Exact local pins at `references/Hexalith.Builds/Props/Directory.Packages.props:226-228,235`; Hosting 10.0.12 exists and brings the console logging provider used by AD-12 ([NuGet](https://www.nuget.org/packages/Microsoft.Extensions.Hosting/10.0.12)). |
| Microsoft.CodeAnalysis.CSharp / Analyzers `5.9.0` | **Verified-current** | Exact local pins at `references/Hexalith.Builds/Props/Directory.Packages.props:212-215`; CSharp 5.9.0 supports netstandard2.0 and net10.0 ([NuGet](https://www.nuget.org/packages/Microsoft.CodeAnalysis.CSharp/5.9.0)). |
| xunit.v3 / Shouldly / NSubstitute / Verify.XunitV3 | **Verified-current repository set** | Exact local pins `4.0.1 / 4.3.0 / 6.2.0 / 33.0.2` at `references/Hexalith.Builds/Props/Directory.Packages.props:275,310,331,335`; the official packages exist ([xunit.v3](https://www.nuget.org/packages/xunit.v3/4.0.1), [Shouldly](https://www.nuget.org/packages/Shouldly/4.3.0), [NSubstitute](https://www.nuget.org/packages/NSubstitute/6.2.0), [Verify.XunitV3](https://www.nuget.org/packages/Verify.XunitV3/33.0.2)). |
| Aspire.Hosting.Testing / Aspire.AppHost.Sdk `13.5.4` | **Verified-current** | Testing is pinned locally at `references/Hexalith.Builds/Props/Directory.Packages.props:135`; official 13.5.4 packages exist and target net10.0 ([Aspire.Hosting.Testing](https://www.nuget.org/packages/Aspire.Hosting.Testing/13.5.4), [Aspire.AppHost.Sdk](https://www.nuget.org/packages/Aspire.AppHost.Sdk/13.5.4)). |
| CommunityToolkit.Aspire.Hosting.Dapr | **Stale in spine** | Exact local pin is `13.5.1-beta.757`; see TR-004. |
| Hexalith test/Aspire packages | **Verified repository pins** | EventStore packages use 3.106.0, Tenants 5.7.0, and Parties 1.1.1 in `references/Hexalith.Builds/Props/Directory.Packages.props:9,13-14,46,55-56,83,97`. |

## Named API and live-behavior audit

| Claim | Result | Evidence |
| --- | --- | --- |
| `McpServerTool.Create(delegate, options)` and the named create options | **Verified** | ModelContextProtocol.Core 2.2.0 exposes Delegate/MethodInfo/AIFunction overloads and `SerializerOptions`, `UseStructuredContent`, `OutputSchema`, `ReadOnly`, `Destructive`, and `Idempotent`; official source is under [`McpServerTool`](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerTool.cs) and [`McpServerToolCreateOptions`](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerToolCreateOptions.cs). |
| MCP structured errors with `IsError`, text content, and `structuredContent` | **Verified** | `CallToolResult` owns all three fields and may be returned directly ([official source](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Protocol/CallToolResult.cs)). |
| `tools/list` cache hints for MCP 2026-07-28 | **Verified by SDK** | The protocol requires cacheable list results; SDK 2.2.0 fills missing `TimeToLive = 0` and `CacheScope = Private` before serialization ([official server source](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerImpl.cs#L1867-L1880)). AD-12 need not hand-code those defaults, but its wiring must satisfy TR-001. |
| `WithStdioServerTransport()` and stderr-only console logging | **Verified** | The main MCP package is the correct hosted-server package; the local `Hexalith.EventStore.Admin.Mcp` uses the same transport and `LogToStandardErrorThreshold`. `ConsoleLoggerOptions.LogToStandardErrorThreshold` exists in Microsoft.Extensions.Logging.Console 10.0.12. |
| `Host.CreateApplicationBuilder` | **Verified** | Present in Microsoft.Extensions.Hosting 10.0.12; the local Admin MCP host uses it. |
| `JsonSchemaExporter.GetJsonSchemaAsNode` and `TransformSchemaNode` | **Verified** | Both APIs exist in System.Text.Json on .NET 10 ([Microsoft API](https://learn.microsoft.com/en-us/dotnet/api/system.text.json.schema.jsonschemaexporter?view=net-10.0)). `JsonSerializerOptions.MakeReadOnly()` also exists. |
| JsonSchema.Net `OutputFormat.List` and `InstanceLocation` | **Verified** | 9.4.0 exposes `EvaluationOptions.OutputFormat` and `EvaluationResults.InstanceLocation` as a JsonPointer. The spine correctly calls it a JSON Pointer. |
| `JsonElement.DeepEquals` | **Verified** | Present in System.Text.Json on .NET 10 and suitable for the AD-5 equality assertion. |
| EventStore gateway registration and operations | **Verified** | `AddEventStoreGatewayClient` returns `IHttpClientBuilder` (`references/Hexalith.EventStore/src/Hexalith.EventStore.Client/Registration/EventStoreServiceCollectionExtensions.cs:22-49`); command/query/status methods and paths exist (`.../Gateway/IEventStoreGatewayClient.cs:10-50`, `.../Gateway/EventStoreGatewayClientOptions.cs:6-31`). |
| Query paging/result members | **Verified** | `SubmitQueryRequest.Paging` and `EventStoreQueryResult.Metadata` exist; Queries have no extensions member. AD-20's mapping is feasible. |
| `FakeEventStoreGatewayClient` and `AspireTopologyFixtureBase<TAppHost>` | **Verified** | Both exist under `references/Hexalith.EventStore/src/Hexalith.EventStore.Testing*`; the generic fixture pattern is used by sibling integration tests. |
| .NET 10 tool packaging flags | **Verified** | `PackAsTool`, `CreateRidSpecificToolPackages = false`, and `UseAppHost = false` are the documented way to keep a framework-dependent platform-agnostic tool when RIDs may be present ([Microsoft breaking-change guidance](https://learn.microsoft.com/en-us/dotnet/core/compatibility/sdk/10.0/dotnet-tool-pack-publish)). |
| Analyzer package shape | **Verified** | `netstandard2.0`, `IsRoslynComponent`, `EnforceExtendedAnalyzerRules`, private Roslyn assets, and `analyzers/dotnet/cs` match existing Hexalith generator packaging patterns and the verified Roslyn 5.9.0 target support. |

## Explicitly unresolved rather than falsely verified

- `JsonSchema.Net 9.4.0` and `HexalithMcpCliVersion` are not yet in the checked-in Hexalith.Builds catalog. Line 319 correctly records this as a prerequisite.
- Decorated Tenants and Parties Contracts package versions do not exist yet. Lines 143 and 320 correctly defer their exact production pins.
- The exact `domain-ci.yml` inputs for the source-based Aspire tier remain open at line 318. The shared workflow and tier exist, but the future repository wiring cannot be reality-verified yet.
- The hosted HTTP transport is correctly deferred. `ModelContextProtocol.AspNetCore` 2.2.0 exists, but no v1 rule depends on it.

## Recommended gate decision

Do not treat the spine as implementation-ready until TR-001 and TR-002 are resolved. TR-003 needs an explicit compatibility decision. TR-004 and TR-005 are safe mechanical documentation corrections. All other named technologies and material API surfaces checked in this lens are verified or already marked as open prerequisites.
