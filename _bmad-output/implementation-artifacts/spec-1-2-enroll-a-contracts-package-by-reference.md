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

### Review Findings

Code review 2026-09-24 (diff `01bd25d..45bd4b6`; layers: blind-hunter, edge-case-hunter, verification-gap, acceptance-auditor).

- [x] [Review][Patch] Replace the copied shipping-project test with proof from the real build (decision resolved 2026-09-24: option 4). Make the scaffold `Program.cs` read `ModuleAssemblyManifest.Entries`, so that removing the import breaks the real solution build; delete `ShippingProjectImportGeneratesFlaggedEntry` and `WriteShippingProject`; and give the fixture root a `Directory.Packages.props` with central package management, so fixture references are versionless like the real tool project. Combine this with the fixture-isolation patch below [tests/Hexalith.McpCli.Manifest.Tests/ManifestBuildTests.cs:215]
- [x] [Review][Patch] Design-time builds skip the generated manifest's `Compile` item, so IDE builds will report `ModuleAssemblyManifest` as undefined once the composition root uses it [src/Hexalith.McpCli/Build/ModuleAssemblyManifest.targets:73]
- [x] [Review][Patch] AC-2's repeated-build byte-stability check never runs with an unflagged reference present (the byte comparison happens only in the all-flagged phase) [tests/Hexalith.McpCli.Manifest.Tests/ManifestBuildTests.cs:56]
- [x] [Review][Patch] Fixture builds are not isolated from the ambient SDK and MSBuild configuration: there is no `global.json`, so the newest installed SDK builds them instead of the pinned 10.0.401, and `Directory.*` files in parent folders would be inherited [tests/Hexalith.McpCli.Manifest.Tests/ManifestBuildTests.cs:175]
- [x] [Review][Patch] The sort test cannot tell ordinal order from case-insensitive or culture-aware order, and the matrix's "reverse name order" pair (MarkedEmpty then Unmarked) is already in order [tests/Hexalith.McpCli.Manifest.Tests/ManifestBuildTests.cs:31]
- [x] [Review][Patch] The `*.Contracts.dll` filename filter is untested: the zero-match package puts its DLL under `tools/`, so removing the filter leaves every test green [tests/Hexalith.McpCli.Manifest.Tests/ManifestBuildTests.cs:83]
- [x] [Review][Patch] Case-insensitive package-ID matching is untested: every reference uses the packed ID's exact casing [tests/Hexalith.McpCli.Manifest.Tests/ManifestBuildTests.cs:205]
- [x] [Review][Patch] The manifest records `PackageReference.ItemSpec` casing rather than the resolved `NuGetPackageId`; `Include="pkg.a"` was confirmed to emit `("pkg.a", …)` [src/Hexalith.McpCli/Build/ModuleAssemblyManifest.targets:19]
- [x] [Review][Patch] The fixture Contracts projects are missing from the solution, unlike `Sample.Contracts`, so solution-wide format and the IDE skip them [Hexalith.McpCli.slnx:9]
- [x] [Review][Patch] The tool project has no note on the enrollment shape, and a reference that omits `HexalithContracts="true"` is silently left out [src/Hexalith.McpCli/Hexalith.McpCli.csproj:9]

**Rejected**

- false — Duplicate assembly name across two flagged packages: verified that the SDK's file-conflict resolution drops one copy, and the build fails with `'Pkg.B' has 0 matching`; no duplicate entry is emitted.
- false — Case-sensitive `.Contracts.dll` suffix: the build fails loudly, which enforces the declared `*.Contracts.dll` convention.
- false — Empty manifest not asserted: the solution build compiles the shipping project with an empty manifest (checked by building a zero-package probe), and CI builds the solution.
- false — Child build nodes keep pipes open and the stream reads hang: the suite runs to completion, so the streams reach EOF.
- low — Runtime-specific `runtimes/<rid>/lib` copies cause a false ambiguity: Contracts packages are pure managed code, the failure is loud, and the fix adds a filter.
- low — `AssemblyName.GetAssemblyName` throws on a native or corrupt DLL: the build still fails and the stale file is never compiled; this is unreachable for managed Contracts packages, and the fix adds try/catch.
- low — Non-boolean `HexalithContracts` values are silently ignored: unlikely, and the fix adds a validation branch.
- low — `Directory.Delete` after a failure can hide the assertion on Windows: CI is Linux, and the fix adds catch branches.
- low — The inline task recompiles on every build: performance only; the fix needs an Inputs/Outputs split.
- low — A `*.Contracts.dll` pulled in through a package dependency is untested: the `NuGetPackageId` filter is correct, and the fixture builder would need dependency support.
- low — An unflagged reference with no attribute is untested: missing metadata compares as `""` ≠ `"true"`, which is trivially correct.
- rejected (spec edit) — The spec status `done` versus sprint status `review`, `review_loop_iteration`, and the `last_updated` format: the fix edits the spec under review, and this workflow updates the sprint status.

