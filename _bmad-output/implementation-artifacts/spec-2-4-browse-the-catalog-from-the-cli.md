---
title: 'Browse the Catalog from the CLI'
type: 'feature'
created: '2026-10-01'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'edc459ea99ec6c4dc680a3eb04f4c858174c6344'
context:
  - 'AGENTS.md'
  - 'references/Hexalith.AI.Tools/hexalith-llm-instructions.md'
  - '_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Discovery exists, but the CLI has only a configured-URL parity test. Offline documents, filters, input errors, lint exits, tables, and strict diagnostics lack acceptance evidence. Table columns are centralized instead of declared beside verbs.

**Approach:** Test the adapter against synthetic Contracts, declare table headers beside verbs, and document discovery. Reuse Core; correct additional discovery behavior only when a failing acceptance test demonstrates a gap.

## Boundaries & Constraints

**Always:** Follow addendum §E/§G: exact document members, ordinal list ordering, read/write filtering, module casing in Schema/example, omitted optional fields, empty arrays, applicable envelope arguments, and lint findings. Availability belongs only to descriptions. Missing URL permits discovery; read-only takes precedence for writes. Unknown errors retain requested spelling and at most three suggestions ordered by case-insensitive edit distance, then ordinal name.

Preserve tab-separated tables: modules `NAME/OPERATIONS/DESCRIPTION`, operations `NAME/KIND/DESCRIPTION`, config `FIELD/VALUE`. Declare headers beside verbs. Describe stays JSON under table format with one existing stderr note and its lint-based exit code. Diagnostics stay on stderr; strict rejects any diagnostic before checking emptiness. Lint alone does not invalidate a strict catalog.

