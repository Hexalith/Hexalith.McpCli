---
title: 'Execute Calls with Structured MCP Results'
type: 'feature'
created: '2026-10-16'
status: 'done'
baseline_commit: e8b7ed89ff9265dd0cc7ec22489730e7fcef09bc
route: 'dispatch'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-3-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The existing MCP handlers bind execution arguments and serialize Core documents, but current MCP tests exercise discovery only. Output schemas are checked for shape rather than validated against real results, leaving execution parity and omission rules unproven.

**Approach:** Complete and verify the generic MCP execution boundary with substituted Gateway responses, canonical Core comparisons, and executable output-schema checks under both supported protocol flows. Repair defects exposed by these checks without duplicating Core policy.

## Boundaries & Constraints

**Always:** Use the shared argument records, executor, envelope context, and result serializer. Preserve every addendum §E argument and §G document field and omission rule. A Core error has `isError: true`, structured `{ error: ... }`, and matching JSON in the first text item. Unexpected tool exceptions become a sanitized `internal_error`. Input binding failures use protocol invalid-parameters errors. Every advertised output schema has an object root and closed success/error branches in `oneOf`; arbitrary result documents and embedded payload schemas remain open where their contract allows. Measure output-schema size separately from the existing 8,000-character input budget. Verify 2025-06-18 and 2026-07-28 clients using their version-appropriate flows.

**Never:** Add module-specific production code, another executor, new tools or transports, retries, dependencies with inline versions, or changes to sibling submodules. Preserve stdio channel and lifecycle guarantees from Story 3.2.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|---------------------------|----------------|
| Command success | Valid payload; correlation, idempotency, aggregate, extensions; optional Gateway result present/absent | Shared request reaches Gateway once; canonical identity, tenant, accepted status; optional fields only when supplied/returned | No invented idempotency or result |
| Query success | Entity and paging arguments; object, scalar, array, or null response; metadata present/absent | Shared request and canonical document; document always present, paging only when returned | Preserve JSON null and value types |
| Tenant policy | Fixed tenant; session tenant with override off/on; no session tenant | Core resolves or refuses per-call tenant identically to direct execution | Canonical validation document; refused calls never reach Gateway |
| Execution refusal | Wrong kind, invalid payload/envelope, missing URL, read-only direct execution, Gateway failure | Same Core error document and flags; discovery remains usable offline | Structured and text JSON agree; no secondary stderr error |
| Boundary failure | Executor or catalog throws; malformed/missing required input | Sanitized tool error for execution faults; protocol invalid parameters for binding faults | No exception or sensitive exception text leaks |
| Schema contract | Every tool's actual success/error results; extra fields and missing required members | Valid fixtures accepted; invalid fixtures rejected under both revisions | Closed document branches; input budget unaffected |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Mcp/McpToolHandlers.cs` — existing shared-record binding, guards, canonical conversion; retain Core ownership.
- `src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs` — runtime tools, required-name protocol filter, exporter-based output schemas; currently closes only branch roots.
- `src/Hexalith.McpCli.Core/McpCliCoreServiceCollectionExtensions.cs` — register real executor and replace only Gateway for integration checks.
- `src/Hexalith.McpCli.Core/Execution/` — canonical result/error records and executor; reuse without policy changes.
- `tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs` — reusable SDK stream-session and full-document comparison patterns; currently discovery coverage only.
- `tests/Hexalith.McpCli.Core.Tests/QueryTestHarness.cs` and `OperationExecutorTests.cs` — Gateway substitutes, complete request assertions, tenant and identity cases.
- `tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs` and `tests/fixtures/StdioHost/Program.cs` — real stdio process fixture and transcript assertions.
- `tests/Directory.Build.props` — existing xUnit, Shouldly, NSubstitute; JsonSchema.Net is already available through Core.

## Tasks & Acceptance

