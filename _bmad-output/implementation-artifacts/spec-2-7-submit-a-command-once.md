---
title: 'Submit a Command Once'
type: 'feature'
created: '2026-10-02'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - 'AGENTS.md'
  - 'references/Hexalith.AI.Tools/hexalith-llm-instructions.md'
  - '_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Shell users need to submit a declared Command through the EventStore Gateway once and receive the identifiers and accepted result needed to trace the action. The existing `send` path has limited acceptance evidence for payload sources, identifier handling, and uncertain outcomes.

**Approach:** Exercise the shared Core executor and CLI `send` command against synthetic Contracts and a bounded loopback Gateway. Fix only demonstrated gaps while preserving the common result contract and Catalog routing.

## Boundaries & Constraints

**Always:** Validate before submission and make one Gateway call on success, zero on refusal. Use Catalog Domain and WireType. Generate one ULID message ID per call; use it as correlation when none is supplied. Accept caller ULID correlation and idempotency values unchanged; never generate an idempotency key. Return the Gateway message ID when present, the resolved correlation ID, Tenant, aggregate ID, `status: accepted`, and only supplied/returned optional fields. Do not imply an uncertain outcome is safe to resubmit.

**Never:** Add module-specific code, dependencies, retries, a `duplicate` result field, or edits under `references/`. Do not change Query behavior or pull Story 2.8 identity and extension policy changes into this work.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Valid send | Decorated Command and valid Payload from inline JSON, `@file`, or stdin | One `SubmitCommandRequest` with Catalog routing; accepted result includes canonical trace IDs | No retry |
| Generated identity | No correlation or idempotency value; separate valid calls | Each call has a distinct ULID message ID; correlation equals that call's message ID; no idempotency key appears | N/A |
| Caller identity | Distinct valid correlation and idempotency ULIDs | Both reach the Gateway unchanged; result echoes only the supplied idempotency key | N/A |
| Refused call | Query passed to `send`, invalid Payload/ULID, or explicit aggregate disagrees with accessor | `validation_failed`; no Gateway call | Operation mismatch is `/operation`; aggregate mismatch is `/aggregateId` |
| Unknown outcome | Gateway timeout or other failed submission | One call only; failure does not claim deduplication or safe retry | Stable error document; no success result |
| Optional result | Successful Gateway response without a result payload | Accepted document omits `result` and `duplicate` | N/A |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs` — owns descriptor/kind gates, Payload validation, envelope IDs, aggregate resolution, one Gateway call, and result mapping. Preserve the existing execution order; fix only matrix failures.
- `src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs`, `AggregateIdAccessors.cs`, and `OperationDescriptor.cs` — establish interface/attribute routing and compiled aggregate accessors. Reuse these; do not reflect in a head.
- `src/Hexalith.McpCli/Cli/CliRunner.cs` (`CreateSend`, `ReadPayloadAsync`) and `CliOutput` — bind operation, payload sources, options, and shared output. Keep the CLI a translator.
- `tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs` — existing command route, validation, identity, and failure tests; extend the acceptance matrix here.
- `tests/Hexalith.McpCli.Cli.Tests/CliMcpCommandParityTests.cs` and `QueryCommandTests.cs` — loopback Gateway and payload-source patterns for the CLI path.
- `tests/Hexalith.McpCli.Sample.Contracts/CreateItemCommand.cs` and `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Commands/` — sample `ICommandContract` plus pinned request/response DTOs.

## Tasks & Acceptance

**Execution:**
- [ ] `tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs` — pin both mismatch directions, distinct generated IDs, distinct caller ULIDs, optional result omission, accessor disagreement, and timeout/no-retry behavior.
- [ ] `tests/Hexalith.McpCli.Cli.Tests/CliMcpCommandParityTests.cs` — cover inline, file, and stdin sends; assert one routed POST and the complete accepted document, including omission rules.
- [ ] `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs` — correct any behavior the acceptance tests prove wrong without adding retries or changing Query semantics.
- [ ] `README.md` — document the accepted Command result identifiers, optional fields, and uncertain Gateway outcomes.

**Acceptance Criteria:**
- Given a valid decorated Command and any supported CLI payload source, when `hexalith send` runs, then Core makes exactly one request using Catalog routing values and CLI output is the shared canonical success document.
- Given invalid command kind, Payload, envelope ID, or aggregate identity, when Core executes the call, then it returns the specified validation failure before any Gateway call.
- Given omitted or supplied caller identifiers, when a Command succeeds, then message/correlation/idempotency fields follow the matrix and the returned correlation matches the submitted value.
- Given a timeout or unknown outcome, when the Gateway call fails, then there is no retry and the error does not state that another submission is safe.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `dotnet build tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Debug --no-restore -m:1` — expected: zero warnings and errors.
- `dotnet build tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Debug --no-restore -m:1` — expected: zero warnings and errors.
- Run the focused Core and CLI acceptance classes, then each test project individually — expected: zero failures; report existing platform-only skips separately.
- `git diff --check` — expected: clean.
