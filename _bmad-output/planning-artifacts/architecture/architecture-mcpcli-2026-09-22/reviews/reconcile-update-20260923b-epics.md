# Epic reconciliation — September 23 architecture update B

Reviewed `epics.md` against the current `ARCHITECTURE-SPINE.md` for VAL-20260923B-01 through VAL-20260923B-06. This is a document reconciliation, not evidence of implemented behavior or completed upstream prerequisites.

**Result: no actionable reconciliation findings.** The changed decisions have corresponding acceptance criteria, and no contradictory earlier wording was found in the affected stories or requirements inventory.

| Finding | Architecture | Acceptance criteria carrying the decision |
| --- | --- | --- |
| VAL-20260923B-01 | AD-7, AD-9 | Story 2.8 explicitly validates a copy without mapped envelope members, preserves ordinary and unknown-member constraints, checks raw ownership, overwrites caller-supplied idempotency/correlation values where permitted, and validates the rebuilt Payload before contract materialization or submission. Fixtures cover raw null and incorrectly typed idempotency fields, invalid correlation, and raw Tenant/Actor disagreements. |
| VAL-20260923B-02 | AD-3, AD-7, AD-19 | Story 1.5 resolves top-level CLR references through `[JsonPropertyName]`, shares the resulting serialized name and escaped pointer across consumers, excludes invalid references, and checks ownership collisions after serialization mapping. Both new diagnostic categories and the retained tenant/aggregate diagnostic are represented. |
| VAL-20260923B-03 | AD-16 | Story 4.8 requires non-default audit filters with discriminating time/category fixtures and asserts actual filtered records. Gateway-ready acceptance remains blocked until the upstream migration and semantic evidence pass. |
| VAL-20260923B-04 | AD-16, AD-20 | Story 4.8 requires exposed paged handlers to consume `QueryEnvelope.Paging`, prevents legacy Payload members from governing generic requests, and tests a non-default page size followed by the returned cursor against actual page contents. Story 2.6 keeps generic paging envelope-only. |
| VAL-20260923B-05 | AD-13 | Story 3.2 preserves the pending operator decision and requires confirmation or revision before implementation. Its provisional criteria match inherited-format handling, explicit JSON acceptance, explicit table/output rejection, deterministic error argument precedence, stderr-only failure, no output-path opening, and rejection before Catalog/transport startup. Story 2.11 scopes output-file success to non-MCP verbs. |
| VAL-20260923B-06 | AD-17 | Story 4.15 requires the authoritative merge, baseline reference containing it, byte-identical local entry points, and successful synchronization evidence; an open PR is insufficient. Story 4.16 carries that evidence into paired-release prerequisites. The Abstractions-only bootstrap remains exempt. |

The early direct-client Tenants spike in Story 2.5 only verifies connectivity and routing; it does not claim the later audit-filter, paging, decorated-package, or Gateway-ready gates have passed. The MCP option assumption and outstanding upstream gates are explicitly retained as prerequisites, so they are not treated as missing reconciliation work.

Validation consisted of reading the changed acceptance criteria and searching the complete epic document for validation order, envelope ownership, property mapping, output options, paging, and instruction-release wording. No application solution or application test projects exist in this repository at review time; no build or runtime test is claimed. No source input was edited.
