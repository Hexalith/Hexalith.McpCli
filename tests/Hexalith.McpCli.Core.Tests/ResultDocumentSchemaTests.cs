using System.Text.Json;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Json.Schema;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Protects Core's result contract without depending on MCP or its advertisements.</summary>
public sealed class ResultDocumentSchemaTests
{
    /// <summary>Canonical document identities remain distinct from exact echoed lookup inputs and Gateway metadata.</summary>
    [Theory]
    [InlineData("sample.get-item", true)]
    [InlineData("0.1", true)]
    [InlineData("Sample.get-item", false)]
    [InlineData("sample.get--item", false)]
    [InlineData("sample", false)]
    [InlineData("sample.get-item\n", false)]
    [InlineData("", false)]
    public void OperationNamesAreCanonicalByOwningBranch(string name, bool canonical)
    {
        JsonSchema schema = Contract<QueryResult>();
        Validates(schema, new QueryResult(name, "acme", null)).ShouldBe(canonical);
        Validates(schema, new { error = new OperationError("validation_failed", Operation: name,
            Violations: [new("/", "Invalid.")]) }).ShouldBe(canonical);
        Validates(schema, new { error = new OperationError("unknown_operation", Operation: name, Suggestions: []) })
            .ShouldBe(name.Length > 0);
    }

    /// <summary>Only identifier fields require canonical uppercase ULIDs; String-kind aggregates retain Gateway syntax.</summary>
    [Theory]
    [InlineData("01ARZ3NDEKTSV4RRFFQ69G5FAV", true)]
    [InlineData("01arz3ndektsv4rrffq69g5fav", false)]
    [InlineData("81ARZ3NDEKTSV4RRFFQ69G5FAV", false)]
    [InlineData("01ARZ3NDEKTSV4RRFFQ69G5FAO", false)]
    [InlineData("01ARZ3NDEKTSV4RRFFQ69G5FAV\n", false)]
    [InlineData("not-a-ulid", false)]
    public void IdentityRulesDoNotLeakToAggregateOrGatewayReason(string value, bool valid)
    {
        const string id = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
        var command = new CommandResult("sample.create-item", id, id, "acme", "Party_42.v1", "accepted");
        JsonSchema schema = Contract<CommandResult>();
        Validates(schema, command with { MessageId = value }).ShouldBe(valid);
        Validates(schema, command with { CorrelationId = value }).ShouldBe(valid);
        Validates(schema, command with { IdempotencyKey = value }).ShouldBe(valid);
        Validates(schema, new { error = new OperationError("gateway_error", Status: 200, Detail: "Malformed.",
            CorrelationId: value, Reason: "future_gateway_reason") }).ShouldBe(valid);
        Validates(schema, command).ShouldBeTrue();
    }

    /// <summary>Core independently enforces numeric, text, cardinality, pointer, and branch-specific rules.</summary>
    [Theory]
    [MemberData(nameof(DocumentFixtures))]
    public void CompleteDocumentsFollowCoreContract(Type type, string json, bool valid)
    {
        JsonSchema schema = JsonSchema.FromText(ResultDocumentSchema.Create(type).GetRawText());
        schema.Evaluate(JsonDocument.Parse(json).RootElement).IsValid.ShouldBe(valid, json);
    }

    /// <summary>Gets independently authored documents and their expected contract verdict.</summary>
    public static TheoryData<Type, string, bool> DocumentFixtures => new()
    {
        { typeof(ModulesDocument), """{"modules":[{"name":"sample","description":"Items.","operationCount":0}]}""", true },
        { typeof(ModulesDocument), """{"modules":[{"name":"sample","description":"Items.","operationCount":-1}]}""", false },
        { typeof(ModulesDocument), """{"modules":[{"name":"","description":"Items.","operationCount":0}]}""", false },
        { typeof(ModulesDocument), """{"modules":[{"name":"Sample","description":"Items.","operationCount":0}]}""", false },
        { typeof(ModulesDocument), """{"modules":[{"name":"sample","description":"","operationCount":0}]}""", false },
        { typeof(OperationsDocument), """{"module":"sample","operations":[]}""", true },
        { typeof(OperationsDocument), """{"module":"Sample","operations":[]}""", false },
        { typeof(QueryResult), """{"operation":"sample.get-item","tenant":"platform:tenant-admin","document":null,"paging":{"pageSize":1,"offset":0,"totalCount":0,"nextCursor":"next"}}""", true },
        { typeof(QueryResult), """{"operation":"sample.get-item","tenant":"acme","document":null,"paging":{"pageSize":0}}""", false },
        { typeof(QueryResult), """{"operation":"sample.get-item","tenant":"acme","document":null,"paging":{"pageSize":1,"offset":-1}}""", false },
        { typeof(QueryResult), """{"operation":"sample.get-item","tenant":"acme","document":null,"paging":{"pageSize":1,"totalCount":-1}}""", false },
        { typeof(QueryResult), """{"operation":"sample.get-item","tenant":"acme","document":null,"paging":{"pageSize":1,"nextCursor":""}}""", false },
        { typeof(QueryResult), """{"operation":"sample.get-item","tenant":"platform:tenant--admin","document":null}""", false },
        { typeof(QueryResult), """{"operation":"sample.get-item","tenant":"Acme","document":null}""", false },
        { typeof(QueryResult), """{"error":{"code":"validation_failed","operation":"sample.get-item","violations":[]}}""", false },
        { typeof(QueryResult), """{"error":{"code":"validation_failed","operation":"sample.get-item","violations":[{"path":"/a~1b/~0key","message":"Invalid."}]}}""", true },
        { typeof(QueryResult), """{"error":{"code":"validation_failed","operation":"sample.get-item","violations":[{"path":"/a~2b","message":"Invalid."}]}}""", false },
        { typeof(QueryResult), """{"error":{"code":"validation_failed","operation":"sample.get-item","violations":[{"path":"/","message":""}]}}""", false },
        { typeof(QueryResult), """{"error":{"code":"unknown_module","module":"Sample?","suggestions":["sample","items","other","fourth"]}}""", false },
        { typeof(QueryResult), """{"error":{"code":"unknown_module","module":"Sample?","suggestions":["sample","items","other"]}}""", true },
        { typeof(QueryResult), """{"error":{"code":"unknown_module","module":"Sample?","suggestions":["Sample"]}}""", false },
        { typeof(QueryResult), """{"error":{"code":"unknown_operation","operation":"Sample ?","suggestions":["sample.get-item"]}}""", true },
        { typeof(QueryResult), """{"error":{"code":"unknown_operation","operation":"Sample ?","suggestions":["sample.get-item","sample.one","sample.two","sample.three"]}}""", false },
        { typeof(QueryResult), """{"error":{"code":"unknown_operation","operation":"Sample ?","suggestions":["get-item"]}}""", false },
        { typeof(QueryResult), """{"error":{"code":"gateway_error","status":202,"detail":"Malformed.","reason":"future_value","clientAction":"inspect","retryAfter":"tomorrow"}}""", true },
        { typeof(QueryResult), """{"error":{"code":"gateway_error","status":409,"detail":""}}""", false },
        { typeof(QueryResult), """{"error":{"code":"invalid_arguments","argument":"","message":"Invalid."}}""", false },
        { typeof(QueryResult), """{"error":{"code":"read_only","message":""}}""", false },
    };


