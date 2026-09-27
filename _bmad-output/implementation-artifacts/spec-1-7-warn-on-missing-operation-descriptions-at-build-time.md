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

- [x] [Review][Decision] Packed analyzer requires Roslyn 5.9 and fails to load on SDKs older than 10.0.4xx — resolved 2026-09-27: require .NET SDK 10.0.4xx or later and move every Hexalith repository's SDK and the Hexalith.Builds Roslyn pin together. All `references/` submodules, including the newly added Hexalith.Platform, now pin 10.0.401. Rejected alternatives: pinning the analyzer to Roslyn 5.0 through a nested `Directory.Packages.props` (prototype loaded on SDK 10.0.302), and deferral.
- [x] [Review][Patch] Document the .NET SDK 10.0.4xx minimum and MCPCLI001 in the packed README so consumers can diagnose CS9057 [README.md:36]
- [x] [Review][Patch] Diagnostic message argument is asserted in every blank-description case and in the same-FQN case [tests/Hexalith.McpCli.Analyzers.Tests/MissingOperationDescriptionAnalyzerTests.cs:39]
- [x] [Review][Patch] Null descriptions are covered for commands and queries [tests/Hexalith.McpCli.Analyzers.Tests/MissingOperationDescriptionAnalyzerTests.cs:32]
- [x] [Review][Patch] Explicit `Attribute` suffix, empty constant, and unrelated query look-alike are covered [tests/Hexalith.McpCli.Analyzers.Tests/MissingOperationDescriptionAnalyzerTests.cs:28]
- [x] [Review][Patch] Attribute lookup uses `GetTypesByMetadataName`, filters by the Abstractions assembly, and has a same-FQN test with `extern alias` [src/Hexalith.McpCli.Analyzers/MissingOperationDescriptionAnalyzer.cs:35]

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

Code review pass 3 of 93fc112..working tree, scoped to story files (2026-09-27): Blind Hunter, Edge Case Hunter, Verification Gap (no gaps), Acceptance Auditor (no AC violations). Analyzer tests 19/19 in Release. Clean review — no decision, patch, or defer items.

**Rejected (pass 3)**

