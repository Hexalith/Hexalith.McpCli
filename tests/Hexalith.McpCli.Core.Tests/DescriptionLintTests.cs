using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Schema;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Sample.Contracts;
using Shouldly;
using Lint = global::Catalog.Lint.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Verifies description warnings on valid catalog operations.</summary>
public sealed class DescriptionLintTests
{
    /// <summary>Nested and collection members use schema pointers; ignored and computed members are excluded.</summary>
    [Fact]
    public void NestedDescriptionIdentifierAndPagingFindingsTargetExportedSchema()
    {
        OperationDescriptor operation = BuildLintCatalog().Modules.Single().Operations.Single(item => item.ContractType == typeof(Lint.InspectItemQuery));
        operation.LintFindings.Select(finding => (finding.Code, finding.Property)).ShouldBe(
        new (string Code, string? Property)[]
        {
            ("missing_property_description", "/properties/Entries/items/properties/Count"),
            ("missing_property_description", "/properties/EntriesByKey/additionalProperties/properties/Quantity"),
            ("unmarked_identifier_like_property", "/properties/ExternalId"),
            ("missing_property_description", "/properties/Maybe/properties/Count"),
            ("unmarked_identifier_like_property", "/properties/Maybe/properties/ExternalId"),
            ("unmarked_identifier_like_property", "/properties/Nested/properties/external~1~0id"),
            ("missing_property_description", "/properties/Nested/properties/nested~1~0"),
            ("missing_property_description", "/properties/Nested/properties/page~1~0size"),
            ("payload_paging_member", "/properties/Nested/properties/page~1~0size"),
            ("payload_paging_member", "/properties/Cursor"),
            ("payload_paging_member", "/properties/Offset"),
            ("payload_paging_member", "/properties/PageSize"),
            ("missing_property_description", "/properties/Tenant"),
            ("missing_property_description", "/properties/lowerCamel"),
        }.OrderBy(item => item.Property, StringComparer.Ordinal).ThenBy(item => item.Code, StringComparer.Ordinal).ToArray());

        JsonNode schema = operation.Schema.Node;
        foreach (LintFinding finding in operation.LintFindings)
        {
            finding.Severity.ShouldBe("warning");
            finding.Message.ShouldNotBeNullOrWhiteSpace();
            Resolve(schema, finding.Property!).ShouldNotBeNull();
        }

        LintFinding renamedIdentifier = operation.LintFindings.Single(finding => finding.Code == "unmarked_identifier_like_property"
            && finding.Property == "/properties/Nested/properties/external~1~0id");
        renamedIdentifier.Message.ShouldContain("Member ExternalId");
        renamedIdentifier.Message.ShouldContain("Use a property marked with HexalithIdentifier");
        operation.LintFindings.Single(finding => finding.Code == "payload_paging_member"
            && finding.Property == "/properties/Nested/properties/page~1~0size").Message.ShouldContain("paging member PageSize");
        operation.LintFindings.Single(finding => finding.Code == "missing_property_description"
            && finding.Property == "/properties/Nested/properties/nested~1~0").Message.ShouldContain("payload member Escaped");
        operation.LintFindings.Where(finding => finding.Code == "missing_property_description")
            .ShouldAllBe(finding => !finding.Message.Contains("supply", StringComparison.OrdinalIgnoreCase));
        schema["properties"]!["Tenant"]!["readOnly"]!.GetValue<bool>().ShouldBeTrue();

        operation.LintFindings.ShouldNotContain(finding => finding.Property!.Contains("IgnoredId", StringComparison.Ordinal)
            || finding.Property.Contains("ComputedId", StringComparison.Ordinal)
            || finding.Property.Contains("MarkedId", StringComparison.Ordinal)
            || finding.Property.Contains("ItemId", StringComparison.Ordinal));
        schema["properties"]!["ExternalId"]!["pattern"].ShouldBeNull();
        schema["properties"]!["ItemId"]!["pattern"]!.GetValue<string>().ShouldBe(SchemaDeriver.UlidPattern);
        schema["properties"]!["Entries"]!["items"]!["properties"]!["MarkedId"]!["pattern"]!.GetValue<string>()
            .ShouldBe(SchemaDeriver.UlidPattern);
        schema["properties"]!["Entries"]!["items"]!["properties"]!["Count"]!["description"]!.GetValue<string>()
            .ShouldBe("   ");
        schema["properties"]!["Nested"]!["properties"]!["nested/~"].ShouldNotBeNull();
        schema["properties"]!["Nested"]!["properties"]!["Label"]!["description"]!.GetValue<string>()
            .ShouldBe("The label supplied for the nested item.");
        schema["properties"]!["Nested"]!["properties"]!["external/~id"]!["description"]!.GetValue<string>()
            .ShouldBe("The external identifier of the nested item.");
        schema["properties"]!["lowerCamel"].ShouldNotBeNull();
    }

    /// <summary>Envelope-bound identifiers are not identifier hints, and command paging names are ordinary payload members.</summary>
    [Fact]
    public void CommandHollowDescriptionDoesNotWarnOnPagingOrEnvelopeIdentifier()
    {
        OperationDescriptor command = BuildLintCatalog().Modules.Single().Operations.Single(item => item.ContractType == typeof(Lint.MoveItemCommand));

        command.Kind.ShouldBe(OperationKind.Command);
        command.LintFindings.Select(finding => finding.Code).ShouldBe(["hollow_description"]);
        command.LintFindings.Single().Property.ShouldBeNull();
        command.Schema.Node["properties"]!["TenantId"]!["readOnly"]!.GetValue<bool>().ShouldBeTrue();
        command.Schema.Node["properties"]!["TenantId"]!["pattern"].ShouldBeNull();
    }

