# Disposable live topology runtime

Run the live Gateway smoke only through `run-isolated.py`. It creates fresh Linux
user, PID, network and mount namespaces, a private Redis, Dapr Sentry, placement
and scheduler, fresh mTLS credentials and disposable state. After checking all
four namespace identities, it sets `MCPCLI_ISOLATED_TOPOLOGY=1` for its child.
The integration fixture and live AppHost refuse execution without that sentinel;
non-launching AppHost preflight and composition inspection remain available.

Requirements: Linux amd64, Python 3, GNU `timeout`, `unshare`, `ip`, OpenSSL,
Docker with a successful `docker info`, Dapr CLI 1.18.2 and runtime 1.18.7 at
`~/.dapr/bin/daprd`. User namespaces and network namespace creation must be
permitted. Install Dapr independently without initializing or changing a user
environment. Build the three root source servers and integration tests using the
repository README first.

From the repository root, create a new task-owned directory and extract the four
native binaries from digest-pinned official images. The bootstrap verifies each
SHA-256 in `binaries.json`, refuses existing destination directories, and removes
only its own never-started extraction containers by exact ID. Docker pulls have
a 300-second bound; create, copy and removal commands have separate bounds.

```sh
private_runtime="$(mktemp -d)/runtime"
timeout --signal=TERM --kill-after=20s 900 \
  python3 tools/live-topology/bootstrap-runtime.py "$private_runtime"
MCPCLI_ISOLATED_RUNTIME_DIR="$private_runtime" \
timeout --signal=TERM --kill-after=20s 960 \
  python3 tools/live-topology/run-isolated.py -- \
  dotnet tests/Hexalith.McpCli.Integration.Tests/bin/Release/net10.0/Hexalith.McpCli.Integration.Tests.dll \
  -class Hexalith.McpCli.Integration.Tests.GatewaySmokeTests
```

The wrapper records the command, both output channels, service diagnostics,
namespace identities and exit codes under `$private_runtime/runs/`. It enforces
a separate 900-second child deadline and stops only its own process groups.
Private signing keys are removed during cleanup and certificate contents are
withheld from result files. An outer process deadline remains mandatory because
the shared platform fixture's pre-existing file-lock wait precedes its startup
timeout. Never use a host Redis or user Dapr environment for this smoke.

These maintained tools are shared by later live-semantic and CI work. The
original qualified copies and receipts remain unchanged in the story 4.12
evidence directory. Non-live checks run with:

```sh
python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'
```
