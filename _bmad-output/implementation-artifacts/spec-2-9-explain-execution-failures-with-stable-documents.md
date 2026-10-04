---
title: 'Explain Execution Failures with Stable Documents'
type: 'feature'
created: '2026-10-04'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Coverage omits malformed and semantic Gateway responses, unexpected exceptions, and exhaustive serialization contracts. Some validation paths and messages obscure the failed input.

**Approach:** Test shared records against §G and the pinned client through bounded loopback HTTP; correct gaps.

## Boundaries & Constraints

**Always:** Failures contain only `{ "error": ... }`. Preserve the actual client exception status, including 2xx; detail falls back from nonblank Detail to Title, then a generic message. Reason falls back through ReasonCode, Code, Reason. Optional metadata comes only from the exception; preserve false and omit absent/blank values. Unexpected failures use a generic `internal_error` message without exception text, stack trace, or token. Ordinary CLI failures go to stdout, exit 2, and leave a requested result file unchanged; MCP startup errors retain stderr-only routing.

Use case-insensitive edit distance and ordinal ties for at most three canonical suggestions. Validation includes the requested operation and nonempty pointer/message violations. Preserve all Schema violations and existing envelope gate ordering. Invalid accessor-derived identifiers use their mapped payload pointer when available; explicit, constant, or computed sources use `/aggregateId`. Distinguish missing tenant, invalid tenant syntax, cursor length, and cursor/offset conflict.

Retain canonical uppercase ULIDs and trusted identity ownership. Local refusals make zero calls; Gateway failures follow one submission without retry or replay classification.

**Never:** Add generated tracking fields to errors, module-specific logic, new dependencies, transports, or `references/` edits. Preserve the existing successful document contract. General parser redesign belongs to Story 2.11.

**Decision (2026-10-04):** Keep additional successful-response hardening deferred, including invalid returned identifiers and paging metadata. Client-reported malformed responses and semantic failures remain in scope.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected behavior | Failure |
|---|---|---|---|
| Gateway rejection | Complete Problem Details or absent/blank metadata | Exact status/detail; supplied metadata only | `gateway_error`, one call |
| Successful HTTP failure | Malformed Command 202, malformed Query 200, semantic Query failure | Client exception status survives unchanged | `gateway_error`, no result |
| Unknown operation | Typo or differently cased requested name; either call kind or describe | Requested name retained; identical capped, ordered suggestions | `unknown_operation`, zero calls |
| Validation | Nested Schema failures; invalid derived ID; missing tenant; cursor rules | All Schema paths, escaped mapped pointers, rule-specific messages | `validation_failed`, zero calls |
| Unexpected failure | Exception containing a token and stack-like text | Fixed safe message, no raw exception data | `internal_error`, no result |
| Serialization | All §G successes and 11 error codes; omitted/present optionals | Exact members/types/constants, empty arrays, required null query document, explicit JSON-null command result | CLI errors always exit 2 |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Core/Execution/OperationError.cs` — reuse `FromGateway`.
- `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs` — shared lookup, validation, mapped `PropertyBindings`, and exception guard.
- `src/Hexalith.McpCli.Core/Catalog/CatalogService.cs` — reuse canonical suggestions without a second algorithm.
- `src/Hexalith.McpCli/Cli/CliOutput.cs` and `CliRunner.cs` — shared error wrapper and guards; distinguish expected profile/configuration failures from unexpected action I/O.
- `tests/Hexalith.McpCli.Cli.Tests/DiscoveryCommandTests.cs` — lookup ordering coverage; `QueryCliHarness.cs` and parity tests supply loopback patterns.
- `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/addendum.md` §G — exhaustive public document contract.

## Tasks & Acceptance

**Execution:**
- [ ] `tests/Hexalith.McpCli.Core.Tests/ResultDocumentContractTests.cs` — add every §G success/error fixture; assert exact member sets, types, constraints, lint variants, availability reasons, optionals, arrays, and arbitrary result/document JSON kinds.
- [ ] `tests/Hexalith.McpCli.Core.Tests/OperationErrorTests.cs` — extend complete JSON assertions, blank-value fallback precedence, absent metadata, and true/false retry hints.
- [ ] `tests/Hexalith.McpCli.Core.Tests/ExecutionFailureTests.cs` — test both call kinds, lookup parity, safe unexpected failures, derived identifier pointers, and distinct validation messages; assert zero/one calls.
- [ ] `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs` — correct derived pointers and distinct messages; retain shared validation order and Gateway mapping. Update pinned expectations in `tests/Hexalith.McpCli.Core.Tests/QueryValidationTests.cs` and the CLI `QueryValidationCommandTests.cs` and `QueryPagingCommandTests.cs`.
- [ ] `tests/Hexalith.McpCli.Cli.Tests/ExecutionFailureCommandTests.cs` — real HTTP fixtures for Problem Details, malformed successes, and semantic failures; assert errors, status, exit 2, one request, bounded cleanup. Test unexpected action failures and all error variants through `CliOutput`, including table mode and existing output files.
- [ ] `src/Hexalith.McpCli/Cli/CliRunner.cs` — prevent unexpected action I/O from exposing raw exception text; preserve expected profile/configuration errors. Fix serializer or output behavior only if contract tests demonstrate a defect.
- [ ] `README.md` — document failure contracts and 2xx Gateway errors.
- [ ] `_bmad-output/implementation-artifacts/deferred-work.md` — mark resolved pointer/message/action-I/O entries with evidence; preserve unrelated and response-policy deferrals.

**Acceptance Criteria:**
- Given each matrix fixture, when exercised through Core or CLI, then its complete document and call count match the expected behavior.
- Given a failed CLI invocation, when it finishes, then stdout contains one error document, exit is 2, no success is emitted, and any result file is unchanged.
- Given the finished change, when suites run individually, then all acceptance cases execute and existing tests pass.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

Build and test each project individually; require zero warnings/errors, passing matrix coverage, and only existing platform-specific skips:

```sh
for lane in Core Cli Mcp; do
    dotnet build "tests/Hexalith.McpCli.$lane.Tests/Hexalith.McpCli.$lane.Tests.csproj" --configuration Debug --no-restore -m:1 || exit
    dotnet "tests/Hexalith.McpCli.$lane.Tests/bin/Debug/net10.0/Hexalith.McpCli.$lane.Tests.dll" -result-xml "/tmp/mcpcli-story-2-9-$lane.xml" || exit
done
git diff --check
```

Run focused new classes first; inspect XML and changed C# CRLF checks.
