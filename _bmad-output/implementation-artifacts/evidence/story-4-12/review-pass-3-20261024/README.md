# Story 4.12 review pass 3 implementation

P25–P32 are implemented. Parent acceptance audit and workflow review remain
pending. No release, dependency pin, gitlink, production contract, inventory or
vector changed in this resumed implementation. Earlier evidence remains intact.

The current source snapshot and acceptance matrix are bound by
[`verification.json`](verification.json) and
[`implementation-file-map.json`](implementation-file-map.json). Each validation
receipt retains the exact command, exit code, duration and both output channels.
The command recorder and corrected mutation verifiers are retained beside the
receipts; their final executions used identical script bytes from task-owned
`/tmp` paths, as recorded in the commands. Initial experiments are labeled
separately.

| Patch | Change and executed coverage |
| --- | --- |
| P25 | The success child exposes all six mTLS/control-plane settings and every Redis, placement, scheduler and Gateway setting. Assertions pin their values and cross-check placement/scheduler service arguments. Inherited inputs are cleared in the fixture. Seven temporary-copy controls reject missing settings or the wrong placement port. |
| P26 | The two readiness loops share a 40-second constant. Four inert fixture modes assert exact failure receipts and no child launch for early Sentry exit, absent certificates, early daemon exit and unreachable ports. Four temporary-copy controls reject removal of these guards. |
| P27 | The Dapr stub can fail `--version`; the additional prerequisite theory row pins its exact standard skip detail. The nested prerequisite count is eleven. The focused disposable-source control rejects removal of the broken-CLI guard. |
| P28 | A linked `references` parent reaches and asserts the exact physical-working-tree refusal. Its focused disposable-source control fails when that comparison is removed. |
| P29 | Both Redis components use JSON syntax accepted as YAML. Two content cases pin names, Redis host, empty password, actor state, key prefix and all three scopes, and cross-check the wrapper's private Redis port and probe. Disabling actor state or dropping Parties from scope fails the actual content test. The live smoke validates that Dapr accepts both rewritten components. |
| P30 | Both maintained READMEs name Aspire CLI 13.6.1 and its DCP/dashboard bundle, distinguishing it from SDK/hosting 13.6.3. That bundle was present in this live run. |
| P31 | The maintained veth setup now states its multicast-networking purpose. |
| P32 | The runtime README explains that both digest-pinned images remain in Docker and names the exact `docker image rm` cleanup. The fresh bootstrap used those references. |

Fresh restore, Release warnings-as-errors solution build and all three separately
bounded root server builds passed with zero warnings/errors. The six individual
non-live projects passed 1,485 tests, zero failed, with five existing unrelated
skips: Abstractions 20, Analyzers 19, Core 704 (three skips), CLI 479 (two skips),
MCP 58 and Manifest 205. All fifteen maintained Python checks passed. Discovery
reported exactly the single `AuthenticatedQueryReturnsSuccessfulDocument` smoke.

The fresh digest-pinned bootstrap verified all four native executable hashes.
The documented isolated `-failSkips` run passed one test, zero failed and zero
skipped in 25.627 seconds (25.942 seconds for the child process). Missing and
wrong-key credentials were rejected before the successful authenticated query.
All four private infrastructure processes exited 0; no private key remained.
The copied live receipts contain no certificate/private-key values. Host Dapr
application identities, process IDs and ports matched before and after the run.

`python-mutation-controls.json` records eleven rejected temporary-copy controls;
`dotnet-mutation-controls.json` records the successful disposable-source build
and four expected test failures. The initial mutation experiment is retained in
`python-mutations-initial.*`: it removed only the redundant first `NAMESPACE`
assignment, so the later assignment correctly preserved behavior. The corrected
control removes both assignments and is rejected. Initial and final receipts
reference distinct output files. The initial .NET snapshot omitted the solution
root marker, so its two component controls failed during root discovery. Those
initial outputs remain in `dotnet-mutation-controls-initial.json`; they do not
qualify those component mutations. The corrected snapshot includes the marker
and requires exactly one assertion failure per final mutation, with no runner
errors.

The existing platform lock and agent-context deferrals remain unchanged. The
mandatory outer process deadline remains in force. Full live vector semantics
and blocking live CI remain Stories 4.13 and 4.14.
