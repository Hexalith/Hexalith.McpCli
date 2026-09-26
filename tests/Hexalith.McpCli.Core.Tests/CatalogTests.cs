using System.Reflection;
using System.Reflection.Emit;
using System.Text.Json;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Schema;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Sample.Contracts;
using Shouldly;
using Invalid = global::Catalog.Invalid.Contracts;
using Routing = global::Catalog.Routing.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Verifies deterministic discovery and pre-resolved operation contracts.</summary>
public sealed class CatalogTests
{
    /// <summary>Marked modules are ordered; unmarked inputs are silent, and a bad provider excludes its module.</summary>
    [Fact]
    public void SuppliedAssemblyManifestIsTheOnlyDiscoverySource()
    {
        CatalogSnapshot catalog = CatalogBuilder.Build([
            typeof(Manifest.Unmarked.Contracts.Placeholder).Assembly,
            typeof(Hexalith.McpCli.Sample.Contracts.CreateItemCommand).Assembly,
            typeof(global::Catalog.String.Contracts.LookupQuery).Assembly,
            typeof(global::Catalog.InvalidProvider.Contracts.Module).Assembly,
        ]);

        catalog.Modules.Select(module => module.Name).ShouldBe(["sample", "string-fixture"]);
        catalog.Diagnostics.ShouldContain(diagnostic => diagnostic.Category == "invalid_serializer_options_provider"
            && diagnostic.TypeName == "Catalog.InvalidProvider.Contracts" && diagnostic.Severity == "error");
        catalog.Diagnostics.ShouldNotContain(diagnostic => diagnostic.TypeName == typeof(Manifest.Unmarked.Contracts.Placeholder).Assembly.GetName().Name);
        catalog.Modules.Single(module => module.Name == "sample").Operations.Select(operation => operation.Name)
            .ShouldBe(["sample.create-item", "sample.get-item", "sample.rename-item"]);
        CatalogSnapshot unmarkedOnly = CatalogBuilder.Build([typeof(Manifest.Unmarked.Contracts.Placeholder).Assembly]);
        unmarkedOnly.Modules.ShouldBeEmpty();
        unmarkedOnly.Diagnostics.ShouldBeEmpty();
    }

    /// <summary>The canonical sample and the valid routing variants build without diagnostics.</summary>
    [Fact]
    public void ValidFixturesBuildWithoutDiagnostics()
    {
        CatalogBuilder.Build([typeof(CreateItemCommand).Assembly]).Diagnostics.ShouldBeEmpty();
        CatalogBuilder.Build([typeof(Routing.Module).Assembly]).Diagnostics.ShouldBeEmpty();
    }

    /// <summary>A marked assembly with no decorated operations remains discoverable.</summary>
    [Fact]
    public void MarkedEmptyModuleRemainsVisible()
    {
        CatalogSnapshot catalog = CatalogBuilder.Build([typeof(Manifest.MarkedEmpty.Contracts.Module).Assembly]);
        catalog.Modules.Single().Name.ShouldBe("marked-empty");
        catalog.Modules.Single().Operations.ShouldBeEmpty();
        catalog.Diagnostics.ShouldContain(diagnostic => diagnostic.Category == "empty_module"
            && diagnostic.Severity == "warning");
    }

