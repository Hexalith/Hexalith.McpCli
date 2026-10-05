using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Schema;
using NSubstitute;
using Shouldly;
using static Hexalith.McpCli.Core.Tests.QueryTestHarness;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Checks query payload validation, identifier syntax, tenant ownership, and offline availability.</summary>
public sealed class QueryValidationTests
{
    /// <summary>Malformed and duplicate JSON produce one root violation without submission.</summary>
    [Theory]
    [InlineData("{")]
    [InlineData("{\"ItemId\":\"a\",\"ItemId\":\"b\"}")]
    [InlineData("{\"Nested\":{\"nested/~\":1,\"nested/~\":2}}")]
    public async Task InvalidJsonMakesZeroCallsAsync(string payload)
    {
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("lint-fixture.inspect-item", payload), Context(), TestContext.Current.CancellationToken);

        AssertRefusal(outcome, gateway, "/");
        outcome.Error!.Violations!.ShouldHaveSingleItem();
    }

    /// <summary>Missing required members, unknown properties, and wrong serialized casing fail before submission.</summary>
    [Theory]
    [InlineData("missing", "ExternalId", "/")]
    [InlineData("unknown", "Unexpected", "/Unexpected")]
    [InlineData("case", "LowerCamel", "/LowerCamel")]
    public async Task InvalidSchemaMembersMakeZeroCallsAsync(string scenario, string member, string path)
    {
        JsonObject payload = JsonNode.Parse(InspectPayload)!.AsObject();
        payload["lowerCamel"] = "ordinary-value";
        OperationDescriptor descriptor = Provider().Get(strict: false).Catalog.ShouldNotBeNull().Modules
            .Single(module => module.Name == "lint-fixture").Operations.Single(operation => operation.Name == "lint-fixture.inspect-item");
        PayloadValidator.Validate(descriptor.Schema, payload.ToJsonString(), isCommand: false).IsValid.ShouldBeTrue();
        if (scenario == "missing")
        {
            payload.Remove(member);
        }
        else
        {
            if (scenario == "case")
            {
                payload.Remove("lowerCamel");
            }

            payload[member] = "ordinary-value";
        }

        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("lint-fixture.inspect-item", payload.ToJsonString()), Context(), TestContext.Current.CancellationToken);
        AssertRefusal(outcome, gateway, path == "/" ? [path] : ["/", path]);
        outcome.Error!.Violations!.ShouldContain(violation => violation.Message.Contains(member, StringComparison.Ordinal)
            || violation.Path == path && path != "/");
    }

    /// <summary>All nested schema failures retain array, map, and escaped serialized member pointers.</summary>
    [Fact]
    public async Task ReportsEveryNestedSchemaViolationAsync()
    {
        const string payload = """
            {"ItemId":"01ARZ3NDEKTSV4RRFFQ69G5FAV","ExternalId":42,
             "Nested":{"Label":false,"nested/~":7,"page/~size":"bad"},
             "Entries":[{"Count":"bad","MarkedId":"01ARZ3NDEKTSV4RRFFQ69G5FAV"}],
             "EntriesByKey":{"key/~":{"Quantity":false}}}
            """;
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("lint-fixture.inspect-item", payload), Context(), TestContext.Current.CancellationToken);

        AssertRefusal(outcome, gateway, "/", "/ExternalId", "/Nested", "/Nested/Label", "/Nested/nested~1~0",
            "/Nested/page~1~0size", "/Entries", "/Entries/0", "/Entries/0/Count", "/EntriesByKey",
            "/EntriesByKey/key~1~0", "/EntriesByKey/key~1~0/Quantity");
        outcome.Error!.Violations!.Count.ShouldBe(12);
    }

    /// <summary>Payload identifier failures use their declared member paths, not envelope paths or name suffixes.</summary>
    [Theory]
    [InlineData("ItemId", "not-a-ulid", "/ItemId")]
    [InlineData("ItemId", "", "/ItemId")]
    [InlineData("ItemId", " ", "/ItemId")]
    [InlineData("ItemId", "550e8400-e29b-41d4-a716-446655440000", "/ItemId")]
    [InlineData("MarkedId", "not-a-ulid", "/Entries/0/MarkedId")]
    [InlineData("MarkedId", "01arz3ndektsv4rrffq69g5fav", "/Entries/0/MarkedId")]
    public async Task InvalidPayloadIdentifiersMakeZeroCallsAsync(string member, string value, string path)
    {
        JsonNode payload = JsonNode.Parse(InspectPayload)!;
        if (member == "ItemId")
        {
            payload[member] = value;
        }
        else
        {
            payload["Entries"] = new JsonArray(new JsonObject { ["Count"] = 1, ["MarkedId"] = value });
        }

        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("lint-fixture.inspect-item", payload.ToJsonString()), Context(), TestContext.Current.CancellationToken);
        AssertRefusal(outcome, gateway, member == "ItemId" ? ["/", path] : ["/", "/Entries", "/Entries/0", path]);
    }

    /// <summary>Provides invalid syntax and adjacent length boundaries for Gateway envelope identifiers.</summary>
    public static IEnumerable<object?[]> InvalidEnvelopeIdentifiers()
    {
        foreach (string value in new[] { "", " ", "-a", "a-", "a.b", "a_b", "A", "a/b", "a:b", "é", "a\n", new string('a', 65) })
        {
            yield return ["tenant", value];
        }

        foreach (string member in new[] { "aggregateId", "entityId" })
        {
            foreach (string value in new[] { "", " ", "-a", "a-", ".a", "a.", "_a", "a_", "a/b", "a:b", "é", "a\n", new string('a', 257) })
            {
                yield return [member, value];
            }
        }
    }

    /// <summary>String aggregate values and entity values must also satisfy the Gateway grammar.</summary>
    [Theory]
    [MemberData(nameof(InvalidEnvelopeIdentifiers))]
    public async Task InvalidEnvelopeIdentifiersMakeZeroCallsAsync(string member, string value)
    {
        IEventStoreGatewayClient gateway = Gateway();
        RunQueryArguments call = member == "tenant"
            ? new("routing-fixture.get-http2-status", "{}", AggregateId: ItemId)
            : new("string-fixture.list-items", "{}", AggregateId: member == "aggregateId" ? value : null,
                EntityId: member == "entityId" ? value : null);
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(call,
            Context(member == "tenant" ? value : "session-tenant"), TestContext.Current.CancellationToken);
        AssertRefusal(outcome, gateway, "/" + member);
        outcome.Error!.Violations!.ShouldHaveSingleItem();
    }

    /// <summary>Supplies the invalid session tenant values as untrusted per-call tenants, with and without override.</summary>
    public static IEnumerable<object?[]> InvalidPerCallTenants() => InvalidEnvelopeIdentifiers()
        .Where(row => string.Equals(row[0] as string, "tenant", StringComparison.Ordinal))
        .SelectMany(row => new[] { new object?[] { row[1], false }, new object?[] { row[1], true } });

    /// <summary>A per-call tenant used without a session tenant or through override must satisfy the Gateway grammar.</summary>
    [Theory]
    [MemberData(nameof(InvalidPerCallTenants))]
    public async Task InvalidPerCallTenantsMakeZeroCallsAsync(string value, bool overrideSession)
    {
        IEventStoreGatewayClient gateway = Gateway();
        EnvelopeContext context = overrideSession ? new("session-tenant", null, true, new HashSet<string>()) : Context(null);
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("routing-fixture.get-http2-status", "{}", Tenant: value, AggregateId: ItemId), context,
            TestContext.Current.CancellationToken);
        AssertRefusal(outcome, gateway, "/tenant");
        outcome.Error!.Violations!.ShouldHaveSingleItem();
    }

    /// <summary>Supplies the invalid String aggregate values already covered at the envelope boundary.</summary>
    public static IEnumerable<object?[]> InvalidStringAccessorIdentifiers() => InvalidEnvelopeIdentifiers()
        .Where(row => string.Equals(row[0] as string, "aggregateId", StringComparison.Ordinal))
        .Select(row => new object?[] { row[1] });

    /// <summary>Invalid String identifiers extracted from a payload accessor use its mapped payload path.</summary>
    [Theory]
    [MemberData(nameof(InvalidStringAccessorIdentifiers))]
    public async Task InvalidStringPayloadAccessorMakesZeroCallsAsync(string value)
    {
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("string-fixture.lookup", JsonSerializer.Serialize(new { Key = value })), Context(),
            TestContext.Current.CancellationToken);
        AssertRefusal(outcome, gateway, "/Key");
        outcome.Error!.Violations!.ShouldHaveSingleItem();
    }

    /// <summary>An invalid explicit String identifier uses the envelope path even when an accessor exists.</summary>
    [Fact]
    public async Task InvalidExplicitStringIdentifierUsesEnvelopePathAsync()
    {
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("string-fixture.lookup", "{\"Key\":\"bad/id\"}", AggregateId: "bad/id"), Context(),
            TestContext.Current.CancellationToken);
        AssertRefusal(outcome, gateway, "/aggregateId");
        outcome.Error!.Violations!.ShouldHaveSingleItem();
    }

    /// <summary>Explicit identifiers on an accessor-free ULID query reach the envelope validation stage.</summary>
    [Theory]
    [InlineData("")]
    [InlineData(" ")]
    [InlineData("not-a-ulid")]
    [InlineData("550e8400-e29b-41d4-a716-446655440000")]
    [InlineData("01arz3ndektsv4rrffq69g5fav")]
    [InlineData("01ARZ3NDEKTSV4RRFFQ69G5FaV")]
    [InlineData("01ARZ3NDEKTSV4RRFFQ69G5FAO")]
    [InlineData("01ARZ3NDEKTSV4RRFFQ69G5FAI")]
    [InlineData("01ARZ3NDEKTSV4RRFFQ69G5FAL")]
    [InlineData("01ARZ3NDEKTSV4RRFFQ69G5FAU")]
    [InlineData("81ARZ3NDEKTSV4RRFFQ69G5FAV")]
    public async Task InvalidUlidAggregateArgumentsUseEnvelopePathAsync(string value)
    {
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("routing-fixture.get-http2-status", "{}", AggregateId: value), Context(),
            TestContext.Current.CancellationToken);
        AssertRefusal(outcome, gateway, "/aggregateId");
    }

    /// <summary>Minimum and maximum lengths, valid punctuation, and canonical ULIDs are preserved.</summary>
    [Theory]
    [InlineData(1, 1, false)]
    [InlineData(64, 256, false)]
    [InlineData(1, 256, true)]
    public async Task ValidIdentifierBoundariesArePreservedAsync(int tenantLength, int entityLength, bool ulid)
    {
        string tenant = new('a', tenantLength);
        string entity = new('A', entityLength);
        string aggregate = ulid ? ItemId : entityLength == 1 ? "A" : "A._-" + new string('z', entityLength - 5) + "9";
        string operation = ulid ? "routing-fixture.get-http2-status" : "string-fixture.list-items";
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments(operation, "{}", AggregateId: aggregate, EntityId: entity), Context(tenant),
            TestContext.Current.CancellationToken);
        string expectedTenant = ulid ? tenant : "fixed-tenant";
        AssertRequest(gateway, new SubmitQueryRequest(expectedTenant, ulid ? "routing" : "string-fixture", aggregate,
            ulid ? "get-http2-status" : "list-items-wire", ulid ? "routing-items" : "string-items",
            JsonSerializer.SerializeToElement(new { }), entity));
        AssertResult(outcome, $$$"""{"operation":"{{{operation}}}","tenant":"{{{expectedTenant}}}","document":{"items":[]}}""");

        // Exercise the session tenant length even when the String module has a fixed tenant.
        if (!ulid)
        {
            IEventStoreGatewayClient sessionGateway = Gateway();
            OperationOutcome sessionOutcome = await Executor(sessionGateway).ExecuteAsync(
                new RunQueryArguments("routing-fixture.get-http2-status", "{}", AggregateId: ItemId), Context(tenant),
                TestContext.Current.CancellationToken);
            AssertRequest(sessionGateway, new SubmitQueryRequest(tenant, "routing", ItemId, "get-http2-status", "routing-items",
                JsonSerializer.SerializeToElement(new { })));
            AssertResult(sessionOutcome, $$$"""{"operation":"routing-fixture.get-http2-status","tenant":"{{{tenant}}}","document":{"items":[]}}""");
        }
    }

    /// <summary>Tenant digit endpoints and internal hyphens are preserved in exact requests and results.</summary>
    [Theory]
    [InlineData("0")]
    [InlineData("0-a-9")]
    public async Task ValidDigitAndHyphenTenantsArePreservedAsync(string tenant)
    {
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("routing-fixture.get-http2-status", "{}", AggregateId: ItemId), Context(tenant),
            TestContext.Current.CancellationToken);
        AssertRequest(gateway, new SubmitQueryRequest(tenant, "routing", ItemId, "get-http2-status", "routing-items",
            JsonSerializer.SerializeToElement(new { })));
        AssertResult(outcome, $$$"""{"operation":"routing-fixture.get-http2-status","tenant":"{{{tenant}}}","document":{"items":[]}}""");
    }

    /// <summary>Omitted and matching tenants are filled from trusted state without changing ordinary payload members.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task TrustedTenantFillsDeclaredMemberAsync(bool matching)
    {
        JsonNode payload = JsonNode.Parse(InspectPayload)!;
        if (matching)
        {
            payload["Tenant"] = "session-tenant";
        }

        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("lint-fixture.inspect-item", payload.ToJsonString()), Context(), TestContext.Current.CancellationToken);
        payload["Tenant"] = "session-tenant";
        AssertRequest(gateway, new SubmitQueryRequest("session-tenant", "lint-fixture", ItemId, "inspect-item", "lint-items",
            JsonSerializer.SerializeToElement(payload)));
        AssertResult(outcome, """{"operation":"lint-fixture.inspect-item","tenant":"session-tenant","document":{"items":[]}}""");
    }

    /// <summary>Conflicting and non-string raw tenants fail ownership before they can be replaced.</summary>
    [Theory]
    [InlineData("\"other-tenant\"")]
    [InlineData("null")]
    [InlineData("42")]
    [InlineData("false")]
    [InlineData("{}")]
    [InlineData("[]")]
    public async Task CallerCannotSupplyUntrustedTenantAsync(string value)
    {
        JsonNode payload = JsonNode.Parse(InspectPayload)!;
        payload["Tenant"] = JsonNode.Parse(value);
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("lint-fixture.inspect-item", payload.ToJsonString()), Context(), TestContext.Current.CancellationToken);
        AssertRefusal(outcome, gateway, "/Tenant");
        outcome.Error!.Violations!.ShouldHaveSingleItem();
    }

    /// <summary>A valid prefill cannot bypass the stricter schema after the trusted tenant is inserted.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task FilledTenantIsValidatedAgainAsync(bool matchingTenant)
    {
        var assembly = new QueryValidationContractsAssembly();
        CatalogSnapshot catalog = Provider(assembly).Get(strict: true).Catalog.ShouldNotBeNull();
        catalog.Diagnostics.ShouldBeEmpty();
        OperationDescriptor operation = catalog.Modules.ShouldHaveSingleItem().Operations.ShouldHaveSingleItem();
        JsonNode payload = JsonNode.Parse($$"""{"ItemId":"{{ItemId}}"}""")!;
        PayloadValidator.Validate(operation.Schema, payload.ToJsonString(), isCommand: false).IsValid.ShouldBeTrue();
        operation.AggregateIdAccessor.ShouldNotBeNull()(JsonSerializer.SerializeToElement(new { ItemId })).ShouldBe(ItemId);
        if (matchingTenant)
        {
            payload["tenant/~"] = "session-tenant";
        }

        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway, probe: assembly).ExecuteAsync(
            new RunQueryArguments(operation.Name, payload.ToJsonString()), Context(), TestContext.Current.CancellationToken);
        AssertRefusal(outcome, gateway, "/", "/tenant~1~0");
    }

    /// <summary>Raw ownership uses the renamed tenant's escaped serialized pointer before final revalidation.</summary>
    [Theory]
    [InlineData("\"other-tenant\"")]
    [InlineData("42")]
    public async Task RenamedTenantOwnershipUsesSerializedPointerAsync(string tenant)
    {
        var assembly = new QueryValidationContractsAssembly();
        string payload = $$"""{"ItemId":"{{ItemId}}","tenant/~":{{tenant}}}""";
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway, probe: assembly).ExecuteAsync(
            new RunQueryArguments("query-validation.tenant-schema-probe", payload), Context(), TestContext.Current.CancellationToken);
        AssertRefusal(outcome, gateway, "/tenant~1~0");
        outcome.Error!.Violations!.ShouldHaveSingleItem().Message.ShouldBe("The payload tenant disagrees with the resolved tenant.");
    }

    /// <summary>A missing URL prevents execution while the same catalog remains available for discovery.</summary>
    [Fact]
    public async Task MissingUrlLeavesOfflineDiscoveryAvailableAsync()
    {
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway, hasUrl: false).ExecuteAsync(
            new RunQueryArguments("routing-fixture.get-http2-status", "{}", AggregateId: ItemId), Context(),
            TestContext.Current.CancellationToken);
        outcome.Document.ShouldBeNull();
        outcome.Error.ShouldBe(new OperationError("configuration_invalid", Message: "Gateway URL is not configured."));
        gateway.ReceivedCalls().ShouldBeEmpty();

        var catalog = new CatalogService(Provider(), new ExecutionAvailability(false, false), strict: false);
        catalog.ListModules().Error.ShouldBeNull();
        catalog.ListOperations("routing-fixture").Error.ShouldBeNull();
        OperationDescriptionDocument described = catalog.Describe("routing-fixture.get-http2-status").Document.ShouldNotBeNull();
        described.Submittable.ShouldBeFalse();
        described.Reason.ShouldBe("configuration_invalid");
        gateway.ReceivedCalls().ShouldBeEmpty();
    }
}
