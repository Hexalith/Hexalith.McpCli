using System.Text.Json;
using System.Text.Json.Nodes;
using Shouldly;
using static Hexalith.McpCli.Cli.Tests.QueryCliHarness;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Checks real CLI paging bindings and complete canonical request/result documents.</summary>
public sealed class QueryPagingCommandTests
{
    /// <summary>Supplies boundary options with independently written expected request paging.</summary>
    public static IEnumerable<object?[]> PagingOptions()
    {
        yield return [Array.Empty<string>(), null];
        yield return [new[] { "--page-size", "1" }, "{\"pageSize\":1}"];
        yield return [new[] { "--page-size", "200" }, "{\"pageSize\":200}"];
        yield return [new[] { "--offset", "0" }, "{\"offset\":0}"];
        yield return [new[] { "--offset", "2147483647" }, "{\"offset\":2147483647}"];
        yield return [new[] { "--cursor", "opaque-cursor" }, "{\"cursor\":\"opaque-cursor\"}"];
        yield return [new[] { "--cursor", " opaque+/=_:\t " }, "{\"cursor\":\" opaque+/=_:\\t \"}"];
        yield return [new[] { "--cursor", "" }, "{\"cursor\":\"\"}"];
        yield return [new[] { "--cursor", " \t", "--offset", "0" }, "{\"cursor\":\" \\t\",\"offset\":0}"];
        yield return [new[] { "--page-size", "200", "--offset", "2147483647" }, "{\"pageSize\":200,\"offset\":2147483647}"];
        string cursor = new('x', 4096);
        yield return [new[] { "--cursor", cursor }, JsonSerializer.Serialize(new { cursor })];
        string unicodeCursor = string.Concat(Enumerable.Repeat("😀", 2048));
        yield return [new[] { "--cursor", unicodeCursor }, JsonSerializer.Serialize(new { cursor = unicodeCursor })];
    }