    /// <summary>Each routing field follows its own precedence, apart from public canonical names.</summary>
    [Fact]
    public void RoutingAndAggregateSourcesAreResolvedAtBuild()
    {
        ModuleDescriptor sample = Sample();
        OperationDescriptor command = Find(sample, "sample.create-item");
        command.Routing.Domain.ShouldBe("sample");
        command.Routing.WireType.ShouldBe("create-item");
        command.AggregateIdAccessor.ShouldNotBeNull();
        using (JsonDocument payload = JsonDocument.Parse("{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\",\"Title\":\"test\"}"))
        {
            command.AggregateIdAccessor(payload.RootElement).ShouldBe("01ARZ3NDEKTSV4RRFFQ69G5FAV");
        }

        OperationDescriptor attributeCommand = Find(sample, "sample.rename-item");
        attributeCommand.Routing.WireType.ShouldBe("rename-item-wire");
        attributeCommand.Routing.Domain.ShouldBe("sample");
        using (JsonDocument payload = JsonDocument.Parse("{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\",\"Title\":\"new\"}"))
        {
            attributeCommand.AggregateIdAccessor!(payload.RootElement).ShouldBe("01ARZ3NDEKTSV4RRFFQ69G5FAV");
        }

        OperationDescriptor propertyQuery = Find(sample, "sample.get-item");
        propertyQuery.Routing.ProjectionType.ShouldBe("sample-items");
        propertyQuery.Routing.WireType.ShouldBe("get-item");
        propertyQuery.AggregateIdAccessor.ShouldNotBeNull();
        propertyQuery.AggregateIdRequired.ShouldBeFalse();

        ModuleDescriptor routing = RoutingModule();
        OperationDescriptor competing = Find(routing, "routing-fixture.competing-route");
        competing.Routing.Domain.ShouldBe("routing");
        competing.Routing.WireType.ShouldBe("interface-wire");
        Find(routing, "routing-fixture.colon-wire").Routing.WireType.ShouldBe("items:colon");

        OperationDescriptor interfaceQuery = Find(routing, "routing-fixture.interface-item");
        interfaceQuery.Routing.Domain.ShouldBe("routing");
        interfaceQuery.Routing.WireType.ShouldBe("interface-item-wire");
        interfaceQuery.Routing.ProjectionType.ShouldBe("routing-items");
        interfaceQuery.Routing.ProjectionActorType.ShouldBe("RoutingProjectionActor");
        OperationDescriptor constant = Find(routing, "routing-fixture.items-list");
        constant.Routing.WireType.ShouldBe("list-items-wire");
        constant.AggregateIdConstant.ShouldBe("routing-list");
        constant.AggregateIdAccessor.ShouldBeNull();
        constant.AggregateIdRequired.ShouldBeFalse();
        OperationDescriptor sourceFree = Find(routing, "routing-fixture.get-http2-status");
        sourceFree.AggregateIdRequired.ShouldBeTrue();
        sourceFree.AggregateIdAccessor.ShouldBeNull();
    }

    /// <summary>Module policy and property bindings remain available without head reflection.</summary>
    [Fact]
    public void ModulePolicySchemaAndEnvelopeBindingsAreFrozen()
    {
        ModuleDescriptor module = Sample();
        module.IdentifierKind.ShouldBe(IdentifierKind.Ulid);
        module.FixedTenant.ShouldBe("sample-tenant");
        module.WireTypeConvention.ShouldBe(WireTypeConvention.KebabCase);
        module.ModulePayloadOptions.IsReadOnly.ShouldBeTrue();
        Find(module, "sample.create-item").IdempotencyKeyRequired.ShouldBeFalse();

        ModuleDescriptor routing = RoutingModule();
        OperationDescriptor operation = Find(routing, "routing-fixture.envelope-item");
        operation.ContractType.ShouldBe(typeof(Routing.EnvelopeItemCommand));
        operation.Schema.Node["properties"].ShouldNotBeNull();
        operation.PropertyBindings[PropertyRole.Tenant].SerializedName.ShouldBe("tenant/~");
        operation.PropertyBindings[PropertyRole.Tenant].Pointer.ShouldBe("/tenant~1~0");
        operation.EnvelopeFilledProperties.ShouldContain("tenant/~");
        operation.EnvelopeFilledProperties.ShouldNotContain("ItemId");
        operation.IdempotencyKeyRequired.ShouldBeTrue();
        operation.Example.ShouldNotBeNull();
        PayloadValidator.Validate(operation.Schema, operation.Example!, true).IsValid.ShouldBeTrue();
        using JsonDocument payload = JsonDocument.Parse("{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\"}");
        operation.AggregateIdAccessor!(payload.RootElement).ShouldBe("01ARZ3NDEKTSV4RRFFQ69G5FAV");

        OperationDescriptor optional = Find(routing, "routing-fixture.nullable-idempotency");
        optional.PropertyBindings.ShouldContainKey(PropertyRole.IdempotencyKey);
        optional.IdempotencyKeyRequired.ShouldBeFalse();
    }

