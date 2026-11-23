---
title: 'Close five CLI and MCP execution deferrals'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent">

## Intent

Close five deferred items affecting operators and the tests that exercise their CLI and MCP sessions. Caller cancellation during MCP startup should finish cleanly. A serving fault in the SDK-hosted session should produce the documented failure. Operators should find a description for every CLI option and positional argument. Both clients should return the Gateway's continuation cursor, and the query tests should release their listener reliably.

</frozen-after-approval>

## Implementation Notes

- Base revision: `a32d073b0c353fc57ec51df36445e0fc102f62e3`. Selected the cursor entry from Story 1.7, startup cancellation from Story 2.1, DW-2 from the project-context review, SDK fault detection from Story 3.2 and listener cleanup from Story 3.3.
- Exercise the real command tree, host registration and HTTP client. Reuse the existing loopback gateway and parity harness. Retain the success, error, and absent-paging cases. Record results in the deferred-work ledger.
- The startup test distinguishes caller cancellation, an unrelated canceled task and an I/O failure. The serving test runs the SDK-registered hosted service with a controllable session and verifies its exit and output channels.
- The two parity cases compare the full returned documents, including the optional Gateway paging fields. All 19 payload-source and routing cases use the existing socket fixture. The command-tree check visits nested commands and reports the path of any missing description.
- All 26 focused cases passed on Linux with .NET 11.

The post-review Release build completed with zero warnings and errors. All 27 cases in the command below passed. The Release CLI also displayed the new argument description in `config use --help`.

## Review Triage Log

| Finding | Verdict and change |
| --- | --- |
| The cancellation catch also covered configuration and catalog errors. | Medium. Limited the catch to the host start call. |
| Clearing log providers hid the SDK's diagnostics. | Medium. The fault test retains production logging and checks for one serving diagnostic, empty stdout and absence of a structured startup error. |
| Socket handlers could outlive fixture disposal. | Medium. Disposal waits for the accept loop and all its accepted connection tasks before releasing the cancellation source. |
| The help test could pass with the profile argument hidden. | Low. Added the rendered `config use --help` case to the operator help contract. |
| The original DW-2 status still said open. | Low. Updated it with the date and resolution spec. |
| The focused result did not identify its test selection. | Low. The post-review invocation below includes the original 26 cases and the rendered-help contract. |

Run from the repository root after the Release build.

```bash
dotnet tests/Hexalith.McpCli.Cli.Tests/bin/Release/net11.0/Hexalith.McpCli.Cli.Tests.dll \
  -method '*SdkHostedSessionFaultExitsTwoAsync' \
  -method '*McpStartupDistinguishesCancellationFromFailureAsync' \
  -method '*EveryCommandArgumentAndOptionHasHelp' \
  -method '*QueryDocumentsAndGatewayRequestsMatchAsync' \
  -method '*PayloadSourcesUseOneDescriptorRoutedPostAsync' \
  -method '*HelpExplainsOperatorInputsAsync'
```
