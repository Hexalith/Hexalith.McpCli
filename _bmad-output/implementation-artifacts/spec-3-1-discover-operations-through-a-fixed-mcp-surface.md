---
title: 'Discover Operations Through a Fixed MCP Surface'
type: 'feature'
created: '2026-10-10'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '12b54bd245fdff2ed443a37d2335ef9c329aa2e6'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** An agent needs predictable discovery across changing Contracts catalogs. The existing MCP head registers the fixed tools, but its descriptions lack the required discovery guidance and protocol coverage does not prove the full Story 3.1 contract.

**Approach:** Complete the five generic tool descriptions and verify their advertisement and discovery behavior through the pinned MCP SDK, reusing the Core Catalog documents and availability rules.

## Boundaries & Constraints

**Always:** Advertise `list_modules`, `list_operations`, `describe_operation`, `send_command`, `run_query` in order; omit only `send_command` in read-only sessions. Descriptions have labeled `Purpose`, `Use when`, and `Next` guidance. Discovery and `run_query` have `readOnlyHint: true`; `send_command` has `readOnlyHint: false`, `idempotentHint: false`, `destructiveHint: true`. Keep five names, descriptions, and input schemas below 8,000 characters. Retain SDK creation and dispatch, one filtered collection, and the post-handler ordering filter. Discovery works without a Gateway URL; direct writes remain gated by Core.

