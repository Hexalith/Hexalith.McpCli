---
title: 'Add and Select a Private Profile'
type: 'feature'
created: '2026-09-29'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'd2501c8d00b336290e15e141ea4d014c856d2c94'
context:
  - '_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `config profile add|list`, `config use [--clear]`, and `config current` exist, but profile-management verbs first resolve the full session. So a missing `EVENTSTORE_PROFILE`/`--profile` blocks the verb that would create it, `list` renders a second snapshot, a malformed JSON target surfaces as `internal_error`, and `add` stores `format: json` when none was given. CLI-level secrecy, no-mutation, and isolation coverage is thin.

**Approach:** Profile-management verbs resolve only presentation settings, never a profile, and each reads or mutates the store exactly once through `ProfileStore`. Malformed targets map to `configuration_invalid`, and `add` stores only supplied fields. Pin every acceptance criterion with CLI-level tests.

## Boundaries & Constraints

**Always:** Persist only in `mcpcli.json` (version 1). Names match `^[a-zA-Z0-9_-]{1,64}$`. Invalid name, URL, token, format, or missing `use` target → `configuration_invalid`, exit 2, target bytes unchanged. A missing required argument (`name`, `--url`, neither name nor `--clear`) stays `invalid_arguments`. Every mutation uses the existing lock → reload/validate → private temp write+flush → atomic replace transaction. Tokens appear only masked (`ProfileStore.MaskToken`) in every document, error, and log.

