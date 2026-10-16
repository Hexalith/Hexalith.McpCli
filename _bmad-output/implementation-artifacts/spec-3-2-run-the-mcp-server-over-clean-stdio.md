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

### Review Findings

Code review of 1107ea1..3388bc3 (2026-10-11): Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor.

- [x] [Review][Decision] (resolved: detect faulted `BackgroundService.ExecuteTask` after shutdown and exit 2; `McpHostServingFaultExitsTwoAsync`) A real serving fault exits 0, but the README promises exit 2 — The SDK's `SingleSessionMcpServerHostedService.ExecuteAsync` lets a `session.RunAsync` exception fault the task and then calls `StopApplication`. In Hosting 10.0.12, `BackgroundService.StopAsync` awaits that task with `ConfigureAwaitOptions.SuppressThrowing`, so `WaitForShutdownAsync` returns normally and `RunMcpHostAsync` returns 0 (`src/Hexalith.McpCli/Cli/CliRunner.cs:776-780`). The only output is the host's `BackgroundService failed` log on stderr. `MCP server stopped unexpectedly.` with exit 2 is reachable only through the `_runMcp` test seam. `README.md:126` claims exit 2. Either detect a faulted hosted service after shutdown and exit 2, or reword the README to describe the actual exit 0 with a stderr log. (blind-hunter+edge-case-hunter+acceptance-auditor)
- [x] [Review][Decision] (resolved: guard dropped, plain `host?.Dispose()`) The new `DisposeMcpHost` guard has no test that fails when the guard is removed — `CliRunner.cs:782-792` swallows every disposal exception on the Catalog-rejection, startup-catch, and serving-`finally` paths, but no test makes host disposal throw. `HostFactory.Create` has no way to inject a throwing service, and no throwing disposal was demonstrated with the shipped registrations. The repo rule requires a test that fails without the guard. Either add a host fault-injection seam with tests for both paths, or drop the guard as protecting an undemonstrated state. (blind-hunter+verification-gap)
- [x] [Review][Patch] (resolved: record every stdout byte before SDK parsing and drain the remainder; stdout-noise mutation fails both protocol cases) Clean stdout is checked only after the session ends; the SDK client silently skips non-JSON lines it reads during the session [tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs:38] — record every stdout byte through a pass-through stream handed to `StreamClientTransport` (lines 38 and 103), then run `AssertProtocolOutput` over the full transcript plus the remainder (lines 75 and 116). (blind-hunter+edge-case-hunter+verification-gap+acceptance-auditor)
- [x] [Review][Patch] (resolved: profile supplies a Gateway URL and must make sample.get-item submittable; ignored-profile mutation fails the profile case) The profile scenario can't detect a child that ignores the profile [tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs:28] — `Format: "table"` has no protocol-visible effect, and if the fixture ignored `MCPCLI_STDIO_PROFILE_PATH`, `ProfileStore` would fall back to `$HOME/.eventstore/mcpcli.json` and the test would still pass. Give the profile a URL and assert `submittable: true` for `sample.get-item`; keep the URL-less `configuration_invalid` assertion for the environment case. (blind-hunter+acceptance-auditor)
- [x] [Review][Patch] (resolved: both startup-document markers use Environment.NewLine) The startup-document markers hard-code `\n`, so they fail on Windows [tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs:194] — `McpCliJson.Result` sets `WriteIndented` without overriding `NewLine`, so documents use `Environment.NewLine`. Build the marker from `Environment.NewLine` here and at `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs:1036`. (blind-hunter+edge-case-hunter+verification-gap)
- [x] [Review][Patch] (resolved: cleanup handles cancellation and Win32 kill failures; three injected cases preserve the original exception and directory cleanup, and removing the new alternatives fails timeout and kill cases) Process cleanup can replace the original test failure [tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs:255] — `StopAsync` catches only `InvalidOperationException`. A 5-second `WaitForExitAsync` timeout (`OperationCanceledException`) or a `Kill` failure escapes from `finally`, masks the assertion, and skips `Directory.Delete`. (blind-hunter+edge-case-hunter)
- [x] [Review][Patch] (resolved: both serving tests reject the format note; injected format-note mutation fails both protocol cases) The process tests don't assert that the format note stays off stderr under an inherited `table` format [tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs:79] — the matrix says "no prompt or note", but stderr is checked only for error text, so `This result is emitted as JSON; no table view is defined.` would pass. Add the absence assertion in both serving tests. (acceptance-auditor)

