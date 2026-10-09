---
title: 'Refuse Writes in Read-only Mode'
type: 'feature'
created: '2026-10-05'
status: 'in-progress'
baseline_commit: '3260812a565d5a6d915e3343ebe2941df549ee13'
route: 'oneshot'
review_loop_iteration: 1
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 2.10 requires read-only sessions to refuse command submission with `read_only`, exit 2, and zero Gateway calls. Core already enforces the gate before payload parsing and URL availability, but CLI `send` reads or requires its payload first, so missing files or stdin can mask or delay that refusal. Execution coverage does not prove flag/environment activation and continued query access together.

**Approach:** Route read-only CLI sends through the existing executor before reading payload input or translating extensions. Preserve catalog lookup and operation-kind checks before the read-only gate. Add regression coverage for refusal with and without a URL, invalid and absent payloads, files and stdin, both settings sources, and successful queries. Commands remain discoverable as writes with `submittable: false, reason: read_only`; discovery and queries retain their normal behavior. Document usage and gate precedence.

</frozen-after-approval>

## Implementation Notes

- Planning: no unresolved intent gaps or irreversible actions. Small footprint: one CLI branch, existing Core tests, one CLI acceptance class plus its existing harness, README, and story tracking. No new public API or dependencies. The oneshot route applies.
- Reuse `ExecutionAvailability.ReasonFor` and `OperationExecutor.ExecuteAsync`; keep Core as the owner of lookup, kind, and availability ordering. Pass an empty payload on the read-only CLI path because every supported `SendCommandArguments` exits before parsing in that mode.
- Existing discovery tests already cover flag activation with/without URL and retain writes. Extend acceptance coverage for environment activation using `QueryCliHarness` and its bounded loopback request capture.
- Verification: build Core and CLI test projects in Debug individually; run focused new/changed cases first, then complete Core, CLI, and MCP suites. Inspect exact JSON errors, zero requests on refusal/discovery, one query request on success, and unchanged output files. Check whitespace and C# CRLF endings.
- User approved proceeding over prior work. At resumption the worktree was clean at the baseline above; preserve any later unrelated changes.

- Implemented the early CLI dispatch with no Core policy duplication. The reviewed implementation contains 32 CLI acceptance cases and 13 direct executor refusal cases. The input test uses a disposed reader to detect any stdin acquisition, and verifies exact error JSON, exit 2, zero Gateway requests, and preserved result-file contents. Both flag/environment modes execute valid queries through the real client; environment discovery and explicit false override are covered.
- Initial focused verification passed before the additional review cases. Resumption verification passes all 32 CLI acceptance cases and all 13 direct executor refusal cases in the full Core suite. CLI and Core Debug builds succeeded with zero warnings/errors.
- Review patches add a successful one-request command with `--read-only false`, three direct-executor identity/extension refusal cases, and the settings/catalog prerequisite in README. The loopback harness now optionally returns a Command 202 response; existing query fixtures keep their defaults.
- Final full-lane results: Core 557 passed / 2 existing Windows-only skips (559 total); CLI 424 passed; MCP 6 passed; Abstractions 20 passed; Analyzers 19 passed. All six individual Debug test-project builds passed with zero warnings/errors. Final whitespace and changed C# CRLF checks passed.
- Full acceptance remains blocked by an existing Manifest dependency-policy failure (7 passed, 1 failed). Per the repository baseline's requirement that all existing/new tests pass, leave this spec `in-review` and sprint story `review`, rather than marking the story complete. Production code and story acceptance tests are implemented and reviewed.
- Commit-message validation: `npx --no -- commitlint --edit /tmp/mcpcli-2-10-commit-message.txt` exited 0; exact candidate and captured output are preserved in `/tmp/mcpcli-2-10-commit-message.txt` and `/tmp/mcpcli-2-10-commitlint.log`.

- Resumed from clean `main` at `2ea615ca54de49bb1aca53d6ff0e25e5830c7f41` on 2026-10-05. Applied the three outstanding review patches: documented exact environment boolean values and override precedence, documented the harness's command acceptance response, and replaced untyped refusal rows with `TheoryData<bool, bool, string>`.
- All six individual test-project Debug builds passed with zero warnings/errors. The focused CLI class passed 32/32; the complete suites passed CLI 424, Core 557 with two existing Windows-only skips, MCP 6, Abstractions 20, and Analyzers 19. XML evidence is preserved in `/tmp/mcpcli-2-10-resume-{Cli,Core,Mcp,Abstractions,Analyzers}.xml`.
- Stale MCP/Abstractions restore assets initially selected EventStore 3.112.0 while rebuilt shared assemblies required 3.113.0. `dotnet restore Hexalith.McpCli.slnx --verbosity quiet` exited 0 using the existing central pins; rebuilding and rerunning those suites resolved their assembly-load failures. No tracked dependency, policy, build configuration, or submodule change was made.
- The required all-tests gate still prevents completion because the exact dependency-policy test fails on EventStore 3.113.0 versus policy 3.110.0. Keep the spec `in-review` and sprint story `review`; the existing deferred-work entry owns dependency reconciliation.
- Resumption commit-message validation: the pinned commitlint 21.2.2 command `npx --no -- commitlint --edit /tmp/mcpcli-2-10-resume-commit-message.txt --verbose` exited 0 with zero problems. The exact message and successful output are preserved in that file and `/tmp/mcpcli-2-10-resume-commitlint.log`.

- Resumed from clean `main` at `8953c8bf4e9abcbb5896d87102c2d4f178d11a8a` on 2026-10-05. Completed the remaining cumulative-review patches: README now distinguishes read-only precedence from ordinary CLI input binding and includes identifier validation; invalid environment values are documented as failing whenever the setting is resolved. Added the three missing blank lines in the CLI acceptance tests and loopback harness, preserving CRLF. The dependency-policy blocker is already resolved by `4d39200b45858c621cf40ff7bd8ec1491ba19803` in this repository history; the full Manifest suite passed in this resumption.

- Final validation on 2026-10-05: all six individual test-project Debug builds (`dotnet build tests/Hexalith.McpCli.<Suite>.Tests/Hexalith.McpCli.<Suite>.Tests.csproj --configuration Debug --no-restore --verbosity quiet`) succeeded with zero warnings/errors. The focused CLI read-only class passed 32/32. Complete suites passed CLI 424, Core 557 with two existing Windows-only skips, MCP 6, Abstractions 20, Analyzers 19, and Manifest 8: 1,034 passed, two skipped, zero failures/errors. Each suite was run directly with `dotnet tests/Hexalith.McpCli.<Suite>.Tests/bin/Debug/net10.0/Hexalith.McpCli.<Suite>.Tests.dll -result-xml /tmp/mcpcli-2-10-final-<Suite>.xml`; XML and test logs for every suite, five subsequent build logs, and `/tmp/mcpcli-2-10-final-validation.json` preserve the results. The CLI build's successful output is in this session. No remaining acceptance blocker or dependency change.
- Exact commit-message validation with the pinned `@commitlint/cli@21.2.2`: `npx --no -- commitlint --edit /tmp/mcpcli-2-10-final-commit-message.txt --verbose` exited 0 with zero problems/warnings. The full candidate and successful output are preserved in that file and `/tmp/mcpcli-2-10-final-commitlint.log`. Whitespace and changed C# CRLF checks passed.

