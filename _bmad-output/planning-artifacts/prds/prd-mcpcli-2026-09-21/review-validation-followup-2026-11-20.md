# Independent review of the 20 November PRD update

All 13 findings in the prior validation are closed in the revised requirements. The hosted transport still needs design and denial evidence, disputed migration rows need owner decisions, and Story 5.17 still needs a response-preserving implementation. Each now has an explicit acceptance condition. [Original findings](validation-report-2026-11-20-before-update.md#findings-by-severity) · [Updated PRD](prd.md) · [Updated addendum](addendum.md)

## Closure by original finding

| # | Original severity | Finding | Status and evidence |
|---|---|---|---|
| 1 | High | Hosted HTTP credential | Closed. PRD §8.2 and OQ-1 require token exchange, approved issuer/audience/client mapping, authenticated actor and effective-origin attestation, and selected-environment denial evidence. Addendum §B identifies the historical Parties handler. [AD-23 K10](../../architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md) |
| 2 | High | Restricted write in UJ-1 | Closed. UJ-1 uses authorized Tenants and Parties reads. FR-21 and SM-2 condition T04 on signed owner reconciliation and retain the direct and chained denial checks for restricted rows. [PRD §§2.3, 5 and 9](prd.md) · [AD-23](../../architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md) |
| 3 | High | CLI exit 2 after acceptance | Closed. FR-14 distinguishes early destination rejection with zero effects from a late write failure after a command or profile change. It specifies the output stream and requires checking state before retry. [CLI execution failure tests](../../../../tests/Hexalith.McpCli.Cli.Tests/ExecutionFailureCommandTests.cs) |
| 4 | High | Query projection selectors | Closed. §5.1 and FR-2 accept `projects.list` with neither selector and accept a projection type alone. An actor selector without a resolved type produces `missing_routing_values`. [PRD §5](prd.md) |
| 5 | Medium | Epic 3 release prerequisite | Closed. §7 dates the output-contract remediation to 8 November and retains candidate-specific package, operator and platform evidence. [Epic 3 remediation evidence](../../../implementation-artifacts/epic-3-retro-2026-10-16.md#f1-remediation-evidence--2026-11-08) |
| 6 | Medium | Migration parity exclusion | Closed. Addendum §F limits the exclusion to generic options and conditional HTTP features. FR-21 still requires applicable handler defaults, filter-before-envelope paging, totals, continuation and invalid-input evidence. [Addendum §F](addendum.md#f-deferred-capabilities) · [AD-23 K03](../../architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md) |
| 7 | Medium | Command correlation | Closed. FR-16, FR-17 and addendum §G retain the submitted correlation even when the Gateway echoes a different valid value. They separately specify the canonical acknowledgment message ID and its omitted/null fallback. [Addendum §G](addendum.md#success-documents) |
| 8 | Medium | MCP payload wire type | Closed. The §E argument row and full `tools/call` frame show a JSON-text string. An outer JSON object fails argument binding, while malformed text inside a bound string returns a tool validation error. [Addendum §E](addendum.md#call-arguments) |
| 9 | Medium | Semantic MCP argument errors | Closed. §G distinguishes a bound `kind` value of `Read` from a wrong JSON type and enumerates the published `invalid_arguments.argument` values. [Result schema](../../../../src/Hexalith.McpCli.Core/Serialization/ResultDocumentSchema.cs) · [Protocol tests](../../../../tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs) |
| 10 | Medium | Status on malformed acknowledgments | Closed in the specification. FR-17 and §G require preserving the actual numeric HTTP response status and submitted correlation at the transport boundary. Story 5.17 identifies the client/adapter dependency and one-submission HTTP 200 and 202 acceptance cases. [PRD FR-17](prd.md) · [Addendum §G error documents](addendum.md#error-documents) |
| 11 | Medium | Serializer provider declaration | Closed. §5.1 defines the provider type, marked-assembly constraint and public static non-indexed `Options` getter. FR-6 specifies assembly exclusion for invalid declarations, throwing getters and null results. [Provider validation](../../../../src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs) |
| 12 | Low | Abbreviated example ULIDs | Closed. The command success and error examples in §G use full canonical ULIDs in identifier fields. [Addendum §G](addendum.md#g-result-and-error-documents) |
| 13 | Low | Startup benchmark | Closed. NFR-1 times the first `CatalogBuilder.Build` in a fresh process after loading all enrolled production assemblies plus one synthetic `Ulid` sample. Exactly 500 ms passes. [Benchmark fixture](../../../../tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs) |

## Rubric judgment on the update

| Dimension | Judgment | Basis |
|---|---|---|
| Decision-readiness | Strong | §8.2 and OQ-1 identify the hosted authority decision, its owner and the evidence required to qualify. |
| Substance over theater | Strong | FR-14 and NFR-1 translate operational claims into observable failure behavior and a bounded benchmark. |
| Strategic coherence | Strong | UJ-1 demonstrates cross-module use with two authorized reads. SM-2 respects the same migration eligibility. |
| Done-ness clarity | Strong | FR-2, FR-17 and FR-21 give positive and negative acceptance cases, including an accepted submission with an unusable acknowledgment. |
| Scope honesty | Strong | §7 and §8 distinguish dated remediation from candidate qualification, pending owner reconciliation and planned HTTP work. |
| Downstream usability | Strong | Addendum §§E–G expose wire types, error ownership and sample documents that a client author can use directly. |
| Shape fit | Strong | The PRD keeps user journeys and release decisions in the main specification and locates the detailed CLI and MCP contracts in the addendum. |
