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

### Review Findings

Code review 2026-10-18 (range `3cd4d33..1064ec0`, code-only scope excluding `_bmad-output/` and `references/`, full mode; Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor). No layer failed. The Verification Gap layer ran 78 single-guard mutations on a scratch copy: 68 were caught, 7 survivors were equivalent or diagnostic-only, and 3 are reported below.

- [x] [Review][Patch] The real policy's exclusion of `Hexalith.Parties.Aspire` is not pinned — medium. The `Hexalith.Parties.Aspire` case of `TestProjectBoundaryRejectsUnapprovedItems` uses `Minimal()`, whose `TestPackages` is empty, so it duplicates the `Unexpected.Package` case; `NamedTestRootsAndSampleAreAllowedOnlyInTests` only asserts acceptance. A copied policy with `Hexalith.Parties.Aspire` added to `testPackages` left all 86 policy cases green. Run that case against `DependencyPolicy.Load` of the repository policy and keep the exact `Assert.Equal`. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:659]
- [x] [Review][Patch] A restored project node without a path is never exercised — medium. Every project node the tests build carries a `ProjectPath`, and the committed fixtures hold only packages. Mutating `node.ProjectPath is null ||` to accept a null path left all 86 cases green, and a pathless `External` project on the root edge stopped failing. Add an exact-diagnostic case expecting `["Production restore contains non-McpCli project External: Hexalith.McpCli > External"]`. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:210]
- [x] [Review][Patch] `CandidateInjectionKeepsExistingNodesAndVersions` hard-codes today's restored versions — low. `"1.4.2"` and `"3.124.0"` change on the next Builds bump that moves ByteAether.Ulid or EventStore.Contracts, failing a test whose behavior is still correct. The adjacent `Assert.Same` already proves retention; compare against the restored node or baseline pin and assert it differs from the fixture's 1.4.1 and 3.117.1. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:111; :113]
- [x] [Review][Patch] `RealCandidate` throws once Tenants or Parties is enrolled — low. `policy.Modules.Add` raises `ArgumentException` when Stories 4.8–4.10 add the real pin, so enrollment would also require a test edit, contrary to configuration-only enrollment. Use `TryAdd`, and add the flagged reference only when the module is not already enrolled. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:784]
- [x] [Review][Patch] Subset assertions hide extra or missing diagnostics — low. `ProjectsCandidateFailsOfflineWithDependencyPaths` checks only 2 of the 4 `Microsoft.AspNetCore.App` carriers (not `Hexalith.FrontComposer.Contracts.UI/4.5.0` or `Microsoft.AspNetCore.Authentication.OpenIdConnect/10.0.12`) and not the cross-module `Hexalith.Conversations.Contracts` edge the README says is rejected. `Assert.Contains` in `SourceProjectGuardsFailWithExactDiagnostics`, `InvalidContractsEnrollmentFails`, `BaselinePinsCannotBeMissingOrChanged(false)`, `TestOnlyPackagesCannotBeAllowlistedIntoProduction`, `TransitiveTestPackageFails`, `ModuleListsCannotOverlapStack`, `MultipleResolvedVersionsFail` and `RestoredExternalAndTestProjectsFail` already hides the duplicate `$(` diagnostic below. Assert the missing Projects lines, and assert the full failure list in the in-memory cases. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:43; :383]
- [x] [Review][Patch] An unresolved `$(` package include also reports an unapproved direct package — low. Unlike the `ProjectReference` branch, the `PackageReference` `$(` branch has no `continue`, so `<PackageReference Include="$(ExternalPackage)" />` also yields "has an unapproved direct package $(ExternalPackage)/unresolved". Add `continue;` and pin the single failure. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:78]
- [x] [Review][Patch] The Analyzers exemption matches any file named `Hexalith.McpCli.Analyzers.csproj` — low. It skips every source check, including the location check, so a probe at `src/Rogue/Hexalith.McpCli.Analyzers.csproj` with an inline version, a `references/` project reference and `Microsoft.AspNetCore.App` produced no failure. Match the full path `src/Hexalith.McpCli.Analyzers/Hexalith.McpCli.Analyzers.csproj`. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:21]
- [x] [Review][Patch] README overstates the test-only production rule — low. It says test packages "are rejected in production even if added to a production policy list", while `src/Hexalith.McpCli.Analyzers` uses the test package `Microsoft.CodeAnalysis.CSharp` (`PrivateAssets="all"`) under an exemption the README never mentions. State that the build-time analyzer project is excluded from the runtime root policy. [README.md:95]
- [x] [Review][Patch] Test projects are evaluated in Release only — low. `EvaluateReferences` passes only `-p:Configuration=Release`, so a package or `references/` project reference under `Condition="'$(Configuration)' == 'Debug'"` passes the test-project gate. Evaluate Debug and Release and check the union. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:724]
- [x] [Review][Patch] Two new allowances have no positive test — low. Removing the `<HexalithContracts>` child-element read or the Decoration Package allowance in `CheckTestProjects` left all 86 cases green; both fail closed. Add an element-form enrollment case and add `Hexalith.McpCli.Abstractions` to the approved list in `NamedTestRootsAndSampleAreAllowedOnlyInTests`. The Verification Gap layer filed `defer`; routed `patch` for parity with first-pass BH-8. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:90; :254]
- [x] [Review][Defer] Production `Reference`/`HintPath` and `PackageDownload` items are not inspected — medium. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:62] — deferred: pre-existing; neither the replaced test nor this gate reads these item types, and they never reach `project.assets.json`, so a DLL from `references/` would enter production unseen. Already tracked (`deferred-work.md:497`).
- [x] [Review][Defer] Per-project dependency direction is not enforced — medium. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:105] — deferred: pre-existing; `directPackages` is shared by every production project, so Abstractions adding `ModelContextProtocol` or Core adding `System.CommandLine` passes CI. Only `scripts/validate-release-packages.py:64` checks Abstractions, at release time. Already tracked (`deferred-work.md:500`).

