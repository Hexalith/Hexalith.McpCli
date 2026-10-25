# Story 4.13 implementation evidence

The post-review full lane passes all 21 vectors with zero failures/skips.
`live-complete/live-lane.json` identifies the authoritative generation
`a45347517d3446de80684c5b084ca366`. The independent audit proves 142 declared
phases, 53 Command submissions with 53 distinct message IDs, 89 Query attempts,
matching current plan hashes and successful owned cleanup for every child.
The final independent smoke also passes with zero skips and verified cleanup.

`review-fixes/parent-verification/` contains the final exact commands, exits,
stdout/stderr and source/binary hashes: fresh restore, Release warnings-as-errors
build, all 70 live-tool Python tests, all 240 Manifest tests, exact discovery of
21 Operation-labelled cases plus smoke, the complete live lane and final smoke.
`acceptance-audit.json` independently checks phase cardinality and current
bindings. `parent-audit/live-acceptance-audit.json` and `matrix-audit.json` record
the final command/observation and six-row acceptance matrix audits.

`commit/` retains the exact full local completion message, successful pinned
commitlint validation and tooling installation evidence.

Three independent BMAD reviewers reported fourteen findings, including one
shared adapter-handoff issue. All were verified, patched and covered by tests;
none were deferred. The spec's Review Triage Log records each individual verdict.
The corrections bind executable package identities and private DLL bytes to the
approved restore, forward the chosen adapter and parent bindings before execution,
enforce Command envelopes/unique IDs and phase cardinality, retain sanitized
progress under termination, reject weakened barriers/noninteger selectors, read
fragmented Redis replies, and add negative Parties filters and update preservation
assertions. `review-fixes/verification.json` retains the implementation handoff's
focused checks; the parent's complete final checks above supersede them.

The external workspace update at `8962e2f` advanced Builds to EventStore 3.127.0.
The production policy and its exact-version expectations were reconciled to that
existing selection. Enrolled Contracts remain Parties 1.5.1 and Tenants 5.10.0;
approved vector and approval bytes are unchanged.

Other retained validation and historical evidence:

- `parent-audit/final/`: both sample conformance gates, all 158 conformance Python
  tests, mandatory restore after loopback and restoration of the production
  adapter manifest. The initial final-stage independent smoke failure is retained;
  its bootstrap read barrier then passed three fresh starts. The latest final
  smoke after review fixes passes separately under the authoritative directory.
- `parent-audit/`: successful unchanged CLI retry (479 passes, two Windows skips),
  dependency reconciliation, earlier builds and full-lane invocations. Restoring
  standard `/dev/shm` mode 1777 repaired the environment; CLI behavior was not changed.
- `verification/`: Abstractions 20, Analyzers 19, Core 704 with three existing skips,
  MCP 58, initial closure/tmpfs failures and the original discovery/conformance checks.
- `final-checks/`, `source-builds/`, `prerequisites/`: intermediate focused checks,
  bounded root source-server builds and hash-qualified disposable runtime preparation.
- `live-complete/7e8ed532bf2b45a8b9075294c42530b8/qualification-before-review/`:
  the earlier complete 21-pass qualification, source bindings and runtime receipts,
  preserved before the review corrections. Its root receipt cannot supersede the
  authoritative latest generation named above.
- `private-runtime-receipts/`: final genuine genesis RDB backups, namespace
  provenance, runtime ownership/cleanup and the final smoke receipt. The original
  private runtime retains its own corresponding files outside the repository.
- `upstream-projection-protocol/`: exact two-file owner repair, real-host red/green
  serialization tests, four unchanged query compatibility cases, validated commit,
  pushed PR and integrated server build. The clean reference is at
  `d83fec24167aafd4edfc4d2f7310d6a87a218a1c`.
- `upstream-query-compatibility/`: investigation disproving missing query discovery,
  plus the initial selected proof after authenticated writer activation.
- `live-before-parties-protocol-fix/`: complete failed run (18 pass, three Parties
  mutations fail). `live-parties-projection-prerequisite-failure/` retains earlier
  failed/aborted prerequisites. Neither grants acceptance.
- `live-coverage-bug/`: explicitly rejected subset incorrectly reported as complete;
  independent coverage enforcement and regression tests replace it.
- `live-diagnostic-create/`, `live-lane-attempt/`, `coverage-status.json`,
  `offline-preflight-before-closure-guard/`: historical selected/preflight evidence,
  superseded by the final complete lane.

`captured-inputs.tar.gz` preserves 3,358 exact input copies across all generations.
Every original/new member was read back and checked against its SHA-256 before
consolidation. `captured-inputs.json` hashes the archive and complete path/hash
inventory; the original archive/proof are retained as `captured-inputs.pre-review.*`.
Extract the current archive from this directory with `tar -xzf captured-inputs.tar.gz`
to restore receipt-relative input paths. Summary and semantic receipts remain
readable without extraction.

The maintained wrapper uses fresh namespaces, Redis and Dapr infrastructure for
each vector. The complete lane uses the mandatory outer deadline:

```sh
MCPCLI_ISOLATED_RUNTIME_DIR=/tmp/mcpcli-413-runtime-7jz660m_/runtime \
timeout --signal=TERM --kill-after=30s 21600 \
  python3 tools/live-topology/run-vectors.py \
  --output _bmad-output/implementation-artifacts/evidence/story-4-13/live-complete
```

The upstream fix remains in [Parties PR #58](https://github.com/Hexalith/Hexalith.Parties/pull/58).
Its CI repeats the same five baseline failures from main (public Contracts snapshot
and existing source-evidence checks); `ci-baseline-comparison.json` in the upstream
packet lists them and hashes both raw logs. No owner main merge or publication
occurred. The active owner's unrelated staged/working changes were preserved.
