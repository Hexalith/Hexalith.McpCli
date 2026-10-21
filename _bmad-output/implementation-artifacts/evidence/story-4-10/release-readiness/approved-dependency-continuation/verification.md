# Published Parties 1.5.1 and production enrollment verification

The protected [owner release](https://github.com/Hexalith/Hexalith.Parties/actions/runs/39576141445)
published Parties 1.5.1 from `8c88c27acd5ed3ee2d2f2b6f51f3432d536f2021`.
[Publication evidence](protected-publication/dispatch.json) retains normal
required-reviewer approval, registry/source preflight and the successful
exact-source publication guard. All nine declared packages are public.

[Exact-main CI](stable-main-ci.json) passed 4,931 unit/integration tests and
98 Aspire tests, with six existing runtime qualification skips. The release tree
preserves all 583 approved production source files and all seven source vectors;
[source comparison](merged-main-continuation.json) also records the later test
helper changes and recovery from external dependency-pointer updates. No runtime
source change or release gate was bypassed.

The user approved the nine exact dependency revisions as `jpiquot`, then the
refreshed complete candidate, seven unchanged vectors and release inventory with
[the recorded instruction](refreshed-candidate-approval.json). Historical
pending receipts and prior approvals remain unchanged. The Catalog-only reviewer
found no description gaps. The search Query description documents its 512
UTF-16-unit input limit.

[Published-artifact binding](published-artifact-binding.json) records the
NuGet archive hash, matching source metadata and each mechanical vector copy.
Only `/package/version` changes; all other bytes and assertions are preserved.
[Public-byte verification](published-verification/verification.json) and
[production enrollment verification](enrollment-checks/enrolled/enrolled.json)
both pass strict Catalog discovery, lint, exact name/type inventory coverage,
and complete seven-vector CLI/MCP replay without dependency overrides. All seven
built description documents are byte-identical to those independently reviewed.

Fresh public replay exposed the loopback guard's unsigned-only hash assumption.
[Regression evidence](signed-replay-regression/checks.json) preserves the initial
failed public receipt and the failing signed-hash test. The generic correction
independently binds NuGet restore-content hashes and exact archive bytes;
corrupting either archive, sidecar, metadata, assets or deps hash still fails.
The temporary process fixture also now selects only its synthetic package, so
production enrollment cannot contaminate sample verification. The original
sample-loopback failure and corrected positive/negative process runs are retained.

[Enrollment checks](enrollment-checks/summary.json) pass Release restore/build,
all six projects (**1,339 tests passed, zero failed**), both sample gates,
**89 Python regressions**, and enrolled-package replay. Four existing
Windows-only profile/ACL tests are skipped on this Linux host.
[Actual production discovery](production-discovery/checks.json) checks stdout,
stderr and exit codes for the built CLI's modules, operations and all seven
lint/strict descriptions; all match actual stdio MCP discovery.
[Current matrix audit](matrix-test-audit-current.json) binds every frozen row
to executed passing tests. The agent-instruction copies remain byte-identical.

[Builds PR #126](https://github.com/Hexalith/Hexalith.Builds/pull/126) delivers the
1.5.1 central pin and a fresh byte-bound Parties audit. Other family observations,
sources and direct consumers are unchanged. All focused owning validators and
both full commit messages pass. Its merge must preserve catalog-source ancestor
`4878668412fe8803c3ef232e1775b1dd09f2f857`.

Full Builds CI passed all required checks, including source/Release package
qualification. The normal merge `2744d549270298cfe73679f76b477a7368429006`
preserves the exact tested tree and catalog-source ancestor. McpCli's final
Builds gitlink selects this merged revision; [integration proof](builds-pin/integration.json)
records equivalence to the fully tested proposal. Another fresh restore and
Manifest check verify the final pointer. [Final independent review](final-review/verification.md)
is complete: thirteen findings were corrected, two low findings were rejected
with evidence, and none was deferred. The post-review parent run again passes
Release restore/build, all six projects (1,339 passed, zero failed, four existing
Windows-only skips), both sample gates, all 100 Python regressions and fresh
seven-vector enrolled-package replay without dependency overrides. Approved
artifact, vector and inventory bytes remain unchanged.
Replay and container liveness checks supply no live authorization, domain-effect
or legacy-retirement qualification; C06–C08 and Stories 4.11/4.13 remain downstream.
