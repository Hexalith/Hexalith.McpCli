# Private runtime qualification

The unchanged published-artifact fixture passed in separate Linux user, PID,
network and mount namespaces. The private veth pair supplies multicast-capable
networking. Actual Redis, Sentry, TLS placement and TLS scheduler listen on private
endpoints; their state and credentials live only in the task run directory.
Published helper IDs, workload/end-user authentication, default-deny ACL and
conflict checks are unchanged. No user AppHost was stopped or reused.

The final smoke (`../live-attempt-5/`) executed one test: one passed, zero failed,
zero skipped in 16.809 seconds. The real authenticated Gateway query returned
HTTP 200. All four owned infrastructure processes exited 0. An earlier passing
smoke and three failed diagnostic attempts remain separately identified; an
infrastructure-only probe is not counted as live acceptance.

The local executable runtime directory is
`/tmp/mcpcli-story412-isolation-mhb5mtn8`. `binaries.json` records SHA-256 hashes
and official source-image identities; no executable binaries or private keys are
vendored. `run-isolated.py` SHA-256 is
`f3ba84defe5a7ea99cddacec7d328cdce7a4e579bd5d12a3abba1586acd29d81`.
It creates fresh private CA/issuer credentials for each run and removes private
keys during cleanup. It passes `DAPR_TRUST_ANCHORS`, `DAPR_CERT_CHAIN`,
`DAPR_CERT_KEY`, `NAMESPACE=default`, `DAPR_CONTROLPLANE_TRUST_DOMAIN=public` and
`DAPR_CONTROLPLANE_NAMESPACE=default` only to its child runtime. Certificate
values are withheld from result files. Sentry uses trust domain `public` and port
50001; placement/scheduler use TLS and that same CA and Sentry.

Dapr initialization alone does not supply this mTLS infrastructure. Caller ACL
identity requires mTLS; see the [official self-hosted mTLS setup](https://docs.dapr.io/operations/security/mtls/).
Dapr CLI 1.18.2 reads the checked-in mTLS enablement but uses the standard
`localhost:50001` Sentry endpoint. Its runtime defaults control-plane trust to
`localhost` unless the two explicit control-plane environment variables above
are supplied. The earlier missing trust-domain environment attempt is retained
as a failed result, not relabeled as a pass.

Disposable isolated Dapr and Redis are mandatory, even if no app-ID conflict is
visible on the host. Operational index discovery writes state; never point this
smoke at a user Redis or reuse persistent state. The wrapper creates fresh data
and credentials per run, private networking and PIDs, and stops only its own
process groups. An outer process deadline is also mandatory.

Recreate the recorded Linux amd64 native binaries from digest-pinned official
images in a **new** task-owned directory. Docker is used only to pull and create
never-started extraction containers, which are removed by exact container ID.
The script verifies every extracted binary SHA-256 against `binaries.json` and
fails on existing destination directories or mismatches. It does not initialize
Dapr, start containers, stop user processes or connect to host Redis. Pulls have
300-second limits; copy/create/removal also have explicit bounds.

From the repository root, after the source servers and integration test build:

```sh
runtime_evidence=_bmad-output/implementation-artifacts/evidence/story-4-12/publication-20261023/expanded-publication/private-runtime
private_runtime="$(mktemp -d)/runtime"
timeout --signal=TERM --kill-after=20s 900 \
  python3 "$runtime_evidence/bootstrap-runtime.py" "$private_runtime"
MCPCLI_ISOLATED_RUNTIME_DIR="$private_runtime" \
timeout --signal=TERM --kill-after=20s 960 \
  python3 "$runtime_evidence/run-isolated.py" -- \
  dotnet tests/Hexalith.McpCli.Integration.Tests/bin/Release/net10.0/Hexalith.McpCli.Integration.Tests.dll \
  -class Hexalith.McpCli.Integration.Tests.GatewaySmokeTests
```

Install the Dapr CLI 1.18.2 and runtime 1.18.7 independently using the official
[Dapr installation instructions](https://docs.dapr.io/getting-started/install-dapr-cli/),
without invoking `dapr init` against a user environment. The wrapper uses the
installed CLI and `~/.dapr/bin/daprd`, while the bootstrap recreates its four
otherwise ephemeral prerequisites. The fixed image digests and binary hashes
fail closed if registry bytes no longer match the recorded qualification.

The wrapper requires Linux user/PID/network/mount namespace support, `unshare`,
`ip`, OpenSSL, the installed Dapr CLI/runtime and the independently extracted
binaries at the recorded runtime directory. It accepts the actual test command
after `--`, captures both channels and applies a separate 900-second outer bound.
The standard fixture keeps its startup limits and separate 30-second Gateway
request deadline. It affects only its private namespaces and owned process groups.
