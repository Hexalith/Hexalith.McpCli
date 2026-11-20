# PRD quality review — Hexalith.McpCli

## Overall verdict

The PRD gives maintainers a usable basis for enrollment, migration and release decisions. All 13 prior documentation findings remain closed. This full review found three medium and two low issues, including a discovery result that fails its own published schema and a README-only acceptance task that still exercises a restricted write. [PRD](prd.md) · [Addendum](addendum.md) · [Previous closure review](review-validation-followup-2026-11-20.md)

## Decision-readiness — strong

Sections 7 and 8 distinguish the shipped 2.0.1 pair from the evidence needed for each candidate. FR-21 and OQ-1 identify who must resolve disputed Parties operations and hosted identity, and what proof each decision requires. The failed hosted build, missing delivery work and outstanding retirements remain explicit.

## Substance over theater — strong

The journeys lead to observable catalog, execution and read-only behavior. NFR-1 measures the first catalog build against a named cohort and inclusive threshold. SM-4 compares both Heads' requests and results while reserving live submissions for semantic evidence.

## Strategic coherence — adequate

The original brief's one-catalog objective carries through both Heads, the no-new-server rule and the four-module success target. The remaining issue is how the operator metric can be demonstrated under the adopted policy.

- **Medium — SM-6 directs the operator to a restricted write.** PRD §9 line 554 requires a successful `send_command` within 15 minutes “using only the README.” The current README lines 243 and 443–455 time and prescribe `parties.create-party`. That is the T04 row that FR-21 and AD-23 K12 place under owner reconciliation. Environment permission to create a synthetic Party supplies no decision on public-agent eligibility. Specify an already eligible, environment-authorized command and fixture in the README/checklist, or explicitly defer this measurement until the T04 decision. Preserve the historical assisted timing as a separate observation. [README task](../../../../README.md#complete-the-approved-cross-module-task) · [AD-23](../../architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md) · [Historical operator timing](../../../../docs/release/operator-setup-history.md)

## Done-ness clarity — adequate

FR-14, FR-16 and FR-17 specify failure timing, identity and submission counts. One legal Query declaration nevertheless produces an invalid discovery result.

- **Medium — A valid Query example can invalidate the entire description.** PRD §5.1 line 141 and FR-1 line 176 require an example that validates against the Payload Schema. FR-7 line 265 permits a Query's declared root type. Addendum §G line 428 requires a present discovery example to be a JSON object. I compiled a temporary marked Query derived from `List<string>` with a constant aggregate and `Example="[]"`. The normal Catalog accepted it without diagnostics and emitted `example: []`. Validating that complete description against Core's advertised output schema returned false. Apply the approved object-root rule to declared examples in FR-1/FR-6 and exclude a violating declaration with `invalid_example`. A Query with an array Payload can omit its optional example. Cover both cases through discovery. [Approved OC-12](../../../specs/spec-epic-3-output-contract-remediation/output-contract.md#embedded-content-and-canonical-parity) · [Catalog validation](../../../../src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs) · [Published schema](../../../../src/Hexalith.McpCli.Core/Serialization/ResultDocumentSchema.cs)

## Scope honesty — strong

Sections 5.7 and 8 distinguish Projects enrollment from native read qualification, and Folders enrollment from retirement. The approved HTTP design work, K12 reconciliation, withheld release evidence and Story 5.17 implementation have owners or acceptance conditions. Their delivery status remains open.

## Downstream usability — adequate

Stable FR identifiers and explicit result documents support story and client authors. Two argument boundaries still require readers to consult the implementation.

- **Medium — The normative paging row omits input and failure boundaries.** Addendum §E line 234 says “Gateway paging.” It does not tell a client whether it may pass both an offset and a cursor or how to handle an out-of-range integer. The shipped contract accepts page sizes 1–200, offsets 0–2,147,483,647, and cursors up to 4,096 UTF-16 code units. A nonblank cursor conflicts with any supplied offset, including zero. MCP rejects a nonrepresentable Int32 before invocation, while a bound page size of 201 produces a structured validation error at `/pageSize`. State or normatively reference these rules where the author implements the §E row, including the two failure cases. [README query contract, lines 591 and 638](../../../../README.md) · [Core paging validation](../../../../src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs) · [MCP binding](../../../../src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs)
- **Low — Whitespace-only names have the wrong documented failure boundary.** FR-11 and addendum §E lines 238–242 place a “non-empty” unknown module name on the catalog path. A space-only string is nonempty, yet both Heads reject it before lookup. The same rule applies to `operation`. Specify nonblank input, MCP `InvalidParams`, and CLI `invalid_arguments` for whitespace-only names. Preserve the exact spelling of nonblank lookup misses. [MCP binding, lines 67–79](../../../../src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs) · [CLI binding, lines 344–350](../../../../src/Hexalith.McpCli/Cli/CliRunner.cs) · [Protocol fixture](../../../../tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs)

## Shape fit — strong

A capability specification fits a shared CLI and MCP server. The main document carries product and release decisions, and the normative argument and result sections give the two Heads a common contract. The compact journeys explain differences in agent, operator and maintainer behavior.

## Mechanical notes

- **Low — The rendered open-question numbers change their identities.** PRD §10 lines 580–593 calls deletion order item 6 and package identities item 7. GitHub-flavored Markdown renders them as 2 and 6 respectively. A Pandoc GFM render produced one list starting at 1 and another starting at 2, each with consecutively numbered items. Put literal labels such as **OQ-6** in bullets or in a table so the rendered handoff preserves the intended references. [PRD §10](prd.md#10-handoff-and-open-questions)
- All 22 FRs, eight NFRs, three UJs, seven SMs and four counter-metrics have unique, contiguous identifiers within their groups. All eight inline assumptions have index rows. All 13 fenced JSON examples parse, and all relative document link paths in the PRD and addendum exist.
- Rechecking the prior 13 findings confirmed the revised authority model, UJ-1, CLI output and interruption, Query routing, Epic 3 closure, K03 parity, submitted correlation, MCP payload binding, bound argument failures, acknowledgment status dependency, serializer provider, example ULIDs and benchmark boundary. The SM-6 issue concerns the separate timed README task. This review exercised the synthetic Query locally and made no live Gateway, release or retirement qualification claim.
