# Disposable live topology runtime

Run the live Gateway smoke and semantic cases only through `run-isolated.py`. It creates fresh Linux
user, PID, network and mount namespaces, a private Redis, Dapr Sentry, placement
and scheduler, fresh mTLS credentials and disposable state. After checking all
four namespace identities, it sets `MCPCLI_ISOLATED_TOPOLOGY=1` for its child.
The integration fixture and live AppHost refuse execution without that sentinel;
non-launching AppHost preflight and composition inspection remain available.

Requirements: Linux amd64, Python 3.11.4 or later,
GNU or uutils coreutils `timeout`, `unshare`, `ip`, OpenSSL 3 (`libssl.so.3` and `libcrypto.so.3`),
zlib (`libz.so.1`) and zstd (`libzstd.so.1`) shared libraries,
Docker with a successful `docker info`, Aspire CLI 13.6.1 with its DCP and dashboard
bundle in `~/.aspire/bundle` (`AspireUseCliBundle=true`; SDK/hosting 13.6.4),
Dapr CLI 1.18.2 and runtime 1.18.7 at
`~/.dapr/bin/daprd`. User namespaces and network namespace creation must be
permitted. For direct wrapper runs, install Dapr independently without
initializing or changing a user environment. The canonical lane uses the exact public packages and qualified source selection
through the CI hooks below; ordinary source builds do not establish that profile.

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
```

Low-level wrapper invocations also require the source/package-qualified native
profile and environment provided by `ci.py`; the bootstrap alone is insufficient.
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

After successful qualified preparation, `run-ci.sh` invokes `run-vectors.py`
with the inherited native profile and fresh package cache. It preflights the entire
production-enrolled set, runs the shared-head boundary in a fresh isolated process,
then launches one new isolated process per approved live vector and the independent smoke.
A failed early boundary stops before the vector sweep. Each case runs once.
Use the bounded preparation/execution hooks
below; direct default/native launches do not establish the canonical profile.

Each vector child retains its independent 960-second bound. The wrapper retains its existing 900-second child bound. The selected
Python runner has an eight-minute process budget, each CLI process a maximum of
30 seconds, and each read observation a 45-second deadline. Only Queries poll;
declared Command steps are submitted once, including intentional repeated
business actions declared as distinct vector steps. The independent smoke is not substituted for a vector.

The fixtures bootstrap `mcpcli-live-admin` through the existing authenticated
Development bootstrap, using the same fresh signing key as the Gateway. Before
executing any vector, a bounded privileged `get-global-administrators` Query must
return that persisted administrator. The independent smoke uses this same read barrier
before its single final usability Query, because resource liveness can precede
handler capability readiness. The same smoke case also sends one valid signed nonmember
administrator hint through the real owner command boundary. It requires the exact
permission rejection and independently reads the target tenant as the persisted
administrator before and after to prove it remains absent. Anonymous and forged
requests still require 401; the selection includes every approved live vector plus independent smoke and shared-head boundary cases. This infrastructure proof does not enroll
the excluded Query in the Catalog. The shared composition binds the finite actual
SDK domain-service route inventory to EventStore's real sidecar identity and the
required bound-bootstrap, stream-read and query routes to their actual peer
identities. Authentication, mTLS and default deny remain required.

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
digests. An approved live vector is an approved vector with a companion plan; a
vector without one runs in loopback only. The preflight fails a plan that has no
approved vector, and fails a module unless every Operation kind it declares has at
least one approved live vector. It validates every approved vector against the
restored package and its Operation Shapes, and binds each selection to the restored
package version and archive hash. A version difference or an operation that no
inventory row mentions is reported as a `reported: …` stderr line and in the
`reported` array of `live-lane.json`; it never changes the exit code. Every original step occurs once in the original order. Read barriers
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
`$private_runtime/runs/`. The non-live CI job discovers every approved live vector case plus
smoke and shared-head boundary; the required CI lane executes them through the hooks below.

## Required CI lane

The caller pins the qualified Builds workflow and supplies the Integration.Tests
project, `microsoft-testing-platform` and `aspire-continue-on-error: false`.
Builds keeps the six non-live Release test projects ahead of its Aspire tier,
builds the Release solution again in that fresh job and initializes Dapr CLI
1.18.2/runtime 1.18.7 before invoking preparation. Linux amd64, Python 3.11.4+
with `venv` and `ensurepip` support, OpenSSL 3, zlib/zstd, Docker,
GNU or uutils coreutils `timeout`, Git, curl, `unshare`, `ip` and working
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

`prepare-ci.sh` authenticates the complete native runtime selection in
`native-runtime.json`: exact public EventStore **4.1.0** archives, public Tenants
**7.0.5** archives and their embedded repository commits, plus the separately
qualified Parties and Platform source revisions. The independent
Testing.Integration **3.128.4** package continues to own the test lifecycle.

Generic CLI and MCP query requests preserve every descriptor-declared
`projectionActorType`, including the frozen published Parties selectors. SDK
4.1.0 supplies the exact owner-enrolled selector policy. The immutable Parties
source selection includes its three digest-bound compatibility bindings; foreign
selectors remain refused. The committed catalog chooses the actual receiver.
Fresh complete native CI remains required for this selected cohort; offline
scripted parity, owner compilation and preflight do not establish live acceptance.

Missing public packages, hash or source mismatches, wrong repository identities,
linked or dirty owned checkouts refuse before source selection. Only disposable
GitHub-hosted CI may fetch and detach a declared root checkout at its exact
qualified commit; local revisions and nested dependencies are never updated.

All builds and nested preparation processes inherit a fresh task-owned
`NUGET_PACKAGES`. The actual gateway, domain hosts, separate Parties adapter and
Integration.Tests/AppHost are built with the public SDK cohort. Parties retains
its qualified Tenants 5.11.2/Memories 3.0.11 dependency selections. Source hosts and
the separate adapter use the root McpCli 2.0.0 pin so their Abstractions identity
matches the AppHost, including later SDK/Aspire rebuilds. The Parties
adapter remains a separate compiled library. Its ordinary build uses
`CopyLocalLockFileAssemblies=true` to materialize the genuine package runtime
closure; every deployed SDK DLL must match its public archive before preparation
is accepted. Online source, AppHost and client builds explicitly audit all dependencies with warnings as errors.
Preparation requires low-level auditing without advisory exclusions or NU19xx warning suppression and retains the effective restore policy.
`native-reader-audit.json` binds both NuGet content hashes and actual archive SHA512 values, plus exact project, Program.cs and any declared PublishedCatalogArtifactCohort.cs input hashes, before the vector lane and each independent case. The private reader also binds the actual direct root-declared Builds catalog, forces that path without sibling fallback, disables reader-only automatic Directory.Build/Packages imports and the inherited source-host post-import hook, and preserves that hook for source owners. Expected project/bindings/source/SDK-policy digests come from sealed in-memory bytes before writing. It copies the audited source files present in the frozen Platform revision, refuses extra source files regardless of extension case, and rechecks seals before compilation, immediately after build before generation, and after generation. Safe preparation evidence retains separate original and copied source digests. Each private reader restores first,
checks every package archive and extracted asset against that proof, then builds with
`--no-restore`. Only the isolated advisory-feed refresh is disabled; native evidence
retains the exact audited graph. No server dependency edge or loader exception is added. The source
catalog retains the pinned root-declared Builds revision with the root's exact
Redis 3.4.31 override. A task-owned MSBuild post-import override also reaches SDK
owner preparation and later Aspire child rebuilds, clearing owner-appended
`WarningsNotAsErrors` exemptions so their compiler policy and deterministic bytes
match preparation. Preparation hashes both private
catalog files and the pinned catalog; execution rejects source or file drift
before vectors and again before smoke. Server build commands retain their
separate 300-second bounds. The owned gateway's mandatory
configuration snapshot is verified against native source commit
`dbc6e7e08d605ba6c6c790e3e08a15dc8bbdec8a`, matching the public 4.1.0 archive
metadata; normal overrides, real JWT validation and sidecar tokens remain active.

Before creating any digest material or catalog authority, the AppHost verifies
the genuine empty pre-application Redis backup. The selected Tenants host uses
SDK preparation of its real Contracts/Server artifacts and dependency closure.
Parties preserves its separate EventStoreExtensions artifact: the existing
qualified Platform CatalogBuilder prepares and checks its actual adapter factory,
compiled declarations and policies without adding a server dependency edge.
The shared `AddEventStoreDevelopmentRouteCatalog` composes the real three-host
model, actual sidecar identities, finite native receiver traffic and run-private
custody. Its SDK model observer and actual hosts perform prepare/ready/commit;
all three persisted readbacks must agree before the administrator barrier.
Composition and metadata ownership remain alive until the application stops;
private digest custody is then removed through its ownership marker.

Tenants receives a fresh run-owned bound-stream proof key, with matching gateway
trust limited to `tenants` and `global-administrators`, plus its existing
owner-bound bootstrap settings. The bootstrap query uses
`platform:global-administrators`; smoke lists `platform:tenants`. Fixture JWTs
carry the signed `eventstore:surface`, exact platform permissions and normal
tenant grants, with no reserved `system` tenant grant or human authority shortcut.
The excluded administrator barrier uses its actual UI-only eligibility through
a separate exact read identity; it is not exposed to the agent Catalog.
Anonymous/forged credentials still require 401. Internal storage namespaces and
publisher topics remain unchanged. The persisted administrator, authenticated
writer-v2 activation, readiness, persisted effects and owned cleanup remain
independent gates.

Preparation seals actual archive hashes, all deployed host DLL/JSON hashes,
selected sources and used settings/sidecar configurations. Execution rechecks
those identities before vectors and again before independent smoke. The
`head-catalog.json` receipt also captures discovery from those compiled CLI and
MCP heads, requiring equal documents, and records SHA-256 for every head DLL and
each module's exact `list_operations` structured content. Its full Catalog digest
hashes the module-name-to-structured-content map. All Catalog digests use sorted
keys, compact separators and UTF-8 JSON with `ensure_ascii=false`. Discovery
submits no Command or Query. Preparation binds the receipt's exact file hash;
the capture refuses binary drift while reading discovery. The sanitized
`native-catalog.json` records the source-selection/preparation digests,
actual SDK artifacts and matching credential-free peer readback. Private custody,
keys, RDB bytes and raw operational state remain outside uploaded evidence.
This is infrastructure for native acceptance; public artifact approval and a
complete successful remote vector and independent-case lane remain separate requirements.

Aspire CLI 13.6.1 is installed from its official Linux x64 release archive when
absent, with a pinned SHA-256 verified before extraction; bounded
`aspire setup` extracts its embedded DCP/dashboard bundle when missing. An
existing incompatible CLI or Dapr version is refused. Python requirements are
installed in a task-owned virtual environment. The existing bootstrap extracts
the four digest-pinned, SHA-256-verified binaries into a new runtime beneath
`RUNNER_TEMP` (the system temporary directory locally). Only a nonsecret
preparation receipt path is exported through `GITHUB_ENV`. Source SHAs and Git
status, each host's selected `HexalithEventStoreVersion`, gateway provenance,
tool versions and executable hashes are retained. Source-checkout commits record
the domain code; the snapshot manifest records its exact configuration source.
The separate gateway package source commit identifies the deployed gateway
implementation.

For a local run, first place each clean direct root checkout for
`Hexalith.EventStore`, `Hexalith.Tenants`, `Hexalith.Parties` and
`Hexalith.Platform` at its exact selected commit in
[`native-runtime.json`](native-runtime.json). A normal root submodule
initialization follows the root gitlinks, which can differ from these qualified
runtime selections. The local hook refuses to change source revisions; only
disposable GitHub-hosted CI selects them automatically. Keep nested submodules
uninitialized.

From the repository root, after the focused Release checks and the workflow's
full `dapr init --runtime-version 1.18.7`, run the same preparation and execution
path:

```sh
ASPIRE_EVIDENCE_PATH=TestResults/live-ci bash tools/live-topology/prepare-ci.sh
ASPIRE_EVIDENCE_PATH=TestResults/live-ci bash tools/live-topology/run-ci.sh
```

The preparation hook has a 2280-second outer deadline inside its 40-minute step.
Its prepared runtime must
have no previous runs and still contain the qualified binaries. The execution
hook has a 17700-second outer deadline inside its 300-minute step:
`run-vectors.py` gets the outer budget minus 960 seconds for each independent case and 600 seconds of provenance/cleanup headroom (currently 15180 seconds). Both independent wrappers, `GatewaySmokeTests` and `SharedHeadBoundaryTests`, get 960 seconds with `-failSkips`. Each owns a separate isolated runtime; the expected runtime count is derived from the vector inventory plus the independent-case registry.
The vector runner's 960-second child and wrapper's 900-second command limits
remain enforced. The 360-minute hosted job budget includes preparation, testing,
setup and upload. The vector aggregate may time out before the sum of every
child's maximum budget; that is a failed lane, with partial evidence retained.
Each hook's 30-second kill grace fits inside its Actions step deadline.
On cancellation, detached-child cleanup waits at most 25 seconds after TERM,
then kills the owned process group and waits at most one more second for its
supervisor, so the hook can retain its failure receipt.

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
requires every approved live vector outcome to pass, complete coverage, fresh matching
semantic receipts, successful cleanup and separate one-case, unskipped passing
authenticated smoke and shared-head boundary XML. Each declared Query observation runs through CLI and MCP; MCP never submits a vector Command. The early boundary already has its own result before vectors;
vector assertion failures still allow the independent smoke attempt. Neither independent case nor preflight/subset evidence can replace vectors.
Each independent child receives its current generation's `smoke/` or `boundary/` directory as
`MCPCLI_LIVE_OUTPUT` for the writer-bootstrap receipt, after inherited live and
Gateway settings have been removed.
Pending Operations marked `running` at a deadline or cancellation are retained
as interrupted Operations and named in stderr. On cancellation, including when
smoke is interrupted after a vector failure, `ci.py` exits 143 and `ci-live.json`
records `SystemExit: 143`. The hook's own `timeout` then exits 143 under GNU
coreutils and 124 under uutils.
The runner refuses reused private runtimes. Rerun preparation to retry a lane.

The `aspire-hook-evidence` artifact is retained seven days on success and failure
after hook paths have passed upstream validation. It contains `preparation.json`,
per-command sanitized stdout/stderr and exit/deadline records, `ci-live.json`,
generation-specific vector receipts and smoke XML, and allowlisted runtime logs
under `<generation>/runtime-diagnostics/`. Runtime keys, certificate material,
Redis RDB files and scheduler data are excluded; JWTs, opaque Bearer credentials,
complete or truncated PEM material and known credential values are redacted from
diagnostic text by `scripts/evidence_redaction.py`. Named private-key JSON and XML
values are redacted even in nested escaped diagnostics or malformed XML. Raw private runtime state
stays outside uploaded evidence. Keep its location from `preparation.json` until
diagnostics are complete, then remove only that task-owned directory.

## Scanning an evidence packet

Before recording Story 5.4's final evidence, sanitize the retained diagnostics
with the shared redactor and scan the complete final packet from the repository
root. Choose a new receipt path; the scanner never overwrites a receipt or edits
source evidence:

```sh
python3 scripts/scan-evidence-secrets.py \
  _bmad-output/implementation-artifacts/evidence/story-5-4 \
  --receipt _bmad-output/implementation-artifacts/evidence/story-5-4/secret-scan.json
