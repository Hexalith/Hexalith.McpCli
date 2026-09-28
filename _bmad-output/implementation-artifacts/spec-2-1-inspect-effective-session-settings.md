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

## Implementation Notes

- Added a hosting-layer settings bootstrap so environment/profile resolution occurs once before Host construction and CLI actions consume the registered singleton.
- Corrected explicit boolean detection, exact environment boolean parsing, source-attributed failures, complete current output, token redaction, and profile allowlist-key validation without per-call limits.
- Added focused Core and CLI coverage for all matrix scenarios, including the executable `--version` path. Verification: Release build 0 warnings/errors; Core 198/198; CLI 25/25; no skipped tests.
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

## Design Notes

Retain the established current-document compatibility shape: flat resolved values plus a `sources` map. Keep secret-bearing `ResolvedSettings.Token` for the bearer handler, but make all display/string paths explicitly redacted. Profile allowlists may exceed one command's 32-extension submission limit; each stored key must still satisfy the same grammar and sanitizer rules.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` -- expected: restore succeeds with pinned dependencies.
- `dotnet build Hexalith.McpCli.slnx --configuration Release` -- expected: zero warnings and errors.
- `dotnet test tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Release --no-build` -- expected: all Core tests pass.
- `dotnet test tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Release --no-build` -- expected: all CLI tests pass.
