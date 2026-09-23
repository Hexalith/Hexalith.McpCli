# Technology and reality validation — 2026-09-23

**Verdict: changes required before the relevant implementation stories.** The pinned packages and principal APIs are credible and the existing upstream prerequisites are explicitly tracked. One library behavior contradicts the prescribed fixed-order MCP registration mechanism, and the Payload schema leaves a null-root validation gap.

**Open findings: 0 Critical, 1 High, 1 Medium, 0 Low.** No architecture, PRD, source, package pin, or existing review was changed by this validation.

## TECH-001 — High — Registering tools in order does not preserve `tools/list` order

**Binding locations:** `ARCHITECTURE-SPINE.md:126` (AD-12) prescribes fixed-order registration into one `ToolCollection`, built-in list/call dispatch, no custom list handler, and fixed-order assertions; `ARCHITECTURE-SPINE.md:195` requires fixed `tools/list` order. `../../epics.md:881` carries the exact five-tool ordering into Story 3.1.

**Primary evidence:** SDK v2.2.0 [McpServerPrimitiveCollection.cs](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerPrimitiveCollection.cs#L11) stores primitives in a `ConcurrentDictionary`; its constructor uses the default comparer (line 25) and `GetEnumerator()` returns dictionary entries directly (lines 212–217). [McpServerImpl.cs](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerImpl.cs#L1377) lists tools by directly iterating the collection and appending them (lines 1377–1384), with no sort.

**Observed result:** A standalone net10.0 probe with `ModelContextProtocol 2.2.0` registered `list_modules`, `list_operations`, `describe_operation`, `send_command`, `run_query` in that sequence. Enumeration returned:

```text
TOOLS:describe_operation,run_query,list_operations,send_command,list_modules
```

This is already different from the prescribed sequence. It does not prove that every process or platform changes order; the unsupported insertion-order assumption alone defeats the specified deterministic contract.

**Recommended action: autofix the mechanism in an Update.** Preserve the filtered collection and built-in call dispatch, and expressly assign order to a deterministic list-result filter after the SDK handler, or an ordered collection implementation with a defined enumerator. The SDK applies `ListToolsFilters` after constructing the augmented list handler (`McpServerImpl.cs:1392`), so an ordering filter can preserve the ban on a replacement list handler. Name the same fixed sequence in the architecture and acceptance criteria, and verify it through the actual protocol for both normal and Read-only sessions.

## TECH-002 — Medium — The specified exporter admits a null Payload root

**Binding locations:** `ARCHITECTURE-SPINE.md:90` (AD-6) fixes serializer settings; `:96` (AD-7) specifies exporter transforms but no non-null root rule; `:108` (AD-9) relies on stored-schema validation before request construction. PRD `prd.md:332` requires invalid Payloads to be rejected before Gateway submission.

**Primary evidence:** Microsoft's [JSON schema exporter documentation](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/extract-schema#configure-the-schema-output) demonstrates a nullable root by default and `TreatNullObliviousAsNonNullable = true` to change it. The checked-in Gateway requires a Command Payload to be an object: `references/Hexalith.EventStore/src/Hexalith.EventStore/Validation/SubmitCommandRequestValidator.cs:77` through `:79`.

**Observed result:** Under installed SDK 10.0.401 / System.Text.Json 10.0.12, a record `Payload(string Name)` and AD-6 settings (case-sensitive PascalCase, null omission, unknown-member rejection, string enum converter) exported:

```json
{"type":["object","null"],"properties":{"Name":{"type":"string"}},"required":["Name"],"additionalProperties":false}
```

`JsonSchema.Net 9.4.0` accepted JSON `null` against that schema (`DEFAULT_NULL_VALIDATION:True`). Adding descriptions, envelope read-only annotations, identifier rules, or closed-object behavior does not remove the nullable root. The exact downstream failure depends on implementation: a contract accessor or Payload rebuild can throw and become `internal_error`, or the Command Gateway can reject the non-object. In each case the advertised contract failed to identify invalid input at the schema boundary.

**Recommended action: autofix the root policy in an Update.** Require the Operation Payload root to be a non-null JSON object and validate it before the accessor/envelope pipeline, while preserving nullable nested members. Configure the exporter for that policy and cover JSON `null` with the shared Core validation fixture. The probe is illustrative library evidence, not a test of an implemented McpCli executor.

## Checks that passed or remain explicit prerequisites

| Area | Evidence and conclusion |
| --- | --- |
| .NET/C# platform | `references/Hexalith.Builds/global.json:3` pins 10.0.401. `dotnet --info` reports installed SDK 10.0.401 and runtime 10.0.12. Microsoft's [.NET 10 download page](https://dotnet.microsoft.com/en-us/download/dotnet/10.0) was checked. No claim that every pin must be the latest release is needed. |
| MCP 2.2.0 | [NuGet package](https://www.nuget.org/packages/ModelContextProtocol/2.2.0) exists and matches `references/Hexalith.Builds/Props/Directory.Packages.props:264`. The [pinned create-options source](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerToolCreateOptions.cs#L120) exposes `UseStructuredContent`, `OutputSchema`, and `SerializerOptions`. Returning `CallToolResult` directly preserves it ([AIFunctionMcpServerTool.cs:298](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/AIFunctionMcpServerTool.cs#L298)). The root `type: object` prevents legacy schema wrapping under the pinned implementation's `ShouldWrapValueForLegacyWire`/`TransformOutputSchemaForLegacyWire` rules (same source, lines 487–559). Prefiltering the collection supports Read-only omission and built-in call dispatch. |
| CLI / hosting | [System.CommandLine 2.0.12](https://www.nuget.org/packages/System.CommandLine/2.0.12) and [Microsoft.Extensions.Hosting 10.0.12](https://www.nuget.org/packages/Microsoft.Extensions.Hosting/10.0.12) are published and match Builds lines 318 and 226. No specific invalid CLI API is prescribed. |
| Schema library | [JsonSchema.Net 9.4.0](https://www.nuget.org/packages/JsonSchema.Net/9.4.0) is published and restored successfully for the probe. `dotnet-inspect` confirmed `EvaluationResults.InstanceLocation` and `JsonSchema.Build(JsonElement, BuildOptions?, Uri?)`; the probe confirmed `OutputFormat.List` exists. The [maintainer docs](https://docs.json-everything.net/schema/basics/) describe list output and default dialect behavior. An initial dialect concern was not promoted: the specified ordinary exporter schema built and evaluated successfully with the exact pin. |
| ULIDs | [ByteAether.Ulid 1.4.1](https://www.nuget.org/packages/ByteAether.Ulid/1.4.1) is published; `dotnet-inspect` and the package XML show `TryParse(string, IFormatProvider, out Ulid)`; the three-argument call shape in AD-8 is available. |
| Analyzer / test packages | [Microsoft.CodeAnalysis.CSharp 5.9.0](https://www.nuget.org/packages/Microsoft.CodeAnalysis.CSharp/5.9.0), [Microsoft.CodeAnalysis.Analyzers 5.9.0](https://www.nuget.org/packages/Microsoft.CodeAnalysis.Analyzers/5.9.0), [xunit.v3 4.0.1](https://www.nuget.org/packages/xunit.v3/4.0.1), [Aspire.Hosting.Testing 13.5.4](https://www.nuget.org/packages/Aspire.Hosting.Testing/13.5.4), and [CommunityToolkit.Aspire.Hosting.Dapr 13.5.1-beta.757](https://www.nuget.org/packages/CommunityToolkit.Aspire.Hosting.Dapr/13.5.1-beta.757) are published and agree with Builds lines 212–214, 335, 135, and 151. Shouldly/NSubstitute/Verify pins match the local catalog; no runtime integration was attempted for those helpers. |
| Gateway DI and requests | `references/Hexalith.EventStore/src/Hexalith.EventStore.Client/Registration/EventStoreServiceCollectionExtensions.cs:29` returns `IHttpClientBuilder`; lines 43–47 leave BaseAddress unset when null. Offline Catalog startup is feasible. `Contracts/Commands/SubmitCommandRequest.cs` and `Contracts/Queries/SubmitQueryRequest.cs` contain the planned transport fields. AD-15 now admits mandatory client transitives; the previous impossible allowlist finding is resolved. |
| Paging / extension limits | `references/Hexalith.EventStore/src/Hexalith.EventStore/Validation/SubmitQueryRequestValidator.cs:94`–`:118` supports cursor/offset exclusion and paging validation. `Configuration/ExtensionMetadataOptions.cs:13,28` establishes 4096 bytes / 32 entries, agreeing with AD-9. Implementation note: also preserve `SubmitCommandRequestValidator.cs:88`–`:89` dangerous-character rejection; sanitizer-only injection checks do not reject every value rejected by the structural validator (for example, `A&B`). This is covered by the existing FR-15 obligation to prevalidate all published Gateway rules and is not counted as a separate architecture finding here. |
| Build and release feasibility | There is no root `.slnx`, implementation `src/`, `.editorconfig`, or `.gitattributes` yet. The bootstrap release breaks the decorated-Contracts cycle. AD-16 and Open Questions `:326`–`:329` already track Parties.Aspire, the bounded CI source-build seam, Builds catalog additions, and first decorated Contracts versions. These are existing prerequisites, not newly missing design. The latest sprint-change proposal stages its live query spike through the existing EventStore AppHost rather than pretending the future McpCli harness exists. |

## Execution evidence and limits

Read the repository AGENTS baseline, declared AI.Tools submodule baseline, architecture, memlog, current epics/sprint change, referenced client/contracts/validators, Builds pins, and previous technology closure report. No root repository Git mutation or submodule update was performed.

Commands and outcomes:

- `dotnet --info` — exit 0; SDK 10.0.401, runtime 10.0.12.
- `dnx dotnet-inspect -y -- member JsonSchemaExporter --platform System.Text.Json --oneline` — exit 1: `Unrecognized option '--oneline'`; the installed CLI has changed from the skill example. `dnx dotnet-inspect -y -- member --help` exposed supported selection options and subsequent calls succeeded.
- `dnx dotnet-inspect -y -- member JsonSchemaExporter --platform System.Text.Json -v:q` — exit 0; System.Text.Json 10.0.12.
- `dnx dotnet-inspect -y -- member EvaluationResults --package JsonSchema.Net@9.4.0 -S Properties` — exit 0; `InstanceLocation` is `Json.Pointer.JsonPointer`.
- `dnx dotnet-inspect -y -- member JsonSchema --package JsonSchema.Net@9.4.0 -m Build` — exit 0; expected build API exists.
- `dnx dotnet-inspect -y -- member Ulid --package ByteAether.Ulid@1.4.1 -m TryParse` — exit 0; expected three-argument signatures present.
- `dotnet run --project /tmp/mcpcli-tech-20260923-hq0oaejh/Probe.csproj --no-restore` — exit 0; exact outputs are recorded above. The first run omitted `--no-restore` and restored successfully. `Probe.csproj` pins JsonSchema.Net 9.4.0 and ModelContextProtocol 2.2.0; all probe files and binaries are outside the repository.

The probe's core checks are `opts.GetJsonSchemaAsNode(typeof(Payload))`, `JsonSchema.Build(...).Evaluate(JsonDocument.Parse("null").RootElement)`, and enumeration of a `McpServerPrimitiveCollection<McpServerTool>` populated with the five actual tool names. This is a small API feasibility experiment, not a production build or end-to-end run.

Official public pages observed in this session show the 2026 pins above; no environment-versus-public-date contradiction was observed for them. The browser returned an internal fetch error for exact EventStore.Client 3.106.0 and Tenants.Aspire 5.7.0 NuGet pages; that is a verification limitation, not evidence those packages do not exist. Their version pins and API fit were checked from the local Builds catalog/reference sources; full package availability and restore remain release preflight obligations. No McpCli restore, build, performance benchmark, Windows ACL test, or live Aspire test can be claimed while implementation artifacts are absent.

## Reproducible isolated probe

Create the following files in a scratch directory, then run `dotnet run --project Probe.csproj` using SDK 10.0.401. These are not proposed repository implementation files.

`Probe.csproj`:

```xml
<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup><ItemGroup><PackageReference Include="JsonSchema.Net" Version="9.4.0"/><PackageReference Include="ModelContextProtocol" Version="2.2.0"/></ItemGroup></Project>
```

`Program.cs`:

```csharp
using System.Text.Json;
using System.Text.Json.Schema;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Json.Schema;
using ModelContextProtocol.Server;
var opts = new JsonSerializerOptions { PropertyNamingPolicy = null, PropertyNameCaseInsensitive = false, DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull, UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow, TypeInfoResolver = new DefaultJsonTypeInfoResolver() };
opts.Converters.Add(new JsonStringEnumConverter());
opts.MakeReadOnly();
var schema = opts.GetJsonSchemaAsNode(typeof(Payload));
Console.WriteLine("SCHEMA:" + schema.ToJsonString());
try { var built = JsonSchema.Build(JsonSerializer.SerializeToElement(schema)); Console.WriteLine("DEFAULT_NULL_VALIDATION:" + built.Evaluate(JsonDocument.Parse("null").RootElement).IsValid); } catch(Exception e) { Console.WriteLine("DEFAULT_BUILD:" + e.GetType().Name + ":" + e.Message); }
Console.WriteLine("OUTPUT_FORMATS:" + string.Join(",", Enum.GetNames<OutputFormat>()));
var c = new McpServerPrimitiveCollection<McpServerTool>();
foreach(var name in new[] {"list_modules", "list_operations", "describe_operation", "send_command", "run_query"}) c.Add(McpServerTool.Create(() => "ok", new McpServerToolCreateOptions { Name = name }));
Console.WriteLine("TOOLS:" + string.Join(",", c.Select(t => t.ProtocolTool.Name)));
public record Payload(string Name);
```
