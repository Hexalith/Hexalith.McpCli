---
title: 'Enroll a Contracts Package by Reference'
type: 'feature'
created: '2026-09-23'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '01bd25ded2e1e7bb34aab75a9cfed6f58ee2bb25'
context:
  - '_bmad-output/implementation-artifacts/epic-1-context.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The tool has no executable project or build-generated Contracts assembly list. A maintainer cannot enroll a Module by adding a package reference alone.

**Approach:** Add the minimal tool project and an MSBuild target that derives a compiled manifest from flagged direct package references after reference resolution. Prove the behavior with isolated packed Contracts fixtures.

## Boundaries & Constraints

**Always:** Match direct `PackageReference` items marked `HexalithContracts="true"` to `ReferenceCopyLocalPaths` by `NuGetPackageId`; count only that package's `*.Contracts.dll` assemblies. Require exactly one per flagged package and generate ordinally sorted assembly names under `obj`. Keep the tool untrimmed and the synthetic sample test-only. Follow .NET 10, central versions, warnings as errors, CRLF C#, and one type per C# file.

**Never:** Add production Module-specific source or runtime configuration, a handwritten assembly list, a folder scan, a sample fixture reference in the shipping tool, or a Catalog/CLI implementation before its story. Do not edit `references/` or publish the scaffold as a functional tool.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Valid enrollment | Two flagged Contracts packages in reverse name order; one unflagged | Generated source has one entry per flagged package, sorted ordinally; unflagged absent | N/A |
| Marker independence | Flagged marked-empty and flagged unmarked Contracts packages | Both assemblies appear; decoration and Operation count do not affect enrollment | N/A |
| Missing match | Flagged package with no `*.Contracts.dll` copy-local asset | Build fails and names package plus zero-match count | No generated manifest accepted |
| Ambiguous match | Flagged package with two `*.Contracts.dll` copy-local assets | Build fails and names package plus multiple-match count | No arbitrary selection |

</frozen-after-approval>

## Code Map

- `_bmad-output/planning-artifacts/epics.md:262` — Story 1.2 acceptance; `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md:76` — AD-4 target/loader boundary; `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md:199` — FR-5 and determinism. The Catalog and loader belong to later stories.
- `Hexalith.McpCli.slnx`, `Directory.Build.props`, `Directory.Packages.props`, `global.json`, `.editorconfig`, `.gitattributes` — existing solution, SDK/build policy, and C# line endings; extend rather than replace.
- `tests/Hexalith.McpCli.Sample.Contracts/` — existing decorated sample to pack only for tests; production project must not reference it. `tests/Directory.Build.props` supplies test framework packages for new `*.Tests` projects.
- `src/Hexalith.McpCli.Abstractions/` — dependency-free decoration package; leave its source and package references unchanged.

## Tasks & Acceptance

**Execution:**
- [x] `src/Hexalith.McpCli/Hexalith.McpCli.csproj`, `src/Hexalith.McpCli/Program.cs`, `Hexalith.McpCli.slnx` — add a buildable, untrimmed executable scaffold with no production Contracts reference or premature publication path.
- [x] `src/Hexalith.McpCli/Build/ModuleAssemblyManifest.targets` — run after `ResolveReferences`, match flagged package IDs to copy-local assets, reject zero/multiple Contracts DLLs, emit deterministic `obj/ModuleAssemblyManifest.g.cs`, and include it in compilation without duplicate entries on repeated builds.
- [x] `tests/Hexalith.McpCli.Manifest.Tests/Hexalith.McpCli.Manifest.Tests.csproj` and `ManifestBuildTests.cs` — create isolated local NuGet package/build fixtures, compare generated entries with flagged references, and exercise all matrix cases including repeated builds. Keep fixture outputs temporary.
- [x] `tests/fixtures/Manifest.MarkedEmpty.Contracts/Manifest.MarkedEmpty.Contracts.csproj` and `Module.cs`; `tests/fixtures/Manifest.Unmarked.Contracts/Manifest.Unmarked.Contracts.csproj` and `Placeholder.cs` — provide packaged marked-empty and unmarked inputs; reuse Sample.Contracts for the decorated case. Construct zero/multiple-assembly package variants in `ManifestBuildTests.cs` from these compiled assets.

