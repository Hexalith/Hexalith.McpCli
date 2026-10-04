---
title: 'Explain Execution Failures with Stable Documents'
type: 'feature'
created: '2026-10-04'
status: 'done'
baseline_commit: 'dc5d783c610dd155f11b0f1763cb35efb05bdf13'
route: 'dispatch'
review_loop_iteration: 2
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

- Shared catalog lookup and Gateway exception mapping were already in place. Preserve and pin their complete documents and one-call behavior.
- Derived String identifiers should report their mapped payload pointer; explicit identifiers retain `/aggregateId`. Existing discovery and query validation tests cover suggestion ordering, nested escaped Schema pointers, and explicit-source pointers.
- `QueryPagingCommandTests.cs` had no pinned message to change in the first pass; verify that remains true.
- A result-file implementation must preserve existing output-path behavior on success: honor an existing file's write restrictions and security metadata, and write through a symbolic link to its target without replacing the link. A failed write or replacement must leave the existing target bytes and link unchanged and remove its temporary file. Use a same-directory temporary file with private permissions until commit; test a failure after that file has been written while an existing result is present.
- Exercise a String-kind aggregate accessor whose serialized name contains both `/` and `~`, so an invalid derived value proves the escaped payload pointer end to end. Add a real CLI `@file` action-failure test, blank or absent Gateway Problem Details over loopback HTTP, and a real table plus output failure invocation.


- For existing result files, stage replacement bytes and backup in a private system temporary location so a writable file in a directory without write permission still works. A write-only file cannot be backed up; refuse it before mutation with a stable internal error. Keep Unix mode, named ACL, and symlink-target identity for successful existing-file writes. A caught write failure after truncation must restore original bytes; process interruption or a second failure during rollback remains an operational limitation.
- Provide a deterministic fault-injection test after destination truncation, and verify restored bytes, mode, ACL where supported, link, and temporary cleanup. If a temporary file cannot be deleted after a committed write, do not report an invocation failure with a changed destination.
- Setup/profile-read I/O must not echo exception paths into public error messages. Keep expected profile validation specific. For Gateway error correlation IDs, include only supplied valid ULIDs; never invent one. Exercise a Problem Details status different from the HTTP response status, and document exception status. On Linux without POSIX ACL support, retain mode coverage without introducing a skipped test.

## Spec Change Log

- Review loop 1 (2026-10-04): Replacement-file findings showed the first implementation changed private-file permissions, bypassed read-only restrictions, and replaced symbolic links while reporting success. The plan also lacked a failed-existing-file commit test and an escaped derived-ID execution fixture. The non-frozen implementation notes now require preservation of output-file semantics and executable proofs for these cases, avoiding the known-bad fresh-file replacement behavior.
  **KEEP:** Preserve the complete §G document fixtures, pinned-client 202/200 malformed-response and semantic-failure loopback tests, one-call and zero-call assertions, mapped String identifier pointer correction, distinct tenant/cursor messages, safe generic action errors, and the three resolved deferred-work entries. Preserve the approved frozen intent verbatim.


- Review loop 2 (2026-10-05): Independent reviewers found that same-directory staging rejects writable existing files in unwritable directories, unreadable write-only files cannot be backed up, and the failure tests never force an exception after truncation. The implementation notes now distinguish safe refusal from a successful overwrite and require a deterministic rollback test. They also require generic setup I/O errors, valid Gateway correlation IDs, portable ACL coverage, and cleanup that cannot report failure after a completed write. The known-bad state is a changed output file paired with exit 2 or leaked setup paths.
  **KEEP:** Preserve the complete §G fixture set, real 409/202/200 pinned-client loopback cases, mapped escaped identifier pointer, distinct tenant/cursor messages, generic action failure, Unix mode/link/ACL preservation for writable readable files, and previously resolved deferred-work entries. Preserve the approved frozen intent verbatim.