    /// <summary>An ICommandContract aggregate source counts as marked, and a kebab-case restatement of the name is hollow.</summary>
    [Fact]
    public void ContractAggregateSourceIsMarkedAndKebabNameIsHollow()
    {
        OperationDescriptor command = BuildLintCatalog().Modules.Single().Operations
            .Single(item => item.ContractType == typeof(Lint.ContractSourceCommand));

        command.Kind.ShouldBe(OperationKind.Command);
        command.PropertyBindings.ShouldBeEmpty();
        command.Schema.Node["properties"]!["AggregateId"].ShouldNotBeNull();
        command.LintFindings.Select(finding => finding.Code).ShouldBe(["hollow_description"]);
        command.LintFindings.Single().Property.ShouldBeNull();
    }

    /// <summary>Operation-level findings omit the property member while property findings include it.</summary>
    [Fact]
    public void FindingDocumentsHaveTheRequiredShape()
    {
        ModuleDescriptor module = BuildLintCatalog().Modules.Single();
        OperationDescriptor hollow = module.Operations.Single(item => item.ContractType == typeof(Lint.InspectHollowQuery));
        LintFinding hollowFinding = hollow.LintFindings.Single();
        hollowFinding.Code.ShouldBe("hollow_description");
        hollowFinding.Severity.ShouldBe("warning");
        hollowFinding.Message.ShouldNotBeNullOrWhiteSpace();
        hollowFinding.Property.ShouldBeNull();

        using JsonDocument hollowJson = JsonDocument.Parse(JsonSerializer.Serialize(hollowFinding, McpCliJson.Result));
        hollowJson.RootElement.TryGetProperty("property", out _).ShouldBeFalse();
        hollowJson.RootElement.GetProperty("code").GetString().ShouldBe("hollow_description");
        hollowJson.RootElement.GetProperty("severity").GetString().ShouldBe("warning");
        hollowJson.RootElement.GetProperty("message").GetString().ShouldNotBeNullOrWhiteSpace();

        LintFinding propertyFinding = module.Operations.Single(item => item.ContractType == typeof(Lint.InspectItemQuery)).LintFindings.First();
        using JsonDocument propertyJson = JsonDocument.Parse(JsonSerializer.Serialize(propertyFinding, McpCliJson.Result));
        propertyJson.RootElement.GetProperty("code").GetString().ShouldNotBeNullOrWhiteSpace();
        propertyJson.RootElement.GetProperty("severity").GetString().ShouldBe("warning");
        propertyJson.RootElement.GetProperty("message").GetString().ShouldNotBeNullOrWhiteSpace();
        propertyJson.RootElement.GetProperty("property").GetString().ShouldBe(propertyFinding.Property);
    }

    /// <summary>Lint alone creates no catalog diagnostics, logging, or strict access failure.</summary>
    [Fact]
    public void LintDoesNotAffectCatalogStrictness()
    {
        var logger = new RecordingLogger<CatalogProvider>();
        var provider = new CatalogProvider(() => [typeof(Lint.Module).Assembly], logger);

        CatalogAccess normal = provider.Get(strict: false);
        CatalogAccess strict = provider.Get(strict: true);

        normal.Catalog.ShouldNotBeNull();
        strict.Catalog.ShouldBeSameAs(normal.Catalog);
        strict.ErrorCode.ShouldBeNull();
        normal.Catalog.Diagnostics.ShouldBeEmpty();
        normal.Catalog.Modules.Single().Operations.Count.ShouldBe(4);
        normal.Catalog.Modules.Single().Operations.ShouldAllBe(operation => operation.LintFindings.Count > 0);
        logger.Entries.ShouldBeEmpty();
    }

    /// <summary>Complete sample descriptions yield an explicit empty array and no diagnostics.</summary>
    [Fact]
    public void CompleteSampleContractsHaveNoFindings()
    {
        CatalogSnapshot catalog = CatalogBuilder.Build([typeof(CreateItemCommand).Assembly]);
        catalog.Diagnostics.ShouldBeEmpty();
        foreach (OperationDescriptor operation in catalog.Modules.Single().Operations)
        {
            operation.LintFindings.ShouldBeEmpty();
            using JsonDocument document = JsonDocument.Parse(JsonSerializer.Serialize(operation, McpCliJson.Result));
            document.RootElement.GetProperty("lintFindings").GetArrayLength().ShouldBe(0);
        }
    }

    /// <summary>Manifest order and repeated builds produce identical lint-bearing result bytes.</summary>
    [Fact]
    public void RepeatedBuildsAndManifestOrderProduceIdenticalDocuments()
    {
        Assembly[] assemblies = [typeof(Lint.Module).Assembly, typeof(CreateItemCommand).Assembly];
        CatalogSnapshot first = CatalogBuilder.Build(assemblies);
        CatalogSnapshot repeated = CatalogBuilder.Build(assemblies);
        CatalogSnapshot reversed = CatalogBuilder.Build([.. assemblies.Reverse()]);

        byte[] Serialize(CatalogSnapshot catalog) => JsonSerializer.SerializeToUtf8Bytes(
            catalog.Modules.SelectMany(module => module.Operations).ToArray(), McpCliJson.Result);
        Serialize(repeated).ShouldBe(Serialize(first));
        Serialize(reversed).ShouldBe(Serialize(first));
    }

    private static CatalogSnapshot BuildLintCatalog() => CatalogBuilder.Build([typeof(Lint.Module).Assembly]);

    private static JsonNode? Resolve(JsonNode root, string pointer)
    {
        JsonNode? current = root;
        foreach (string segment in pointer.Split('/').Skip(1))
        {
            current = current?[segment.Replace("~1", "/", StringComparison.Ordinal).Replace("~0", "~", StringComparison.Ordinal)];
        }

        return current;
    }
}