**Acceptance Criteria:**
- Given a flagged `*.Contracts` package reference in the tool project, when `ResolveReferences` completes, then the generated C# manifest is compiled into the tool and contains that package's one Contracts assembly name.
- Given the isolated fixture's flagged and unflagged package references, when it builds on repeated runs, then generated bytes and flagged package/assembly equivalence remain stable with ordinal ordering.
- Given zero or multiple matching Contracts assemblies for a flagged package, when the target runs, then the build fails with the package identity and match count instead of using an incomplete manifest.
- Given the shipping solution, when restored and built, then it builds without a source-maintained scan list, folder loading, sample package dependency, or publishable stub tool.

## Implementation Notes

- Added a non-packable, non-publishable executable scaffold. The production project has no Contracts package reference until decorated production packages are available.
- The build target matches flagged direct package IDs to copy-local Contracts DLLs, records package/assembly pairs in an ordinal manifest, and deletes stale output on a mismatch. Generated C# uses CRLF and is registered in MSBuild `FileWrites` for clean.
- Isolated package tests cover the decorated sample, marked-empty and unmarked assemblies, an unflagged package, zero and multiple matches, repeat builds, line endings, and clean behavior. Verification on 2026-09-24: solution restore and Release build succeeded with zero warnings; manifest tests passed 3/3; existing Abstractions tests passed 20/20; `git diff --cached --check` passed before the final spec update.
- Review fixes added the manifest test project to CI, isolated fixture package caches, validated DLL assembly identity, exercised the shipping project import and stale-output cleanup, and bounded concurrent subprocess output reads. Final local verification: solution restore and Release build succeeded with zero warnings; manifest tests passed 5/5; `actionlint .github/workflows/ci.yml` passed. The earlier 20/20 Abstractions result still applies; its source and tests did not change.

## Spec Change Log

## Review Triage Log

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| BH-01: manifest tests absent from CI | medium — `.github/workflows/ci.yml` runs only Abstractions tests, so a broken target could merge with green CI. | patch |
| BH-02: shared NuGet cache | medium — the fixture reuses fixed IDs/version without setting `NUGET_PACKAGES`, so a machine's cached package can replace the archive under test. | patch |
| BH-03: DLL filename used as assembly identity | medium — package creation can rename the `.Contracts.dll` asset while retaining its internal assembly name; the target emits the filename and the planned assembly loader cannot rely on it. | patch |
| BH-04: shipping project import untested | medium — the fixture imports the target directly; removing the import from `Hexalith.McpCli.csproj` would leave all fixture tests green. | patch |
| BH-05: stale manifest failure path untested | low — zero/multiple-match tests begin without a manifest, so deletion of a previously generated file is unverified. | patch |
| BH-06: sequential pipe reads | low — `ReadToEnd` on stdout before stderr can block when the child fills stderr; the process helper must drain both streams together. | patch |
| EC-01: sequential pipe reads | low — same reachable pipe deadlock as BH-06 at `RunDotnet`; concurrent draining resolves both. | patch |
| EC-02: child process has no timeout | low — a hung restore or build leaves the test process waiting indefinitely; bound the subprocess and kill it on expiry. | patch |
| EC-03: imported target path is not XML escaped | low — an ampersand or quote in the checkout path breaks the generated fixture project before the target is tested. | patch |
| EC-04: global NuGet cache persists fixtures | medium — the test deletes its temporary root but NuGet writes fixed fixture IDs to the global cache; same root cause as BH-02. | patch |
| VG-01: manifest tests absent from CI | medium — the normal CI lane lists only Abstractions tests; manifest regression is not exercised. | patch |
| VG-02: shipping project import untested | medium — the checked fixture directly imports the target and the shipping project's unused generated type does not prove its import. | patch |

## Design Notes

Keep package resolution in the build target. The generated type should expose assembly names for the later composition root; it should not reflect over declarations or discover assemblies at runtime. A zero-flagged production build may generate an empty manifest until real decorated production Contracts packages are published.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` and `dotnet build Hexalith.McpCli.slnx --configuration Release` — solution builds with warnings as errors.
- `dotnet test tests/Hexalith.McpCli.Manifest.Tests/Hexalith.McpCli.Manifest.Tests.csproj --configuration Release` — isolated manifest cases pass.
- `git diff --check` — no whitespace damage.
