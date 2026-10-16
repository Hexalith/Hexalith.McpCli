---
title: 'Execute Calls with Structured MCP Results'
type: 'feature'
created: '2026-10-16'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-3-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The existing MCP handlers bind execution arguments and serialize Core documents, but current MCP tests exercise discovery only. Output schemas are checked for shape rather than validated against real results, leaving execution parity and omission rules unproven.

**Approach:** Complete and verify the generic MCP execution boundary with substituted Gateway responses, canonical Core comparisons, and executable output-schema checks under both supported protocol flows. Repair defects exposed by these checks without duplicating Core policy.

## Boundaries & Constraints

**Always:** Use the shared argument records, executor, envelope context, and result serializer. Preserve every addendum §E argument and §G document field and omission rule. A Core error has `isError: true`, structured `{ error: ... }`, and matching JSON in the first text item. Unexpected tool exceptions become a sanitized `internal_error`. Input binding failures use protocol invalid-parameters errors. Every advertised output schema has an object root and closed success/error branches in `oneOf`; arbitrary result documents and embedded payload schemas remain open where their contract allows. Measure output-schema size separately from the existing 8,000-character input budget. Verify 2025-06-18 and 2026-07-28 clients using their version-appropriate flows.

**Never:** Add module-specific production code, another executor, new tools or transports, retries, dependencies with inline versions, or changes to sibling submodules. Preserve stdio channel and lifecycle guarantees from Story 3.2.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|---------------------------|----------------|
| Command success | Valid payload; correlation, idempotency, aggregate, extensions; optional Gateway result present/absent | Shared request reaches Gateway once; canonical identity, tenant, accepted status; optional fields only when supplied/returned | No invented idempotency or result |
| Query success | Entity and paging arguments; object, scalar, array, or null response; metadata present/absent | Shared request and canonical document; document always present, paging only when returned | Preserve JSON null and value types |
| Tenant policy | Fixed tenant; session tenant with override off/on; no session tenant | Core resolves or refuses per-call tenant identically to direct execution | Canonical validation document; refused calls never reach Gateway |
| Execution refusal | Wrong kind, invalid payload/envelope, missing URL, read-only direct execution, Gateway failure | Same Core error document and flags; discovery remains usable offline | Structured and text JSON agree; no secondary stderr error |
| Boundary failure | Executor or catalog throws; malformed/missing required input | Sanitized tool error for execution faults; protocol invalid parameters for binding faults | No exception or sensitive exception text leaks |
| Schema contract | Every tool's actual success/error results; extra fields and missing required members | Valid fixtures accepted; invalid fixtures rejected under both revisions | Closed document branches; input budget unaffected |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Mcp/McpToolHandlers.cs` — existing shared-record binding, guards, canonical conversion; retain Core ownership.
- `src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs` — runtime tools, required-name protocol filter, exporter-based output schemas; currently closes only branch roots.
- `src/Hexalith.McpCli.Core/McpCliCoreServiceCollectionExtensions.cs` — register real executor and replace only Gateway for integration checks.
- `src/Hexalith.McpCli.Core/Execution/` — canonical result/error records and executor; reuse without policy changes.
- `tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs` — reusable SDK stream-session and full-document comparison patterns; currently discovery coverage only.
- `tests/Hexalith.McpCli.Core.Tests/QueryTestHarness.cs` and `OperationExecutorTests.cs` — Gateway substitutes, complete request assertions, tenant and identity cases.
- `tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs` and `tests/fixtures/StdioHost/Program.cs` — real stdio process fixture and transcript assertions.
- `tests/Directory.Build.props` — existing xUnit, Shouldly, NSubstitute; JsonSchema.Net is already available through Core.

## Tasks & Acceptance

**Execution:**
- [ ] `tests/Hexalith.McpCli.Mcp.Tests/McpExecutionTests.cs` and focused test helpers — exercise matrix cases using real Core plus a substituted Gateway, assert complete requests and canonical structured/text documents; separately inject exceptions to test boundary guards.
- [ ] `tests/Hexalith.McpCli.Mcp.Tests/McpOutputSchemaTests.cs` — validate actual success/error fixtures for all five tools and reject extra/missing document members; report separate output-schema sizes under both protocol revisions.
- [ ] `src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs` and `McpToolHandlers.cs` — repair schema or binding/conversion failures demonstrated by the new checks.
- [ ] `tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs`, `tests/fixtures/StdioHost/Program.cs`, and fixture project references if needed — provide a deterministic substituted Gateway fixture mode and call every available tool through SDK stdio under both revisions; retain offline execution/discovery coverage.
- [ ] `README.md` — document verified MCP execution argument representation and structured success/error behavior.

**Acceptance Criteria:**
- Given the same execution inputs and trusted context, when CLI/Core and MCP serialize outcomes, then their complete JSON documents and omission rules agree.
- Given an SDK stdio session under either revision, when the client lists tools and calls each available tool, then calls complete without JSON-RPC parse errors and subsequent discovery remains usable after an execution error.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

- `dotnet restore Hexalith.McpCli.slnx` — fresh package assets.
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` — no warnings or errors.
- `dotnet test tests/Hexalith.McpCli.Mcp.Tests --no-build --configuration Release` — all protocol, execution, and schema cases pass.
- `dotnet test tests/Hexalith.McpCli.Cli.Tests --no-build --configuration Release` — stdio and CLI regressions pass.
- Run Core and Manifest projects individually after fresh restore; run remaining existing test projects before marking complete. If Core validation, sample contracts, or Gateway wire output changes, also run both documented conformance scripts and restore afterwards.