    /// <summary>Argument errors expose only the existing semantic, management, fallback, and normalized parser names.</summary>
    [Theory]
    [MemberData(nameof(ArgumentNames))]
    public void ArgumentErrorNamesAreClosed(string name, bool valid)
        => Validates(Contract<QueryResult>(), new { error = new OperationError("invalid_arguments", Argument: name, Message: "Invalid.") })
            .ShouldBe(valid, name);

    /// <summary>Gets independently specified accepted and forbidden binding names.</summary>
    public static TheoryData<string, bool> ArgumentNames
    {
        get
        {
            var data = new TheoryData<string, bool>();
            foreach (string name in new[] { "module", "kind", "operation", "payload", "tenant", "aggregateId", "correlationId",
                "idempotencyKey", "extensions", "entityId", "pageSize", "offset", "cursor", "lint", "url", "token", "actor",
                "allowTenantOverride", "profile", "format", "output", "readOnly", "strict", "name", "set", "arguments", "clear", "transport", "extension" })
            {
                data.Add(name, true);
            }

            foreach (string name in new[] { "unknown", "--page-size", "page-size", "Extension", "field", "value", "allowedExtensions", "" })
            {
                data.Add(name, false);
            }

            return data;
        }
    }

    /// <summary>Independent endpoint and length cases also detect drift between advertisements and Core's existing routing predicates.</summary>
    [Theory]
    [MemberData(nameof(RoutingBoundaries))]
    public void RoutingGrammarMatchesCoreAtBoundaries(string value, bool tenant, bool aggregate, bool platform)
    {
        RoutingResolver.IsTenantDomain(value).ShouldBe(tenant);
        RoutingResolver.IsAggregateId(value).ShouldBe(aggregate);
        RoutingResolver.IsPlatformScope(value).ShouldBe(platform);
        Validates(Contract<QueryResult>(), new QueryResult("sample.get-item", value, null))
            .ShouldBe(tenant || platform, value);
        const string id = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
        Validates(Contract<CommandResult>(), new CommandResult("sample.create-item", id, id, "acme", value, "accepted"))
            .ShouldBe(aggregate, value);
    }

    /// <summary>Gets independently specified common syntax and exact Gateway length boundaries.</summary>
    public static TheoryData<string, bool, bool, bool> RoutingBoundaries => new()
    {
        { "", false, false, false },
        { "a", true, true, false },
        { "A", false, true, false },
        { "-a", false, false, false },
        { "a-", false, false, false },
        { "a--b", true, true, false },
        { "a.b", false, true, false },
        { "a_b", false, true, false },
        { "a:b", false, false, false },
        { "a\n", false, false, false },
        { new string('a', 64), true, true, false },
        { new string('a', 65), false, true, false },
        { new string('a', 256), false, true, false },
        { new string('a', 257), false, false, false },
        { "a" + new string('.', 254) + "Z", false, true, false },
        { "." + new string('a', 255), false, false, false },
        { new string('a', 255) + "_", false, false, false },
        { "platform:a", false, false, true },
        { "platform:a--b", false, false, false },
        { "platform:-a", false, false, false },
        { "platform:a-", false, false, false },
        { "platform:a\n", false, false, false },
        { "platform:" + new string('a', 65), false, false, true },
    };

    private static JsonSchema Contract<T>() => JsonSchema.FromText(ResultDocumentSchema.Create(typeof(T)).GetRawText());

    private static bool Validates(JsonSchema schema, object value)
        => schema.Evaluate(JsonSerializer.SerializeToElement(value, McpCliJson.Result)).IsValid;
}
