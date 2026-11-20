# Architecture reviewer gate — 20 November 2026

**Final verdict — pass.** The 23 stable architecture decisions cover both Heads, their shared Core, Contracts enrollment, Gateway execution, local state, migration, testing and release. The revised spine addresses all four review findings. Platform connected-mode qualification, production release authority and the remaining runtime gates require the named owners' evidence. [Architecture spine](../ARCHITECTURE-SPINE.md) · [Platform AD-11](../../../../../references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md#ad-11--one-generic-tool-with-environment-aware-discovery-adopted-amended)

## Findings on the reviewed draft

| Priority | Location | Evidence and correction |
|---|---|---|
| High | AD-3, AD-10, AD-13 and Open Questions | Local `submittable` uses read-only mode and URL presence. Platform AD-11 requires connected execution to use eligibility served by the selected Gateway, matching contract-schema digest and current authorization. The Platform profile binds Gateway, issuer, audience and token to one environment and source. A local discovery result cannot qualify connected execution, including stdio. Name the Platform, McpCli and EventStore owners, require refusal for absent or mismatched metadata and wrong environment/authority, and preserve the Gateway's independent per-call check. |
| Medium | AD-21 migration and census | Platform AD-11 also requires applicable EventStore AD-22 consumer-removal authority. Link this requirement where a cutover removes consumer infrastructure. EventStore ties authorization to the same immutable subject and per-consumer evidence. |
| Low | AD-5 and capability map | Include `ICatalog.ListModules()` with the other two discovery calls. Point SM-4 parity to the reset-loopback conformance runner. Integration.Tests owns the distinct live effects lane. |
| Low | AD-17 | Platform AD-11 defines a run-scoped, never-published source/package-mode tool using Platform's AD-4 Contracts mapping. Identify it separately from the two release tracks so local integration cannot become publication evidence. |

## Good-spine checklist

- **Shared decisions and enforcement.** Core owns admission, routing, serialization, identifiers and execution. AD-12 and AD-13 assign protocol/CLI binding, management selection and early failure carriage. AD-14 distinguishes whole-profile replacement and future private credential rotation. AD-15–21 assign package, inventory, vector, and release proof to named boundaries. These decisions cover FR-1–22 and NFR-1–8. [Capability map](../ARCHITECTURE-SPINE.md#capability--architecture-map)
- **Brownfield and operational fit.** The SDK, toolchain, enrolled packages and MCP, CLI and EventStore dependencies agree with the source and restored policy at `790d2cdb`. Production runs as an operator process. The environment table covers local execution, native test topology, CI and release. Candidate-specific verification, including package hashes, is distinct from released 3.0.0 and current source enrollment. [Dependency policy](../../../../../tools/dependency-policy.json) · [Product CI](../../../../../.github/hexalith-ci.json) · [Release dispatch](../../../../../.github/workflows/release.yml)
- **Deferrals and owner gates.** AD-7 records the implementation gap for declared collection examples, AD-9 records the missing HTTP status boundary, and AD-22 waits for EventStore's tenant canonicalizer. The approved nine-story proposal retains live Projects proof, private credential entry, profile size, the hosted census, process cleanup, and exact-candidate CI. AD-10 gates HTTP on transport admission and identity proof. AD-17 stops stable promotion pending a joint publisher decision. AD-23 retains the restricted Parties decisions and the SM-6 fixture gate. [Approved change proposal](../../../sprint-change-proposal-2026-11-20.md) · [PRD validation](../../../prds/prd-mcpcli-2026-09-21/validation-report.md)
- **Checks.** The deterministic spine lint returned zero findings. AD-1–23 occur once, in order. Relative document link targets resolved. Both immutable AD-23 companion hashes match their approval receipt. This review checked the contract, sources and gates. Deployment, runtime proof and external owner approvals remain separate. [AD-23 approval](../../../../implementation-artifacts/evidence/story-5-2/approval.json)

## Final disposition

| Reviewed finding | Disposition in the revised spine |
|---|---|
| Platform connected-mode authority | Closed. AD-3 requires served eligibility, a matching schema digest, current authorization, per-call reauthorization and same-environment positive and denial proof by Platform, EventStore and McpCli. AD-13 requires single-environment, single-source Gateway, issuer, audience and token binding. |
| Consumer infrastructure removal | Closed. AD-21 requires applicable EventStore AD-22 authority for a cutover that removes consumer infrastructure. |
| Discovery and parity ownership | Closed. AD-5 names all three discovery calls. The SM-4 capability map identifies the reset-loopback conformance runner and the separate live Integration.Tests lane. |
| Run-scoped Platform tool | Closed. AD-17 gives the Platform source/package-mode tool its AD-4 mapping and explicitly excludes that artifact from publication. |

The final deterministic lint returned zero findings. All 23 decision IDs remain present. No rubric findings remain open against the architecture document.