## Review Triage Log

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| Blind 1: private result mode | high | bad_spec | `CliOutput.WriteResultFileAsync` replaces a 0600 destination with a new file; a local CLI run left it at 0644. The replacement design omitted destination security metadata. |
| Blind 2: read-only destination | medium | bad_spec | `File.Move(..., overwrite: true)` succeeded against a 0444 destination in a writable directory; the previous direct write would have refused it. |
| Blind 3: symbolic-link destination | medium | bad_spec | The same move replaces the link itself; a local CLI run exited 0, changed the link to a regular file, and left its target stale. |
| Blind 4: profile action I/O text | medium | patch | `RunManagementAsync` passes profile action `IOException` and `UnauthorizedAccessException.Message` into `configuration_invalid`; presentation-only host creation does not read the profile first. This still exposes action paths. |
| Blind 5: failed existing-file replacement test | medium | bad_spec | The directory-target failure test has no existing result file, while the existing-file test succeeds. Neither exercises failure during an attempted replacement of an existing file. |
| Blind 6: blank HTTP metadata | medium | patch | Loopback tests cover complete Problem Details and malformed success, while blank or absent metadata is exercised only with a constructed client exception; the pinned HTTP parsing path lacks that fixture. |
| Blind 7: MCP Gateway error protocol | medium | defer | `McpProtocolTests` covers an unknown operation error but no Gateway failure with 2xx status. The MCP protocol test gap predates this change and belongs with the MCP execution work. |
| Blind 8: escaped derived-ID pointer | medium | bad_spec | `QueryValidationTests` covers `/Key`; `CatalogTests` proves an escaped binding exists, but no execution failure asserts that escaped pointer. A String-kind escaped fixture is needed to reach the new executor branch. |
| Blind 9: combined table/output failure | low | patch | `CliOutput` is tested directly with table and output, and real CLI failures are tested with output separately; no actual invocation combines both flags on a failure. A direct CLI case is a small addition. |
| Verification 1: action guard bypassed by test | medium | patch | The output-write test is caught inside `CliOutput`; a missing `@file` reaches the changed `CliRunner` action catch and is not tested. |
| Verification 2: failed existing-file replacement | medium | bad_spec | The verified coverage search found success replacement, directory-target failure, and Gateway failure only; a partial write or commit failure with an existing result is untested. |
| Verification other 1: private result mode | high | bad_spec | The reviewer ran the CLI against a 0600 file and observed 0644 after success, matching Blind 1. |
| Verification other 2: symbolic-link destination | medium | bad_spec | The reviewer ran the CLI against a link and observed replacement of the link with an unchanged target, matching Blind 3. |
| Edge 1: private result mode | high | bad_spec | The new temporary file receives default permissions before the replacement, so a stricter existing file can become readable to others. |
| Edge 2: symbolic-link destination | medium | bad_spec | The prior direct write followed the output link; the new move replaces it and reports success, leaving the target stale. |
| Edge 3: unknown CLI verb | medium | defer | System.CommandLine handles unknown verbs before a verb action with help and exit 1. This predates Story 2.9, and the frozen intent assigns general parser redesign to Story 2.11. |

Review groups: the replacement-file semantics (Blind 1–3, Verification other 1–2, Edge 1–2), existing-file failure proof (Blind 5, Verification 2), and escaped derived-ID proof (Blind 8) require a spec-level correction. The remaining current-story gaps are small patches; the MCP protocol and parser findings are pre-existing deferrals.