**Execution:**
- [x] `tests/Hexalith.McpCli.Mcp.Tests/McpExecutionTests.cs` and focused test helpers — exercise matrix cases using real Core plus a substituted Gateway, assert complete requests and canonical structured/text documents; separately inject exceptions to test boundary guards.
- [x] `tests/Hexalith.McpCli.Mcp.Tests/McpOutputSchemaTests.cs` — validate actual success/error fixtures for all five tools and reject extra/missing document members; report separate output-schema sizes under both protocol revisions.
- [x] `src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs` and `McpToolHandlers.cs` — repair schema or binding/conversion failures demonstrated by the new checks.
- [x] `tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs`, `tests/fixtures/StdioHost/Program.cs`, and fixture project references if needed — provide a deterministic substituted Gateway fixture mode and call every available tool through SDK stdio under both revisions; retain offline execution/discovery coverage.
- [x] `README.md` — document verified MCP execution argument representation and structured success/error behavior.

**Acceptance Criteria:**
- Given the same execution inputs and trusted context, when CLI/Core and MCP serialize outcomes, then their complete JSON documents and omission rules agree.
- Given an SDK stdio session under either revision, when the client lists tools and calls each available tool, then calls complete without JSON-RPC parse errors and subsequent discovery remains usable after an execution error.

## Implementation Notes

- Resumed the committed implementation with its original baseline intact. `McpOutputSchema` closes canonical nested objects, requires non-omitted members, and advertises error-code-specific branches while leaving embedded JSON open. The incoming filter validates SDK input schemas before binding; existing handler guards and canonical conversion required no changes.
- Added an optional internal service-registration seam through `CliRunner` and `HostFactory`. Only the StdioHost fixture selects its substituted Gateway; the real Core, CLI startup, hosted transport, and shutdown remain exercised.
- Both protocol revisions measure 2,329 characters for tool names, descriptions, and input schemas, and 13,022 for output schemas measured separately.
- Review corrections make numeric output strict, preserve canonical nullability, constrain status/kind and payload-schema roots, and reject paging values the SDK cannot bind to Int32 before tool dispatch. Core retains tenant and paging policy ownership.

## Spec Change Log

## Review Triage Log

| ID | Finding | Verdict / route | Verified evidence |
|----|---------|-----------------|-------------------|
| B1 | Int32 overflow passes input schema validation. | medium / patch | Parent reproduced `pageSize` and `offset` equal to 2147483648 through the built stdio host: the SDK returns unstructured text and logs a JsonException instead of protocol invalid parameters. Check representability before SDK binding. |
| B2 | Integral decimal/exponent syntax passes schema validation but fails binding. | medium / patch | Parent reproduced `pageSize: 25.0` and `offset: 1e20` with the same malformed outcome. Shares the numeric binding root cause with B1. |
| B3 | Required error fields accept null. | medium / patch | Parent validated actual advertised schemas with jsonschema 4.26.0: `internal_error.message: null` and `validation_failed.operation/violations: null` pass even though these fields cannot be omitted in these branches. |
| B4 | Numeric output fields accept strings. | medium / patch | Parent confirmed `gateway_error.status: "409"` and `paging.pageSize: "25"` validate. Exporting the Web serializer's read-number behavior misstates the canonical numeric output contract. |
| B5 | Optional omitted-when-null fields accept explicit null. | medium / patch | Parent confirmed `idempotencyKey: null` and `paging.hasMore: null` validate although the serializer omits them. Shares exporter nullability fidelity with B3. Preserve intentional null inside arbitrary result/document values. |
| B6 | Non-null string collections accept null items. | medium / patch | Parent confirmed `envelope.arguments: [null]` and `suggestions: [null]` validate; CatalogService constructs these from non-null names. Shares exporter nullability fidelity with B3/B5. |
| B7 | Fixed status and kind values are unconstrained. | medium / patch | Parent confirmed command `status: "failed"` and description `kind: "wrong"` validate. Core emits only `accepted` and `read`/`write`; constrain these fields so the executable contract detects such regressions. |
| B8 | Embedded payload schema accepts an invalid scalar root. | medium / patch | Parent confirmed description `schema: 42` validates. Require an object or boolean schema root while retaining arbitrary schema contents. |
| B9 | Tenant tests omit command override and implicit session fallback cases. | low / patch | Inspection confirms every tenant-matrix row supplies a tenant and uses queries; existing command coverage supplies a matching tenant. Add direct command refusal/acceptance and omitted-tenant fallback cases to protect the independently bound tenant argument. |
| B10 | Process tests lack injected unexpected exceptions and validation refusals. | low / reject | This is an additional process-test permutation, with no demonstrated escaping exception: real Core catches unexpected Gateway faults, all five tool guards have exact sensitive-exception tests, and process tests cover canonical execution failure and recovery. Extra fixture fault branches/wrappers add complexity for an unlikely uncovered defect. Numeric binding's demonstrated protocol/stderr defect is addressed separately. |
| E1 | Numeric values accepted by schema fail SDK binding. | medium / patch | Parent reproduced the edge review's cases in the actual stdio fixture. Same root cause and correction as B1/B2. |
| V1 | Error discriminator enums have no negative regression test. | medium / patch | Pre-verified gap: existing schema mutations remove/add members but never mismatch code and shape. Removing enum constraints accepts `validation_failed` with only a message without failing current checks. Add mismatched-code/shape and unknown-code rejections under both revisions. |