    /// <summary>String identifiers and fixed tenant resolve in an isolated marked assembly.</summary>
    [Fact]
    public void StringIdentifierKindDoesNotApplyUlidPattern()
    {
        CatalogSnapshot catalog = CatalogBuilder.Build([typeof(global::Catalog.String.Contracts.LookupQuery).Assembly]);
        ModuleDescriptor module = catalog.Modules.Single();
        module.IdentifierKind.ShouldBe(IdentifierKind.String);
        module.FixedTenant.ShouldBe("fixed-tenant");
        OperationDescriptor operation = module.Operations.Single();
        operation.Name.ShouldBe("string-fixture.lookup");
        operation.Routing.WireType.ShouldBe(typeof(global::Catalog.String.Contracts.LookupQuery).FullName);
        operation.Schema.Node["properties"]!["Key"]!["pattern"].ShouldBeNull();
        using JsonDocument payload = JsonDocument.Parse("{\"Key\":\"ordinary-id\"}");
        operation.AggregateIdAccessor!(payload.RootElement).ShouldBe("ordinary-id");
    }

    /// <summary>An explicit convention requires a wire type but keeps valid neighboring declarations.</summary>
    [Fact]
    public void ExplicitConventionExcludesOnlyTheMissingWireType()
    {
        CatalogSnapshot catalog = CatalogBuilder.Build([typeof(global::Catalog.Explicit.Contracts.ValidQuery).Assembly]);
        ModuleDescriptor module = catalog.Modules.Single();
        module.Operations.Single().ContractType.ShouldBe(typeof(global::Catalog.Explicit.Contracts.ValidQuery));
        module.Operations.Single().Routing.WireType.ShouldBe("explicit-wire");
        catalog.Diagnostics.ShouldContain(diagnostic => diagnostic.Category == "missing_routing_values"
            && diagnostic.TypeName == typeof(global::Catalog.Explicit.Contracts.MissingWireQuery).FullName);
    }

    /// <summary>The aggregate accessor uses the resolved JSON name, including escaped characters.</summary>
    [Fact]
    public void AggregateAccessorReadsMappedSerializedName()
    {
        OperationDescriptor operation = Find(RoutingModule(), "routing-fixture.renamed-aggregate");
        operation.PropertyBindings[PropertyRole.AggregateId].SerializedName.ShouldBe("aggregate/~id");
        operation.PropertyBindings[PropertyRole.AggregateId].Pointer.ShouldBe("/aggregate~1~0id");
        using JsonDocument payload = JsonDocument.Parse("{\"aggregate/~id\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\"}");
        operation.AggregateIdAccessor!(payload.RootElement).ShouldBe("01ARZ3NDEKTSV4RRFFQ69G5FAV");
    }

    /// <summary>Each invalid declaration is excluded with its own diagnostic category.</summary>
    /// <param name="contractType">The invalid contract type.</param>
    /// <param name="category">The expected diagnostic category.</param>
    [Theory]
    [InlineData(typeof(Invalid.AbstractOperationQuery), "invalid_operation_declaration")]
    [InlineData(typeof(Invalid.BadNameQuery), "invalid_operation_name")]
    [InlineData(typeof(Invalid.ColonWireQuery), "invalid_routing_value")]
    [InlineData(typeof(Invalid.ConflictingEnvelopeCommand), "conflicting_property_roles")]
    [InlineData(typeof(Invalid.ConflictingRoleCommand), "tenant_is_aggregate_id")]
    [InlineData(typeof(Invalid.DoublyDecoratedOperation), "conflicting_operation_kinds")]
    [InlineData(typeof(Invalid.DualAggregateQuery), "ambiguous_aggregate_id")]
    [InlineData(typeof(Invalid.DuplicateSecondQuery), "duplicate_operation_name")]
    [InlineData(typeof(Invalid.ExtensionDataCommand), "invalid_schema")]
    [InlineData(typeof(Invalid.GenericOperationQuery<>), "invalid_operation_declaration")]
    [InlineData(typeof(Invalid.InvalidConstantQuery), "invalid_routing_value")]
    [InlineData(typeof(Invalid.InvalidExampleQuery), "invalid_example")]
    [InlineData(typeof(Invalid.InvalidIdentifierCommand), "invalid_identifier_type")]
    [InlineData(typeof(Invalid.InvalidProjectionQuery), "invalid_routing_value")]
    [InlineData(typeof(Invalid.InvalidRoleCommand), "invalid_property_reference")]
    [InlineData(typeof(Invalid.InvalidRoutingQuery), "invalid_routing_value")]
    [InlineData(typeof(Invalid.MissingDescriptionQuery), "missing_description")]
    [InlineData(typeof(Invalid.MissingProjectionQuery), "missing_routing_values")]
    [InlineData(typeof(Invalid.NoAggregateCommand), "missing_routing_values")]
    [InlineData(typeof(Invalid.WhitespaceProjectionActorQuery), "invalid_routing_value")]
    public void InvalidOperationIsExcludedWithItsCategory(Type contractType, string category)
    {
        CatalogSnapshot catalog = CatalogBuilder.Build([typeof(Invalid.Module).Assembly]);
        catalog.Modules.Single().Operations.ShouldNotContain(operation => operation.ContractType == contractType);
        catalog.Diagnostics.Where(diagnostic => diagnostic.TypeName == contractType.FullName)
            .Select(diagnostic => (diagnostic.Category, diagnostic.Severity))
            .ShouldBe([(category, "error")]);
    }

