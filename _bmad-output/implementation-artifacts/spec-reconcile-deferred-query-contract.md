---
title: 'Reconcile five deferred query contract findings'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Query discovery should advertise only default aggregate identifiers that callers can use. The CLI and MCP should apply the adopted query routing and paging rules, and MCP clients should receive the documented failure when the Gateway rejects a call.

Close the five ledger findings on constant overrides, blank cursors with offsets, invalid default identifiers, MCP paging argument binding and MCP Gateway-failure coverage. Apply AD-19 at catalog admission. Verify the existing paging and Gateway-failure contracts against the pinned SDK, and correct any divergence.

</frozen-after-approval>

## Implementation Notes

- Baseline revision is `95a4329a59e00e8abec977a3719fd50408a3ced4`. Planning found a single query-contract scope with no unresolved product decisions. The footprint is Core catalog admission, MCP protocol validation if required, query fixtures and tests, and the related documentation and ledger.
- AD-19 and Story 5.24 require the Gateway grammar and Module Identifier Kind at admission, preserve explicit overrides and prioritize dual-source diagnostics. AD-20 and the README permit blank cursors alongside offsets. Existing session tests cover Gateway 409 and malformed successful responses.
- Catalog admission now uses the same aggregate identifier check as execution and retains diagnostic precedence for dual declarations. All seven defaults in the three pinned production Contracts assemblies are valid String-kind values. The three synthetic ULID defaults now use canonical IDs.
- The casing regression initially failed for both SDK revisions. The pinned SDK ignored differently cased paging properties. The incoming filter now refuses casing variants of all three paging names before binding or submission. Both supported protocol revisions exercise the refusal in in-process and child-process sessions.
- The CLI and the child-process MCP client exercise optional aggregate IDs through a loopback Gateway and verify the exact submitted ID. MCP discovery also checks the required flag for a Query with no aggregate source.
- Story 5.24 entered review on 2026-11-23. The review patches were applied and verified on 2026-11-27.

## Review Triage Log

- Medium, patched. A mis-cased `Cursor` could disappear even with an offset. The filter now recognizes case variants of all three paging names. A regression checks `InvalidParams` and zero calls for `Cursor` with an offset.
- Low, documented. The SDK advertises an open argument schema and the incoming filter enforces exact paging names and numeric token spelling. The `run_query` description now names the case requirement. Closing the schema would also reject unrelated additional members.
- Medium, patched. Real stdio verifies optional discovery, defaults and valid overrides on both protocol revisions. Each case asserts the negotiated version and captured request.
- Medium, patched. A malformed explicit aggregate must fail even when a valid default exists. The CLI regression asserts the complete refusal and zero submissions.
- Low, patched. `HexalithQueryAttribute.AggregateId` remarks describe identifier-kind admission and explicit override behavior for module authors.
- Low, patched. The spec records the test commands and observed outcomes.
- Low, patched. The five original ledger entries link to the resolution table.
- Low, patched. The sprint tracker links Story 5.24 to this follow-up and records its review status.

### Review Findings

Review on 2026-11-27 of `95a4329a..bcf8cf5d`, with later fixes checked on `main`.

- [x] [Review][Patch] Medium. Reject a case variant of the `run_query` `aggregateId` argument before submitting to the Gateway [src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs:87]. The stdio probe supplied a valid override with `AggregateId` and received the fixture's default aggregate. The same value under `aggregateId` reached the Gateway as the override.
- [x] [Review][Patch] Low. Make the advertised `run_query` input schema reject the reserved paging case variants [src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs:45]. The schema accepted `PageSize: 25` and the same session returned `InvalidParams` for that input. Preserve support for unrelated additional properties.
- [x] [Review][Patch] Low. Cover `Cursor` with an offset over child-process stdio for both revisions [tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs:279]. The child-process matrix covers the two numeric aliases. The cursor alias is exercised in the in-process matrix.
- [x] [Review][Patch] Low. Test a canonical paging argument alongside its case variant [tests/Hexalith.McpCli.Mcp.Tests/McpExecutionTests.cs:337]. An isolated alias test would still pass if the guard accidentally allowed `PageSize` whenever `pageSize` was present. Assert `InvalidParams` and zero Gateway calls for the mixed request.
- [x] [Review][Patch] Low. Exercise a malformed explicit `aggregateId` on a defaulted Query over stdio [tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs:119]. The CLI checks the complete `/aggregateId` refusal. The new stdio matrix covers omission and valid override. Check the structured and text refusal and zero submissions over stdio.
- [x] [Review][Patch] Low. Clarify diagnostic precedence for conflicting Query declarations in the README [README.md:570]. `invalid_routing_value` applies to a sole invalid constant. A Query with both declarations reports `ambiguous_aggregate_id` even when its constant is invalid.
- [x] [Review][Defer] Low. Correct the obsolete AD-19 description of catalog admission [_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md:232]. Deferred to the architecture document. Runtime admission uses both checks.

#### Rejected

- Low. The SDK discovery probe could fall back before a slow child started. `1bff511a` gives the pinned handshake the test's overall deadline.
- Medium. The reviewed revision could return success for malformed Gateway paging. Story 5.22 adds response validation and parity tests. The resolution is already tracked (`deferred-work.md:80`).
- Low. The original verification record omitted the sample loopback command. The independent review ran the conformance gates and records their results below.

## Verification

- The .NET 11 Release solution restore and build passed with the workspace's installed Aspire bundle. The first full Core, CLI and MCP suites reported 922, 632 and 96 passing tests. Six expected platform or benchmark tests were skipped.
- After the review patches, the Release CLI and MCP test builds passed with warnings treated as errors. The focused `PlatformScopeCommandTests`, `McpStdioProcessTests`, and `McpExecutionTests` ran 67 tests with zero failures or skips.
- `run-sample-validation.sh Release` passed 194 validator tests and validated three sample vectors. The pinned Commitlint CLI reported zero warnings and problems for the exact commit message.
- `git diff --check` passed.

### Independent review on 2026-11-27

- On `bcf8cf5d` with its pinned Builds revision, the three focused Release projects built with `-warnaserror`. `CatalogTests`, `PlatformScopeCommandTests`, `McpStdioProcessTests`, and `McpExecutionTests` passed all 131 tests.
- `bash tools/conformance-vectors/v1/run-sample-validation.sh Release` passed the 194 validator tests and all three sample vectors.
- `bash tools/conformance-vectors/v1/run-sample-loopback.sh` exited 0. Sample CLI/MCP replay, isolated and combined packaged enrollment, SDK response cases, and both negative evidence checks passed.
- A local stdio probe with the routing fixture and a loopback Gateway confirmed the aggregate override casing issue and the difference between the advertised schema and the paging guard.

### Review patches applied on 2026-11-27

- The `run_query` input schema and request guard reject ASCII case variants of `aggregateId`, `pageSize`, `offset`, and `cursor`. Canonical names and unrelated additional properties remain valid when their other arguments pass validation.
- Both stdio revisions check the aggregate alias, the cursor alias with offset, the complete error for a malformed explicit aggregate ID, and zero Gateway submissions. The MCP tests check mixed spellings and the advertised schema.
- Before the patch, all four stdio regression cases accepted the aggregate alias and both schema cases accepted it. After the patch, Release builds with `-warnaserror` and all 204 tests passed across the MCP suite, the focused CLI classes, and `CatalogTests`.
- The three packaged sample vectors passed CLI and MCP replay using `run_loopback.py`. `bash tools/conformance-vectors/v1/run-sample-validation.sh Release` passed 207 validator tests and all three sample vectors.