Rejected:

- `false` — The README omits pre-serving error codes: `README.md:99` and `:103` already document stderr pre-serving failures, `internal_error`, and `unsupported_transport`.
- `false` — `McpResolvesSettingsOnceBeforeServingAsync` doesn't prove the build happens before serving: the seam never reads the manifest, so moving the Catalog build out of the pre-serving gate makes `catalogBuilds` 0 and the test fails. The fixed count of nine `EVENTSTORE_*` reads fails loudly by design.
- `false` — The `ExecutionFailureCommandTests` relaxation hides a defect: the console logger writes asynchronously, and stderr ordering between logs and the note isn't part of the output contract.
- `false` — The startup/serving split after `StartAsync` can write a startup document mid-session: with the single SDK hosted service and no lifecycle services, nothing after the transport starts can throw from `StartAsync`.
- `low` — The 2026-07-28 case doesn't assert that `initialize` is absent: a fallback to `initialize` would also have to negotiate 2026-07-28 to pass, which the SDK behavior doesn't show.
- `low` — The fixture calls `CliRunner` through reflection: it fails only when the internal signatures change, and the fix adds `InternalsVisibleTo` to the shipped project.
- `low` — The fixture path assumes the default `bin/<config>/net10.0` layout: the repo and CI use only that layout.
- `low` — Test setup is duplicated with `RunExecutableAsync`: no caller diverges in behavior the tests rely on.
- `low` — Cancellation during startup writes with a cancelled token (reported twice): the same catch pattern predates this change, it only matters on Ctrl+C before serving, and `README.md:101` already documents interruption exits.
- `low` — `_startMcp` without `_runMcp` hangs: this is test-seam misuse that no caller does.
- `low` — Whitespace `--output " "` coverage was removed: any non-null `Output` is rejected, and restoring the case is an addition rather than a correction.
- `low` — The real `StartAsync` failure is pinned only through the seam: the only reachable production `StartAsync` failure is cancellation.
- `low` — Spec status `done` disagrees with sprint status `review`: the fix edits workflow-managed status, which this review updates.
- `low` — The triage log is a table rather than one-line `[Review]` rows: the fix edits the spec under review.
- `low` — The EventStore 3.120.0 policy alignment shipped inside the feature commit: this is commit history, not a code defect, and the ledger forbids reconfirmation entries.
- `false` — "Press Ctrl+C to shut down." is a startup prompt: it is a `Microsoft.Hosting.Lifetime` info log on stderr, which the spec routes there, and no input is awaited.

### Review Findings (2026-10-16)

Code review of 1107ea1..74c63af (2026-10-16): Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor.

- [x] [Review][Defer] No test faults the real SDK hosted service, so the `OfType<BackgroundService>` fault detection is pinned only by a synthetic `FaultingService` [src/Hexalith.McpCli/Cli/CliRunner.cs:787] — deferred: already-unreachable until an SDK change; would be settled by asserting the hosted service registered by `HostFactory.Create(mcp: true)` is a `BackgroundService` (gate: none).

Rejected (2026-10-16):

