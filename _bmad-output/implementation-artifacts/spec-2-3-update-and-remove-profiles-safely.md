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

### Review Findings

Second-pass code review (2026-09-29) of `6fe785e..0668bf6`, run as four layers: blind-hunter, edge-case-hunter, verification-gap and acceptance-auditor.

- [x] [Review][Patch] The concurrency test never shows that either child blocked on the held lock. A `set` that skipped the lock would still pass if both children finished inside the 2 s window. Fix: assert that both child tasks are still incomplete just before the lock is released. [tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs:1564]
- [x] [Review][Patch] The Windows ledger entries understate the gap. `ConcurrentSetProcessesPreserveBothValuesAsync` and `VerbsNeverOpenAdminProfilesAsync` also skip on Windows, so a `windows-latest` job alone would still not exercise them; it also needs a home override that Windows honors. The pre-existing read-only `CurrentExecutableReadsProcessEnvironmentAsync` also reads the developer's real profile on Windows, and the entry does not name it. [_bmad-output/implementation-artifacts/deferred-work.md:181]
- [x] [Review][Defer] No run has executed the Windows ACL tests: the CI runs only on `ubuntu-latest` and both tests skip there. [tests/Hexalith.McpCli.Core.Tests/ProfileStoreTests.cs:928] — deferred: already tracked by this story's Windows CI entry in `deferred-work.md`; needs shared CI infrastructure.
- [x] [Review][Defer] System.CommandLine parse errors break AC 1: help goes to stdout, the unmatched token is echoed on stderr, and the exit code is 1. This also covers `config profile add dev --url U --tenant` with no value, which never reaches `RejectOperatorFlags`. [src/Hexalith.McpCli/Cli/CliRunner.cs:310] — deferred: pre-existing default ParseErrorAction, owned by Story 2.11; the `add --tenant` (no value) case is added to that entry.

**Rejected**

- `false`: Operator flags are named by fixed priority, not command-line order. Decision (1) itself says "names the first offending flag in that order".
- `false`: A supplied secret could leak through a `set` failure. Every `ProfileStore` failure message is a constant string, and the CLI rows that pass `--token SuppliedToken` assert the token is absent from both streams.
- `false`: `add` replaces a profile silently, with no `replaced` flag. The frozen Boundaries define `add` as a whole-record replace, and adding the flag would mean new output surface.
- `false`: The probe converter's serializer options have drifted from the store's. The settings that affect writing (Web defaults plus `WhenWritingNull`) are identical; the two that differ only apply when reading.
- `low`: The admin-isolation test can't catch a read guarded by `File.Exists`, and it runs only `config` verbs. No `src` reference to `profiles.json` or `EVENTSTORE_ADMIN_*` exists, and closing the gap needs a new platform-specific test variant.
- `low`: The operator-flag check runs before the missing-name and missing-URL checks. This is a rare input, and moving the check behind settings resolution changes how `--tenant " "` is reported.
- `low`: `set`, `remove` and `use` still ignore explicit operator flags. This is pre-existing, and Decision (1) limits the refusal to `add`; the fix would add branches to every verb.
- `low`: A failed `set` or `remove` on a clean machine creates `~/.eventstore/` and `mcpcli.json.lock`. This is pre-existing: `Apply` creates both before `update` throws, the target bytes are unchanged, and the input is rare. The fix would change the transaction, which requires a failing test first.
- `low`: `RunExecutableAsync` has no timeout and never kills the child process. Lock acquisition gives up after 10 s, and adding cancellation and a process-tree kill is more than a direct correction.
- `low`: `config profile add --help` lists the recursive operator flags, and the error text uses a `<profile>` placeholder. The name can still be null when the error is built, and hiding recursive options per subcommand is not a direct fix.
- `low`: A missing `set` argument is reported as `set`, and the new rows pin that. The message is pre-existing, the case is rare, and naming the actual missing positional adds branches.
- Rejected because the fix would edit the spec: the Interrupted row is not tested through the CLI, although the task says every row is. The Implementation Notes already acknowledge this.

Third-pass code review (2026-09-29) of `6fe785e..6f1950a` (`references/`, this spec, and `sprint-status.yaml` excluded), run as four layers: blind-hunter, edge-case-hunter, verification-gap and acceptance-auditor. The verification-gap layer found no gaps. The two open second-pass `[Review][Patch]` items above were confirmed again, still unfixed, by acceptance-auditor, blind-hunter and edge-case-hunter; they stay open and are not duplicated here.

