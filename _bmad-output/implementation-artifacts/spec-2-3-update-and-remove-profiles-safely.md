---
title: 'Update and Remove Profiles Safely'
type: 'feature'
created: '2026-09-29'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '6fe785e063c1d4e76d001c1ec825b41e42b589d7'
context:
  - '_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `config set`, `config profile remove`, and `config profile add` already mutate `mcpcli.json` through the locked transaction. But `set`/`remove` report a supplied blank name, and `set` a blank field, as `invalid_arguments`, while `add`/`use` report them as `configuration_invalid`. `add` silently drops `--tenant`, `--actor`, and `--allow-tenant-override`. Replacement, cross-process concurrency, interrupted writes, temporary-file permissions, Windows ACLs, and admin-path isolation have no evidence.

**Approach:** Treat only an absent argument as `invalid_arguments`, and send every supplied value to `ProfileStore` validation. Pin each Story 2.3 criterion with Core and CLI tests. Change the transaction only if a test exposes a gap.

## Boundaries & Constraints

**Always:** Fields are exactly `tenant`, `actor`, `allowTenantOverride`, and `allowedExtensions` (case-sensitive). `set` changes only the named field. `allowedExtensions` is split on `,` without trimming and stored as a validated list; an empty value stores `[]`. A key that is empty, has surrounding spaces, is invalid, or is a case-insensitive duplicate fails. Unknown fields, invalid values, missing profiles, and supplied-but-invalid names → `configuration_invalid`, exit 2, bytes unchanged. `add` replaces the whole record, keeping other profiles and `activeProfile`. `remove` clears `activeProfile` only when it names the removed profile. Tokens stay masked.

**Decisions:** (1) `add` with an explicit `--tenant`, `--actor`, or `--allow-tenant-override` fails as `invalid_arguments` and writes nothing. The error names the first offending flag in that order and points to `config set`. Other global options are unaffected. (2) Windows ACL tests are written and skipped off Windows. CI is Ubuntu-only, so the missing Windows runner is logged in `deferred-work.md` and never reported as verified.