#### Rejected

- `low` Decoration pin unchecked when Abstractions resolves as a project (AA, BH). By design: the spec accepts the decoration as a project or package. Dropping it breaks the build because Core references it, and a module requesting a newer Abstractions is decided by the real restore, which treats all warnings as errors (as first-pass BH-3).
- `low` Remaining guard sub-conditions without tests (AA, partial). `moduleNode.Type != "package"`, the direct-root reconciliation sub-conditions (mutants M24, M25, M25b equivalent) and `.Append(decoration)` in `CheckIntegrity`: removing any of them admits nothing, because the restored-project and test-only checks still fail the same inputs.
- `low` Synthetic paths in integrity, multiple-version and schema diagnostics (AA). A sibling restored-node failure carries the real path, a real assets file cannot hold two versions of one id, and a schema failure names no dependency.
- `false` README misstates what `baselinePackages` pins (AA, BH). Every restored package must carry a baseline, module or decoration pin or fail (`DependencyPolicyGate.cs:228-236`), so the restored closure is exactly pinned.
- `low` Lowercase MSBuild item elements bypass the XML checks (EC). Restore still honors them, and the restored-graph checks catch the resulting package, project or framework edge. A complete fix also needs case-insensitive attributes.
- `low` Missing dependency behind the decoration passes (EC). NuGet restore fails with NU1101 before the gate runs, and Abstractions has no package references.
- `low` RID-specific targets and the hard-coded `net10.0` key (EC, BH). The tool is framework-dependent with no RuntimeIdentifier, adding one is a reviewed change, and a TFM change fails loudly.
- `low` Candidate edges requesting versions above the retained nodes (EC). Same as first-pass BH-3: the real restore decides.
- `low` Release-only imported production package (EC). Literal conditional items are still read, so this needs a hidden imported props file.
- `false` `dotnet msbuild` output read can hang on a grandchild (EC). `-getItem` is evaluation-only: a piped run returned in 0.4 s and started no MSBuild worker node.
- `low` Empty `sampleContracts` accepted (EC). It requires a deliberate edit of the reviewed policy, which governs every list the same way.
- `low` Analyzer packages have no reviewed allowlist (BH, partial). The spec sanctions "Analyzers excluded", and the replaced test excluded it too.
- `low` Imported `PrivateAssets="all"` packages in libraries are invisible (BH). This needs a hidden imported props file, the restored graph covers every non-private package, and no src project declares one today.
- `low` Target-time test items and test-project closures (BH). The spec requires test roots only, and target-time items are contrived.
- `low` Test failures name the project rather than the imported file (BH). The evaluated project is named, which satisfies "names project and item".
- `low` Fallback paths for unreachable nodes (BH). Real assets do not produce unreachable nodes, and the wording is cosmetic.
- `low` Fixture provenance unchecked and not regenerable (BH). Provenance is documentary, and enrollment replaces the fixture checks with the real restore.
- `low` Policy byte-equality assertion is weak (BH). Harmless: no test writes the policy.
- `low` `DependencyPolicy.Load` is permissive (BH). A missing key fails loudly, duplicate object keys throw, and duplicate array entries are harmless.
- `low` Other README wording (BH, partial). The decoration-closure claim is false (see above), the `references/` sentence lists the allowed set accurately, and the missing injection caveat is cosmetic.
- `low` `Hexalith.EventStore.Contracts` hard-coded in the Contracts-root rule (BH). Pre-existing, and a new `*.Contracts` stack root already requires a PRD change.


