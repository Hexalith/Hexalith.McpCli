---
title: Architecture update review — good-spine rubric
date: '2026-09-23'
intent: update-review
reviewer: rubric-walker
verdict: pass-with-follow-up
---

# Good-spine rubric review

**Final verdict:** Pass after the AD-16 vector provenance fix; no open findings from this lens. The initial Medium finding and its closure are retained below. This review does not claim implementation or release readiness.

**Scope:** Current working-tree `ARCHITECTURE-SPINE.md`, PRD `prd.md`, normative `addendum.md`, `epics.md`, the September 23 validation report, and the repository baseline. The spine, requirements, and code were not edited. Technology API and version fit belong to the separate technology reviewer; this rubric makes no fresh currency claim.

## Finding

### RUB-UPD-20260923-01 · Medium · Specify how a vector is bound to the selected Contracts release

**Criterion:** AD-16 must prevent two independent producers and the generic runner from disagreeing on vector compatibility. **Disposition:** Add a bounded requirement to AD-16 and the companion contract before upstream vector approval.

AD-16 now gives McpCli maintainers one versioned, closed vector contract and validator before Tenants or Parties author vectors, and requires the runner to reject stale vectors ([spine:151](../ARCHITECTURE-SPINE.md)). The PRD repeats the pre-authoring gate and stale-vector rejection ([PRD:402–409](../../../prds/prd-mcpcli-2026-09-21/prd.md)); Story 4.11 asks the runner to reject stale or incompatible vectors ([epics:1318–1326](../../../epics.md)). The new rule names **format** versions and canonical Operation Names but does not require the companion contract to define a compatibility identity tied to the *selected decorated Contracts release*. An unchanged Operation Name can survive a contract Payload or routing change. A validator that checks only format version and Catalog membership could accept a vector authored for an older package, while another implementation rejects it by package version or schema fingerprint. Both could plausibly satisfy the current prose.

Require the companion contract to declare one compatibility identity for each vector set or Operation, derived from the exact selected Contracts package version or an equivalent immutable descriptor fingerprint, and require the shared validator to compare it with the built Catalog before approval and before loopback/live execution. The spine need only state this invariant; the companion artifact should own its field layout and migration rule. Story 4.11 can prove a vector from an earlier decorated release is rejected even when its canonical Operation Name is unchanged. This is a release-evidence gap, not a reason to reopen the five completed runtime decisions.

## Five-finding closure check

| Validation gap | Rubric judgment | Current evidence |
| --- | --- | --- |
| Call kind versus descriptor kind | Closed | AD-5 and AD-9 bind mismatch to `validation_failed` at `/operation` before availability and Payload checks; addendum §E and Story 2.7 require the same result for heads and direct Core calls ([spine:85,109](../ARCHITECTURE-SPINE.md); [addendum:209–213](../../../prds/prd-mcpcli-2026-09-21/addendum.md); [epics:705–708](../../../epics.md)). |
| Required envelope members before aggregate getter | Closed | AD-9 validates raw JSON without materialization, fills and revalidates, then invokes AD-19 on the rebuilt Payload. FR-16 and Story 2.8 include omitted required members and conflicting Tenant/Actor cases ([spine:109,169](../ARCHITECTURE-SPINE.md); [PRD:355–359](../../../prds/prd-mcpcli-2026-09-21/prd.md); [epics:745–758](../../../epics.md)). |
| Deterministic MCP list | Closed as an architecture contract; SDK fit is for the technology reviewer | AD-12 names a post-handler `ListToolsFilters` projection from the permitted collection, with fixed order, uniqueness, Read-only omission, and protocol tests. The addendum and Story 3.1 agree ([spine:127,196](../ARCHITECTURE-SPINE.md); [addendum:82–89](../../../prds/prd-mcpcli-2026-09-21/addendum.md); [epics:894–902](../../../epics.md)). |
| Non-null Command Payload root | Closed | AD-7 normalizes only the top-level type to object and rejects null/non-object at `/`; nested nullability remains intact. FR-7/15 and Story 2.8 agree ([spine:97](../ARCHITECTURE-SPINE.md); [PRD:235–241,335–338](../../../prds/prd-mcpcli-2026-09-21/prd.md); [epics:760–763](../../../epics.md)). |
| Shared conformance-vector contract | Mostly closed; Medium detail above | AD-16 assigns McpCli ownership, a closed format, shared validator, pre-authoring approval, and both runner lanes. FR-20 and Stories 4.8–4.11 repeat the gate. The exact release compatibility identity remains unspecified ([spine:151](../ARCHITECTURE-SPINE.md); [PRD:402–409](../../../prds/prd-mcpcli-2026-09-21/prd.md); [epics:1233–1236,1268–1271,1318–1326](../../../epics.md)). |

## Complete rubric walk

| Criterion | Judgment |
| --- | --- |
| Real divergence points at feature altitude | Pass with the AD-16 Medium follow-up. The hexagonal paradigm, dependency rules, shared Catalog/executor, head contracts, and external vector boundary are allocated. |
| Every AD Rule is enforceable and prevents its stated divergence | Pass except the undefined stale-vector identity. The five updated rules give order, error, schema, and gate behavior with matching story checks. |
| Deferred choices cannot let v1 units diverge | Pass. HTTP, typed tools, query extras, trimming, and table presentation have bounded revisit conditions; none is needed to implement the v1 shared call path. |
| Named technology verified-current and fit | Separate technology lens required. Exact pins are recorded in the spine; this review did not rerun SDK or package probes. |
| Ratifies the brownfield codebase | Pass for this lens. The product solution is still a structural seed; no existing McpCli implementation was found to contradict the updated rules. Sibling code and upstream package prerequisites remain distinguished from shipped local code. |
| Covers PRD/addendum capabilities | Pass with the vector follow-up. The capability map covers FR-1–22 and NFR ownership; the five changed contracts match current PRD/addendum and affected story criteria. |
| Honors inherited parent invariants | Not applicable. No parent spine or inherited AD namespace is declared; existing AD-1–AD-21 identifiers remain stable. |
| Every owned dimension decided, deferred, or open | Pass. Boundaries, data and validation, security/settings, local runtime, CI, release, package policy, and future transport are represented; upstream readiness prerequisites remain explicit Open Questions. |

**Gate recommendation:** Accept the five validation repairs at the rubric level. Tighten the vector contract's release compatibility identity before approving Tenants or Parties vectors. Keep technology and adversarial review outcomes separate in the combined gate.

## Closure check — vector freshness

**RUB-UPD-20260923-01 is closed on the revised working tree. Final rubric verdict: pass, with no open Critical, High, Medium, or Low finding from this lens.** This note supersedes the earlier finding and gate recommendation above; those paragraphs remain as the review history.

AD-16 now requires every vector to declare its owning Contracts package ID and exact version. The shared validator compares both values with the flagged restored production package before Module maintainer approval and again before the loopback and live runner lanes; a reused canonical Operation Name under a changed package version is explicitly stale ([spine:151](../ARCHITECTURE-SPINE.md)). FR-20 states the same identity comparison and timing ([PRD:408–409](../../../prds/prd-mcpcli-2026-09-21/prd.md)). Story 4.11 requires a differing package ID/version to fail before vector approval ([epics:1318–1325](../../../epics.md)); Stories 4.8–4.10 retain shared-validator approval gates. This fixes the producer/consumer divergence described above. Field layout remains properly delegated to the single McpCli-owned companion contract.