```

Exit 0 means clean under `mcpcli-evidence-redaction/v1`; exit 1 means recognized
sensitive content was detected; exit 2 means the packet could not be completely
scanned or its receipt could not be written. Findings contain only relative file
names and rule identifiers, without source snippets or credential values. A
finding applies to the whole file, including decoded JSON/XML diagnostics.

The JSON receipt is also printed to stdout. It binds every input's relative path,
byte length and SHA-256, a digest of that sorted manifest, the redaction policy
and SHA-256 hashes of the scanner and redactor implementations. Output and ordering
are deterministic for identical input bytes and environment. Known values from
credential environment variables are checked as well; only their count is
recorded. The receipt itself is the only excluded path when it is created inside
the packet. Freeze all other packet files before scanning. Any edit or added file
requires another scan with a new receipt destination; compare the receipt's
manifest with the final packet.

There are no extension or hidden-file exclusions. Inputs must be UTF-8 text or
BOM-marked UTF-16 text; unsupported binary/archive formats, invalid encodings,
non-whitespace C0 controls and DEL, links, special files, unreadable inputs and
empty packets fail closed. Render terminal controls as plain text first. Extract
archives and select the sanitized text packet before scanning; record binary and
downloaded artifact hashes in the packet. This policy detects the credential and
private-key forms covered by the shared redactor, rather than arbitrary unknown
secret strings. Retention-policy changes and a general repository scanning hook
remain separate work. A clean receipt establishes neither live acceptance nor an
owner verdict.

Paired package publication requires exact-source CI, a successful staged pair,
candidate-bound acceptance and production approval; see
`docs/release/operator-setup-checklist.md`.
