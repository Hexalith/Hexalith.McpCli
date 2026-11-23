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
- Story 5.24 is recorded as ready for review in sprint status. The affected CLI and MCP inputs retain the adopted precedence and validation rules.

## Review Triage Log

- Medium, patched. A mis-cased `Cursor` could disappear even with an offset. The filter now recognizes case variants of all three paging names. A regression checks `InvalidParams` and zero calls for `Cursor` with an offset.
- Low, documented. The SDK advertises an open argument schema and the incoming filter enforces exact paging names and numeric token spelling. The `run_query` description now names the case requirement. Closing the schema would also reject unrelated additional members.
- Medium, patched. Real stdio verifies optional discovery, defaults and valid overrides on both protocol revisions. Each case asserts the negotiated version and captured request.
- Medium, patched. A malformed explicit aggregate must fail even when a valid default exists. The CLI regression asserts the complete refusal and zero submissions.
- Low, patched. `HexalithQueryAttribute.AggregateId` remarks describe identifier-kind admission and explicit override behavior for module authors.
- Low, patched. The spec records the test commands and observed outcomes.
- Low, patched. The five original ledger entries link to the resolution table.
- Low, patched. The sprint tracker links Story 5.24 to this follow-up and records its review status.

## Verification

- The .NET 11 Release solution restore and build passed with the workspace's installed Aspire bundle. The first full Core, CLI and MCP suites reported 922, 632 and 96 passing tests. Six expected platform or benchmark tests were skipped.
- After the review patches, the Release CLI and MCP test builds passed with warnings treated as errors. The focused `PlatformScopeCommandTests`, `McpStdioProcessTests`, and `McpExecutionTests` ran 67 tests with zero failures or skips.
- `run-sample-validation.sh Release` passed 194 validator tests and validated three sample vectors. The pinned Commitlint CLI reported zero warnings and problems for the exact commit message.
- `git diff --check` passed.