**Review patch verification (2026-10-18):** All ten patch-routed findings above
are implemented. Regression cases now use the real policy for unpublished
Parties.Aspire rejection, reject pathless restored projects and misplaced analyzer
projects, accept child-element enrollment flags and test Decoration references,
and evaluate the union of Debug and Release test dependencies without restoring.
Shared imported roots produce one diagnostic. Candidate helpers retain restored
versions and existing module enrollment. The requested in-memory checks assert
complete failure lists, and the Projects fixture checks all four web-framework
carriers plus the cross-module Conversations edge. The README describes the
build-time analyzer exemption.

- `dotnet restore Hexalith.McpCli.slnx` — passed.
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` — passed, zero warnings/errors.
- `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` — 96 passed, zero failed/skipped (51.140 s), including all 90 dependency-policy cases.
- `git diff --check` — passed.

The dependency-policy SHA-256 before and after verification remained
`32d12675fbcaf979f75cedc7336af5a01354cb06eb7d09936c1fdd892a9d1d5a`.
No module was enrolled; policy, production source, references, and frozen intent
remain unchanged. The two pre-existing deferred findings remain tracked in the
existing ledger entries; no duplicate entries were added.

**Resumed build review (2026-10-18):** All three independent layers completed.
Edge Case Hunter returned no findings. Each remaining finding is classified below
before grouping; previously logged claims retain their verdict and disposition.

| ID | Finding | Verdict | Evidence and route |
|---|---|---|---|
| R2-BH-1 | Imported private production dependencies escape the root graph | low | Carried: same claim as the rejected imported `PrivateAssets="all"` finding above. The previous rejection and its route stand; no new ledger entry. |
| R2-BH-2 | Configuration-specific imported production dependencies escape the restored configuration | low | Carried: same claim as the rejected conditional imported production-package finding above. The previous rejection and its route stand. |
| R2-BH-3 | Candidate injection retains orphan fixture nodes after replacing shared versions | low | `WithCandidate` retains all fixture nodes while preserving restored shared nodes, so a synthetic shared package that dropped a dependency leaves an orphan. None of the committed candidate fixtures encounters this state. Rejected: uncommon helper limitation whose fix introduces pruning logic beyond a direct correction. |
| R2-BH-4 | An enrolled module replaces the historical candidate root under test | low | `TryAdd` and retained restored nodes deliberately preserve the actual enrolled pin. The current repo has no enrolled modules, and the real production gate independently checks future enrolled closures. Rejected: separating historical and enrolled candidate graphs adds helper state and branches for a future fixture concern; configuration-only enrollment was explicitly required by the preceding review. |
| R2-BH-5 | Source-reference diagnostic paths can omit the declaring project | low | The package lookup at `DependencyPolicyGate.cs:66` selects the globally shortest package path even when a library declares the offending reference. **patch**: construct source-reference paths through the declaring project's path and add an exact-diagnostic regression. |
| R2-BH-6 | Inline version metadata is compared case-sensitively | low | The XML checks use exact attribute/element names although MSBuild metadata is case-insensitive. The Builds override guard blocks restoration today, so this is policy-diagnostic consistency rather than a shipping bypass. **patch**: compare Version/VersionOverride metadata names case-insensitively and cover both attribute and child forms. |
| R2-BH-7 | Reference/HintPath and PackageDownload are not inspected | medium | Carried: same pre-existing limitation already deferred above and tracked (`deferred-work.md:497`). No duplicate ledger entry. |
| R2-BH-8 | Production project dependency direction is not enforced | medium | Carried: same pre-existing limitation already deferred above and tracked (`deferred-work.md:500`). No duplicate ledger entry. |
| R2-BH-9 | Fixture capture lacks a reproducible command | low | Carried: same claim as the rejected fixture-provenance/regeneration finding above. The previous rejection and its route stand. |
| R2-BH-10 | README omits the candidate version-resolution caveat | low | Carried: same claim as the rejected candidate-injection documentation finding above. The previous rejection and its route stand. |
| R2-VG-1 | Imported-dependency negatives bypass the actual discovery/evaluation wiring | medium | Pre-verified regression gap: the repository test chooses `EvaluateReferences` at line 36, while imported-props negatives build their own evaluated dictionary. Switching only that repository loader to literal XML leaves the negatives green. **patch**: share the directory-taking discovery/evaluation/check pipeline and exercise it with the existing imported-props negatives. |

**Final resumed-build verification (2026-10-18):** R2-BH-5, R2-BH-6, and
R2-VG-1 are fixed. Source diagnostics include their declaring project, inline
version metadata uses case-insensitive comparisons, and repository discovery and
the imported-props negatives use the same directory-taking pipeline. All tasks
and every matrix row remain covered by passing tests.

- `dotnet restore Hexalith.McpCli.slnx` — passed.
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` — passed, zero warnings/errors.
- `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` — 101 passed, zero failed/skipped (30.779 s), including all 95 dependency-policy cases.
- The same individual-project test command passed for Abstractions (20), Analyzers (19), Core (654), CLI (479), and MCP (58). Core and CLI each skipped two Windows-specific tests on Linux. Combined final results: 1,331 passed, four platform skips, zero failures.
- `python3 /tmp/mcpcli-story-4-7-mutations.py` — ten targeted mutations caught on an isolated copy. Baseline selected tests passed; replacing discovery evaluation with literal XML, dropping the declaring project from paths, restoring case-sensitive version checks, permitting pathless projects, removing child-element enrollment or test Decoration allowance, broadening the analyzer exemption, dropping the unresolved-reference continue, omitting Debug evaluation, and allowing Parties.Aspire each caused the expected regression test to fail. Logs: `/tmp/mcpcli-4-7-mutations-hnv8afmc/`.
- `git diff --check` — passed. Frozen intent, policy SHA-256, production source, and reference checkouts are unchanged from this resumed build's starting state. No modules were enrolled and no new deferrals were added.
- `npm ci` and the pinned `npx --no -- commitlint --verbose --edit /tmp/mcpcli-4-7-review-commit-message.txt` — passed; exact-message validation is preserved in [commitlint-review-validation.txt](evidence/story-4-7/commitlint-review-validation.txt).

