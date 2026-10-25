# Story 4.13 final pass-3 qualification

All nine pass-3 patches are implemented and verified. The user-approved Parties
probes use offset 2 with page size 2, preserving the existing owner paging
contract and the approved vectors' original filters.

Fresh generation `2ee4b89b49db4c22b0ea4965a302bb19` passes **all 21 vectors with zero failures
or skips**. The independent audit proves 144 phases, exactly 53 single Command
submissions with 53 distinct message IDs, 91 Query attempts,
real cursor/time bindings, every original and added assertion, genuine empty
Redis backups and all 21 private topology cleanups. `paging-audit.json` separately
proves that Parties list/search each retain one matching first-page item, return
an empty second page, and retain total count 1 with offset metadata 2.

The updated 88-case live-tool Python suite and complete offline preflight pass.
The regression test rejects a server that repeats the first page. The six-row
matrix audit requires fresh live success for complete inputs and paging, and
binds its other rows to exact passing regression names.

Only the two companion plans and their Python regression expectations changed
since the preceding qualification. `validation-reuse.json` verifies 432 unchanged
source/configuration files, all 507 runtime DLLs, the four selected reference
commits and the four private runtime binaries. It binds reused successful
restore, Release/source-server builds, all six non-live .NET suites (1,531 passes,
five existing skips, including 251 Manifest cases), 158 conformance Python tests,
22-case discovery, five detected Python mutations and the independent smoke to
their exact prior receipts. These unchanged checks were not rerun solely for the
plan adjustment. Every vector still receives a fresh namespace and empty store.

The complete offset-1 failure packet remains byte-identical at
`../pass-3-patches-20261025/`: its 19-pass/two-failure lane and denied full
acceptance are historical evidence of the contract conflict. All 315 indexed
historical files were verified unchanged. The user's decision and the successful
replacement qualification are recorded in the story spec. No approved vector,
Contracts, dependency, upstream source or reference selection changed.

`commands.json` retains the new exact commands, exits and durations, with matching
stdout/stderr logs. `source-bindings.json` records the final input/runtime hashes.
`live/`, `live-audit.stdout.txt`, `paging-audit.json`, and `matrix-audit.json`
retain the passing semantic proof. `private-runtime-receipts/` contains 21 fresh
ownership receipts and actual empty Redis backups; the independent smoke's
receipt remains bound in the prior packet.

`live-inputs.tar.gz` and `runtime-diagnostics.tar.gz` preserve exact frozen inputs
and sanitized runtime logs. Every archived byte was read back and verified
before removing duplicate copies. Extract the archives beside this README to
restore their original relative paths. `retention-audit.json` records manifests
and credential-pattern checks; `artifact-index.json` hashes the retained packet.

`retain-evidence.py` is a one-time compaction helper. It refuses to run if either
output archive already exists, before copying receipts or changing evidence.

The retained `audit-paging.py` and `audit-reuse.py` are one-off scripts tied to
the original checkout at `/home/administrator/projects/hexalith/mcpcli`.
Paging requires the matching approved vectors and companion plans in that
checkout. Reuse also requires the original compiled DLLs at their recorded
paths, the recorded reference commits, the adjacent historical packet, and the
private runtime binaries at `/tmp/mcpcli-413-pass3-runtime-20261025/runtime`.
Extracting the archives alone does not provide those prerequisites. Both
scripts write their audit JSON beside the script; reuse also refreshes
`source-bindings.json`, so rerunning it changes the retained source snapshot.

`audit-live.py` instead takes explicit repository and lane directory arguments:
`python3 audit-live.py /path/to/mcpcli /path/to/this-packet/live`.
It uses the supplied checkout's matching vectors, plans and conformance helpers,
the adjacent `source-bindings.json`, and retained receipts/backups as a fallback
when the original runtime paths are absent. It does not require the original
compiled binaries or running topology.

`review-fix-verification.json` records the later focused review checks: compaction
refuses a rerun without changing any retained bytes, either archive independently
blocks compaction, and HTTP 400/401/403 plus a Core refusal each preserve the exact
diagnostic after one attempt. Its source hashes cover these review changes;
`source-bindings.json` remains the snapshot from the passing live qualification.
