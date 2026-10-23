# Story 4.12 implementation handoff

The published-artifact topology passed parent acceptance audit, all three review
layers and final verification. The required local completion commit records this
work; the McpCli remote remains unchanged. Current results supersede the earlier
implementation checkpoints, whose receipts remain retained.

## Publication and provenance

The user authorized the expanded source `08f43497b3f916efa0cdf9b110258f763d894bd9`
and its normal ten-package/three-image-family release. The ledger-only successor
`a4716d0da37b27762d9931c778223d13e85695dc` preserves all 95 qualified source hashes
and all eight gitlinks. Its normal CI/range/commitlint/CodeQL gates passed;
[normal release 39954248029](https://github.com/Hexalith/Hexalith.Parties/actions/runs/39954248029)
then published and verified all ten NuGet 1.6.0 packages and all three container
families on amd64 and arm64. Ordinary production approvals preserved protection
configuration. See `release-complete.json`, `publication-verification.json`,
`a471-gates/`, and the complete retained artifact ZIPs.

The actual signed `Hexalith.Parties.Aspire` 1.6.0 archive is 26,220 bytes, SHA-256
`6b7678949525490453e07113611d19a7e7d6cf3c0b64e427773694da0f457695`, source commit
`a4716d0da37b27762d9931c778223d13e85695dc`. Its sole DLL is accompanied by exactly
two direct dependencies: Aspire.Hosting 13.6.3 and EventStore.Aspire 3.126.1.
Fresh-cache NuGet-only restoration, server-free closure and all six root locator
probes passed (`published-helper/`). Actual McpCli restored-byte and separate
platform-fixture closure receipts are in `actual-restored-helper-and-platform-closure.json`.
No production Contracts selection changed.

The frozen [08f qualification packet](../expanded-source-candidate/README.md)
is unchanged. Local `.1`–`.4` archives remain unpublished qualification artifacts.
Failed prepublication workflows and their narrow corrections remain in this
folder and the historical continuation receipts.

## Owning Builds integration

Catalog `ca1262562b8da711043fd698b0aea1e7b34e5c40` adds the independent Parties
helper pin and SDK exception, then advances only the global Parties family to
published 1.6.0 under the unchanged audit validator. Six global defaults changed;
all 306 existing McpCli evaluated selections remain identical under its explicit
Parties 1.5.1/Tenants 5.10.0 overrides. The 307-package/151-family audit, SDK
inventory, 30 fixture scenarios and consumer authority passed. No G-4 changes
were made. The separate approved two-file execution backport remains `d9070aa0`.

[Commitlint 39958144989](https://github.com/Hexalith/Hexalith.Builds/actions/runs/39958144989)
passed. [Normal CI 39958144971](https://github.com/Hexalith/Hexalith.Builds/actions/runs/39958144971)
attempt 2 passed at the exact catalog source; its first Module.Tests failure and both job snapshots remain
in `builds-catalog-ci-attempt-*`. The story did not rerun or cancel that CI.
Local locked commitlint identities/full message hashes and the successful owning
remote gates are retained separately from superseded drifted-tool receipts.

## Actual root verification

Fresh full restore succeeded. The final full Release build with `-warnaserror`
succeeded with zero warnings/errors (`mcpcli-final-build.*`). Final parent individual project commands and both channels are retained in
`parent-final-verification/`; earlier results remain in `final-root-tests/`:

| Project | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Abstractions | 20 | 0 | 0 |
| Analyzers | 19 | 0 | 0 |
| Core | 704 | 0 | 3 |
| CLI | 479 | 0 | 2 |
| MCP | 58 | 0 | 0 |
| Manifest | 177 | 0 | 0 |

The five skips are existing platform/benchmark conditions. No skipped test is
used to cover a story matrix row. `final-smoke-discovery.*` proves focused
non-live discovery lists exactly the one integration smoke without launching
source services.

## Executed matrix coverage

| Frozen matrix state | Executed covering evidence |
| --- | --- |
| Qualified helpers, built source, available Dapr | `GatewaySmokeTests.AuthenticatedQueryReturnsSuccessfulDocument`: final private run 1 passed, 0 failed, 0 skipped; actual Gateway POST returned 200 (`live-attempt-5/`). All three source services passed liveness; all four private infrastructure processes exited 0. |
| Missing helper / forbidden helper dependency | `AspireHelperDependencyTests.MissingHelperHasAnExactDiagnostic`, `MissingHelperRestoreCannotFallBackToWorkspaceOrGlobalPackages`, `HelperWithImplementationDependencyIsRejected` (each forbidden dependency case), `UnreviewedHelperIsRejected`, `SourceHelperIsRejected`: all passed within the final Manifest's 177 executed cases; diagnostics include exact package/dependency paths. |
| Missing / undeclared root checkout | `TopologyConfigurationTests.ExistingUndeclaredSourceFails`, `AlternateLayoutCannotReplaceRootSource`, `CopiedSourceIsNotAQualifiedCheckout`, `SiblingLinkIsRejected`, plus actual Program subprocess `TopologyLaunchTests.MissingDeclaredRootStopsLaunch`: passed, asserting exit and both channels before resources exist. |
| Missing Dapr prerequisites | `DaprPrerequisiteTests.MissingDaprProducesStandardSkipAndNeverClaimsLiveSuccess`: outer test passed, asserting the actual child smoke reports the exact standard diagnostic and one skip. The skipped child is not the covering result. |
| Resources alive / Gateway unusable | `GatewaySmokeBoundaryTests.AliveGatewayThatNeverAnswersQueryFailsWithinSmokeDeadline`: real HTTP liveness succeeds and real query stalls; executed test passes only on the shipped 30-second deadline, useful exact diagnostic and two real requests. |
| Conflicting user topology | Program subprocess `TopologyLaunchTests.ExistingApplicationStopsLaunch` plus direct identity/occupied-port guard cases: passed with exact diagnostics; no stop/reuse. Six malformed-record subprocess cases and weak-key launch rejection also passed. |

`TopologyAccessControlTests.MetadataDiscoveryRequiresGatewayPostAndDefaultDeny`
passed and seven actual-file permission mutations failed as expected. Disabling
mTLS also failed the covering test. `acl-regression/` preserves these executed
negative controls and restored positive results. Earlier root/auth/conflict
Program guard-removal mutation evidence remains in the historical continuation.

## Live runtime and limitations

The private Linux environment used the unchanged published helpers and platform
fixture, fixed IDs, authenticated app channels/JWT and default-deny Dapr ACL.
Actual Sentry and TLS control-plane services supply authenticated caller identity.
The final test-owned Gateway content root removed inherited sample registrations:
no sample metadata request occurred. The executable `verify-live-result.py` passes
for the final run and rejects the earlier passing run with inherited sample
registrations (`gateway-content-root-control.json`). Request timeout remains 30 seconds, separate
from bounded source startup and the wrapper's outer process deadline.

The pre-review run `20261023T135123Z-ecfde206` passed in 16.809 test seconds.
After review corrections, the parent final run `20261023T144400Z-93ddc6dd`
passed in 23.741 test seconds with two real 401 rejections and successful
pinned-client document assertions. Its final success completion log was not
flushed; the result is established by executed assertions, not an invented log.
The preceding passing run took 41.480 outer command seconds before content-root
isolation.
`live-attempt-1` through `live-attempt-3` retain the earlier routing/ACL/mTLS
failures rather than relabeling them. `private-runtime/README.md` records actual
prerequisites, binary/image hashes and the task-local reproduction command.
Private keys are excluded. No user AppHost or datastore was changed.

Full live vector semantics and blocking source-build CI remain stories 4.13 and
4.14, as required by the frozen scope. Normal owning Builds CI, parent audit and workflow review passed. Fourteen patch
findings are resolved; the two platform-lock findings share one pre-existing
upstream deferral. The mandatory outer deadline bounds the supported command. Superseded progress
notes are preserved in `historical-implementation-notes.md`.

## Final review verification

`review-fixes/README.md` records the focused corrections and removal controls.
`parent-final-verification/summary.json` is the current full-check summary:
1,457 passed, five existing skips, 177/177 Manifest cases and a live pass with
no skips. The unchanged CLI listener cleanup race initially recurred, then its
19-case class and full suite passed; it is already tracked at
`deferred-work.md:467`. The published platform lock wait is tracked once at
`deferred-work.md:589`. All private infrastructure exited cleanly, and user
processes and data remained untouched.