### Review Findings (pass 2)

Code review 2026-10-18 (range `3cd4d33..447085c`, code-only scope excluding `_bmad-output/` and `references/`, full mode; Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor). No layer failed. The Verification Gap layer removed each of the 32 `failures.Add` guards in an isolated copy and every removal failed a test; of 15 condition-level mutants, 11 were caught and 3 of the 4 survivors were equivalent. 30 normalized findings: 8 survive as 1 decision, 2 patch and 1 defer entry; 22 are rejected. The production half of Blind Hunter's import finding is listed with the rejections, and its test half joins the decision. The decision resolved to a patch, and all three patches were applied on 2026-10-19: after a fresh restore and a `-warnaserror` Release build, the 103 Manifest.Tests pass, each new test fails when its guard is removed, and `tools/dependency-policy.json` is unchanged.

- [x] [Review][Decision] Test-project items behind a non-Configuration property toggle escape the test gate — medium. `EvaluateReferences` evaluates each test project only with `-p:Configuration=Debug` and `Release` (`tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:848-868`), and nothing scans items whose condition is inactive under those defaults. The Verification Gap layer added `<ItemGroup Condition="'$(UseHexalithProjectReferences)' == 'true'">` with a `references/Hexalith.EventStore/.../Hexalith.EventStore.Testing.csproj` project reference and `Hexalith.Parties.Aspire` to `tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj` in a copy: `RepositoryTestProjectsUseOnlyApprovedDependencies` passed; unconditional, the same items failed with two diagnostics. That toggle is the standard Hexalith source-build switch (109 uses under `references/`), and the README rule says tests cannot reference `references/` projects (VG, EC, BH). Options: (1) union each test csproj's literal declarations, conditions ignored, with the evaluated Debug/Release items — catches toggles in the project file; toggles hidden in an imported file stay a known limit, as for production; (2) add a third evaluation with `-p:UseHexalithProjectReferences=true` — also catches that toggle in imports, but names one ecosystem property and misses `$(Hexalith*FromSource)`, `$(OS)` and others; (3) both; (4) defer as a known limit. Resolved 2026-10-19: option 1, now a patch.
- [x] [Review][Patch] Scan each test csproj's literal `PackageReference` and `ProjectReference` declarations, conditions ignored, and union them with the evaluated Debug/Release items — medium. Keeps the evaluated items for imports and `$(...)` includes; a toggle hidden in an imported file stays a known limit, as for production. Add a test that a condition-gated `references/` project reference and an unapproved package in a test csproj fail (Decision above). [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:848]
- [x] [Review][Patch] The Decoration Package allowance for a production source `PackageReference` has no positive test — low. Deleting `&& !id.Equals(decoration, StringComparison.OrdinalIgnoreCase)` left all 95 policy cases green; `DecoratedCandidatePassesOffline(packagedDecoration: true)` swaps only the restored node, and the source projects still use a `ProjectReference` to Abstractions. The removal fails closed, but the spec accepts a packaged Decoration; add a `Minimal()` fact with `<PackageReference Include="Hexalith.McpCli.Abstractions" />` on the tool, a `Package(policy.DecorationPackage.Key, "1.0.0")` node, and an empty `Check` result (VG; parity with pass-1 allowance tests). [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:108]
- [x] [Review][Patch] README understates the test and analyzer allowances — low. The test sentence lists only the named test packages and the sample, but `CheckTestProjects` also admits `directPackages`, enrolled `modules` and the Decoration Package, and rejects baseline-only packages such as `Microsoft.Extensions.DependencyInjection` as test roots (`DependencyPolicyGate.cs:255-257`). The analyzer sentence names only `Microsoft.CodeAnalysis.CSharp`, while `src/Hexalith.McpCli.Analyzers` also uses `Microsoft.CodeAnalysis.Analyzers` with `PrivateAssets="all"`, and the exemption skips every source check for that project, not only the runtime root rule (`DependencyPolicyGate.cs:21`) (AA, BH, EC). [README.md:95]
- [x] [Review][Defer] A stale or missing `project.assets.json` is not detected [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:944] — deferred: pre-existing; the replaced test read the same file. A stale restore gives a local false pass or misleading "has no production reference" failures, the pitfall `CLAUDE.md` documents; CI restores fresh.