    /// <summary>Invalid declarations do not hide the valid first duplicate or add unexplained diagnostics.</summary>
    [Fact]
    public void InvalidOperationsAreExcludedWithoutHidingValidOnes()
    {
        CatalogSnapshot catalog = CatalogBuilder.Build([typeof(Invalid.Module).Assembly]);
        catalog.Modules.Single().Operations.Select(operation => operation.ContractType)
            .ShouldBe([typeof(Invalid.DuplicateFirstQuery)]);
        catalog.Diagnostics.Count.ShouldBe(20);
    }

    /// <summary>An invalid module marker excludes the whole module with a diagnostic.</summary>
    /// <param name="name">The module name.</param>
    /// <param name="description">The module description.</param>
    /// <param name="identifierKind">The raw identifier kind.</param>
    /// <param name="convention">The raw wire type convention.</param>
    /// <param name="fixedTenant">The fixed tenant, if any.</param>
    /// <param name="category">The expected diagnostic category.</param>
    [Theory]
    [InlineData("Bad_Name", "Invalid name.", 0, 2, null, "invalid_module_declaration")]
    [InlineData("-leading", "Invalid name.", 0, 2, null, "invalid_module_declaration")]
    [InlineData("blank-description", "   ", 0, 2, null, "invalid_module_declaration")]
    [InlineData("bad-kind", "Unknown identifier kind.", 99, 2, null, "invalid_module_declaration")]
    [InlineData("bad-convention", "Unknown convention.", 0, 99, null, "invalid_module_declaration")]
    [InlineData("bad-tenant", "Invalid fixed tenant.", 0, 2, "Bad Tenant", "invalid_routing_value")]
    public void InvalidModuleMarkerExcludesTheModule(string name, string description, int identifierKind, int convention,
        string? fixedTenant, string category)
    {
        const string assemblyName = "InvalidMarker.Contracts";
        AssemblyBuilder assembly = AssemblyBuilder.DefineDynamicAssembly(new AssemblyName(assemblyName), AssemblyBuilderAccess.Run);
        ConstructorInfo constructor = typeof(HexalithModuleAttribute).GetConstructor(
            [typeof(string), typeof(string), typeof(IdentifierKind)])!;
        assembly.SetCustomAttribute(new CustomAttributeBuilder(constructor, [name, description, (IdentifierKind)identifierKind],
            [
                typeof(HexalithModuleAttribute).GetProperty(nameof(HexalithModuleAttribute.WireTypeConvention))!,
                typeof(HexalithModuleAttribute).GetProperty(nameof(HexalithModuleAttribute.FixedTenant))!,
            ],
            [(WireTypeConvention)convention, fixedTenant]));

        CatalogSnapshot catalog = CatalogBuilder.Build([assembly]);

        catalog.Modules.ShouldBeEmpty();
        catalog.Diagnostics.Select(diagnostic => (diagnostic.TypeName, diagnostic.Category, diagnostic.Severity))
            .ShouldBe([(assemblyName, category, "error")]);
    }

