# Query compatibility and named projection prerequisite

No upstream production repair or publication is required. The proposed missing
host-assembly diagnosis was disproved: `PartyAggregate` is in the host assembly,
which the existing `AddEventStoreDomainService` call already scans. Adding the
same assembly again would duplicate query registrations.

The clean detached Parties candidate at the path in `candidate.json` contains
only the new `PartyHostQueryDiscoveryTests.cs`. Its four cases pass against the
unchanged production host: authenticated metadata advertises each approved
query once, real DI resolves each handler once, and all three unchanged
actor-bearing Contracts 1.5.1 wire requests execute through the shared router
and authenticated `/query`, reading canonical models. The regression source,
exact build/test commands and output are retained here. `red-host-discovery`
records the attempted red check that unexpectedly passed and corrected the
diagnosis. `owner-preservation.json` proves the owning repository's staged user
changes and Program.cs were preserved. The temporary regression was removed
from the active owner checkout and retained in the detached candidate/evidence.

The earlier live failure also routed correctly. Its retained runtime stdout at
`/tmp/mcpcli-413-runtime-7jz660m_/runtime/runs/20261025T094504Z-8fb8b921/command.stdout.txt`
lines 1347–1395 shows EventStore invoking Parties `/query`, which returns HTTP
200. The package-mode `PartySdkQueryFailureReason.ReadModelUnavailable` aliases
to `actor-not-found-infrastructure`; the error meant the SDK detail read model
was missing. Decompiled actual runtime code and package/source bindings are
retained here. Query registry negative caching did not cause this failure.

Runtime lines 1292/1302 show both named projection routes denied with
`delivery_state_unavailable`; the private fresh Redis had no writer-v2 marker.
The legacy `/project` fallback returned 404 because Parties uses named SDK
projections. The fix is a test-topology prerequisite using existing platform
APIs:

- The isolated wrapper verifies `DBSIZE=0`, saves an actual Redis RDB backup
  before any application starts, and retains its SHA-256 proof.
- After verifying persisted administrator authority, the fixture verifies the
  backup and invokes the existing authenticated writer activation once, bound
  to the exact EventStore source commit. It then observes `/ready`.
- The default-deny ACL admits only the additional EventStore POST `/project/v2`
  route. The full-lane receipt requires the activation proof to match that
  child's genesis backup. No domain/control-plane state is written directly.

`live-party-create/live-lane.json` proves a fresh selected Parties create vector
passed: its Command was submitted once, and both the persisted read barrier
and every approved postcondition passed on their first Query attempt. Its
writer activation count is one, readiness passed, and owned cleanup passed.
The selected subset correctly retains `fullLiveAccepted: false`. The real
genesis RDB and isolation receipts are copied under
`live-party-create/isolated-runtime/`.

Verification: Release Manifest/integration build passed with warnings as
errors; 50 Python live-tool cases passed; eight focused bootstrap/ACL cases
passed. Exact commands are in `bootstrap-checks.json`, `red-commands.json`,
`inspection-commands.json` and `live-command.json`. Full 21-vector acceptance
remains for the parent audit and complete isolated lane.
