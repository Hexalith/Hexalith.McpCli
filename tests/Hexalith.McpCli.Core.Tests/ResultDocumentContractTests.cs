using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Schema;
using Hexalith.McpCli.Core.Serialization;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Pins the complete public result and error document shapes in PRD §G.</summary>
public sealed class ResultDocumentContractTests
{
    private const string Id = "01J9MZHXT3RKM0VWXRXGSJDATK";

    /// <summary>Discovery arrays and rows have only their declared members.</summary>
    [Fact]
    public void DiscoveryDocumentsHaveExactMembers()
    {
        AssertJson(new ModulesDocument([]), """{"modules":[]}""");
        AssertJson(new OperationsDocument("sample", []), """{"module":"sample","operations":[]}""");
        AssertJson(new ModulesDocument([new ModuleSummary("sample", "Sample module.", 2)]),
            """{"modules":[{"name":"sample","description":"Sample module.","operationCount":2}]}""");
        AssertJson(new OperationsDocument("sample", [new OperationSummary("sample.get", "read", "Get item."),
            new OperationSummary("sample.create", "write", "Create item.")]),
            """{"module":"sample","operations":[{"name":"sample.get","kind":"read","description":"Get item."},{"name":"sample.create","kind":"write","description":"Create item."}]}""");
    }

    /// <summary>Description options, all lint variants, and both unavailability reasons serialize exactly.</summary>
    [Theory]
    [InlineData(null)]
    [InlineData("read_only")]
    [InlineData("configuration_invalid")]
    public void DescriptionIncludesOnlyApplicableOptions(string? reason)
    {
        var findings = new[]
        {
            new LintFinding("missing_property_description", "warning", "Describe it.", "/properties/key~1~0"),
            new LintFinding("unmarked_identifier_like_property", "warning", "Mark it.", "/properties/id"),
            new LintFinding("payload_paging_member", "warning", "Move it.", "/properties/pageSize"),
            new LintFinding("hollow_description", "warning", "Expand it."),
        };
        var description = new OperationDescriptionDocument("sample.get", "read", "Get item.",
            JsonNode.Parse("""{"type":"object","properties":{}}""")!, JsonNode.Parse("{}"),
            new OperationEnvelopeDocument("system", false, false, ["aggregateId", "pageSize"]), findings,
            reason is null, reason);
        string suffix = reason is null ? "" : ",\"reason\":\"" + reason + "\"";
        AssertJson(description, """
            {"name":"sample.get","kind":"read","description":"Get item.","schema":{"type":"object","properties":{}},
             "example":{},"envelope":{"fixedTenant":"system","aggregateIdRequired":false,
             "idempotencyKeyRequired":false,"arguments":["aggregateId","pageSize"]},"lintFindings":[
             {"code":"missing_property_description","severity":"warning","message":"Describe it.","property":"/properties/key~1~0"},
             {"code":"unmarked_identifier_like_property","severity":"warning","message":"Mark it.","property":"/properties/id"},
             {"code":"payload_paging_member","severity":"warning","message":"Move it.","property":"/properties/pageSize"},
             {"code":"hollow_description","severity":"warning","message":"Expand it."}],"submittable":
            """ + (reason is null ? "true" : "false") + suffix + "}");
        AssertJson(new OperationDescriptionDocument("sample.create", "write", "Create item.",
            JsonNode.Parse("""{"type":"object"}""")!, null,
            new OperationEnvelopeDocument(null, true, true, ["tenant", "aggregateId", "idempotencyKey"]),
            [], true, null),
            """{"name":"sample.create","kind":"write","description":"Create item.","schema":{"type":"object"},"envelope":{"aggregateIdRequired":true,"idempotencyKeyRequired":true,"arguments":["tenant","aggregateId","idempotencyKey"]},"lintFindings":[],"submittable":true}""");
    }

    /// <summary>Command result is optional even for explicit JSON null; absent metadata stays absent.</summary>
    [Theory]
    [InlineData("null")]
    [InlineData("true")]
    [InlineData("17")]
    [InlineData("\"text\"")]
    [InlineData("[]")]
    [InlineData("{}")]
    public void CommandResultAcceptsEveryJsonKind(string resultJson)
    {
        JsonElement result = JsonSerializer.Deserialize<JsonElement>(resultJson);
        AssertJson(new CommandResult("sample.create", Id, Id, "acme", "item-1", "accepted", Id, result),
            $$$"""{"operation":"sample.create","messageId":"{{{Id}}}","correlationId":"{{{Id}}}","tenant":"acme","aggregateId":"item-1","status":"accepted","idempotencyKey":"{{{Id}}}","result":{{{resultJson}}}}""");
        AssertJson(new CommandResult("sample.create", Id, Id, "acme", "item-1", "accepted"),
            $$$"""{"operation":"sample.create","messageId":"{{{Id}}}","correlationId":"{{{Id}}}","tenant":"acme","aggregateId":"item-1","status":"accepted"}""");
    }

