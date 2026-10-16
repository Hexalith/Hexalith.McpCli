# Verification and acceptance evidence

## Traceability and implementation boundary

This spec implements [F1 and action 1](../../implementation-artifacts/epic-3-retro-2026-10-16.md#action-items), selector `epic-3-retro-item-1-complete-output-contract` in [sprint status](../../implementation-artifacts/sprint-status.yaml). Binding acceptance criteria are PRD FR-11, addendum §G, architecture AD-5/12, and [Story 3.3](../../planning-artifacts/epics.md#story-33-execute-calls-with-structured-mcp-results). The retrospective remains `rejected` until a subsequent evidence-based reassessment. Creating this spec completes neither the action nor implementation.

| Location | Responsibility in this remediation |
|---|---|
| `src/Hexalith.McpCli.Core/Catalog/` and `Execution/` | Canonical document records, shared semantic contract metadata, availability, lint/argument conditions, and response mapping. |
| `src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs`, `Catalog/CatalogBuilder.cs`, `Catalog/RoutingResolver.cs`, `Execution/OperationExecutor.cs` | Existing authoritative identifier, name, Gateway syntax, and runtime validation rules; reuse rather than shadow them in MCP. |
| `src/Hexalith.McpCli.Mcp/McpOutputSchema.cs` and `McpCliMcpServiceCollectionExtensions.cs` | Export Core-owned rules into closed success/error unions and advertise them through the existing registration. |
| `tests/Hexalith.McpCli.Mcp.Tests/McpOutputSchemaTests.cs`, `McpExecutionTests.cs`, protocol/session helpers | Independent semantic negatives, valid boundaries, actual advertised-schema validation, and complete Core/MCP document comparison. |
| `tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs`, existing CLI contract suites, `tests/fixtures/StdioHost/` | Built-process protocol flows, channel assertions, and CLI/MCP canonical parity using fixture Contracts and a substituted Gateway. |
| Core/Manifest test projects, `tools/conformance-vectors/v1/` | Producer/descriptor invariants, dependency boundary and exact restored closure, packaged CLI/MCP replay parity. |
| `README.md` | Update advertised output-contract claims in the implementation change; verify every new CLI/MCP behavior claim through the built fixture-backed surfaces it covers. |

The existing schema deferral is already tracked at `deferred-work.md:438` (under the Story 3.1 heading). Link its eventual resolution to this spec and passing evidence; append no duplicate or reconfirmation entry. F2/F3 and other existing action items keep their own scope and ownership.

## Required schema and parity evidence

1. Obtain the actual `tools/list` output from the built server for `2025-06-18` using `initialize` and for `2026-07-28` using `server/discover`. Assert negotiated revision and the distinct first-request flow. Preserve each complete output schema and validate it as an executable schema; helper-generated schema fragments alone do not establish advertisement conformance.
2. Add independently authored fixture expectations from addendum §G for OC-1–OC-14. Fixtures identify the tool, rule, full document, expected validity, and offending pointer. Start from valid documents, change one semantic condition at a time, and test relevant fields/variants individually. For shared error branches, run the semantic negatives against every advertised tool schema. Execute the same corpus under both revisions, including read-only/offline advertisements where applicable.
3. Preserve a red-to-green result showing the F1 negatives expose the current defect and the final advertised schemas reject them. Demonstrate that removing each newly added semantic rule makes its corresponding regression fail; fixtures must not derive their expected constraints from the exporter or Core metadata they verify. Existing closure/null/type/discriminator tests remain active.
4. Validate actual successes and errors from each Head against the advertised schemas, and cover every §G error variant with shared-record fixtures, including startup-only and CLI-binding variants. JSON-RPC binding failures remain protocol errors. Cover all five tools in writable sessions, four in read-only sessions, offline descriptions, conditional availability, lint variants, fixed-tenant arguments, and all positive boundaries. A missing accepted example is a verification gap even if all negatives reject.
5. Serialize complete matching fixtures through Core and both Heads. Compare canonical JSON with type-preserving equality (`JsonElement.DeepEquals` or equivalent), including required fields, omitted optional fields, nulls, string casing, and numeric/boolean distinctions. Compare MCP `structuredContent` with parsed `Content[0].Text`, and assert `isError` for errors. Across separate executions mask only generated message/correlation identifiers; preserve supplied IDs, Gateway-canonical IDs, and idempotency keys. Compare captured Gateway requests in loopback as well as result documents.
6. Keep stdout JSON-RPC-only during MCP serving and preserve startup stderr/empty-stdout behavior. For tested CLI error paths assert the entire JSON error document, stdout, stderr, and exit 2; retain `describe --lint` exit 1 and ordinary success exits. Exercise subsequent discovery after a tool error. Use `CliRunner.InvokeAsync` fixture Contracts or the existing process/conformance host: the unenrolled shipped executable returns `catalog_empty`.
7. Record the combined tool-name/description/input-schema character count below 8,000 and output-schema size separately for both revisions. Preserve the fixed ordered names, annotations, read-only command omission, and existing dependency direction. No output-schema size cap is inferred from the input budget.

Use the existing JsonSchema.Net test validator and independently evaluate the captured schema/fixture corpus with the repository-pinned Python `jsonschema==4.26.0`. Store the independent runner or exact reproducible invocation with the fixtures; do not depend on the retrospective's `/tmp` scripts surviving.

## Required execution gates

Run on the final implementation. Record the exact command, exit code, result counts, skipped cases/reasons, and environment or platform limits. Execute test projects individually, not solution-level tests. These gates are requirements for remediation acceptance; spec creation does not claim they have run.

```bash
dotnet restore Hexalith.McpCli.slnx
dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror
dotnet test tests/Hexalith.McpCli.Mcp.Tests --no-build --configuration Release
dotnet test tests/Hexalith.McpCli.Cli.Tests --no-build --configuration Release
dotnet test tests/Hexalith.McpCli.Core.Tests --no-build --configuration Release
dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release
dotnet test tests/Hexalith.McpCli.Abstractions.Tests --no-build --configuration Release
dotnet test tests/Hexalith.McpCli.Analyzers.Tests --no-build --configuration Release
```

Run both existing CI conformance gates for this remediation, even if the implementation changes only schema metadata. Install `tools/conformance-vectors/v1/requirements.txt` in an isolated Python environment and place that environment on `PATH` for the scripts.

```bash
bash tools/conformance-vectors/v1/run-sample-validation.sh Release
bash tools/conformance-vectors/v1/run-sample-loopback.sh
dotnet restore Hexalith.McpCli.slnx
dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release
```

The loopback replaces `obj/` package assets with a temporary cache it deletes; the final restore and Manifest run must use ordinary freshly restored assets. Require zero new dependency-policy violations and no unapproved dependency changes. If a new test project is unavoidable, enroll it in both `Hexalith.McpCli.slnx` and CI's project list. Finish with `git diff --check` and verify every companion/reference path resolves.

A blocked broad gate records its exact failure separately from any focused fallback evidence. Apply the repository's focused-build/direct-xUnit/serialized-build fallback guidance without weakening the required gate. Existing platform-only skips remain explicit limitations; no required semantic fixture may be skipped. Packaged replay with a substituted Gateway proves conformance and parity, not a new live EventStore semantic qualification.

## Durable packet and reconsideration gate

When implementing, place evidence under this spec's `evidence/` directory (or link an equally durable retained CI artifact) and add a concise manifest. Include:

- The exact final implementation revision and working-diff identity, toolchain and dependency versions, protocol request/response captures, complete advertised schemas for both revisions, and input/output size measurements.
- Full independent positive/negative fixtures keyed to OC-1–OC-14 and the original F1 examples; before/after validity results and evidence that each semantic regression detects removal of its guard.
- Canonical Core/CLI/MCP documents and captured replay requests, allowed identifier masks, structured/text equality, availability/lint cases, and channel/exit assertions.
- Final restore/build/test/conformance commands and logs, pass/fail/skip counts, post-loopback restore/Manifest evidence, and ownership/dependency/README checks.
- A reconciliation table mapping each F1 counterexample and binding criterion to its schema rule, named test, and durable result. Reference the existing schema deferral once.

Reconsider Epic 3 only when every F1 counterexample rejects under both advertised revisions, the full semantic matrix passes its positive and negative expectations, Core ownership and open embedded content are preserved, canonical parity holds, and all required gates pass with stated limitations. The McpCli maintainer and architecture owner then record a fresh assessment against FR-11, AD-5/12, and Story 3.3, linking this spec and the evidence packet. Action 1 may be proposed as done only with that evidence; acceptance is not inferred from story completion or passing older tests. Preserve the original rejected retrospective as historical evidence and record any subsequent acceptance decision explicitly through the normal tracking workflow.

F2/F3, real SDK hosted-service fault coverage, Windows/platform verification, and the retained listener-race record remain separately identified. They did not independently cause the Epic 3 rejection; this spec supplies no new verification evidence for them. A narrower §G contract would require an explicit human-approved product/architecture change.
