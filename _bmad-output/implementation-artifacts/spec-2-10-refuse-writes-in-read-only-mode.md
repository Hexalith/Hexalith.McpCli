---
title: 'Refuse Writes in Read-only Mode'
type: 'feature'
created: '2026-10-05'
status: 'in-review'
baseline_commit: '3260812a565d5a6d915e3343ebe2941df549ee13'
route: 'oneshot'
review_loop_iteration: 0
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

- Implemented the early CLI dispatch with no Core policy duplication. Added 31 CLI acceptance cases and expanded the direct executor refusal to 10 cases. The input test uses a disposed reader to detect any stdin acquisition, and verifies exact error JSON, exit 2, zero Gateway requests, and preserved result-file contents. Both flag/environment modes execute valid queries through the real client; environment discovery and explicit false override are covered.
- Focused verification passed: 31/31 CLI cases and 10/10 direct executor cases. CLI and Core Debug builds succeeded with zero warnings/errors.
- Review patches add a successful one-request command with `--read-only false`, three direct-executor identity/extension refusal cases, and the settings/catalog prerequisite in README. The loopback harness now optionally returns a Command 202 response; existing query fixtures keep their defaults.
- Final full-lane results: Core 557 passed / 2 existing Windows-only skips (559 total); CLI 424 passed; MCP 6 passed; Abstractions 20 passed; Analyzers 19 passed. All six individual Debug test-project builds passed with zero warnings/errors. Final whitespace and changed C# CRLF checks passed.
- Full acceptance remains blocked by an existing Manifest dependency-policy failure (7 passed, 1 failed). Per the repository baseline's requirement that all existing/new tests pass, leave this spec `in-review` and sprint story `review`, rather than marking the story complete. Production code and story acceptance tests are implemented and reviewed.
- Commit-message validation: `npx --no -- commitlint --edit /tmp/mcpcli-2-10-commit-message.txt` exited 0; exact candidate and captured output are preserved in `/tmp/mcpcli-2-10-commit-message.txt` and `/tmp/mcpcli-2-10-commitlint.log`.

## Review Triage Log

- **Low, rejected:** The missing-file case cannot detect a hypothetical read whose exception is discarded before refusal. The actual branch returns before `ReadPayloadAsync`; moving it below existing acquisition fails the absent/file/stdin cases. Detecting an otherwise invisible discarded read needs a new I/O seam or platform-specific blocking-file fixture, disproportionate to this speculative regression. The disposed-reader case directly detects stdin acquisition.
- **Low, patched:** The explicit-false case stopped at malformed JSON. Added a valid command and Command 202 loopback response, asserting accepted result and exactly one Gateway request.
- **Low, patched:** Direct-executor refusal tests lacked invalid envelope inputs. Added separate invalid correlation, idempotency, and unapproved-extension cases with valid payloads and zero Gateway interactions.
- **Low, patched:** README overstated unconditional refusal. Qualified the behavior with successful settings resolution and catalog access; unknown-operation and kind errors remain documented.

## Verification Blocker

Exact command: `dotnet tests/Hexalith.McpCli.Manifest.Tests/bin/Debug/net10.0/Hexalith.McpCli.Manifest.Tests.dll -result-xml /tmp/mcpcli-2-10-Manifest.xml` (stdout/stderr captured in `/tmp/mcpcli-2-10-Manifest-tests.log`) exited 1. `DependencyPolicyTests.ProductionContractsStayWithinPinnedDependencyClosure` reports:

```text
Restored package Hexalith.EventStore.Client/3.112.0 is outside the exact dependency policy
Restored package Hexalith.EventStore.Contracts/3.112.0 is outside the exact dependency policy
```

`tools/dependency-policy.json` pins both to 3.110.0, while existing tool restore assets resolve 3.112.0. The current root-declared Builds checkout declares 3.113.0. No dependency, build configuration, policy, or submodule files changed during this story (`git diff --` on these paths is empty). Reconciling this pre-existing dependency policy requires separate work; no restore, package update, policy weakening, or submodule update was performed. The focused executable fallback and all affected complete test suites passed as recorded above.