    /// <summary>Omitted paging stays absent and supplied members arrive without defaults.</summary>
    [Theory]
    [MemberData(nameof(PagingOptions))]
    public async Task PagingOptionsSubmitExactlyOnceAsync(string[] options, string? paging)
    {
        await using var harness = new QueryCliHarness();
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "string-fixture.list-items", "--payload", "{}", .. options]);
        exit.ShouldBe(0, output + error);
        AssertDiagnostics(error);
        string pagingMember = paging is null ? "" : ",\"paging\":" + paging;
        harness.AssertRequest($$"""
            {"tenant":"fixed-tenant","domain":"string-fixture","aggregateId":"items-index",
             "queryType":"list-items-wire","projectionType":"string-items","payload":{}{{pagingMember}}}
            """);
        AssertJson(output, """{"operation":"string-fixture.list-items","tenant":"fixed-tenant","document":{"items":[]}}""");
    }

    /// <summary>Entity identifiers follow Gateway syntax and retain exact values, independent of ULID aggregate kind.</summary>
    [Theory]
    [InlineData(1, 1)]
    [InlineData(64, 256)]
    public async Task EntityAndTenantBoundaryValuesArePreservedAsync(int tenantLength, int entityLength)
    {
        string tenant = new('a', tenantLength);
        string entity = entityLength == 1 ? "A" : "A._-" + new string('z', entityLength - 5) + "9";
        string aggregate = ItemId.ToLowerInvariant();
        await using var harness = new QueryCliHarness();
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "routing-fixture.get-http2-status", "--payload", "{}", "--tenant", tenant,
                "--aggregate-id", aggregate, "--entity-id", entity]);
        exit.ShouldBe(0, output + error);
        AssertDiagnostics(error);
        harness.AssertRequest($$"""
            {"tenant":"{{tenant}}","domain":"routing","aggregateId":"{{aggregate}}",
             "queryType":"get-http2-status","projectionType":"routing-items","payload":{},"entityId":"{{entity}}"}
            """);
        AssertJson(output, $$$"""{"operation":"routing-fixture.get-http2-status","tenant":"{{{tenant}}}","document":{"items":[]}}""");
    }

    /// <summary>Tenant digit endpoints and internal hyphens survive CLI binding and Gateway submission.</summary>
    [Theory]
    [InlineData("0")]
    [InlineData("0-a-9")]
    public async Task ValidDigitAndHyphenTenantsArePreservedAsync(string tenant)
    {
        await using var harness = new QueryCliHarness();
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "routing-fixture.get-http2-status", "--payload", "{}", "--tenant", tenant, "--aggregate-id", ItemId]);
        exit.ShouldBe(0, output + error);
        AssertDiagnostics(error);
        harness.AssertRequest($$$"""
            {"tenant":"{{{tenant}}}","domain":"routing","aggregateId":"{{{ItemId}}}",
             "queryType":"get-http2-status","projectionType":"routing-items","payload":{}}
            """);
        AssertJson(output, $$$"""{"operation":"routing-fixture.get-http2-status","tenant":"{{{tenant}}}","document":{"items":[]}}""");
    }

    /// <summary>String aggregate boundary values are passed unchanged rather than validated as ULIDs.</summary>
    [Theory]
    [InlineData(1)]
    [InlineData(256)]
    public async Task StringAggregateBoundaryValuesArePreservedAsync(int length)
    {
        string aggregate = length == 1 ? "A" : "A._-" + new string('z', length - 5) + "9";
        await using var harness = new QueryCliHarness();
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "string-fixture.list-items", "--payload", "{}", "--aggregate-id", aggregate]);
        exit.ShouldBe(0, output + error);
        AssertDiagnostics(error);
        harness.AssertRequest($$$"""
            {"tenant":"fixed-tenant","domain":"string-fixture","aggregateId":"{{{aggregate}}}",
             "queryType":"list-items-wire","projectionType":"string-items","payload":{}}
            """);
        AssertJson(output, """{"operation":"string-fixture.list-items","tenant":"fixed-tenant","document":{"items":[]}}""");
    }

    /// <summary>Tenant filling keeps payload paging data intact and lint warnings remain visible.</summary>
    [Theory]
    [InlineData(false, false)]
    [InlineData(false, true)]
    [InlineData(true, false)]
    [InlineData(true, true)]
    public async Task PayloadPagingIsIndependentAndTenantIsFilledAsync(bool envelopePaging, bool matchingTenant)
    {
        JsonNode payload = JsonNode.Parse(InspectPayload)!;
        payload["PageSize"] = 999;
        payload["Offset"] = -1;
        payload["Cursor"] = "payload-cursor";
        if (matchingTenant)
        {
            payload["Tenant"] = "session-tenant";
        }

        await using var harness = new QueryCliHarness();
        string[] options = envelopePaging ? ["--page-size", "25", "--offset", "0"] : [];
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "lint-fixture.inspect-item", "--payload", payload.ToJsonString(), "--tenant", "session-tenant", .. options]);
        exit.ShouldBe(0, output + error);
        AssertDiagnostics(error);
        payload["Tenant"] = "session-tenant";
        string pagingMember = envelopePaging ? ",\"paging\":{\"pageSize\":25,\"offset\":0}" : "";
        harness.AssertRequest($$"""
            {"tenant":"session-tenant","domain":"lint-fixture","aggregateId":"{{ItemId}}",
             "queryType":"inspect-item","projectionType":"lint-items","payload":{{payload.ToJsonString()}}{{pagingMember}}}
            """);
        AssertJson(output, """{"operation":"lint-fixture.inspect-item","tenant":"session-tenant","document":{"items":[]}}""");

        (int lintExit, string lintOutput, string lintError) = await harness.InvokeAsync(["describe", "lint-fixture.inspect-item", "--lint"]);
        lintExit.ShouldBe(1);
        AssertDiagnostics(lintError);
        using JsonDocument description = JsonDocument.Parse(lintOutput);
        string[] pagingPaths = [.. description.RootElement.GetProperty("lintFindings").EnumerateArray()
            .Where(finding => finding.GetProperty("code").GetString() == "payload_paging_member")
            .Select(finding => finding.GetProperty("property").GetString()!)];
        pagingPaths.ShouldContain("/properties/PageSize");
        pagingPaths.ShouldContain("/properties/Offset");
        pagingPaths.ShouldContain("/properties/Cursor");
        harness.Calls.ShouldBe(1);
    }

    /// <summary>Returned paging fields are independent and request options are never copied into results.</summary>
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
    public async Task ReturnedPagingContainsOnlyGatewayFieldsAsync(string? paging, bool requestPaging, bool nullDocument)
    {
        await using var harness = new QueryCliHarness(paging, nullDocument);
        string[] options = requestPaging ? ["--page-size", "25", "--offset", "8"] : [];
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "string-fixture.list-items", "--payload", "{}", .. options]);
        exit.ShouldBe(0, output + error);
        AssertDiagnostics(error);
        string requestPagingMember = requestPaging ? ",\"paging\":{\"pageSize\":25,\"offset\":8}" : "";
        harness.AssertRequest($$"""
            {"tenant":"fixed-tenant","domain":"string-fixture","aggregateId":"items-index",
             "queryType":"list-items-wire","projectionType":"string-items","payload":{}{{requestPagingMember}}}
            """);
        string pagingMember = paging is null ? "" : ",\"paging\":" + paging;
        string document = nullDocument ? "null" : "{\"items\":[]}";
        AssertJson(output, $$"""{"operation":"string-fixture.list-items","tenant":"fixed-tenant","document":{{document}}{{pagingMember}}}""");
    }
}
