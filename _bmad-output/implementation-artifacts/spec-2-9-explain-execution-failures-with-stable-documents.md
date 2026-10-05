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
- [x] `tests/Hexalith.McpCli.Core.Tests/ResultDocumentContractTests.cs` — add every §G success/error fixture; assert exact member sets, types, constraints, lint variants, availability reasons, optionals, arrays, and arbitrary result/document JSON kinds.
- [x] `tests/Hexalith.McpCli.Core.Tests/OperationErrorTests.cs` — extend complete JSON assertions, blank-value fallback precedence, absent metadata, and true/false retry hints.
- [x] `tests/Hexalith.McpCli.Core.Tests/ExecutionFailureTests.cs` — test both call kinds, lookup parity, safe unexpected failures, derived identifier pointers, and distinct validation messages; assert zero/one calls.
- [x] `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs` — correct derived pointers and distinct messages; retain shared validation order and Gateway mapping. Update pinned expectations in `tests/Hexalith.McpCli.Core.Tests/QueryValidationTests.cs` and the CLI `QueryValidationCommandTests.cs` and `QueryPagingCommandTests.cs`.
- [x] `tests/Hexalith.McpCli.Cli.Tests/ExecutionFailureCommandTests.cs` — real HTTP fixtures for Problem Details, malformed successes, and semantic failures; assert errors, status, exit 2, one request, bounded cleanup. Test unexpected action failures and all error variants through `CliOutput`, including table mode and existing output files.
- [x] `src/Hexalith.McpCli/Cli/CliRunner.cs` — prevent unexpected action I/O from exposing raw exception text; preserve expected profile/configuration errors. Fix serializer or output behavior only if contract tests demonstrate a defect.
- [x] `README.md` — document failure contracts and 2xx Gateway errors.
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` — mark resolved pointer/message/action-I/O entries with evidence; preserve unrelated and response-policy deferrals.

**Acceptance Criteria:**
- Given each matrix fixture, when exercised through Core or CLI, then its complete document and call count match the expected behavior.
- Given a failed CLI invocation, when it finishes, then stdout contains one error document, exit is 2, no success is emitted, and any result file is unchanged.
- Given the finished change, when suites run individually, then all acceptance cases execute and existing tests pass.

### Review Findings

Code review 2026-10-05 of `dc5d783..e59ca7d`. Layers: Blind Hunter, Edge Case Hunter, Verification Gap, and Acceptance Auditor; none failed. The auditor reran the three suites one at a time and matched the recorded counts (Core 539 passed with 2 pre-existing skips, CLI 371/371, MCP 6/6). The findings below are cases those tests do not catch.

- [x] [Review][Patch] Gateway `correlationId` validity check accepts any 26-character text — low (blind-hunter+edge-case-hunter+acceptance-auditor). `ValidCorrelationId` relies only on `Ulid.TryParse`. A triage probe against the pinned ByteAether.Ulid 1.4.1 confirmed that this accepts 26 spaces, `<script>alert(1)</script>!`, `…DAT~`, `…DATU`, `81J9…` and `OIJ9…`, so a misbehaving Gateway can put non-ULID text into `gateway_error.correlationId`, against §G (`addendum.md:441`) and README line 91. The same check also passes lowercase text, which `RetainsValidLowercaseGatewayCorrelationId` pins. The frozen Always clause says "Retain canonical uppercase ULIDs", and README line 67 says the CLI refuses lowercase `--correlation-id`. Options: (1) round-trip and compare ordinally, so only canonical uppercase passes and lowercase is omitted; (2) round-trip and compare ignoring case, keeping supplied lowercase text as loop 3 decided; (3) leave as is. Either round-trip option is a one-line change, plus near-miss rows in `BlankValuesUseStableFallbacks`. Resolved by user decision 2026-10-05: option 1. Only canonical uppercase text passes; flip `RetainsValidLowercaseGatewayCorrelationId` to expect omission. [src/Hexalith.McpCli.Core/Execution/OperationError.cs:56]
- [x] [Review][Patch] A missing or unreadable `--payload @file` returns `internal_error` "The CLI action failed." — medium (blind-hunter+acceptance-auditor). `ReadPayloadAsync` lets `File.ReadAllTextAsync` throw (`CliRunner.cs:566`). The action catch turns that into the generic error, so a mistyped path looks the same as a defect. This conflicts with the frozen Problem ("messages obscure the failed input") and with README's description of `internal_error` as the code for unexpected failures. §G already defines `invalid_arguments` with an `argument` member. Options: (1) map @file read failures to `invalid_arguments`, `argument: "payload"`, with a fixed message that omits the path; keep `internal_error` for `--output` write failures, which can happen after a command was accepted; (2) keep `internal_error` as pinned by `MissingPayloadFileHidesPathAndKeepsResultAsync`. Resolved by user decision 2026-10-05: option 1. @file read failures become `invalid_arguments` with `argument: "payload"` and a fixed message that omits the path; `--output` failures stay `internal_error`. [src/Hexalith.McpCli/Cli/CliRunner.cs:566]
- [x] [Review][Patch] `--output` to `/dev/null`, `/dev/stdout`, a pipe or a FIFO now fails with exit 2 — high (blind-hunter+edge-case-hunter+acceptance-auditor). Three layers reproduced `internal_error` at HEAD, where the old `File.WriteAllTextAsync` succeeded. There are two causes. First, `SetLength(0)` fails on a character device. Second, `ResolveFinalSymlink` treats the `/proc/self/fd` link target `pipe:[N]` as a relative path, and creating the staging file there fails. For `send`, the command has already been accepted when this happens, so exit 2 invites the unsafe retry the README warns against. The implementation notes require preserving existing output-path success behavior. Fix: write non-regular targets (character devices, FIFOs, sockets, `pipe:`/`socket:` fd links) directly, as before, without staging or backup, and keep the backup path for regular files. Replace `NonSeekableResultTargetIsRefusedAsync` with direct-write coverage that uses a FIFO reader, and add a `/dev/null` case. [src/Hexalith.McpCli/Cli/CliOutput.cs:63]
- [x] [Review][Patch] `ResolveFinalSymlink` resolves `..` in a relative link target by text, so it can write to a different file than the OS would — medium (blind-hunter+edge-case-hunter+verification-gap). The code applies `Path.GetFullPath(Path.Combine(<unresolved parent>, target))`. With `a/linkdir -> ../x/y` and `x/y/result.json -> ../t.json`, the CLI exits 0 after creating or overwriting `a/t.json`, and the real target `x/t.json` stays stale. Two layers reproduced this. Fix: resolve each relative target against the physical parent directory, or let the OS follow the links when it opens the file. [src/Hexalith.McpCli/Cli/CliOutput.cs:160]
- [x] [Review][Patch] After a buffered write failure, the restore step never runs — medium (edge-case-hunter). The destination is opened with a 4096-byte buffer. When `FlushAsync` fails (for example ENOSPC) with bytes still buffered, the restore's `destination.Position = 0` flushes them again and rethrows, which skips the restore. A triage probe confirmed this on `/dev/full`, and showed `bufferSize: 0` avoids it. The failure leaves a truncated or partial file, and the `finally` block then deletes the backup. This breaks the "caught write failure restores the previous bytes" guarantee in the one case it exists for. Fix: open the destination unbuffered (`bufferSize: 0`), and add a buffered-failure test. [src/Hexalith.McpCli/Cli/CliOutput.cs:100]
- [x] [Review][Patch] The setup catches in `CliRunner` label or echo errors that do not come from the profile — medium (blind-hunter+edge-case-hunter+verification-gap+acceptance-auditor). `SettingsResolver` now handles profile I/O and data errors itself. The catches before the action or host starts (`CliRunner.cs:472`, `:477`, `:532`, `:537`) therefore only see host-builder or assembly errors:
  - An unreadable `appsettings.json` in the working directory, or an inotify-limit `IOException` from the reload watcher, is reported as "Unable to read the mcpcli profile file."
  - In `mcp`, `CatalogProvider.Get` → `ManifestLoader.Load` → `Assembly.Load` runs before `hostStarted`, so a `FileNotFoundException` for a missing Contracts assembly gets the same profile message.
  - A malformed `appsettings.json` echoes "Failed to load configuration from file '/abs/…/appsettings.json'." as `configuration_invalid`. The echo is pre-existing; the profile mislabel is new.

  Fix: drop the setup I/O and `InvalidDataException` catches, so non-profile setup failures reach the generic `internal_error` catch ("The CLI action failed." / "MCP startup failed."). Add CLI and MCP tests. [src/Hexalith.McpCli/Cli/CliRunner.cs:532]
- [x] [Review][Patch] The loopback harness cannot see a second Gateway request — medium (edge-case-hunter+acceptance-auditor). `InvokeGatewayAsync` accepts one `GetContextAsync` and increments `calls` once, so `calls.ShouldBe(1)` always passes. A retry would hang until the HTTP client times out instead of failing the count, because `InvokeCliAsync` runs on the test token rather than the 15-second `timeout.Token`. Task 5 asks for "one request, bounded cleanup". Fix: loop, answering and counting every request as `QueryCliHarness` does, and run the CLI under the bounded token. [tests/Hexalith.McpCli.Cli.Tests/ExecutionFailureCommandTests.cs:513]
- [x] [Review][Patch] No test overwrites an existing result with shorter output or checks that restore removes bytes already written — medium (verification-gap). Every existing-file test seeds 10 bytes and writes 17, and the post-truncation fault fires before any new bytes are copied. If either `SetLength(0)` were removed, all tests would still pass while a shorter result keeps a stale tail and exits 0. Fix: seed about 4 KB and assert the exact JSON. In the fault test, write more bytes than the original before throwing, then assert the original bytes come back exactly. [tests/Hexalith.McpCli.Cli.Tests/ExecutionFailureCommandTests.cs:216]
- [x] [Review][Patch] Relative symbolic-link targets are never tested — medium (verification-gap). Every output link uses an absolute target, so the relative branch of `ResolveFinalSymlink`, which has the bug above, never runs. Fix: add relative-target rows (`File.CreateSymbolicLink(link, "target.json")`) to `ExistingResultPreservesModeAclAndLinkAsync` and `DanglingResultLinkCreatesTargetAsync`. [tests/Hexalith.McpCli.Cli.Tests/ExecutionFailureCommandTests.cs:265]
- [x] [Review][Patch] Nothing tests an invalid explicit aggregate ID on a String accessor operation — low (verification-gap). Dropping `call.AggregateId is null &&` from the pointer choice would report `/Key` instead of `/aggregateId` for `--aggregate-id bad/id` on `string-fixture.lookup`, and every test would still pass. Fix: add that row next to `InvalidStringPayloadAccessorMakesZeroCallsAsync`. [tests/Hexalith.McpCli.Core.Tests/QueryValidationTests.cs:172]
- [x] [Review][Patch] Platform-gated tests return early and count as passes — low (blind-hunter+acceptance-auditor). Seven new tests start with `if (OperatingSystem.IsWindows()) return;` or `if (!OperatingSystem.IsLinux()) return;`. The repository's pattern is `Assert.SkipWhen(..., reason)` (`ConfigCommandTests.cs:1699`, `ProfileStoreTests.cs:525`). [tests/Hexalith.McpCli.Cli.Tests/ExecutionFailureCommandTests.cs:138]
- [x] [Review][Patch] The leak tests never check stderr — low (blind-hunter). `MissingPayloadFileHidesPathAndKeepsResultAsync`, `ProfileActionIoUsesSafeMessageAsync`, `ReadOnlyExistingResultStaysUnchangedAsync` and `TableOutputWriteFailureUsesInternalErrorAsync` discard the captured stderr. A log line carrying the path, token or stack would still pass. Assert that stderr is also free of them, as `McpHostIoFailureIsInternalErrorOnStandardErrorAsync` does. [tests/Hexalith.McpCli.Cli.Tests/ExecutionFailureCommandTests.cs:77]
- [x] [Review][Patch] The ledger was not fully reconciled with this story's outcomes — low (blind-hunter+acceptance-auditor). Four problems:
  - The new entry at `deferred-work.md:335` duplicates the open entries at `:52` and `:55` for malformed success IDs and paging. Remove it, and cite those entries from the loop-3 defers.
  - The Story 2.7 entry (`:281`) still says "Story 2.9 owns the fix". Record the frozen "Never: Add generated tracking fields to errors" decision and the README retry warning, and drop the stale owner.
  - The Story 2.3 entry (`:210`) still says management-verb `--output` failures report `configuration_invalid`; they now report `internal_error`. The underlying problem, exit 2 after the profile changed, remains.
  - The loop-1 defers (no MCP test of a Gateway failure, including 2xx; unknown CLI verbs before 2.11) have no ledger entry.

  [_bmad-output/implementation-artifacts/deferred-work.md:335]
- [x] [Review][Patch] README leaves out new `--output` behaviors — low (blind-hunter). New result files are now always created with mode 0600 rather than following the umask. A read-only existing file is refused, not only a write-only one. A dangling symbolic link creates its target. Updating an existing file stages copies in the system temporary directory. Rewrite the paragraph after the special-target fix. [README.md:93]
- [x] [Review][Patch] `getxattr` P/Invoke declares `long` for `ssize_t` — low (edge-case-hunter). The type is wrong on 32-bit Linux. Use `nint`. [tests/Hexalith.McpCli.Cli.Tests/ExecutionFailureCommandTests.cs:620]

**Rejected**

- low — A failed rollback deletes the backup (blind-hunter): the spec already accepts "a second failure during rollback" as an operational limitation, the backup's random temporary name is never reported, and keeping it adds a branch. The buffered-flush patch removes the self-inflicted second failure.
- low — Management `config` verbs report an unreadable profile as `internal_error` while `modules` reports `configuration_invalid` (blind-hunter+acceptance-auditor): loop 1 (Blind 4) chose `internal_error` for action I/O on purpose, an unreadable profile is rare, and separating profile I/O from output I/O would need branches at every `ProfileStore` call site.
- low — Staging existing-file writes in the system temporary directory adds a copy and a TMPDIR dependency (blind-hunter+edge-case-hunter): the loop-2 implementation note mandates this staging, the backup needs TMPDIR anyway, and a full or unwritable TMPDIR is uncommon.
- low — Spec `done` versus sprint `review`, `review_loop_iteration: 2` alongside three loop tables, unchecked tasks, and conflicting staging notes (blind-hunter+acceptance-auditor): the fix would edit the spec. The sprint entry moves when this review closes.
- low — `ProfileActionIoUsesSafeMessageAsync` fails when tests run as root (edge-case-hunter): developers and CI do not run the suite as root, and the fix adds a guard.
- false — The Unix mode-bit pre-check refuses root on a 0444 file and ignores ACLs (blind-hunter): the implementation note requires honoring an existing file's write restrictions, and a named-user ACL that grants write appears in the mask (group) bits, so the check passes it.
- false — A blank cursor with an offset bypasses the conflict rule (edge-case-hunter): Story 2.6's frozen rule says "Only nonblank cursors conflict with supplied offsets; preserve blank cursors", and this change kept that condition.
- false — The new `OperationErrorTests` cases do not assert whole documents (acceptance-auditor): complete `FromGateway` documents are pinned with `JsonElement.DeepEquals` in `ExecutionFailureCommandTests` (complete, blank, 2xx) and `ExecutionFailureTests`, so an extra member would fail there.
- false — `UnknownOperationMatchesDescribeWithNoSubmissionAsync` would pass if both lookups returned `[]` (acceptance-auditor): `DiscoveryCommandTests:223-224` pins the shared ordered suggestions, including differently cased input, so a regression to empty fails there, and divergence fails the equality check.

## Implementation Notes

- Shared catalog lookup and Gateway exception mapping were already in place. Preserve and pin their complete documents and one-call behavior.
- Derived String identifiers should report their mapped payload pointer; explicit identifiers retain `/aggregateId`. Existing discovery and query validation tests cover suggestion ordering, nested escaped Schema pointers, and explicit-source pointers.
- `QueryPagingCommandTests.cs` had no pinned message to change in the first pass; verify that remains true.
- A result-file implementation must preserve existing output-path behavior on success: honor an existing file's write restrictions and security metadata, and write through a symbolic link to its target without replacing the link. A failed write or replacement must leave the existing target bytes and link unchanged and remove its temporary file. Use a private same-directory temporary file for new results and private system temporary copies for existing results; test a failure after staging while an existing result is present.
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

### Review loop 4

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| Blind 1: umask restricts temporary files | high | patch | Reproduced with `umask 0777`: existing output was emptied after stage and backup reopened as mode 0000; new output succeeded with mode 0000. Set owner read/write explicitly after private creation, before reopening. |
| Blind 2: deleted proc fd writes a ghost path | medium | patch | Reproduced `config current --output /proc/self/fd/N` for an unlinked regular file: exit 0 created `<old path> (deleted)` and left the fd bytes unchanged. Preserve the fd path and use the regular-file backup/write path. |
| Blind 3: literal pipe target symlink | low | patch | Reproduced an ordinary `result -> pipe:[123]` link failing instead of creating the literal target. The pseudo-fd exception must apply only to `/proc/self/fd` links. |
| Blind 4: trailing slash in link target | medium | patch | Reproduced `result -> target.json/` overwriting `target.json` and exiting 0, whereas OS open of that link fails. Preserve the trailing-directory requirement while resolving. |
| Blind 5: 33-link chain | low | patch | Direct Linux open reached the target through 33 links; the resolver rejected it at its artificial limit of 32. Align the bound with the platform's accepted link count. |
| Blind 6: regular file under `/dev` | low | reject | The `/dev/` prefix would route an existing regular file to direct write and could leave a stale tail, but creating such a file needs unusual device-directory access; replacing the prefix with file-type inspection adds complexity for a rare path. |
| Blind 7: FIFO with no reader | medium | defer | The first synchronous write-only open blocks before cancellation; the baseline `File.WriteAllTextAsync` also opened a FIFO this way. This predates Story 2.9 and needs a nonblocking FIFO design. |
| Blind 8: post-send output warning | medium | patch | A failed result-file write after Gateway acceptance produces `internal_error` without a command result. README warns only about Gateway errors; add the same retry caution for post-submission output failures. |
| Blind 9: missing `send @file` case | low | patch | `send` and `query` have separate changed branches, but the failing-file test covers only `query`; a `send` branch regression would pass. Add a `send` row with the exact error and unchanged result. |
| Blind 10: accepted send plus output failure | medium | patch | The output-failure tests invoke discovery verbs, so none proves the accepted command's one-request, exit-2 behavior and retry ambiguity. Add a bounded send fixture with an unwritable result target. |
| Blind 11: MCP Gateway failure protocol | medium | defer | carried: Review loop 1 Blind 7 already recorded the same missing MCP Gateway error protocol test; the code and protocol tests still have that gap, and the deferred ledger records it. |
| Edge 1: FIFO with no reader | medium | defer | The same blocking FIFO open as Blind 7 occurs before a token can cancel; the baseline writer behaved likewise. Group with Blind 7 in deferred work. |
| Edge 2: destination dispose failure | low | reject | carried: Review loop 3 Edge 4 already rejected the same post-flush close-failure claim because no ordinary-file trigger was demonstrated; the disposal scope is unchanged. |
| Edge 3: probed port race | low | reject | carried: Review loop 3 Blind 9 already rejected this small test-only bind race; the harness still probes then binds. |
| Verification 1: `send @file` branch | low | patch | The gap reviewer found no failing-file send test and showed that removing the send-specific branch leaves the checked suite passing. Group with Blind 9. |
| Verification 2: unauthorized profile read | low | patch | `ProfileReadIoHidesPaths` covers IOException and InvalidDataException but not the new UnauthorizedAccessException catch arm. Add an assertion for its fixed `configuration_invalid` message. |

The patch entries are independent targeted corrections to temporary-file permissions, path resolution, documentation, and test branches. The no-reader FIFO predates this story; the existing MCP protocol gap remains deferred. The carried and rejected entries need no code change.

## Verification

Implementation and acceptance audit: all eight task areas, 15 earlier review patches, and all six matrix scenarios are covered by executed tests. Review loop 4 patches cover restrictive umask, proc fd and symlink paths, post-submission output behavior, and missing test branches. Individual Debug builds passed with zero warnings and errors. Core: 546 total, 544 passed, 2 existing Windows-only skips; CLI: 387 passed; MCP: 6 passed. XML confirms 17 result-document, 11 Core failure, 31 Core settings, and 44 CLI failure cases ran and passed. Focused cases verify correct paths through directory links and `..`, direct pipe output, and safe setup errors. `git diff --check` and changed C# CRLF checks passed. Caught write failures restore previous bytes; a process interruption or second failure during rollback can leave a partial existing file.

Build and test each project individually; require zero warnings/errors, passing matrix coverage, and only existing platform-specific skips:

```sh
for lane in Core Cli Mcp; do
    dotnet build "tests/Hexalith.McpCli.$lane.Tests/Hexalith.McpCli.$lane.Tests.csproj" --configuration Debug --no-restore -m:1 || exit
    dotnet "tests/Hexalith.McpCli.$lane.Tests/bin/Debug/net10.0/Hexalith.McpCli.$lane.Tests.dll" -result-xml "/tmp/mcpcli-story-2-9-$lane.xml" || exit
done
git diff --check
```

Run focused new classes first; inspect XML and changed C# CRLF checks.
