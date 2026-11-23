---
title: 'Align contributor guidance with CLI and live-test behavior'
type: 'chore'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent">

## Intent

Close five open documentation findings in the deferred-work ledger. Contributors need accurate instructions for CLI output routing, v1 scope, regex syntax, Aspire resource launches and the selection of live conformance vectors. Reconcile the three repository instruction files with the PRD, implementation and existing tests, and record how each finding was verified.

</frozen-after-approval>

## Implementation Notes

- The starting revision of McpCli main is `292641ce923e897f240666304a67abbd51cc523d`. The selected entries come from the Story 2.11 output review, the Story 4.18 topology review and the Story 5.12 vector coverage review.
- Check the output contract against `CliOutput.WriteAsync` and the README, scope against PRD §§8.2–8.3, and whole-string validation against `ProfileStore.ProfileNamePattern` and `SchemaDeriver.UlidPattern`.
- Check runtime composition against the test AppHost and live selection against `run-vectors.py` and `live_plans.py`. Run the focused regressions and the instruction synchronization check.

### Verification

- The Release solution restore and build passed with .NET 11.0.100 and zero warnings. The Linux run of `CliOutputContractTests` passed 23 cases and skipped two Windows-specific cases. The seven cases selected by `*StartupFailuresWriteOneStructuredErrorAsync` and `*EveryAvailableToolExecutesOverCleanStdioAsync` passed, as did `SdkHostedSessionFaultExitsTwoAsync`.
- All 11 Core cases selected by `*NewlineSuffixedName*`, `*UlidRequiresExactlyTwentySixCharacters` and `*UlidSchemaRejectsLowercaseMarkedAndTypedValues` passed. The test project dependency check, AppHost helper closure check and integration fixture package closure check in `DependencyPolicyTests` also passed.
- `PYTHONPATH=tools/live-topology python3 -m unittest test_live_plans.LiveKindCoverageTests` passed all ten checks, including a vector without a plan and a plan without an approved vector. Reviewed the runtime resource selection directly in the AppHost.
- `scripts/check-agent-instructions-sync.sh` and `git diff --check` passed. Compared all three instruction files against the starting revision to verify the edits are confined to the repository-specific context. The original ledger is a byte-identical prefix of the updated file.

## Review Triage Log

- Medium. Scoped generated message IDs and default correlation IDs to Commands, matching the `SendCommandArguments` branch in `OperationExecutor`.
- Low. Qualified the JSON fallback note with the success condition in `CliOutput.WriteAsync`.
- Medium. Added the stderr diagnostic and exit code for an MCP serving-process fault, as exercised by the hosted-session fault test.
- Medium. Restored the PRD §8.2 requirement for FR-21 evidence of module-specific Query semantics.
- Low. The Story 5.12 row's original open status is part of the hashed historical record in Story 5.11's `deferral-dispositions.json`. The dated resolution table supersedes that row while preserving its evidence hash.
- Low. Recorded the executed checks and their results before closing the spec.
