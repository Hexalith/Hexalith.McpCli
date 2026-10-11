---
title: 'Run the MCP Server over Clean Stdio'
type: 'feature'
created: '2026-10-11'
status: 'done'
baseline_commit: 1107ea1497b75cbe1a3776c08f3797fdce00a245
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
- [x] `src/Hexalith.McpCli/Cli/CliRunner.cs` — isolate startup error handling from serving and normal shutdown.
- [x] `tests/fixtures/StdioHost/Hexalith.McpCli.StdioHost.csproj` and `Program.cs` — invoke the real runner in a child process with project-referenced sample and diagnostic manifests.
- [x] `Hexalith.McpCli.slnx` and `tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj` — build the fixture with the existing CLI test lane.
- [x] `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs` — assert full startup documents/channels, option precedence before manifest access, settings and Catalog failures, and revised host lifecycle.
- [x] `tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs` — run SDK stdio clients for both revisions; assert first handshake request, tools/list, offline discovery, profile/environment and format cases, clean channels, and MCP-only errors.
- [x] `README.md` — document verified stdio, option, and channel behavior.
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` — resolve the prior version-flow entry with process-test evidence.

**Acceptance Criteria:**
- Given profile or environment settings and a valid Catalog, when an SDK client connects under either revision, then one settings resolution and Catalog build precede parseable stdio discovery without a prompt.
- Given a serving session, when a tool call fails or the client ends the session, then failure travels through MCP only and normal shutdown exits 0.

## Implementation Notes

- `tools/dependency-policy.json` now matches the already-pinned EventStore 3.120.0 restore; this clears the Manifest gate without changing dependencies.
- `ExecutionFailureCommandTests.AcceptedCommandWritesExistingResultFileAsync` now checks the format note once regardless of asynchronous HTTP log ordering on stderr.

## Spec Change Log

## Review Triage Log

| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| Blind 1, `CliRunner.cs:742` | medium | patch | `RunAsync` performs host startup before waiting for shutdown; its catch currently treats a startup exception as a serving failure. Separate startup from the serving wait. |
| Blind 2, `CliRunner.cs:725` | medium | patch | `Dispose` during Catalog rejection can throw, then the catch calls it again and can escape before writing the startup document. Preserve the original startup error through disposal. |
| Blind 3, `McpStdioProcessTests.cs:75` | low | patch | The test excludes only two stderr strings; an `unknown_operation` diagnostic would pass. Assert that the tool failure adds no stderr error diagnostic. |
| Blind 4, `McpStdioProcessTests.cs:102` | false | reject | `McpProtocolTests` already verifies read-only discovery still lists writes and describes them with `reason: read_only`; this process test need only verify the live read-only tool surface. |
| Blind 5, `McpStdioProcessTests.cs:92` | low | patch | The process test proves explicit `json` is accepted but does not inspect the effective setting. Add a direct effective-settings assertion for precedence. |
| Blind 6, `McpStdioProcessTests.cs:185` | false | reject | `ConfigCommandTests` asserts exact serialized startup documents for settings and both Catalog gates; the process tests verify the same runner's stderr carriage and exit status. |
| Blind 7, `McpStdioProcessTests.cs:205` | medium | patch | Disposing `Process` does not kill a still-running child after an assertion or timeout. Ensure process cleanup on test failure. |
| Blind 8, `McpStdioProcessTests.cs:209` | medium | patch | `RunAsync` waits on the test context token with no local bound. Apply a child-process deadline and cleanup on timeout. |
| Edge 1, `CliRunner.cs:725-733` | medium | patch | The same throwing-disposal path as Blind 2 can escape without a startup error document. |
| Edge 2, `McpStdioProcessTests.cs:35-80` | medium | patch | The same missing child cleanup as Blind 7 can leave a live server when SDK setup fails. |
| Edge 3, `McpStdioProcessTests.cs:228-239` | low | patch | The child inherits `MCPCLI_STDIO_CATALOG` unless a test overrides it, so a caller environment can select the wrong fixture. Clear it in `Start`. |
| Edge 4, `McpStdioProcessTests.cs:69-76` | medium | patch | The SDK parses stdout while connected, but the test never checks bytes emitted during shutdown. Capture or drain remaining stdout and assert it is empty or valid JSON-RPC. |

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` — succeeds with pinned dependencies.
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` — succeeds without warnings.
- `dotnet test tests/Hexalith.McpCli.Cli.Tests --no-build --configuration Release` — 467 passed, 2 Windows-only skips; includes stdio process and startup checks.
- `dotnet test tests/Hexalith.McpCli.Mcp.Tests --no-build --configuration Release` — 14 passed; includes fixed-surface protocol tests.
- `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` — 8 passed after policy alignment.
- `git diff --check` — reports no whitespace errors.