- [x] [Review][Patch] The two ledger entries for the Windows ACL tests describe one item. The entry at l.199 says it "is the same item as the Windows CI entry above", yet it is a separate open entry with its own `source_spec`, so a ledger sweep counts two items and could resolve one while leaving the other. Fix: fold its traceability note into the l.181 entry (while applying the second-pass ledger patch) and delete it. [_bmad-output/implementation-artifacts/deferred-work.md:199]
- [x] [Review][Patch] `SetChangesOnlyTheNamedField` pins the property order of the written `dev` record (`["url","token","tenant","actor"]`). The criterion is which fields are present, so reordering `ConnectionProfile` members would fail the test with no behaviour change. Fix: `ShouldBe([...], ignoreOrder: true)`, as the `Profiles.Keys` checks already do. [tests/Hexalith.McpCli.Core.Tests/ProfileStoreTests.cs:294]
- [x] [Review][Defer] A stored `tenant` or `actor` cannot be cleared: `set dev tenant ""` fails validation, and the only path back is `config profile add`, which replaces the whole record and drops the token, format and allowed extensions. The new `add` error hint points users to `config set` as the only editing path. [src/Hexalith.McpCli.Core/Settings/ProfileStore.cs:152] — deferred: by design for v1 (frozen Never: no field-unset verb); no owner recorded yet.

**Rejected (third pass)**

