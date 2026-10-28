---
title: 'Resolve five deferred repository guidance items'
type: 'chore'
created: '2026-10-28'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Five open deferred items describe repository instructions that predate the current enrollment gates, production ConformanceHost, isolated live-test tier, test-only module composition, and root EventStore version pin. Following those instructions can select the wrong artifacts or test tier.

**Approach:** Resolve those five related items by correcting the repository-specific guidance in `AGENTS.md`, copying it byte-for-byte to `CLAUDE.md` and `.github/copilot-instructions.md`, and recording dated resolutions on the existing ledger entries. Verify claims against tracked configuration and source, run the existing synchronization check, obtain independent review, and commit and push to `main` as requested.

</frozen-after-approval>

## Implementation Notes

- Selected the five related guidance entries under Stories 4.10 (enrollment), 4.11 (ConformanceHost), 4.12 (live tests and test-only composition), and 4.14 (EventStore pin). Other deferred work remains outside this change.
- Planning: no unresolved intent gaps; documentation-only edits are reversible. The user explicitly authorized the final commit/push. Footprint: three instruction entry points, the existing ledger, this spec, and compact validation evidence. The small-change route applies.
- Baseline revision: `5aa3ee23ef4b395a4500453a50d4815e9837dd07` on clean `main`. Read the permitted root-declared AI.Tools baseline and Git instructions, architecture spine, root build/editor configuration, CI, test projects, conformance tools, and live-topology documentation.
- Read-only investigation independently confirmed all five items. Source anchors: `Directory.Build.props:4`, `tests/Hexalith.McpCli.ConformanceHost/Hexalith.McpCli.ConformanceHost.csproj:6`, `tools/conformance-vectors/v1/run-sample-loopback.sh:17`, `tests/Hexalith.McpCli.Core.Tests/EnrolledInventoryCoverageGate.cs:22`, `tools/conformance-vectors/v1/check_enrolled.py:171`, `.github/workflows/ci.yml:22`, and `tools/live-topology/README.md`.
- Corrected only the repository-specific managed block and recorded five dated resolutions in place in `deferred-work.md`. Universal instructions and all submodule pointers are unchanged. The provenance comment distinguishes the older full-context verification from this targeted update.
- Validation: `bash scripts/check-agent-instructions-sync.sh` and `git diff --check` both exited 0 after copying `AGENTS.md` to its two peers.
- `dotnet msbuild src/Hexalith.McpCli/Hexalith.McpCli.csproj -p:Configuration=Release -getProperty:HexalithEventStoreVersion,HexalithPartiesVersion,HexalithTenantsVersion` exited 0 and reported 3.128.3, 1.5.1, and 5.10.0 respectively; the existing restored tool assets contain those same EventStore Client/Contracts and module Contracts versions. `dotnet msbuild tests/Hexalith.McpCli.AppHost/Hexalith.McpCli.AppHost.csproj -getProperty:HexalithPartiesAspireVersion` separately confirmed the test-only Parties Aspire helper pin is 2.0.0.
- `dotnet msbuild tests/Hexalith.McpCli.ConformanceHost/Hexalith.McpCli.ConformanceHost.csproj -getProperty:ConformanceProduction` reported `true`; adding `-p:ConformanceProduction=false` reported `false`. Both exited 0. The maintained sample script supplies the false property on restore and build.
- `dotnet tests/Hexalith.McpCli.Core.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.Tests.dll -class Hexalith.McpCli.Core.Tests.EnrolledModuleCoverageTests` exited 0: 5 passed, none failed/skipped. Documentation-only scope used the existing Release assembly.
- `python3 tools/live-topology/run-vectors.py --output /tmp/mcpcli-deferred-guidance-preflight-20261028 --preflight-only` exited 0 with all approved plans preflighted and `fullLiveAccepted: false`, as expected. No live-service run or hosted acceptance is claimed.
- `npm ci` installed the pinned commit tooling. `npx --no -- commitlint --verbose --edit /tmp/mcpcli-deferred-guidance-20261028-commit.txt` passed with zero problems/warnings; successful output is retained at `evidence/deferred-guidance-20261028/commitlint.txt`.
- `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'` completed with exit 0. Its negative scenarios intentionally print failed fixture receipts; the test command itself passed.
- Fresh `dotnet restore Hexalith.McpCli.slnx` exited 0 (all projects up-to-date), then `dotnet tests/Hexalith.McpCli.Manifest.Tests/bin/Release/net10.0/Hexalith.McpCli.Manifest.Tests.dll -method Hexalith.McpCli.Manifest.Tests.DependencyPolicyTests.RepositoryTestProjectsUseOnlyApprovedDependencies -method Hexalith.McpCli.Manifest.Tests.DependencyPolicyTests.TestAppHostUsesOnlyReviewedPublishedServerFreeHelpers` exited 0: 2 passed, none failed/skipped. These existing checks confirm the test dependency restrictions named in the corrected guidance.
- `dotnet tests/Hexalith.McpCli.Integration.Tests/bin/Release/net10.0/Hexalith.McpCli.Integration.Tests.dll -preEnumerateTheories -list tests` and the exact vector-name-plus-smoke assertion from CI passed: 21 vectors plus the independent smoke, without starting services.
- Independent review produced six findings; all were checked against source and addressed within the authorized guidance update. Nothing newly deferred. Synchronization and whitespace checks passed again after the corrections.
- Before publication, `git fetch origin main` and `git rev-list --left-right --count main...origin/main` confirmed zero divergence from the starting revision. Commit uses the exact validated message file. No runtime source, dependency policy, package pin, or submodule pointer changed.
- Concurrent unrelated edits appeared after verification in `.github/workflows/commitlint.yml`, root/live-topology READMEs, `tools/live-topology/ci.py`, `test_ci.py`, and Story 4.14 evidence. They are excluded from this commit and left untouched; this change's validation describes the commands run before those concurrent edits were observed.

## Review Triage Log

- **medium / patch:** The test-composition exception could suggest the dependency policy applied only to production. `DependencyPolicyGate.CheckTestProjects` and the AppHost helper-closure check still enforce test boundaries. Clarified the test allowlist, repository-owned project references, published server-free helpers, and separately reviewed platform fixture closure.
- **low / patch:** Expanded Release validation guidance left the shared baseline's local Debug/project-reference wording implicit. Made this repository's existing package/Release validation rule explicit; no dependency or build behavior changed.
- **low / patch:** Fixture assemblies enter through the constructor's `manifest` delegate, not `InvokeAsync` parameters (`src/Hexalith.McpCli/Cli/CliRunner.cs:33`). Corrected the recipe and supplied an empty-manifest example.
- **low / patch:** The new non-live checklist omitted CI's independent .NET discovery assertion. Linked the exact `topology-vector-discovery` sequence and named its enumeration flags and vector-plus-smoke assertion.
- **low / patch:** The old provenance comment did not distinguish the targeted corrections from a full context refresh. Preserved the old full-context revision with its canonical identifier and recorded this update's canonical baseline separately.
- **low / patch:** Validation evidence was pending when the reviewer inspected the in-progress spec. Recorded actual synchronization, whitespace, MSBuild, preflight and focused-test outcomes; distinguished Contracts and test-only Aspire package pins. Final tooling, dependency and discovery outcomes are recorded above.
