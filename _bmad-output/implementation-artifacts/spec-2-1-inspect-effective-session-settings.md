---
title: 'Inspect Effective Session Settings'
type: 'feature'
created: '2026-09-28'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'e599f5c3faa41dbf90bd9219a4a1de47c40f2fd3'
context:
  - '_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Operators cannot yet rely on `hexalith config current` to prove the exact effective session before execution: important precedence, source attribution, boolean-flag, DI ownership, offline, and secret-redaction behaviors are incomplete or weakly tested.

**Approach:** Harden the existing settings model and CLI path so one pre-host resolution selects the profile and every setting deterministically, registers one immutable snapshot, and renders all effective values with their sources without exposing credentials.

## Boundaries & Constraints

**Always:** Select profile by flag, `EVENTSTORE_PROFILE`, then `activeProfile`; select each supported setting by flag, environment, profile, then documented default. Read only `~/.eventstore/mcpcli.json`. Keep URL optional for inspection/version, report invalid configuration through `{ "error": ... }` with exit 2, use one Host and its single `ResolvedSettings` instance per implemented verb, and mask long tokens to four visible prefix characters while fully hiding tokens of four or fewer characters.

**Never:** Read the admin CLI's `profiles.json` or `EVENTSTORE_ADMIN_*`; build the Catalog or contact the Gateway for `config current` or `--version`; log, serialize, or include a raw token in record text; change profile mutation/transaction semantics, execution behavior, MCP transport policy, dependencies, or files under `references/`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Profile precedence | Flag, `EVENTSTORE_PROFILE`, and active profile differ | Flag wins, then environment, then active profile; selected profile source is shown | Missing selected profile returns `configuration_invalid` |
| Setting precedence | All supported sources exist | Each effective value comes from its highest supported source; flat current document includes every setting, including output, plus source attribution | Invalid URL, format, blank text, allowlist, or boolean names its source |
| Boolean settings | Bare flags or environment `true`, `false`, `1`, `0` | Bare flags resolve true; all four environment forms resolve exactly | Any other environment value returns `configuration_invalid`, exit 2 |
| Offline inspection | No Gateway URL; manifest would fail if loaded | `config current` and `--version` succeed without Catalog construction or Gateway traffic | URL remains absent for later execution preflight |
| Token display | Long or short token from any source | Long value shows only first four characters plus a mask; short value is fully masked; raw secret is absent from stdout, stderr, and `ResolvedSettings.ToString()` | N/A |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Core/Settings/SettingsResolver.cs` -- existing profile-first and per-field resolver; preserve one store read, correct source labels/defaults, and make failures source-specific.
- `src/Hexalith.McpCli.Core/Settings/ResolvedSettings.cs` -- immutable DI snapshot currently has a generated record string that can expose `Token`.
- `src/Hexalith.McpCli.Core/Settings/ProfileStore.cs` -- owns only `mcpcli.json`, profile validation, and display masking; do not copy the sibling admin store's permissive parsing or unsafe JSON projection.
- `src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs` -- submission limits are currently reused incorrectly for profile allowlist-key validation; separate key validity from per-call count/value/size limits.
- `src/Hexalith.McpCli/Cli/GlobalOptionsBinding.cs` -- binds recursive flags; explicit boolean presence must use parser presence rather than value-token count.
- `src/Hexalith.McpCli/Hosting/HostFactory.cs` and new `src/Hexalith.McpCli/Hosting/SettingsBootstrap.cs` -- composition boundary for environment/profile resolution before constructing exactly one Host.
- `src/Hexalith.McpCli/Cli/CliRunner.cs` -- remove direct environment/resolver ownership, consume the registered singleton, and include `Output` in `config current` without touching the Catalog.
- `src/Hexalith.McpCli/Program.cs` -- preserve the existing early `--version` path unchanged.
- `tests/Hexalith.McpCli.Core.Tests/SettingsAndRegistrationTests.cs` and `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs` -- focused resolver, DI, parser, offline, output, error, isolation, and secrecy coverage.

## Tasks & Acceptance

**Execution:**
- [x] `SettingsResolver.cs`, `ExtensionValidator.cs`, `ProfileStore.cs`, and `ResolvedSettings.cs` -- make precedence, source attribution, boolean parsing, allowlist-key validation, and redaction satisfy the frozen matrix without applying command-submission limits to stored allowlists.
- [x] `GlobalOptionsBinding.cs`, `Hosting/SettingsBootstrap.cs`, `HostFactory.cs`, and `CliRunner.cs` -- bind bare flags correctly, move environment/profile resolution to the composition boundary, consume settings from DI, and render the complete current snapshot.
- [x] `SettingsAndRegistrationTests.cs` -- cover every source tier/default, all three environment booleans and invalid values, allowlist source/size semantics, raw-token-safe stringification, one profile read, and singleton identity.
- [x] `ConfigCommandTests.cs` -- cover profile-selection combinations, bare flags, complete value/source output, source-specific exit-2 errors, admin-path isolation, token secrecy, absent URL, and a throwing manifest proving offline inspection never builds the Catalog.

**Acceptance Criteria:**
- Given any implemented CLI verb, when settings resolution succeeds and the verb runs, then exactly one Host owns one `ResolvedSettings` singleton and Core/head behavior uses that instance rather than rereading environment or profile state.
- Given `config current` with any valid combination of flags, environment, selected profile, and defaults, when its JSON or table result is emitted, then all effective settings and their sources are represented and no raw token is observable.
- Given malformed configuration from a known source, when resolution fails, then the CLI emits only the canonical `configuration_invalid` document naming that source and exits 2.

### Review Findings

Code review 2026-09-28 (range `e599f5c..d19eb40`, layers: blind-hunter, edge-case-hunter, verification-gap, acceptance-auditor).

- [x] [Review][Patch] Production environment reader is never exercised: every CLI test injects `readEnvironment`, parity tests set no `EVENTSTORE_*`, loopback strips them; defaulting the reader to `_ => null` stays green. Add an out-of-process `config current` test with temp `HOME` plus `EVENTSTORE_TENANT`/`EVENTSTORE_READ_ONLY` asserting values and sources (medium, verification-gap) [src/Hexalith.McpCli/Hosting/SettingsBootstrap.cs:23]
- [x] [Review][Patch] `mcp` verb configuration-error path is untested: no test drives `HostFactory.Create` failure under `mcp`; routing it to stdout or returning 0 stays green. Add an `mcp` case with `EVENTSTORE_URL=not-a-url` and a failing `runMcp` stub asserting exit 2, empty stdout, stderr `configuration_invalid` naming the source (medium, verification-gap) [src/Hexalith.McpCli/Cli/CliRunner.cs:411]
- [x] [Review][Patch] Allowlist-key validation is unpinned at both layers: `ProfileStore.Read` rejects first, so the resolver's source-specific branch is unreachable in production and both raw-file tests assert only `ShouldContain("profile")`, which the generic catch prefix satisfies; no test submits an invalid-grammar key via `Add`/`Set`. Pin `store.Set("dev", "allowedExtensions", "../unsafe")` throwing without mutation, and drive the resolver seam (`Func<ProfileSnapshot>`) asserting the exact message (medium, verification-gap+blind-hunter+acceptance-auditor) [tests/Hexalith.McpCli.Core.Tests/SettingsAndRegistrationTests.cs:239]
- [x] [Review][Patch] Blank token and tenant rejection is untested: only actor is covered; dropping `ValidateText(token)` or `ValidateText(tenant)` stays green. Add `EVENTSTORE_TOKEN " "` and `EVENTSTORE_TENANT " "` rows (medium, verification-gap) [tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs:319]
- [x] [Review][Patch] Profile-file failures are reported under the ambiguous prefix "Invalid mcpcli profile or environment setting:"; split the catch so environment `FormatException` keeps its variable-named message and store failures say they come from the mcpcli profile file (low, acceptance-auditor) [src/Hexalith.McpCli.Core/Settings/SettingsResolver.cs:112]
- [x] [Review][Patch] `config current --format table` is never asserted although AC2 covers table output; add a table case checking every field, the `sources` entry, and the masked token (low, acceptance-auditor) [tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs:285]
- [x] [Review][Patch] A flag-selected missing profile is untested; only the environment-selected case exists. Add `--profile missing` asserting exit 2 and `flag` in the message (low, acceptance-auditor) [tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs:346]
- [x] [Review][Patch] `McpReadOnlyOmitsSendCommandAsync` has no positive control: an empty tool collection also passes. Also assert the query tool is advertised (low, blind-hunter) [tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs:483]
- [x] [Review][Patch] `VersionUsesEarlyOfflineEntryPointAsync` does not poison settings, so it cannot prove `--version` skips resolution; set `EVENTSTORE_READ_ONLY=yes` and `EVENTSTORE_URL=not-a-url` in `startInfo.Environment` (low, blind-hunter) [tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs:506]
- [x] [Review][Defer] `config profile add/remove/use/set` run through `RunAsync` settings resolution, so a missing `EVENTSTORE_PROFILE` or corrupt profile file blocks the verbs that would repair it [src/Hexalith.McpCli/Cli/CliRunner.cs:302] — deferred: pre-existing, belongs to Stories 2.2/2.3 profile management
- [x] [Review][Defer] `--output` path is not validated before execution, so a `send` can reach the Gateway and then fail writing the result [src/Hexalith.McpCli/Cli/CliOutput.cs:25] — deferred: pre-existing, belongs to Story 2.11 output routing
- [x] [Review][Defer] Cancellation during `host.RunAsync` startup is caught by the generic handler and reported as `internal_error` exit 2 [src/Hexalith.McpCli/Cli/CliRunner.cs:462] — deferred: pre-existing, MCP stdio lifecycle (Epic 3)
- [x] [Review][Defer] `Host.CreateApplicationBuilder()` loads content-root `appsettings*.json` and all environment variables (including `EVENTSTORE_ADMIN_*`) into unused `IConfiguration` [src/Hexalith.McpCli/Hosting/HostFactory.cs:39] — deferred: pre-existing; consider `Host.CreateEmptyApplicationBuilder` in a hosting hardening change

**Rejected:**
- Mask oracle/containment (`abcd***` → `abcd****`, `abcd*` → `abcd***`): low; requires tokens ending in asterisks, output never literally equals the raw token, and any fix adds branches.
- Prefix shown for 5–8 character tokens: spec-mandated threshold (">4 visible prefix"); fix would edit the spec.
- Environment booleans case-sensitive while flags are not: exact `true/false/1/0` is spec-mandated for environment values.
- MCP host built before format/output checks and `EVENTSTORE_FORMAT=table` unchecked: false; the host is disposed unstarted with no Catalog built, and the explicit-format check is unchanged pre-existing behavior.
- `HostFactory.Create` out-parameter contract: false; no caller diverges, no named harm.
- Hand-written `ToString` omits `AllowedExtensions`/`Sources`: false; diagnostic-only, token redaction is the only requirement.
- Test mutates `Environment.CurrentDirectory` under parallel runs: false; the CLI test assembly sets `ParallelMode.None`.
- Dead `ThenBy`, redundant temp-directory creation: false; no bad outcome.
- Unbounded stored allowlist: false; Design Notes allow exceeding 32, and the 1 MiB file cap bounds it.
- Admin isolation test does not use real `~/.eventstore/profiles.json`: false; `src/` has no reference to `profiles.json` or `EVENTSTORE_ADMIN_*`.
- `null` fields in `config current`: spec requires every setting in the flat current document.
- No CLI-level singleton identity test: false; `HostFactory` passes the same instance to `AddMcpCliCore` and `AddMcpCliMcpServer`, and Core asserts identity.
- Empty `EVENTSTORE_*` treated as set: false; pre-existing, fails loudly with the source named, consistent with the blank-text rule.

## Implementation Notes

- Added a hosting-layer settings bootstrap so environment/profile resolution occurs once before Host construction and CLI actions consume the registered singleton.
- Corrected explicit boolean detection, exact environment boolean parsing, source-attributed failures, complete current output, token redaction, and profile allowlist-key validation without per-call limits.
- Added focused Core and CLI coverage for all matrix scenarios, including the executable `--version` path, production environment capture, and a real MCP stdio initialize/list-tools exchange. Verification: Release build 0 warnings/errors; Core 205/205; CLI 33/33; no skipped tests.
- Three independent review lenses found no unresolved Story 2.1 defect after patches. One pre-existing profile-management snapshot race was recorded in `deferred-work.md` for Stories 2.2/2.3.
- Unrelated concurrent pointer changes under `references/Hexalith.FrontComposer` and `references/Hexalith.Tenants` were observed during final audit and left untouched.

## Spec Change Log

## Review Triage Log

| Reviewer | Finding | Verdict | Evidence / route |
|---|---|---|---|
| blind-hunter | Mask output can equal `abcd***` or `***` verbatim. | high | Confirmed from `MaskToken`; a complete bearer token can be emitted. Patch with collision-safe masking and regression tests. |
| blind-hunter | Two `references/` gitlinks advanced. | false | Initial status was clean; both pointers moved concurrently after implementation and remain unrelated external work that this story will not stage, revert, or claim. |
| blind-hunter | MCP does not consume the DI-owned settings instance. | false | `HostFactory` passes the exact `ResolvedSettings` object registered by `AddMcpCliCore`; MCP closes over that same object and never rereads profile/environment state. |
| blind-hunter | Profile management actions reread or mutate `ProfileStore` after bootstrap. | medium | Confirmed and pre-existing: list can render a later snapshot with earlier format/output settings. Defer to profile-management work because Story 2.1's inspection path does not reread and the frozen intent forbids changing mutation semantics. |
| blind-hunter | `config current` allowlist order is not contractual. | low | Confirmed set enumeration can vary. Patch by sorting the display projection without changing settings semantics. |
| blind-hunter | Precedence is not exhaustively tested per setting. | false | `SettingsResolver` uses shared selectors with representative tier coverage and all boolean fields; the distinct bootstrap allowlist gap is separately confirmed below. |
| blind-hunter | Explicit `false` flag precedence is untested. | medium | Confirmed; parser accepts explicit false but no test proves it overrides true environment/profile values. Patch the CLI suite. |
| blind-hunter | Current-document source completeness is untested. | false | Core asserts the complete source-key set and CLI serializes that dictionary directly while asserting representative fields; no independent projection can drop individual source entries. |
| blind-hunter | Token secrecy coverage misses sources, formats, and mask-like values. | high | The demonstrated mask-like collision is real; source/format paths share one masker. Patch the root masker and add direct collision/current-output coverage. |
| blind-hunter | No observable Gateway factory proves offline inspection. | false | `config current` resolves no gateway service and invokes no executor; the lazy throwing-manifest test proves the only adjacent activation path is untouched, so no HTTP call site is reachable. |
| blind-hunter | Real composition could create duplicate settings/hosts without a test. | false | `RunAsync` and `RunMcpAsync` each contain one `HostFactory.Create` call, and DI identity is asserted; there is no second registration or construction path in the traced call graph. |
| blind-hunter | `--version` should also run under malformed settings. | false | The test launches the actual entry point, whose only successful `--version` parse is the pre-runner early return; profile/environment resolution is structurally unreachable. |
| blind-hunter | Spec and sprint review states disagree. | false | The workflow intentionally keeps sprint status `in-progress` during review and synchronizes terminal status only after review succeeds. |
| blind-hunter | Redacted record strings omit non-secret properties. | false | No consumer or requirement treats `ToString()` as a complete settings document; the public `config current` projection remains complete and `ToString()` is diagnostic-only. |
| edge-case-hunter | Four Unicode text elements can exceed four UTF-16 units. | medium | Confirmed: code-unit slicing can expose a prefix for a four-character secret or split a surrogate. Patch with text-element-aware masking. |
| edge-case-hunter | A token can equal its computed mask. | high | Confirmed with `abcd***`; patch the shared masker so its result never equals the input. |
| edge-case-hunter | Control characters in a visible prefix can forge diagnostics. | medium | Confirmed because tokens reject only blank text. Patch by fully masking unsafe prefixes. |
| edge-case-hunter | `SettingsInput.ToString()` can contain a complete mask-like token. | high | Confirmed through the shared masker collision; covered by the shared patch and record-string tests. |
| edge-case-hunter | `config current` can contain a complete mask-like token. | high | Confirmed through the shared masker collision; covered by the shared patch and CLI-output tests. |
| verification-gap | `SettingsBootstrap` capture is not tested for tenant, tenant-override, or strict. | medium | Pre-verified gap: removing those names leaves current tests green. Patch with a CLI theory/fixture covering every supported environment name. |
| verification-gap | The actual `mcp` verb does not prove resolved read-only settings reach advertisement. | high | Pre-verified safety gap: direct MCP tests bypass the CLI/bootstrap bridge. Patch with a CLI-verb stdio test proving `send_command` omission. |
| verification-gap | Blank output-path rejection has no observing test. | medium | Pre-verified: deleting the new check leaves tests green. Patch a canonical exit-2/source test. |
| verification-gap | A selected profile with no allowlist has unpinned default attribution. | medium | Pre-verified: reverting the source expression leaves tests green. Patch the selected-profile source assertion. |
| verification-gap | Two `references/` gitlinks advanced. | false | Same unrelated concurrent workspace changes as the blind-hunter finding; preserve them without attributing them to Story 2.1. |
| verification-gap | The production `mcp` host runner is bypassed by every CLI test. | high | Pre-verified: injected CLI tests and direct protocol tests do not execute `RunMcpHostAsync`; replacing it with an immediate success leaves them green while the installed command serves nothing. Patch with an out-of-process initialize/list-tools exchange through the real CLI entry point. |
| verification-gap | Four Unicode text elements occupying more than four UTF-16 units are not pinned to full masking. | medium | Pre-verified: changing the boundary back to UTF-16 length leaves the current fixtures green and can expose a complete four-element secret. Patch the masker theory with a four-element non-BMP case. |
| verification-gap | Unicode line- and paragraph-separator masking branches have no verification. | medium | Pre-verified: deleting both category guards leaves all tests green and permits attacker-controlled line breaks in diagnostic text. Patch the masker theory with U+2028 and U+2029 cases. |
| blind-hunter | `MaskToken` outputs can contain the complete original mask-like token as a substring. | high | Confirmed: `abcd***` becomes `abcd****` and `***` becomes `****`, so the full credential remains observable despite output inequality. Patch the shared masker to fall back to a full mask that cannot contain the input and add regression cases. |
| blind-hunter | Whitespace `mcp --output` returns `configuration_invalid` before the MCP explicit-option error. | medium | Confirmed against the baseline flow: new generic output validation runs inside `HostFactory.Create` before MCP's existing `invalid_arguments` checks. Patch by preserving the format-then-output MCP checks before settings resolution/host creation. |
| blind-hunter | MCP-incompatible format/output flags are checked only after host construction. | medium | Confirmed: the current flow calls `HostFactory.Create` first, whereas the baseline checked these options before `HostFactory.Create`; unrelated host configuration can now replace the deterministic MCP error. Patch by moving both checks ahead of host creation. |
| blind-hunter | `Host.CreateApplicationBuilder` can make offline `config current` depend on unrelated application configuration. | medium | Confirmed but pre-existing at the recorded baseline: every CLI action already constructed the same default Host. Defer hosting-configuration isolation outside this story's settings hardening. |
| blind-hunter | Nested values in `config current --format table` spill onto unlabelled continuation lines. | low | Confirmed: `JsonElement.GetRawText()` retains indented array/object formatting, so `allowedExtensions` and `sources` are not one field/value row. Patch the table cell serialization to compact JSON. |
| blind-hunter | Diagnostic settings strings interpolate unrestricted non-secret values without escaping line breaks. | low | Confirmed, but no production caller currently emits these record strings and escaping every unrestricted field adds policy and branches beyond the token-secrecy requirement. Reject as unlikely developer-only harm. |
| blind-hunter | Three edited C# files have mixed LF/CRLF terminators despite the repository CRLF rule. | low | Confirmed by `file` and `git check-attr`: the files contain mixed terminators while `.gitattributes` requires `eol=crlf`. Patch mechanically by normalizing the edited files. |
| blind-hunter | Five `references/` gitlinks are part of the supplied baseline diff. | false | The pointers were advanced by the separate pre-existing commit `f40ad372db2e658235ab6867e04afab9a360abe1`; the working tree was clean at this run's start and this story did not modify or stage them. |
| blind-hunter | The implementation note mentioning two observed pointer changes omits three pointers now in the baseline diff. | false | The note accurately records two concurrent changes observed during the earlier Story 2.1 audit; the later separate five-pointer commit is not an exhaustive fact the note purports to catalogue. |
| blind-hunter | The recorded review range does not cover the final supplied diff. | low | The range labels a prior dated review round rather than this workflow's current review, but the adjacent completion prose is stale. Reject because the requested remedy only edits this build's spec; the current triage log records the final review evidence. |
| blind-hunter | The checked source-tier coverage claim lacks a flag-tenant and profile-format test. | false | carried: `SettingsResolver` uses the same traced selector for string tiers, representative tier tests exercise it, and distinct boolean/bootstrap gaps have dedicated tests; per-field Cartesian duplication is not required. |
| edge-case-hunter | Environment values can change between per-name reads in `SettingsBootstrap`. | low | Confirmed only under concurrent in-process environment mutation; production does not mutate these process settings during startup, and an atomic snapshot path would add a separate seam and branch. Reject as unlikely and disproportionate. |
| edge-case-hunter | A valid-looking but unusable output path can fail only after a Gateway action. | medium | Confirmed and pre-existing at the baseline; this story added blank validation but intentionally did not change execution/output transaction semantics. Defer to Story 2.11 output routing. |
| edge-case-hunter | MCP startup cancellation is mapped by the generic catch instead of a clean shutdown. | medium | Confirmed and pre-existing in the baseline `host.RunAsync` flow. Defer to Epic 3 MCP stdio lifecycle. |
| edge-case-hunter | Profile-management actions reread or mutate `ProfileStore` after bootstrap. | medium | carried: confirmed pre-existing snapshot divergence, already deferred to Stories 2.2/2.3 because the frozen intent excludes profile mutation semantics. |
| edge-case-hunter | The alternate token mask lets observers reconstruct mask-like credentials. | high | Confirmed through the same shared-mask defect: the output contains the complete original credential as a prefix. Patch with the collision-safe full-mask fallback used for the blind-hunter finding. |

## Design Notes

Retain the established current-document compatibility shape: flat resolved values plus a `sources` map. Keep secret-bearing `ResolvedSettings.Token` for the bearer handler, but make all display/string paths explicitly redacted. Profile allowlists may exceed one command's 32-extension submission limit; each stored key must still satisfy the same grammar and sanitizer rules.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` -- expected: restore succeeds with pinned dependencies.
- `dotnet build Hexalith.McpCli.slnx --configuration Release` -- expected: zero warnings and errors.
- `dotnet test tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Release --no-build` -- expected: all Core tests pass.
- `dotnet test tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Release --no-build` -- expected: all CLI tests pass.
