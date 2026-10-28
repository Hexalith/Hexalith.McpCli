# Initial Story 4.14 resumed verification — 2026-10-28

The source-dependency exception was subsequently approved. Three review layers completed and their fixes are recorded in the [final qualification](final/README.md); the observations below describe the initial checkpoint, not the final state.

The current CI hooks passed locally: all 21 semantic vectors and the independent
authenticated smoke, zero live skips, 22 passing XML cases and 22 native owned
cleanup receipts. The parent independently checked every receipt with
`require_owned` and compared all 1,452 archived files against their original
bytes. `live-ci.tar.gz` contains the support-safe hook output, not the private
runtime. `verification.json` records the commands, results and archive digest.

The complete Python suite passed 148 tests. Eighteen guard removals and two
workflow-pin drift mutations were detected. The recorded Release build passed
without warnings or errors; the six focused .NET projects passed 1,531 tests,
with five existing non-live skips. Owning Builds workflow tests passed 411
assertions and detected three removed steps. Exact outputs are retained here.

The local fixes add independent guard coverage, report lane-level errors and
only failed Operations, remove an unreachable bundle guard, and require Python
3.11.4 for archive extraction. Source-version documentation records resolved
versions rather than a stale matrix. The Builds wording and ordering-test patch
is retained as `builds.patch`; it is recorded in owning commit
`30455c2fbbc2a93a82fccd4255b7cd3520f20a46`. The caller still pins
`abc0e1be8069d1c7a567515a13bb015adc407536`; this run makes no claim of hosted
qualification for a later revision. No push or remote operation was performed.

Completion remains pending. The inherited Tenants build uses
`HexalithEventStoreFromSource=true`, contrary to the frozen spec's requirement
for published sibling dependencies. A user decision is required before accepting
that exception or enforcing the published-dependency requirement. The required
final Build review has not run. Concurrent gitlink and Manifest-test changes
were preserved and are not attributed to this implementation.
