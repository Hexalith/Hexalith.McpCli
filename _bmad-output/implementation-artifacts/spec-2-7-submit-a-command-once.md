---
title: 'Submit a Command Once'
type: 'feature'
created: '2026-10-02'
status: 'done'
baseline_commit: 'dbc10bb99715584848deb7d1a9aa58fcfc9994c4'
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
- [x] `tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs` — pin both mismatch directions, distinct generated IDs, distinct caller ULIDs, optional result omission, accessor disagreement, and timeout/no-retry behavior.
- [x] `tests/Hexalith.McpCli.Cli.Tests/CliMcpCommandParityTests.cs` — cover inline, file, and stdin sends; assert one routed POST and the complete accepted document, including omission rules.
- [x] `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs` — correct any behavior the acceptance tests prove wrong without adding retries or changing Query semantics.
- [x] `README.md` — document the accepted Command result identifiers, optional fields, and uncertain Gateway outcomes.

**Acceptance Criteria:**
- Given a valid decorated Command and any supported CLI payload source, when `hexalith send` runs, then Core makes exactly one request using Catalog routing values and CLI output is the shared canonical success document.
- Given invalid command kind, Payload, envelope ID, or aggregate identity, when Core executes the call, then it returns the specified validation failure before any Gateway call.
- Given omitted or supplied caller identifiers, when a Command succeeds, then message/correlation/idempotency fields follow the matrix and the returned correlation matches the submitted value.
- Given a timeout or unknown outcome, when the Gateway call fails, then there is no retry and the error does not state that another submission is safe.

### Review Findings

Code review 2026-10-02 of `dbc10bb..954a426` (excluding `_bmad-output/`); layers: Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor (none failed). Verification Gap confirmed both new Core tests fail if the correlation fix is reverted.

- [x] [Review][Patch] README does not say which `gateway_error` reasons are uncertain outcomes — medium (blind-hunter). A transport `HttpRequestException`, including a connection reset after the body was sent, becomes 503 `gateway-unreachable` with detail "The EventStore gateway could not be reached." That reads as not delivered, so a script may resubmit. Name `gateway-timeout` and `gateway-unreachable` as possibly delivered, whatever the detail text says. [README.md:65]
- [x] [Review][Patch] README wording suggests an invalid caller ID silently falls back — low (blind-hunter). "Uses it as correlation unless `--correlation-id` supplies a ULID" and "`--idempotency-key` accepts a caller ULID" do not say that a non-ULID value fails with `validation_failed` at `/correlationId` or `/idempotencyKey` (`OperationExecutor.cs:148-156`). [README.md:65]
- [x] [Review][Patch] README omits `send` exit codes and the `--aggregate-id` agreement rule — low (blind-hunter). The query paragraphs state exit 0 or 2 and the aggregate rule; the command paragraph does neither, though the executor applies the same accessor-agreement check to commands (`OperationExecutor.cs:201-205`). [README.md:65]
- [x] [Review][Patch] Timeout test asserts the root name of an anonymous object it built itself — low (blind-hunter). `new { error = outcome.Error }` always serializes with the single root `error`, so the assertion cannot fail. The test's other checks are real: no retry, no added `retryable`/`clientAction`, and no "safe" text. [tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs:441]
- [x] [Review][Patch] `CallerIdentifiersArePreservedAsync` uses `ItemId` as the Gateway's differing correlation — low (blind-hunter). It reads as a typo; a maintainer "correcting" it to `CorrelationId` would remove this test's proof that the Gateway value is ignored. Use a named Gateway-correlation constant and assert the result differs from it. [tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs:104]
- [x] [Review][Defer] An uncertain command failure carries no identifier to trace it — medium (verification-gap+blind-hunter) [src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:34] — deferred: pre-existing executor behavior; the transport failure document drops the generated message and correlation IDs, and the Gateway status endpoint is keyed by message ID. Resolved by user decision 2026-10-02: add a new ledger entry naming Story 2.9 as owner, so the error format is designed once, including the idempotency case (`deferred-work.md:276`).
- [x] [Review][Defer] Empty or whitespace Gateway `messageId` reaches the accepted document [src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:223] — deferred: pre-existing; already tracked (`deferred-work.md:274`, also `:52`); no new ledger entry.
- [x] [Review][Defer] Caller cancellation after the POST is reported as `internal_error`, not an unknown outcome [src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:38] — deferred: pre-existing; already tracked (`deferred-work.md:49`); no new ledger entry.

**Rejected**

