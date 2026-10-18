---
title: '4.7 Enforce the production dependency boundary'
type: 'feature'
created: '2026-10-18'
status: 'in-progress'
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

- [ ] [Review][Patch] The real policy's exclusion of `Hexalith.Parties.Aspire` is not pinned — medium. The `Hexalith.Parties.Aspire` case of `TestProjectBoundaryRejectsUnapprovedItems` uses `Minimal()`, whose `TestPackages` is empty, so it duplicates the `Unexpected.Package` case; `NamedTestRootsAndSampleAreAllowedOnlyInTests` only asserts acceptance. A copied policy with `Hexalith.Parties.Aspire` added to `testPackages` left all 86 policy cases green. Run that case against `DependencyPolicy.Load` of the repository policy and keep the exact `Assert.Equal`. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:659]
- [ ] [Review][Patch] A restored project node without a path is never exercised — medium. Every project node the tests build carries a `ProjectPath`, and the committed fixtures hold only packages. Mutating `node.ProjectPath is null ||` to accept a null path left all 86 cases green, and a pathless `External` project on the root edge stopped failing. Add an exact-diagnostic case expecting `["Production restore contains non-McpCli project External: Hexalith.McpCli > External"]`. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:210]
- [ ] [Review][Patch] `CandidateInjectionKeepsExistingNodesAndVersions` hard-codes today's restored versions — low. `"1.4.2"` and `"3.124.0"` change on the next Builds bump that moves ByteAether.Ulid or EventStore.Contracts, failing a test whose behavior is still correct. The adjacent `Assert.Same` already proves retention; compare against the restored node or baseline pin and assert it differs from the fixture's 1.4.1 and 3.117.1. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:111; :113]
- [ ] [Review][Patch] `RealCandidate` throws once Tenants or Parties is enrolled — low. `policy.Modules.Add` raises `ArgumentException` when Stories 4.8–4.10 add the real pin, so enrollment would also require a test edit, contrary to configuration-only enrollment. Use `TryAdd`, and add the flagged reference only when the module is not already enrolled. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:784]
- [ ] [Review][Patch] Subset assertions hide extra or missing diagnostics — low. `ProjectsCandidateFailsOfflineWithDependencyPaths` checks only 2 of the 4 `Microsoft.AspNetCore.App` carriers (not `Hexalith.FrontComposer.Contracts.UI/4.5.0` or `Microsoft.AspNetCore.Authentication.OpenIdConnect/10.0.12`) and not the cross-module `Hexalith.Conversations.Contracts` edge the README says is rejected. `Assert.Contains` in `SourceProjectGuardsFailWithExactDiagnostics`, `InvalidContractsEnrollmentFails`, `BaselinePinsCannotBeMissingOrChanged(false)`, `TestOnlyPackagesCannotBeAllowlistedIntoProduction`, `TransitiveTestPackageFails`, `ModuleListsCannotOverlapStack`, `MultipleResolvedVersionsFail` and `RestoredExternalAndTestProjectsFail` already hides the duplicate `$(` diagnostic below. Assert the missing Projects lines, and assert the full failure list in the in-memory cases. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:43; :383]
- [ ] [Review][Patch] An unresolved `$(` package include also reports an unapproved direct package — low. Unlike the `ProjectReference` branch, the `PackageReference` `$(` branch has no `continue`, so `<PackageReference Include="$(ExternalPackage)" />` also yields "has an unapproved direct package $(ExternalPackage)/unresolved". Add `continue;` and pin the single failure. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:78]
- [ ] [Review][Patch] The Analyzers exemption matches any file named `Hexalith.McpCli.Analyzers.csproj` — low. It skips every source check, including the location check, so a probe at `src/Rogue/Hexalith.McpCli.Analyzers.csproj` with an inline version, a `references/` project reference and `Microsoft.AspNetCore.App` produced no failure. Match the full path `src/Hexalith.McpCli.Analyzers/Hexalith.McpCli.Analyzers.csproj`. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:21]
- [ ] [Review][Patch] README overstates the test-only production rule — low. It says test packages "are rejected in production even if added to a production policy list", while `src/Hexalith.McpCli.Analyzers` uses the test package `Microsoft.CodeAnalysis.CSharp` (`PrivateAssets="all"`) under an exemption the README never mentions. State that the build-time analyzer project is excluded from the runtime root policy. [README.md:95]
- [ ] [Review][Patch] Test projects are evaluated in Release only — low. `EvaluateReferences` passes only `-p:Configuration=Release`, so a package or `references/` project reference under `Condition="'$(Configuration)' == 'Debug'"` passes the test-project gate. Evaluate Debug and Release and check the union. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:724]
- [ ] [Review][Patch] Two new allowances have no positive test — low. Removing the `<HexalithContracts>` child-element read or the Decoration Package allowance in `CheckTestProjects` left all 86 cases green; both fail closed. Add an element-form enrollment case and add `Hexalith.McpCli.Abstractions` to the approved list in `NamedTestRootsAndSampleAreAllowedOnlyInTests`. The Verification Gap layer filed `defer`; routed `patch` for parity with first-pass BH-8. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:90; :254]
- [x] [Review][Defer] Production `Reference`/`HintPath` and `PackageDownload` items are not inspected — medium. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:62] — deferred: pre-existing; neither the replaced test nor this gate reads these item types, and they never reach `project.assets.json`, so a DLL from `references/` would enter production unseen.
- [x] [Review][Defer] Per-project dependency direction is not enforced — medium. [tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:105] — deferred: pre-existing; `directPackages` is shared by every production project, so Abstractions adding `ModelContextProtocol` or Core adding `System.CommandLine` passes CI. Only `scripts/validate-release-packages.py:64` checks Abstractions, at release time.

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
