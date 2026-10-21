# Final published-enrollment review and verification

All three independent review layers completed before triage. The spec records
each of their 13 findings plus two parent findings. Thirteen findings were
corrected; two low findings were rejected with evidence, and none was deferred.
[Review identity and outcome](review.json) preserves the immutable reviewed-diff
snapshot and protected input hashes. [Mutation evidence](mutations/results.json)
records ten isolated guard removals, all detected by their focused regressions.

The generic verifier now enforces the exact approved inventory digest, freezes
artifact/vector inputs, rechecks approved hashes during capture, rejects duplicate
paths and requires independent signed-archive binding. Enrollment preflight
invalidates previous child success, rejects malformed receipts and compares
package identities case-insensitively. The real process fixture proves a pending
inventory fails through the C# adapter before replay. CI retains full enrolled
evidence with the owning Builds pinned upload action and an always condition.

[All 13 parent commands](checks.json) pass: both sample gates, fresh solution
restore, Release build with zero warnings/errors, six test projects, fresh
enrolled-package verification, instruction synchronization and whitespace checks.
[Test totals](test-summary.json) are 1,339 .NET tests passed, zero failed, four
existing Windows-only skips, and 100 Python regressions passed. All three process
cases pass: valid enrollment/replay, pending-inventory rejection and deliberate
semantic-assertion rejection. No frozen matrix case was skipped.

[Fresh enrolled verification](enrolled/enrolled.json) confirms the approved exact
signed archive for `Hexalith.Parties.Contracts` 1.5.1, all seven operations and
vectors, clean strict discovery/lint/inventory and complete CLI/MCP replay without
dependency overrides. It retains all 53 restored identities and both archive and
restore-content hash meanings. All seven describe documents remain byte-identical
to the independently reviewed public artifact. [Integrity evidence](integrity.json)
confirms unchanged approved inventory, seven vectors, approval/binding receipts,
frozen intent and selected merged Builds revision
`2744d549270298cfe73679f76b477a7368429006`.

The protected Parties release and Builds integration remain established by their
earlier exact-source CI and release evidence; this patch changes no upstream
runtime source or package. The new McpCli CI upload step was checked locally;
remote McpCli CI awaits submission of this working tree. Replay does not establish
live authorization, domain effects or legacy retirement. C06–C08 and Stories
4.11/4.13 remain downstream gates.