    /// <summary>The first declaration in sorted assembly order survives a duplicate module name.</summary>
    [Fact]
    public void FirstModuleDeclarationSurvivesDuplicateName()
    {
        AssemblyBuilder duplicate = AssemblyBuilder.DefineDynamicAssembly(
            new AssemblyName("ZZDuplicateSample.Contracts"), AssemblyBuilderAccess.Run);
        ConstructorInfo constructor = typeof(HexalithModuleAttribute).GetConstructor(
            [typeof(string), typeof(string), typeof(IdentifierKind)])!;
        duplicate.SetCustomAttribute(new CustomAttributeBuilder(constructor,
            ["sample", "Later duplicate sample module.", IdentifierKind.Ulid]));
        Assembly sample = typeof(CreateItemCommand).Assembly;

        CatalogSnapshot first = CatalogBuilder.Build([duplicate, sample]);
        CatalogSnapshot reversed = CatalogBuilder.Build([sample, duplicate]);

        first.Modules.Single().Name.ShouldBe("sample");
        first.Modules.Single().Operations.ShouldContain(operation => operation.Name == "sample.create-item");
        first.Diagnostics.ShouldContain(diagnostic => diagnostic.Category == "duplicate_module"
            && diagnostic.TypeName == "ZZDuplicateSample.Contracts" && diagnostic.Severity == "error");
        JsonSerializer.Serialize(reversed, McpCliJson.Result)
            .ShouldBe(JsonSerializer.Serialize(first, McpCliJson.Result));
    }

    /// <summary>Two distinct assemblies with the same identity have order-independent precedence.</summary>
    [Fact]
    public void SameIdentityAssembliesUseStableModuleTieBreak()
    {
        AssemblyBuilder one = MarkedDynamicModule("SameIdentity.Contracts", "First content");
        AssemblyBuilder two = MarkedDynamicModule("SameIdentity.Contracts", "Second content");
        one.FullName.ShouldBe(two.FullName);
        one.ManifestModule.ModuleVersionId.ShouldNotBe(two.ManifestModule.ModuleVersionId);

        CatalogSnapshot forward = CatalogBuilder.Build([one, two]);
        CatalogSnapshot reverse = CatalogBuilder.Build([two, one]);

        string expectedDescription = one.ManifestModule.ModuleVersionId.CompareTo(two.ManifestModule.ModuleVersionId) < 0
            ? "First content" : "Second content";
        forward.Modules.Single().Description.ShouldBe(expectedDescription);
        forward.Diagnostics.Count(diagnostic => diagnostic.Category == "duplicate_module").ShouldBe(1);
        JsonSerializer.Serialize(reverse, McpCliJson.Result)
            .ShouldBe(JsonSerializer.Serialize(forward, McpCliJson.Result));
    }

    /// <summary>Result serialization is byte-identical across repeated and reordered manifests.</summary>
    [Fact]
    public void CanonicalSerializationIsIndependentOfAssemblyInputOrder()
    {
        Assembly[] assemblies = [typeof(CreateItemCommand).Assembly, typeof(global::Catalog.String.Contracts.LookupQuery).Assembly,
            typeof(Routing.Module).Assembly, typeof(Invalid.Module).Assembly, typeof(Manifest.Unmarked.Contracts.Placeholder).Assembly];
        string first = JsonSerializer.Serialize(CatalogBuilder.Build(assemblies), McpCliJson.Result);
        string second = JsonSerializer.Serialize(CatalogBuilder.Build(assemblies.Reverse().ToArray()), McpCliJson.Result);
        second.ShouldBe(first);
    }

    private static ModuleDescriptor Sample() => CatalogBuilder.Build([typeof(CreateItemCommand).Assembly]).Modules.Single();

    private static ModuleDescriptor RoutingModule() => CatalogBuilder.Build([typeof(Routing.Module).Assembly]).Modules.Single();

    private static OperationDescriptor Find(ModuleDescriptor module, string name)
        => module.Operations.Single(operation => operation.Name == name);

    private static AssemblyBuilder MarkedDynamicModule(string assemblyName, string description)
    {
        AssemblyBuilder assembly = AssemblyBuilder.DefineDynamicAssembly(new AssemblyName(assemblyName), AssemblyBuilderAccess.Run);
        ConstructorInfo constructor = typeof(HexalithModuleAttribute).GetConstructor(
            [typeof(string), typeof(string), typeof(IdentifierKind)])!;
        assembly.SetCustomAttribute(new CustomAttributeBuilder(constructor, ["same-identity", description, IdentifierKind.String]));
        return assembly;
    }
}
