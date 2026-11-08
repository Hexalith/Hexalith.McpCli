---
title: 'Complete the advertised output contract'
type: 'bugfix'
created: '2026-11-08'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'aac815ed7423ea1f674a4e47cdfa79a13aaadf3d'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Epic 3 retrospective F1 identified twelve invalid documents accepted by advertised MCP output schemas. This violates PRD addendum §G and blocks releases after 2.0.1 under the approved November 8 proposal.

**Approach:** Complete the shared Core-owned output contract and derive MCP advertisements from it. Independently specified negative fixtures must reject forbidden documents under both supported protocol flows while real results and arbitrary returned JSON remain valid.

## Boundaries & Constraints

**Always:** Core owns document rules; MCP remains an adapter. Preserve closed document objects, omitted optional members, canonical uppercase ULIDs, String-kind aggregates, exact platform/fixed tenant compatibility, and arbitrary `result`/`document` JSON. Keep embedded schema contents open. Owner decisions (2026-11-08): `unknown_operation.operation` preserves the exact nonempty requested name; success names and suggestions remain canonical. Amend §G narrowly to record this exception. Require object roots for embedded `schema`, retaining open contents and nested boolean schemas. Preserve existing user changes.

**Never:** Add dependencies, module-specific production branches, executor retries, new tools, transport features, releases, or unrelated retrospective repairs. Do not silently narrow §G or change retrospective verdicts.

## I/O & Edge-Case Matrix

| Scenario | Input / state | Expected behavior |
|---|---|---|
| Numbers | Page size zero; negative counts/offset | Schema rejects; positive page size and zero counts/offset pass |
| Strings and identity | Empty required text; noncanonical ULID; malformed canonical names | Schema rejects; valid tenant/platform scope and String-kind aggregate pass |
| Cardinality | Empty violations; four suggestions | Schema rejects; one violation and zero through three suggestions pass |
| Availability | Unavailable without reason; invalid reason | Schema rejects; Core-produced available/read-only/offline descriptions pass |
| Lint | Unknown code/severity; property finding without valid pointer | Schema rejects; four warning codes and escaped property pointers pass |
| Envelope | Duplicate/inapplicable arguments; fixed tenant plus platform scope | Schema rejects; applicable scope-specific argument lists pass |
| Embedded JSON | Nested schema/example objects; returned scalar/array/object/null | Retain each member's declared root type and arbitrary permitted contents |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Mcp/McpOutputSchema.cs` — existing exporter and success/error union; move contract responsibility into Core and retain a thin adapter.
- `src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs` — canonical result serializer; reuse without changing payload options.
- `src/Hexalith.McpCli.Core/Catalog/{CatalogBuilder,RoutingResolver,CatalogService,ExecutionAvailability,DescriptionLinter}.cs` — existing name/routing, suggestions, availability, and lint rules.
- `src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs` — canonical ULID pattern and payload export; preserve module behavior.
- `tests/Hexalith.McpCli.Mcp.Tests/McpOutputSchemaTests.cs` — actual advertisements, both protocol flows, closure/nullability checks, arbitrary JSON fixtures.
- `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/addendum.md` §G and architecture AD-5/12 — authority; change normative wording only with recorded owner approval.

## Tasks & Acceptance

**Execution:**
- [x] `src/Hexalith.McpCli.Core/Serialization/ResultDocumentSchema.cs` — centralize output-schema construction and semantic constraints using existing Core rules; constrain by owning record and error branch rather than global member names.
- [x] `src/Hexalith.McpCli.Mcp/McpOutputSchema.cs` — delegate to Core's contract export.
- [x] `tests/Hexalith.McpCli.Mcp.Tests/McpOutputSchemaTests.cs` — add independent negative and accepted-boundary fixtures for every matrix row against real advertisements under both protocol revisions; preserve structured/text equality checks.
- [x] `tests/Hexalith.McpCli.Core.Tests/ResultDocumentSchemaTests.cs` — protect Core export independently of MCP, including canonical identity and error branch distinctions.
- [x] `README.md` and §G — describe the completed advertised constraints and implement only explicitly approved contract clarifications. Preserve existing lookup and input-binding behavior.
- [x] `_bmad-output/implementation-artifacts/epic-3-retro-2026-10-16.md` and `sprint-status.yaml` — append verified F1 remediation evidence and mark only this action done after acceptance; preserve existing edits and verdicts.

**Acceptance Criteria:**
- Given each retrospective F1 counterexample, when evaluated against its actual advertised schema under either protocol revision, then it fails for the intended semantic rule.
- Given valid discovery, execution, and error results, when evaluated against their advertisements, then they pass and structured/text documents remain equal.
- Given the shared contract, when MCP constructs its advertisements, then constraints come from Core and no dependency or module-specific production logic is added.

## Implementation Notes

