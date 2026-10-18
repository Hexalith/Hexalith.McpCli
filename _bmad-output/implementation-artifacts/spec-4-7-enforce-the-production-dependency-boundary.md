---
title: '4.7 Enforce the production dependency boundary'
type: 'feature'
created: '2026-10-18'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '3cd4d33e71e03d81b1961e236abff3111944330c'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `DependencyPolicyTests` checks csproj text and module closures, but
reports no dependency path, lets `baselinePackages` grow to admit a module's extra
packages, inspects framework references only on enrolled modules, rejects a
decorated module's own Abstractions dependency, and never evaluates test projects
or a candidate pin.

**Approach:** Turn the test into a reusable gate over the restored dependency graph
(FR-20, NFR-6, AD-15). Prove it rejects the real `Hexalith.Projects.Contracts`
1.0.0 closure and admits Tenants- and Parties-shaped decorated closures, all
without network access.

## Boundaries & Constraints

**Always:** Production direct roots are exactly the policy's direct packages,
the Decoration Package, and flagged `modules` pins; production projects are only
`src/Hexalith.McpCli.*`. `baselinePackages` must equal the exact closure reachable
from the non-module roots, so the baseline cannot be widened to fit a module.
Every failure names the offending identity/version and its path from
`Hexalith.McpCli`. Every restored package's framework references are
`Microsoft.NETCore.App` only. Test-only packages and the synthetic sample fixture
are allowed in `tests/` and rejected in production, even if listed in policy.
Each guard has a test that fails when the guard is removed.

**Never:** Enroll a module, change `src/` or runtime behavior, edit `references/`,
widen the allowlist, admit `Hexalith.Parties.Aspire` before it is published, add
network-dependent restores to tests, or put module-specific branches in the gate.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Current tool | Fresh restore, `modules: {}` | Gate passes | N/A |
| Projects candidate | Captured 1.0.0 closure pinned and flagged | Fails: `Microsoft.AspNetCore.App` and UI/web packages, each with its path | Policy file unchanged |
| Widened baseline | Projects candidate plus its packages added to baseline | Still fails: baseline entries outside the stack closure | Named per entry |
| Decorated Tenants/Parties | Compliant closure plus Abstractions dependency, exact pin | Passes | N/A |
| Sample or test package in production | Through `src` project or package reference, or listed in `modules` | Fails as test-only, with path | Even when allowlisted |
| Test projects | Named EventStore testing/Aspire roots, sample fixture | Passes; unapproved package or `references/` project fails | Names project and item |

</frozen-after-approval>

## Code Map

- `tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs` -- current gate.
  Keep its src csproj XML checks (inline versions, flags, `$(` includes, framework
  references; Analyzers excluded). `FindUnapprovedModuleDependencies` reports no
  path and calls an Abstractions dependency resolved as a project "unresolved".
- `src/Hexalith.McpCli/obj/project.assets.json` -- `targets.net10.0` entries carry
  `type`, `dependencies`, per-package `frameworkReferences`; project entries
  (Abstractions, Core, Mcp) carry their package roots; `libraries[*].path` is the
  csproj path; tool roots are in `project.frameworks.net10.0.dependencies`.
- `tools/dependency-policy.json` -- 10 used `directPackages`, exact
  `baselinePackages`, `decorationPackage`, `modules`; consumed only by this test.
- `tests/Directory.Build.props` injects Microsoft.NET.Test.Sdk, xunit.v3, Shouldly,
  NSubstitute; `tests/Hexalith.McpCli.ConformanceHost` (outside the slnx) uses the
  sample package. Stack table (`ARCHITECTURE-SPINE.md:207-223`) also names
  Verify.XunitV3, Microsoft.CodeAnalysis.CSharp, Aspire.Hosting.Testing,
  CommunityToolkit.Aspire.Hosting.Dapr, Hexalith.EventStore.Testing,
  .Testing.Integration, .Aspire, Hexalith.Tenants.Aspire.
