---
title: '4.16 Stage and validate the paired packages'
type: 'feature'
created: '2026-10-29'
status: 'done'
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
- [x] `tests/Hexalith.McpCli.Core.Tests/ProfileStoreTests.cs`, mapped CLI tests — cover override/invalid inputs, exact JSON channels/bytes, isolated child processes and Windows ACL/process execution; repair platform fixture defects exposed by execution. Actual Windows Core/CLI suites and every required ACL/process test passed in staging run 40869271473.
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

Each finding was classified independently before grouping. `BH` denotes blind hunter, `EH` edge-case hunter, and `VG` verification-gap reviewer. These private validation corrections preserve the approved intent and public surface.

| Finding | Verdict | Evidence and disposition |
| --- | --- | --- |
| BH1 — malformed PE optional header/metadata | medium | Independently reproduced acceptance of magic `0x9999` by placing the CLR directory at the parser's erroneous fallback offset; the positive fixture also lacks CLR metadata. Patch the existing managed-assembly parser to require recognized magic and a valid mapped CLR metadata root, with negative controls. |
| BH2 — native payload outside portable tool directory | medium | Independently added `tools/net10.0/win-x64/payload.exe` containing `MZnative`; `validate_tool_payload` accepted it because its prefix filter skipped the entry. Patch the existing package-layout/payload check to reject alternate tools layouts and native executable payload anywhere in the package. |
| BH3 — standalone Abstractions bytes never consumed | medium | Preparation only checks the two standalone DLL filenames, and installed-tool smoke uses its bundled Abstractions rather than the separate package. Reuse the existing isolated bootstrap consumer against the staged local pair, retaining its compiler/analyzer proof before preparation succeeds. |
| BH4 — minimal XML accepted as a complete suite | low | Synthetic minimal XML does pass `inspect_xml`; however, the producer invokes each entire exact-source assembly without a test filter, checks process exit, retains both suite outcomes, and requires every named Windows fact. Actual acceptance retains 718 Core and 485 CLI cases. Reject: reaching truncated-but-successful fabricated XML requires bypassing that trusted producer, while independent case discovery/identity matching adds machinery and duplicate display names are legitimate. |
| BH5 — auxiliary smoke logs lack individual receipt hashes | low | The inner smoke receipt binds discovery rather than each auxiliary diagnostic file. The hosted artifact archive digest and retained packet file index already bind the complete actual logs; deleting extracted diagnostics manually is outside the normal producer path. Reject: adding a second diagnostic-manifest protocol adds complexity for an unlikely post-extraction mutation and does not change the executed assertions. |
| BH6 — incomplete installed MCP discovery coverage | medium | `mcp_smoke` invokes module discovery and only the first description; it never invokes `list_operations`, so an installed adapter failure there can survive this smoke. Patch by iterating the existing CLI module/operation captures and comparing every MCP list/description, retaining deterministic captures through the existing mechanism. |
| BH7 — JSON-RPC marker alone accepted as protocol | medium | The request loop and final transcript check only inspect `jsonrpc`; an unrelated object with that marker and a debug field is ignored and accepted. Patch the existing protocol predicate to require a valid response or notification envelope, with a malformed-message regression. |
| BH8 — config success does not establish transitions | medium | The five config calls assert JSON/channel/token safety only; no-op use/clear/remove implementations can satisfy them while leaving the private profile wrong. Patch with direct assertions of the existing command documents and isolated saved state at each transition. |
| BH9 — timeout loses subprocess diagnostics | low | `subprocess.run(timeout=120)` raises before `execute` writes captures or command metadata; partial output is available on `TimeoutExpired` but discarded. Patch the existing capture path to retain that output and timeout outcome before failing, without changing the deadline or adding retries. |
| BH10 — incomplete FR-22 provenance accepted | medium | Independently reproduced comparator acceptance when both `baseline_revision` and `upstream_main` are absent from the hash-bound source evidence. Patch the existing FR-22 predicate to require canonical full revisions and regression cases for omitted/malformed values. |
| EH1 — non-main dispatch ref can masquerade as main | medium | Checkout uses `github.sha`, but preparation passes a literal `refs/heads/main`; a branch/tag at current main's SHA therefore bypasses the dispatch-ref rule in `verify-release-source`. Patch the stage entry guard to require the actual `GITHUB_REF` to be `refs/heads/main` before selection/preparation. |
| EH2 — MCP request timeout resets on unrelated messages | medium | Each `messages.get(timeout=60)` starts a new timeout; a child emitting unrelated messages can prevent request completion indefinitely. Patch to use one monotonic deadline per request and retain existing failure transcripts. |
| EH3 — successful partial CI rerun rejected | medium | `verify_jobs` requests only the latest attempt, whereas GitHub's attempt endpoint lists that attempt's jobs; unchanged successful required jobs are absent after rerunning only failed jobs. Patch by selecting the newest occurrence per required job across attempts, preserving pagination and refusing newer failed/skipped/duplicate occurrences. Primary API contract: <https://docs.github.com/en/rest/actions/workflow-jobs#list-jobs-for-a-workflow-run-attempt>. |
| VG1 — real no-release selector branch untested | medium | Pre-verified gap: registered real selector regressions cover releasable histories, while the no-release preparation fixture fabricates its selection. Add a real tagged history without releasable commits and assert the exact false/null selection. |
| VG2 — nuspec source binding untested | medium | Pre-verified gap: package fixtures omit `--source-sha` and preparation mocks validation. Add real paired-validator positive/missing/wrong repository-commit cases for both packages with `--source-sha` and `--output`, requiring no success receipt on failure. |
| CI1 — asynchronous diagnostic order in query assertion | medium | Exact-source CI `40879087695` exposed the existing `QueryPreflightRunsAfterNoResultChecksAsync` assumption that the format note ends stderr. Its retained output contains exactly one complete note followed by the buffered HTTP completion diagnostic; README promises one stderr note without relative log ordering. Patch this assertion directly to recognize/remove the exact note line anywhere while retaining duplicate-note, diagnostic, stdout, file and preflight checks. |