- Implemented Core-owned export and thin MCP delegation; no dependency, executor, or payload-serializer changes. Owner-approved §G wording preserves exact unknown-name echoes and object schema roots.
- Verification receipts: `evidence/epic-3-retro-item-1/verification-summary.json`. Release build passed without warnings; Core 792 passed/four expected skips; MCP 94 passed; CLI 489 passed/two Windows skips; fresh Manifest 362 passed. Sample validation and complete loopback passed. All 21 production descriptions/examples passed actual advertisement validation offline; native JavaScript accepted/rejected the exported patterns correctly.
- Matrix audit: `SemanticContractFixturesValidateAgainstAdvertisementsAsync` covers all seven rows under both protocol revisions; `ReturnedValuesAndOptionalMembersValidateAsync` additionally protects arbitrary returned JSON; `GatewayAndAvailabilityErrorsValidateAsync` checks actual unavailable descriptions. Core's 40 focused cases passed independently. Every covering test ran in the full passing MCP/Core suites.
- Compared all four pre-existing changed files with task-start byte snapshots before the targeted action-status edit. Only this action changes from open to done; existing planning changes and retrospective verdicts are preserved. No staging, commit, or remote operation performed.

- Final review follow-ups: constrained invalid argument names, added routing/length/endpoint negatives and differential checks, corrected the embedded example, and made preserved evidence probes portable with shared sanitization and source/binary hashes. Focused Core contract cases increased to 101, all passing; both-protocol schema cases passed.
- Final parent acceptance passed after all fixes: Abstractions 20, Analyzers 19, Core 853/four skips, Manifest 362, CLI 489/two skips, MCP 94; total 1,837 passed and six expected skips. Release build had zero warnings/errors. Both sample gates passed again; final loopback took 552.04 seconds. Actual production discovery and native JavaScript checks passed again.
- All 13 review findings are triaged below; every patch is verified and nothing is deferred. Local completion commit is required by workflow step 5; pinned commitlint validation passed before staging task-owned changes. Pre-existing planning edits are excluded, including all pre-existing sprint-status hunks.

## Spec Change Log

## Review Triage Log

| Finding | Verdict / route | Evidence and disposition |
|---|---|---|
| Blind 1: command aggregateIdRequired | low / reject | CatalogBuilder currently emits false for commands; §G declares this member boolean without a write-specific constraint. No forbidden emitted document was shown. Adding another conditional solely to describe the current output subset is unnecessary. |
| Blind 2: invalid argument names | medium / patch | §G requires a canonical argument name, but the new branch accepts arbitrary text. Constrain it to actual emitted call/session/binding names without changing CLI binding behavior. |
| Blind 3: numeric upper bounds | false / reject | §G explicitly requires positive/nonnegative integers and supplies no upper limit. Accepting a mathematical integer beyond current CLR storage is not a violation of that advertised constraint; no runtime overflow is introduced. |
| Blind 4: mirrored grammars | low / patch | Current patterns match Core validators, so no current behavioral divergence was found. Add differential boundary assertions against existing routing predicates to catch future drift; a shared-definition refactor is unnecessary. |
| Blind 5: embedded example fixture | low / patch | The synthetic example supplies a property whose nested schema is false. Keep the open-content assertion while making that example consistent with its embedded schema. Actual CatalogBuilder independently rejects invalid examples. |
| Blind 6: grammar boundaries | medium / patch | Current fixtures lack tenant/aggregate length and endpoint rejection cases. Add accepted/rejected boundaries to protect the new limits. |
| Blind 7: evidence sanitization | medium / patch | New recorder/probes write raw diagnostic channels while MR11 requires shared redaction for public evidence. Reuse the existing sanitizer and audit the retained packet; no new general redaction framework. |
| Blind 8: recorder checkout path | low / patch | The recorder hardcodes the original absolute checkout. Derive its root and output folder from its own path so the preserved probe can be rerun elsewhere. |
| Blind 9: evidence fingerprints | low / patch | Receipts record the baseline and temporary probe invocations. Rerun preserved probe sources and record current source/probe/binary hashes to associate evidence with reviewed bytes. |
| Blind 10: probe shutdown timeout | low / reject | The conditional leak requires an unobserved host shutdown hang; both task-owned probes completed normally. Adding timeout/kill branches exceeds a direct correction for this unlikely evidence-only case. |
| Edge 1: production probe shutdown timeout | low / reject | Same conditional outcome as Blind 10 at the production probe. Normal bounded shutdown passed; no running child or product defect was demonstrated. |
| Edge 2: advertisement probe shutdown timeout | low / reject | Same conditional outcome as Blind 10 at the fixture probe. Normal bounded shutdown passed; additional cleanup guards are unnecessary for this task-owned capture script. |
| Verification 1: module/aggregate negative cases | medium / patch | Pre-verified gap: removing the respective pattern applications preserves current tests; the JavaScript receipt reads a frozen artifact. Add uppercase module and malformed aggregate negatives against current advertisements under both protocols and independently in Core. |


Review patch outcomes: all routed patches were applied and passed focused and complete final verification. Invalid argument names are closed; the module/aggregate guards and length/endpoints have current-schema regression coverage; the example validates against its embedded schema; preserved probes are portable, sanitized, rerun from repository paths, and bound to current source/probe/binary hashes. No deferrals were recorded.

## Verification

- Restore the solution and build Release with warnings as errors.
- Run Core, MCP, CLI, and freshly restored Manifest test projects individually; focused xUnit assembly invocations support diagnosis.
- Run sample validation and loopback gates for changed Core validation/schema behavior, restoring the production solution afterward.
- Preserve task-owned command/result evidence and inspect the final diff for unrelated changes.
