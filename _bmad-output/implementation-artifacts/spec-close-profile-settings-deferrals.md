---
title: 'Close five profile and settings deferrals'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Reject newly saved profile tenants that cannot satisfy the Gateway tenant grammar. Close five profile and settings ledger findings with regression coverage for tenant writes, whole-string .NET regexes, short token display, large profile extension allowlists, and invalid profile home overrides.

</frozen-after-approval>

## Implementation Notes

- Baseline is `2e678329678143864ebca5c5f467580bb8e27e35`. The user authorized implementation and publication on `main`. The five selected ledger entries share the profile configuration boundary.
- Reuse `RoutingResolver.IsTenantDomain` with the executor's invariant lowercasing when validating a newly supplied tenant. Keep the stored spelling, preserve readability of older profiles, and allow operators to repair earlier values. Apply one field-update implementation to both `ProfileStore.Set` and `ValidateSet`.
- Reflect over generated regexes in the runtime assemblies to catch unescaped dollar anchors on patterns that start with a caret. Verify large settings allowlists and token masking through the Core and CLI paths. Extend the existing invalid-home process test to the reported verbs and verify that version reporting works independently of the profile.

## Verification

- `dotnet restore Hexalith.McpCli.slnx` and `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror -m:1` passed. The build used the installed Aspire 17 bundle via `AspireCliBundlePath` and reported zero warnings and errors.
- The Release Core test executable passed 131 tests selected from `ProfileStoreTests` and `SettingsAndRegistrationTests`. Three Windows ACL cases skipped on Linux.
- The Release CLI test executable passed 643 tests, with two Windows-specific skips. The profile and regex classes passed all 230 selected tests. The revised operator-help test passed independently.
- `bash tools/conformance-vectors/v1/run-sample-validation.sh Release` passed all 203 tests and validated three vectors. `bash tools/conformance-vectors/v1/run-sample-loopback.sh` passed all three sample vector replays before the outer deadline stopped its supplemental packaged-process fixture.
- The full Release Core suite passed 929 tests with four skips. Abstractions, Analyzers, and MCP passed 135 tests in total. Manifest passed 381 of 382 tests. Its descendant-process cleanup test timed out in this container and passed when rerun under the workspace's child subreaper.
- The shared pre-push command `python3 references/Hexalith.Builds/check.py` stopped before ownership comparison because its anonymous Git transport could not connect to GitHub to clone `delivered/Hexalith.McpCli`.
- The exact commit message passed the released Builds commitlint configuration with zero problems and warnings.
- Aspire startup could not complete in this workspace because the CLI attempted to write to the read-only user profile directory.

## Review Triage Log

- Medium, patched. Updated the help regression to assert the new tenant rule and the separate actor description.
- Medium, patched. The regex reflection check covers properties as well as methods.
- Medium, patched. The invalid-home subprocesses use a private working directory and Unix home override. They check that the fallback profile bytes are preserved and that the relative directory remains absent.
- Low, patched. The README scopes the extension count to a single submitted command.
- Low, patched. The version subprocess checks the exact assembly informational version and empty stderr.
- Low, patched. The spec records the executed verification commands and results.