- `~/.nuget/packages/hexalith.projects.contracts/1.0.0` -- 55-package closure:
  ASP.NET Core framework, Fluxor, FluentUI, FrontComposer.Shell, IdentityModel,
  NUlid. Tenants 5.8.0 and Parties 1.4.0 use only baseline packages.

## Tasks & Acceptance

**Execution:**
- [x] `tools/dependency-policy.json` -- add `testPackages` (above names) and
  `sampleContracts`. Keep schemaVersion 1.
- [x] `tests/Hexalith.McpCli.Manifest.Tests/{DependencyPolicy,RestoredDependencyGraph,DependencyPolicyGate}.cs`
  -- policy model; graph loaded from assets with deterministic first-path tracking
  and candidate injection (existing nodes keep their restored version); gate
  covering the Boundaries rules, stale direct entries, missing pins, and policy
  integrity (no overlap between test and production lists). One type per file.
- [x] `tests/Hexalith.McpCli.Manifest.Tests/Fixtures/*.closure.json` -- capture the
  real Projects 1.0.0 closure; add Tenants 5.8.0 and Parties 1.4.0 closures, each
  with the simulated `Hexalith.McpCli.Abstractions` dependency.
- [x] `tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs` -- real-repo
  production and test-project gates, plus one in-memory test per guard and matrix
  row. Assert exact failure strings.
- [x] `README.md` "Gateway boundary" -- document the gate, test-only allowances,
  and why Projects stays out.

**Acceptance Criteria:**
- Given a fresh `dotnet restore Hexalith.McpCli.slnx`, when Manifest.Tests runs,
  then every test passes and `tools/dependency-policy.json` is unmodified.
- Given any single guard removed from the gate, when its tests run, then at least one fails.

## Design Notes