Routing after individual classification: every survivor retains a separate root; a shared validator or file does not make two defects the same. Every survivor routes to `patch`: each smallest correction is private, directly exercises a demonstrated state, and needs no intent or spec change. BH4/BH5 are rejected as recorded; there are no new deferrals or loopbacks.

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

Full CI also passed for repaired source `251a6c32f8a61739a1650a67a1f0709eb4186973`. Staging run `40862502648` prepared version 1.2.0 and passed installation smoke on all three systems; all 26 raw discovery files matched byte for byte. macOS CLI passed 471 tests with 14 platform skips. Windows Core exposed six inherited-access failures and a 547.1785 ms cold measurement under concurrent collection load. The parent inspected repairs for inheritable directory rights, a non-parallel cold collection retaining the 500 ms limit, robust denied-data-access fixture setup, and complete-suite diagnostics. Focused Linux checks passed; see [Windows repair evidence](evidence/story-4-16/windows-fixes-20261029/README.md). The repaired source still requires actual Windows acceptance; no accepted staging receipt exists yet.

### Executed acceptance superseding the pending records above

Source `00680e93423521053b7e7d4a2c39fdcaf3345cc1` passed full CI `40866110044` and staging run `40869271473`. Version 1.2.0 is accepted for staging only: all three installed-tool smokes passed, all 26 raw discovery captures match, Windows Core passed 715 tests with three unrelated skips, Windows CLI passed 454 with 31 platform skips, and macOS CLI passed 471 with 14 platform skips. All seven explicitly required Windows ACL/process tests passed, as did the unchanged 500 ms cold-construction test. No required test skipped and no platform test failed.

The parent downloaded all five artifacts, verified their archive hashes and independently reproduced the hosted accepted receipt byte for byte. [Current acceptance evidence](evidence/story-4-16/hosted-20261029/accepted-00680e9/README.md) binds source, version, package hashes, actual platform XML and raw captures. All implementation tasks and matrix scenarios now have executed coverage; the workflow advances to review. No package, tag or GitHub release was published. The existing Windows evidence deferrals and macOS portion are resolved; Linux ARM qualification remains deferred.

### Review corrections and local verification

All 15 review findings are classified above. Thirteen private corrections were implemented and inspected; two low-severity findings were rejected on their recorded evidence. The parent reran restore, the Release warning-as-error build, all six ordinary suites, all 113 Python release-tool tests, sample validation/loopback, enrolled inventory coverage and complete production enrollment replay; every command passed. The worker's 44 focused cases, real semantic-release no-release history, source-bound package validation, compiler/analyzer consumer and 49-capture installed smoke also passed. [Review correction evidence](evidence/story-4-16/review-patches-20261029/README.md) retains exact commands, outcomes, guard-removal controls and raw local captures.

The expanded acceptance checks now require fresh clean-source CI and actual three-OS staging. The accepted `00680e9` pair above remains historical evidence for its exact source and original 26-capture matrix; it is not acceptance for the review corrections. The user's existing source-push and staging authorization covers this verification rerun.

The review-fix source `630ea7f29c02f6d10b19eae1136e01538527266e` passed bootstrap, commitlint and synchronization, but CI `40879087695` exposed the existing format-note ordering race recorded as CI1. Its direct test correction preserves every documented output assertion; the focused Release build and both worker/parent output-contract class runs passed (22 passes, two Windows-only skips). [Diagnostic-order evidence](evidence/story-4-16/format-note-order-20261029/README.md) retains the exact failure and correction. No staging was dispatched from this failed-CI source; the corrected source must pass fresh CI first.

### Final acceptance after review

Corrected source `32fb5dbf75216adaf21551bcfa36439741c41e01` passed full CI `40880599269`, including the blocking Aspire tier, plus bootstrap, commitlint, synchronization and a fresh local source/FR-22 precheck. Staging `40885068007` succeeded at version 1.2.0 with the strengthened compiler/analyzer consumer, config state, protocol and complete MCP discovery checks. All 49 raw captures match across Linux, Windows and macOS. Windows Core passed 715 tests with three unrelated skips, Windows CLI passed 454 with 31 platform skips, and macOS CLI passed 471 with 14 platform skips. Every required Windows test and the unchanged 500 ms cold-construction test passed.

The parent verified all five artifact ZIP hashes and independently reproduced the accepted receipt byte for byte. [Final accepted staging evidence](evidence/story-4-16/hosted-20261029/accepted-32fb5db/README.md) retains the exact source, package hashes, source gates, compiler proof, platform XML and raw captures. Review corrections and verification are complete, with no new deferrals; Linux ARM qualification remains in the existing ledger. This spec is done and sprint status is `review`, ready for human walkthrough. The final documentation/evidence commit records acceptance of source `32fb5db`; it does not change the validated implementation. No package, tag or GitHub release was published.
