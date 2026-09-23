---
title: 'Declare a Module and Its Operations'
type: 'feature'
created: '2026-09-23'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'b410fcd17f38b6441e9dfc0c18cb9668ea4ba2e3'
context:
  - '_bmad-output/implementation-artifacts/epic-1-context.md'
  - '_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Module authors have no buildable decoration contract or synthetic example with which to declare agent-facing Commands and Queries. The repository also lacks the structural seed needed to build, check, and later release that contract.

**Approach:** Add the flat .NET 10 Abstractions package, one synthetic Contracts fixture, focused tests, and the approved build and delivery scaffold. Keep discovery and execution for later stories.

## Boundaries & Constraints

**Always:** Match PRD §5.1 and the architecture spine: assembly-level `HexalithModule(name, description, IdentifierKind)` with `FixedTenant`, `WireTypeConvention`, and `Type? SerializerOptionsProvider`; required description constructors for `HexalithCommand` and `HexalithQuery` with their documented optional routing, identity, example, and envelope-member properties; property-level `HexalithIdentifier`; `IdentifierKind` values `Ulid` and `String`. Abstractions has no consumer-visible package dependencies. The sample is test-only and declares exactly one `Ulid` Module. Use the pinned SDK, central versions, warnings as errors, one C# type per file, and `.slnx` only.

**Never:** Add module-specific production code, a Catalog or executor, generated per-operation commands/tools, plugin loading, a legacy `.sln`, or references to sibling implementation layers. Do not edit `references/`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Name part | `TLSConfigCommand` | `tls-config`; strip only the trailing `Command` | N/A |
| Boundaries | acronym, lower-to-upper, digit-to-upper, interior `Command`/`Query` | ASCII lowercase kebab parts; digits stay attached; interior text remains | N/A |
| Package consumer | Contracts project references Abstractions | Assembly, operation, and identifier decorations compile | No extra package dependencies in packed Abstractions |

</frozen-after-approval>

## Code Map

- `_bmad-output/planning-artifacts/epics.md:222` — Story 1.1 acceptance; `_bmad-output/implementation-artifacts/sprint-status.yaml:39` — tracking key `1-1-declare-a-module-and-its-operations`.
- `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md:122` — authoritative decoration members; `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md:188` — names, kebab rule, fixture, seed, and release phases.
- `references/Hexalith.Builds/global.json` and `Props/Directory.Packages.props` — SDK and central pins; `references/Hexalith.Tenants/Directory.Build.props`, `Directory.Packages.props`, `tests/Directory.Build.props`, `package.json`, `commitlint.config.mjs`, `.releaserc.json`, and `.github/workflows/` — patterns to adapt, never edit here.
- `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Commands/ICommandContract.cs` and `Queries/IQueryContract.cs` — interface-routed fixture shape; sample may depend on Contracts, Abstractions may not.
- Existing `.github/workflows/agent-instructions-sync.yml` remains; root has no product solution or build configuration yet.

## Tasks & Acceptance

