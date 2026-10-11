---
title: 'Run the MCP Server over Clean Stdio'
type: 'feature'
created: '2026-10-11'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-3-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** In-process tests do not prove clean process stdio. A broad host-run catch can write a structured stderr error after serving begins.

**Approach:** Harden the existing lifecycle and test a project-reference fixture process with the pinned MCP SDK under both protocol flows.

## Boundaries & Constraints

**Always:** Resolve settings once; build the Catalog before serving. Ignore valid inherited format for protocol output; accept explicit `--format json`. Reject explicit `--format table` and any `--output` before Catalog or transport startup, with format first when both appear; never open the output path. Keep stdout to JSON-RPC and logs/diagnostics on stderr. Pre-serving failure writes one structured stderr error, exits 2, and writes zero stdout bytes. Serving tool failures use MCP only; normal shutdown exits 0.

**Never:** Add another resolver, prompt, Module-specific tool, transport, or MCP formatter. Leave Story 3.3's schema and execution-document work there.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|---------------------------|----------------|
| Stdio discovery | Sample Catalog, no URL; profile/environment; 2025-06-18 or 2026-07-28 client | Version-specific flow, fixed tools, discovery over parseable JSON-RPC; no prompt or note | Tool failure stays in MCP; no second stderr error |
| Presentation options | Inherited `table` or explicit `json`; explicit `table` and/or `--output` | Valid settings serve; invalid flags stop before Catalog/transport | Full `invalid_arguments` stderr document, exit 2, empty stdout, untouched path |
| Startup rejection | Malformed settings, empty Catalog, strict diagnostic | No session starts | One canonical stderr error, exit 2, zero stdout |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli/Cli/CliRunner.cs:689` — preflight, host, Catalog gate, stderr writer, broad catch; separate pre-serving from serving failure.
- `src/Hexalith.McpCli/Hosting/HostFactory.cs:35`, `SettingsBootstrap.cs:25`, `src/Hexalith.McpCli.Core/Catalog/CatalogProvider.cs:27` — reuse one settings snapshot, stderr logging, and strict-before-empty Catalog policy.
- `src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs:96` — reuse SDK stdio transport and fixed tools.
- `tests/Hexalith.McpCli.ConformanceHost/Program.cs:28` — package-based loopback pattern; use project references in the new fixture because the shipped CLI enrolls no modules.
- `tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs:24` — in-process version assertions only.
- `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs:694` — startup seams and outdated host-run catch expectation.
- `README.md:93`, `_bmad-output/implementation-artifacts/deferred-work.md:441` — user contract and existing version-flow deferral.

## Tasks & Acceptance

**Execution:**
- [ ] `src/Hexalith.McpCli/Cli/CliRunner.cs` — isolate startup error handling from serving and normal shutdown.
- [ ] `tests/fixtures/StdioHost/Hexalith.McpCli.StdioHost.csproj` and `Program.cs` — invoke the real runner in a child process with project-referenced sample and diagnostic manifests.
- [ ] `Hexalith.McpCli.slnx` and `tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj` — build the fixture with the existing CLI test lane.
- [ ] `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs` — assert full startup documents/channels, option precedence before manifest access, settings and Catalog failures, and revised host lifecycle.
- [ ] `tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs` — run SDK stdio clients for both revisions; assert first handshake request, tools/list, offline discovery, profile/environment and format cases, clean channels, and MCP-only errors.
- [ ] `README.md` — document verified stdio, option, and channel behavior.
- [ ] `_bmad-output/implementation-artifacts/deferred-work.md` — resolve the prior version-flow entry with process-test evidence.

**Acceptance Criteria:**
- Given profile or environment settings and a valid Catalog, when an SDK client connects under either revision, then one settings resolution and Catalog build precede parseable stdio discovery without a prompt.
- Given a serving session, when a tool call fails or the client ends the session, then failure travels through MCP only and normal shutdown exits 0.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` — succeeds with pinned dependencies.
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` — succeeds without warnings.
- `dotnet test tests/Hexalith.McpCli.Cli.Tests --no-build --configuration Release` — passes stdio process and startup checks.
- `dotnet test tests/Hexalith.McpCli.Mcp.Tests --no-build --configuration Release` — passes fixed-surface protocol tests.
- `git diff --check` — reports no whitespace errors.
