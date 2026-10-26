# Pass-4 chunk-A tooling patches

Baseline: `ffeb071708bd50b9be09d884be238f1348ebbb89` on 2026-10-26. This packet covers the twelve accepted
`tools/live-topology` review findings in Story 4.13. Approved vectors, live plans,
dependency policy and source checkouts are unchanged.

The fixes preserve inventory findings from nonzero adapter exits, reject
case-insensitive package-policy collisions and whitespace-only live identities,
stop malformed CLI responses immediately with phase/Operation diagnostics, and
verify the retained genesis RDB bytes and owned location before lane acceptance.
Regression coverage pins actual CLI cursor/time arguments, real production Core
validation, converged Query receipts, inherited environment removal, RID runtime
bytes, final phase exit codes and invalidation of success before preflight.

## Validation

- `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'`:
  94 tests; before the runtime fixes, 14 failing subcases and two errors reproduced
  the defects ([tests-red.log](tests-red.log)). After the fixes, all 94 pass in
  32.664 seconds ([tests-green.log](tests-green.log)). Expected failure diagnostics
  printed by negative tests appear after the test-run summary; they are fixtures.
- `python3 _bmad-output/implementation-artifacts/evidence/story-4-13/pass-4-tool-patches-20261026/check-mutations.py`:
  all thirteen isolated mutations are detected ([mutations.json](mutations.json)).
  The extra mutation independently removes per-attempt document reset. The script
  modifies only process-local modules or temporary files, leaving checkout source
  untouched. Per-mutation logs retain the detecting assertion/error.
- Exact commands and exit codes: [commands.json](commands.json).
  Tooling, vector and plan hashes: [source-bindings.json](source-bindings.json).

The tests use the existing restored/built production ConformanceHost for real
Core validation and inventory preflight; they require the documented .NET and
Python prerequisites. No topology is launched by these checks. Fresh solution,
source-server and full live qualification are the parent verification step and
are not claimed by this packet.

The possible flattened RID DLL gap remains the existing deferred entry at
`_bmad-output/implementation-artifacts/deferred-work.md:602`; it was not expanded
or duplicated. The new RID test protects the existing deps-relative byte check.
