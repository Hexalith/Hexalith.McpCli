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

## Review Triage Log

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
- [ ] [Review][Patch] README understates read-only refusal precedence: lookup and kind errors win over missing-payload and extension errors only in read-only mode, and identifier options also go unvalidated [README.md:67]
- [ ] [Review][Patch] README "During read-only settings resolution" is ambiguous; state that the value fails whenever the read-only setting is resolved [README.md:69]
- [x] [Review][Patch] Ledger evidence reports a stale 3.112.0 restore and omits the drift source, the Builds `HexalithEventStoreVersion` default of 3.113.0 [_bmad-output/implementation-artifacts/deferred-work.md:357] — superseded by the decision: the entry now carries `status: resolved by 4d39200` naming the 3.113.0 source
- [x] [Review][Patch] Story 2.10 ledger entry sits under the Story 2.9 pass-2 heading; give it its own `implementation of` heading [_bmad-output/implementation-artifacts/deferred-work.md:353]
- [ ] [Review][Patch] Statements directly follow closing braces, unlike the touched files' convention [tests/Hexalith.McpCli.Cli.Tests/QueryCliHarness.cs:58; ReadOnlyCommandTests.cs:90, :145]

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

## Verification Blocker

Resolved 2026-10-05 by `4d39200` (`build(deps): align EventStore dependency policy with 3.113.0`, commitlint 0 problems). `dotnet tests/Hexalith.McpCli.Manifest.Tests/bin/Debug/net10.0/Hexalith.McpCli.Manifest.Tests.dll` passes 8/8 after a zero-warning Debug build. The history below is kept for reference.

Resumption command: `dotnet tests/Hexalith.McpCli.Manifest.Tests/bin/Debug/net10.0/Hexalith.McpCli.Manifest.Tests.dll -result-xml /tmp/mcpcli-2-10-resume-Manifest.xml` (stdout/stderr captured in `/tmp/mcpcli-2-10-resume-Manifest-tests.log`) exited 1. `DependencyPolicyTests.ProductionContractsStayWithinPinnedDependencyClosure` reports:

```text
Restored package Hexalith.EventStore.Client/3.113.0 is outside the exact dependency policy
Restored package Hexalith.EventStore.Contracts/3.113.0 is outside the exact dependency policy
```

`tools/dependency-policy.json` pins both to 3.110.0, while the current root-declared Builds checkout and refreshed restore assets select 3.113.0. The full Manifest suite passes seven tests and fails this one; a focused rerun with `-class Hexalith.McpCli.Manifest.Tests.DependencyPolicyTests -result-xml /tmp/mcpcli-2-10-resume-DependencyPolicy.xml` also exited 1 (one passed, one failed). No tracked dependency, build configuration, policy, or submodule files changed during this story. Reconciling the existing policy is separately deferred; restore used existing pins without package updates, policy weakening, or submodule updates. All five other complete suites passed as recorded above.
