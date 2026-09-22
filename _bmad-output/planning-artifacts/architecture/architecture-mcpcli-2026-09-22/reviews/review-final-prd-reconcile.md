# Final PRD reconciliation review — Hexalith.McpCli architecture spine

Reviewed the current draft `ARCHITECTURE-SPINE.md` against the final `prd.md` and `addendum.md` after the product-owner-approved source amendments on 2026-09-22. This review changes no source document.

## Result

**No critical or high PRD-to-spine contradiction found.** The approved FR-20/SM-4 conformance split, the `unknown_module` public error, and the MCP registration model are now consistent across the three documents. The remaining item below is a medium contract-boundary ambiguity for absent or empty arguments; it does not reopen the approved `unknown_module` behavior.

## Critical and high findings

None.

## Confirmed alignment

| Contract | PRD and addendum | Spine | Verdict |
| --- | --- | --- | --- |
| FR-20/SM-4 parity | `prd.md:396-405,509` requires one approved vector per listed Operation; both out-of-process Heads execute identical inputs against a reset loopback Gateway script and compare canonical discovery, error, and result documents after masking only generated message/correlation identifiers. | AD-16 `ARCHITECTURE-SPINE.md:146-150` specifies the same reset loopback/capture-replay lane, masking boundary, and equal caller-supplied idempotency keys. | Aligned. |
| FR-20/NFR-7 live semantics | `prd.md:398,431,465` requires one blocking live Aspire execution per approved vector, accepted Commands or returned Query documents, and semantic checks; duplicate live Commands are not required for parity. | AD-16 `ARCHITECTURE-SPINE.md:150` runs each vector once against one Aspire topology and asserts acceptance, documents, and semantic effects. | Aligned. |
| Vector completeness and Module ownership | `prd.md:398,404,465` requires versioned, maintainer-approved Module vectors, valid Payload/Envelope, prerequisite calls, and rejection of missing, duplicate, or stale vectors. | AD-16 `ARCHITECTURE-SPINE.md:150` names the same owner, vector contents, and generic runner gate; AD-21 `:176-180` keeps the migration inventory separate. | Aligned. |
| `unknown_module` lookup | FR-9/FR-11 `prd.md:254-261,276-285` define a non-empty missing Module lookup in `list_operations` as `unknown_module` with up to three nearest declared names. Addendum §E `addendum.md:186-203` requires a non-empty argument; §G `:376-392,427-430` fixes required fields, exact requested `module`, suggestion ordering, and example. | AD-3/AD-5 `ARCHITECTURE-SPINE.md:67-72,79-84` use the same lookup condition and error record; the code list at `:192` includes the variant. | Aligned for a non-empty lookup miss. |
| MCP registration | Addendum §B `addendum.md:77-90` now specifies runtime `McpServerTool.Create` plus one filtered `ToolCollection` and built-in list/call dispatch. | AD-12 `ARCHITECTURE-SPINE.md:121-126` binds the same arrangement. | Aligned. |
| Migration inventory | FR-20/FR-21 `prd.md:402-413` require approved inventory-to-Catalog and contract-type checks. | AD-21 `ARCHITECTURE-SPINE.md:176-180` covers Legacy Servers and Frozen CLIs, exact canonical names, `OperationDescriptor.ContractType`, exclusions, and release gating. | Aligned. |

## Medium observation — absent/empty `module` binding has no explicit public error carriage

- **Evidence:** Addendum §E `addendum.md:201-203` says an absent or empty `module` fails Head input binding, while §G `:370-392` is exhaustive for error documents and reserves `unknown_module` for a non-empty lookup miss. PRD FR-11 `prd.md:276-285` says tool failures return structured errors, and FR-14 `:311-324` says a CLI validation failure exits 2 with a structured error. The spine AD-3 `ARCHITECTURE-SPINE.md:72` also delegates absent/empty values to Head input binding, without saying whether the MCP SDK emits a protocol-level invalid-parameters response or a §G error document, or what structured CLI code is used.
- **Impact:** The two Heads can make different choices for absent/empty `module` while each claims to follow the input-binding sentence. This does **not** affect the specified `unknown_module` case, which requires a non-empty name.
- **Recommended clarification:** State explicitly which failures occur before tool invocation and therefore use transport/parser errors, and bind the CLI's exit-2 structured error code for this case. If they must be §G documents, add an exhaustive error variant that can represent a missing argument without an Operation Name.

## Gate scope

The pending Parties Aspire helper, CI source-build seam, central package pins, and decorated Contracts releases are identified as prerequisites in `ARCHITECTURE-SPINE.md:325-329`; they are implementation blockers already surfaced in the spine, not contradictions introduced by the approved PRD edits. This review is document reconciliation only; it does not claim those external prerequisites are complete.

## Closure check — input-binding error carriage

**The medium observation above is closed by the subsequent source edits.** PRD FR-11 `prd.md:284` and FR-14 `:318-324` now distinguish a non-empty unknown Module from absent/empty input and bind CLI exit 2. Addendum §E `addendum.md:201-205` assigns absent/empty `module` to Head binding; §G `:378-399,440-443` defines the exact CLI `invalid_arguments` document (`code`, canonical `argument`, non-empty `message`) and states that MCP input-schema failures return JSON-RPC invalid parameters before tool invocation, outside the tool-document contract. Spine AD-3/AD-5 `ARCHITECTURE-SPINE.md:72,84` and the error-code convention `:192` adopt that split. The non-empty lookup miss still returns `unknown_module` in both Heads. No critical, high, or medium PRD-to-spine contradiction remains from this review.
