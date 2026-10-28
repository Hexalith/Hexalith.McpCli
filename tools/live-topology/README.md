# Disposable live topology runtime

Run the live Gateway smoke and semantic cases only through `run-isolated.py`. It creates fresh Linux
user, PID, network and mount namespaces, a private Redis, Dapr Sentry, placement
and scheduler, fresh mTLS credentials and disposable state. After checking all
four namespace identities, it sets `MCPCLI_ISOLATED_TOPOLOGY=1` for its child.
The integration fixture and live AppHost refuse execution without that sentinel;
non-launching AppHost preflight and composition inspection remain available.

Requirements: Linux amd64, Python 3.11 or later, GNU `timeout`, `unshare`, `ip`, OpenSSL 3 (`libssl.so.3` and `libcrypto.so.3`),
zlib (`libz.so.1`) and zstd (`libzstd.so.1`) shared libraries,
Docker with a successful `docker info`, Aspire CLI 13.6.1 with its DCP and dashboard
bundle in `~/.aspire/bundle` (`AspireUseCliBundle=true`; SDK/hosting 13.6.3),
Dapr CLI 1.18.2 and runtime 1.18.7 at
`~/.dapr/bin/daprd`. User namespaces and network namespace creation must be
permitted. Install Dapr independently without initializing or changing a user
environment. Build the three root source servers and integration tests using the
repository README first.

From the repository root, create a new task-owned directory and extract the four
native binaries from digest-pinned official images. The bootstrap verifies each
SHA-256 in `binaries.json`, refuses existing destination directories, and removes
only its own never-started extraction containers by exact ID. Docker pulls have
a 300-second bound; create, copy and removal commands have separate bounds.
Both pulled images remain in the host Docker store; remove them when no longer
needed with `docker image rm daprio/dapr@sha256:0ac4fadf0016be85065cdebab952a8350e468cf9283d26777b0307a14a10aecc redis@sha256:c35b83ce044bb6d148c484d36e059ad28e02d5714ba6731fb55b6421e2ed0ccf`.

If bootstrap fails, choose a fresh task-owned directory before retrying, for
example by rerunning `private_runtime="$(mktemp -d)/runtime"`. A failed destination
is deliberately non-reusable; bootstrap continues to refuse existing directories
and never overwrites their contents.

```sh
private_runtime="$(mktemp -d)/runtime"
timeout --signal=TERM --kill-after=20s 900 \
  python3 tools/live-topology/bootstrap-runtime.py "$private_runtime"
MCPCLI_ISOLATED_RUNTIME_DIR="$private_runtime" \
timeout --signal=TERM --kill-after=20s 960 \
  python3 tools/live-topology/run-isolated.py -- \
  dotnet tests/Hexalith.McpCli.Integration.Tests/bin/Release/net10.0/Hexalith.McpCli.Integration.Tests.dll \
  -class Hexalith.McpCli.Integration.Tests.GatewaySmokeTests -failSkips
```

`MCPCLI_ISOLATED_RUNTIME_DIR` must explicitly name the prepared directory; an
unset or empty value is refused before creating files. `-failSkips` makes a
skipped smoke fail with `FAIL_SKIP`, preserving the prerequisite diagnostic.

The wrapper records the command, both output channels, service diagnostics,
namespace identities and exit codes under `$private_runtime/runs/`. It enforces
a separate 900-second child deadline and stops only its own process groups.
Private signing keys are removed during cleanup and certificate contents are
withheld from result files. An outer process deadline remains mandatory because
the shared platform fixture's pre-existing file-lock wait precedes its startup
timeout. Never use a host Redis or user Dapr environment for this smoke.

These maintained tools are shared by later live-semantic and CI work. The
original qualified copies and receipts remain unchanged in the story 4.12
evidence directory. Non-live checks require the root-declared Builds checkout
and a restored, built production adapter. From the repository root, restore and
build the Integration.Tests project; this also builds its production
ConformanceHost dependency and provides the restore assets used by the Python
preflight tests. These checks run without starting source servers or Docker:

```sh
dotnet restore tests/Hexalith.McpCli.Integration.Tests/Hexalith.McpCli.Integration.Tests.csproj
dotnet build tests/Hexalith.McpCli.Integration.Tests/Hexalith.McpCli.Integration.Tests.csproj --no-restore --configuration Release -warnaserror
python3 -m pip install -r tools/conformance-vectors/v1/requirements.txt
python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'
```

## Complete semantic lane

Build the source servers and solution using the root README, then prepare the
private runtime above. `run-vectors.py` preflights the entire production-enrolled
set and launches one fresh isolated test process per approved vector:

```sh
MCPCLI_ISOLATED_RUNTIME_DIR="$private_runtime" \
timeout --signal=TERM --kill-after=30s 21600 \
  python3 tools/live-topology/run-vectors.py --output /tmp/mcpcli-live-vector-evidence
```

