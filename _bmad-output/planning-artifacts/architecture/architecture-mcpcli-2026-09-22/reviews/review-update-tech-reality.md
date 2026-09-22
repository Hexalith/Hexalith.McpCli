---
title: "Update reviewer: technology and reality"
target: ARCHITECTURE-SPINE.md
date: '2026-09-22'
lens: technology-reality
intent: update
verdict: resolved-after-update
findings:
  critical: 0
  high: 1
  medium: 2
  low: 0
---

# Technology and reality review

## Verdict

**Needs update: 1 High and 2 Medium findings.** The prior review's tool-registration, extension-limit, Payload-casing, Dapr-version, and ULID-overload findings have been addressed. The pinned stack and named gateway/Aspire APIs checked below are plausible against the current primary sources. The remaining High finding is a protocol-version-dependent mismatch between advertised MCP output schemas and returned structured content.

## Findings

### TRU-001 — High — The `oneOf` output schema is wrapped for older MCP clients, but the returned object is not

- **Spine:** `ARCHITECTURE-SPINE.md:121-125` (AD-12), especially the `OutputSchema` and direct `CallToolResult` requirements.
- **Evidence:** [ModelContextProtocol 2.2.0 `McpServerImpl.ConfigureTools`](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerImpl.cs#L1495-L1523), [2.2.0 `AIFunctionMcpServerTool` legacy schema transformation](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/AIFunctionMcpServerTool.cs#L235-L265), [transformation rules](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/AIFunctionMcpServerTool.cs#L577-L607), [direct result handling](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/AIFunctionMcpServerTool.cs#L270-L334).

AD-12 requires a root schema containing only `oneOf` with closed success and error object branches. For clients negotiating a protocol earlier than `2026-07-28`, SDK 2.2.0 transforms any output schema without root `type: object` into `{ "type": "object", "properties": { "result": <original schema> }, "required": ["result"] }`. The tool delegate's explicit `CallToolResult` is returned unchanged, including its root success object or `{ "error": ... }` `structuredContent`. Those results therefore cannot satisfy the schema the server advertised to an older client. This affects the cross-client promise and the parity claim even though the built-in `ToolCollection` dispatch itself is now correctly specified.

**Fix:** Give the shared output schema root `type: object` as well as `oneOf` over the two closed branches. An object root remains semantically equivalent for these branches and the SDK leaves it unwrapped for older clients. Exercise `tools/list` and one success and one error call with both a pre-`2026-07-28` negotiated protocol and the current revision; validate each `structuredContent` against the schema advertised in that session.

### TRU-002 — Medium — Paging arguments have no stated Core validation against the pinned gateway policy

- **Spine:** `ARCHITECTURE-SPINE.md:79-83,103-107,169-173` (AD-5, AD-9, AD-20).
- **Evidence:** The exact `v3.106.0` tag's `src/Hexalith.EventStore/Validation/SubmitQueryRequestValidator.cs:94-118` and `src/Hexalith.EventStore.Contracts/Queries/QueryPolicyLimits.cs:15-20`, checked with `git show v3.106.0:<path>` in the EventStore submodule. The current checkout retains the same checks at `references/Hexalith.EventStore/src/Hexalith.EventStore/Validation/SubmitQueryRequestValidator.cs:114-141`.

The spine maps `pageSize`, `offset`, and `cursor` to `SubmitQueryRequest.Paging`, but AD-9's validation sequence names only Payload, routing, identifiers, and Command extensions. The pinned gateway rejects cursor plus offset, `pageSize` outside `1..200`, negative offset, and cursors longer than 4,096 characters. Without an explicit Core preflight rule, one head could reject locally while the other submits and maps a gateway error, undermining the shared call model. An invalid paging request also reaches the gateway despite the AD-9 zero-call expectation for validation failures.

**Fix:** Bind the pinned paging checks in Core and return `validation_failed` at `/pageSize`, `/offset`, or `/cursor` before the single gateway call. Keep the gateway as the final authority for a deployment with stricter settings.

### TRU-003 — Medium — The sample Module cannot appear in the installed tool's manifest as currently specified

- **Spine:** `ARCHITECTURE-SPINE.md:73-77,139-149,193,238-241` (AD-4, AD-15, AD-16 and Tests convention).
- **Evidence:** AD-4 generates the manifest exclusively from flagged production `PackageReference` entries in the tool project; AD-15 says the sample Contracts project is never referenced by `src/`; AD-16 nevertheless specifies one production-like Catalog with Tenants, Parties, and that sample, and tests the built `hexalith` CLI/MCP processes against the same Catalog.

As written, the built tool cannot discover `Hexalith.McpCli.Sample.Contracts`: it is absent from the only assembly manifest and there is no test assembly injection seam. A test may construct an in-process Catalog with the sample, but that is a different Catalog from the out-of-process heads the same rule requires. The sample's converter-backed identifier and interface-routed Command therefore cannot get the promised end-to-end cross-head parity coverage without an additional mechanism.

**Fix:** State a test-only composition method, such as a separate test host using the same heads and executor with a manifest including the sample, or a test-build-only flagged reference whose package cannot enter the release artifact. Keep the production manifest rule and release package check intact.

## Verified technology and API fit

| Area | Result and evidence |
| --- | --- |
| Stack pins | `.NET SDK 10.0.401` matches `references/Hexalith.Builds/global.json`; MCP 2.2.0, System.CommandLine 2.0.12, ByteAether.Ulid 1.4.1, Aspire.Hosting.Testing 13.5.4, Dapr integration `13.5.1-beta.757`, Roslyn 5.9.0, xUnit 4.0.1, Shouldly 4.3.0, NSubstitute 6.2.0, and Verify.XunitV3 33.0.2 match `references/Hexalith.Builds/Props/Directory.Packages.props`. `JsonSchema.Net 9.4.0` and `HexalithMcpCliVersion` remain explicitly unlanded upstream prerequisites. |
| MCP | SDK 2.2.0 [appends registered `ToolCollection` entries to `tools/list` and dispatches them](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerImpl.cs#L1464-L1527); the update correctly removes the custom list handler and prefilters the collection. `McpServerToolCreateOptions` has `SerializerOptions`, `UseStructuredContent`, `OutputSchema`, and the stated annotations in [the pinned API](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerToolCreateOptions.cs). |
| Gateway and extensions | `AddEventStoreGatewayClient` returns `IHttpClientBuilder` at `references/Hexalith.EventStore/src/Hexalith.EventStore.Client/Registration/EventStoreServiceCollectionExtensions.cs:29-49`; Commands and Queries requests have the AD-9/AD-20 members. The AD-9 fixed `32`-entry/`4096`-byte policy matches the default sanitizer (`.../Configuration/ExtensionMetadataOptions.cs:9-28`) and the structural request validator's tighter per-key/per-value lengths; the sanitizer still has separately configured limits and grammar (`.../Validation/ExtensionMetadataSanitizer.cs:28-100,117-135`), which AD-9 now acknowledges. |
| Aspire and CI | `AspireTopologyFixtureBase<TAppHost>` exists at `references/Hexalith.EventStore/src/Hexalith.EventStore.Testing.Integration/AspireTopologyFixtureBase.cs:33`; Tenants' helper locates its server source through `TenantsServerProjectMetadata`. The shared `domain-ci.yml` has `aspire-test-project`, `test-platform`, and `aspire-continue-on-error` inputs and initializes root-declared submodules, but its Aspire job only restores/builds the caller solution before Dapr tests (`references/Hexalith.Builds/.github/workflows/domain-ci.yml:642-702`). The source-build prerequisite and unpublished Parties Aspire helper remain correctly open. |
| .NET tool packaging | `PackAsTool`, `CreateRidSpecificToolPackages=false`, and `UseAppHost=false` are the [documented .NET 10 framework-dependent, platform-agnostic combination](https://learn.microsoft.com/en-us/dotnet/core/compatibility/sdk/10.0/dotnet-tool-pack-publish). |

No code was built: this is a documentation/API review, and the solution and projects in the spine do not yet exist.

## Closure check — 2026-09-22

All three findings are **resolved in the revised spine**. The findings above record what the earlier draft required; they are retained as review history.

| Finding | Closure evidence | Result |
| --- | --- | --- |
| TRU-001 | AD-12 at `ARCHITECTURE-SPINE.md:126` now requires root `type: object` around the closed `oneOf` branches and tests both pre-`2026-07-28` and current negotiated protocols against each session-advertised schema. This avoids the SDK's legacy `{ result: ... }` schema rewrite while retaining the direct result shape. | Resolved |
| TRU-002 | AD-20 at `ARCHITECTURE-SPINE.md:174` now binds the exact `v3.106.0` constraints: page size `1..200`, nonnegative offset, cursor length at most `4096`, and no nonblank cursor with offset. It specifies Core `validation_failed` paths and zero Gateway calls. | Resolved |
| TRU-003 | AD-16 at `ARCHITECTURE-SPINE.md:150` now limits the out-of-process Catalog to flagged production assemblies. The sample joins only a separately constructed in-process Catalog through `CatalogBuilder.Build`; cross-head parity uses the same shipped production Catalog. AD-15 still keeps the sample outside `src/`. | Resolved |

There is no remaining technology/reality gap from these three findings. The revised design still needs implementation tests and the explicitly named upstream package, Aspire helper, and CI source-build prerequisites before a runnable release can be claimed.
