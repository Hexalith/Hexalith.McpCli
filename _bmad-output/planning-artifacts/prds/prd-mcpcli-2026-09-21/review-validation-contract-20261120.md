# McpCli public contract review

Reviewed the 20 November 2026 working-tree PRD and its normative addendum against the implementation, protocol tests, current vectors and operator documentation at McpCli commit `6993abfe`. This was a document and source review. The examples received a JSON parse and ULID grammar check. The product test suite was outside this review.

## Verdict

Two high findings affect an enrolled Projects read and the safe interpretation of a failed CLI command. Five medium findings affect client interoperability or module enrollment. One low finding affects the reuse of contract examples as fixtures.

### High · Query declarations reject an enrolled shape on paper

The §5.1 table requires `projectionType` whenever a Query lacks `IQueryContract`. FR-20 explicitly permits a shape with no projection selector. The approved `projects.list` vector expects a Gateway request containing neither selector. Enforcing the table would exclude a supported read or give it the wrong route. Make both selectors optional for computed queries. Require a resolved `projectionType` when an actor selector is supplied. [PRD §5.1 and FR-20](prd.md) (lines 147 and 430). [Routing resolver](../../../../src/Hexalith.McpCli.Core/Catalog/RoutingResolver.cs) (line 55). [Catalog regression test](../../../../tests/Hexalith.McpCli.Core.Tests/CatalogTests.cs) (line 154). [Projects list vector](../../../../tools/conformance-vectors/v1/current/modules/Hexalith.Projects.Contracts/list.vector.json) (line 22).

### High · Exit 2 can follow a successful Command

FR-14 describes exit 2 as “No result document”. Addendum §E lists the output-file option but omits the distinction between failure to open a destination before submission and failure to write the result after Gateway acceptance. Both can produce exit 2 and an `internal_error` on stdout. A script that treats either outcome as permission to retry can duplicate a write. State that predictable preflight failure makes zero Gateway calls, while a late write failure can follow acceptance or a saved profile mutation. On a late failure, inspect state before considering another submission. Also identify the selected file as the success destination when `--output` is active. [FR-14](prd.md) (lines 342–346). [Addendum §E](addendum.md) (line 250). [CLI regression tests](../../../../tests/Hexalith.McpCli.Cli.Tests/ExecutionFailureCommandTests.cs) (lines 137 and 162). [Operator contract](../../../../README.md) (lines 601–605 and 624).

### Medium · Successful Command results use the submitted correlation ID

FR-17 attributes both result IDs to the Gateway. A regression test gives the Gateway a different correlation ID and requires the public result to contain the submitted one. Following FR-17 literally would make it harder for callers to reconcile their request with the outcome. Specify the two sources independently. The result uses the submitted correlation ID, whether supplied or generated. The separate acknowledgment rule governs the message ID. [FR-16 and FR-17](prd.md) (lines 371 and 394). [Executor](../../../../src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs) (lines 251–256). [Distinct-ID regression test](../../../../tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs) (lines 133–156).

### Medium · MCP execution requires JSON text in the payload argument

The §E row says the payload is “validated against the Schema”. It omits the outer wire type. An agent that assigns an object matching the discovered schema directly to `arguments.payload` receives a JSON-RPC invalid-parameters error before any Gateway call. Specify that the outer value is a required string containing JSON text. Show one complete call with a quoted payload, and identify file and stdin shorthand as CLI-only. [Addendum §E](addendum.md) (lines 203–212). [Two-revision binding test](../../../../tests/Hexalith.McpCli.Mcp.Tests/McpExecutionTests.cs) (lines 339–356). [Published syntax](../../../../README.md) (line 636).

### Medium · A bound MCP argument can produce a structured tool error

Addendum §G describes `invalid_arguments` as a CLI binding result and restricts its `argument` to a canonical §E name. In both MCP revisions a valid module and `kind` value of `Read` pass string binding and produce a structured tool error with `isError` and `argument` set to `kind`. A malformed argument type instead fails at protocol binding. The CLI also uses management and parser names such as `transport` and `arguments`, both absent from §E. Clients implementing the stated contract could listen on the wrong error channel or reject valid error documents. Describe the two stages and align the permitted names with the published schema. [Addendum §G](addendum.md) (lines 469 and 483–486). [Protocol test](../../../../tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs) (lines 134–139). [Result schema](../../../../src/Hexalith.McpCli.Core/Serialization/ResultDocumentSchema.cs) (lines 72–79).

### Medium · Story 5.17 needs an observable HTTP status for malformed acknowledgments

The planned rule requires `gateway_error` and says to preserve the actual status “when exposed”. The exhaustive error schema requires an integer status every time. The successful Gateway DTO passed to Core has no status member. A valid JSON receipt carrying a bad message ID can reach this path without a client exception, leaving an implementer with no specified value to emit. Define who retains the actual status, for example by detecting this condition while the client has the HTTP response, or obtain an explicit public contract decision for absent status. A fixture should cover a well-formed response with a noncanonical ID and check the agreed status, submitted correlation and exactly one submission. This concerns the acceptance criteria before implementation. [FR-17](prd.md) (line 395). [Addendum §G](addendum.md) (lines 433–439, 466 and 491–495). [McpCli executor](../../../../src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs) (lines 251–256). [Gateway DTO](../../../../references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Commands/SubmitCommandResponse.cs) (lines 12–15).

### Medium · Module authors need the serializer provider type and failure category

The §5.1 table describes `serializerOptionsProvider` as a static member. The published attribute takes a `Type` from the Contracts assembly. That type must expose a public static `JsonSerializerOptions Options` getter. A provider failing this contract excludes the entire Module and emits `invalid_serializer_options_provider`, a category missing from FR-6. Document the attribute value, required getter, failure scope and category so authors can enroll modules using custom converters and diagnose a rejected package. [PRD §5.1 and FR-6](prd.md) (lines 166 and 227–247). [Published attribute](../../../../src/Hexalith.McpCli.Abstractions/HexalithModuleAttribute.cs) (line 28). [Provider validation](../../../../src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs) (lines 38–77). [Catalog test](../../../../tests/Hexalith.McpCli.Core.Tests/CatalogTests.cs) (lines 18–32).

### Low · Two normative JSON examples contain invalid ULIDs

The §G `send_command` and `gateway_error` examples parse as JSON, but their abbreviated `01J9…` values fail the document’s own canonical ULID grammar. Four example field values are affected. Use complete synthetic ULIDs so readers can copy the examples into schema tests. [Addendum §G](addendum.md) (lines 374, 430 and 514). [Shared ULID grammar](../../../../src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs) (line 18).