The outer six-hour bound covers 21 independently bounded children (960 seconds
each). The wrapper retains its existing 900-second child bound. The selected
Python runner has an eight-minute process budget, each CLI process a maximum of
30 seconds, and each read observation a 45-second deadline. Only Queries poll;
declared Command steps are submitted once, including intentional repeated
business actions declared as distinct vector steps. The independent smoke can
still be run with the earlier command and is not substituted for a vector.

The fixtures bootstrap `mcpcli-live-admin` through the existing authenticated
Development bootstrap, using the same fresh signing key as the Gateway. Before
executing any vector, a bounded privileged `get-global-administrators` Query must
return that persisted administrator. The independent smoke uses this same read barrier
before its single final usability Query, because resource liveness can precede
handler capability readiness. This infrastructure proof does not enroll
the excluded Query in the Catalog. The ACL admits only POST `/project` and `/project/v2` from
EventStore and POST `/api/v1/commands` from Tenants in addition to the smoke's
existing permissions. Authentication, mTLS and default deny remain required.

Before starting any application, the wrapper verifies `DBSIZE=0` and saves an
actual provider-native Redis RDB backup. It retains immutable backup bytes and a
SHA-256 receipt outside the repository. After proving persisted administrator
authority, the fixture invokes the existing authenticated platform writer-v2
activation endpoint once and observes `/ready`. The backup and private
namespaces establish a fresh store with no old writers or retry workers; no
domain data or control-plane state is written directly. The lane binds each
activation receipt to that child's genesis backup, rereads its retained RDB bytes
and verifies the SHA-256 and owned location before accepting the child. This prerequisite enables
Parties' SDK named projections; a legacy `actor-not-found-infrastructure` query
error can mean a missing SDK read model rather than actor routing.

`plans/*.json` are test-only companions bound to exact approved vector SHA-256
digests. Every original step occurs once in the original order. Read barriers
check persisted state after Commands. A repeated idempotent Command step is
proven by its single accepted submission plus unchanged persisted state; all
original static assertions remain.
Scripted cursor assertions explicitly capture nonempty returned cursors and bind
the later continuation call. The audit plan captures real event timestamps and
probes category exclusion, inclusive lower/upper bounds, and windows before and
after matching events. Every original, observation and resolved dynamic call
passes production Core validation without contacting a Gateway before dispatch.
Malformed CLI output, mismatched response identities and missing Query documents
fail immediately; they are not read-convergence conditions.
There are no module-specific runner branches or direct state-store mutations.

For diagnostics, these commands still preflight the complete approved set:

```sh
python3 tools/live-topology/run-vectors.py --output /tmp/mcpcli-live-preflight --preflight-only
MCPCLI_ISOLATED_RUNTIME_DIR="$private_runtime" timeout --signal=TERM --kill-after=30s 1000 \
  python3 tools/live-topology/run-vectors.py --output /tmp/mcpcli-live-selected --operation tenants.get-tenant-audit
```

A preflight-only receipt and a successful selected subset always retain
`fullLiveAccepted: false`. An empty `--operation` is refused; a live run without
`MCPCLI_ISOLATED_RUNTIME_DIR` fails before preflight. Each invocation invalidates `live-lane.json` first
and uses a new generation directory for child outputs. The lane requires exactly
one passing, unskipped Operation-labelled xUnit case, a matching fresh semantic
receipt and successful owned infrastructure cleanup for each child. A missing
prerequisite, skipped case, timeout, assertion mismatch or incomplete run cannot
grant full acceptance. Standard platform prerequisite diagnostics remain in
child logs. Receipts record complete coverage and every attempted outcome even
when another vector fails. `live-result.json` retains the Operation, phase,
assertion path, query attempts, sanitized documents and immutable input bindings;
credentials are excluded. Failed vectors also print their sanitized phase and
assertion diagnostics so they appear in the selected test failure. Namespace and service cleanup details remain under
`$private_runtime/runs/`. The non-live CI job discovers all 21 vector cases plus
smoke; the required CI lane executes them through the hooks below.

## Required CI lane

