# Restore green main — local evidence

Baseline: `a8792ab1c4843a102988f1ccb49fde5df01fd382`.

Downloaded `aspire-hook-evidence` with `gh run download` for runs 42130012324 (green), 42184403625, 42191198755, and 42195205971. Both earlier failed runs have exactly 21 failed vector outcomes plus smoke; every XML failure is the same compiled-declaration read failure. Their aggregate vectors-process.stderr.txt files are empty. The latest run stops during preparation because the frozen Platform revision has no cohort source file.

The public Abstractions 2.0.1 DLL in the reproduction has SHA-256 `aeb390050b08451827b147a958ba355e1e5c96de526834221645028b85c26c2e`, matching failed hosted preparation. `old-loader.txt` exposes the underlying FileLoadException. `qualified-loader.txt` uses the identical frozen Parties source against 2.0.0 and successfully reads all 41 declarations. No upstream runtime defect was demonstrated.

The selected native runtime commits, public artifact manifest and root versions are unchanged from the last green run. The root gitlink comparison is recorded in the spec; all gitlinks remain unchanged. Both workflow references now match Builds `beb85e497957fedc66854013efd2cc4bd216ecbc`.

Checks passed:

- `dotnet restore Hexalith.McpCli.slnx`
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` (zero warnings/errors, repeated after final reader test additions)
- `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release`: 359/359 on retry. First attempt: 358/359, one existing boundary test failed with address already in use.
- Final reader/audit classes invoked directly: 65/65, including the three subsequent negative cases.
- Complete preflight: `/tmp/mcpcli-green-main-preflight/live-lane.json`; `fullLiveAccepted: false` as required.
- Built discovery: exactly 21 approved vector cases plus independent smoke.
- Real MSBuild inherited package-override control and frozen-reader runner/audit control.
- `bash scripts/check-agent-instructions-sync.sh` and `git diff --check`.

First Python suite: 196/197, with one exact command expectation requiring the new version flag. The corrected diagnostic test passes; the complete final rerun and hosted main qualification are pending at this snapshot. Local checks are not live acceptance.
