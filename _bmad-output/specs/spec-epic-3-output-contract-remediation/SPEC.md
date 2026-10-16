---
id: SPEC-epic-3-output-contract-remediation
epic: 3
finding: F1
action_item: epic-3-retro-item-1-complete-output-contract
created: '2026-10-16'
companions:
  - output-contract.md
  - verification.md
  - ../../planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md
  - ../../planning-artifacts/prds/prd-mcpcli-2026-09-21/addendum.md
  - ../../planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md
sources: []
---

> **Canonical contract.** This SPEC and its companions define what to build and verify. The PRD addendum §G is normative; the companions identify the remediation scope and required evidence.

# Remediate the Epic 3 MCP output contract

## Why

Epic 3 acceptance is rejected because advertised MCP schemas accept documents forbidden by PRD FR-11 and addendum §G. Agents cannot rely on those schemas to detect invalid results. Resolve blocking [F1](../../implementation-artifacts/epic-3-retro-2026-10-16.md#f1--advertised-output-schemas-omit-declared-semantic-constraints) through action `epic-3-retro-item-1-complete-output-contract`, owned by the McpCli maintainer with the architecture owner.

## Capabilities

- **CAP-1**
  - **intent:** Consumers can validate discovery, execution, and error values against the normative advertised output contract.
  - **success:** Every advertised tool schema rejects its applicable independently specified invalid fixtures, including all twelve F1 counterexamples, under both supported protocol revisions; valid boundaries pass the matrix in [output-contract.md](output-contract.md).
- **CAP-2**
  - **intent:** Consumers can distinguish valid availability, envelope, and lint states.
  - **success:** Schemas reject invalid conditional combinations and lint discriminator/property combinations; Core-produced fixtures prove the session and descriptor semantics identified in [output-contract.md](output-contract.md).
- **CAP-3**
  - **intent:** Consumers retain canonical documents and arbitrary embedded JSON across both heads.
  - **success:** CLI and MCP documents agree with Core records, MCP structured and text documents agree, all JSON value types remain valid in `result` and `document`, and omission remains distinct from explicit JSON null.
- **CAP-4**
  - **intent:** Maintainers can reconsider F1 and Epic 3 acceptance from reproducible evidence.
  - **success:** The evidence packet and passing checks in [verification.md](verification.md) identify the final implementation revision, both protocol advertisements, independent fixture outcomes, canonical document parity, and an explicit reassessment against the rejected criteria.

## Constraints

- Core owns the shared result/error contract, semantic rules, serializer, identifiers, and availability. MCP exports and advertises that contract without a second policy implementation or a dependency from Core onto either head.
- Enforce §G types, ranges, nonempty strings, canonical syntax, cardinalities, discriminators, required members, omission, and document-local conditions as specified in [output-contract.md](output-contract.md). Context-dependent membership, Module Identifier Kind, ordering, and descriptor facts remain Core responsibilities with direct evidence.
- Keep generic schemas and the existing fixed tool surface. A generic aggregate identifier admits Gateway-valid String identifiers; it cannot assume all Modules use ULIDs.
- Close canonical document objects while preserving embedded content. `schema` and present `example` have object roots; `result` and required `document` accept any JSON value. Module serialization casing remains intact.
- Validate the actual `tools/list` schemas using the distinct `2025-06-18` and `2026-07-28` flows. Keep names, descriptions, and input schemas under 8,000 characters; measure output schemas separately.
- Use existing centrally pinned dependencies. Require fresh dependency assets, the Release build, project-level regressions, and both conformance lanes in [verification.md](verification.md).

## Non-goals

- F2 call-envelope/case-collision hardening and F3 input guidance or general deferral cleanup, except linking F1 evidence to its existing schema deferral.
- New tools, per-operation tool schemas, module-specific production branches, transports, resources/prompts, plugin loading, identity services, retries, or dependency upgrades.
- Changes to §G, sibling submodules, completed story statuses, or an automatic change to the retrospective verdict or action status.
- New live EventStore or Windows/platform qualification; retain the retrospective's stated limits.

## Success signal

Both advertised protocol contracts reject every required negative fixture and accept the valid boundary and embedded-JSON fixtures. Canonical parity and all required checks pass on the final implementation, and the recorded evidence permits the maintainer and architecture owner to reassess `epic-3-retro-item-1-complete-output-contract` and Epic 3 acceptance without relying on expired temporary files.