The caller pins the qualified Builds workflow and supplies the Integration.Tests
project, `microsoft-testing-platform` and `aspire-continue-on-error: false`.
Builds keeps the six non-live Release test projects ahead of its Aspire tier,
builds the Release solution again in that fresh job and initializes Dapr CLI
1.18.2/runtime 1.18.7 before invoking preparation. Linux amd64, Python 3.11+,
OpenSSL 3, zlib/zstd, Docker, GNU `timeout`, Git, curl, `unshare`, `ip` and working
user/PID/network/mount namespaces are required. The hooks name missing tools,
sources, namespace permissions and source-build commands before live acceptance.
They never initialize nested dependencies or change host Redis/Dapr services.
The SDK is selected by `global.json`, including its `latestPatch` roll-forward
policy. Preparation records both the declared policy and selected SDK version;
an SDK-resolution failure stops preparation before source builds.
When the initial namespace probe is denied on a disposable GitHub-hosted runner,
preparation uses bounded noninteractive `sudo sysctl` to permit unprivileged
user namespaces, then repeats the actual probe before building sources.
This follows [Ubuntu's user-namespace configuration](https://ubuntu.com/blog/ubuntu-23-10-restricted-unprivileged-user-namespaces).
Local and self-hosted environments retain operator-managed namespace permissions.
Every live child still proves all four private namespaces; setup or probe failure
fails preparation.

`prepare-ci.sh` first validates all three declared direct Git source checkouts,
then builds EventStore, Tenants and Parties from their own working directories.
Each server build has its own 300-second deadline and uses the documented
`UseHexalithProjectReferences=false` / `UseNuGetDeps=true` Release switches.
Tenants also sets `HexalithEventStoreFromSource=true` so it compiles against the
sibling EventStore checkout. That checkout contains the routing contracts added
after the published `Hexalith.EventStore.Contracts` 3.128.2 package.
Aspire CLI 13.6.1 is installed from its official Linux x64 release archive when
absent, with a pinned SHA-256 verified before extraction; bounded
`aspire setup` extracts its embedded DCP/dashboard bundle when missing. An
existing incompatible CLI or Dapr version is refused. Python requirements are
installed in a task-owned virtual environment. The existing bootstrap extracts
the four digest-pinned, SHA-256-verified binaries into a new runtime beneath
`RUNNER_TEMP` (the system temporary directory locally). Only a nonsecret
preparation receipt path is exported through `GITHUB_ENV`. Source SHAs and Git
status, each source build's resolved `HexalithEventStoreVersion`, tool versions
and executable hashes are retained. Only McpCli's own restore pins EventStore
3.128.3. Source servers follow their own configuration and the pinned Builds
catalog; `preparation.json` records the version each one resolves.

From the repository root, after the focused Release checks and host Dapr
initialization, run the same preparation and execution path:

```sh
ASPIRE_EVIDENCE_PATH=TestResults/live-ci bash tools/live-topology/prepare-ci.sh
ASPIRE_EVIDENCE_PATH=TestResults/live-ci bash tools/live-topology/run-ci.sh
```

The preparation hook has a 2280-second outer deadline inside its 40-minute step.
Its prepared runtime must
have no previous runs and still contain the qualified binaries. The execution
hook has a 17700-second outer deadline inside its 300-minute step:
`run-vectors.py` gets 16200 seconds and
the independent `GatewaySmokeTests` wrapper gets 960 seconds with `-failSkips`.
The vector runner's 960-second child and wrapper's 900-second command limits
remain enforced. The 360-minute hosted job budget includes preparation, testing,
setup and upload. The vector aggregate may time out before the sum of every
child's maximum budget; that is a failed lane, with partial evidence retained.
Each hook's 30-second kill grace fits inside its Actions step deadline.
On cancellation, detached-child cleanup waits ten seconds after TERM and at
most five more after KILL so the hook can retain its failure receipt.

`ASPIRE_EVIDENCE_PATH` must be a repository-relative directory without traversal
or symbolic links. Its default is `TestResults/live-ci`.
Preparation requires an absent or empty evidence directory, and records an
ownership marker before writing its receipts. A retry needs a fresh evidence
directory, for example `ASPIRE_EVIDENCE_PATH=TestResults/live-ci-retry`, supplied
to both hooks; existing user files are refused and left unchanged. Builds rejects
nonempty evidence before enabling its upload. `RUNNER_TEMP` must be outside the
evidence upload directory. Failed preparation retains its owned private directory
path for cleanup. Nested Python processes inherit the prepared virtual environment.
Every file in a fresh extraction from the selected qualified Aspire CLI must
match the installed bundle; mismatched installed bytes are refused.
GitHub-hosted runners first refresh the complete installed bundle with the pinned
CLI's `setup --force`, including its managed launcher, before this hash comparison.

Each run invalidates
`ci-live.json` before execution and writes a new generation directory. Acceptance
requires exactly 21 passing vector outcomes, complete coverage, fresh matching
semantic receipts, successful cleanup and a separate one-case, unskipped passing
authenticated smoke XML. Vector assertion failures still allow the independent
smoke attempt; neither smoke nor preflight/subset evidence can replace vectors.
The runner refuses reused private runtimes. Rerun preparation to retry a lane.

The `aspire-hook-evidence` artifact is retained seven days on success and failure
after hook paths have passed upstream validation. It contains `preparation.json`,
per-command sanitized stdout/stderr and exit/deadline records, `ci-live.json`,
generation-specific vector receipts and smoke XML, and allowlisted runtime logs
under `<generation>/runtime-diagnostics/`. Runtime keys, certificate material,
Redis RDB files and scheduler data are excluded; JWTs, PEM material and known
credential values are redacted from diagnostic text. Raw private runtime state
stays outside uploaded evidence. Keep its location from `preparation.json` until
diagnostics are complete, then remove only that task-owned directory.

Paired package publication remains disabled; the bootstrap-only release gate
continues to refuse it.
