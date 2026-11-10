using System.Reflection;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Sample.Contracts;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Pins Operation Shape derivation from real fixture Catalog descriptors and the sensitivity of its key.</summary>
public sealed class OperationShapeTests
{
    private static readonly Lazy<CatalogSnapshot> Fixtures = new(() => new CatalogProvider(() => new Assembly[]
    {
        typeof(CreateItemCommand).Assembly,
        typeof(global::Catalog.String.Contracts.LookupQuery).Assembly,
        typeof(global::Catalog.Routing.Contracts.Module).Assembly,
        typeof(global::Catalog.Explicit.Contracts.Module).Assembly,
    }, new RecordingLogger<CatalogProvider>()).Get(false).Catalog!);

    /// <summary>Gets fixture operations whose shapes together take every value of every component.</summary>
    public static TheoryData<string, string> FixtureShapes => new()
    {
        { "sample.create-item", "kind=command;identifierKind=ulid;wireTypeConvention=kebabCase;tenantSource=fixedTenant;aggregateIdSource=property;projectionSelector=none;idempotencyKey=optional" },
        { "sample.get-item", "kind=query;identifierKind=ulid;wireTypeConvention=kebabCase;tenantSource=fixedTenant;aggregateIdSource=property;projectionSelector=projectionType;idempotencyKey=optional" },
        { "string-fixture.lookup", "kind=query;identifierKind=string;wireTypeConvention=fullTypeName;tenantSource=fixedTenant;aggregateIdSource=property;projectionSelector=projectionType;idempotencyKey=optional" },
        { "string-fixture.list-items", "kind=query;identifierKind=string;wireTypeConvention=fullTypeName;tenantSource=fixedTenant;aggregateIdSource=constant;projectionSelector=projectionType;idempotencyKey=optional" },
        { "explicit-fixture.valid", "kind=query;identifierKind=string;wireTypeConvention=explicit;tenantSource=public;aggregateIdSource=none;projectionSelector=projectionType;idempotencyKey=optional" },
        { "routing-fixture.colon-wire", "kind=command;identifierKind=ulid;wireTypeConvention=kebabCase;tenantSource=platformScope;aggregateIdSource=property;projectionSelector=none;idempotencyKey=optional" },
        { "routing-fixture.computed-envelope", "kind=command;identifierKind=ulid;wireTypeConvention=kebabCase;tenantSource=public;aggregateIdSource=property;projectionSelector=none;idempotencyKey=optional" },
        { "routing-fixture.envelope-item", "kind=command;identifierKind=ulid;wireTypeConvention=kebabCase;tenantSource=public;aggregateIdSource=property;projectionSelector=none;idempotencyKey=required" },
        { "routing-fixture.interface-item", "kind=query;identifierKind=ulid;wireTypeConvention=kebabCase;tenantSource=public;aggregateIdSource=property;projectionSelector=projectionActorType;idempotencyKey=optional" },
        { "routing-fixture.items-list", "kind=query;identifierKind=ulid;wireTypeConvention=kebabCase;tenantSource=platformScope;aggregateIdSource=constant;projectionSelector=projectionType;idempotencyKey=optional" },
        { "routing-fixture.get-http2-status", "kind=query;identifierKind=ulid;wireTypeConvention=kebabCase;tenantSource=public;aggregateIdSource=none;projectionSelector=projectionType;idempotencyKey=optional" },
    };

    /// <summary>Each fixture operation derives its exact key from its module and operation descriptors.</summary>
    /// <param name="operation">The canonical fixture operation name.</param>
    /// <param name="expected">The exact Operation Shape key.</param>
    [Theory]
    [MemberData(nameof(FixtureShapes))]
    public void DerivesTheExactKeyFromCatalogDescriptors(string operation, string expected)
        => Shape(operation).Key.ShouldBe(expected);

    /// <summary>The fixture table exercises every value of every component, and distinct tuples never share a key.</summary>
    [Fact]
    public void FixtureTableCoversEveryComponentValueWithDistinctKeys()
    {
        OperationShape[] shapes = FixtureShapes.Select(row => Shape(row.Data.Item1)).ToArray();
        shapes.Select(shape => shape.Kind).Distinct().ShouldBe(["command", "query"], ignoreOrder: true);
        shapes.Select(shape => shape.IdentifierKind).Distinct().ShouldBe(["ulid", "string"], ignoreOrder: true);
        shapes.Select(shape => shape.WireTypeConvention).Distinct().ShouldBe(["explicit", "fullTypeName", "kebabCase"], ignoreOrder: true);
        shapes.Select(shape => shape.TenantSource).Distinct().ShouldBe(["platformScope", "fixedTenant", "public"], ignoreOrder: true);
        shapes.Select(shape => shape.AggregateIdSource).Distinct().ShouldBe(["property", "constant", "none"], ignoreOrder: true);
        shapes.Select(shape => shape.ProjectionSelector).Distinct().ShouldBe(["projectionActorType", "projectionType", "none"], ignoreOrder: true);
        shapes.Select(shape => shape.IdempotencyKey).Distinct().ShouldBe(["required", "optional"], ignoreOrder: true);
        shapes.Select(shape => shape.Key).Distinct(StringComparer.Ordinal).Count().ShouldBe(shapes.Distinct().Count());
    }

    /// <summary>Changing any single component to any other value changes the key.</summary>
    /// <param name="component">The changed component.</param>
    /// <param name="value">The replacement value.</param>
    [Theory]
    [InlineData("Kind", "query")]
    [InlineData("IdentifierKind", "string")]
    [InlineData("WireTypeConvention", "explicit")]
    [InlineData("WireTypeConvention", "fullTypeName")]
    [InlineData("TenantSource", "platformScope")]
    [InlineData("TenantSource", "public")]
    [InlineData("AggregateIdSource", "constant")]
    [InlineData("AggregateIdSource", "none")]
    [InlineData("ProjectionSelector", "projectionActorType")]
    [InlineData("ProjectionSelector", "projectionType")]
    [InlineData("IdempotencyKey", "required")]
    public void ChangingOneComponentChangesTheKey(string component, string value)
    {
        OperationShape baseline = Shape("sample.create-item");
        OperationShape changed = component switch
        {
            nameof(OperationShape.Kind) => baseline with { Kind = value },
            nameof(OperationShape.IdentifierKind) => baseline with { IdentifierKind = value },
            nameof(OperationShape.WireTypeConvention) => baseline with { WireTypeConvention = value },
            nameof(OperationShape.TenantSource) => baseline with { TenantSource = value },
            nameof(OperationShape.AggregateIdSource) => baseline with { AggregateIdSource = value },
            nameof(OperationShape.ProjectionSelector) => baseline with { ProjectionSelector = value },
            _ => baseline with { IdempotencyKey = value },
        };

        changed.Key.ShouldNotBe(baseline.Key);
        changed.Key.Split(';').ShouldContain(char.ToLowerInvariant(component[0]) + component[1..] + "=" + value);
        changed.Key.Split(';').Except(baseline.Key.Split(';')).Count().ShouldBe(1);
    }

    private static OperationShape Shape(string operation)
    {
        ModuleDescriptor module = Fixtures.Value.Modules.Single(item => item.Operations.Any(descriptor => descriptor.Name == operation));
        return OperationShape.From(module, module.Operations.Single(descriptor => descriptor.Name == operation));
    }
}
