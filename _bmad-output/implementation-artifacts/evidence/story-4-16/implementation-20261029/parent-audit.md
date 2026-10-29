# Parent implementation audit

The parent read the implementation diff, inspected the final validator/provenance
repairs and their passing controls, and independently recomputed both retained
package hashes. They match `verification.json` and `prepared.json`. The complete
tracked/untracked diff was captured through a separate temporary Git index;
the real index was unchanged. Raw evidence is represented as binary entries in
that audit diff, with its content inspected through the retained receipts/logs.
The temporary capture includes its exact commands and environment overrides.

The two implementation-audit findings are repaired: arbitrary native payloads,
native dependency entries and precompiled/mixed DLLs are rejected; FR-22 checks
the committed root `.gitmodules` declaration and the gitlink's mode/type. The
final 24-test paired lane and three package-validator controls passed. The
strengthened validator also passed against the retained real package pair.

| Approved matrix row | Executed evidence |
| --- | --- |
| Eligible source and releasable commits | Synthetic fresh-pair preparation and complete acceptance tests passed; real version selection, packing and validation passed in explicitly local-only mode. Actual green-main accepted staging is pending. |
| No next release | Temporary local tagged-source selection returned `release: false`, `version: null`; preparation test verified no staged pair. |
| Stale/dirty source or missing/skipped gates/FR-22 | Source, prerequisite and comparator negative tests passed; real dirty-source staging refused before any remote check. |
| Existing staging, malformed/missing/extra packages or changed bytes | Fresh-output, staging/package, source-change, tampering and native-payload refusal tests passed. |
| Isolated CLI/config/MCP installation smoke | Actual Linux install and eight smoke categories passed; all 21 descriptions and 26 raw discovery captures retained. Windows/macOS execution is pending. |
| Missing/failed OS, byte mismatch or required Windows tests skipped | Synthetic comparison controls passed for each required outcome. They are comparison-logic evidence, not Windows/macOS runtime acceptance. |

The ordinary suites passed 1,544 tests with five reported Linux skips. The
sample gates, mandatory subsequent restore/Release build, five enrolled coverage
tests and exact two-module/21-operation production replay passed. The replay's
command receipt records exit 0; its output explicitly confirms both approved
Contracts versions and complete operation coverage.

The Windows execution task remains unchecked. Story and sprint stay in progress;
no accepted-pair receipt exists. Step 3 requires every acceptance criterion to
be satisfied before advancing to workflow review, so that transition has not
been made. Actual Windows/macOS receipts and their raw-byte comparison remain
required. Committing/pushing and dispatching the staging workflow require user
authorization: the implementation step says “No push. No remote ops.”

The earlier read-only GitHub scope deviation remains separately disclosed in
the implementation evidence. The parent audit used local checks only. No
commit, push, publication or workflow dispatch was performed.