**Never:** Open the admin `profiles.json` or read `EVENTSTORE_ADMIN_*`. Follow or overwrite a symlinked target or lock. Overwrite a malformed or unsupported-version target. Change `config current` resolution or output shape, `config set`/`remove` semantics beyond sharing the new bootstrap mode, execution, MCP, dependencies, or `references/`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| First add | no file; `add dev --url U --token T` | version-1 file with `dev` {url, token}; no null or defaulted `format`; output has no raw token; sibling `profiles.json` bytes unchanged | N/A |
| Add under missing selection | `EVENTSTORE_PROFILE=staging` (absent); `add staging --url U` | succeeds; profile created | N/A |
| List/use/clear | two profiles with tokens | `list` sorted, masked tokens; `use dev` → activeProfile dev; `use --clear` → null | N/A |
| Invalid input | bad name, `--url ftp://x`, `--format xml`, `--token " "`, `use missing` | exit 2 `configuration_invalid`; file unchanged or absent | message never contains the supplied token |
| Hostile target | symlink target or lock; malformed JSON; `version: 2`; unknown field | exit 2 `configuration_invalid`; symlink not followed; target bytes unchanged | N/A |
| Stale temp | leftover `mcpcli.json.tmp-*` | ignored; add succeeds | N/A |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Core/Settings/ProfileStore.cs` -- `Read` lets `JsonException` escape (unknown field, duplicate key, bad syntax); `Add` validation is otherwise complete. Reuse `ValidateName`/`ValidateProfile`/`MaskToken`; `JsonOptions` writes explicit nulls.
- `src/Hexalith.McpCli.Core/Settings/ProfileFileTransaction.cs` -- lock/temp/replace/permission transaction already meets AD-14; leave unchanged unless a test proves a gap.
- `src/Hexalith.McpCli.Core/Settings/SettingsResolver.cs` -- full resolver, including the profile-selection failure at ~line 62. Do not change its `config current` behavior.
- `src/Hexalith.McpCli/Hosting/SettingsBootstrap.cs`, `HostFactory.cs` -- composition boundary; add the presentation-only mode here, never in the head.
- `src/Hexalith.McpCli/Cli/CliRunner.cs` -- `CreateConfigProfile`, `CreateConfigUse`, `CreateConfigSet` call `RunAsync`, which does full resolution. `add` uses `input.Format ?? "json"` (~line 322) and treats blank names as `invalid_arguments`.
- `tests/Hexalith.McpCli.Core.Tests/ProfileStoreTests.cs` -- existing round-trip, concurrency, stale-temp, and symlink tests; extend them.
- `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs` -- `InvokeAsync` harness with an injected environment; extend it.
- Pattern reference only: `references/Hexalith.EventStore/src/Hexalith.EventStore.Admin.Cli/Commands/Config/ProfileAddCommand.cs` stores a null format when omitted.

## Tasks & Acceptance

**Execution:**
- [x] `src/Hexalith.McpCli.Core/Settings/ProfileStore.cs` -- wrap `JsonException` from parse/deserialize in `InvalidDataException` with a fixed message (no inner text); write with `DefaultIgnoreCondition = WhenWritingNull` -- malformed targets become `configuration_invalid` and the stored shape matches AD-14.
- [x] `src/Hexalith.McpCli/Hosting/SettingsBootstrap.cs`, `HostFactory.cs` -- add a presentation-only mode that ignores `--profile`/`EVENTSTORE_PROFILE` and resolves against an empty snapshot without touching the store -- management verbs cannot be blocked by the selection they repair.
- [x] `src/Hexalith.McpCli/Cli/CliRunner.cs` -- route profile `list|add|remove`, `use`, and `set` through that mode. `list` reads once inside the action. `add` stores only the supplied url/token/format and maps a supplied-but-invalid name to the store's `configuration_invalid`.
- [x] `tests/Hexalith.McpCli.Core.Tests/ProfileStoreTests.cs` -- add malformed-JSON, unknown-field, and version-2 targets: `Add`/`Use` throw `InvalidDataException` and the bytes are unchanged. Assert the null-omitting written shape.
- [x] `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs` -- cover every matrix row through the parser. Assert the exit code, error code, and unchanged bytes; the absence of the raw token in stdout and stderr; and an untouched sibling `profiles.json`.

**Acceptance Criteria:**
- Given any profile-management verb, when it runs, then it never fails because of the selected profile, and it reads or mutates the store exactly once.
- Given any profile command output, error, or log, when a token exists anywhere in the flags or the file, then only its masked form is observable.

## Design Notes

Presentation-only mode: management verbs render with format flag → `EVENTSTORE_FORMAT` → `json`, and `--output` from its flag. The active profile's `format` no longer styles `list`/`use`/`add` output. This removes the second-snapshot race and the self-blocking selection, and environment values are still validated. A missing `name` stays `invalid_arguments`, because an absent argument is a usage error rather than a bad configuration value.

## Verification

**Commands:**
- `dotnet build Hexalith.McpCli.slnx --configuration Release` -- expected: 0 warnings, 0 errors.
- `dotnet test tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Release --no-build` -- expected: all pass.
- `dotnet test tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Release --no-build` -- expected: all pass.

## Implementation Notes

- `SettingsBootstrap.ResolvePresentation` uses `SettingsResolver`'s internal snapshot-reader constructor (Core grants `InternalsVisibleTo` to `Hexalith.McpCli`) with a fixed empty snapshot; `config current` behavior is unchanged.
- `CliRunner.Parse` disables System.CommandLine response-file expansion, so `@`-prefixed values (tokens, `--payload @file`) reach their options verbatim and are never echoed in parser errors.
- `HostFactory.Create` takes `presentationOnly`; `CliRunner.RunManagementAsync` routes profile `list|add|remove`, `use`, and `set` through it. `remove` and `set` keep their existing argument checks.
- `add` treats only an absent name as `invalid_arguments`; a supplied empty or invalid name reaches `ProfileStore.ValidateName` and becomes `configuration_invalid`.
- `ProfileStore` now omits null members when writing, so a cleared `activeProfile` is absent from the file rather than `null`.

## Spec Change Log

## Review Triage Log

| Reviewer | Finding | Verdict | Evidence / route |
|---|---|---|---|
| blind-hunter | Legacy profiles storing `format: json` override `EVENTSTORE_FORMAT` for execution verbs. | false | `SettingsResolver.Select` orders flag → environment → profile, so `EVENTSTORE_FORMAT` always beats a stored profile format. |
| blind-hunter | `add ""` fails as `configuration_invalid` while `remove ""`/`set ""` fail as `invalid_arguments`. | low | Real inconsistency, but the frozen intent forbids changing `set`/`remove` semantics beyond the bootstrap mode. Deferred to Story 2.3. |
| blind-hunter | The exactly-once acceptance criterion is untested, and `remove` is missing from the missing-selection test. | medium | Same root as the verification-gap finding: the management-mode routing of `set`/`remove` is unpinned. Patched there. |
| blind-hunter | Unrelated invalid environment values still block management verbs. | low | Real, but Design Notes deliberately keep environment validation, and the only fix edits this spec. Rejected. |
| blind-hunter | A failed `use missing` creates the directory, the lock file, and 0700 mode before throwing. | low | Pre-existing transaction behavior; the profile file is never created and a stray lock file is harmless. Rejected as unlikely harm. |
| blind-hunter | Windows symlink cases return early and report green. | low | Confirmed; replacing the early return with `Assert.SkipWhen` is a direct correction. Patched. |
| blind-hunter | README does not say management verbs ignore `--profile`/`EVENTSTORE_PROFILE` and profile format. | low | Confirmed at `README.md` global-options paragraph; a one-sentence doc correction. Patched. |
| blind-hunter | Core's `SettingsResolver(Func<ProfileSnapshot>, …)` was made public for one internal caller. | medium | Confirmed: it adds permanent public API to the Core package. Patched: restore `internal` plus `InternalsVisibleTo` for the head. |
| blind-hunter | `Parse` parses twice and wraps only `JsonException`. | low | The double parse predates this change, and no reachable non-`JsonException` deserializer failure was shown. Rejected. |
| blind-hunter | Management verbs build a full host holding the token. | false | AD-13 requires every verb to run inside one Host; no Catalog or Gateway is activated by these verbs. |
| blind-hunter | Spec `in-review` versus sprint `in-progress` with no recorded evidence. | false | The workflow syncs the terminal sprint status after review; verification evidence is recorded at completion. |
| blind-hunter | Table-format and `EVENTSTORE_FORMAT` assertions are shallow. | low | No defect demonstrated in the shared, pre-existing table renderer; tokens are masked before rendering. Rejected. |
| edge-case-hunter | `add` silently drops `--tenant`/`--actor`/`--allow-tenant-override`. | low | Real, but pre-existing: AD-14 limits `add` to url/token/format, and the baseline dropped them too. Deferred. |
| edge-case-hunter | Re-adding an existing profile erases fields set with `config set`. | false | AD-14 specifies that `add` replaces the named profile. Intended behavior. |
| edge-case-hunter | Public resolver constructor given a null-returning delegate throws NRE. | low | Same root as the public-constructor finding; restoring `internal` removes external callers. Patched there. |
| edge-case-hunter | `--token @secret` echoes the token via response-file expansion. | high | Reproduced: the Release build printed `Response file not found 's3cretTok'.` and exited 1, violating the frozen secrecy rule. Patched: disable response-file expansion at the single parse entry point. |
| verification-gap | `set` and `remove` routing through presentation mode is unpinned. | medium | Pre-verified: reverting either to `RunAsync` keeps every test green. Patched by running every management verb under a never-existing selection. |
