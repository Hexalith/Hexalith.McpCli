---
title: '4.16 Stage and validate the paired packages'
type: 'feature'
created: '2026-10-29'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '9ba8e5bd0e213501b39d33cedf46859566fc89a4'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The package pair lacks validated staging, portable installation evidence and Windows profile-safety execution.

**Approach:** Extend the existing release workflow with a staging-only path: select one semantic-release version, pack the manifest's two projects, validate their bytes and install the same tool on Linux, Windows and macOS.

## Boundaries & Constraints

**Always:** Require clean current-main source, successful exact-SHA dependency/inventory/loopback/live gates and FR-22 integration, containing baseline and synchronization evidence. Bind results to the full source SHA, version and package hashes. Preserve bootstrap, framework-dependent untrimmed .NET 10 packaging and CLI/MCP channels. Add absolute `MCPCLI_HOME`, retaining `.eventstore/mcpcli.json`; explicit constructor paths take precedence, unset retains the default, invalid values fail safely. Emit JSON with LF internally and at its terminator; retain table formatting.

**Never:** Publish packages, tags or GitHub releases; enable paired publication/recovery; run hosted v1 services during installation smoke; change approved dependencies, inventories or vectors; edit reference contents; claim unexecuted platform checks passed. Operator-client setup and publication remain stories 4.17–4.18.

## I/O & Edge-Case Matrix

| State | Required behavior |
| --- | --- |
| Eligible source and releasable commits | One selected version, exactly two fresh staged packages and hash-bound validation evidence |
| No next release | Explicit no-release result; no staged pair |
| Stale/dirty source, missing or skipped gates, absent FR-22 proof | Refuse accepted staging |
| Existing staging, wrong/extra/missing packages, malformed contents or changed bytes | Fail without overwriting prior artifacts or recording success |
| Isolated install, discovery, config and MCP smoke | Exact version and channel assertions; raw deterministic discovery bytes |
| Missing/failed OS receipt, discovery mismatch or required Windows tests skipped | No accepted-pair receipt |

</frozen-after-approval>

## Code Map

- `.github/workflows/release.yml`, `.releaserc.json`: existing entry point and analyzer; isolate publication hooks from staging.
- `scripts/verify-release-source.py`: current-main/latest-run checks, presently bootstrap-only. `ci.yml` covers the blocking full-v1 gates.
- `scripts/release-request.py`, `release-prepare.sh`, `release-receipt.py`: retain publication refusal and bootstrap semantics; reuse fresh staging and source/hash checks.
- `scripts/validate-release-packages.py`, `tools/release-packages.json`: existing pair/tool checks; generated manifest and restored policy establish enrollment.
- Story 4.15 `evidence/story-4-15/code-review-20261029/verification.json`: authoritative revision `70dbf73e80787299c832d30d911b16b105ab194d`; recheck current committed containment and synchronization rather than trusting historical pending fields.
- `src/Hexalith.McpCli.Core/Settings/ProfileStore.cs`, `Serialization/McpCliJson.cs`; `src/Hexalith.McpCli/Cli/CliOutput.cs`: home resolution and platform-dependent JSON newlines. Existing tool project already declares the required pack properties.
- `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs`, `CliOutputContractTests.cs`, `McpStdioProcessTests.cs`; Core `ProfileStoreTests.cs`: reuse process/channel and ACL assertions; remove home-related Windows skips after isolation works.

## Tasks & Acceptance

**Execution:**

- [x] `scripts/select-release-version.mjs` — calculate the next version with pinned semantic-release in an isolated temporary Git copy/local remote; omit publishing plugins and external writes, preserve source history/tags and return an explicit no-release result.
- [x] `scripts/verify-release-source.py`, `scripts/verify-paired-prerequisites.py` — add a staging context requiring current clean main, latest successful exact-SHA CI/commitlint runs with required jobs executed, and fresh upstream/baseline/sync evidence.
- [x] `scripts/prepare-paired-release.py`, `scripts/validate-release-packages.py` — restore/build the solution in Release at that version, pack only manifest projects into fresh staging, verify structure/effective packaging properties, Contracts-reference equality and framework-dependent managed payload; bind both hashes and source provenance.
- [x] `scripts/smoke-paired-tool.py` — install exclusively from staged local source with private caches/config/home; capture version, offline discovery/config, error and MCP protocol/channel checks, output-file behavior and package hashes.
- [x] `ProfileStore.cs`, `McpCliJson.cs`, `CliOutput.cs` at the mapped paths — implement home precedence/validation and deterministic JSON without changing envelope or table behavior.
- [ ] `tests/Hexalith.McpCli.Core.Tests/ProfileStoreTests.cs`, mapped CLI tests — cover override/invalid inputs, exact JSON channels/bytes, isolated child processes and Windows ACL/process execution; repair platform fixture defects exposed by execution. Code and Linux verification are complete; actual Windows execution remains outstanding.
- [x] `.github/workflows/release.yml`, `scripts/compare-paired-evidence.py` — add staging-only jobs with read-only repository permissions, one packed pair, three OS consumers, Windows Core/CLI suites and macOS CLI suite; accept only complete matching hash-bound receipts and raw discovery captures.
- [x] `scripts/tests/test_paired_release.py` — test matrix failures and refusal paths, including stale source, tampering, skipped gates/tests and unchanged paired-publication rejection.
- [x] `README.md`, story evidence, this spec and `sprint-status.yaml` — document behavior/commands and distinguish local checks from executed hosted acceptance; reconcile existing Windows/macOS deferrals only with evidence.