- false — Gateway `retryable` passthrough contradicts the README caution (verification-gap+blind-hunter): the Gateway sets `retryable: true` only on idempotency-admission paths under a caller key (`SubmitCommandHandler.cs:112,162,218,243`). There its dedup makes the hint authoritative, and the epic requires passing optional metadata through when supplied.
- false — CLI loopback echoes the submitted correlation, so a revert passes (blind-hunter+edge-case-hunter): both new Core tests fail on a revert, and `CliRunner.CreateSend` writes the Core `CommandResult` without remapping.
- false — Gateway correlation silently dropped (blind-hunter+edge-case-hunter+acceptance-auditor): the pinned Gateway returns `request.CorrelationId` on every accept and replay path (`SubmitCommandHandler.cs:131,189,657` → `CommandsController.cs:163`), and the spec's Always list mandates the resolved correlation.
- false — Tests cannot tell Catalog routing from the Operation Name (acceptance-auditor): CI's `conformance-vector-loopback` job sends `sample.rename-item` through both heads and asserts `commandType: rename-item-wire` (`tools/conformance-vectors/v1/sample-rename.json:21`).
- false — Attribute-accessor aggregate mismatch untested (acceptance-auditor): attribute accessor extraction is pinned at `CatalogTests.cs:119`, and the executor's mismatch check is accessor-agnostic (`OperationExecutor.cs:201-205`).
- false — Wrong-kind refusal tested only in read-only mode (acceptance-auditor): the kind gate (`OperationExecutor.cs:66-71`) has no mode dependency and runs before availability; the read-only tests prove the stronger ordering.
- false — The 250 ms drain guards a case that cannot happen (blind-hunter): it catches a duplicate POST from the CLI head, which is AC1's "exactly one request"; a 202 retry is not the only source.
- low — Correlation and idempotency flags toggle together in the CLI theory (blind-hunter+edge-case-hunter): the spec matrix rows (none, both distinct) are covered, and a key-only cross-copy bug is unlikely; it would need new theory parameters.
- low — A duplicate arriving more than 250 ms after the 202 escapes the count (edge-case-hunter): no retry policy re-sends a success, and restructuring the listener is more than a direct fix.
- low — CLI test duplicates `QueryCliHarness`, and field-by-field asserts miss stray members (blind-hunter): the CLI passes null extensions when none are given (`CliRunner.cs:192`), and generalizing the query-path harness (`QueryCliHarness.cs:106`) is a refactor.
- low — README omits the extension allowlist and the required-key rule for `send` (blind-hunter): Story 2.8 owns identity and extension policy, which this spec's Never list keeps out.
- low — README does not call the returned `messageId` the status-tracking key (blind-hunter): the README already states its provenance; status guidance depends on the Decision above.
- low — The `"/"` prefix matches any path for the `[]` payload row (edge-case-hunter): the row still proves zero Gateway calls; the matrix fixes no root path, and exact matching would need a per-row branch.
- low — Free-port probe race (edge-case-hunter): an existing fixture pattern, already rejected as Edge 3 in the implementation review.

## Implementation Notes

- The executor returns the resolved correlation ID submitted to the Gateway even when a Gateway response contains a different correlation ID. The Gateway message ID still takes precedence when present.
- The Command result documentation now describes the message ID fallback and submitted correlation ID.
- Review tightened the timeout test to match the Gateway client's translated 503 error, made the CLI listener observe additional requests, and covered optional fields independently.

## Spec Change Log

## Review Triage Log

- **Blind 1 — medium, patch:** The new timeout test throws a raw `TimeoutException`, while `EventStoreGatewayClient.SendTranslatingAsync` wraps HTTP timeout as a 503 `EventStoreGatewayException`. The test therefore misses the actual Gateway timeout error mapping; use the translated exception and assert its stable fields.
- **Blind 2 — medium, patch:** The new CLI listener accepts only one request, so a second queued POST can escape its `calls == 1` assertion. Observe the listener for a bounded interval after the first response.
- **Blind 3 — low, patch:** `CallerIdentifiersArePreservedAsync` proves the generated message ID parses but does not prove it differs from the two caller IDs. Add direct inequality assertions.
- **Blind 4 — low, patch:** The new CLI test combines idempotency and result payload in one Boolean, leaving their independent omission unverified. Exercise all four combinations.
- **Blind 5 — false, reject:** A missing Gateway `messageId` is covered by `GeneratedIdentifiersAreDistinctAndOptionalFieldsAreOmittedAsync`; `CliRunner.CreateSend` serializes that same `CommandResult` without remapping it. The loopback fixture's always-present ID does not create a different fallback path.
- **Blind 6 — low, reject:** The CLI fixture covers success only, but `CliRunner.CreateSend` passes the Core `OperationOutcome` directly to the common `CliOutput.WriteAsync` path. Core failure and timeout tests cover single submission and stable errors; another HTTP fixture would add test machinery without exposing a distinct command path.
- **Blind 7 — false, reject:** Sprint status temporarily remains `in-progress` during review; workflow step 05 explicitly syncs it to `review` before presentation.
- **Edge 1 — medium, patch:** The second queued POST is invisible to the single-accept listener, the same root cause as Blind 2. Add bounded observation.
- **Edge 2 — medium, defer:** `SubmitCommandResponse.MessageId` can be empty or whitespace and the existing `response.MessageId ?? messageId` expression would return it, leaving an unusable tracking ID. This expression predates Story 2.7; handling malformed Gateway IDs needs its own response-policy decision.
- **Edge 3 — low, reject:** The free-port probe creates a narrow bind race, but the same loopback fixture pattern already exists in these tests. A retry loop adds complexity for an unlikely local test collision.

## Verification

**Commands:**
- `dotnet build tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Debug --no-restore -m:1` — passed, zero warnings and errors.
- `dotnet build tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Debug --no-restore -m:1` — passed, zero warnings and errors.
- `dotnet tests/Hexalith.McpCli.Core.Tests/bin/Debug/net10.0/Hexalith.McpCli.Core.Tests.dll -class Hexalith.McpCli.Core.Tests.OperationExecutorTests` — 29 passed.
- `dotnet tests/Hexalith.McpCli.Cli.Tests/bin/Debug/net10.0/Hexalith.McpCli.Cli.Tests.dll -class Hexalith.McpCli.Cli.Tests.CliMcpCommandParityTests` — 14 passed.
- `dotnet tests/Hexalith.McpCli.Core.Tests/bin/Debug/net10.0/Hexalith.McpCli.Core.Tests.dll` — 421 passed, 2 Windows-only skips.
- `dotnet tests/Hexalith.McpCli.Cli.Tests/bin/Debug/net10.0/Hexalith.McpCli.Cli.Tests.dll` — 338 passed.
- `git diff --check` — clean.
- `npx --no -- commitlint --edit /tmp/mcpcli-story-2-7-commit-YpXiGCXq.txt` — passed for `fix(command): preserve correlation when submitting a command once`.
