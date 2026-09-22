---
title: "Final reviewer gate: technology and reality"
target: ARCHITECTURE-SPINE.md and aligned PRD/addendum
date: '2026-09-22'
lens: technology-reality
verdict: resolved-after-update
findings:
  critical: 0
  high: 1
---

# Final technology and reality review

## Verdict

**One High finding, no Critical findings.** The MCP 2.2.0 tool-registration and output-schema plan is feasible; the scripted cross-head and once-per-vector live gates now express different, compatible checks; `unknown_module` has one consistent Core dispatch and document shape. The production dependency graph gate needs correction before implementation because its literal allowlist rejects dependencies of the mandated pinned client.

## High finding

### FTR-001 — The restored-assets allowlist rejects the pinned EventStore client it requires

- **Spine:** `ARCHITECTURE-SPINE.md:140-144` (AD-15), `:203-219` (Stack), and `:339` (FR-20 amendment).
- **PRD:** `prd.md:99` (§4) says the tool references `Hexalith.EventStore.Client` yet says *all other transitive dependencies* must remain in the external allowlist; `prd.md:400-403` makes a restored-graph CI test part of v1 acceptance.
- **Primary source:** [`Hexalith.EventStore.Client.csproj` at the exact pinned `v3.106.0` tag](https://github.com/Hexalith/Hexalith.EventStore/blob/v3.106.0/src/Hexalith.EventStore.Client/Hexalith.EventStore.Client.csproj#L18-L24), also checked locally with `git show v3.106.0:src/Hexalith.EventStore.Client/Hexalith.EventStore.Client.csproj` in the EventStore submodule. It directly requires `Dapr.Client`, `Microsoft.AspNetCore.DataProtection.Abstractions`, `Microsoft.Extensions.Configuration.Binder`, `Microsoft.Extensions.Hosting.Abstractions`, and `Microsoft.Extensions.Http`. The pinned version is `3.106.0` in `references/Hexalith.Builds/Props/Directory.Packages.props:9,47`.

At least `Dapr.Client`, `Microsoft.AspNetCore.DataProtection.Abstractions`, and `Microsoft.Extensions.Configuration.Binder` are absent from the spine's named Stack and the PRD's listed closure of `Hexalith.EventStore.Contracts`. Restoring the required `Hexalith.EventStore.Client` necessarily adds them. A CI check that enforces the text literally will reject every valid tool package; widening the check without a stated rule would silently weaken the dependency boundary. `ByteAether.Ulid` is explicitly allowed even though it is not a `Hexalith.*` package, another reason to define the rule by the approved baseline graph rather than a vendor prefix alone.

**Suggested replacement wording for PRD §4 and AD-15:**

> Direct production package references are limited to `Hexalith.McpCli.Abstractions`, `Hexalith.EventStore.Client`, the flagged exposed `*.Contracts` packages, and the named pinned Stack packages. The allowed transitive baseline is the exact restored, locked closure of `Hexalith.EventStore.Client`, `Hexalith.EventStore.Contracts`, and those Stack packages at their pinned versions. An exposed Contracts package may add its own identity and the Decoration Package, but no other package identity outside that baseline without a PRD change. The CI assets check enforces direct-reference identities, the baseline graph and exact versions, rejects any additional Module or Hexalith package, and rejects FrameworkReferences beyond `Microsoft.NETCore.App`.

This preserves the intended Contracts dependency boundary while admitting the pinned client's mandatory Dapr and Microsoft packages. If the implementation uses a dependency-lock file, the gate must compare the resolved assets to that approved baseline, not assume the brief Stack table enumerates all transitives.

## Focused feasibility checks

| Area | Result |
| --- | --- |
| MCP SDK 2.2.0 | **Consistent.** AD-12 at `ARCHITECTURE-SPINE.md:126` prefilters one `ToolCollection` and uses built-in list/call dispatch. The root `type: object` plus closed `oneOf` avoids the SDK's pre-2026-07-28 output-schema wrapper; both negotiated protocol versions have advertised-schema conformance tests. This matches the [pinned SDK tool configuration](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerImpl.cs#L1464-L1527) and [legacy schema transformation](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/AIFunctionMcpServerTool.cs#L577-L607). |
| CLI and Gateway APIs | **Consistent.** System.CommandLine `2.0.12`, MCP `2.2.0`, and EventStore `3.106.0` match the checked-in Builds pins. `AddEventStoreGatewayClient` returns `IHttpClientBuilder`; the pinned Command/Query request contracts support the specified fields. The .NET 10 tool packaging flags match [Microsoft's compatibility guidance](https://learn.microsoft.com/en-us/dotnet/core/compatibility/sdk/10.0/dotnet-tool-pack-publish). |
| Scripted parity and live vectors | **Consistent at the architecture level.** AD-16 at `ARCHITECTURE-SPINE.md:146-150` and PRD FR-20/SM-4 at `prd.md:398,509` use reset loopback responses to compare both out-of-process Heads after masking only generated identifiers; a separate blocking Aspire lane submits each approved vector once and checks semantic outcomes. AD-21 separately catches catalog omissions and wrong decorated contract types. The loopback script should echo each incoming generated command correlation identifier in successful command responses: the PRD expects that correlation to be returned (`prd.md:344`), and the pinned client requires a non-empty response `CorrelationId` (`references/Hexalith.EventStore/src/Hexalith.EventStore.Client/Gateway/EventStoreGatewayClient.cs:145-179`). This is a concrete test-fixture implementation detail, not a new architecture decision. |
| `unknown_module` | **Consistent.** AD-3/5 at `ARCHITECTURE-SPINE.md:72,84` route a non-empty missing Module through Core; `prd.md:260,284` and `addendum.md:376-392,427-430` agree on `code`, exact requested `module`, and up to three ordered canonical suggestions. Empty input fails Head binding, and the success `module` field remains canonical. |
| Unlanded prerequisites | **Correctly open.** Decorated Tenants/Parties package pins, `Hexalith.Parties.Aspire`, a source-build path for the blocking Aspire job, and Builds catalog entries are named at `ARCHITECTURE-SPINE.md:325-329`. No runnable release is claimed before they land. |

This is a documentation and source/API review. The McpCli solution and implementation projects do not yet exist, so no McpCli build or end-to-end test was run.

## Closure check — 2026-09-22

**FTR-001 is resolved. No Critical or High finding remains in this review.** The revised PRD §4 (`prd.md:99`) and AD-15 (`ARCHITECTURE-SPINE.md:144`) now separate permitted direct package roots from the exact locked transitive baseline of the pinned EventStore client, EventStore Contracts, and Stack packages. They explicitly admit the client's Dapr and Microsoft dependencies, while the restored-assets CI check still rejects new identities introduced by a Module Contracts package, unapproved Module/Hexalith packages, version drift, and extra FrameworkReferences. This closes the impossible-gate condition identified above without broadening Module enrollment by implication.
