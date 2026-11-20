# Hexalith.McpCli PRD validation

**Grade Fair.** 0 critical · 4 high · 7 medium · 2 low.

Reviewed 2026-11-20T15:25+01:00. [PRD](prd.md) · [Normative addendum](addendum.md) · [Quality rubric](../../../../.agents/skills/bmad-prd/assets/prd-validation-checklist.md)

**Follow-up on 2026-11-20.** The Fair grade below describes the documents before the update. The independent follow-up review records how the PRD and addendum addressed all 13 findings. [Review of the corrections](review-validation-followup-2026-11-20.md)

## Overall verdict

The PRD is usable for sprint planning. The manifest, release history and open qualification work are traceable. Four high-priority corrections are needed before teams use it to implement HTTP identity, approve a public-agent write, infer a command outcome from CLI exit 2, or choose routing fields for a computed query.

The rubric grade is Fair. Thirteen distinct findings remain after consolidating the three reviews. This assessment covers the working-tree PRD and addendum on McpCli commit 6993abfe. The documented CI failure and the pending Projects, Folders and retirement gates are delivery status, separate from the findings below.

## Dimension verdicts

| Dimension | Verdict | Assessment |
|---|---|---|
| Decision-readiness | Adequate | The PRD names owners for final archive acceptance and Projects paging. The release section omits the recorded closure of an earlier prerequisite. |
| Substance over theater | Strong | The profile size boundary, preservation of state on failure and required contents of two populated Projects pages give maintainers observable acceptance criteria. |
| Strategic coherence | Adequate | Both interfaces serve the same catalog and Gateway. The featured cross-module journey depends on a write whose public-agent eligibility remains disputed. |
| Done-ness clarity | Adequate | Parity and live semantic coverage have separate criteria. Several command and error outcomes still admit incompatible acceptance tests. |
| Scope honesty | Strong | The document distinguishes the two original v1 modules, the three enrolled packages, and the remaining qualification and retirement work. |
| Downstream usability | Thin | Stable requirement IDs and field tables aid implementation. The HTTP handoff, query declaration table and portions of the public protocol contract would send implementers in the wrong direction. |
| Shape fit | Strong | The product journeys explain who uses the two interfaces. The addendum gives maintainers a single place to look for field-level contracts. |

## Findings by severity

### Critical (0)

None.

### High (4)

#### The planned HTTP transport would forward the wrong credential

*PRD §8.2, line 526 and addendum §B, lines 90–92 · Downstream usability.*

The addendum directs implementers to reuse the Parties handler, which copies the incoming bearer token. Adopted decision K10 requires token exchange and attestation of the actor and effective origin for a shared HTTP service. The issue concerns the proposed HTTP design. The shipped service uses stdio.

