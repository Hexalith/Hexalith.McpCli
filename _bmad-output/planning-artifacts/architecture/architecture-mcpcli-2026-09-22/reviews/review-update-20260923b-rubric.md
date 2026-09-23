# Rubric review — architecture update 20260923B

Reviewed 2026-09-23 against the current `ARCHITECTURE-SPINE.md`, using the good-spine checklist in `.agents/skills/bmad-architecture/references/reviewer-gate.md`. This pass checks the whole spine for context and concentrates substantive findings on VAL-20260923B-01 through VAL-20260923B-06.

**Verdict: pass for this update. No new critical, high, or medium rubric finding requires another architecture decision before finalization.** AD-13's explicit pending assumption and the recorded upstream readiness gates remain implementation prerequisites; this verdict does not claim that they are satisfied.

## Deterministic gate

`uv run .agents/skills/bmad-architecture/scripts/lint_spine.py --workspace _bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22` completed successfully with `ok: true`, `total_findings: 0`, and an empty findings array.

## Rule enforceability

Every AD retains stable identification plus Binds, Prevents, and Rule. The checks below assess semantic enforceability rather than just field presence.

| AD | Assessment |
| --- | --- |
| AD-1 | Core ownership and package restrictions give both heads one validation, execution, and result contract. References and adapter behavior can verify the boundary. |
| AD-2 | The project dependency graph and sole composition project fix permitted direction; AD-15 supplies the closure checks. |
| AD-3 | One immutable Catalog, one property-binding map, excluded invalid declarations, and explicit dispatch/error semantics make the updated ownership rules testable. |
| AD-4 | Flagged references, generated manifest ordering, and assembly-cardinality failure rules prevent a divergent hand-maintained enrollment list. |
| AD-5 | Core argument/result ownership, exhaustive normative result records, and surface/parity fixtures fix both adapter contracts. |
| AD-6 | One frozen serializer policy per Module and a separate result policy prevent head-specific casing or converter choices. |
| AD-7 | Stored Schema, pre-fill copy validation, raw-value retention, and final complete-Payload validation establish one implementable sequence. The updated rule no longer relies on `readOnly` to bypass JSON Schema validation. |
| AD-8 | Explicit marking and Module Identifier Kind define the identifier typing boundary; generated envelope identifiers remain independently constrained. |
| AD-9 | The ordered pipeline defines lookup, kind, availability, pre-fill validation, ownership, filling, final validation, aggregate access, and submission. Tenant/Actor raw ownership and overwritten correlation/idempotency values have distinct, explicit rules. |
| AD-10 | EnvelopeContext, a single client registration seam, and hosting-owned authentication are concrete boundaries with a stated no-handler Core test. |
| AD-11 | One host/container, one settings singleton, one store, and one gateway client establish composition ownership. |
| AD-12 | One filtered tool collection, exact schemas and order, protocol-version tests, and startup channel rules make MCP behavior verifiable. The AD-13 option check is explicitly before Catalog and transport startup. |
| AD-13 | Source precedence and parsed option presence distinguish explicit options from inherited settings. The provisional policy specifies conflict ordering, output channels, exit status, and absence of file side effects. It is testable once confirmed before Story 3.2. |
| AD-14 | Profile ownership and atomic, locked mutation rules define state consistency and confidentiality across platforms. |
| AD-15 | Explicit production roots, locked transitive baseline, source restrictions, and restored-assets checks give the dependency rule a mechanical gate. |
| AD-16 | Module-approved versioned vectors, reset loopback parity, and independent live semantic checks provide distinct evidence. The new Tenants gates require observable filter/page results and identify the upstream owner and readiness boundary. |
| AD-17 | Bootstrap versus paired publication is explicit. The new authoritative-instruction merge and synchronization evidence is a release preflight condition, with an explicit bootstrap exemption. |
| AD-18 | Analyzer packaging and zero runtime dependency requirements are observable in the produced package. |
| AD-19 | Aggregate access consumes the shared property mapping or the final validated contract instance; it cannot reintroduce raw required-member materialization before filling. |
| AD-20 | Gateway paging arguments, validation, and retained legacy Payload-member treatment have a single meaning. AD-16 now prevents unchanged Tenants handlers from being declared ready on status-only evidence. |
| AD-21 | Approved inventory-to-Catalog and contract-type checks independently enforce migration coverage. |

## Good-spine checklist

- **Divergence points and feature altitude:** Catalog/property mapping, Schema, executor, both heads, settings, external Gateway, test evidence, and publication are covered. The B-01/02 changes establish a shared mapping and execution order across the Catalog/Schema/executor seam. B-03/04 and B-06 put external prerequisites at named acceptance gates rather than implying availability.
- **Seed versus invariants:** Named projects and initial file layout remain visibly grouped as structural seed; cross-unit ownership and externally observable behavior remain in ADs. Some ADs are dense, but the added detail resolves the specific independent-builder ambiguities under review. No structural seed item in this update silently overrides an invariant.
- **Deferred scope:** HTTP identity design, richer query arguments, payload paging mappings, and additional tooling remain outside v1 with explicit seams or revisit conditions. Current generic paging cannot be changed by a builder invoking the deferred payload-paging item.
- **Capabilities and inputs:** The capability map continues to cover the PRD's Catalog, execution, adapters, profiles, Module coverage, migration, and policy work. The separate PRD reconciliation found the six changes aligned with normative PRD/addendum language. No parent spine is inherited.
- **Brownfield reality:** This repository has no application implementation yet. The update acknowledges, rather than ratifies, known incompatible Tenants handler behavior and the absent upstream instruction rule. Successful runtime operation is not claimed.
- **Environment and operations:** The deployment view establishes a local framework-dependent tool and an external Gateway, with no hosted v1 infrastructure. CI topology, source-build prerequisite, release ownership, packaging, profile state durability, stdout/stderr discipline, unknown command outcome/no retry, and status lookup deferral are represented. The update leaves no operational dimension newly silent.
- **Technology currency:** The update introduces no new Stack version or technology choice. Current API/source compatibility belongs to the parallel technology reviewer and the existing version evidence; this rubric pass does not independently claim a fresh package-availability verification.

## Remaining conditions, not new findings

AD-13's MCP option behavior still requires the recorded operator/product review before Story 3.2 implementation. The Tenants handler migrations and semantic evidence, authoritative instruction merge, decorated Contracts releases, Parties Aspire helper, and CI/source-build/catalog prerequisites remain outstanding at their existing gates. A finalized architecture document does not satisfy those delivery conditions.

No spine, PRD, source code, or upstream repository was edited by this review. No application test or live Gateway result is claimed.