Code review 2026-09-24, round 3 (diff `01bd25d..dccd5dd`; layers: blind-hunter, edge-case-hunter, verification-gap, acceptance-auditor).

- [x] [Review][Patch] The `RequireContractsFlag` branch has only one test input: a `*.Contracts` package with an explicit `HexalithContracts="false"`. Two regressions would pass unnoticed. First, rejecting every unflagged reference would break the build as soon as `Hexalith.EventStore.Client` is added. Second, rejecting only an explicit `"false"` would bring back silent non-enrollment when the attribute is left out. Fix: let `WriteProject` omit the attribute; with the flag on, require a successful build for an unflagged package whose ID does not end in `.Contracts`, and a failed build for a `*.Contracts` reference with no attribute [tests/Hexalith.McpCli.Manifest.Tests/ManifestBuildTests.cs:80]
- [x] [Review][Patch] The sort assertion cannot tell sorting by assembly name from sorting by package ID: in every fixture both orders agree, so changing the comparer to `x.PackageId` leaves the tests green. Give one flagged package an ID that sorts to the opposite end from its assembly name [tests/Hexalith.McpCli.Manifest.Tests/ManifestBuildTests.cs:44]
- [x] [Review][Patch] The fixture root writes `global.json` and `Directory.*` files but no `NuGet.config`. On a developer machine whose user-level config enables `packageSourceMapping`, `restore --source feed` fails with NU1100. Fix: write a `NuGet.config` that clears `packageSources`, `packageSourceMapping`, and `fallbackPackageFolders` [tests/Hexalith.McpCli.Manifest.Tests/ManifestBuildTests.cs:201]

**Rejected (round 3)**

- false — An unflagged direct `*.Contracts` reference (such as `Hexalith.EventStore.Contracts`) cannot be opted out, and this deviates from the matrix's "unflagged absent" row (blind-hunter, edge-case-hunter, verification-gap, acceptance-auditor): AD-15 limits direct production references to Abstractions, the EventStore client, flagged `*.Contracts` packages, and Stack packages. EventStore Contracts is transitive-only and is pinned through `CentralPackageTransitivePinningEnabled`, so the loud failure enforces the architecture. The fixture's matrix behavior is unchanged because the flag defaults to off.
- false — `ProjectReference` enrollment is unsupported and silently ignored (blind-hunter, edge-case-hunter): AD-4 defines enrollment by `PackageReference` and AD-15 forbids project references to Modules. The source-build seam concerns server source for the test AppHost, not the tool.
- false — An unflagged package with a non-`.Contracts` ID that ships a `*.Contracts.dll` is left out silently (edge-case-hunter): none of the unflagged direct roots AD-15 admits ships its own `*.Contracts.dll`, and EventStore Contracts is a separate package.
- false — The `ShippingProjectRequiresContractsFlag` test writes a `packages/` folder into the checkout (blind-hunter): `msbuild -getProperty` does not restore, so nothing is written.
- false — Child build nodes hold the redirected pipes, so `GetResult` blocks with no limit (edge-case-hunter): this repeats a finding already rejected in round 1. The suite completes locally and in CI.
- false / maybe-false — The design-time test is tautological and does not run IDE design-time targets (blind-hunter): the evaluation-time `-getItem:Compile` check is the intended regression guard for the static `Compile` item from the round-1 patch. Whether `CompileDesignTime` generates the file on a fresh clone cannot be checked with the Linux SDK; if it does not, the only effect is IDE errors until the first build.
- maybe-false — Inherited `MSBuild*` or `DOTNET_*` environment variables override the fixture's `global.json` (blind-hunter, part of the fixture-isolation finding): the fixture pins the same SDK the tests run on, and no mismatch has been observed; at worst the effect would be low.
- low — The build errors have no diagnostic codes (blind-hunter): cosmetic, and the messages already name the package and the count.
- low — The ambiguous-match error does not list the matched file paths (blind-hunter): the spec requires the package and the count, which the message already gives, and ambiguous packages are rare.
- low — Build servers left running can lock the temporary root on Windows (blind-hunter): CI runs on Linux; this repeats a rejection from round 1.
- low — The subprocess-heavy tests run in the unit lane (blind-hunter): they finish in bounded time, and a separate lane adds CI complexity.
- rejected (spec edit) — The Verification section omits `dotnet format`, `actionlint`, and the Abstractions run (blind-hunter); also the status mismatch between the commit message, the spec, and sprint status (edge-case-hunter): the fix edits the spec, and this workflow updates the status.

