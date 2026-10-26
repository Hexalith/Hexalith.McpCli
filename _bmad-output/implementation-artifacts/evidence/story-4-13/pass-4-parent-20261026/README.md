# Pass-4 parent qualification before final review corrections

This packet records the first complete parent verification of the twelve accepted
chunk-A review patches. It passes all 21 live vectors with zero failures/skips and
the independent authenticated smoke. The independent audit proves 144 phases,
53 single Command submissions with distinct IDs, real cursor/time bindings,
every original/additional assertion, both Parties paging probes and all 22
private topology cleanups. Every spec matrix row passes.

`commands.json` contains the exact commands, exits and durations. The sibling
`pass-4-tool-patches-20261026/` packet contains the 94 passing tooling tests and
13 detected guard-removal mutations. `source-bindings.json` records these exact
sources and unchanged compiled DLLs. `validation-reuse.json` binds earlier
restore, Release/source builds, six non-live .NET suites, conformance Python tests
and discovery evidence to 427 unchanged sources, 507 unchanged runtime DLLs,
four reference commits and 315 verified historical files. Those unchanged
checks were reused rather than repeated.

`rid-inspection.json` records both Windows EventLog runtime assets at their
expected deps-relative paths; the flattened EventLog DLL matches the neutral
package asset. No current Linux flattened-RID defect was demonstrated.

`live/`, `live-audit.stdout.txt`, `paging-audit.json`, `matrix-audit.json` and
`smoke-audit.json` retain the semantic and cleanup evidence. Original provider
backups and receipts are in `private-runtime-receipts/`. `live-inputs.tar.gz` and
`runtime-diagnostics.tar.gz` contain byte-verified inputs and sanitized logs;
`retention-audit.json` lists archive hashes and members. The archives were read
back before their duplicate unpacked copies were removed. The one-time retention
helper refuses existing archives before modifying anything.

Final build review subsequently found two additional corrections: compare RID
metadata and fail immediately on invalid successful response envelopes. This
packet is preserved as the earlier run; the final patched qualification is in
`../pass-4-final-20261026/`.
