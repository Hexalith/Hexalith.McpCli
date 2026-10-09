---
title: 'Keep CLI Output and Exit Codes Predictable'
type: 'feature'
created: '2026-10-09'
status: 'ready-for-dev'
baseline_commit: '52cf2aa31e40b04d2defaa39818e8a53c5eadbee'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Parser errors print usage and exit 1, breaking the Epic 2 script contract. Empty tables contain a spurious row, HTTP refusal omits the release cue, and bad result paths can fail after a Gateway call or profile mutation.

**Approach:** Route parser failures through the existing error writer, fix tables and HTTP wording, and preflight predictable output failures before side effects. Test and document the cross-verb contract.

## Boundaries & Constraints

**Always:** Exit 0 means result, 1 means only `describe --lint` findings, and 2 means no result. Non-MCP errors are one `{ "error": ... }` JSON object on stdout, regardless of format/output; pre-request MCP errors use stderr and leave stdout empty. Parse failures use safe `invalid_arguments` messages without raw token values. Preserve help/version. JSON uses the canonical serializer; only discovery/config displays use tables. Diagnostics and format notes use stderr. Preflight predictable output failures before Gateway calls or profile mutations while preserving file, link, permission, and device behavior. Document residual runtime write failures.

**Never:** Change Core records, Gateway semantics, Profile transactions, MCP JSON-RPC, or `references/`. Preserve JSON escaping and Story 2.2's explicit `activeProfile: null` clear result.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|---------------------------|----------------|
| Parse | Unknown verb/option, surplus config token, missing value, invalid/overflowing number | No action, help, token echo, Gateway request, or profile write | `invalid_arguments`, exit 2; MCP startup uses stderr |
| Result | Discovery, config, describe, send, query; default or `--output` | Canonical document on stdout or file; file output leaves stdout empty | No-result failure leaves existing file intact |
| Table | Empty/nonempty discovery, config, JSON-only verbs | Header plus actual rows; JSON-only verbs emit JSON and one stderr note | Same exit, including lint exit 1 |
| Preflight | Unusable output path on send/query/config mutation | No Gateway request/profile change; target intact | Safe `internal_error`, exit 2 |
| Catalog/MCP | Diagnostics, `--strict`, HTTP transport | Diagnostics on stderr; HTTP refused before Catalog | Strict `catalog_invalid`; HTTP `unsupported_transport` and next-release cue on stderr, empty stdout |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli/Program.cs`, `Cli/CliRunner.cs` -- direct `Parse(...).InvokeAsync()` bypasses errors; add checked invocation. Preserve response-file policy, lint status, and transport-first check.
- `src/Hexalith.McpCli/Cli/GlobalOptionsBinding.cs` -- map known parse failures to public argument names without token echo.
- `src/Hexalith.McpCli/Cli/CliOutput.cs` -- reuse serializer/writer; fix `FormatTable` empty rows and add nonmutating output preflight.
- `src/Hexalith.McpCli.Core/Settings/SettingsResolver.cs`, `Core/Catalog/CatalogProvider.cs` -- existing format/configuration/strict rules; do not duplicate.
- `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs`, `DiscoveryCommandTests.cs`, `ExecutionFailureCommandTests.cs`, `QueryCliHarness.cs` -- stream capture, fixture Catalog, loopback count, file checks, MCP seams.
- `README.md` -- update the parser exception and exit/channel contract.

## Tasks & Acceptance

**Execution:**
- [ ] `src/Hexalith.McpCli/Cli/CliRunner.cs`, `src/Hexalith.McpCli/Program.cs` -- check parse errors before actions, serialize safe `invalid_arguments` errors, and route MCP startup parse errors to stderr; retain help/version semantics and the existing transport-first check.
- [ ] `src/Hexalith.McpCli/Cli/CliOutput.cs` and `CliRunner.cs` -- render empty discovery tables without phantom rows; preflight deterministic output failures before side-effecting actions while reusing the existing file writer's path rules.
- [ ] `tests/Hexalith.McpCli.Cli.Tests/CliOutputContractTests.cs` -- add parser, output/channel, lint, diagnostic, HTTP transport, and preflight cases from the matrix; use the fixture Catalog so `catalog_empty` cannot mask query parser failures.
- [ ] `tests/Hexalith.McpCli.Cli.Tests/DiscoveryCommandTests.cs` -- assert empty tables have a header and no blank data row.
- [ ] `README.md` -- document JSON/error routing, formats, exits 0/1/2, diagnostics, `--strict`, HTTP refusal, and residual write-failure risk.

**Acceptance Criteria:**
- Given any non-MCP result or no-result failure, when a shell script captures stdout, stderr, status, and an optional output file, then exactly the documented destination contains the document and status is 0, 1, or 2 according to the result contract.
- Given a malformed invocation, when parsing fails, then no verb action runs and the invocation exits 2 with one safe addendum §G `invalid_arguments` document.
- Given `mcp --transport http`, when the CLI parses transport before Catalog construction, then stderr contains `unsupported_transport` and a next-release message, stdout is empty, and status is 2.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

Map recognized option failures to their public argument (`pageSize`, `offset`, `tenant`, etc.); use `arguments` for unmatched command syntax. Never include `ParseError.Message` verbatim because it can contain a token or secret. Preflight detects ordinary path/permission failures before an action; it cannot promise that a later disk or device write succeeds. Keep Story 2.2's explicit null for `config use --clear`; addendum §G lists generic tool documents, not config management result shapes.

## Verification

**Commands:**
- `dotnet build tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Debug` -- zero warnings/errors.
- `dotnet tests/Hexalith.McpCli.Cli.Tests/bin/Debug/net10.0/Hexalith.McpCli.Cli.Tests.dll` -- CLI suite passes, including focused Story 2.11 cases.
- Build and run each other test project individually, then `git diff --check` -- existing suites and whitespace pass; changed C# files retain CRLF.
