---
title: 'Harden request validation'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Close five deferred findings in the shared validation used by CLI and MCP. Reject an invalid schema evaluation even when the evaluator supplies no violation details. Return the extension count error as soon as a command exceeds 32 extensions. Verify that the existing SQL, LDAP, and event-handler checks each reject an allowlisted value before the Gateway receives a command.

</frozen-after-approval>

## Implementation Notes

- Base `40f5a38bdf91e541173bd91d193dfb2aeca44c92`. The five ledger findings share the Core request validation boundary.
- `PayloadValidator` preserves detailed evaluator violations when available and supplies a fixed root violation when an invalid evaluation has no details. The test uses a temporary dialect with a keyword that reports failure without a diagnostic, through the normal List evaluation path.
- `OperationExecutor` captures at most 33 extension entries and `ExtensionValidator` returns the count violation before checking members. The regression checks bounded enumeration, the complete error document, and zero Gateway calls. Separate theory cases cover both reachable SQL and LDAP alternatives and the event-handler check.

## Review Triage Log

- Medium, patched. Bound the executor snapshot as well as the validator's member checks.
- Low, patched. Describe the count error at the extension validation stage, where the rule applies.
- Low, patched. Exercise the fallback through `PayloadValidator.Validate` with the pinned evaluator's List output.
- Low, verified. Exercise six extension refusals through the built CLI and MCP stdio fixture and compare each public error document.
- Low, patched. Describe `/` as the product's payload root marker.
- Low, patched. Record the executed checks and link the five ledger resolutions to this verification section.
- Low, patched. Replace stale ledger line numbers with symbols and current test names.

## Verification

- `dotnet restore Hexalith.McpCli.slnx` and the Release solution build with `-warnaserror -m:1` passed with no build warnings or errors.
- All 186 `SchemaTests` and `OperationExecutorTests` passed.
- Six process-level cases in each head returned matching validation documents. CLI returned exit 2 and empty stderr. MCP set `isError` and returned matching structured and text content.
- `bash tools/conformance-vectors/v1/run-sample-validation.sh Release` passed 203 tests and validated three sample vectors. All three sample vectors replayed successfully through both heads.
- The shared pinned commitlint accepted the exact commit message with zero problems and warnings.