- `false` — Plain-text serving-failure stderr line contradicts the structured-error rule: the spec's one-structured-error rule covers pre-serving failures, and `README.md:126` documents the fixed diagnostic.
- `false` — A host built alongside an error leaks: `HostFactory.Create` returns null whenever `error` is set (`HostFactory.cs:38`).
- `false` — Serving-phase cancellation reports a crash on Ctrl+C: `ConsoleLifetime` stops the host through `ApplicationStopping`, and no production code cancels the token passed to `WaitForShutdownAsync`; the startup variant is tracked at `deferred-work.md:164`.
- `false` — The `EndsWith(noteLine)` relaxation hides a defect: already adjudicated in the earlier triage (asynchronous console logger ordering is not part of the output contract); the note is still asserted exactly once.
- `low` — Canceled (not faulted) `ExecuteTask` exits 0: no demonstrated path; the fix adds a branch.
- `low` — Cause of a serving fault is not written to stderr: the fixed diagnostic is intentional, and the host logger already records the exception.
- `low` — Fixture reflection uses null-forgiving lookups and a hard-coded `bin/<config>/net10.0` path: already rejected in the earlier triage.
- `low` — `RecordingReadStream` is unsynchronised and the stderr tasks are unobserved on failure: transcripts are read after the child exits, so no interleaving is demonstrated.
- `low` — Missing process coverage (EOF without shutdown, SIGTERM, `--transport http`, write refusal) and README gaps for EOF/signals: speculative additions, not corrections.
- `low` — Fifteen submodule gitlinks moved in `3e02d1e`: commit history, not a code defect; policy versions are aligned per the Implementation Notes.
- `low` — Spec `status: done` vs sprint `review`, triage-log format, and `/tmp` commitlint log path: the fix edits the spec under review or workflow-managed status.

## Implementation Notes

- `tools/dependency-policy.json` matches the current Builds restore: EventStore Client/Contracts 3.121.0, ByteAether.Ulid 1.4.2, JsonPointer.Net 7.0.3, and JsonSchema.Net 9.4.1. A fresh restore exposed five stale policy versions; aligning these entries changes no dependencies or allowed package identities.
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


### Resumed review (2026-10-15)

All three review layers completed before triage. Edge Case Hunter returned no findings. All eight patch entries below are resolved: the lifecycle test captures both channels, counter assertions run at serving entry, rejected Catalogs never reach the startup seam, and process tests cover standalone table rejection, complete SDK-validated transcripts, a successful post-error call, and legacy offline discovery.

| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| Blind R2-1, `ConfigCommandTests.cs:738` | low | patch | The synthetic fault host uses default stdout logging and captures only stderr. Isolate the lifecycle unit test from framework providers and assert both channels so unrelated logs cannot pass unnoticed. |
| Blind R2-2, `ConfigCommandTests.cs:985` | low | patch | Post-invocation counters do not directly assert their values at callback entry. Add the existing count assertions inside `InspectDirectAsync`; this is distinct from merely removing Catalog construction, which the prior review correctly rejected. |
| Blind R2-3, `McpStdioProcessTests.cs:197` | low | patch | Searches found table rejection only with output also present. Add the table-only input to the existing process theory to protect the independent flag rule. |
| Blind R2-4, `McpStdioProcessTests.cs:292` | medium | patch | `RemoveEmptyEntries` demonstrably discards an extra blank stdout line. Allow only the final framing newline and reject empty message lines. |
| Blind R2-5, `McpStdioProcessTests.cs:295` | low | patch | A document containing only the JSON-RPC version satisfies the helper despite lacking any message shape. Validate message shape with the SDK if available, and pin this malformed transcript. |
| Blind R2-6, `McpStdioProcessTests.cs:71` | medium | patch | The final failing request cannot show whether another request remains possible. Make a successful discovery call after the tool error. |
| Blind R2-7, `McpStdioProcessTests.cs:16` | low | patch | Only the newer process revision currently has no URL. Add the legacy offline input to the existing theory; no new test logic is needed. |
| Blind R2-8, `McpStdioProcessTests.cs:310` | maybe-false | reject | A real fixture process holding a temporary file while its kill fails was not demonstrated; ordinary profile reads release file handles. Establishing this needs Windows fault injection with an actual locked fixture file. If true, this is a rare test-cleanup diagnostic issue of low severity, so an additional speculative cleanup policy is rejected. |
| Blind R2-9, spec/sprint status | low | reject | The review stage deliberately sets the spec to in-review; final sprint synchronization belongs to the presentation step. The proposed fix edits this build's workflow-managed spec, which review instructions reject. |
| Verification R2-1, `CliRunner.cs:737` | medium | patch | The gate test supplies only `_runMcp`, skipping the explicit host-start branch; process rejection cases send no request. Add a startup-seam assertion on both rejected Catalog cases so moving the startup block above validation fails deterministically. |

