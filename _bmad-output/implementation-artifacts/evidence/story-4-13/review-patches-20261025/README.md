# Story 4.13 code-review patch evidence (2026-10-25)

This packet qualifies patches P1–P14 from the code review recorded in the Story
4.13 spec. It preserves earlier evidence and the user-selected root gitlinks.
The approved Contracts, vectors, approvals and companion plans are unchanged.

The changes extract the existing privileged administrator polling into a helper
shared with Manifest.Tests; use the platform's `command:submit` permission;
exercise all missing plan, document-identity, private-entry, timeout and exact
child-selector checks; defer a vector's passing result until writer-bootstrap
validation finishes; print a successful preflight-only summary; and run complete
production Core plan preflight in the existing non-live CI discovery job. The
private-entry table also protects an empty userinfo field, rejected by checking
for absent username/password rather than their truthiness. Documentation now
states the idempotent-step proof, exact ACL routes, test-package version,
companion-plan enrollment and Python 3.11 minimum.

`commands.json` lists exact commands and their recorded output files.
`source-bindings.json` records source hashes and the exact selected checkout
commits, including Parties `559b91c8` and EventStore `6ca1b4cb`.
`preflight.tar.gz` retains the full successful non-live preflight, immutable
approval/vector/plan input copies and complete 21-operation bindings. Its stdout
summary is in `preflight.txt` and it retains `fullLiveAccepted: false`.

Non-live verification:

| Check | Result |
| --- | --- |
| Fresh solution restore; Release warnings-as-errors build | Passed; zero warnings/errors |
| Manifest | 243 passed, zero skips |
| CLI | 479 passed; two existing Windows-only skips |
| Core | 704 passed; three existing skips |
| Abstractions / Analyzers / MCP | 20 / 19 / 58 passed |
| Live-tool Python | 81 passed |
| Conformance Python | 158 passed |
| Exact MTP discovery | 21 Operation-labelled vectors plus one smoke |
| Current EventStore / Tenants / Parties source-server builds | All passed; zero warnings/errors |
| Native-runtime bootstrap | Four hash-verified binaries; fresh task-owned directory |

`mutations.json` proves the new Python cases detect all 24 targeted guard
regressions. `mcpcli-413-mutation-check.py` applies each mutation in memory,
executes its actual focused test and restores the function; it does not edit
production sources. `authority-mutation.json` separately proves P1's actual
new test succeeds against the helper and fails when its predicate is weakened to
`Payload != null`. That script compiles isolated binaries in a disposable
directory, preserving the real sources/build. The full Manifest run also waits
for and asserts the shipped 60-second authority timeout and exact diagnostic.

`audit-live.py` independently rechecks all selected operations, parent/child
bindings, current plan/vector hashes, resolved cursor/time values, retained
static assertions, exact declared phase/Command coverage, message-ID freshness,
writer activation tied to real empty backups and successful owned cleanup.

The fresh full lane `7370f00a1b6b4b4d8a576175a650c257` passes all 21 vectors
with zero failures/skips against those current source-server builds. Its
`live-audit.json` proves 142 phases, exactly 53 single Command submissions with
53 distinct message IDs and 89 Query attempts. `live/` retains all result,
writer-bootstrap, MTP and ownership receipts; `live-inputs.tar.gz` retains their
immutable input copies (extract beside this README with `tar -xzf live-inputs.tar.gz`).
The isolated final independent smoke passes one case with zero skips, both
original 401 checks and successful owned cleanup; its receipts are in `smoke/`.
No live CI tier, publication, reference edit or dependency upgrade was added.

`runtime-diagnostics.tar.gz` retains the exact 44 runtime command stdout/stderr
files, compressed after byte-for-byte readback verification. Extract beside this
README to restore their receipt-relative locations. The immutable RDB backups and
ownership receipts stay directly readable. `retention-audit.json` records archive
and credential-pattern checks; `artifact-index.json` hashes every retained file.