### Review loop 2

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| Blind 1: write-only existing result | medium | bad_spec | The new `FileAccess.ReadWrite` open needs read permission although the previous direct writer needed only write permission. Backing up unreadable bytes is impossible; fail before mutation and document that safe refusal. |
| Blind 2: unwritable destination directory | medium | bad_spec | A writable existing file can be opened without directory write permission, but the new sibling temporary creation fails first. Existing-file staging can use a private system temporary directory. |
| Blind 3: new-result mode | low | reject | A new result now has private mode rather than the previous umask-derived mode, which can prevent file sharing. No sharing consumer is shown, and restoring ambient permissions would weaken the private staged-file design. |
| Blind 4: backup disk space | low | reject | Two staged copies can exhaust storage for unusually large results. Removing the backup would lose recoverable failure protection; this is unlikely in ordinary CLI use. |
| Blind 5: UTF-8 allocation | low | reject | `Encoding.UTF8.GetBytes` allocates a second full representation. The result is already materialized as a JSON string; streaming would add complexity for an uncommon large-result case. |
| Blind 6: post-truncation failure test | medium | bad_spec | The read-only test fails before `SetLength(0)` and cannot verify rollback after partial writes. Add a controlled fault after truncation. |
| Blind 7: symlink retarget race | low | reject | If another process retargets a link between resolution and open, the old target receives the result. Coordinating concurrent external link changes would add substantial path-handling complexity for an uncommon race. |
| Blind 8: Gateway correlation ULID | medium | patch | `FromGateway` forwards a nonblank arbitrary correlation string, while §G requires a ULID. The pinned client accepts response text without ULID validation; omit invalid values and test it. |
| Blind 9: profile-read message | medium | bad_spec | `SettingsResolver` includes `exception.Message` in `configuration_invalid`, which can contain the profile path. The safe action catch does not cover a returned setup error. |
| Blind 10: POSIX ACL fixture portability | medium | patch | The Linux test assumes its temporary filesystem accepts `system.posix_acl_access`; on a filesystem without ACL support `setxattr` fails before behavior is tested. Keep a mode-only fallback without a new skip. |
| Blind 11: Gateway status documentation | low | patch | The client can use Problem Details `status` instead of the HTTP response status. README should say client exception status and a mismatch fixture should pin that behavior. |
| Verification 1: post-truncation rollback | medium | bad_spec | The cited tests cover successful replacement and a pre-write refusal only; a broken restore would pass. A deterministic post-truncation failure test is needed. |
| Verification other 1: unwritable directory | medium | bad_spec | Reviewer reproduced success with direct write and `internal_error` with the new sibling staging for an existing file in a 0555 directory. |
| Verification other 2: write-only file | medium | bad_spec | Reviewer reproduced success with direct write and `internal_error` with the new backup read requirement for a 0200 existing file. Safe refusal must be explicit. |
| Edge 1: write-only file | medium | bad_spec | Same reachable `FileAccess.ReadWrite` restriction as Blind 1; a previously writable output path now fails. |
| Edge 2: failed rollback | high | bad_spec | A restore failure after truncation leaves partial target bytes despite exit 2. The in-place method cannot promise recovery from process interruption or a second I/O failure; state this operational limit and test recoverable failures. |
| Edge 3: cleanup failure after write | medium | patch | `finally` deletes the staged file after an existing destination has already changed. If deletion throws, the CLI reports failure with modified output; cleanup after commit must not reverse the reported outcome. |
| Edge 4: profile-read message | medium | bad_spec | `SettingsResolver` embeds profile I/O exception text in a returned configuration error, so the new `RunAsync` exception guard cannot mask the path. |

Review loop 2 groups: existing-file staging and unreadable destinations, recoverable rollback proof, and setup-error safety require non-frozen specification correction. Correlation filtering, ACL test portability, status wording, and cleanup reporting are direct patches to carry into re-implementation. The low findings above are rejected after verification.


