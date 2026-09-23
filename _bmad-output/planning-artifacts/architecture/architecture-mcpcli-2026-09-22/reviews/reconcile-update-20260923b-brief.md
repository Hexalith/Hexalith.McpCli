# Brief reconciliation — architecture update 20260923B

**Reviewed:** 2026-09-23  
**Verdict:** PASS for brief reconciliation; no new dropped requirement or constraint found in the VAL-20260923B-01..06 update. AD-13's output-option behavior remains an explicitly recorded assumption requiring review before Story 3.2; this report does not adopt it on the user's behalf.

## Scope and authority

Compared the current [architecture spine](../ARCHITECTURE-SPINE.md) with the [brief](../../../briefs/brief-mcpcli-2026-09-21/brief.md) and [brief addendum](../../../briefs/brief-mcpcli-2026-09-21/addendum.md), focusing on the six findings in the [12:41 validation report](../VALIDATION-REPORT-2026-09-23-1241.md). Read the architecture memlog's adopted amendments and the current PRD requirements to distinguish inherited intent from superseded brief wording. No source document was edited.

Repository AGENTS.md and the permitted root-declared Hexalith.AI.Tools baseline were read. The repository has no application solution, build properties, application test projects, root .editorconfig, or root .gitattributes to exercise for this document reconciliation. This is a source comparison, not a runtime verification or independent technology-version review.

## Findings

No actionable brief-reconciliation findings.

| Update | Brief requirement retained | Evidence in the current spine |
| --- | --- | --- |
| B-01: pre-fill validation | Both heads validate and fill one envelope; Tenant is supplied by the envelope and cannot be controlled by Payload. | AD-7 validates ordinary and unknown members in a copy while retaining raw ownership values; AD-9 checks raw Tenant/Actor disagreements and Payload-only idempotency before fill, then validates the complete Payload. The pre-fill exception does not make Tenant caller-owned. |
| B-02: property references | Hybrid discovery supports contract-interface routing and attribute fallbacks without Module-specific implementation. | AD-3 resolves exact CLR references once to serialized members and pointers; AD-19 consumes the shared mapping, and the routing convention retains interface priority. Alias exclusion prevents one role changing another role's envelope or routing value. |
| B-03: audit filters | Discovery and successful execution must represent real Module capability; CLI and MCP must agree. | AD-16 makes Tenants audit-filter compatibility an upstream readiness gate and requires discriminating live vectors that check returned records. AD-1/5/16 retain one Core and deterministic head parity. |
| B-04: paging | A generic tool must execute the declared query correctly without Module branches in this repository. | AD-20 retains envelope paging; AD-16 assigns the migration to Tenants and requires non-default page-size and continuation content checks. The generic runner remains free of Module branches. |
| B-05: MCP output options | Version one is local stdio, with protocol output on stdout and diagnostics on stderr; the CLI remains a thin companion. | AD-12/13 keep protocol output protected and define provisional handling of inherited versus explicit format options. The choice is marked as an assumption, with a review condition; no extra transport, hosting requirement, or new tool surface is added. |
| B-06: authoritative instruction rule | Version one includes a written no-new-per-Module-server rule in Hexalith agent instructions. | AD-17 now requires authoritative upstream merge evidence, an enclosing baseline reference containing that merge, byte-identical local entry points, and the sync check before paired v1 publication. Its bootstrap exemption permits the Decoration Package prerequisite without claiming tool completion. |

## Superseded wording deliberately not reopened

- The brief names four Modules for v1. Adopted PRD FR-20 and AD-15/16 bind v1 to Tenants and Parties; Projects and Folders remain follow-on coverage and SM-1 obligations.
- The brief generates an idempotency key. Adopted PRD policy and AD-8/9 require optional caller-supplied keys only and retain one generated message identifier per Command.
- The brief's general ULID wording is refined by the adopted Module Identifier Kind contract; envelope identifiers remain ULIDs, while Module identifiers follow their declared kind.
- The brief's `serve` terminology is refined to the adopted `hexalith mcp` verb; the one-binary, stdio-first intent remains.
- Historical SDK custom-list-handler advice in the brief addendum is superseded by the adopted restricted ToolCollection plus list-filter design. The five generic tools and read-only filtering remain the product contract.

## Limits and remaining conditions

The Tenants handler migrations, upstream instruction merge, and live test evidence remain future implementation prerequisites; their inclusion in the spine is not evidence that they already exist. The B-05 assumption is visible in the spine and memlog and must remain distinguishable from an adopted product decision. The wider existing open questions and unrelated historical decisions were not reopened.