**Never:** Change the transaction without a failing test, `config current`, the resolver, execution, MCP, dependencies, or `references/`. Open `profiles.json` or read `EVENTSTORE_ADMIN_*`. Add a field-unset verb.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Set one field | `dev` has url, token, tenant; `set dev actor ops` | only `actor` changes | N/A |
| Extensions list | `set dev allowedExtensions task-id,trace-id`; then `""` | `["task-id","trace-id"]`; then `[]` | N/A |
| Invalid set | `set dev colour red`; `set dev allowTenantOverride yes`; `set dev tenant " "`; `set dev allowedExtensions a,A` / `a,` / `a, b`; `set missing tenant x`; `set "" tenant x`; `set dev "" x` | exit 2 `configuration_invalid`; bytes unchanged | N/A |
| Remove | active `dev`, also `test`: `remove dev`; then `remove test` while `dev` absent and active `test` | `dev` gone, `activeProfile` absent; `test` removal clears only its own selection | `remove missing`/`remove ""` → `configuration_invalid`, bytes unchanged |
| Replace | `dev` with tenant, active `dev`, plus `test`; `add dev --url U2` | `dev` = {url U2} only; `test` and `activeProfile` preserved | N/A |
| Concurrent | two processes: `set dev tenant a` and `set dev actor b` | both values present | N/A |
| Interrupted | serialization fails after partial temp write | target bytes equal the previous file; no temp left | N/A |
| Add with operator flag | `add dev --url U --tenant acme` (or `--actor x`, `--allow-tenant-override`) | exit 2 `invalid_arguments`, argument `tenant`/`actor`/`allowTenantOverride` | file unchanged or absent |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Core/Settings/ProfileStore.cs` -- `Set`/`Remove`/`Add` already hold the required semantics (field switch, `ValidateProfile` duplicate and key checks, active clearing). Reuse them. Expected unchanged.
- `src/Hexalith.McpCli.Core/Settings/ProfileFileTransaction.cs` -- internal `Apply(read, update, JsonSerializerOptions)`. Tests can pass options whose converter observes the `.tmp-*` file mid-write, or throws after a partial write. Core.Tests has `InternalsVisibleTo`.
- `src/Hexalith.McpCli/Cli/CliRunner.cs` -- `remove` (~l.333) and `set` (~l.384) use `IsNullOrWhiteSpace` guards: switch to `is null`. The `add` action (~l.308) reads `_globals.Read(parsed)`; `SettingsInput.Tenant/Actor/AllowTenantOverride` are non-null only when explicit.
- `tests/Hexalith.McpCli.Core.Tests/ProfileStoreTests.cs` -- the Unix-mode assertions at ~l.59 and the concurrent-writer test at ~l.78 are the patterns to extend.
- `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs` -- `InvalidManagementInputs` (~l.1080) and `MissingRequiredArgumentIsInvalidArgumentsAsync` (~l.1147) are the theories to extend. The process harness is `ExecutableStoresAtPrefixedTokenVerbatimAsync` (~l.213): redirect `HOME`/`USERPROFILE` and strip `EVENTSTORE_*`.

## Tasks & Acceptance

**Execution:**
- [x] `src/Hexalith.McpCli/Cli/CliRunner.cs` -- `remove`/`set` return `invalid_arguments` only for null arguments; `add` rejects explicit tenant/actor/allow-tenant-override flags per Decision (1) -- one naming rule across verbs, no silent loss.
- [x] `tests/Hexalith.McpCli.Core.Tests/ProfileStoreTests.cs` -- add tests for the set-only-one-field, replace, and remove matrix rows. Add an interrupted-write test through `Apply` with a throwing converter, and a temp-file mode check (600) through an observing converter. Pre-create a 0755 directory and a 0644 file and assert 700/600 after a mutation. Add Windows-only ACL tests (protected, only the current user and LocalSystem) for the directory, target, lock, and temp files, skipped elsewhere with `Assert.SkipUnless`.
- [x] `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs` -- cover every matrix row through the parser. Add a two-process concurrent `set` test. Add an admin-isolation test in which `profiles.json` is a directory, so any open fails, and every verb still succeeds.

**Acceptance Criteria:**
- Given any failed `set`, `remove`, or `add`, when it exits, then stdout holds only the error document and no raw token appears on either stream.
- Given the full Release test run on Linux, when it completes, then only the Windows-ACL tests are skipped.

## Verification

**Commands:**
- `dotnet build Hexalith.McpCli.slnx --configuration Release` -- expected: 0 warnings, 0 errors.
- `dotnet test tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Release --no-build` -- expected: all pass.
- `dotnet test tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Release --no-build` -- expected: all pass.

## Implementation Notes

- `ProfileStore` and `ProfileFileTransaction` are unchanged: no new test exposed a transaction gap. The interrupted-write test forces a real partial temporary write (a 256 KiB profile makes the resumable dictionary serializer flush before the failing profile) and asserts the temporary file had bytes before the failure.
- The `add` operator-flag check runs before settings resolution, so `--tenant " "` also reports `invalid_arguments` (argument `tenant`) instead of a resolver `configuration_invalid`. An explicit `--allow-tenant-override false` is rejected too, because it is explicit.
- The probe for temporary-file inspection is `tests/Hexalith.McpCli.Core.Tests/ConnectionProfileProbeConverter.cs`; it runs before each profile write inside `ProfileFileTransaction.Apply`.
- The "Interrupted" matrix row has no parser seam, so it is pinned only in Core; the CLI already covers a stale temporary file (`AddIgnoresStaleTemporaryFileAsync`).
- Windows ACL tests (`WindowsProfileFilesHavePrivateAcls`, `WindowsTemporaryFileHasPrivateAclBeforeTokenBytesAreWritten`) compile and skip on Linux; they have not been executed. The missing Windows runner is logged in `deferred-work.md`.
- Red check: against the baseline `CliRunner.cs`, 24 new CLI cases failed (blank `set`/`remove` names and fields, and every operator-flag case); all pass after the change.
- Review patches (2026-09-29): environment-only `add` test; the concurrency test holds `mcpcli.json.lock` while both processes start (a CLI run against a held flock waited ~2.6 s, confirming cross-process blocking); new process tests skip on Windows; `AssertPrivateAcl` accepts a LocalSystem runner.
- Verification evidence (2026-09-29, Linux): `dotnet build Hexalith.McpCli.slnx --configuration Release` → 0 warnings, 0 errors; `dotnet test Hexalith.McpCli.slnx --configuration Release --no-build` → 434 total, 432 passed, 0 failed, 2 skipped (`WindowsProfileFilesHavePrivateAcls`, `WindowsTemporaryFileHasPrivateAclBeforeTokenBytesAreWritten`).

## Spec Change Log

## Review Triage Log

| Reviewer | Finding | Verdict | Evidence / route |
|---|---|---|---|
| verification-gap | No test pins that `add` ignores `EVENTSTORE_TENANT`/`ACTOR`/`ALLOW_TENANT_OVERRIDE`; a refactor to resolved settings would stay green. | medium | Pre-verified: every environment operator test targets `config current`. Patched: environment-only `add` test. |
| blind-hunter | Spec `in-review`, sprint `in-progress`, and Story 2.2 deferrals stamped resolved before review ends. | false | Workflow bookkeeping: the terminal sprint status is synced after review, and both resolved entries are implemented and tested in this diff. |
| blind-hunter | Story 2.1 deferral "management verbs cannot repair the configuration that blocks them" left open; corrupt `mcpcli.json` still blocks mutations. | false | Missing selection was fixed in Story 2.2; a malformed target failing without overwrite is the AD-14 rule and the frozen Never. |
| blind-hunter | New Windows-CI deferral names Story 4.14, which is the live-semantic CI lane in another repo. | low | Confirmed; direct wording correction. Patched: entry now states no story owns it yet. |
| blind-hunter | Other verbs still silently ignore global flags (`set … --tenant b`). | false | Out of scope by frozen Decision (1): "Other global options are unaffected." |
| blind-hunter | `config set` missing-argument error reports `set` instead of `name`/`field`/`value`. | low | Pre-existing message; rarely met and the fix adds branches. Rejected. |
| blind-hunter | `add` operator-flag check precedes name/URL/name-validation errors. | low | Real ordering, but every outcome is a documented usage failure with no write; recorded in Implementation Notes. Rejected. |
| blind-hunter | `add` reads globals twice and passes `ParseResult` to the helper. | false | No named harm: both reads are pure, same input. |
| blind-hunter | Two cold-started processes almost never contend for the lock, so the concurrency test proves little. | medium | Confirmed: the lock is held for milliseconds versus hundreds of ms of startup. Patched: the test holds the lock while both processes start. |
| blind-hunter | `RunExecutableAsync` duplicates older process setup and never kills a hung child. | low | Duplication is cosmetic; the hang also affects pre-existing process tests and needs extra handling. Rejected. |
| blind-hunter | Interrupted-write test covers one failure point and relies on dictionary order. | low | Rename atomicity is an OS guarantee with no seam; insertion order is stable for an unmodified `Dictionary`. Rejected. |
| blind-hunter | Windows ACL assertions: no permissive-preexisting counterpart, no rights/owner check, LocalSystem SID collapse. | low | SID collapse is a one-line fix. Patched. The extra ACL tests would never run on this CI. Rejected. |
| blind-hunter | `allowTenantOverride` success values lack CLI coverage. | low | Parsing is pre-existing and Core-covered; adding a theory is more than a direct correction. Rejected. |
| blind-hunter | Spec records no actual test-run evidence. | false | Fix edits the spec; evidence is recorded at completion (step 5). |
| blind-hunter + edge-case-hunter | A `profiles.json` directory does not catch `File.Exists`-gated reads. | low | True for a gated read, but no src reference to that path exists and Story 2.2 tests pin real sentinel content; the fix adds a platform-specific variant. Rejected. |
| edge-case-hunter | Operator-flag error is written outside `RunAsync`'s try/catch. | false | `WriteErrorAsync` writes only to `Console.Out`; the `RunAsync` catch writes to the same stream, so a broken stdout escapes either way. |
| edge-case-hunter | On Windows the new process tests ignore USERPROFILE and mutate the real profile file. | medium | `GetFolderPath(UserProfile)` uses the known-folder API on Windows. Patched: new process tests skip on Windows; the pre-existing test is deferred. |
| edge-case-hunter | Child process never killed on hang or cancellation. | low | Same as the `RunExecutableAsync` row; rejected. |
| edge-case-hunter | Windows ACL test fails when run as LocalSystem. | low | Grouped with the SID-collapse fix; patched. |
| edge-case-hunter | Parse errors print help on stdout, echo the token on stderr, and exit 1. | medium | Reproduced (`config set dev tenant a b`); pre-existing default ParseErrorAction. Deferred to Story 2.11. |
| edge-case-hunter | Task claims parser coverage of every matrix row, but Interrupted is Core-only. | low | Acknowledged in Implementation Notes; the fix edits the spec or adds a CLI seam. Rejected. |
