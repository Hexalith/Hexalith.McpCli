---
title: 'Close the next ten actionable deferred-work items'
type: 'bugfix'
created: '2026-11-24'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Complete ten still-relevant deferred items in severity order, using ledger order for ties. Track completed items separately from blocked and superseded findings. Each implementation carries its regression coverage and ledger closure in a separate validated commit. Run the full Release build and test suite before directly pushing main.

</frozen-after-approval>

## Implementation Notes

- The initial local and remote main revision was `fab626ebc6c433ee8195ca7013b7aec5f16f0f53`. Release restore and build passed.
- The baseline live preparation stopped at the Dapr runtime version check. The isolated host reported 1.19.1 and the qualified profile requires 1.19.2.
- The first two commits reached origin/main via an external process before the final workspace checks. Subsequent commits were built on the same revision in a detached checkout to hold them for verification.
- Focused checks cover the actual Windows NUL behavior, profile transaction destinations, MCP input contracts on both protocol revisions, Dapr AppHost composition and discovery, dependency policy, package Gateway socket authentication, and native provenance and artifact catalog selection.
- The historical Story 5.11 archived reconciliation suite compares the old approved audit to the live ledger. The mismatch predates this work. The maintained product suite is checked independently.

## Review Triage Log

- **High, patched.** Aspire testing can randomize the sidecar's public endpoint. Readiness now uses actual registered HTTP ports and checks every expected sidecar.
- **Medium, patched.** Internal gRPC ports fall below both the normal Linux ephemeral range and Aspire's executable target-port pool.
- **Medium, patched.** Negative fixture coverage verifies configured port collision and missing sidecar registration.
- **Low, patched.** The topology guide distinguishes Aspire-managed proxied target ports from the fixed internal gRPC listeners.
- **High, patched.** The normal result writer verifies the opened destination identity before truncation. A late conflict has a separate diagnostic that makes no claim about prior Gateway activity.
- **Medium, patched.** First-profile path comparison includes Windows suffix normalization. The tests exercise hard links to the profile, lock and temporary file, plus a post-inspection replacement. Ordinary single-link output outside the profile directory needs no profile-directory enumeration.
- **Medium, patched.** The dependency gate checks evaluated Release item imports as well as literal declarations and the restored graph.
- **Medium, patched.** Both protocol revision tests require the complete argument sets and the README preserves the structured error for an unsupported kind string.
- **Low, coverage limit.** Windows regressions validate NUL through the actual CLI entry point and verify the console names select the native output buffer. An attached-console process is required for end-to-end console writes.