**Correction.** Revise OQ-1 and the transport handoff to require token exchange, issuer and audience checks, attestation, and denial evidence. Identify the Parties handler as historical context. [AD-23-non-gateway-capability-classes.md, line 233](../../../../_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md#L233)

#### The main agent journey uses a write with disputed eligibility

*PRD UJ-1, line 56 and FR-21, line 447 · Strategic coherence.*

UJ-1 treats a successful parties.create-party call as the normal outcome. It is target T04, one of three enrolled Parties commands whose public-agent exposure conflicts with the inventory’s restricted classification. Discovery or a successful test invocation cannot settle that decision.

**Correction.** Use an operation cleared for the intended surface in SM-2, or mark the write scenario as conditional on the Parties and McpCli owners resolving the restriction. Keep the separate authorization and effects checks. [AD-23-non-gateway-capability-classes.md, line 178](../../../../_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md#L178)

#### A CLI command can exit 2 after the Gateway accepts it

*PRD FR-14, lines 338–346 and addendum §E, output setting · Done-ness clarity.*

Two regression tests return exit 2. An unwritable destination detected before submission sends zero requests. A late result-write failure follows one accepted command. Treating either error as evidence that nothing happened can duplicate the write.

**Correction.** Document both outcomes, the success destination selected by --output, and interruption exits separately. Direct callers with an uncertain outcome to check state before considering another submission. [ExecutionFailureCommandTests.cs, line 137](../../../../tests/Hexalith.McpCli.Cli.Tests/ExecutionFailureCommandTests.cs#L137)

#### The projection rule would exclude an enrolled Projects query

*PRD §5.1, lines 147–148 and FR-20, line 430 · Downstream usability.*

The declaration table requires projectionType for a query without IQueryContract. The approved projects.list request has neither projection selector. Enforcing the table could exclude the query or change its Gateway route.

**Correction.** Allow computed queries to omit both selectors. Require a resolved projectionType when projectionActorType is supplied, matching the routing resolver and the approved vector. [list.vector.json, line 22](../../../../tools/conformance-vectors/v1/current/modules/Hexalith.Projects.Contracts/list.vector.json#L22)

### Medium (7)

#### The release summary omits a prerequisite’s completion

*PRD §7, line 475 · Decision-readiness.*

The text says publication after 2.0.1 requires resolution of the Epic 3 output-contract item. The sprint tracker records it as done and the retrospective documents the two-protocol checks.

**Correction.** Date the historical condition and record its satisfaction. Retain the candidate-specific CI, platform, final-archive and operator acceptance requirements. [epic-3-retro-2026-10-16.md, line 137](../../../../_bmad-output/implementation-artifacts/epic-3-retro-2026-10-16.md#L137)

#### The migration parity exclusion is broader than the approved decision

*Addendum §F, lines 318–322 and PRD FR-21, line 446 · Decision-readiness.*

Section F can be read as waiving search, filtering, ordering and freshness during parity checks. K03 still requires proof for approved module-specific behavior, including filtering before paging.

**Correction.** Limit the exclusion to generic query arguments and HTTP features. Preserve the evidence required for each approved replacement’s payload and handler semantics. [AD-23-non-gateway-capability-classes.md, line 127](../../../../_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md#L127)

#### Successful commands return the submitted correlation ID

*PRD FR-16, line 371 and FR-17, line 394 · Done-ness clarity.*

FR-17 attributes both identifiers to the Gateway. The executor returns the resolved submission correlation ID even when the Gateway acknowledges a different one. Clients need to know which trace identifier they can rely on.

**Correction.** State the correlation and message ID rules separately. Cover a deliberately different acknowledgment correlation ID in the example or acceptance criterion. [OperationExecutorTests.cs, line 154](../../../../tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs#L154)

#### The MCP payload row omits its outer wire type

*Addendum §E, lines 203–212 · Downstream usability.*

The operation schema describes the decoded payload. Both execution tools advertise their outer payload argument as a string containing JSON text. A caller sending an object directly fails at protocol binding.

**Correction.** Declare the required string type and show a complete tool call with serialized JSON. Keep CLI file and stdin syntax in the CLI column. [McpToolHandlers.cs, line 49](../../../../src/Hexalith.McpCli.Mcp/McpToolHandlers.cs#L49)

#### A bound MCP value can still fail as a structured tool error

*Addendum §G, lines 465–486 · Downstream usability.*

The addendum assigns invalid_arguments to CLI binding. An MCP argument that passes type binding can still produce a structured invalid_arguments result, for example the unsupported case-sensitive kind value Read. CLI parser argument names can also fall outside the §E table.

**Correction.** Distinguish JSON-RPC binding errors from structured errors after binding. Align the permitted argument names with the public result schema. [McpProtocolTests.cs, line 134](../../../../tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs#L134)

#### The malformed-acknowledgment story lacks a source for HTTP status

*PRD FR-17, line 395 and addendum §G, lines 433–439 and 466 · Done-ness clarity.*

Story 5.17 requires a gateway_error for a malformed ID in a successful response. Its schema requires an integer status, but the success DTO reaching Core carries no HTTP status. “When exposed” leaves the acceptance fixture undefined.

**Correction.** Identify which boundary retains the actual status, or secure a public-contract decision for an unavailable status. The test must still establish one submission and the submitted correlation ID. [OperationExecutor.cs, line 254](../../../../src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs#L254)

#### The serializer provider declaration omits its type and failure mode

*PRD §5.1, line 166 and FR-6, lines 227–247 · Downstream usability.*

The attribute expects a provider Type from the Contracts assembly with a public static JsonSerializerOptions Options getter. Passing a static member as the table suggests does not express that contract. Invalid providers exclude the whole module and produce a specific diagnostic.

**Correction.** Specify the attribute type and getter signature, and add invalid_serializer_options_provider with its module-wide effect to FR-6. [McpCliJson.cs, line 38](../../../../src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs#L38)

### Low (2)

#### Two normative JSON examples use abbreviated ULIDs

*Addendum §G, lines 374, 430 and 514 · Downstream usability.*

The command success and Gateway error examples use 01J9… in four identifier fields. They parse as JSON, but the identifiers fail the canonical ULID grammar. The advertised send_command output schema rejected the sample in the local check.

**Correction.** Use complete synthetic uppercase ULIDs in both examples so they can be reused as schema fixtures. [SchemaDeriver.cs, line 18](../../../../src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs#L18)

#### NFR-1 leaves the benchmark cohort and boundary ambiguous

*PRD NFR-1, line 461 · Done-ness clarity.*

“The v1 Modules” and “under 500 ms” suggest the original pair and a strict inequality. The benchmark exercises the entire enrolled manifest plus its sample, and exactly 500 ms passes.

**Correction.** Specify the full enrolled manifest plus one sample, the first construction measurement, and the inclusive 500 ms boundary. [CatalogPerformanceTests.cs, line 116](../../../../tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs#L116)

## Checks and scope

- All 22 functional requirement IDs are unique. The eight NFRs, seven primary/secondary success metrics, four counter-metrics and eight indexed assumptions were accounted for. Document metadata, proposal paths, ten local links and anchors, and JSON syntax checks passed.
- The dependency policy and the local Release CLI both gave Parties 7, Projects 4 and Tenants 15 operations. Offline stdio discovery returned the five generic tools. Under MCP 2025-11-25, four of the five full success examples passed their advertised output schema. The send_command example failed the ULID constraints. No Gateway execution was needed for these checks.
- This validates the working-tree documents. The offline probe used the available Release binary. The hosted CI result in §0 and the open qualification stories remain separate evidence. Reviewer severities were consolidated by distinct issue and consequence.

## Reviewer files

- [Quality rubric](review-validation-rubric-20261120.md)
- [Public contract](review-validation-contract-20261120.md)
- [Migration and release](review-validation-migration-20261120.md)