    /// <summary>Query document is required even when null; paging optionals are independent.</summary>
    [Theory]
    [InlineData("null")]
    [InlineData("false")]
    [InlineData("0")]
    [InlineData("\"text\"")]
    [InlineData("[]")]
    [InlineData("{}")]
    public void QueryDocumentAcceptsEveryJsonKind(string documentJson)
    {
        JsonElement document = JsonSerializer.Deserialize<JsonElement>(documentJson);
        AssertJson(new QueryResult("sample.get", "acme", document),
            $$$"""{"operation":"sample.get","tenant":"acme","document":{{{documentJson}}}}""");
        AssertJson(new QueryResult("sample.get", "acme", document, new QueryPagingDocument(1, 0, "next", 0, false)),
            $$$"""{"operation":"sample.get","tenant":"acme","document":{{{documentJson}}},"paging":{"pageSize":1,"offset":0,"nextCursor":"next","totalCount":0,"hasMore":false}}""");
        AssertJson(new QueryResult("sample.get", "acme", document, new QueryPagingDocument(200)),
            $$$"""{"operation":"sample.get","tenant":"acme","document":{{{documentJson}}},"paging":{"pageSize":200}}""");
    }

    /// <summary>Every stable error code has exactly the required shape and optional members.</summary>
    [Fact]
    public void EveryErrorCodeHasExactEnvelope()
    {
        (OperationError Error, string Expected)[] cases =
        [
            (new("validation_failed", Operation: "sample.get", Violations: [new PayloadViolation("/key~1~0", "Invalid key.")]),
                """{"error":{"code":"validation_failed","operation":"sample.get","violations":[{"path":"/key~1~0","message":"Invalid key."}]}}"""),
            (new("gateway_error", Status: 202, Detail: "Malformed response.", Reason: "invalid-response", Retryable: false,
                ClientAction: "inspect", RetryAfter: "30", CorrelationId: Id),
                $$$"""{"error":{"code":"gateway_error","status":202,"detail":"Malformed response.","reason":"invalid-response","retryable":false,"clientAction":"inspect","retryAfter":"30","correlationId":"{{{Id}}}"}}"""),
            (new("unknown_operation", Operation: "sample.ge", Suggestions: ["sample.get"]),
                """{"error":{"code":"unknown_operation","operation":"sample.ge","suggestions":["sample.get"]}}"""),
            (new("unknown_module", Module: "sampl", Suggestions: []),
                """{"error":{"code":"unknown_module","module":"sampl","suggestions":[]}}"""),
            (new("invalid_arguments", Argument: "payload", Message: "Payload is required."),
                """{"error":{"code":"invalid_arguments","message":"Payload is required.","argument":"payload"}}"""),
            (new("read_only", Message: "Read-only mode."), """{"error":{"code":"read_only","message":"Read-only mode."}}"""),
            (new("catalog_empty", Message: "Empty catalog."), """{"error":{"code":"catalog_empty","message":"Empty catalog."}}"""),
            (new("catalog_invalid", Message: "Invalid catalog."), """{"error":{"code":"catalog_invalid","message":"Invalid catalog."}}"""),
            (new("unsupported_transport", Message: "Unsupported transport."), """{"error":{"code":"unsupported_transport","message":"Unsupported transport."}}"""),
            (new("configuration_invalid", Message: "Invalid configuration."), """{"error":{"code":"configuration_invalid","message":"Invalid configuration."}}"""),
            (new("internal_error", Message: "Operation failed."), """{"error":{"code":"internal_error","message":"Operation failed."}}"""),
        ];
        cases.Length.ShouldBe(11);
        foreach ((OperationError error, string expected) in cases)
        {
            AssertJson(new { error }, expected);
        }

        AssertJson(new { error = new OperationError("gateway_error", Status: 409, Detail: "Conflict.") },
            """{"error":{"code":"gateway_error","status":409,"detail":"Conflict."}}""");
        AssertJson(new { error = new OperationError("unknown_operation", Operation: "sample.x", Suggestions: []) },
            """{"error":{"code":"unknown_operation","operation":"sample.x","suggestions":[]}}""");
    }

    private static void AssertJson(object actual, string expected)
    {
        JsonElement serialized = JsonSerializer.SerializeToElement(actual, McpCliJson.Result);
        using JsonDocument expectedDocument = JsonDocument.Parse(expected);
        JsonElement.DeepEquals(serialized, expectedDocument.RootElement).ShouldBeTrue(serialized.GetRawText());
    }
}