### Review loop 3

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| Blind 1: dangling output symlink | medium | patch | A local .NET 10 probe shows `File.Exists` is true for a dangling symlink; the current existing-file path then fails opening its absent target. The prior direct writer followed the link and created that target. Resolve the final link target before choosing new versus existing output. |
| Blind 2: ignored temporary cleanup failure | low | reject | `TryDelete` can leave a staged result or backup if deletion fails, but the files have private mode and unpredictable names. Reliable retry across process exits would add state for an uncommon filesystem failure. |
| Blind 3: invocation-level post-truncate fault | low | reject | The direct fault test verifies rollback after truncation; real CLI tests independently verify that action I/O is caught as one `internal_error` with unchanged output. A combined injection hook through `CliRunner` would duplicate both checks. |
| Blind 4: ACL setup errors hidden | low | patch | `TrySetAcl` returns null for every `setxattr` error, silently losing ACL coverage on a capable filesystem. Only unsupported-filesystem errors should fall back; unexpected errors should fail the test. |
| Blind 5: lowercase Gateway ULID | medium | patch | `Ulid.TryParse` accepts lowercase text but `ValidCorrelationId` rejects it using canonical string equality. §G calls for a supplied valid ULID; preserve valid supplied text and test it. |
| Blind 6: malformed success message ID | medium | defer | The pinned response and executor can surface a non-ULID command `messageId`, but the frozen decision explicitly defers successful-response hardening. |
| Blind 7: malformed success paging | medium | defer | Query result metadata can violate §G constraints; the frozen decision explicitly defers additional successful-response hardening. |
| Blind 8: Console test interference | false | reject | CLI test assembly sets `Xunit.v3.Parallelization(Mode = None)` in `AssemblyInfo.cs`; tests redirecting `Console` do not run concurrently. |
| Blind 9: probed loopback port | low | reject | The small release-to-bind race is real, but no conflict occurred in the full 365-case lane and the existing harness uses the same pattern; retaining ownership while binding `HttpListener` would require more setup for an uncommon collision. |
| Blind 10: MCP host I/O mislabel | medium | patch | `RunMcpAsync` catches host-runner `IOException` in the same branch as profile setup and reports a profile-read error. Track when host execution starts and use generic `internal_error` for later I/O. |
| Blind 11: blank tenant as missing | false | reject | `ResolveTenant` returns a supplied empty string, not null; the syntax message correctly distinguishes a supplied invalid tenant from a missing tenant, as the frozen intent requires. |
| Verification 1: new-file mode untested | medium | patch | Existing-target tests never assert the mode of a newly created result. Add a Unix assertion that new output is private. |
| Verification other 1: MCP host I/O | medium | patch | The host runner's I/O exception reaches the profile-read catch after setup; this is the same defect as Blind 10. |
| Edge 1: cooperative reader sharing | medium | patch | Existing targets now open with `FileShare.None`; a reader sharing writes can coexist with the prior direct writer but blocks the new open. Use read sharing. |
| Edge 2: FIFO backup | medium | patch | A local .NET probe shows `File.Exists` true and `FileStream.CanSeek` false for a FIFO opened read/write. The backup copy can wait forever; refuse non-seekable outputs before copying. |
| Edge 3: dangling output symlink | medium | patch | The final target does not exist, so the existing-file open fails; resolving the target before staging restores the prior successful path without replacing the link. |
| Edge 4: destination dispose failure | low | reject | A close failure after the flushed write could report error with changed bytes, but no reachable ordinary-file trigger was demonstrated. Coordinating a second restore after close adds complexity for a rare failure. |
| Edge 5: MCP host I/O | medium | patch | Same reachable host-runner exception and false profile diagnosis as Blind 10. |
| Edge 6: success message ID | medium | defer | A non-ULID returned `messageId` is possible; successful-response validation is excluded by the frozen decision. |

The direct patches are dangling links, mode and ACL test coverage, valid Gateway correlation IDs, MCP host error classification, cooperative file sharing, and non-seekable target refusal. The two successful-response findings share the pre-existing response-policy deferral.

## Verification

Implementation and acceptance audit: all eight task areas and all six matrix scenarios are covered by executed tests. Individual Debug builds passed with zero warnings and errors. Core: 541 total, 539 passed, 2 existing Windows-only skips; CLI: 371 passed; MCP: 6 passed. XML confirms 17 result-document, 11 Core failure, 31 CLI failure, and one MCP host-I/O case ran and passed. `git diff --check` and changed C# CRLF checks passed. Caught write failures restore previous bytes; a process interruption or second failure during rollback can leave a partial existing file.

Build and test each project individually; require zero warnings/errors, passing matrix coverage, and only existing platform-specific skips:

```sh
for lane in Core Cli Mcp; do
    dotnet build "tests/Hexalith.McpCli.$lane.Tests/Hexalith.McpCli.$lane.Tests.csproj" --configuration Debug --no-restore -m:1 || exit
    dotnet "tests/Hexalith.McpCli.$lane.Tests/bin/Debug/net10.0/Hexalith.McpCli.$lane.Tests.dll" -result-xml "/tmp/mcpcli-story-2-9-$lane.xml" || exit
done
git diff --check
```

Run focused new classes first; inspect XML and changed C# CRLF checks.
