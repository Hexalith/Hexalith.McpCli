# Technology and reality review — 2026-09-23 update

**Final verdict:** Pass after source and integration fixes; no open findings from this lens. The initial one High and two Medium findings and their closure are retained below.

## Findings

### High — idempotency-key discovery now contradicts the public result contract

**Location:** `ARCHITECTURE-SPINE.md:109`, PRD `prd.md:358`, addendum `addendum.md:313`.

The updated spine and PRD say `idempotencyKeyRequired` is true when the mapped property is non-nullable **or serializer-required**. Addendum §G, which AD-5 says is the exact public document contract, says it is true **exactly when** the property is non-nullable. A nullable constructor parameter marked `[JsonRequired]` can satisfy the second criterion without the first, making conforming discovery implementations disagree. Reconcile addendum §G with the rule chosen in AD-9 (and any §G fixture) before declaring the spine final.

### Medium — AD-6 must fix the serializer metadata resolver before schema export

**Location:** `ARCHITECTURE-SPINE.md:91-97`.

`JsonSchemaExporter.GetJsonSchemaAsNode(JsonSerializerOptions, Type)` rejects a fresh `JsonSerializerOptions` instance without a `TypeInfoResolver`. The rule specifies a newly composed Module options instance, copies converters, and makes it read-only, but leaves the resolver choice implicit. A literal implementation using `MakeReadOnly()` or calling the exporter before read-only preparation fails at Catalog build. In an isolated .NET 10 repro, the exporter threw `InvalidOperationException: JsonSerializerOptions instance must specify a TypeInfoResolver setting before being marked as read-only`; setting `TypeInfoResolver = new DefaultJsonTypeInfoResolver()` or calling `MakeReadOnly(populateMissingResolver: true)` allowed export. Specify one deterministic resolver policy in AD-6 and test schema export with a provider-backed Module. This also clarifies whether a provider's custom resolver is intentionally discarded by the “non-converter settings” rule. [Microsoft's .NET 10 API contract](https://learn.microsoft.com/en-us/dotnet/api/system.text.json.schema.jsonschemaexporter.getjsonschemaasnode?view=net-10.0).

### Medium — “Before JSON-RPC initialization” does not cover the 2026-07-28 MCP revision

**Location:** `ARCHITECTURE-SPINE.md:127`.

The pinned SDK 2.2.0 supports the 2026-07-28 revision, which removed the `initialize` handshake; its packaged XML documentation says this explicitly. AD-12's startup-failure boundary (“before JSON-RPC initialization” versus “after initialization”) has no literal transition in that revision, although it is meaningful for older peers. Phrase it as “before the MCP transport/session starts serving requests” and “once requests can be served,” with version-specific tests for both supported revisions. The official [SDK v2 release notes](https://github.com/modelcontextprotocol/csharp-sdk/releases) also identify the handshake removal.

## Checks that support the update

- `ModelContextProtocol.Core` **2.2.0** packaged XML confirms `McpRequestFilters.ListToolsFilters`, `McpServerOptions.ToolCollection`, `McpServerTool.Create(delegate, ...)`, `UseStructuredContent`, and explicit `OutputSchema`. It states tools in `ToolCollection` are included in list results and checked first for call dispatch. The [official SDK filter guide](https://github.com/modelcontextprotocol/csharp-sdk/blob/main/docs/concepts/filters.md) confirms a list filter can inspect and replace the result after `next(...)`. Thus AD-12's fixed-order projection is feasible. The phrase “same filtered collection” is imprecise: the filter changes the list response, while the separately restricted `ToolCollection` handles calls; the restricted set is what keeps advertisement and dispatch aligned.
- The .NET 10 repro exported a reference-type Command as root `{"type":["object","null"]}` with a nullable nested string member as `{"type":["string","null"]}`. AD-7's current instruction to normalize **only the top-level** Command `type` therefore preserves nested nullability as intended. [Official exporter API](https://learn.microsoft.com/en-us/dotnet/api/system.text.json.schema.jsonschemaexporter.getjsonschemaasnode?view=net-10.0).
- The pinned `SubmitCommandRequestValidator` requires an object Payload and uses the stated Tenant, aggregate ID, Command type, and extension limits; `ExtensionMetadataOptions` defaults to 32 entries and 4,096 total bytes, so AD-9's fixed intersection is accurate. The pinned `SubmitQueryRequestValidator` allows optional Payload and enforces the stated page size, cursor length, offset, and cursor/offset exclusion. `SubmitQueryRequest` has no correlation or extension fields. Local evidence: `references/Hexalith.EventStore/src/Hexalith.EventStore/Validation/{SubmitCommandRequestValidator,SubmitQueryRequestValidator,ExtensionMetadataSanitizer}.cs`, `references/Hexalith.EventStore/src/Hexalith.EventStore/Configuration/ExtensionMetadataOptions.cs`, and `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Queries/SubmitQueryRequest.cs`.

## Method

Compared the current spine and its uncommitted diff with pinned EventStore source, the installed MCP 2.2.0 package XML, official SDK documentation, and a local .NET 10 schema-export repro. No source or spine file was edited.

## Closure check — 2026-09-23

**All three findings resolved in the current documents.** Addendum §G now uses the same non-nullable-or-serializer-required `idempotencyKeyRequired` rule as AD-9 and PRD §FR-16, including effective `JsonPropertyInfo.IsRequired`. AD-6 now specifies a tool-owned `DefaultJsonTypeInfoResolver` before `MakeReadOnly()` and schema export and explicitly discards the provider resolver. AD-12 now uses the serving-requests boundary and calls for separate legacy `initialize` and 2026-07-28 handshake-free tests. No further change is requested by this technology review.
