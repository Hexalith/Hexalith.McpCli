# Committed-range review patches — 2026-10-21

R2–R12 are implemented. The approved Parties Contracts publication, seven vectors, release inventory, historical approvals and agent entry points are unchanged. R13 remains the existing deferred agent-context refresh; no new ledger entry was added.

## Changes

- Candidate verification removes inherited `HexalithContracts` PackageReferences from the copied tool project, preserves stack references, and pins its selected package with central `Remove` then `Include` items. Both attribute and child-element metadata forms are covered.
- New regressions protect module/inventory identity with two actual module assemblies, full accepted-lint structural diagnostics in C# and Python, absence of enrollment dependency overrides, malformed module names and missing approval directories. Every digest/malformed-root subtest now re-seeds its successful child receipt and hash.
- The packaged-process fixture resolves its temporary root and requires no candidate dependency overrides. Its supporting verifier-test root also resolves symlinks, after the first symlinked run exposed that existing read-count test assumption.
- Git fixes LF for hash-bound module files and inventory JSON. README operation names/order match the built CLI; enrollment guidance is consolidated and the verifier synopsis includes `--accepted-lint`.

## Focused verification

[Session observations](focused-session-observations.json) retain the exact focused commands and observed results: Python 105/105; Core Release restore/build with zero warnings/errors; both changed Core test classes 14/14, zero skips; all three newly documented CLI examples pass; both hash-bound path families have `text: set`, `eol: lf`.

[Executed process checks](checks.json) and their stdout/stderr logs retain the full sample loopback run with `TMPDIR` pointing through a directory symlink: 105 Python tests, all three tracked-host CLI/MCP replays, nonempty fixture enrollment, real pending-inventory rejection and deliberate semantic-replay failure checks pass. The solution was freshly restored after that loopback removed its cache. `initial-symlink-*` retains the first failed attempt and successful cleanup restore; that failure was solely the existing unresolved test-fixture read-count assumption and is corrected.

The same current candidate regressions run against an isolated copy of `HEAD`'s original verifier fail all three isolation/pin cases, as expected (`original-verifier-regressions.stderr.txt`). The patched verifier then runs against the real production checkout and a freshly packed sample candidate absent from Builds' central versions. [Its receipt](real-candidate-verification.json) passes strict Catalog, lint, inventory and all vectors; [explicit assertions](real-candidate-assertions.json) pin only the three sample operations and prove no inherited Parties package among 53 restored packages. The temporary sample package/cache and input snapshots were removed after recording this result; this is synthetic evidence, not an enrollment or approval.

[Protected-input hashes](protected-inputs.json) confirm all 15 protected tracked files equal `HEAD`, with no reference changes. No commits, pushes, releases, dependency upgrades or remote Git operations were performed.

## Remaining verification and limits

This is the implementation handoff's focused verification. Parent full-suite verification and independent review remain to run. No upstream Parties code changed. Scripted replay proves transport routing/parity, not live authorization, persistent domain effects or retirement readiness. The symlink case ran on Linux; no macOS or Windows run is claimed.