- `false`: A secret typed as a positional `set` value (`set dev token X`) could be echoed. `ProfileStore.Set` rejects the field before any read, with a constant message that holds neither the field value nor the stored token. `InvalidSetFailsWithoutChangingBytes` needs no value-absence assertion for the same reason.
- `false`: `add` silently drops `--read-only`, `--strict` and `--profile`. Decision (1) says "Other global options are unaffected."
- `false`: The admin-isolation environment is vacuous because `EVENTSTORE_ADMIN_*` are not in `SettingsBootstrap.EnvironmentNames`. That is the point of the test: a new read of those names would get `not-a-url` or `yaml` and fail, or leak `admin-secret-value`.
- `low`: The admin-isolation test would not catch an `EVENTSTORE_ADMIN_TOKEN` fallback stored by the token-less second `add`. `add` takes its token only from parsed flags, so such a regression is hypothetical.
- `low`: The concurrency test never checks that stderr is empty. Exit 0 and the secret checks already cover the contract. The blocked-children assertion is the open second-pass patch.
- `low`: A failed `set` or `remove` on a clean machine leaves `.eventstore/` and the lock file, and the ledger does not record it. The second pass already rejected this: it is pre-existing and the transaction is unchanged.
- `low`: The Story 2.11 criteria do not name "no unmatched token echoed on stderr" or `add --tenant` with no value. Its "missing required CLI argument … exit 2, no partial result" criterion covers the contract, and both ledger entries carry the cases to 2.11's tests.
- `low`: The probe converter rebuilds the store's serializer options instead of reusing them. The settings are identical today, and reusing them would expose `ProfileStore.JsonOptions`, which is new internal surface on a class this story leaves unchanged.
- `low`: An invalid `EVENTSTORE_ALLOW_TENANT_OVERRIDE` (for example `yes`) fails `add` even though `add` ignores that setting. This is pre-existing and shared by every management verb through `ResolvePresentation`, and the epic requires environment booleans to be validated.
- `low`: If `Task.Delay` is cancelled inside the concurrency test's `using` block, the children are orphaned, and `RunExecutableAsync` never kills a hung child. The second pass rejected the same point: it needs cancellation plumbing and a process-tree kill.
- `low`: Commit `0668bf6` says it pins Windows ACLs, but those tests have never run. Fixing that means rewriting history, and the ledger already records the gap.

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
- Second- and third-pass review patches (2026-09-29): the concurrency test asserts both child `set` tasks are still incomplete just before the held lock is released (red check: holding a lock on a different path fails with "`set dev tenant a` finished while the transaction lock was held."; three green reruns); `SetChangesOnlyTheNamedField` compares written property names with `ignoreOrder: true`; the Windows ledger entry in `deferred-work.md` now names the two Windows-skipped process tests, the need for a Windows-honored home override, and the pre-existing `CurrentExecutableReadsProcessEnvironmentAsync`, and absorbs the duplicate "no run has executed the Windows ACL tests" entry, which is deleted.
- Verification evidence after review patches (2026-09-29, Linux): `dotnet build Hexalith.McpCli.slnx --configuration Release` → 0 warnings, 0 errors; Core.Tests → 240 total, 238 passed, 2 skipped; Cli.Tests → 141 total, 141 passed; `dotnet test Hexalith.McpCli.slnx --configuration Release --no-build` → 434 total, 0 failed, 2 skipped (the two Windows ACL tests).
- Fourth-pass review (2026-09-29): verification-gap found no gaps; one patch added the whitespace-only field row (`set dev " " x`) to the CLI and Core invalid-set tests. Evidence: `dotnet build Hexalith.McpCli.slnx --configuration Release` → 0 warnings, 0 errors; Core.Tests → 241 total, 239 passed, 2 skipped (Windows ACL); Cli.Tests → 143 total, 143 passed.

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
| verification-gap (fourth pass) | No verification gaps found. | — | No finding to route. |
| blind-hunter (fourth pass) | A failed `set` could echo a supplied positional secret (`set dev token X`); tests assert only the stored token's absence. | false | carried: third-pass Rejected row; `ProfileStore.Set` rejects the field with a constant message before any read, and it is unchanged. |
| blind-hunter + edge-case-hunter (fourth pass) | The 2 s hold in the concurrency test proves nothing if child `dotnet` startup exceeds 2 s: both tasks stay incomplete even without locking. | low | Real on a slow runner, but local red check (lock on another path) failed within 2 s, so the check discriminates in normal runs; a readiness signal or warm-up timing adds new test machinery. Rejected. |
| blind-hunter + edge-case-hunter (fourth pass) | `RunExecutableAsync` has no timeout and never kills a hung child. | low | carried: second-pass and triage-log rows; rejected. |
| edge-case-hunter (fourth pass) | A failing `IsCompleted` assertion inside the lock's `using` block orphans the children while `finally` deletes the directory, which can raise an `IOException` that masks the assertion. | low | Real, but only when the test is already failing on a lock regression; still a red test. Awaiting the children in a new `try`/`finally` adds a guard. Rejected. |
| blind-hunter (fourth pass) | Pre-existing process tests keep inline process setup and no Windows skip; the destructive Windows case should be fixed now. | medium | carried: triage-log row "On Windows the new process tests ignore USERPROFILE"; already deferred in `deferred-work.md`. |
| blind-hunter + edge-case-hunter (fourth pass) | A `profiles.json` directory does not catch a `File.Exists`-guarded admin read. | low | carried: triage-log row; rejected. |
| blind-hunter (fourth pass) | `add` operator-flag refusal precedes name, URL, and settings errors, with untested precedence. | low | carried: triage-log row; rejected. |
| blind-hunter (fourth pass) | "First offending flag" means fixed priority, not command-line order. | false | carried: second-pass Rejected row; Decision (1) says "in that order". |
| blind-hunter (fourth pass) | A missing `set` argument reports `set`, not the missing positional. | low | carried: triage-log row; rejected. |
| blind-hunter (fourth pass) | A whitespace-only field name now reaches the store after the guard changed to `is null`, but neither layer tests `set dev " " x`. | low | Confirmed: only `""` is covered; the store rejects `" "` as an unknown field. The fix adds one data row per layer. Patched. |
| blind-hunter (fourth pass) | No Windows test that a mutation tightens a pre-existing permissive ACL; rights are not checked. | low | carried: triage-log row; rejected. |
| blind-hunter (fourth pass) | The probe converter duplicates the store's serializer options. | false | carried: second-pass Rejected row and third-pass `low`; write-affecting settings are identical. |
| blind-hunter (fourth pass) | Interrupted-write test depends on dictionary order and index 2. | low | carried: triage-log row; rejected. |
| blind-hunter (fourth pass) | `add` silently replaces the whole record with no `replaced` flag. | false | carried: second-pass Rejected row; frozen Boundaries define whole-record replace. |
| edge-case-hunter (fourth pass) | `set`, `remove`, and `use` silently ignore explicit operator flags. | low | carried: second-pass Rejected row; rejected. |
| edge-case-hunter (fourth pass) | A failed `set`/`remove` on a clean machine creates `~/.eventstore/` and the lock file. | low | carried: second- and third-pass Rejected rows; rejected. |
| edge-case-hunter (fourth pass) | `existing=false` rows in `InvalidManagementInputs` check only that the target is absent, so the created directory and lock pass as "without a write". | low | Same root cause as the preceding row: the transaction creates both before `update` throws, and tightening the assertion would require a transaction change. The target file is absent as the matrix requires. Rejected. |
| edge-case-hunter (fourth pass) | Child never killed on hang or cancellation during `WaitForExitAsync`. | low | carried: triage-log row; rejected. |
| edge-case-hunter (fourth pass) | Parse errors break AC 1 (help on stdout, token echo, exit 1), including `add dev --url U --tenant`. | medium | carried: second-pass `[Review][Defer]`; already deferred to Story 2.11. |