**Never:** Generate one tool per Operation, reimplement Catalog documents in the MCP head, alter Core's tenant or availability precedence, or expand this story into stdio startup and execution-result work owned by Stories 3.2 and 3.3.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Tool discovery | Normal or read-only session, any Catalog size | Five or four fixed ordered tools with required annotations and labels within budget | No extra or duplicate tools |
| Offline discovery | Catalog with no Gateway URL | Module counts, filtered Operations, and described Schema/example/Envelope/lint plus `submittable: false` and `configuration_invalid` reason | No startup or discovery failure |
| Module lookup | `list_operations` with read/write `kind`, unknown, missing, or empty `module` | Filtered Core document; unknown name gets up to three suggestions | Missing or empty name yields MCP InvalidParams before tool invocation |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs` — fixed collection, SDK creation, descriptions, annotations, input filter, and post-handler ordering; retain its structure.
- `src/Hexalith.McpCli.Mcp/McpToolHandlers.cs` — maps discovery to `ICatalog` and serializes Core documents; reuse.
- `src/Hexalith.McpCli.Core/Catalog/CatalogService.cs` and `ExecutionAvailability.cs` — counts, filters, suggestions, description fields, and offline/read-only state; no Core change expected.
- `tests/Hexalith.McpCli.Mcp.Tests/McpToolRegistrationTests.cs` — existing count, schema, budget checks; add labels and annotations.
- `tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs` — in-process SDK streams for legacy and 2026-07-28 revisions; extend discovery cases.
- `README.md` — existing MCP documentation.

## Tasks & Acceptance

**Execution:**
- [x] `src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs` — replace each tool description with concise labeled guidance that leads an agent from modules to Operations to description and then the appropriate execution tool; retain the budget and annotations.
- [x] `tests/Hexalith.McpCli.Mcp.Tests/McpToolRegistrationTests.cs` — assert exact ordered names, three labels, annotation values, one filter, and the total name/description/input-schema budget for both modes.
- [x] `tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs` — assert fresh SDK `tools/list` order and three discovery documents across both revisions and modes, kind filters, no URL, unknown and missing/empty modules, and Catalog growth. Compare structured documents with Core serialization and inspect required/optional fields.
- [x] `README.md` — document the discovery sequence and read-only visibility using built behavior.

**Acceptance Criteria:**
- Given a normal or read-only session, when an SDK client lists tools, then it sees exactly the permitted names in fixed order with the specified annotations and labeled guidance, within the 8,000-character input budget.
- Given a Catalog and no Gateway URL, when an SDK client calls the discovery tools, then it receives §G documents with correct counts, filters, Schema, optional example, Envelope, lint findings, and head-level `submittable` state; read-only takes precedence for write availability.
- Given a nonempty unknown Module, when the client lists its Operations, then it receives `unknown_module` with at most three suggestions; given missing or empty `module`, it receives protocol InvalidParams before Catalog dispatch.
- Given Catalog growth, when a new SDK session lists tools, then no per-Operation tool appears and read-only still omits only `send_command`.

## Implementation Notes

- Added labeled guidance to the five existing SDK tools without changing their collection, filters, annotations, or Core dispatch.
- Extended MCP tests with Catalog routing and lint fixtures for optional example and nonempty lint findings. SDK `tools/list` tests assert advertisement order because the SDK collection's iteration order is not stable.
- Verified restore, warning-free Release build, 14/14 MCP tests, and 558/560 Core tests (two Windows-only skips). The Core run covers the existing direct write refusal in read-only mode.
- Review fixes clarified availability guidance and added required-input, envelope, empty-module, suggestion-cap, and next-tool assertions. Final restore, Release build, and 14/14 MCP tests passed; output-schema fixtures and version-specific stdio flows were deferred to Stories 3.3 and 3.2.
- Commit candidate `feat(mcp): complete fixed operation discovery surface` passed the pinned `npx --no -- commitlint --verbose` check after `npm ci`: 0 problems, 0 warnings.

## Spec Change Log

## Review Triage Log

- [Review][BH1][low][patch] `README.md:124` presents five tools before the read-only exception. The count is ambiguous in isolation; state normal and read-only counts explicitly.
- [Review][BH2][medium][patch] `McpCliMcpServiceCollectionExtensions.cs:31` and `README.md:124` direct a read to `run_query` without checking `submittable`. Offline descriptions report unavailable reads, so qualify the next step.
- [Review][BH3][medium][defer] `McpToolRegistrationTests.cs:33` checks only the output-schema `oneOf` count; success/error fixture validation is absent. The schema and test predate this change, and Story 3.3 explicitly owns validation of both branches.
- [Review][BH4][low][patch] `McpToolRegistrationTests.cs:54` checks only two tools' required fields; the new surface test can miss a changed discovery or command input schema. Assert the remaining required fields and kind's supported calls.
- [Review][BH5][low][patch] `McpProtocolTests.cs:123` reads envelope booleans without asserting values; wrong caller guidance could survive the MCP test despite Core parity. Assert the sample read/write envelope values and argument names.
- [Review][BH6][medium][patch] `McpProtocolTests.cs:42` lacks an empty module, so this MCP test would miss an omitted or null `operations` array. Include the existing marked-empty fixture and assert its document.
- [Review][BH7][medium][patch] `McpProtocolTests.cs:166` checks a three-suggestion cap with at most three modules, so removing the cap could pass. A fourth fixture module makes the bound testable.
- [Review][BH8][medium][defer] `McpProtocolTests.cs:61` varies protocol versions through one client setup but does not prove distinct negotiated flows. Story 3.2 explicitly owns the version-appropriate session exchange over stdio.
- [Review][VG1][medium][patch] `McpProtocolTests.cs:64` checks description labels but not their next-tool guidance. Replacing `describe_operation` with immediate execution in the guidance would pass; assert the advertised sequence.
- [Review][EH1][false][reject] `McpToolRegistrationTests.cs:26` sorts collection names for membership because SDK collection iteration is not the public order. `McpProtocolTests.cs:64` asserts the actual `tools/list` order in every session, so the claimed advertisement gap does not occur.

### Review Findings

Code review 2026-10-11 of `12b54bd..68c0475`. Layers: Blind Hunter, Edge Case Hunter, Verification Gap and Acceptance Auditor; none failed, and Verification Gap reported no gaps. The Acceptance Auditor found no violation of the acceptance criteria or the Always/Never constraints and reran the 14 MCP tests green on the current Release build.

All nine patches were applied. After them, `dotnet restore Hexalith.McpCli.slnx` and the warning-free Release build succeeded, `dotnet test tests/Hexalith.McpCli.Mcp.Tests --no-build --configuration Release` passed 14/14, and `git diff --check` was clean. Temporarily deleting the handler's `kind` guard failed the new `kind: "Read"` case, and the restored handler is byte-identical.

- [x] [Review][Patch] The `send_command` guidance never warns that an uncertain outcome may already have been accepted. Its `Next:` says only "Inspect the accepted result or error before any further action", while `README.md:67` tells CLI users that `gateway-timeout` and `gateway-unreachable` outcomes may have reached the Gateway and that resubmitting is not safe. An agent is the caller most likely to retry an `isError` result automatically, and the outcome is a duplicate destructive write. Extend `Next:` with that caution, keep the three labels, keep the input budget below 8,000 characters, and assert the caution in both MCP test files. [src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs:39]
- [x] [Review][Patch] The README MCP paragraph says that without a Gateway URL descriptions report `reason: configuration_invalid`, but a write in a read-only session without a URL reports `read_only` (`ExecutionAvailability.cs:10`, asserted at `McpProtocolTests.cs:147-150`). The CLI paragraph says `read_only` is reported first; state the same precedence here. [README.md:124]
- [x] [Review][Patch] The README MCP paragraph says to execute "When the description says `submittable: true`" without the caveat at `README.md:89`: `submittable` reflects only read-only mode and whether a URL is configured, not the token, tenant, actor, or Gateway reachability. Add that clause so operators do not read `submittable: true` as a promise that the call succeeds. [README.md:124]
- [x] [Review][Patch] No MCP test sends an invalid `kind`. Core's `ListOperations` throws `ArgumentException` for any other value (`CatalogService.cs:27-29`), so deleting the handler guard (`McpToolHandlers.cs:28-31`) would turn `kind: "Read"` into a generic `internal_error` with the suite still green. Add a `kind: "Read"` case asserting the full `invalid_arguments` document for `kind`. This story's `kind` loop already covers the valid-kind half of `deferred-work.md:90`; mark that entry resolved. [tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs:109]
- [x] [Review][Patch] The `fixedTenant` assertion cannot tell the module's value from the session's. The test's session tenant and `Sample.Contracts`' `FixedTenant` are both `sample-tenant`, so a head that substituted the session tenant would pass both the field check at `:139` and the Core-parity comparison. Use a distinct session tenant such as `session-tenant`. [tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs:40]
- [x] [Review][Patch] The Catalog-growth check lists tools before the Catalog exists. `CatalogProvider` builds it lazily on first access (`CatalogProvider.cs:21`), and the test first touches it in the `list_modules` call after `tools/list`, whereas production builds the Catalog before serving. List tools again after the discovery calls and assert the same ordered names. [tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs:65]
- [x] [Review][Patch] The InvalidParams cases assert only the error code. Also assert the messages (`module is required and must be non-empty.` and its `operation` variant), following the repo's full-error-document rule. A protocol error, not an `invalid_arguments` tool result, already shows the handler did not run; only the message is unpinned. [tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs:211]
- [x] [Review][Patch] Neither protocol-revision row asserts the negotiated version, so a silent fallback would collapse the two revisions into one. SDK 2.2.0 exposes `McpSession.NegotiatedProtocolVersion`; assert it equals `protocolVersion` after client creation, and narrow the evidence at `deferred-work.md:442` to the stdio flow work Story 3.2 still owns. [tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs:62]
- [x] [Review][Patch] The two Story 3.1 ledger entries omit the medium severity their triage gave (BH3, BH8), unlike neighbouring spec-2-11 and DW entries, so a ledger sweep must regrade them. Prefix each evidence with `Medium.` [_bmad-output/implementation-artifacts/deferred-work.md:439]
- [x] [Review][Defer] The README does not say how MCP failures reach the client: `isError: true` with `{"error": …}` in `structuredContent` and the first text item, and protocol InvalidParams for a missing or blank `module` or `operation` [README.md:124] — deferred: pre-existing behavior this change did not alter; Story 3.3 pins the MCP error contract and should document it in the same change.
- [x] [Review][Defer] MCP input schemas carry no parameter descriptions or `kind` enum, so agents see `payload` as a bare string with no hint that it is JSON text [src/Hexalith.McpCli.Mcp/McpToolHandlers.cs:20] — deferred: pre-existing handler signatures; Story 3.3 binds the §E arguments and must fit any added descriptions within the 8,000-character input budget.

Rejected:

- `low` The spec says `done` while sprint status says `review`, and `review_loop_iteration` stays 0 after a review loop (Blind Hunter, Acceptance Auditor). This review's status step sets both from its outcome; the counter is a spec edit.
- `low` `context: []` omits `epic-3-context.md` (Blind Hunter). The fix edits the spec under review.
- `low` The Verification section omits the Core test command and the Code Map omits the new fixture references (Blind Hunter). The fix edits the spec under review.
- `low` The BH3 and BH8 triage rows cite `:33` and `:61` and use a different row format (Blind Hunter). The ledger's `:34` and `:62` anchors are correct; changing the rows edits the spec under review.
- `low` The registration-test task says "exact ordered names" while the test sorts (Acceptance Auditor). EH1 showed the protocol test asserts the advertised order in every session; rewording the task edits the spec under review.
- `low` No test makes the advertisement filter throw (Blind Hunter). It checks a collection this method builds itself, so the throw is unreachable today, and the fix needs a new fake-handler harness. The companion flakiness claim is `false`: every protocol session asserts the advertised order, so dropping the reorder fails unless unordered SDK iteration happens to match it.
- `false` No MCP test shows a read-only session refusing a direct `send_command` (Blind Hunter). The tool is not registered then, so the SDK cannot dispatch it; registering it would fail the four-tool `tools/list` and registration-count assertions, and Core tests its executor refusal.
- `false` The input budget is measured server-side and output schemas are unmeasured (Blind Hunter). The SDK serializes the same `ProtocolTool` objects in `tools/list`, and Story 3.3's acceptance criteria own output-schema measurement.
- `false` The expanded-Catalog cases are thin: no expanded-plus-URL row, an unchecked routing-fixture `tenant` argument and `idempotencyKeyRequired`, unordered suggestions, and one large theory (Blind Hunter). `AssertCoreDocument` deep-compares every MCP document with Core serialization, and `CatalogServiceTests` and `CatalogTests` pin those fields.
- `false` A whitespace-only or JSON-null `module` is never sent (Edge Case Hunter). The incoming filter shares one predicate across tools, so weakening `IsNullOrWhiteSpace` fails the existing `operation = " "` case, and JSON null takes the same branch as the tested missing key.
- `false` Required discovery members such as descriptions, describe `name` and `kind`, and lint `code`, `severity`, and `message` are not inspected directly (Acceptance Auditor). The Core-parity deep comparison covers the head; field presence is tested in Core.
- `false` `submittable` is never shown to ignore an unresolved tenant (Acceptance Auditor). `ExecutionAvailability` takes only read-only mode and URL presence, so the tenant cannot affect it, and the head returns Core's document unchanged.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` — succeeds with pinned package versions.
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` — succeeds without warnings.
- `dotnet test tests/Hexalith.McpCli.Mcp.Tests --no-build --configuration Release` — passes the Story 3.1 SDK protocol cases.
- `git diff --check` — reports no whitespace errors.