- Resumed from clean `main` at `e159f82b7528797fc245045625ff387d65294ba9` on 2026-10-05. Addressed the two outstanding cumulative-review patches in README: ordinary `send` precedence now names the errors users see first, and environment validation documents command-line parse failures and the three rejected `config profile add` operator flags as early exits. Checked both statements against `CliRunner`, `SettingsBootstrap`, and `SettingsResolver`; no execution behavior or dependencies changed.
- Closing validation: the focused CLI read-only class passed 32/32. All six individual Debug test-project builds succeeded with zero warnings/errors; complete suites passed CLI 424, Core 557 with two existing Windows-only skips, MCP 6, Abstractions 20, Analyzers 19, and Manifest 8 (1,034 passed, two skipped, zero failures/errors). Commands, results, and log paths are recorded in `/tmp/mcpcli-2-10-close-validation.json`; suite XML is `/tmp/mcpcli-2-10-close-<Suite>.xml`, and the focused XML is `/tmp/mcpcli-2-10-close-ReadOnlyCommandTests.xml`. CLI build and focused-run output are preserved in this session. The pinned commitlint 21.2.2 command `npx --no -- commitlint --edit /tmp/mcpcli-2-10-close-commit-message.txt --verbose` exited 0 with zero problems/warnings; the exact full message is preserved in that file and successful validation output in this session.

- Resumed from clean `main` at `0937e0b6fdd429764f7d5a555a932481a833979b` on 2026-10-05. Completed the two post-closing review patches: README now states the flag's optional, case-insensitive `true`/`false` values separately from the environment's exact values, and places both read-only paragraphs after the Commands and Queries guidance. The original baseline and frozen intent remain intact.

- Documentation resumption validation: all six individual Debug test-project builds succeeded with zero warnings/errors using `dotnet build tests/Hexalith.McpCli.<Suite>.Tests/Hexalith.McpCli.<Suite>.Tests.csproj --configuration Debug --no-restore --verbosity quiet`. Direct runs with `dotnet tests/Hexalith.McpCli.<Suite>.Tests/bin/Debug/net10.0/Hexalith.McpCli.<Suite>.Tests.dll -result-xml <evidence-directory>/<Suite>.xml` passed Core 557 (two existing Windows-only skips), CLI 424, MCP 6, Abstractions 20, Analyzers 19, and Manifest 8: 1,034 passed, two skipped, zero failures/errors. The focused CLI read-only class passed 32/32. Exact commands, build/test logs, suite XML, and results are preserved in `/tmp/mcpcli-2-10-docs-fj8vjhrg/validation.json` and that directory. Seven process-level `config current --read-only` checks verified no value, `true`, `True`, `FALSE`, and `false`, plus numeric `1` and `0` rejection with parser exit 1; `flag-values.json` records each command and result. The pinned commitlint 21.2.2 command `npx --no -- commitlint --edit /tmp/mcpcli-2-10-docs-fj8vjhrg/commit-message.txt --verbose` exited 0 with zero problems/warnings; `commit-message.txt` and `commitlint.log` preserve the exact candidate and validation evidence. Whitespace, original baseline, and frozen-intent checks passed.

- Resumed from clean `main` at `5a0eaa4c7687197dc40c5b0d2d6bd1c18c8d53e5` on 2026-10-08. Corrected the remaining post-bump README finding: numeric `1`/`0` are not boolean flag values; use `true`/`false`. Removed the unconditional parser-exit claim because an unbound positional argument can consume a numeric token. The read-only execution behavior and existing regression tests already satisfy all four story acceptance criteria; this resumption changes documentation and tracking only. Validation evidence for this resumption is collected in `/tmp/mcpcli-2-10-oct08-_4sgoz1_`.

- Current resumption validation: `dotnet restore Hexalith.McpCli.slnx --verbosity quiet` succeeded and restored EventStore Client/Contracts 3.117.1. All six individual Debug test-project builds succeeded with zero warnings/errors. Direct test-assembly runs passed CLI 424, Core 557 (two existing Windows-only skips), MCP 6, Abstractions 20, Analyzers 19, and Manifest 8: 1,034 passed, two skipped, zero failures/errors. The focused `ReadOnlyCommandTests` class passed 32/32. Exact commands, exit codes, build/test logs, suite XML, and results are preserved in `/tmp/mcpcli-2-10-oct08-_4sgoz1_/validation.json` and its directory. `git diff --check` passed. Pinned commitlint 21.2.2 validation with `npx --no -- commitlint --edit /tmp/mcpcli-2-10-oct08-_4sgoz1_/commit-message.txt --verbose` succeeded with zero problems/warnings; the exact full candidate and successful output are preserved in `commit-message.txt` and `commitlint.log` there.