## Implementation Notes

- Added a non-packable, non-publishable executable scaffold. The production project has no Contracts package reference until decorated production packages are available.
- The build target matches flagged direct package IDs to copy-local Contracts DLLs, records package/assembly pairs in an ordinal manifest, and deletes stale output on a mismatch. Generated C# uses CRLF and is registered in MSBuild `FileWrites` for clean.
- Isolated package tests cover the decorated sample, marked-empty and unmarked assemblies, an unflagged package, zero and multiple matches, repeat builds, line endings, and clean behavior. Verification on 2026-09-24: solution restore and Release build succeeded with zero warnings; manifest tests passed 3/3; existing Abstractions tests passed 20/20; `git diff --cached --check` passed before the final spec update.
- Review fixes added the manifest test project to CI, isolated fixture package caches, validated DLL assembly identity, exercised the shipping project import and stale-output cleanup, and bounded concurrent subprocess output reads. Final local verification: solution restore and Release build succeeded with zero warnings; manifest tests passed 5/5; `actionlint .github/workflows/ci.yml` passed. The earlier 20/20 Abstractions result still applies; its source and tests did not change.
- Review loop fixes on 2026-09-24 made the real scaffold compile against the generated manifest, exposed generated source to design-time builds, required explicit flags for shipping Contracts references, preserved resolved package ID casing, and added fixture coverage for ordering, unflagged repeatability, DLL filtering, and case-insensitive package IDs. The fixture writes local SDK and MSBuild configuration with central package versions. The final review added assertions for design-time `Compile` membership and the shipping project's flag setting. Solution restore and Release build passed with zero warnings; manifest tests passed 6/6; Abstractions tests passed 20/20; `dotnet format Hexalith.McpCli.slnx --verify-no-changes --no-restore` passed.

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
| BH2-01: invalid flag on a differently named package | low — a non-boolean marker on a package whose ID does not end in `.Contracts` is ignored, but ordinary unflagged packages must be excluded and the previous review explicitly rejected adding value validation. The additional guard would add a branch for an unlikely authoring error. | reject |
| BH2-02: unreadable Contracts DLL leaves stale output | low — `AssemblyName.GetAssemblyName` can throw before the failure cleanup, but the build fails and managed Contracts packages normally contain readable assemblies. Catching this adds a failure branch for an unlikely corrupt package. | reject |
| BH2-03: concurrent writes to generated source | low — `File.WriteAllText` can expose a partial file to another independent build using the same `obj` directory. The generated file is small, and an atomic replacement adds cross-process file handling for an unlikely collision. | reject |
| BH2-04: mutable manifest array | false — the generated array is internal and the current consumer only reads it; no current caller mutates an entry, so the claimed changed result does not occur. | reject |
| BH2-05: design-time `Compile` membership untested | medium — the test checks only file existence after a design-time build, so excluding the generated file from `Compile` would pass while the IDE lacks the referenced type. | patch |
| BH2-06: shipping flag property untested | medium — the fixture passes `RequireContractsFlag=true` on its command line, so removal of the shipping project's property would leave tests green. | patch |
| BH2-07: no `dotnet pack` fixture | low — tests package compiled fixture DLLs into real NuGet archives and exercise restore/build, but cannot detect a future fixture project's pack-layout change. The fixture projects are test inputs, and invoking pack adds process complexity for an unlikely regression. | reject |
| EC2-01: unreadable Contracts DLL leaves stale output | low — the call to `AssemblyName.GetAssemblyName` precedes cleanup and can throw, but the build fails for corrupt managed package content. The previous review also rejected this unlikely failure path. | reject |
| VG2-01: design-time `Compile` membership untested | medium — verified gap: the test asserts generated file existence but never queries design-time `Compile` items, allowing the IDE regression to escape CI. | patch |
| VG2-02: shipping flag property untested | medium — verified gap: the fixture overrides the property, while the shipping solution has no Contracts reference to exercise its own property. | patch |

## Design Notes

Keep package resolution in the build target. The generated type should expose assembly names for the later composition root; it should not reflect over declarations or discover assemblies at runtime. A zero-flagged production build may generate an empty manifest until real decorated production Contracts packages are published.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` and `dotnet build Hexalith.McpCli.slnx --configuration Release` — solution builds with warnings as errors.
- `dotnet test tests/Hexalith.McpCli.Manifest.Tests/Hexalith.McpCli.Manifest.Tests.csproj --configuration Release` — isolated manifest cases pass.
- `git diff --check` — no whitespace damage.