## Verification

**Matrix audit:** `SdkClientDiscoversOverCleanStdioAsync` covers both protocol flows and profile/environment discovery; `ExplicitJsonAndReadOnlyEnvironmentKeepProtocolOutputAsync` and `InvalidPresentationOptionsStopBeforeCatalogAsync` cover presentation options; `StartupFailuresWriteOneStructuredErrorAsync` covers settings, empty Catalog, and strict diagnostics. All 15 process/transcript cases ran and passed, including legacy offline discovery, standalone table rejection, and malformed/blank transcript rejection. `ConfigCommandTests` additionally verifies complete startup documents and one settings/Catalog resolution before serving.

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` — succeeds with pinned dependencies.
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` — succeeds without warnings.
- `dotnet test tests/Hexalith.McpCli.Cli.Tests --no-build --configuration Release` — 475 passed, 2 Windows-only skips after review patches; includes stdio process, startup, and cleanup-failure checks.
- `dotnet test tests/Hexalith.McpCli.Mcp.Tests --no-build --configuration Release` — 14 passed; includes fixed-surface protocol tests.
- `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` — 8 passed after alignment with the current Builds restore.
- `dotnet build tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --no-restore --configuration Release -warnaserror` — succeeds without warnings after the review patches.
- `dotnet tests/Hexalith.McpCli.Cli.Tests/bin/Release/net10.0/Hexalith.McpCli.Cli.Tests.dll -class Hexalith.McpCli.Cli.Tests.McpStdioProcessTests` — 15 passed, including three cleanup-failure cases and SDK transcript validation.
- Temporary fixture mutations — stdout noise fails both protocol cases in `AssertProtocolOutput`; ignoring the configured profile fails the profile `submittable` assertion; an injected stderr format note fails both protocol cases. Original fixture restored and rebuilt.
- Temporary cleanup-guard mutation — removing the cancellation and Win32 alternatives fails the timeout and kill cases. Original source restored and rebuilt.
- `git diff --check` — reports no whitespace errors.

**Additional suite evidence (2026-10-15):** Individual Release runs passed Core (558 passed, 2 Windows-only skips), Abstractions (20 passed), and Analyzers (19 passed). The final CLI lane passed 475 tests with 2 Windows-only skips; MCP passed 14 and Manifest passed 8. Across all six projects, 1,094 tests passed and 4 Windows-only cases were skipped. No matrix case was skipped.

**Resolved verification failure:** After the first fresh `dotnet restore Hexalith.McpCli.slnx`, `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` exited 2 (7 passed, 1 failed). `ProductionContractsStayWithinPinnedDependencyClosure` reported ByteAether.Ulid/1.4.2, Hexalith.EventStore.Client/3.121.0, Hexalith.EventStore.Contracts/3.121.0, JsonPointer.Net/7.0.3, and JsonSchema.Net/9.4.1 outside the stale exact dependency policy. Updating only those policy versions made all 8 Manifest tests pass; no dependency or submodule was updated.

**Commit-message validation:** After `npm ci`, the pinned `npx --no -- commitlint --verbose` accepted the exact local commit-message file with 0 problems and 0 warnings. Evidence: `/tmp/mcpcli-story-3-2-commitlint.log`.
