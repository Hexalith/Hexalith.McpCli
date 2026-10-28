# Final resumed Story 4.14 qualification — 2026-10-28

The user approved the inherited Tenants sibling EventStore source dependency.
The frozen spec now records that exception. The caller selects Builds
`3d7f49a5430294da5bcd437cbdace85c62c42027`, matching the selected catalog
checkout and incorporating the owner documentation and ordering-test fixes.
The reusable `domain-ci.yml` bytes are unchanged from the previous `abc0e1be`
pin. The selected checkout passed all 411 workflow assertions. This run made
no remote operation and does not claim hosted acceptance of the selected pin.

All three review layers completed. The 12 findings are individually triaged in
the spec. Fixes cover independent prerequisite/receipt guards, cancellation
through the real nested vector runner, XML-encoded credentials, simultaneous
vector/smoke diagnostics, reproduction commands and tool-version documentation.
The cancellation regression fails against the original HEAD with a surviving
detached child; the corrected code allows the vector runner's 20-second cleanup
inside a 25-second group grace and retains diagnostics within the outer
30-second cancellation bound. Remaining owned group members are killed after
supervisor exit. XML credentials are sanitized after decoding; unchanged XML
is preserved byte-for-byte.

The broad Python run passed 151 tests. The separate committed-HEAD pin check
also passed after integration: 152 Python tests passed in total. Fresh restore and the Release
warnings-as-errors build passed, as did all six focused .NET projects. Exact
outputs and source fingerprints are retained here. Earlier guard-removal and
pin-drift evidence remains in the parent directory.

Final native preparation and execution passed: 21 semantic vectors and the
independent authenticated smoke, zero live skips/failures, 22 passing XML cases
and 22 owned cleanup receipts. Parent audit confirms 144 semantic phases, 53
single Command submissions with distinct message IDs, 91 Query attempts and
all 1,452 archive files matching their originals. `live-ci.tar.gz` retains the
complete support-safe hook output; `verification.json` records its SHA-256.
Earlier passing native evidence remains in the parent directory.

Hosted acceptance, the pre-existing Dapr port-bind intermittence, and agent
context follow-ups remain outside this local completion and retain their
existing tracking. The unrelated source gitlink edits are preserved; local
native receipts identify the exact source checkouts used. The Builds catalog
integration includes its matching Parties helper version expectations.