**Execution:**
- [x] `global.json`, `Directory.Build.props`, `Directory.Packages.props`, `tests/Directory.Build.props`, `Hexalith.McpCli.slnx` — create pinned, flat, warning-as-error solution; copy the Builds SDK file and use three-path central import.
- [x] `src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj` and `src/Hexalith.McpCli.Abstractions/{HexalithModuleAttribute,HexalithCommandAttribute,HexalithQueryAttribute,HexalithIdentifierAttribute,IdentifierKind,WireTypeConvention,KebabCase}.cs` — implement public decorations and naming with exact PRD members; one type per file.
- [x] `tests/Hexalith.McpCli.Sample.Contracts/Hexalith.McpCli.Sample.Contracts.csproj` and its `*.cs` files — declare one Module with interface- and attribute-routed Commands, a converter-backed value-object identifier, and a Query; reference allowed Contracts and Abstractions only.
- [x] `tests/Hexalith.McpCli.Abstractions.Tests/Hexalith.McpCli.Abstractions.Tests.csproj` and `KebabCaseTests.cs` — test the matrix, sample's single Module, and routing forms.
- [x] `package.json`, `commitlint.config.mjs`, `.releaserc.json`, `tools/release-packages.json` — pin sibling Conventional Commits tooling, use one `v<version>` semantic-release path, and declare exactly Abstractions plus tool package IDs for the later paired release.
- [x] `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `.github/workflows/commitlint.yml` — add thin shared CI/commitlint calls and a release path that can bootstrap Abstractions alone before paired publishing; defer later live gates without claiming they pass now.

**Acceptance Criteria:**
- Given a checkout with root-declared Builds, when `dotnet restore` and Release build run on `Hexalith.McpCli.slnx`, then Abstractions, Sample.Contracts, and tests build under SDK 10.0.401 with central versions and warnings as errors.
- Given a Contracts consumer, when it applies the Module, Command, Query, and Identifier decorations with required descriptions and kind, then it compiles and the packed Abstractions package declares no package dependencies.
- Given the synthetic sample, when its declarations are inspected or tested, then it has exactly one `Ulid` Module, both Command routing forms, a converter-backed identifier, and a Query, with no production project depending on it.
- Given the seeded delivery files, when inspected, then CI calls Builds `domain-ci.yml`, release permits an Abstractions-only bootstrap and defines the later paired path, and commitlint and semantic-release use the pinned single-version policy.

### Review Findings

Code review of 2026-09-23 (`b410fcd..0a7079c`, excluding `package-lock.json`; layers: Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor; none failed).

All 8 patches applied and reverified on 2026-09-23: Release solution build with zero warnings, 20 tests passed with zero skipped, `release-prepare.sh` bootstrap run with package validation, preflight rejects `paired` and invalid versions, `actionlint`, `bash -n`, and `git diff --check`. Note: recovery runs the scripts at the tag, so only tags cut after this change get the idempotent `--skip-duplicate` push.

- [x] [Review][Patch] A failed NuGet push leaves an orphan release tag; add a `workflow_dispatch` recovery workflow (adapted from Tenants `recover-partial-release.yml`) that republishes an existing `v<version>` tag with `--skip-duplicate` and creates any missing GitHub release (decision resolved 2026-09-23: option 1) [scripts/release-publish.sh:9]
- [x] [Review][Patch] CI bootstrap job bypasses the release scripts that production runs; run `release-prepare.sh` and assert that preflight rejects `paired` [.github/workflows/ci.yml:38]
- [x] [Review][Patch] No test pins single-suffix stripping (`SaveQueryCommand` → `save-query`, `FindCommandQuery` → `find-command`) [tests/Hexalith.McpCli.Abstractions.Tests/KebabCaseTests.cs:19]
- [x] [Review][Patch] `actions/setup-node@v7.0.0` is pinned by tag in the publish job that holds `contents: write` and `NUGET_API_KEY`; pin it to `820762786026740c76f36085b0efc47a31fe5020`, as in Builds `domain-release.yml` [.github/workflows/release.yml:69]
- [x] [Review][Patch] Test packages and `IsTestProject` are conditioned on one exact project name, so later `*.Tests` projects get no framework [tests/Directory.Build.props:6]
- [x] [Review][Patch] Sample fixture tests live in `KebabCaseTests`; move them to `SampleContractsTests.cs` [tests/Hexalith.McpCli.Abstractions.Tests/KebabCaseTests.cs:54]
- [x] [Review][Patch] XML docs omit PRD constraints: `AggregateId` cannot be combined with `AggregateIdProperty`, and the `Name` override is ASCII lowercase kebab-case [src/Hexalith.McpCli.Abstractions/HexalithQueryAttribute.cs:29]
- [x] [Review][Patch] Release gates fail without printing a reason (the `test` ref/SHA checks and the version regex) [.github/workflows/release.yml:35]
- [x] [Review][Defer] `KebabCase` uses `ThrowIfNullOrWhiteSpace` and range slicing, so it cannot be linked into the `netstandard2.0` analyzer that the architecture says shares it [src/Hexalith.McpCli.Abstractions/KebabCase.cs:17] — deferred: the Story 1.7 analyzer must choose linked source or multi-targeting and add a `netstandard2.0` compile check
- [x] [Review][Defer] Preflight will still accept `bootstrap` after paired releases exist, which would split the shared version line [scripts/release-preflight.sh:9] — deferred: unreachable while `paired` fails closed; the paired-release story must reject bootstrap once `Hexalith.McpCli` is published
- [x] [Review][Defer] The architecture's Code style row requires a StyleCop header, but no new file has one and neither does sibling Tenants [src/Hexalith.McpCli.Abstractions/HexalithModuleAttribute.cs:1] — deferred: the fix is either amending the architecture spine or adopting headers repo-wide; that is a planning decision
- [x] [Review][Defer] No rule or diagnostic rejects a non-canonical `Name` override or module name, for example `a.b`, which breaks the `<module>.<operation>` split [src/Hexalith.McpCli.Abstractions/HexalithModuleAttribute.cs:10] — deferred: planning gap for the Catalog diagnostics stories (1.4/1.5); nothing consumes names yet
- [x] [Review][Defer] No diagnostic category covers a type that carries both `[HexalithCommand]` and `[HexalithQuery]` [src/Hexalith.McpCli.Abstractions/HexalithCommandAttribute.cs:7] — deferred: planning gap for Stories 1.4/1.5; the read-only filter depends on an unambiguous kind

**Rejected**

- `false` — IPv6AddressQuery → `i-pv6-address`: this is what the architecture's specified split rule produces.
- `false` — throw on empty Command description in the attribute constructor: PRD FR-1 assigns this to the analyzer and a startup diagnostic, and throwing would break reflection during Catalog build.
- `false` — throw on empty Query description: same refutation as the Command description.
- `false` — out-of-range `IdentifierKind`/`WireTypeConvention` casts: nothing consumes them yet, and Catalog validation owns declaration errors.
- `false` — both `AggregateId` and `AggregateIdProperty` set: the Catalog's `ambiguous_aggregate_id` category owns this.
- `low` — `default(SampleItemId)` makes `AggregateId` null: test fixture only, never constructed that way, and the fix adds a guard.
- `false` — converter accepts non-ULID strings: identifier-kind validation belongs to Schema and PayloadValidator (FR-7/FR-15), not to the Module converter.
- `low` — missing Builds submodule skips imports silently: restore still fails with NU1010 naming the packages, the import copies the sibling pattern, and the fix adds a guard target.
- `false` — shared workflows referenced `@main`: identical to sibling Tenants `ci.yml`/`commitlint.yml`.
- `low` — no test forbids production references to Sample.Contracts: true today, and enforcing it needs new architecture-test infrastructure.
- `low` — no tests for `AttributeUsage` flags or the `Explicit` default: static metadata that is unlikely to regress in everyday work.
- `low` — spec `status: done` vs sprint `review`: the fix would edit the spec under review; "12 passed" and "18 tests" are labelled sequential runs.
- `low` — validator skips packed README/XML and there is no SourceLink/`ContinuousIntegrationBuild`: publishing works, and the fix adds configuration.
- `false` — README describes a product that does not exist yet: it describes the repository's product, and the provider contract is documented on `SerializerOptionsProvider`.
- `low` — no coverage collection: with `run-coverage-gate` defaulting to false, no `--coverage` argument is passed, so nothing breaks; adopting a gate is a separate policy choice.
- `false` — workflows are not "thin": the frozen task scopes "thin" to the CI/commitlint calls, and the bootstrap-consumer job came from the earlier review (BH-04/VG-01).
- `false` — paired path is only a stub: the spec explicitly defers paired gates, and preflight fails closed.
- `low` — tracking status mismatch (Acceptance Auditor): the fix would edit the spec under review.

## Implementation Notes

- Added `.editorconfig` and `.gitattributes` so C# remains CRLF in the workspace while Git stores normalized text and `git diff --check` passes.
- The paired release phase fails closed until its tool project and later publication gates exist; the Abstractions-only bootstrap path builds and validates one package.
- Verified `dotnet restore Hexalith.McpCli.slnx`, Release solution build (zero warnings), the focused test project (12 passed, zero skipped), Abstractions pack and release package validator, and a temporary Contracts consumer build against the packed package (zero warnings). The package lock matches `package.json`; the implementation agent also ran `npm ci`, `actionlint`, and shell syntax checks.
- Review fixes reject invalid canonical names and default sample IDs, document the decorations, build a staged-package consumer in CI, require the package DLL, check NuGet version availability, and verify exact-source commitlint and `main` after release approval. Reverification passed: Release build with zero warnings, 18 tests with zero skipped, package validation, `actionlint`, shell syntax, and `git diff --check`.
- The exact local commit message `feat: Add module decorations and release scaffold` passed `npx --no -- commitlint --edit /tmp/mcpcli-story-1-1-commit-message.txt` with exit code 0 on 2026-09-23.

## Spec Change Log

## Review Triage Log

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| BH-01: unsupported name characters | medium — `KebabCase.Convert` copies legal CLR `_` and non-ASCII characters, so a future Catalog caller receives a noncanonical name. | patch |
| BH-02: suffix-only type | medium — `FromTypeName("Command")` and `("Query")` return empty strings, which cannot be an operation name part. | patch |
| BH-03: package readme | medium — the packed root README only names the project; a Contracts author gets no declaration example from the package. | patch |
| BH-04: CI package consumer | high — CI validates metadata but never restores a Contracts consumer from the staged package; project-reference tests cannot detect an unusable package. | patch |
| BH-05: package asset | high — the validator checks nuspec ID/version/dependencies but accepts a package without a `lib/net10.0` Abstractions DLL. | patch |
| BH-06: manifest path drift | low — hardcoded pack paths currently match both manifest entries; only a later edit could diverge, and dynamic packaging adds complexity to a disabled paired phase. Rejected. | reject |
| BH-07: stale staging | low — a stale package makes validation fail safely before publication; automatic deletion of staging is more intrusive than this local retry inconvenience. Rejected. | reject |
| BH-08: occupied NuGet version | high — preflight validates syntax and credentials but does not check whether the selected package version already exists; NuGet publication can fail after release preparation. | patch |
| BH-09: source moves during approval | high — `verify-source` runs before the protected environment wait; the publish job does not recheck the current `main` SHA. | patch |
| BH-10: commitlint gate | medium — the source check requires successful CI but has no exact-SHA commitlint check, so a failing commitlint push can reach release. | patch |
| BH-11: semantic-release no-op | false — semantic-release deliberately succeeds without publication when no releasable commit exists; the workflow makes no package-success assertion to another caller. | reject |
| BH-12: paired partial push | false — `release-preflight.sh` rejects every paired release before prepare or publish, so the two-push path is unreachable in this story. | reject |
| EC-01: unsupported name characters | medium — the same legal CLR input in BH-01 flows through the unchanged `Convert` loop and remains invalid. | patch |
| EC-02: suffix-only type | medium — the same empty output in BH-02 is returned explicitly at `KebabCase.cs:55`. | patch |
| EC-03: default sample identifier | low — `default(SampleItemId).Value` is null, so the converter writes JSON null while its reader rejects null; a direct guard can keep the fixture symmetric. | patch |
| EC-04: commitlint gate | medium — the same release source check in BH-10 omits commitlint's exact-SHA result. | patch |
| VG-01: package consumer | high — the verification reviewer reproduced a metadata-valid package that fails consumer restore with `NU1212`; the checked CI path cannot catch it. | patch |

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` and `dotnet build Hexalith.McpCli.slnx --configuration Release` — solution succeeds.
- `dotnet test tests/Hexalith.McpCli.Abstractions.Tests/Hexalith.McpCli.Abstractions.Tests.csproj --configuration Release` — focused behavior passes.
- `dotnet pack src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj --configuration Release` — inspect `.nuspec` for no dependency entries.
