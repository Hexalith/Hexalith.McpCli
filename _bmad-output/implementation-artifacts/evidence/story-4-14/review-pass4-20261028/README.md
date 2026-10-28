# Story 4.14 pass-4 implementation — 2026-10-28

All eight review patches (P1–P8) are implemented. Parent Build review remains
pending. The frozen intent and original baseline revision are preserved.

The nested cancellation regression now accepts the two qualified supervisor
statuses: uutils returns 124 on external TERM; GNU coreutils propagates the
child's 143. It continues to require exit 143 from the interrupted CI process,
no surviving detached child and retained command diagnostics. Both READMEs name
GNU or uutils coreutils `timeout`.

Checkout-dependent Git stubs and exact assertions now protect each source's
commit, status and capture working directory. Recorded executable, daprd and
bundle hashes are checked against fixture bytes. Lane-level failures must print
the exact generation-specific lane receipt path and retain it in the JSON error.
Documentation distinguishes wrapper prerequisites from hook-only Python
venv/ensurepip support and full Dapr initialization. Tenants' recorded version
is described as a sibling-source stamp. Pin/supervisor comments and the
story-wide captured-evidence whitespace rule are current.

Executed verification:

- Full Python suite: **156 passed**, zero failures/skips, 132.948 seconds,
  using uutils coreutils 0.8.0.
- GNU coreutils 9.7 via a disposable PATH shim: **59 hook/workflow tests passed**,
  zero failures/skips, 96.378 seconds. The real nested cancellation ran under
  each timeout implementation.
- Eight isolated record/diagnostic mutations were detected. Removing the
  status field yields the intended missing-field error; the other seven
  mutations fail assertions. Repository files are never mutated by this harness.
- Selected Builds checkout: **411 workflow assertions passed**.
- Bash syntax, actionlint and full story-range whitespace validation passed.

`verification.json` indexes exact outputs and source fingerprints.
`scope-verification.json` confirms the CI helper AST and effective build XML
are unchanged, with no changes to production, .NET tests, workflows, wrappers,
approved vectors, dependency policy or paired-publication refusal.

All five frozen matrix rows retain executed passing coverage: current full hook
acceptance plus historical native semantics; named prerequisites; source
failures/deadlines; failed/skipped/interrupted/incomplete evidence; and current
owner tests for unchanged no-hook VSTest/MTP behavior.

No fresh live, hosted or .NET execution is claimed. The parent re-audited the
[historical final native/.NET packet](../review-pass2-20261028/final/README.md):
SHA-256 `15bde706b18e14684abf16e5ddd37527d2f3eb273fbcaf426b9f00b7f9097848`,
all 1,452 files matched, all 21 vectors and the independent authenticated smoke
passed, and 22 passing XML cases and owned cleanup receipts were present.
`parent-native-audit.json` records that audit. The historical packet retains the
Release build and 1,531 passing .NET tests with five existing non-live skips.
The source spec already records hosted acceptance of the selected Builds pin.

No reference contents, agent-context entries or deferred-work ledger entries
were changed. Existing Dapr port-bind intermittence and the two deferred
agent-context corrections remain tracked. No Git remote operation or publication
was performed.