Failure shape: `Module Hexalith.Projects.Contracts adds unapproved package
Fluxor.Blazor.Web/6.11.0: Hexalith.McpCli > Hexalith.Projects.Contracts/1.0.0 >
Fluxor.Blazor.Web/6.11.0`. Projects are path segments without a version. The
Decoration Package is accepted whether it resolves as a project or a package, and
it is not traversed. Direct-root widening is a reviewed edit to `directPackages`;
the README states that it requires a PRD change.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx && dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` -- 0 warnings/errors
- `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` -- all pass
- `git status --porcelain tools/dependency-policy.json` after tests -- shows only the intended task edit

**Implementation evidence (2026-10-18):** Fresh solution restore passed. Release
solution build and the final Manifest project build passed with zero warnings and
errors. Manifest.Tests passed 69/69 (no failures or skips), including all 63
DependencyPolicyTests cases. `git diff --check` passed. Policy SHA-256 before and
after the full suite was
`32d12675fbcaf979f75cedc7336af5a01354cb06eb7d09936c1fdd892a9d1d5a`;
only the intended `testPackages` and `sampleContracts` additions differ from the
baseline. The complete baseline diff, including new files, was captured and read.

**Matrix audit:** Current restore → `ProductionContractsStayWithinPinnedDependencyClosure`;
Projects → `ProjectsCandidateFailsOfflineWithDependencyPaths`;
widened baseline → `WideningBaselineCannotAdmitProjects`;
decorated Tenants/Parties → `DecoratedCandidatePassesOffline` (four cases);
production test/sample leakage → `TestOnlyPackagesCannotBeAllowlistedIntoProduction`,
`ProductionProjectReferenceGuardFails`, and `RestoredExternalAndTestProjectsFail`;
test allowances/rejections → `RepositoryTestProjectsUseOnlyApprovedDependencies`,
`NamedTestRootsAndSampleAreAllowedOnlyInTests`, and
`TestProjectBoundaryRejectsUnapprovedItems`. All covering cases ran and passed.

## Review Triage Log

| ID | Finding | Verdict | Evidence and route |
|---|---|---|---|
| BH-1 | Decoration project bypasses origin validation | medium | The restored-project branch explicitly skips the Decoration identity, so a matching identity under `references/` is accepted. The production-project boundary applies to this origin too. **patch**. |
| BH-2 | Decoration project bypasses restored direct-root validation | medium | The branch also skips all Decoration project package edges, admitting a baseline-only direct root supplied by an import. This weakens the direct-root rule for a production caller. **patch**. |
| BH-3 | Candidate injection does not solve dependency version requirements | low | Injection deliberately retains already-restored nodes and does not perform a NuGet restore. An incompatible candidate can pass this policy-only prediction, but an actual fresh restore rejects it before the production gate runs. Rejected: rare offline-helper limitation whose fix adds version-resolution logic beyond a direct correction. |
| BH-4 | Imported test dependencies bypass literal XML checks | medium | The real test caller reads csproj files and only `tests/Directory.Build.props`; another imported props/targets file can add forbidden roots or external projects unseen by that caller. **patch**, grouped with EC-1. |
| BH-5 | PackageReference Update/Remove becomes an empty identity | low | `Include` returns empty for these valid MSBuild item operations, causing a false unapproved-root failure. Direct correction: separate declarations from metadata updates/removals while retaining inline-version checks. **patch**. |
| BH-6 | Inactive XML declarations satisfy stale-direct guard | medium | The `direct` set is populated from literal XML without reconciling restored project roots. An inactive declaration can therefore claim a transitive package is an active direct root. **patch**. |
| BH-7 | Nested VersionOverride guard lacks an independent test | medium | Reviewer mutation removed nested VersionOverride handling and all 63 cases passed. Losing this guard admits inline pinning without failing the suite. **patch**: add exact-diagnostic case. |
| BH-8 | Enrolled-module test allowance lacks positive coverage | medium | Reviewer mutation removed the test-only caller's Modules allowance and all 63 cases passed. Tests could wrongly reject future enrolled module references. **patch**: add populated-Modules acceptance case. |
| BH-9 | Root project-reference loading lacks independent coverage | medium | Reviewer mutation disabled root project-reference edge loading and all 63 cases passed. Diagnostics can lose paths through local production projects. **patch**: assert an assets-loaded project path. |
| BH-10 | Restored library module-root restriction lacks coverage | medium | Reviewer mutation removed the root-project restriction and all 63 cases passed. Imported module roots in production libraries could become allowed. **patch**: assert rejection through a restored library node. |
| EC-1 | Imported test dependencies bypass the test gate | medium | Same caller omission as BH-4: only literal project XML and one props file are inspected. **patch**, grouped with BH-4. |
| EC-2 | Diagnostic paths stop at Decoration | medium | `paths` is also used to format failures for all restored nodes, so a rejected package reachable only through Decoration receives an invented direct path. Keep closure traversal stopped but trace complete diagnostic paths. **patch**. |
| VG-1 | Root assets framework parsing lacks regression coverage | medium | Pre-verified: removing `ReadFrameworks(framework)` left all 63 policy cases passing; the existing negative case constructs the node after parsing. **patch**: exercise assets Load through the gate. |
| VG-2 | Valid McpCli name outside src lacks negative coverage | medium | Pre-verified: weakening the location predicate to exclude only tests left all 63 cases passing. Existing external names already fail the name check. **patch**: cover source, restored, and test project-reference callers with an allowed name at a forbidden location. |

**Review fixes and final verification (2026-10-18):** Every patch-routed finding
above is fixed. The gate now validates Decoration project origins/direct roots,
checks effective test dependencies through MSBuild item evaluation without restore,
handles metadata operations separately from declarations, reconciles direct roots
with restored project edges, and traces full diagnostic paths. New regressions
cover every review gap, including nested VersionOverride, module test allowances,
assets-loaded root edges/frameworks, and valid project names outside src.

Final commands after the review fixes:
- `dotnet restore Hexalith.McpCli.slnx` — passed.
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` — passed, zero warnings/errors.
- `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` — 92 passed, zero failed/skipped (22.344 s).
- `git diff --check` — passed.

The final suite includes all 86 dependency-policy cases and every matrix-covering
case. The policy SHA-256 remained
`32d12675fbcaf979f75cedc7336af5a01354cb06eb7d09936c1fdd892a9d1d5a`.
Production policy values, src, references, and the frozen intent are unchanged.