#### Rejected (pass 2)

- `low` Analyzer exemption skips project-reference, framework and inline-version checks (AA, EC). Pre-existing: the replaced test dropped every path under `Hexalith.McpCli.Analyzers/`. The Code Map sanctions "Analyzers excluded", pass 1 narrowed the exemption to the real path, and a netstandard2.0 Roslyn analyzer gaining a `references/` project is unlikely; narrowing the skip further adds a branch.
- `low` Test-project failures carry no version or path from `Hexalith.McpCli` (AA). The matrix requires "Names project and item", which they do. The fix is to re-scope the frozen Always sentence, which is a spec edit.
- `low` Duplicate top-level policy keys silently take the last value (BH). It needs a duplicated block in a reviewed file, visible in its diff. Rejecting duplicates and unknown keys adds guards. Pass 1's "duplicate object keys throw" covers keys inside a map only.
- `low` Unused `testPackages` entries have no stale-entry guard (BH). Task 1 mandates exactly those twelve names ahead of the live-topology stories, so a stale guard would require changing the spec.
- `low` Test-package closures and versions are not inspected (BH). Carried: pass 1 rejected test-project closures; the spec approves test roots only.
- `false` Test-side version overrides are invisible (BH). `references/Hexalith.Builds/Props/Directory.Packages.props:4` sets `CentralPackageVersionOverrideEnabled=false`, so `VersionOverride` fails restore with NU1013, and a `Version` attribute fails with NU1008 under central management. `tests/Hexalith.McpCli.ConformanceHost/Directory.Packages.props` adds only the sample's `PackageVersion`.
- `low` Production source checks read raw csproj XML only (BH, EC). Carried: R2-BH-1 and R2-BH-2. An imported or configuration-conditioned production item needs a hidden imported props file.
- `low` The policy-unchanged byte assertion cannot fail (BH). Carried: pass 1 rejected it as harmless.
- `low` `Hexalith.EventStore.Contracts` is hard-coded in the Contracts-root rule (BH). Carried: pass 1 rejected it as pre-existing; a new `*.Contracts` stack root needs a PRD change.
- `low` Fixture provenance cannot be reproduced and "captured closures prove" overstates (BH). Carried: pass 1 provenance and README-wording rejections and R2-BH-9. "Tenants- and Parties-shaped" already signals the simulated edge.
- `low` `EvaluateReferences` duplicates `ManifestBuildTests.RunDotnet` (BH). No caller diverges: a 60 s limit is ample for an evaluation-only call. Sharing one helper across two test classes is a refactor.
- `false` Case-sensitive path comparisons fail on Windows (BH). Every compared path is built from the same `root`. Source paths come from `Directory.EnumerateFiles` under it, and restored project paths join relative assets library paths to the tool directory. The only restore-recorded absolute path (`RestoredDependencyGraph.cs:37`) falls back to its file-name id, which equals the target id.
- `low` `HexalithContracts` set through `Update`, `ItemDefinitionGroup` or a lowercase metadata name escapes the gate (EC). Only the already-approved `Hexalith.EventStore.Contracts` can be enrolled this way: other `*.Contracts` roots fail as unapproved, and a group-wide flag makes the manifest task fail on non-Contracts packages (`src/Hexalith.McpCli/Build/ModuleAssemblyManifest.targets:37`). No package enters the closure, and handling `Update` and definition metadata adds guards.
- `low` A `GlobalPackageReference` in a src library escapes the source checks (EC). `NuGet.targets` converts it to `PrivateAssets="All"` without compile assets, so it never reaches the tool closure. Declaring one in a csproj is unusual, and catching it adds a guard; same class as pass 1's imported private-assets rejection.
- `low` Targets other than `net10.0` are ignored (EC). Carried: pass 1 rejected the RID-specific targets and the hard-coded TFM.
- `low` Candidate edges requesting versions above the retained nodes pass offline (EC, VG). Carried: pass 1 BH-3. The Verification Gap layer confirmed that no committed fixture requests more than what resolves.
- `low` Tenants and Parties candidate tests become vacuous once those modules are enrolled (BH, EC). Carried: R2-BH-4. Configuration-only enrollment was required.
- `low` A schema-2 policy without a version-one key throws `KeyNotFoundException` (EC). It fails loudly. Carried: pass 1's "a missing key fails loudly".
- `low` README's "every rejected dependency includes its path" overstates (EC). The sentence is in the paragraph about the production graph. Fallback paths are carried from pass 1's synthetic-path and unreachable-node rejections.
