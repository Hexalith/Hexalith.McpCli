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

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` — succeeds with pinned package versions.
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` — succeeds without warnings.
- `dotnet test tests/Hexalith.McpCli.Mcp.Tests --no-build --configuration Release` — passes the Story 3.1 SDK protocol cases.
- `git diff --check` — reports no whitespace errors.