- Review verification: six process-level probes against the current Debug CLI are recorded in `/tmp/mcpcli-2-10-oct08-_4sgoz1_/flag-values.json`. With an invalid `EVENTSTORE_READ_ONLY` value, `operations --read-only 0` and `describe --read-only 1` passed parsing and settings resolution before returning `catalog_empty` (exit 2; no production Contracts are enrolled); the numeric token binds the missing name and the bare flag overrides the environment. `operations example --read-only 0` and `config current --read-only 0` failed parsing (exit 1). `config current --read-only` reported `readOnly: true`; explicit `false` reported `readOnly: false`. README now gives the positional-token example without promising a parser exit code. The optional ConformanceHost build command `dotnet build tests/Hexalith.McpCli.ConformanceHost/Hexalith.McpCli.ConformanceHost.csproj --configuration Debug --no-restore --verbosity quiet` was blocked by `NETSDK1064` (Dapr.Common 1.18.10 missing from that host's stale restore location); the probes instead used the already validated production CLI directly, so no remaining validation blocker or package change was introduced.

- Resumed from clean `main` at `d2a607d50afb7a86e5c16095df34724c9c8242e8` on 2026-10-08. Completed the three Post-Sync Cumulative Review patches: README distinguishes missing payloads from unreadable payload files and explains `config current` read-only state/source inspection; direct-executor envelope refusal now asserts the complete stable `OperationError` record. Preserved the original baseline, frozen intent, and C# CRLF endings. Validation evidence for this resumption is collected in `/tmp/mcpcli-2-10-post-sync-iznn0fbz`.

- Post-Sync resumption validation: `dotnet restore Hexalith.McpCli.slnx --verbosity quiet` succeeded using the existing central package pins. All six individual Debug test-project builds passed with zero warnings/errors; direct assembly runs passed Core 557 (two existing Windows-only skips), CLI 424, MCP 6, Abstractions 20, Analyzers 19, and Manifest 8 (1,034 passed, two skipped, zero failures/errors). Focused direct assembly runs passed the 13 Core refusal cases and all 32 CLI read-only cases. Exact commands, exit codes, logs, and XML are preserved in `/tmp/mcpcli-2-10-post-sync-iznn0fbz/validation.json` and its directory; `summary.json` records the complete-suite counts. Pinned commitlint 21.2.2 validation with `npx --no -- commitlint --edit /tmp/mcpcli-2-10-post-sync-iznn0fbz/commit-message.txt --verbose` exited 0 with zero problems/warnings; the exact candidate and successful output are preserved in `commit-message.txt` and `commitlint.log`. The independent review adds explicit JSON format to the configuration-inspection example; no execution behavior or dependency changes were needed. Build status is `done`; sprint status is `review` according to the oneshot workflow.

- Resumed on 2026-10-09 from clean `main` at `dbfbc23f91e3b545cde68ea083294ba59ada2701`. Closed the two outstanding Post-Fix review patches: README now names MCP `--transport`, `--format`, and `--output` as early validation exits; the read-only CLI acceptance tests assert stderr for lookup, discovery, description, and explicit-false override calls. No production behavior or dependencies changed.
- Current verification: `dotnet build tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Debug --no-restore --verbosity quiet` passed with zero warnings/errors; the focused `ReadOnlyCommandTests` passed 32/32. After the first test edit, all six direct Debug suites passed: CLI 424, Core 557 with two Windows-only skips, MCP 6, Abstractions 20, Analyzers 19, and Manifest 8 (1,034 passed, two skips). After review extended stderr assertions to the explicit-false cases, the CLI test project rebuilt cleanly and the focused 32/32 cases passed again. `git diff --check` passed; changed C# lines retain CRLF.
- The exact commit message is preserved in `/tmp/mcpcli-2-10-oct09-commit-message.txt`; pinned `npx --no -- commitlint --edit /tmp/mcpcli-2-10-oct09-commit-message.txt --verbose` exited 0 with zero problems and warnings.

## Review Triage Log

### October 9 Resumption Review Triage

Independent Blind Hunter reviewed 2.625 kB of changed content; finding floor `min(floor(sqrt(2.625) + 1), 10) = 2`. All three findings were checked; nothing was deferred.

- **Low, rejected:** The README's MCP early-exit statement lacks dedicated invalid-`EVENTSTORE_READ_ONLY` test rows. `CliRunner.RunMcpAsync` returns for unsupported `--transport`, non-JSON explicit `--format`, and any `--output` before `HostFactory.Create` resolves settings; the existing tests cover those option errors, and `ConfigCommandTests` covers invalid read-only environment values. Dedicated cross-product rows would mirror this unchanged control flow.
- **Low, rejected:** Lookup and kind precedence are tested with flag activation only. Both activation sources reach the same `ResolvedSettings.ReadOnly` branch; `SendRefusesBeforeReadingInputAsync` proves environment activation reaches that branch, while the lookup/kind theory pins its ordering. Extra environment rows would repeat unchanged behavior.
- **Low, patched:** The two explicit-false override tests did not inspect stderr. Both now call `AssertDiagnostics`, matching the other invocations in this acceptance class; the focused class passes 32/32.

### Post-Sync Resumption Review Triage

Independent Blind Hunter reviewed the current worktree (5.388 kB; finding floor `min(floor(sqrt(5.388) + 1), 10) = 3`). All three findings were checked against their callers and existing tests; nothing was deferred.

- **Low, patched:** The configuration-inspection example inherited the selected output format, which could be table. `ConfigCommandTests` verifies both table rendering and source reporting; the example now requests `--format json` so `sources.readOnly` appears as the documented JSON path. It also says to retain the same read-only flag and environment because flags apply to each invocation.
- **Low, rejected:** The envelope-refusal theory lacks an explicit aggregate mismatch row. This is an existing optional coverage expansion: `OperationExecutor` checks availability before payload parsing, while aggregate selection/mismatch validation follows deserialization and envelope filling; the ten existing payload refusal rows already pin this ordering. The changed assertion strengthens the complete error contract for the three existing envelope cases. Adding another scenario and discriminator branch would cover a speculative reorder rather than a defect introduced here.
- **False, rejected:** An unsupported `invalidField` can produce valid arguments, but all three theory rows are fixed in this file and exactly match the three branch values (`correlation`, `idempotency`, `extensions`). No external input or current caller supplies another value; a throwing guard would protect an unreachable case rather than fix a vacuous current test.


### October 8 Resumption Review Triage

Independent Blind Hunter reviewed the current worktree (4.607 kB; finding floor `min(floor(sqrt(4.607) + 1), 10) = 3`). All three findings were checked; nothing was deferred.

- **Low, patched:** README omitted the positional-token behavior behind the correction. `CreateOperations` binds an optional module name, and current process probes confirm that `operations --read-only 0` reaches catalog access while `operations example --read-only 0` fails parsing. Added an example explaining that the bare flag enables read-only mode and `0` becomes the module name.
- **Low, patched:** The current validation record had no numeric-token probes. Added six direct CLI checks covering omitted and supplied positional arguments, parser rejection, bare-flag activation, and explicit false. Their exact commands and results are in `flag-values.json` alongside the build/test evidence.
- **False, rejected:** Earlier documentation triage is a historical record of the prior resumption's `config current` probes, not current flag guidance. The Post-Bump Cumulative Review Findings already identify the incorrect generalization, and this resumption corrects it. This October 8 triage supersedes that earlier numeric-parser conclusion; the original observations are retained as history.

### Documentation Resumption Review Triage

Independent Blind Hunter reviewed the current worktree (5.312 kB; finding floor `min(floor(sqrt(5.312) + 1), 10) = 3`). All three findings were checked; no new work was deferred.

- **Low, patched:** The adjacent environment values made numeric flag failures easy to miss. Process-level checks confirmed `--read-only 1` and `--read-only 0` fail parsing with exit 1; README now states both explicitly.
- **Low, patched:** The moved refusal paragraph mentioned extension validation before its later explanation. README now introduces the exact `--extension key=value` syntax at that first prose reference.
- **False, rejected:** This resumption lacked validation evidence. Review read the interim implementation note while verification was still running; finalization now records all current build/test commands and results, the seven parser checks, and pinned commitlint evidence in Implementation Notes above.

### Closing Review Triage

Independent Blind Hunter reviewed this resumption's changed files (4.223 kB, finding floor `min(floor(sqrt(4.223) + 1), 10) = 3`). All three findings were verified against the implementation and patched; nothing was deferred.

- **Low, patched:** "Malformed extension entries" overstated which errors precede lookup. `CliRunner.CreateSend` checks only a nonempty key before `=` and exact duplicate keys; Core checks key grammar, case-insensitive duplicates, and the allowlist later. README now names the early checks precisely.
- **Low, patched:** The early-exit wording omitted failures earlier in settings resolution. `SettingsResolver.Resolve` validates profile selection, URL, format, text settings, and the tenant-override boolean before the read-only boolean. README now states that earlier configuration errors can take precedence, with URL and profile examples.
- **Low, patched:** The precedence explanation omitted stable error codes. Confirmed the CLI's early input checks return `invalid_arguments`, catalog lookup returns `unknown_operation`, and sending a read returns `validation_failed`; README now names all three.

Build workflow complete: spec status is `done`; sprint status advances to `review` as required by the oneshot workflow, pending the separate sprint review gate.

- **Low, rejected:** The missing-file case cannot detect a hypothetical read whose exception is discarded before refusal. The actual branch returns before `ReadPayloadAsync`; moving it below existing acquisition fails the absent/file/stdin cases. Detecting an otherwise invisible discarded read needs a new I/O seam or platform-specific blocking-file fixture, disproportionate to this speculative regression. The disposed-reader case directly detects stdin acquisition.
- **Low, patched:** The explicit-false case stopped at malformed JSON. Added a valid command and Command 202 loopback response, asserting accepted result and exactly one Gateway request.
- **Low, patched:** Direct-executor refusal tests lacked invalid envelope inputs. Added separate invalid correlation, idempotency, and unapproved-extension cases with valid payloads and zero Gateway interactions.
- **Low, patched:** README overstated unconditional refusal. Qualified the behavior with successful settings resolution and catalog access; unknown-operation and kind errors remain documented.

### Review Findings

Code review 2026-10-05 of `3260812..269369e` (Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor; no layer failed).

- [x] [Review][Patch] README now documents exact `true`, `false`, `1`, `0` values, case sensitivity, and explicit-flag precedence during read-only settings resolution [README.md:69].
- [x] [Review][Patch] `QueryCliHarness` class and constructor summaries now describe query and command responses, including the `commandResponse` HTTP 202 mode [tests/Hexalith.McpCli.Cli.Tests/QueryCliHarness.cs:16].
- [x] [Review][Patch] `RefusedInputs` now returns `TheoryData<bool, bool, string>` and adds typed rows matching the theory signature [tests/Hexalith.McpCli.Cli.Tests/ReadOnlyCommandTests.cs:11].
- [x] [Review][Defer] Manifest dependency-policy gate fails on EventStore Client/Contracts drift from the 3.110.0 pin [tools/dependency-policy.json:27] — deferred: pre-existing; already tracked (`deferred-work.md:353`); no new ledger entry

Rejected:

- `false` — Stale-restore claim (suites ran on 3.112.0 binaries, ledger names wrong version): a fresh 3.113.0 restore/build reproduced CLI 424 and Core 557+2 skipped; the ledger entry already names Builds' 3.113.0.
- `low` — Explicit-false send asserts only the request count, not route/envelope: `AssertRequest` hardcodes `/api/v1/queries`, so checking needs a new harness parameter; the command route is covered by `CliMcpCommandParityTests` and `ExecutionFailureCommandTests`.
- `false` — Read-only CLI "silently drops" `--aggregate-id`/`--correlation-id`/`--idempotency-key`: refusal before identity validation is the AD-12 order (availability before parse and identifier checks), proven for direct callers by `ReadOnlyCommandFailsBeforeEnvelopeValidationAsync`.
- `low` — No CLI test that settings/catalog failures precede `read_only`: settings resolve in `RunAsync` before any handler and the executor checks catalog access first, so ordering is structural; adding tests outweighs the risk.
- `false` — `read_only` error lacks `operation`: `OperationError.Operation` is defined only for lookup and validation failures, and `ResultDocumentContractTests` fixes the Story 2.9 `read_only` shape without it.
- Fix edits this spec — Implementation-note counts (31/10) predate the review patches (32/13 now) and `review_loop_iteration: 0`.
- Fix edits this spec — Evidence cited under `/tmp`; an empty commitlint log is expected, since commitlint prints nothing on success.
- `false` — Stdin comment wrong for the absent case: it states the disposed reader catches any stdin acquisition, including an omitted-payload fallback; the absent row still fails the old code via `read_only`.
- `false` — README duplication/placement: the global-options sentence and the new paragraph agree; no reader is misled.
- `low` — Non-read-only send without a URL reads stdin/file before `configuration_invalid`: pre-existing, outside this story, and the fix adds a new availability branch.
- `false` — CLI gate could diverge from Core's `ExecutionAvailability`: both come from the single host `ResolvedSettings` snapshot; a Core reorder fails the exact-JSON refusal tests and never submits.
- `low` — Harness silently ignores `paging`/`nullDocument` with `commandResponse`: no caller combines them; a guard adds complexity for an unreachable case.
- `false` — `modules` untested in read-only: `DiscoveryCommandTests.AvailabilityUsesReadOnlyAndUrlWithoutFilteringListsAsync` runs `modules` with `--read-only`.
- Fix edits this spec — Same stale verification counts as above (Acceptance Auditor).
- `low` — Environment activation tested only with `true`: the single shared `SelectBoolean` switch is exercised by `ConfigCommandTests` (including the invalid `yes`); extra end-to-end rows add little.

### Resumption Review Triage

Independent Blind Hunter reviewed the three changed files during this workflow run (1.429 kB, finding floor 2).

- **Low, patched:** The new environment documentation initially promised `configuration_invalid` before every verb. `CliRunner.RunMcpAsync` rejects HTTP transport before settings resolution, and profile-management verbs resolve presentation settings only. Restricted the statement to read-only settings resolution, preserving both paths' error precedence.
- **Low, rejected:** The command-override case checks one request and the accepted result without using the query-only `AssertRequest`. The harness captures commands correctly; its updated summary makes no promise that the query assertion accepts commands. `CliMcpCommandParityTests` already verifies command POST routing, payload, tenant, aggregate and envelope identifiers. Extending this harness for the same assertions adds a test seam for an existing hypothetical regression without any command-path change in this resumption.

### Cumulative Review Findings

Code review 2026-10-05 of `3260812..2978717`, excluding this spec (Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor; no layer failed). Verification Gap found no gaps and reran the focused class (32 passed).

- [x] [Review][Decision] Dependency-policy blocker has no owner, so the story has no path to `done` — Resolved (option 1): `4d39200` aligns both pins to 3.113.0 in a separate `build(deps)` commit; the full Manifest suite passes 8/8. The only open blocker is the pre-existing Manifest failure (EventStore Client/Contracts restore 3.113.0 against policy 3.110.0). The ledger entry names no owner, and every later story inherits the failing gate. Choose: align `tools/dependency-policy.json` to 3.113.0 in a separate `build(deps)` commit (precedent `06514df`), or close 2.10 with a documented exception and give the reconciliation an owner in `sprint-status.yaml` `action_items`.
- [x] [Review][Patch] README understates read-only refusal precedence: lookup and kind errors win over missing-payload and extension errors only in read-only mode, and identifier options also go unvalidated [README.md:67]
- [x] [Review][Patch] README "During read-only settings resolution" is ambiguous; state that the value fails whenever the read-only setting is resolved [README.md:69]
- [x] [Review][Patch] Ledger evidence reports a stale 3.112.0 restore and omits the drift source, the Builds `HexalithEventStoreVersion` default of 3.113.0 [_bmad-output/implementation-artifacts/deferred-work.md:357] — superseded by the decision: the entry now carries `status: resolved by 4d39200` naming the 3.113.0 source
- [x] [Review][Patch] Story 2.10 ledger entry sits under the Story 2.9 pass-2 heading; give it its own `implementation of` heading [_bmad-output/implementation-artifacts/deferred-work.md:353]
- [x] [Review][Patch] Statements directly follow closing braces, unlike the touched files' convention [tests/Hexalith.McpCli.Cli.Tests/QueryCliHarness.cs:58; ReadOnlyCommandTests.cs:90, :145]

Rejected:

- `false` — Stdin comment overstates the absent case: the comment is conditional; it detects any stdin acquisition, including a regression that falls back to stdin for an omitted payload. Prior triage reached the same verdict.
- `low` — Harness ignores `paging`/`nullDocument` with `commandResponse`: no caller combines them; a guard adds complexity for an unreachable case.
- `low` — Explicit-false send asserts only the request count: `CliMcpCommandParityTests` covers command routing and envelope; checking them here needs a new harness parameter.
- `low` — `AssertRequest` hard-codes `/api/v1/queries`: no command test calls it, so it cannot pass wrongly; a path parameter adds harness surface.
- `false` — Spine and addendum need a read-only exception to CLI input binding: addendum §G (`addendum.md:424`) states where `invalid_arguments` originates, not that binding always precedes Core. The read-only branch still emits the empty-operation `invalid_arguments` before Core, and AD-4 (`ARCHITECTURE-SPINE.md:49`) holds because Core, not the head, produces `read_only`. The README imprecision is patched above.
- `false` — CLI relies on an unstated empty-payload assumption: the comment at `CliRunner.cs:174` states it, Core's `""` rows pin it, and a divergence yields only `validation_failed` with zero Gateway calls.
- `low` — Invalid `EVENTSTORE_READ_ONLY` with an explicit flag, and `True`, are untested: `SelectBoolean` returns the flag before reading the environment (`SettingsResolver.cs:153-157`), and the `TRUE`/`False` rows exercise the same case-sensitive switch.
- `low` — Direct-executor refusal lacks aggregate and tenant rows: moving those later checks above availability is unlikely; correlation, idempotency, and extension rows already pin the order.
- `low` — Empty-payload sentinel and duplicated execute/write tail in `CliRunner`: three duplicated lines with a documenting comment; restructuring exceeds a direct correction.
- `false` — `QueryCliHarness` name and single-variable environment hook: no current caller is misled or blocked; the rename and dictionary hook serve only hypothetical tests.
- `low` — Canned 202 response reuses one ULID for `messageId` and `correlationId`: Core executor tests and `CliMcpCommandParityTests` cover the field mapping, which this story does not change.
- `false` — `ExplicitFalseOverridesEnvironmentAsync` is redundant: it covers the override reaching payload validation with zero requests, a failure path the successful send does not exercise.

### Final Resumption Review Triage

Independent Blind Hunter reviewed the current worktree changes; the configured oneshot workflow has no other review layers. Finding floor: `min(floor(sqrt(3.681) + 1), 10) = 2`. Both findings were checked against the implementation and patched; nothing was deferred.

- **Low, patched:** README's new lookup/kind precedence wording could be read as applying to `query` in read-only mode. `CliRunner.CreateQuery` still acquires its payload before Core lookup. Scoped both precedence statements explicitly to `send`; queries retain their normal input path.
- **Low, patched:** "Whenever the read-only setting is resolved" did not tell users which commands validate the environment value. `SettingsBootstrap.ResolvePresentation` calls the complete `SettingsResolver` even for profile-management verbs, while help/version and `CliRunner.RunMcpAsync` transport/output-option rejection can finish before settings resolution. Named discovery, execution, `config` (including profile management), and MCP stdio startup, plus these early exits, in README.

### Final Cumulative Review Findings

Code review 2026-10-05 of `3260812..8dd69d6`, excluding this spec (Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor; no layer failed). Verification Gap found no gaps and reran `ReadOnlyCommandTests` (32 passed), the Core read-only cases, and the Manifest suite (8 passed).

- [x] [Review][Patch] README's ordinary-`send` precedence sentence uses internal terms ("CLI payload acquisition", "extension binding", "Core lookup") that appear nowhere else in README; state it as which errors users see first [README.md:67]
- [x] [Review][Patch] README's list of exits that precede `EVENTSTORE_READ_ONLY` validation omits command-line parse failures and the `config profile add` operator-flag refusal, which returns `invalid_arguments` before settings resolution (`CliRunner.cs:331-335`) [README.md:69]

Rejected:

- Fix edits this spec — Spec `status: 'done'` disagrees with sprint `review` (Acceptance Auditor): the spec was marked done in `8dd69d6` before this review finished; this review's completion sets both to the same status.
- Fix edits this spec — Same status mismatch (Blind Hunter).
- Fix edits this spec — The dependency-policy bump contradicts the "no dependency change" note: it is the approved cumulative Decision (option 1), landed separately in `4d39200`.
- `false` — Stdin comment wrong for the omitted payload: the comment is conditional and detects a regression that falls back to stdin for an omitted payload. Third identical verdict.
- `false` — README does not name the errors that precede `read_only`: "After settings resolution and catalog access succeed" covers `configuration_invalid`, `catalog_empty`, and `catalog_invalid`; README:44 documents the current `catalog_empty` state, and an empty operation name names no declared write.
- `false` — Empty `EVENTSTORE_READ_ONLY=` is undocumented: `SelectBoolean` throws for `""` (`SettingsResolver.cs:160-168`), so "any other value" is accurate. On Windows, an empty assignment unsets the variable at the shell level, which gives the documented default. The resolver is unchanged by this story.
- `false` — Flag `true` over environment `false` is untested: `SelectBoolean` returns any non-null flag before reading the environment (`SettingsResolver.cs:154-158`), and the explicit-false tests exercise that same branch.
- `false` — Lookup/kind precedence is tested only with stdin: the read-only branch reads no payload or extension option (`CliRunner.cs:172-179`), so the input form cannot change the result; the 24-row refusal matrix catches any reorder.
- `false` — Identifier options are untested in read-only CLI: the branch builds `SendCommandArguments(name, string.Empty)` without them. Core rows pin correlation and idempotency, and aggregate validation follows payload parsing, which the `{` and `""` rows show comes after refusal.
- `false` — Duplicated ULID literal and hand-written matrix in `ReadOnlyCommandFailsBeforeGatewayAsync`: refusal precedes parsing, so payload values are irrelevant and no divergence can weaken the test.
- `false` — Nothing durable stops dependency drift: CI runs the Manifest suite (`.github/workflows/ci.yml:26`), so a drifting `references/` bump fails the blocking gate.
- `false` — Ledger entry contradicts itself: `evidence` records the first run's observation, while `status` names the fresh-restore 3.113.0 source and the resolution. The cumulative Decision already settled this.
- `low` — Harness ignores `paging`/`nullDocument` with `commandResponse`: no caller combines them; a guard adds complexity for an unreachable case. Third identical verdict.
- `low` — Explicit-false send asserts only the request count: `CliMcpCommandParityTests` covers command routing and the envelope; asserting them here needs a new harness parameter. Third identical verdict.

### Post-Closing Cumulative Review Findings

Code review 2026-10-05 of `3260812..6d7eab8`, excluding this spec (Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor; no layer failed). Verification Gap found no gaps. Acceptance Auditor found no acceptance-criteria violations and reran `ReadOnlyCommandTests` (32 passed).

- [x] [Review][Patch] README documents the accepted `EVENTSTORE_READ_ONLY` values but not the flag's, which differ. `--read-only 1` and `--read-only 0` fail to parse (exit 1, "Unrecognized command or argument"), while `--read-only True` is accepted, as verified against the built CLI. State that the flag takes no value, `true`, or `false` (case-insensitive) [README.md:69]
- [x] [Review][Patch] The read-only paragraphs precede the `send` and `query` paragraphs they depend on: they reference `--aggregate-id`, `--correlation-id`, `--idempotency-key`, extensions, and `invalid_arguments` before those are introduced. Move both paragraphs after the Queries paragraph [README.md:67]
- [x] [Review][Defer] `--read-only` help text says only "Disable command submission" and does not mention `EVENTSTORE_READ_ONLY` or the explicit `false` override [src/Hexalith.McpCli/Cli/GlobalOptionsBinding.cs:18] — deferred: pre-existing since `de67938` (Story 2.1); no global option's help names its environment variable, so this is a CLI-wide help convention

Rejected:

- `false` — No README read-only example: README:67 gives both activation forms (`--read-only`, `EVENTSTORE_READ_ONLY=true`), README:65 states the MCP tool-list effect, and scripts match the documented `read_only` code with exit 2.
- `false` — "even without a Gateway URL" attaches to the wrong clause: it qualifies "returns `read_only`", which is the guarantee that `read_only` beats the missing-URL error.
- `false` — `refusal` is misnamed because the branch can return lookup, kind, or catalog errors: every one of those outcomes refuses the send. Availability and `settings.ReadOnly` come from one settings snapshot, so this branch can never submit.
- `false` — No Core test runs a successful read-only query: `QueryRemainsAvailableAsync` drives the real `OperationExecutor` with `ReadOnly` true for both activation sources, and the MCP server uses the same executor, so an executor regression fails that test.
- `false` — Dependency-drift rule is buried in a resolved ledger entry: CI runs the Manifest suite (`.github/workflows/ci.yml:26`), which checks restored assets whatever the version source (submodule, MSBuild override, checkout layout). Fourth identical verdict.
- `false` — `--output`/`--format table` add no read-only evidence and leak temp files: the spec's verification requires unchanged output files, and `finally` deletes the temp file.
- `false` — Environment discovery test is weaker than the flag test: listing reads only the resolved `ReadOnly` boolean, never its source. The `describe` assertions prove environment activation, and `DiscoveryCommandTests` proves the exact unfiltered listing for `ReadOnly` true.
- `low` — Harness ignores `paging`/`nullDocument` with `commandResponse`: no caller combines them; a guard adds complexity for an unreachable case. Fourth identical verdict.
- `low` — Command-mode harness answers any path and the explicit-false send does not check the route: the harness exposes no request list, so checking needs new harness surface. `CliMcpCommandParityTests` covers command routing. Fourth identical verdict.

### Post-Bump Cumulative Review Findings

Code review 2026-10-08 of `3260812..2104a5b`, excluding this spec (Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor; no layer failed). Verification Gap found no gaps. Acceptance Auditor found all four acceptance criteria satisfied. During the review, `HEAD` advanced to `342e072` (`fix(references): update subproject commits for Hexalith modules`), outside the reviewed range.

- [x] [Review][Decision] Dependency policy pin is stale again at `HEAD`, and CI on `main` is red — Resolved (option 1): `c6cd224` aligns both pins to 3.117.1 in a separate `build(deps)` commit. After a fresh restore, all six suites pass (1,034 passed, two existing skips). Option 3, pinning `HexalithEventStoreVersion` locally, was rejected: it drifts from the shared Builds catalog and leaves `references/Hexalith.EventStore` ahead of the compiled package. `342e072` moved `references/Hexalith.Builds` from `ba4ca78` to `58d9b54`, whose `Props/Directory.Packages.props:9` defaults `HexalithEventStoreVersion` to 3.117.1. `tools/dependency-policy.json:27-28` still pins Client and Contracts to 3.113.0. CI run 37814775292 (`ci / build-and-test`) failed: `Restored package Hexalith.EventStore.Client/3.117.1 is outside the exact dependency policy` (and Contracts). Local runs still pass on stale 2026-10-05 `obj/project.assets.json` assets. The 3.117.1 nuspecs declare the same dependency closure as 3.113.0, apart from the two packages themselves. The ledger entry `status: resolved by 4d39200` (`deferred-work.md:357`) and this spec's "Resolved" note no longer hold at `HEAD`. Choose: align the policy to 3.117.1 in a separate `build(deps)` commit (precedent `4d39200`), or defer it to the owner of the reference bump and close 2.10 on its own unaffected code.
- [x] [Review][Patch] README claims `--read-only 1` and `--read-only 0` always fail parsing with exit code 1. On verbs whose operation or module argument is omitted, the token is taken as that name and read-only turns on. Verified on the Debug build: `operations --read-only 0`, `describe --read-only 1`, `send --read-only 0 --payload {}` and `query --read-only 0 --payload {}` exit 2, while `config current`, `modules` and `operations routing-fixture` exit 1. Exit 1 for parse failures is also the known defect Story 2.11 owns (`deferred-work.md:188`). State that the flag does not accept `1`/`0` and to use `true`/`false`, without promising an exit code [README.md:73]

Rejected:

- `low` — `QueryCliHarness` ignores `paging`/`nullDocument` with `commandResponse` (Edge Case Hunter): no caller combines them, and a guard adds complexity for an unreachable case. Fifth identical verdict.
- `low` — No automated test for the flag grammar (`True`, `FALSE`, `=false`, numeric values) (Blind Hunter): this is System.CommandLine's bool parsing at the pinned 2.0.12, unchanged by this story. The README patch drops the exit-code promise, and the new tests would cover framework behavior only.
- `false` — MCP environment activation is untested (Blind Hunter): `McpCliMcpServiceCollectionExtensions.cs:35` and `:84` read only the resolved `settings.ReadOnly`, never its source. The shared resolver's environment path is proven by `SendRefusesBeforeReadingInputAsync` and `EnvironmentPreservesDiscoveryAsync`, and `mcp --read-only` covers the MCP filter.
- `low` — The `read_only` message does not name its source or the override (Blind Hunter): the message is the Story 2.9 stable error document (`OperationExecutor.cs:82`, shared by CLI and MCP). README names both activation sources and the `--read-only false` override, and changing the message alters a pinned contract.
- `false` — README does not say read-only cannot live in a profile (Blind Hunter): README names exactly two activation sources, and `config set` accepts only `tenant`, `actor`, `allowTenantOverride` and `allowedExtensions` (`CliRunner.cs:417`), so an attempt to store it fails loudly instead of misleading.
- `low` — `switch (source)` and `invalidField` have no throwing default (Blind Hunter): every row's spelling matches, the data sit in the same file or attribute right beside the test, and the guard adds code that only protects against a future typo.
- `false` — `InvokeAsync` lacks `<param>` docs (Blind Hunter): the harness's methods carry summaries only, and the pre-existing `withUrl` had none. Only the constructor gained `<param>` tags, by an earlier review patch. The build is warning-free, and the parameter names describe themselves.

### Post-Sync Cumulative Review Findings

Code review 2026-10-08 of `3260812..d2fc528`, excluding this spec (Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor; no layer failed). Verification Gap found no gaps. Acceptance Auditor found all four acceptance criteria satisfied and reran `ReadOnlyCommandTests` (32 passed) and the Core read-only cases (14 passed). `8247a2d` moves `references/Hexalith.Builds` to `fef0318`, which changes nothing under `Props/` from `58d9b54` and keeps `HexalithEventStoreVersion` at 3.117.1, so the policy pin from `c6cd224` still holds.

- [x] [Review][Patch] README says ordinary `send` returns `invalid_arguments` for "missing or unreadable payloads", but only omitted payloads and `@file` read failures do. `ReadPayloadAsync` catches file I/O exceptions only (`CliRunner.cs:571-578`); a stdin read that throws reaches `RunAsync`'s catch-all and returns `internal_error`. Say "missing payloads or unreadable payload files" (Acceptance Auditor + Verification Gap) [README.md:71]
- [x] [Review][Patch] README never says how to confirm the mode is active. `config current` reports `readOnly` and its origin in `sources.readOnly` (`flag`, `EVENTSTORE_READ_ONLY`, or `default`), as `ConfigCommandTests` asserts; add one sentence to the read-only paragraph (Blind Hunter) [README.md:73]
- [x] [Review][Patch] `ReadOnlyCommandFailsBeforeEnvelopeValidationAsync` asserts only `Code`, while its sibling pins the full `OperationError("read_only", Message: ...)` record; an envelope-specific refusal that gained violations, `operation`, or a different message would still pass. Use the same full-record assertion (Blind Hunter) [tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs:199]

Rejected:

- Fix edits this spec — The eight `references/` pointer moves (`342e072`, `8247a2d`) are not all recorded in this spec or the ledger (Acceptance Auditor; Blind Hunter's "no stated purpose"). They are owner commits outside the story; only the Builds move affects the build, and it changes no package version.
- `false` — Stdin comment wrong for the omitted payload (Verification Gap): the comment is conditional and detects a regression that falls back to stdin for an omitted payload. Fourth identical verdict.
- `low` — `QueryCliHarness` ignores `paging`/`nullDocument` with `commandResponse` (Edge Case Hunter): no caller combines them, and a guard adds complexity for an unreachable case. Sixth identical verdict.
- `false` — Ledger rule "align the policy in the same commit" contradicts the separate `build(deps)` commit (Blind Hunter): the separate commit remediated a bump that had already landed; the rule prevents recurrence. `8247a2d` changed no package version, so it had nothing to align. Moving the rule into `AGENTS.md` was rejected four times: CI's blocking Manifest suite enforces it.
- `low` — Boolean flag and environment rules are documented for read-only only, though `--strict` and `--allow-tenant-override` share them (Blind Hunter): pre-existing Story 2.1/2.2 documentation gap, partly tracked (`deferred-work.md:225`); `--strict 0` is unlikely in everyday use, and restating all three settings is a README restructure. "An earlier configuration error, such as…" is explicitly non-exhaustive, so the invalid `EVENTSTORE_ALLOW_TENANT_OVERRIDE` case is covered.
- `low` — Flag accepts case-insensitive `true`/`false` while `EVENTSTORE_READ_ONLY` accepts exactly `true`/`false`/`1`/`0`, so PowerShell `$true` (`True`) fails every verb (Blind Hunter): this is the Story 2.1 contract (`SettingsResolver.cs:151-174`, unchanged by this story), and it fails loudly with `EVENTSTORE_READ_ONLY must be true, false, 1, or 0.` Aligning them changes a pinned contract or needs a custom parser.
- `false` — README turns incidental ordering into contract that Story 2.11 will make stale (Blind Hunter): the frozen Approach requires documenting gate precedence, and an earlier review patch added the ordinary-`send` ordering. The sentences promise order, not parser exit codes; Story 2.11's parse-error fix (`deferred-work.md:188`) still fails before settings resolution.
- `false` — README read-only guidance omits MCP (Blind Hunter): README:65 states the tool-list effect, README:103 says "up to five" tools and that diagnostics use stderr, and README:73 names MCP stdio startup's `configuration_invalid`. MCP host configuration belongs to Epic 3 (Story 3.2).
- `low` — The help-text deferral has no owner and no links to the two other help-gap entries (Blind Hunter): those entries (`deferred-work.md:225`, `:325`) also have no owner, and grouping related ledger entries is the sweep's job. Assigning an owner is a planning decision, not a review correction.
- `low` — `references/Hexalith.EventStore` sits at `v3.117.1-8-g07d1e23`, past the pinned package (Blind Hunter): the drift touches only Client `Aggregates`/`Events`/`Streams` and Contracts `Security`/`Streams`. `Gateway`, `Commands`, and `Queries`, which this repository reads, are identical to the tag. Re-pinning a reference is a dependency change outside this story.
- `low` — Conventional Commit types `fix(references)`, `fix(dependencies)`, and `fix(status)` add patch-level release-note noise (Blind Hunter): each `fix(status)` commit does set `in-progress`, so its message is accurate, and the types pass commitlint. Correcting them means rewriting published `main` history.

### Post-Fix Cumulative Review Findings

Code review 2026-10-08 of `3260812..1b1012d`, excluding this spec (Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor; no layer failed). Verification Gap found no gaps. Acceptance Auditor found all four acceptance criteria satisfied and reran `ReadOnlyCommandTests` (32 passed) and the Core read-only cases (14 passed).

- [x] [Review][Patch] README's list of exits that precede `EVENTSTORE_READ_ONLY` validation now names MCP `--transport`, `--format`, and `--output` errors (`CliRunner.cs:449-468`) [README.md:73]
- [x] [Review][Patch] `SendPreservesLookupAndKindErrorsAsync` and `EnvironmentPreservesDiscoveryAsync` now assert stderr diagnostics for all invocations [tests/Hexalith.McpCli.Cli.Tests/ReadOnlyCommandTests.cs:74, :118]

Rejected:

- `false` — README does not say read-only is not a security boundary (Blind Hunter): README:71 states that an explicit `--read-only false` overrides the environment setting, so no reader can take the variable for a lock. The story frames the mode as preventing accidental business-state changes (`epics.md:878`), not as access control.
- `false` — README does not scope read-only, and `config` verbs and `--output` still write local files (Blind Hunter): README:65 and :71 scope the mode to CLI `send` and MCP command registration, as FR19 does. `config` verbs change only the local profile file, never business state, and each later invocation applies its own flag or environment.
- `false` — No test calls `send_command` on a read-only MCP server (Blind Hunter): `McpCliMcpServiceCollectionExtensions.cs:35` never registers the tool in read-only mode, so no call can reach the executor or the Gateway. The PRD validation split this into "the MCP head does not register `send_command`" and "the executor called directly returns `read_only`" (`validation-report.md:126`), and Story 3.1 (backlog) owns the read-only tool surface. This story changes no MCP code.
- `low` — Ordinary `send` `invalid_arguments` precedence appears only in the read-only paragraph (Blind Hunter): the omitted-payload error explains itself, README:93 lists `invalid_arguments`, and an earlier review patch deliberately placed the contrast here. Moving it into the Commands section is a README restructure.
- `false` — `ExplicitFalseOverridesEnvironmentAsync` cannot prove JSON parsing ran, because a `/tenant` or `/actor` violation also yields `validation_failed` (Blind Hunter): the test proves the override. If the override failed, availability would return `read_only` before any validation (`OperationExecutor.cs:78-83`). `ExplicitFalseAllowsCommandSubmissionAsync` proves a full submission.
- `false` — The unknown-operation row does not pin `suggestions` (Blind Hunter, the second half of the stderr finding): the executor delegates unknown names to the shared `CatalogService.Describe` (`OperationExecutor.cs:59-62`), whose suggestions `DiscoveryCommandTests` pins (`:223-224`). The read-only branch cannot change them.
- `low` — Refusing before reading stdin can send SIGPIPE to a large piped payload's producer (Blind Hunter): this is the frozen Approach's required order, and README:71 already says refusal happens before reading stdin. The pipeline still reports exit 2, and draining stdin would add a branch that contradicts the intent.
- `low` — The explicit-false send asserts only output fields and one request, not route or envelope (Edge Case Hunter): `CliMcpCommandParityTests` covers command routing and the envelope. Checking them here needs new harness surface. Fifth identical verdict.
- `low` — `QueryCliHarness` ignores `paging`/`nullDocument` with `commandResponse` (Edge Case Hunter): no caller combines them, and a guard adds complexity for an unreachable case. Seventh identical verdict.
- `false` — `AssertRequest` hard-codes `/api/v1/queries` (Edge Case Hunter): no command test calls it, and calling it on a command request fails loudly on the path, so no test can pass wrongly.

### Post-Diagnostics Cumulative Review Findings

Code review 2026-10-09 of `3260812..ecf8952`, excluding this spec (Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor; no layer failed). Verification Gap found no gaps. Acceptance Auditor found all four acceptance criteria satisfied and reran `ReadOnlyCommandTests` (32 passed) and the Core read-only cases (14 passed).

- [ ] [Review][Patch] Ledger evidence labels `de67938` as Story 2.1, but that commit precedes Story 2.1's `baseline_commit` `e599f5c`; drop "(Story 2.1)" (Blind Hunter) [_bmad-output/implementation-artifacts/deferred-work.md:364]
- [ ] [Review][Patch] Six exit-code assertions omit the `output + error` message used at :162, so a failing row reports only the exit value, not the error document naming the gate that fired (Blind Hunter) [tests/Hexalith.McpCli.Cli.Tests/ReadOnlyCommandTests.cs:58, :81, :106, :124, :134, :180]

Rejected:

- `false` — Read-only and ordinary `send` return different codes for the same bad input, and Story 2.11 has no ledger entry (Blind Hunter): the frozen Approach requires lookup and kind checks before the read-only gate, and the gate before input acquisition. README:71 documents both orders, the exit code is 2 either way, and Story 2.11's criteria (`epics.md:904`) fix output channels and exit codes, not cross-mode error codes. The Cumulative review settled the addendum §G question.
- `false` — README omits `--read-only=0` (Blind Hunter): README:73 says the flag does not accept `1` or `0` and to use `true` or `false`, whichever syntax is used; `operations --read-only 0` is an example.
- `low` — A read-only MCP server drops `send_command` without a stderr diagnostic (Blind Hunter): pre-existing, since this story changes no MCP code. Story 3.1 (backlog) owns the read-only tool surface and Story 3.2 owns startup logging; a startup line adds a branch for an uncommon inherited-environment case, and `config current` already reports the source.
- `low` — No test places `--read-only` before the verb (Blind Hunter): all ten global options share `Recursive = true` (`GlobalOptionsBinding.cs:10-19`), and no CLI test places any of them before the verb. The placement works today; the gap is CLI-wide and pre-existing, and the fix is a new test rather than a correction.
- `low` — `QueryCliHarness` ignores `paging`/`nullDocument` with `commandResponse` (Edge Case Hunter): no caller combines them, and a guard adds complexity for an unreachable case. Eighth identical verdict.
- `low` — `AssertRequest` hard-codes the query route, and the explicit-false send checks only the call count (Edge Case Hunter): `CliMcpCommandParityTests` covers command routing and the envelope; checking them here needs new harness surface. Sixth identical verdict.
- `false` — Cumulative `git diff --check` flags `tools/dependency-policy.json:27-28` (Acceptance Auditor): all 74 lines were CRLF at `3260812`, the changed lines keep those endings, and `.gitattributes` sets CRLF only for `*.cs`. There is no trailing whitespace.
- `false` — AC1 is proven only through the harness, because the shipped CLI returns `catalog_empty` (Acceptance Auditor): no production Contracts are enrolled yet (README:44), and README:71 qualifies refusal with "after settings resolution and catalog access succeed".
- `false` — The range includes the dependency-policy and `references/` moves (Acceptance Auditor): the policy bumps are the approved Decisions landed as separate `build(deps)` commits `4d39200` and `c6cd224`, and the pointer moves are owner commits `342e072` and `8247a2d`.
- Fix edits this spec — Spec `status: done` versus sprint `review` (Acceptance Auditor): this review's completion sets both.

## Verification Blocker

Resolved 2026-10-05 by `4d39200` (`build(deps): align EventStore dependency policy with 3.113.0`, commitlint 0 problems). `dotnet tests/Hexalith.McpCli.Manifest.Tests/bin/Debug/net10.0/Hexalith.McpCli.Manifest.Tests.dll` passes 8/8 after a zero-warning Debug build. The history below is kept for reference.

Recurred 2026-10-08 after `342e072` moved the Builds default to 3.117.1, failing CI run 37814775292. Resolved by `c6cd224` (`build(deps): align EventStore dependency policy with 3.117.1`, pinned commitlint 21.2.2: 0 problems, 0 warnings). A fresh `dotnet restore Hexalith.McpCli.slnx` selected 3.117.1. All six Debug test-project builds had zero warnings and errors. The suites passed Manifest 8, Abstractions 20, Analyzers 19, MCP 6, Core 557 (two existing Windows-only skips) and CLI 424.

Resumption command: `dotnet tests/Hexalith.McpCli.Manifest.Tests/bin/Debug/net10.0/Hexalith.McpCli.Manifest.Tests.dll -result-xml /tmp/mcpcli-2-10-resume-Manifest.xml` (stdout/stderr captured in `/tmp/mcpcli-2-10-resume-Manifest-tests.log`) exited 1. `DependencyPolicyTests.ProductionContractsStayWithinPinnedDependencyClosure` reports:

```text
Restored package Hexalith.EventStore.Client/3.113.0 is outside the exact dependency policy
Restored package Hexalith.EventStore.Contracts/3.113.0 is outside the exact dependency policy
```

`tools/dependency-policy.json` pins both to 3.110.0, while the current root-declared Builds checkout and refreshed restore assets select 3.113.0. The full Manifest suite passes seven tests and fails this one; a focused rerun with `-class Hexalith.McpCli.Manifest.Tests.DependencyPolicyTests -result-xml /tmp/mcpcli-2-10-resume-DependencyPolicy.xml` also exited 1 (one passed, one failed). No tracked dependency, build configuration, policy, or submodule files changed during this story. Reconciling the existing policy is separately deferred; restore used existing pins without package updates, policy weakening, or submodule updates. All five other complete suites passed as recorded above.
