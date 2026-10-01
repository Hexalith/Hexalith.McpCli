---
title: 'Validate and Page Query Calls'
type: 'feature'
created: '2026-10-01'
status: 'done'
baseline_commit: '9b0b6e7a082bf93b669a883e48672c26c6f0630d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - 'AGENTS.md'
  - '_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 2.6 lacks acceptance coverage for query validation, envelope paging, tenant ownership, and optional metadata.

**Approach:** Test Core and CLI with synthetic Contracts and a bounded loopback Gateway; fix demonstrated acceptance failures.

## Boundaries & Constraints

**Always:** Validate before exactly one descriptor-routed submission; refusals make zero calls. Preserve Story 2.5 tenant/aggregate precedence. Envelope aggregate identifiers follow Module kind (`Ulid.TryParse` or nonempty String) plus Gateway syntax; entity identifiers follow Gateway syntax. Tenant: 1–64 lowercase ASCII alphanumeric/hyphens; aggregate/entity: 1–256 ASCII alphanumeric/dot/underscore/hyphen. All start/end alphanumeric.

Use Client/Contracts 3.110.0 rules, source `27279fe6431925a6ea046c3f89af61487185c7de`. Paging accepts size 1–200, nonnegative Int32 offset, cursor ≤4,096 UTF-16 units. Only nonblank cursors conflict with supplied offsets; preserve blank cursors. Invent no request defaults or response fields. CLI exits 2 on failure, 0 on success.

