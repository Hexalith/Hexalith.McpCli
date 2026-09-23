# PRD reconciliation — architecture update 20260923B

Reviewed 2026-09-23 against the current working copies of `ARCHITECTURE-SPINE.md`, `prd.md`, and the normative PRD `addendum.md`. Scope is VAL-20260923B-01 through VAL-20260923B-06 from `VALIDATION-REPORT-2026-09-23-1241.md`; unrelated inherited issues are outside this review.

**Verdict: reconciled. No substantive contradictory instruction introduced or left by this update was found between the spine and the PRD package.**

| Finding | Spine contract | PRD package reconciliation |
| --- | --- | --- |
| VAL-20260923B-01 | AD-7/9 preserve raw values, validate a copy without mapped envelope-owned members, apply ownership checks, fill, and validate the rebuilt Payload before aggregate access. | FR-7 and FR-16 state the same sequence, expressly permit overwritten correlation/idempotency values of any JSON shape, preserve Tenant/Actor disagreement failures, and prevent raw required-member deserialization. Addendum §G repeats the shared sequence. |
| VAL-20260923B-02 | AD-3 resolves exact top-level CLR property names once through Module serialization metadata and rejects invalid references and conflicting serialized ownership; AD-19 consumes the mapping. | PRD §5.1 fixes the same name contract and mapping, including `[JsonPropertyName]`; FR-6 includes `invalid_property_reference`, `conflicting_property_roles`, and the retained `tenant_is_aggregate_id` exception. Addendum §G uses the same cached serialized names and pointers. |
| VAL-20260923B-03 | AD-16 requires upstream audit-filter alignment and discriminating live semantic vectors before Tenants readiness. | FR-20 and §8.1 explicitly require handling the serialized `From`, `To`, and `Category` fields and checking actual filtered records. They do not treat current upstream compatibility as completed work. |
| VAL-20260923B-04 | AD-16/20 require envelope paging, upstream handler migration, and live page-content/continuation evidence. | FR-16 retains envelope-only generic paging; FR-20 and §8.1 require `QueryEnvelope.Paging`, non-default pages, and subsequent-cursor content assertions. Legacy Payload members remain ordinary input and cannot govern generic paging. |
| VAL-20260923B-05 | AD-13 provisionally accepts explicit JSON, ignores valid inherited format, and rejects explicit table/output before startup with stderr-only errors and no file opening. | FR-13 and addendum §E match option precedence, failure ordering, channel behavior, and malformed-setting handling. All retain an explicit assumption requiring confirmation before Story 3.2; this is a permitted pending product choice, not an adopted decision. |
| VAL-20260923B-06 | AD-17 gates paired v1 publication on authoritative upstream merge, a root-declared baseline containing it, and successful byte-identical entry-point synchronization. | FR-22 names the same evidence and rejects an open PR as completion. Both exempt the one-time Abstractions-only bootstrap. |

No source edits are required to close a substantive reconciliation finding. Keep the MCP option proposal pending user confirmation and retain the Tenants and authoritative-instruction prerequisites as actual implementation/release gates.

One minor bookkeeping omission remains: PRD §11 says it indexes every inline assumption but does not yet list the newly added FR-13 MCP output-option assumption. Adding that row would improve the confirmation checklist; it does not change the contract or block this reconciliation.

This was a document reconciliation, not application or live Gateway verification. No source documents, upstream repositories, or application code were changed by this review.