**Acceptance Criteria:**

- Given eligible current-main source, when staging completes, then exactly the manifest pair shares the semantic-release version and its validated hashes identify the retained artifacts.
- Given that same staged tool, when each OS installs and runs offline smoke, then version, CLI/MCP channels and raw discovery bytes agree without hosted infrastructure.
- Given Windows validation, when Core/CLI suites run with isolated home overrides, then both private-ACL tests and formerly home-skipped concurrency/admin-isolation process tests execute successfully.
- Given any failed prerequisite or platform check, when acceptance is evaluated, then no accepted pair is produced and publication remains refused.

## Implementation Notes

Approved by the user on 2026-10-29: "approve and continue". Implementation follows the frozen intent; no push or remote operations in this stage. Hosted Windows/macOS acceptance remains pending until actual runner evidence exists.

## Spec Change Log

## Review Triage Log

## Design Notes

No intent gaps or irreversibles. Semantic-release dry runs check push permission, requiring temporary Git state. Windows/macOS acceptance needs actual runner evidence. ARM verification remains deferred.

## Verification

- Run `python3 -m unittest discover -s scripts/tests -p 'test_*.py'` and real local paired preparation/install smoke; exercise negative controls with temporary fixtures.
- Restore/build `Hexalith.McpCli.slnx` in Release with warnings as errors; run the six ordinary test projects individually. Refresh restore before Manifest.Tests.
- Run sample validation/loopback and enrolled coverage/replay gates for Core JSON changes; restore again after sample loopback.
- Require actual three-OS receipts, raw-byte comparison and named Windows test outcomes before platform acceptance. Preserve exact commands/results and blockers in task-owned evidence.


## Implementation Evidence (2026-10-29)

Implementation and local Linux checks are recorded in `evidence/story-4-16/implementation-20261029/README.md`. The staging path, isolated home and deterministic JSON are implemented; paired publication/recovery still refuse requests. One local-only version 1.1.1 pair was packed, validated and installed successfully. No accepted-pair receipt was produced.

Actual hosted Windows/macOS checks and three-OS acceptance remain pending. The existing Windows/macOS/ARM ledger entries remain open with implementation notes; code changes and synthetic matrix tests are not platform evidence. This spec and sprint remain in progress until the required executed acceptance evidence exists.

The implementation session made read-only GitHub API observations before correcting its interpretation of the no-remote-operations constraint. The evidence packet labels those fresh observations separately from local committed/gitlink and cached remote-tracking evidence. No remote writes, pushes, tags, releases or workflow dispatches occurred.

Parent implementation audit: [matrix/evidence assessment](evidence/story-4-16/implementation-20261029/parent-audit.md). Both audit findings were fixed and verified. The parent independently checked retained package hashes and passing command receipts. Actual Windows/macOS execution remains required before advancing from implementation to workflow review; the Windows execution task is intentionally unchecked.

The user subsequently approved committing/pushing this implementation, waiting for the required CI gates and dispatching `stage-paired` to obtain actual platform evidence. This specific authorization supersedes the implementation step's no-push/no-remote restriction for those actions. Package, tag and GitHub release publication remain prohibited. Keep the source checkout clean during staging and retain hosted-run observations separately from the earlier local-only evidence.

Full CI passed for source `513784a53226ae64e47a63fd76ea46222781a3ef`. Its first staging run stopped before packing with `ERELEASEBRANCHES`: exact-SHA checkout had detached HEAD and no local main, so the temporary mirror lacked the configured release branch. The selector now resets main and symbolic HEAD only inside its temporary mirror. Three real Git/semantic-release regression cases pass for absent, older and newer main refs; removing the repair reproduces failures. Bootstrap installs the existing pinned Node/npm tooling to run and retain these regressions. See [detached-source evidence](evidence/story-4-16/detached-source-20261029/README.md). Actual Windows/macOS acceptance still awaits a successful staging run from the repaired source.