**Never:** Add module-specific code, dependencies, retries, topology changes, or `references/` edits. Defer Commands, MCP transport, general parser/output redesign, conformance tooling, and malformed response hardening.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Invalid payload | Malformed/duplicate JSON; multiple nested failures and renamed `/`/`~` members | All schema violations with RFC 6901 paths; malformed JSON: one `/` violation | `validation_failed`, zero calls |
| Identifiers | ULID/String aggregates; tenant/entity; length boundaries, blanks, forbidden characters | Preserve valid values; envelope failures at `/tenant`, `/aggregateId`, `/entityId` | `validation_failed`, zero calls |
| Paging | Omitted; size 1/200; offset 0/max; cursor 4096; invalid adjacent limits; nonblank cursor plus offset 0 | Supplied values only in request `Paging`; omitted paging absent | Invalid `/pageSize`, `/offset`, `/cursor`; zero calls |
| Payload paging names | `PageSize`, `Offset`, `Cursor`; differing or absent envelope values | Payload unchanged; lint retained; no paging inference | Valid submission |
| Tenant ownership | Omitted/matching/conflicting declared tenant; non-string caller tenant | Trusted value fills declared serialized member; conflicting value fails at its pointer | `validation_failed`, zero calls |
| Revalidation | Prefill passes; filled tenant violates schema | Rebuilt payload fails at tenant member | `validation_failed`, zero calls |
| Returned paging | Absent; pageSize only; independent offset/nextCursor/totalCount/hasMore, including 0/false | Exact returned fields; omit unavailable metadata | Canonical success |
| Missing URL | Valid query without resolved Gateway URL | `configuration_invalid`; offline discovery remains available | Exit 2, zero calls |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs` — reuse existing validation/paging; shared checks in `PayloadValidator`/`RoutingResolver`.
- `src/Hexalith.McpCli/Cli/CliRunner.cs` — reuse `CreateQuery` bindings.
- `tests/Hexalith.McpCli.Core.Tests/QueryExecutionTests.cs` — exact requests/results and zero-call patterns. Explicit IDs on `Routing.GetHTTP2StatusQuery` reach `/aggregateId`; accessor failures use payload pointers.
- `tests/fixtures/Catalog.Lint.Contracts/InspectItemQuery.cs` — tenant/paging/nested fixtures; `String.ListItemsQuery` supplies String coverage. Preserve fixture catalogs.
- `tests/Hexalith.McpCli.Cli.Tests/QueryCommandTests.cs` — loopback, restored streams, bounded cancellation, unconditional cleanup; compare complete JSON with type-preserving equality.

## Tasks & Acceptance

**Execution:**
- [x] `tests/Hexalith.McpCli.Core.Tests/TenantSchemaProbeQuery.cs` and `tests/Hexalith.McpCli.Core.Tests/QueryValidationContractsAssembly.cs` — isolated probe following `FaultingContractsAssembly`: separate aggregate accessor and string tenant marked ULID; prove final revalidation.
- [x] `tests/Hexalith.McpCli.Core.Tests/QueryValidationTests.cs` — payload, identifier, ownership, revalidation, availability matrix; exact paths and zero calls.
- [x] `tests/Hexalith.McpCli.Core.Tests/QueryPagingTests.cs` — paging matrix, payload isolation/lint, independent metadata; complete requests/results.
- [x] `tests/Hexalith.McpCli.Cli.Tests/QueryValidationCommandTests.cs` — error documents, exit 2, zero requests, offline discovery.
- [x] `tests/Hexalith.McpCli.Cli.Tests/QueryPagingCommandTests.cs` — loopback option binding, complete requests/results, partial metadata, exit 0.
- [x] `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs` — fix demonstrated defects; preserve shared checks/order.
- [x] `README.md` — explain entity/paging options, limits, payload separation, metadata omission.

**Acceptance Criteria:**
- Given matrix fixtures, when focused Core/CLI cases run, then every row passes with zero calls on refusal and one on success.
- Given the completed change, when both full test projects run individually, then existing behavior passes and no new acceptance case is skipped.

## Implementation Notes

- Added four acceptance classes, two shared test harnesses, and two isolated tenant probe types. README explains entity syntax, paging limits, payload isolation, and optional metadata.
- The existing executor passed the approved matrix; no production, dependency, or fixture catalog changes were necessary.
- Schema evaluation reports both parent summaries and leaf violations. Tests assert their complete locations, including escaped names, rather than dropping summaries.
- Blank global CLI tenant settings fail earlier with `configuration_invalid`; Core tests cover blank resolved envelope tenants, and CLI tests exercise a missing session tenant at `/tenant`.

### Validation and matrix audit (2026-10-01)

- Both specified Debug builds passed with zero warnings/errors.
- Implementation focused runs: Core 100 passed, CLI 89 passed; zero failures/skips/not-run cases.
- Full Core: 371 total, 369 passed, zero failures, two existing Windows-only ACL skips on Linux. Full CLI: 320 passed, zero failures/skips.
- Parent read the entire unified diff, including untracked files, and reran all four new classes with xUnit XML results: every one of the 100 Core and 89 CLI cases passed.
- Matrix coverage: invalid JSON and nested errors (`InvalidJson*`, `ReportsEveryNestedSchemaViolationAsync`, `NestedFailuresKeepEverySerializedPointerAsync`); identifiers (`InvalidEnvelopeIdentifiers*`, `InvalidUlidAggregateArguments*`, `ValidIdentifierBoundaries*`, CLI option/boundary cases); paging (`SuppliedPaging*`, `InvalidPaging*`, `PagingOptions*`, CLI cursor conflict); payload isolation/lint (`PayloadPagingNamesAreNeverInferredAsync`, `PayloadPagingIsIndependentAndTenantIsFilledAsync`); ownership (`TrustedTenantFillsDeclaredMemberAsync`, `CallerCannotSupplyUntrustedTenantAsync`, renamed ownership and CLI raw tenant cases); revalidation (`FilledTenantIsValidatedAgainAsync`, both rows); metadata (`ReturnedMetadataIsMappedWithoutInventedFieldsAsync`, `ReturnedPagingContainsOnlyGatewayFieldsAsync`); missing URL (`MissingUrlLeavesOfflineDiscoveryAvailableAsync` in both heads). All covering cases ran and passed.
- Durable local evidence: `/tmp/mcpcli-story-2-6-{core,cli}-{build,focused,full}.log`; parent `/tmp/mcpcli-story26-{core,cli}-audit.log` and `.xml`; complete diff `/tmp/mcpcli-story-26-implementation-bjranbnv.diff`.
- `git diff --check` and all eight new C# files' CRLF/final-newline/trailing-whitespace checks passed.

## Spec Change Log

## Review Triage Log

All three review layers completed: blind hunter (nine findings), edge-case hunter (one finding), and verification-gap reviewer (no gaps). Each finding was assessed before grouping.

| Finding | Verdict / route | Evidence |
|---|---|---|
| BH-1 | medium / defer | The built CLI with `--offset 2147483648` exits 1, prints usage on stdout and a parse error on stderr. `CreateQuery`'s existing Int32 binding never reaches execution. The README's validation exit statement predates this change; general parser consistency belongs to Story 2.11. |
| BH-2 | low / patch | New query schema cases check types but leave missing-required, unknown-property, and wrong-case inputs unexercised at execution. Add direct refusal cases so preprocessing cannot silently drop them. |
| BH-3 | low / patch | String invalid-aggregate cases use explicit arguments only. Add invalid `LookupQuery.Key` values with no explicit ID to protect Gateway validation after accessor extraction. |
| BH-4 | low / patch | Tenant success cases use letter endpoints. Add valid `0` and `0-a-9` tenants to protect the documented digit/hyphen syntax. |
| BH-5 | low / patch | Nonblank cursor examples lack whitespace/punctuation. Add an opaque value with both so accidental trimming/sanitization is detected. |
| BH-6 | medium / patch | Every response-paging case requests paging. Add returned metadata with request paging omitted in Core and CLI so Gateway defaults remain visible. |
| BH-7 | low / patch | Both new harnesses always return an object document. Add null-document responses with paging to protect the required null member and independent metadata together. |
| BH-8 | low / reject | Core refusal helper checks unique locations and nonempty messages; repeated locations are legitimate when multiple schema keywords fail. Complete canonical shape/operation is already checked through the CLI on shared failure paths. Adding required helper parameters and keyword multiplicity expectations adds complexity without a demonstrated everyday defect. |
| BH-9 | low / reject | The port probe is released before HttpListener binds, permitting a rare external port collision. This pattern is shared with existing loopback tests; adding retry guards or another server for the uncommon race exceeds a direct correction. |
| EC-1 | low / reject | Same demonstrated port-allocation window as BH-9; no retry or binding replacement is warranted for this uncommon environment race. |

Six surviving coverage findings are direct test patches. The parser issue is pre-existing and deferred. No intent-gap or spec loopback was identified.

### Review patches

- [x] Missing-required, unknown-property, and wrong-case query schema refusals.
- [x] Invalid String aggregate identifiers extracted from payload accessors.
- [x] Valid digit/hyphen tenant forms.
- [x] Opaque nonblank cursors with whitespace and punctuation.
- [x] Gateway metadata when request paging is omitted.
- [x] Gateway paging beside a null document.

### Review patch validation (2026-10-01)

All six patches are complete. Parent inspected every patch against the previously reviewed complete diff and regenerated the full unified diff, including untracked files. The frozen intent is unchanged.

- Final Debug builds: Core and CLI each passed with zero warnings/errors.
- Final focused matrix runs: Core 122/122 and CLI 95/95 passed; zero failures/skips/not-run cases. All six new coverage groups ran successfully, including missing/unknown/case schema members, String accessor validation, digit/hyphen tenants, opaque cursor preservation, metadata without request paging, and metadata beside null documents.
- Final full runs: Core 393 total / 391 passed / zero failures / two existing Windows ACL skips; CLI 326/326 passed, zero skips/failures.
- Parent evidence: `/tmp/mcpcli-story26-final-{core,cli}-build.log` and `/tmp/mcpcli-story26-final-{core,cli}-{focused,full}.log` plus corresponding xUnit `.xml` results. The Windows-only checks remain unexecuted on Linux; every new acceptance case passed.
- The pre-existing numeric parser behavior is recorded in `deferred-work.md` for Story 2.11. No required Story 2.6 work remains.

## Verification

- `dotnet build tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Debug --no-restore -m:1`
- `dotnet build tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Debug --no-restore -m:1`
- `dotnet tests/Hexalith.McpCli.Core.Tests/bin/Debug/net10.0/Hexalith.McpCli.Core.Tests.dll`
- `dotnet tests/Hexalith.McpCli.Cli.Tests/bin/Debug/net10.0/Hexalith.McpCli.Cli.Tests.dll`
- Restore only if needed. Builds: zero warnings/errors. Run assemblies first with single-dash `-class` filters for the four new classes, then unfiltered: zero failures; record existing platform-only skips separately.
- `git diff --check` — expect no whitespace errors.