- low — Blind: in-repo Contracts projects never run MCPCLI001: their `ProjectReference` to Abstractions omits the packed analyzer by design; attaching it under inherited `TreatWarningsAsErrors` would fail the intentionally invalid fixtures (spec Never), and the CI package consumer covers auto-loading. Same verdict as passes 1–2.
- low — Blind: CI `1 Warning(s)` grep depends on console-logger text: `tee` disables the terminal logger and the runner locale is fixed; intended strictness, same verdict as passes 1–2.
- low — Blind: linked `KebabCase` is unused and its netstandard guard is untested and duplicated: the link is a spec Always constraint; the guard mirrors `ThrowIfNullOrWhiteSpace` exactly. Same verdict as passes 1–2.
- false — Blind: message `type.Name` is ambiguous across namespaces, nested, or generic types: every diagnostic carries a source location at the type identifier. Same verdict as pass 2.
- false — Blind: TPA reference set breaks alias isolation: TPA does include an unaliased `Hexalith.McpCli.Abstractions.dll`, but the source counterfeit wins by CS0436 and `GetTypesByMetadataName` still returns both symbols, so the same-FQN test exercises the lookup fix (the pre-fix `GetTypeByMetadataName` returned the source type and would fail it); no fixture uses `KebabCase`.
- low — Blind: early-return, single-attribute, nested/generic, `<auto-generated>` header, and `.editorconfig` suppression paths are untested: each is a trivial branch or Roslyn platform behavior (`ConfigureGeneratedCodeAnalysis` covers all generated forms).
- low — Blind: README omits `TreatWarningsAsErrors` impact and suppression syntax, and no `helpLinkUri`: the message names the type and the fix; standard .NET suppression applies. Same verdict as passes 1–2.
- low — Blind: analyzer DLL packed from a hard-coded `bin/$(Configuration)/netstandard2.0` path: no `UseArtifactsOutput`, `OutputPath`, or `BaseOutputPath` is configured, `release-prepare.sh` builds then packs `--no-build`, and the validator fails on a missing DLL. Same verdict as passes 1–2.
- low — Blind: package validation checks only presence of the analyzer DLL, not absence of Roslyn DLLs or a `lib/` copy: only one explicit `None` item packs to `analyzers/dotnet/cs`, and `ReferenceOutputAssembly="false"` keeps the analyzer out of `lib/`; the guard would add checks for a state not demonstrated.
- low — Edge: in-repo Contracts never run MCPCLI001: same as the Blind finding above.
- low — Edge: hard-coded analyzer pack path: same as the Blind finding above.
- false — Edge: public linked `KebabCase` causes CS0433 in the test project: the Analyzers test project references both assemblies but never names `KebabCase`, and its Release build is clean.
- false — Edge: blank description dropped when no type location falls inside the decorated declaration span: a type's identifier location always lies inside each of its declaration spans, and a null declaration falls back to the first location.
- false — Edge: two referenced assemblies named `Hexalith.McpCli.Abstractions` leave the second copy unchecked: a non-strong-named duplicate simple name is CS1704, so the compilation cannot reach the analyzer with two copies.
- low — Edge: exact `1 Warning(s)` CI check fails on unrelated warnings: intended strictness, same as the Blind finding above.
- false — Edge: alias test binds the global alias too: same refutation as the Blind TPA finding above.
- reject — Auditor: auto-loading requires .NET SDK 10.0.4xx: resolved as a pass-2 decision and documented in the README.
- low — Auditor: genuine attribute recognized by assembly simple name only: no spec requirement for identity pinning; a spoofed Abstractions assembly is not a realistic consumer state.
- reject — Auditor: null descriptions warn though the matrix names only empty and whitespace: a superset matching runtime exclusion; the fix would edit the frozen spec.
- low — Auditor: hard-coded analyzer pack path: same as the Blind finding above.
- false — Auditor: packaged-consumer probe missing from `release-prepare.sh`: `release.yml` requires a green `ci.yml` run on the exact SHA. Same verdict as pass 1.

## Implementation Notes

