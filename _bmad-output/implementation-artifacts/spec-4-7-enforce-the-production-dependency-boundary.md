---
title: '4.7 Enforce the production dependency boundary'
type: 'feature'
created: '2026-10-18'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
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
- [ ] `tools/dependency-policy.json` -- add `testPackages` (above names) and
  `sampleContracts`. Keep schemaVersion 1.
- [ ] `tests/Hexalith.McpCli.Manifest.Tests/{DependencyPolicy,RestoredDependencyGraph,DependencyPolicyGate}.cs`
  -- policy model; graph loaded from assets with deterministic first-path tracking
  and candidate injection (existing nodes keep their restored version); gate
  covering the Boundaries rules, stale direct entries, missing pins, and policy
  integrity (no overlap between test and production lists). One type per file.
- [ ] `tests/Hexalith.McpCli.Manifest.Tests/Fixtures/*.closure.json` -- capture the
  real Projects 1.0.0 closure; add Tenants 5.8.0 and Parties 1.4.0 closures, each
  with the simulated `Hexalith.McpCli.Abstractions` dependency.
- [ ] `tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs` -- real-repo
  production and test-project gates, plus one in-memory test per guard and matrix
  row. Assert exact failure strings.
- [ ] `README.md` "Gateway boundary" -- document the gate, test-only allowances,
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
