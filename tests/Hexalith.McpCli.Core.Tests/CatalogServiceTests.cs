using System.Text.Json;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Sample.Contracts;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Checks the shared public discovery documents and session availability.</summary>
public sealed class CatalogServiceTests
{
    /// <summary>Lists a declared module and applies the public read/write filter.</summary>
    [Fact]
    public void ListsModuleAndFilteredOperations()
    {
        ICatalog catalog = Create(readOnly: false, hasGatewayUrl: true);

        ModulesDocument modules = catalog.ListModules().Document.ShouldNotBeNull();
        modules.Modules.Count.ShouldBe(1);
        modules.Modules[0].Name.ShouldBe("sample");
        modules.Modules[0].OperationCount.ShouldBe(3);

        OperationsDocument reads = catalog.ListOperations("sample", "read").Document.ShouldNotBeNull();
        reads.Operations.Count.ShouldBe(1);
        reads.Operations[0].Name.ShouldBe("sample.get-item");
        reads.Operations[0].Kind.ShouldBe("read");

        OperationsDocument writes = catalog.ListOperations("sample", "write").Document.ShouldNotBeNull();
        writes.Operations.Count.ShouldBe(2);
        writes.Operations.ShouldAllBe(item => item.Kind == "write");
    }

    /// <summary>A flagged, marked assembly with no operations remains visible beside a callable module.</summary>
    [Fact]
    public void MarkedEmptyModuleRemainsDiscoverable()
    {
        var provider = new CatalogProvider(
            () => [typeof(CreateItemCommand).Assembly, typeof(Manifest.MarkedEmpty.Contracts.Module).Assembly],
            new RecordingLogger<CatalogProvider>());
        ICatalog catalog = new CatalogService(provider, new ExecutionAvailability(false, true), strict: false);

        ModulesDocument modules = catalog.ListModules().Document.ShouldNotBeNull();
        ModuleSummary empty = modules.Modules.Single(item => item.OperationCount == 0);
        OperationsDocument operations = catalog.ListOperations(empty.Name).Document.ShouldNotBeNull();

        operations.Operations.ShouldBeEmpty();
    }

    /// <summary>Unknown names have only the specified error fields and nearest suggestions.</summary>
    [Fact]
    public void UnknownNamesReturnCanonicalSuggestions()
    {
        ICatalog catalog = Create(readOnly: false, hasGatewayUrl: true);

        OperationError unknownModule = catalog.ListOperations("smple").Error.ShouldNotBeNull();
        JsonElement moduleJson = JsonSerializer.SerializeToElement(unknownModule, McpCliJson.Result);
        unknownModule.Code.ShouldBe("unknown_module");
        unknownModule.Suggestions.ShouldBe(["sample"]);
        moduleJson.EnumerateObject().Select(item => item.Name).ShouldBe(["code", "module", "suggestions"]);

        OperationError unknownOperation = catalog.Describe("sample.get-itm").Error.ShouldNotBeNull();
        unknownOperation.Code.ShouldBe("unknown_operation");
        unknownOperation.Suggestions![0].ShouldBe("sample.get-item");
    }

    /// <summary>Read-only mode blocks writes while no URL blocks otherwise available reads.</summary>
    [Fact]
    public void DescriptionsUseSharedAvailabilityPriority()
    {
        ICatalog catalog = Create(readOnly: true, hasGatewayUrl: false);

        OperationDescriptionDocument write = catalog.Describe("sample.create-item").Document.ShouldNotBeNull();
        write.Kind.ShouldBe("write");
        write.Submittable.ShouldBeFalse();
        write.Reason.ShouldBe("read_only");
        write.Envelope.FixedTenant.ShouldBe("sample-tenant");
        write.Envelope.Arguments.ShouldNotContain("tenant");
        write.Envelope.Arguments.ShouldContain("idempotencyKey");

        OperationDescriptionDocument read = catalog.Describe("sample.get-item").Document.ShouldNotBeNull();
        read.Kind.ShouldBe("read");
        read.Submittable.ShouldBeFalse();
        read.Reason.ShouldBe("configuration_invalid");
        read.Envelope.Arguments.ShouldContain("pageSize");
        read.Envelope.Arguments.ShouldNotContain("idempotencyKey");
    }

    /// <summary>A nullable mapped key remains required when serializer metadata requires it.</summary>
    [Fact]
    public void RequiredNullableIdempotencyAppearsInDiscovery()
    {
        var provider = new CatalogProvider(() => [typeof(global::Catalog.Routing.Contracts.Module).Assembly],
            new RecordingLogger<CatalogProvider>());
        ICatalog catalog = new CatalogService(provider, new ExecutionAvailability(false, true), strict: false);

        OperationDescriptionDocument description = catalog.Describe("routing-fixture.required-nullable-idempotency")
            .Document.ShouldNotBeNull();
        description.Envelope.IdempotencyKeyRequired.ShouldBeTrue();
        description.Schema["properties"]!["Idempotency"]!["readOnly"]!.GetValue<bool>().ShouldBeTrue();
    }

    /// <summary>Optional fields are absent, and payload schema casing stays unchanged.</summary>
    [Fact]
    public void DescriptionSerializationPreservesContractShape()
    {
        ICatalog catalog = Create(readOnly: false, hasGatewayUrl: true);
        OperationDescriptionDocument description = catalog.Describe("sample.get-item").Document.ShouldNotBeNull();

        JsonElement json = JsonSerializer.SerializeToElement(description, McpCliJson.Result);
        json.TryGetProperty("reason", out _).ShouldBeFalse();
        json.GetProperty("schema").GetProperty("properties").TryGetProperty("ItemId", out _).ShouldBeTrue();
        json.GetProperty("envelope").TryGetProperty("fixedTenant", out _).ShouldBeTrue();
        json.GetProperty("lintFindings").ValueKind.ShouldBe(JsonValueKind.Array);
    }

    private static ICatalog Create(bool readOnly, bool hasGatewayUrl)
    {
        var provider = new CatalogProvider(() => [typeof(CreateItemCommand).Assembly], new RecordingLogger<CatalogProvider>());
        return new CatalogService(provider, new ExecutionAvailability(readOnly, hasGatewayUrl), strict: true);
    }
}