- Added `MCPCLI001` for blank Command and Query descriptions. It matches attribute symbols from the Abstractions assembly, reports at the decorated type, and leaves runtime Catalog exclusion unchanged.
- The analyzer targets `netstandard2.0`, links the existing naming helper, and is packed within the Abstractions package. Its Roslyn references are private; the package nuspec has zero consumer dependencies.
- Verification: Release solution build (zero warnings/errors); analyzer tests 11/11; Abstractions tests 20/20; Core tests 158/158. The package contains `analyzers/dotnet/cs/Hexalith.McpCli.Analyzers.dll`; an isolated fresh-cache consumer with only the Abstractions reference produced one `MCPCLI001` warning at its decorated type.
- A first consumer probe reused an older local NuGet cache entry for package version `1.0.0` and showed zero warnings. Repeating with an isolated package cache loaded the newly packed DLL and passed.
- Review patches enabled diagnostics for generated Contracts source, added a generated-source test, enrolled the analyzer suite in CI, required the analyzer asset in release package validation, and asserted one warning from CI's staged-package consumer. Final Release build had zero warnings/errors; analyzer tests passed 12/12, Abstractions tests 20/20, and the fresh staged-package consumer emitted one `MCPCLI001` warning.
- The final review patches document `MCPCLI001` and the SDK minimum in the packed README, resolve ambiguous same-name attribute symbols, and assert the message and remaining description cases. Analyzer tests passed 19/19, Abstractions tests 20/20, Core tests 173/173, and the Release solution build had zero warnings/errors. A fresh one-package consumer emitted one `MCPCLI001` warning; package inspection confirmed the analyzer asset and zero consumer dependencies. The final review found no analyzer-specific defect and deferred eight findings in concurrent CLI, settings, executor, MCP, and conformance work.

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
| Blind 3: bare boolean switches are ignored | high: carried — `ExplicitFlag` still requires a token; the earlier triage recorded this CLI defect. | defer |
| Blind 3: blank operation becomes internal error | medium: carried — `CatalogService.Describe` still receives blank input from the executor. | defer |
| Blind 3: cancellation becomes internal error | medium: carried — the executor still catches cancellation as `Exception`. | defer |
| Blind 3: malformed response identifiers | medium: carried — the executor still copies Gateway response IDs without ULID validation. | defer |
| Blind 3: returned correlation differs from request | false: the PRD defines the Gateway response as the canonical result and makes no equality promise; an idempotency replay can return the earlier command's correlation. | reject |
| Blind 3: malformed response paging | medium: carried — the executor still copies paging without validating its values. | defer |
| Blind 3: blank cursor and offset | medium: `ValidateQueryArguments` accepts a whitespace cursor and bypasses its offset conflict; concurrent executor work, unrelated to description analysis. | defer |
| Blind 3: extension allowlist count | medium: carried — profile validation still applies a per-command 32-entry limit to the whole allowlist. | defer |
| Blind 3: short token masking | medium: `MaskToken` reveals every character of a token of four or fewer characters in config output; concurrent profile work. | defer |
| Blind 3: vector request subset comparison | medium: `_expect_fields` traverses expected keys only, so an unexpected Gateway envelope field passes; concurrent conformance work. | defer |
| Blind 3: vector public result shape | medium: CLI/MCP equality and vector-specific assertions do not guarantee all required public result fields; concurrent conformance work. | defer |
| Blind 3: HTTP transport release message | low: `RunMcpAsync` returns the correct code but its text omits the PRD's next-release wording; concurrent CLI work. | defer |
| Verification 3: bearer header has no gateway request test | medium: verified — command parity uses a null token and never asserts `Authorization`; concurrent hosting and CLI work. | defer |
| Verification 3: paging cursor has no public output test | medium: verified — parity uses a response without paging and the Core test checks only the in-memory result; concurrent query work. | defer |
| Verification 3: MCP kind filter lacks handler test | medium: verified — Core filtering is tested, while MCP parity calls `list_operations` without `kind`; concurrent MCP work. | defer |
| Verification 3: bare boolean switches are ignored | high: carried — the earlier triage recorded this same `ExplicitFlag` defect and the code still requires a value token. | defer |
| Edge 3: bare boolean switches are ignored | high: carried — the earlier triage recorded this same `ExplicitFlag` defect. | defer |
| Edge 3: extension allowlist count | medium: carried — `SettingsResolver` still validates the whole allowlist as one command. | defer |
| Edge 3: blank operation becomes internal error | medium: carried — executor lookup still sends blank input to `Describe`. | defer |
| Edge 3: cancellation becomes internal error | medium: carried — the executor's blanket catch is unchanged. | defer |
| Edge 3: explicit aggregate ID overrides query constant | high: carried — caller ID still takes precedence over the declared constant. | defer |
| Edge 3: malformed response identifiers | medium: carried — the executor still copies response IDs without ULID validation. | defer |
| Edge 3: malformed response paging | medium: carried — the executor still copies paging without validating it. | defer |

## Design Notes

Use a semantic attribute match to avoid warning on an unrelated type with the same short attribute name. Evaluate the positional description as a compile-time constant so `const string` cases behave like literals. Keep the warning separate from Catalog diagnostics and let the existing runtime check cover values that cannot be evaluated at build time.

## Verification

**Commands:**
- `dotnet build Hexalith.McpCli.slnx --configuration Release` — analyzer, linked helper, and current fixtures compile with no new build failure.
- `dotnet test tests/Hexalith.McpCli.Analyzers.Tests/Hexalith.McpCli.Analyzers.Tests.csproj --configuration Release` — analyzer cases pass.
- `dotnet test tests/Hexalith.McpCli.Abstractions.Tests/Hexalith.McpCli.Abstractions.Tests.csproj --configuration Release` — naming behavior remains unchanged.
- `dotnet pack src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj --configuration Release` — inspect nupkg entry and nuspec, then build an isolated consumer from that package.
