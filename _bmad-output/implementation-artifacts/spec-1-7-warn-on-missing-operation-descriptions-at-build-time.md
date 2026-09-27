---
title: 'Warn on Missing Operation Descriptions at Build Time'
type: 'feature'
created: '2026-09-27'
status: 'done'
baseline_commit: '93fc1125e79c1b87a47a52f4e70d92b80e004372'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Contracts author can leave a decorated Command or Query description empty and learn only when the Catalog excludes the Operation at startup.

**Approach:** Bundle a Roslyn analyzer in `Hexalith.McpCli.Abstractions` so the consuming Contracts build warns at the decorated class or record. Keep startup validation as the runtime backstop.

## Boundaries & Constraints

**Always:** Warn for empty or whitespace descriptions on `[HexalithCommand]` and `[HexalithQuery]`; accept nonblank descriptions and ignore unrelated declarations. Identify decorations by their fully qualified attribute symbols, including normal `Attribute` suffix omission. Pack the separate `netstandard2.0` analyzer under `analyzers/dotnet/cs` in the one Abstractions package; keep Roslyn dependencies private and the package's consumer dependency list empty. Link the existing `KebabCase` source into the analyzer and make it compile for `netstandard2.0`, preserving its current conversion behavior.

**Never:** Make the analyzer a second package reference, change Catalog diagnostic categories or runtime exclusion, add Module-specific rules, or make existing intentionally invalid Contracts fixtures fail the solution build.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Missing description | Decorated class or record with `""`, whitespace, or a compile-time constant of either | One warning on the type declaration | Catalog still excludes at startup |
| Valid description | Either decoration with a nonblank constant | No description warning | None |
| Unrelated type | Undecorated type, or another attribute named like a Hexalith decoration | No description warning | None |
| Package consumer | Contracts project references only the packed Abstractions package | Analyzer loads automatically and reports the warning | No extra NuGet dependency |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Abstractions/{HexalithCommandAttribute,HexalithQueryAttribute}.cs` — positional `string description` and exact attribute metadata names; leave public API intact.
- `src/Hexalith.McpCli.Abstractions/KebabCase.cs` — existing Catalog naming helper; link its source into the analyzer and replace net10-only calls while retaining its tests and behavior.
- `src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj` — add analyzer build dependency and pack its DLL at `analyzers/dotnet/cs`; runtime library remains free of package references.
- `src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:180` — existing `missing_description` runtime exclusion; do not modify.
- `Directory.Build.props`, `Directory.Packages.props`, `.editorconfig`, `.gitattributes` — inherited net10/warnings-as-errors, central Roslyn 5.9.0 pins, and CRLF C# source rules.
- `tests/fixtures/Catalog.Invalid.Contracts/MissingDescriptionQuery.cs` — intentionally invalid runtime fixture; avoid attaching analyzer to every project reference.
- `Hexalith.McpCli.slnx` and `tests/Directory.Build.props` — register new analyzer and test projects using current test conventions.

## Tasks & Acceptance

**Execution:**
- [x] `src/Hexalith.McpCli.Analyzers/Hexalith.McpCli.Analyzers.csproj` — create a private-dependency `netstandard2.0` Roslyn component, link `KebabCase.cs`, and enforce analyzer rules.
- [x] `src/Hexalith.McpCli.Analyzers/MissingOperationDescriptionAnalyzer.cs` — inspect decorated named types semantically and report one stable warning at each blank description declaration.
- [x] `src/Hexalith.McpCli.Abstractions/KebabCase.cs` — make the shared source compile on `netstandard2.0` without changing conversion results.
- [x] `src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj` — build then pack the analyzer DLL; do not expose its dependencies.
- [x] `tests/Hexalith.McpCli.Analyzers.Tests/{Hexalith.McpCli.Analyzers.Tests.csproj,MissingOperationDescriptionAnalyzerTests.cs}` — cover the matrix, diagnostic location, symbol matching, and no false warning for valid text.
- [x] `Hexalith.McpCli.slnx` — include the analyzer and its tests so the Release solution build exercises the netstandard compile check.

**Acceptance Criteria:**
- Given one reference to the packed Abstractions package, when a Contracts consumer builds a blank-described decorated type, then it receives the warning without adding an analyzer package reference.
- Given that package, when its contents and nuspec are inspected, then it contains the analyzer DLL at `analyzers/dotnet/cs` and has no consumer-visible package dependencies.
- Given the existing invalid Contracts fixture, when the solution builds, then runtime Catalog tests can still exercise its startup exclusion.

### Review Findings

Code review of 93fc112..9590d29 (2026-09-27).

Pass-1 open items (Roslyn 5.9 pin, message argument, suffix/null coverage, same-FQN lookup) were re-verified in pass 2 and are tracked there.

**Rejected**

- low — Analyzer DLL packed from hard-coded `bin/$(Configuration)/netstandard2.0`: `release-prepare.sh` builds the solution in Release, then packs `--no-build` from the same tree, and no artifacts output or custom `OutputPath` is configured. The fix adds an MSBuild target for a layout nobody uses.
- low — Linked `KebabCase` is unused and duplicates a public type: the link is required by the spec's Always constraint, and CS0433 appears only if `Analyzers.Tests` uses `KebabCase`, which it does not.
- false — Release scripts lack the packaged-consumer probe: `release.yml` `verify-source` requires a successful `ci.yml` push run on the exact SHA, and that run includes the bootstrap-package consumer probe.
- false — CI warning assertion is brittle: the output is piped through `tee`, so the terminal logger is automatically off. A local run matched both greps, and the exactly-one-warning check is intended strictness.
- low — The repo's own Contracts projects never run MCPCLI001: the spec scopes the warning to package consumers and the Code Map says to avoid attaching the analyzer to every project reference.
- low — No `helpLinkUri` or README entry for MCPCLI001: the message names the type and states the fix.
- low — Deferred-work entries for concurrent CLI, settings, and executor work are attributed to this spec: bookkeeping only, no code impact.
- reject — Spec `status: done` differs from sprint `review`: the fix would edit the spec under review, and this review step resets both statuses.

Code review pass 2 of 93fc112..9590d29 (2026-09-27): Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor.

- [ ] [Review][Decision] Packed analyzer requires Roslyn 5.9 and fails to load on SDKs older than 10.0.4xx — `Hexalith.McpCli.Analyzers.csproj` inherits the central `Microsoft.CodeAnalysis.CSharp` 5.9.0 pin (`references/Hexalith.Builds/Props/Directory.Packages.props:215`). A consumer on SDK 10.0.302 (Roslyn 5.6, installed locally) gets CS9057, no MCPCLI001, and a failed build under warnings-as-errors. The CI consumer copies `global.json` 10.0.401, so it cannot catch this. `CentralPackageVersionOverrideEnabled=false` rules out `VersionOverride`. All four layers raised it.
- [ ] [Review][Patch] Diagnostic message argument is never asserted; replacing `type.Name` with `string.Empty` leaves all 12 tests green [tests/Hexalith.McpCli.Analyzers.Tests/MissingOperationDescriptionAnalyzerTests.cs:30]
- [ ] [Review][Patch] Null description warns today but no test pins it; a `Value is string s` refactor would silently drop it while the runtime still excludes null [tests/Hexalith.McpCli.Analyzers.Tests/MissingOperationDescriptionAnalyzerTests.cs:19]
- [ ] [Review][Patch] Test matrix omits the explicit `Attribute` suffix spelling, a constant equal to `""`, and an unrelated `HexalithQueryAttribute` look-alike (Always constraint and I/O matrix) [tests/Hexalith.McpCli.Analyzers.Tests/MissingOperationDescriptionAnalyzerTests.cs:19]
- [ ] [Review][Patch] Attribute lookup via `GetTypeByMetadataName` returns null for an ambiguous FQN and disables the rule for the compilation; use `GetTypesByMetadataName` filtered to the `Hexalith.McpCli.Abstractions` assembly (reachable only with `extern alias`, direct one-line fix) [src/Hexalith.McpCli.Analyzers/MissingOperationDescriptionAnalyzer.cs:35]

**Rejected (pass 2)**

- false — Counterfeit test pairs no genuine violation: when a same-FQN type exists in source or a second reference, a genuine `[HexalithQuery]` binds to the counterfeit (CS0436) or fails as ambiguous (CS0433), so a pairing is only expressible with `extern alias`; the lookup fix above covers that case.
- false — Message names only the short type name and not the attribute: every diagnostic carries a file and line location at the type declaration, which identifies the type.
- false — CI consumer never checks which type warned: unit tests pin the diagnostic location on the type name; the CI probe exists to prove package auto-loading.
- false — Module descriptions are not checked at build time: the spec Intent and Always constraint scope this story to `[HexalithCommand]` and `[HexalithQuery]`.
- low — Linked `KebabCase` is unused, duplicates a public type, and its netstandard shim is untested: the link is a spec Always constraint, and no fixture uses `KebabCase`, so CS0433 does not occur.
- low — Analyzer DLL packed from a hard-coded `bin/$(Configuration)/netstandard2.0` path: no artifacts output or custom `OutputPath` is configured; same verdict as pass 1.
- low — Exact `1 Warning(s)` CI check is brittle against unrelated warnings: intended strictness, same verdict as pass 1.
- low — Test compilations reference every trusted platform assembly: slower but correct, and no fixture references a duplicated type.
- low — No README entry or `helpLinkUri` for MCPCLI001: the message names the type and states the fix; same verdict as pass 1.
- low — Nothing moves MCPCLI001 to `AnalyzerReleases.Shipped.md` at release: no build break results; a release-process chore.
- low — Named-argument and nested-type cases are untested: `description:` still populates `ConstructorArguments`, and nested types are ordinary `NamedType` symbols.

## Implementation Notes

- Added `MCPCLI001` for blank Command and Query descriptions. It matches attribute symbols from the Abstractions assembly, reports at the decorated type, and leaves runtime Catalog exclusion unchanged.
- The analyzer targets `netstandard2.0`, links the existing naming helper, and is packed within the Abstractions package. Its Roslyn references are private; the package nuspec has zero consumer dependencies.
- Verification: Release solution build (zero warnings/errors); analyzer tests 11/11; Abstractions tests 20/20; Core tests 158/158. The package contains `analyzers/dotnet/cs/Hexalith.McpCli.Analyzers.dll`; an isolated fresh-cache consumer with only the Abstractions reference produced one `MCPCLI001` warning at its decorated type.
- A first consumer probe reused an older local NuGet cache entry for package version `1.0.0` and showed zero warnings. Repeating with an isolated package cache loaded the newly packed DLL and passed.
- Review patches enabled diagnostics for generated Contracts source, added a generated-source test, enrolled the analyzer suite in CI, required the analyzer asset in release package validation, and asserted one warning from CI's staged-package consumer. Final Release build had zero warnings/errors; analyzer tests passed 12/12, Abstractions tests 20/20, and the fresh staged-package consumer emitted one `MCPCLI001` warning.

## Spec Change Log

## Review Triage Log

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| Blind: CLI entry point remains unimplemented | false: `Program.Main` now dispatches through `CliRunner().CreateRoot().Parse(args).InvokeAsync()`; the placeholder described by the snapshot is gone. | reject |
| Blind: bare boolean CLI flags are ignored | high: `GlobalOptionsBinding.ExplicitFlag` requires a value token, while bare bool switches have none; this can leave read-only mode off. The file belongs to concurrent CLI work. | defer |
| Blind: boolean environment values `1` and `0` fail | medium: addendum §E accepts both, but `SettingsResolver.SelectBoolean` uses only `bool.TryParse`. The file belongs to concurrent settings work. | defer |
| Blind: table formatting reaches describe, send, and query | medium: `CliOutput.WriteAsync` formats every successful document as a table, while PRD FR-12 requires JSON for these verbs. This belongs to concurrent CLI work. | defer |
| Blind: directory or dangling symlink profile path is treated as missing | medium: `ProfileStore.Read` returns defaults on `!File.Exists`, which also holds for these invalid paths. This belongs to concurrent settings work. | defer |
| Blind: allowed extension list inherits per-command count limit | medium: `SettingsResolver` passes the whole allowlist to `ExtensionValidator.Validate`, whose 32-entry check applies to one command's extensions. This belongs to concurrent settings work. | defer |
| Blind: blank setting error lacks field and source | low: the combined token/tenant/actor branch returns one generic message; blank settings are uncommon and splitting validation adds branches. | reject |
| Blind: cancellation becomes internal error | medium: `OperationExecutor.ExecuteAsync` catches all exceptions after the Gateway catch, including cancellation. This belongs to concurrent executor work. | defer |
| Blind: response identifiers are not validated | medium: `OperationExecutor` copies Gateway response IDs into the public success record, although addendum §G requires ULIDs. This belongs to concurrent executor work. | defer |
| Blind: invalid Gateway paging metadata can become a success record | medium: `OperationExecutor` copies paging without checking a nonempty cursor or valid numeric values. This belongs to concurrent executor work. | defer |
| Blind: analyzer tests bypass packaged consumption | medium: the tests attach the analyzer directly, so removing the NuGet analyzer asset would leave them green. A one-package consumer check is needed in the release gate. | patch |
| Blind: settings and CLI paths lack focused tests | medium: current test projects have no settings precedence, flag, or CLI output tests for the concurrent work. | defer |
| Edge: generated decorated types get no analyzer warning | medium: `GeneratedCodeAnalysisFlags.None` excludes generated code even when its decorated description is blank; the requirement has no generated-code exception. | patch |
| Edge: null or blank operation becomes internal error | medium: executor lookup calls `CatalogService.Describe`, which throws for a blank name and is caught as `internal_error`. This belongs to concurrent executor work. | defer |
| Edge: cancellation becomes internal error | medium: the same blanket executor catch captures `OperationCanceledException`. This belongs to concurrent executor work. | defer |
| Edge: explicit ID overrides a Query constant | high: `call.AggregateId ?? accessorId ?? operation.AggregateIdConstant` lets a supplied ID replace a declared constant. This belongs to concurrent executor work. | defer |
| Edge: package-consumer coverage claim relies on direct analyzer tests | medium: direct `WithAnalyzers` tests cannot prove NuGet auto-loading; the isolated consumer ran locally, but release verification does not yet run it. | patch |
| Verification: CI omits analyzer tests | medium: `.github/workflows/ci.yml` lists existing unit projects but not the new analyzer test project. | patch |
| Verification: release package gate misses analyzer consumption | medium: `validate-release-packages.py` checks the runtime DLL and dependencies, while its staged Contracts consumer has only valid descriptions. Dropping the analyzer asset would pass the gate. | patch |

## Design Notes

Use a semantic attribute match to avoid warning on an unrelated type with the same short attribute name. Evaluate the positional description as a compile-time constant so `const string` cases behave like literals. Keep the warning separate from Catalog diagnostics and let the existing runtime check cover values that cannot be evaluated at build time.

## Verification

**Commands:**
- `dotnet build Hexalith.McpCli.slnx --configuration Release` — analyzer, linked helper, and current fixtures compile with no new build failure.
- `dotnet test tests/Hexalith.McpCli.Analyzers.Tests/Hexalith.McpCli.Analyzers.Tests.csproj --configuration Release` — analyzer cases pass.
- `dotnet test tests/Hexalith.McpCli.Abstractions.Tests/Hexalith.McpCli.Abstractions.Tests.csproj --configuration Release` — naming behavior remains unchanged.
- `dotnet pack src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj --configuration Release` — inspect nupkg entry and nuspec, then build an isolated consumer from that package.
