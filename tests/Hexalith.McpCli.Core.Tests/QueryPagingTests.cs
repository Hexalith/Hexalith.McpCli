using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Queries;
using Shouldly;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using static Hexalith.McpCli.Core.Tests.QueryTestHarness;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Checks envelope paging boundaries, payload isolation, and exact returned paging metadata.</summary>
public sealed class QueryPagingTests
{
    /// <summary>Supplies omitted, single-member, boundary, and blank cursor paging requests.</summary>
    public static IEnumerable<object?[]> ValidPaging()
    {
        yield return [null, null, null];
        yield return [1, null, null];
        yield return [200, null, null];
        yield return [null, 0, null];
        yield return [null, int.MaxValue, null];
        yield return [null, null, new string('x', 4096)];
        yield return [null, null, string.Concat(Enumerable.Repeat("😀", 2048))];
        yield return [null, null, ""];
        yield return [null, null, " \t\r\n"];
        yield return [null, 0, ""];
        yield return [200, int.MaxValue, " \t"];
        yield return [1, null, "opaque-cursor"];
        yield return [null, null, " opaque+/=_:\t "];
    }

    /// <summary>Exactly the supplied paging values reach the request; the client never inserts defaults.</summary>
    [Theory]
    [MemberData(nameof(ValidPaging))]
    public async Task SuppliedPagingIsPreservedAsync(int? pageSize, int? offset, string? cursor)
    {
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("string-fixture.list-items", "{}", PageSize: pageSize, Offset: offset, Cursor: cursor),
            Context(), TestContext.Current.CancellationToken);
        var expected = new SubmitQueryRequest("fixed-tenant", "string-fixture", "items-index", "list-items-wire", "string-items",
            JsonSerializer.SerializeToElement(new { }))
        {
            Paging = pageSize is null && offset is null && cursor is null ? null : new QueryPagingOptions(pageSize, offset, cursor),
        };
        AssertRequest(gateway, expected);
        AssertResult(outcome, """{"operation":"string-fixture.list-items","tenant":"fixed-tenant","document":{"items":[]}}""");
    }

    /// <summary>Supplies adjacent invalid boundaries and the nonblank cursor/offset conflict.</summary>
    public static IEnumerable<object?[]> InvalidPaging()
    {
        yield return [0, null, null, "/pageSize"];
        yield return [-1, null, null, "/pageSize"];
        yield return [201, null, null, "/pageSize"];
        yield return [null, -1, null, "/offset"];
        yield return [null, null, new string('x', 4097), "/cursor"];
        yield return [null, null, new string(' ', 4097), "/cursor"];
        yield return [null, null, string.Concat(Enumerable.Repeat("😀", 2048)) + "x", "/cursor"];
        yield return [null, 0, "opaque-cursor", "/cursor"];
        yield return [200, int.MaxValue, "opaque-cursor", "/cursor"];
    }

    /// <summary>Every paging refusal identifies its envelope member and makes zero calls.</summary>
    [Theory]
    [MemberData(nameof(InvalidPaging))]
    public async Task InvalidPagingMakesZeroCallsAsync(int? pageSize, int? offset, string? cursor, string path)
    {
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("string-fixture.list-items", "{}", PageSize: pageSize, Offset: offset, Cursor: cursor),
            Context(), TestContext.Current.CancellationToken);
        AssertRefusal(outcome, gateway, path);
        outcome.Error!.Violations!.ShouldHaveSingleItem();
    }

    /// <summary>Payload paging members remain ordinary data whether envelope paging differs or is absent.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task PayloadPagingNamesAreNeverInferredAsync(bool envelopePaging)
    {
        JsonNode payload = JsonNode.Parse(InspectPayload)!;
        payload["PageSize"] = 999;
        payload["Offset"] = -1;
        payload["Cursor"] = "payload-cursor";
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("lint-fixture.inspect-item", payload.ToJsonString(),
                PageSize: envelopePaging ? 25 : null, Offset: envelopePaging ? 0 : null),
            Context(), TestContext.Current.CancellationToken);
        payload["Tenant"] = "session-tenant";
        AssertRequest(gateway, new SubmitQueryRequest("session-tenant", "lint-fixture", ItemId, "inspect-item", "lint-items",
            JsonSerializer.SerializeToElement(payload)) { Paging = envelopePaging ? new QueryPagingOptions(25, 0) : null });
        AssertResult(outcome, """{"operation":"lint-fixture.inspect-item","tenant":"session-tenant","document":{"items":[]}}""");

        OperationDescriptor descriptor = Provider().Get(strict: false).Catalog.ShouldNotBeNull().Modules
            .Single(module => module.Name == "lint-fixture").Operations.Single(operation => operation.Name == "lint-fixture.inspect-item");
        descriptor.LintFindings.Where(finding => finding.Code == "payload_paging_member").Select(finding => finding.Property)
            .ShouldContain("/properties/PageSize");
        descriptor.LintFindings.ShouldContain(finding => finding.Code == "payload_paging_member" && finding.Property == "/properties/Offset");
        descriptor.LintFindings.ShouldContain(finding => finding.Code == "payload_paging_member" && finding.Property == "/properties/Cursor");
    }

    /// <summary>Returned paging members are independent, including zero, false, and an empty cursor.</summary>
    [Theory]
    [InlineData(null, true, false)]
    [InlineData("{\"pageSize\":17}", true, false)]
    [InlineData("{\"pageSize\":17,\"offset\":0}", true, false)]
    [InlineData("{\"pageSize\":17,\"nextCursor\":\"next-page\"}", true, false)]
    [InlineData("{\"pageSize\":17,\"nextCursor\":\"\"}", true, false)]
    [InlineData("{\"pageSize\":17,\"totalCount\":0}", true, false)]
    [InlineData("{\"pageSize\":17,\"totalCount\":9223372036854775807}", true, false)]
    [InlineData("{\"pageSize\":17,\"hasMore\":false}", true, false)]
    [InlineData("{\"pageSize\":17,\"hasMore\":true}", true, false)]
    [InlineData("{\"pageSize\":17,\"offset\":0,\"nextCursor\":\"next-page\",\"totalCount\":0,\"hasMore\":false}", true, false)]
    [InlineData("{\"pageSize\":17}", false, false)]
    [InlineData("{\"pageSize\":17,\"offset\":0,\"nextCursor\":\"next-page\",\"totalCount\":0,\"hasMore\":false}", false, true)]
    [InlineData("{\"pageSize\":17,\"offset\":0,\"nextCursor\":\"next-page\",\"totalCount\":0,\"hasMore\":false}", true, true)]
    public async Task ReturnedMetadataIsMappedWithoutInventedFieldsAsync(string? returnedPaging, bool requestPaging, bool nullDocument)
    {
        QueryPagingMetadata? paging = returnedPaging is null ? null
            : JsonSerializer.Deserialize<QueryPagingMetadata>(returnedPaging, new JsonSerializerOptions(JsonSerializerDefaults.Web));
        IEventStoreGatewayClient gateway = Gateway(new QueryResponseMetadata(ETag: "unrelated-metadata", Paging: paging), nullDocument);
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("string-fixture.list-items", "{}", PageSize: requestPaging ? 25 : null, Offset: requestPaging ? 8 : null),
            Context(), TestContext.Current.CancellationToken);
        AssertRequest(gateway, new SubmitQueryRequest("fixed-tenant", "string-fixture", "items-index", "list-items-wire", "string-items",
            JsonSerializer.SerializeToElement(new { })) { Paging = requestPaging ? new QueryPagingOptions(25, 8) : null });
        string pagingMember = returnedPaging is null ? "" : ",\"paging\":" + returnedPaging;
        string document = nullDocument ? "null" : "{\"items\":[]}";
        AssertResult(outcome, $$"""{"operation":"string-fixture.list-items","tenant":"fixed-tenant","document":{{document}}{{pagingMember}}}""");
    }
}