Review grouping: B1/B2/E1 share the numeric binding fix; B3/B5/B6 share exporter nullability fidelity. B4, B7, B8, B9, and V1 each retain their distinct verified outcome. All retained findings are bounded patches with no public API or Core policy change; none requires intent/spec renegotiation or deferral.

Review resolution: all retained findings were fixed and verified. `NonRepresentablePagingValuesUseInvalidParametersAsync` and the four full-tool stdio sessions protect B1/B2/E1, including both standard streams. Recursive null/item/type mutations protect B3–B6; `DocumentDiscriminatorsAndPayloadSchemaRootsAreConstrainedAsync` protects B7/B8; `SessionTenantFallbackAndCommandOverrideMatchCoreAsync` protects B9; `ErrorCodesDiscriminateTheirDocumentShapesAsync` protects V1. All ran under both revisions with no skips. No work was deferred.

## Verification

- `dotnet restore Hexalith.McpCli.slnx` — fresh package assets.
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` — no warnings or errors.
- `dotnet test tests/Hexalith.McpCli.Mcp.Tests --no-build --configuration Release` — all protocol, execution, and schema cases pass.
- `dotnet test tests/Hexalith.McpCli.Cli.Tests --no-build --configuration Release` — stdio and CLI regressions pass.
- Run Core and Manifest projects individually after fresh restore; run remaining existing test projects before marking complete. If Core validation, sample contracts, or Gateway wire output changes, also run both documented conformance scripts and restore afterwards.

### Results (2026-10-16)

- Fresh restore and the exact Release build above passed with zero warnings and errors.
- After review fixes, the parent ran all six test projects individually with `dotnet test tests/<Project> --no-build --configuration Release`: MCP 58 passed; CLI 479 passed, 2 Windows-only skips; Core 558 passed, 2 Windows-only skips; Manifest 8 passed; Abstractions 20 passed; Analyzers 19 passed. Total: 1,142 passed, 4 skipped, zero failures.
- An initial CLI run encountered an existing `QueryCommandTests` HTTP-listener cleanup race. All 19 cases of the affected method passed in isolation, followed by the complete successful CLI rerun. The stdio class independently passed all 19 cases, including both revisions in writable/read-only sessions.
- Parent read and then re-read the complete unified baseline diff after review fixes, including untracked files, at `/tmp/mcpcli-story-3-3-kjj6s18p.diff`. Final fresh restore, Release build, and all-project evidence: `/tmp/mcpcli-story-3-3-final-verification.log`. Initial evidence: `/tmp/mcpcli-story-3-3-verification-20261016.log`; focused review-fix evidence: `/tmp/mcpcli-story-3-3-reviewfix-verification.log` and its XML artifacts.
- `git diff --check` passed; touched C# files use CRLF. No Core validation, sample Contracts, or Gateway wire format changed, so the conditional conformance-script gates do not apply.
- After `npm ci`, the exact local commit message passed the pinned commitlint CLI with zero problems and warnings. Successful evidence is preserved at `/tmp/mcpcli-story-3-3-commitlint.log`.

### Matrix audit

Every covering test below ran and passed under both protocol revisions; the complete MCP project had zero skips.

| Matrix row | Passing coverage |
|------------|------------------|
| Command success | `CommandArgumentsAndOptionalResultMatchCoreAsync`, `CommandDefaultsDoNotInventOptionalMembersAsync` |
| Query success | `QueryArgumentsAndValueTypesMatchCoreAsync`, `IndependentQueryPagingArgumentsMatchCoreAsync`, `ReturnedValuesAndOptionalMembersValidateAsync` |
| Tenant policy | `TenantResolutionAndRefusalsMatchCoreAsync`, `SessionTenantFallbackAndCommandOverrideMatchCoreAsync` |
| Execution refusal | `ExecutionRefusalsAndGatewayFailuresMatchCoreAsync`, `ReadOnlyDirectExecutionIsStillGuardedAsync`, `SdkClientDiscoversOverCleanStdioAsync`, `EveryAvailableToolExecutesOverCleanStdioAsync` |
| Boundary failure | `BoundaryExceptionsAreSanitizedAsync`, `BindingFailuresUseInvalidParametersAsync`, `NonRepresentablePagingValuesUseInvalidParametersAsync`, `EveryAvailableToolExecutesOverCleanStdioAsync` |
| Schema contract | `ActualResultsValidateAndDocumentMutationsFailAsync`, `QueryVariantsAndCoreErrorsValidateAsync`, `ReturnedValuesAndOptionalMembersValidateAsync`, `GatewayAndAvailabilityErrorsValidateAsync`, `DocumentDiscriminatorsAndPayloadSchemaRootsAreConstrainedAsync`, `ErrorCodesDiscriminateTheirDocumentShapesAsync` |

Complete Core document comparisons protect execution parity and omission rules. `EveryAvailableToolExecutesOverCleanStdioAsync` protects every advertised tool, clean JSON-RPC, and continued discovery after a Gateway error in all four revision/mode combinations.

### Review Findings

Code review of `e8b7ed8..HEAD` (2026-10-16), four layers.

- [x] [Review][Patch] README does not state that paging values not representable as Int32 (`2147483648`, `25.0`, `1e20`) return JSON-RPC invalid-parameters [README.md:132]
- [x] [Review][Defer] Int32 paging check indexes exact `pageSize`/`offset` names; a differently-cased key may still reach case-insensitive SDK binding [src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs:89] — deferred: unverified Medium; settle by sending `{"PageSize": 2147483648}` over the stdio fixture and checking for a JsonException on stderr
- [x] [Review][Defer] Existing `QueryCommandTests` HTTP-listener cleanup race seen on the first CLI run [_bmad-output/implementation-artifacts/spec-3-3-execute-calls-with-structured-mcp-results.md:106] — deferred: pre-existing, not caused by this change

#### Rejected

- README omits the output schemas (blind-hunter, first pass): false. `README.md:132` documents them.
- Error-code enum can drift from Core, and four codes (`read_only`, `catalog_empty`, `catalog_invalid`, `unsupported_transport`) lack schema tests (all layers): low. Those codes are not returned by any registered tool call: read-only sessions do not register `send_command`, and the catalog codes are startup errors. Core has no shared code constant a test could enumerate, so the fix adds machinery for a drift nobody has shown.
- `Json.Schema` used by `Hexalith.McpCli.Mcp` through `Core` only (blind-hunter, acceptance-auditor): low. A Core change that drops it fails the build loudly, and JsonSchema.Net is already on the approved list.
- `IsOmittedWhenNull` recognizes only `WhenWritingNull`; `properties["status"]!`, `["kind"]!` and `errorProperties[name]!` lookups (edge-case, blind, verification-gap): low. `McpCliJson.Result` sets no default ignore condition, and a rename fails at startup in every test.
- `25.0` and `1e2` rejected as not Int32 (edge-case): by design, B2 in the Review Triage Log.
- Schema failures give a generic invalid-params message (blind): low.
- Int32 check hard-codes `run_query`, `pageSize`, `offset` (blind): low, matches the B1 decision.
- Spec `status: done` versus sprint `review` (acceptance, blind): resolved by this workflow's status sync.
- Seam in `CliRunner` and `HostFactory`, fixture reflection, `MCPCLI_STDIO_GATEWAY` (acceptance, blind): disclosed in Implementation Notes; the variable is read only by the test fixture's `Program.cs`.
- Process-lane error coverage, read-only negative over stdio, cancellation, 20 s shared timeout, pipe disposal, `AssertClosedObjects` exemptions, duplicated helpers and ULID constants, unasserted output size, `/tmp` evidence logs, extra boundary and negative paging cases, exact SDK message text (blind, edge-case, verification-gap, acceptance): low, no demonstrated defect; the fix adds tests, guards or edits to the spec.