**Never:** Add module-specific production code or test hooks; change profiles, settings precedence, execution, MCP, packages, or `references/`. General parser/output remediation stays in Story 2.11.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Offline | No URL; three discovery verbs | §G documents; describe unavailable with `configuration_invalid`; zero requests | Exit 0 |
| Filter/order | Multiple modules; kind filters; marked-empty beside valid module | Ordinal lists, counts, correct filtered/empty arrays | Exit 0 |
| Binding | Absent/blank names; invalid kind | Named argument error; manifest untouched | `invalid_arguments`, exit 2 |
| Unknown | Unknown names, including case variants | Exact fields and capped, ordered suggestions | `unknown_module`/`unknown_operation`, exit 2 |
| Lint | Clean/findings; lint flag on/off | Same document; exit 1 only with flag and findings | Otherwise exit 0 |
| Table | Lists/config; describe with/without lint | Existing rows; describe JSON and one note | Preserve exit 0/1 |
| Diagnostics/empty | Diagnostic or empty manifest; strict on/off | Ordinary retains valid entries; strict rejects diagnostics before emptiness | `catalog_invalid`/`catalog_empty`, exit 2 |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli/Cli/CliRunner.cs` — discovery handlers, lint exit mapping, profile/manifest/environment seams.
- `src/Hexalith.McpCli/Cli/CliOutput.cs` — `WriteAsync` and `FormatTable`; retain rows and format note.
- `src/Hexalith.McpCli.Core/Catalog/` — CatalogService/Provider already own documents, suggestions, availability, strict/empty policy, and lazy diagnostics; reuse.
- `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs` — config table and lazy/version regression evidence. AssemblyInfo disables parallel Console capture.
- `tests/fixtures/` — lint; routing (warning, example, required idempotency); explicit (error); marked-empty. Sample.Contracts supplies fixed tenant and converted identifiers.

## Tasks & Acceptance

**Execution:**
- [x] `tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj` — reference existing lint, routing, explicit, and marked-empty fixture projects.
- [x] `tests/Hexalith.McpCli.Cli.Tests/DiscoveryCommandTests.cs` — test the matrix through parsing/invocation with isolated settings and restored streams. Assert complete fields and concrete values; fixed/nonfixed tenant, optional example, required idempotency; availability with read-only/URL combinations; suggestion cap/ties; strict versus lint; stream separation. A bounded local listener counts zero requests with a configured URL; also test no URL.
- [x] `src/Hexalith.McpCli/Cli/CliRunner.cs` and `CliOutput.cs` — replace the tabular boolean with an optional header declared beside supported verbs; preserve rows and fallback. Make only acceptance-driven discovery corrections.
- [x] `README.md` — document offline discovery, filters, columns, lint exits, and strict diagnostics.

**Acceptance Criteria:**
- Given matrix fixtures, when discovery tests run, then every row passes without an external service or Gateway request.
- Given updated tables, when config and CLI/MCP parity tests run, then documents, rows, masking, and exits remain unchanged.
- Given config/version, when existing offline tests run, then Catalog construction is bypassed.

## Implementation Notes

- Implemented the approved adapter/header refactor, four fixture references, 44 discovery test cases, and README guidance. Core required no correction.
- Reviewed a unified baseline diff including untracked files at `/tmp/mcpcli-story-24-hng1ih2_.diff`; Git index was not changed.
- Matrix audit: Offline → DiscoveryWorksOfflineWithExactDocumentsAsync, AvailabilityUsesReadOnlyAndUrlWithoutFilteringListsAsync, ConfiguredUrlDiscoveryDoesNotContactGatewayAsync; Filter/order → ListsAreOrdinalAndKeepMarkedEmptyModulesAsync, FiltersReturnExactOperationDocumentsAsync; Binding → BindingErrorsDoNotBuildCatalogAsync; Unknown → UnknownNamesReturnExactErrorsAndSuggestionsAsync, UnknownModuleWithOneCandidateHasOneSuggestionAsync; Lint → LintFlagChangesOnlyExitAndTableFallbackKeepsJsonAsync, PropertyLintUsesSerializedPointersAndAllRequiredMembersAsync; Table → TablesPreserveModuleOperationAndEmptyRowsAsync and existing config display tests; Diagnostics/empty → DiagnosticsAffectOnlyStrictAccessAsync, EmptyCatalogReturnsExactErrorsAsync. All ran and passed with no skips.
- Serialized Debug build passed with zero warnings/errors. Focused discovery run passed 44 cases; complete CLI assembly run passed 211 cases, zero failed/skipped, including config/version and CLI/MCP parity. Evidence: `/tmp/mcpcli-story-24-cli-tests.log`.
- Project-level test/restore startup was silent and canceled; direct xUnit execution and a serialized build using restored assets supplied successful focused evidence. No package changes were made.


- All six direct review corrections were applied in DiscoveryCommandTests.cs. The low culture-discrimination finding was rejected; nothing was deferred. Post-patch matrix audit remains complete.
- Parent final checks: serialized Debug build succeeded with 0 warnings/errors; focused runner passed 44/44; full CLI runner passed 211/211 with zero failures/skips. Final test evidence: `/tmp/mcpcli-story-24-final-tests.log`. Changed C# files retain CRLF, and `git diff --check` passed.
- Exact local commit candidate was validated by repository-pinned @commitlint/cli 21.2.2 using `npx --no -- commitlint --edit /tmp/mcpcli-story-24-commit-62kn1y7v.txt --verbose`; exit 0, zero errors/warnings. Successful validation evidence: `/tmp/mcpcli-story-24-commitlint.log`.

## Spec Change Log

## Review Triage Log

| Reviewer | Finding | Verdict | Evidence and route |
|---|---|---|---|
| blind-hunter | Listener Stop is skipped if the collector faults. | low | Confirmed: Stop follows an unprotected await in finally. A failed socket read can leave the bound listener alive until collection. Patch: always stop in a nested finally. |
| blind-hunter | Request count is asserted before the collector finishes. | low | Confirmed: the collector can increment between the assertion and cancellation. This weakens the zero-request regression check. Patch: join the collector before asserting its final count. |
| blind-hunter | Existing names do not distinguish ordinal from culture sorting. | low | Confirmed: supplied names have identical cultural and ordinal order. The unchanged CatalogBuilder explicitly uses StringComparer.Ordinal for both lists. Rejected: discriminating this hypothetical future algorithm regression needs new Contracts fixtures/culture machinery rather than a direct correction. |
| blind-hunter | Ordinary diagnostic branches permit incomplete retained results. | low | Confirmed: modules/describe only parse JSON, operations only asserts a count. A malformed retained result could pass this test. Patch: assert complete expected retained documents and exclude invalid operations. |
| blind-hunter | Mapped-envelope Schema assertion is partial. | low | Confirmed: property types, constraints, descriptions, and extra Schema members are not pinned by this case. Patch: compare its complete expected Schema. |
| blind-hunter | Fourteen lint entries are counted but most codes/paths are unchecked. | low | Confirmed: duplicate or incorrect unchecked entries could preserve the count. Patch: assert the complete expected code/path collection in addition to finding fields and existing message checks. |
| blind-hunter | Read-only matrix omits filtered writes and module counts. | low | Confirmed: read-only lists currently assert only the unfiltered operation names. Patch: add exact filtered write listing and module count assertions to the existing availability cases. |

Edge-case-hunter returned no findings. Verification-gap returned no verification gaps. All three layers completed before triage.

## Verification

- `dotnet build tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Debug --no-restore -m:1` — succeeds; restore this project first if needed.
- `dotnet tests/Hexalith.McpCli.Cli.Tests/bin/Debug/net10.0/Hexalith.McpCli.Cli.Tests.dll -class '*DiscoveryCommandTests'` — new cases pass.
- Run that assembly without filters — full CLI suite passes. Build/run Core or MCP projects individually if shared code changes; record environmental blockers separately.
