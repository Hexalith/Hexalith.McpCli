using System.Reflection;
using System.Reflection.Emit;
using System.Text.Json;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Schema;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Sample.Contracts;
using Shouldly;
using CatalogSnapshot = Hexalith.McpCli.Core.Catalog.Catalog;

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
            .ShouldBe(catalog.Modules.Single(module => module.Name == "sample").Operations.Select(operation => operation.Name)
                .OrderBy(name => name, StringComparer.Ordinal));
        CatalogSnapshot unmarkedOnly = CatalogBuilder.Build([typeof(Manifest.Unmarked.Contracts.Placeholder).Assembly]);
        unmarkedOnly.Modules.ShouldBeEmpty();
        unmarkedOnly.Diagnostics.ShouldBeEmpty();
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
        ModuleDescriptor module = Sample();
        OperationDescriptor command = Find(module, "sample.create-item");
        command.Routing.Domain.ShouldBe("sample");
        command.Routing.WireType.ShouldBe("create-item");
        command.AggregateIdAccessor.ShouldNotBeNull();
        using (JsonDocument payload = JsonDocument.Parse("{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\",\"Title\":\"test\"}"))
        {
            command.AggregateIdAccessor(payload.RootElement).ShouldBe("01ARZ3NDEKTSV4RRFFQ69G5FAV");
        }

        OperationDescriptor competing = Find(module, "sample.competing-route");
        competing.Routing.Domain.ShouldBe("sample");
        competing.Routing.WireType.ShouldBe("interface-wire");

        OperationDescriptor attributeCommand = Find(module, "sample.rename-item");
        attributeCommand.Routing.WireType.ShouldBe("rename-item-wire");
        attributeCommand.Routing.Domain.ShouldBe("sample");
        using (JsonDocument payload = JsonDocument.Parse("{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\",\"Title\":\"new\"}"))
        {
            attributeCommand.AggregateIdAccessor!(payload.RootElement).ShouldBe("01ARZ3NDEKTSV4RRFFQ69G5FAV");
        }

        OperationDescriptor interfaceQuery = Find(module, "sample.interface-item");
        interfaceQuery.Routing.Domain.ShouldBe("sample");
        interfaceQuery.Routing.WireType.ShouldBe("interface-item-wire");
        interfaceQuery.Routing.ProjectionType.ShouldBe("sample-items");
        interfaceQuery.Routing.ProjectionActorType.ShouldBe("SampleProjectionActor");
        Find(module, "sample.get-item").Routing.ProjectionType.ShouldBe("sample-items");
        Find(module, "sample.get-item").Routing.WireType.ShouldBe("get-item");
        OperationDescriptor constant = Find(module, "sample.items-list");
        constant.Routing.WireType.ShouldBe("list-items-wire");
        constant.AggregateIdConstant.ShouldBe("sample-list");
        constant.AggregateIdAccessor.ShouldBeNull();
        constant.AggregateIdRequired.ShouldBeFalse();
        OperationDescriptor sourceFree = Find(module, "sample.get-http2-status");
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
        OperationDescriptor operation = Find(module, "sample.envelope-item");
        operation.ContractType.ShouldBe(typeof(EnvelopeItemCommand));
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
        OperationDescriptor operation = Find(Sample(), "sample.renamed-aggregate");
        operation.PropertyBindings[PropertyRole.AggregateId].SerializedName.ShouldBe("aggregate/~id");
        operation.PropertyBindings[PropertyRole.AggregateId].Pointer.ShouldBe("/aggregate~1~0id");
        using JsonDocument payload = JsonDocument.Parse("{\"aggregate/~id\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\"}");
        operation.AggregateIdAccessor!(payload.RootElement).ShouldBe("01ARZ3NDEKTSV4RRFFQ69G5FAV");
    }

    /// <summary>Invalid declarations are isolated, with data retained for the later diagnostic policy.</summary>
    [Fact]
    public void InvalidOperationsAreExcludedWithoutHidingValidOnes()
    {
        CatalogSnapshot catalog = CatalogBuilder.Build([typeof(CreateItemCommand).Assembly]);
        ModuleDescriptor module = catalog.Modules.Single();
        module.Operations.ShouldContain(operation => operation.Name == "sample.create-item");
        module.Operations.ShouldNotContain(operation => operation.Name == "sample.no-aggregate");
        module.Operations.ShouldNotContain(operation => operation.ContractType == typeof(BadNameQuery));
        module.Operations.ShouldNotContain(operation => operation.ContractType == typeof(DoublyDecoratedOperation));
        module.Operations.ShouldNotContain(operation => operation.ContractType == typeof(InvalidExampleQuery));
        module.Operations.ShouldNotContain(operation => operation.ContractType == typeof(InvalidIdentifierCommand));
        module.Operations.ShouldNotContain(operation => operation.ContractType == typeof(InvalidRoleCommand));
        OperationDescriptor duplicate = Find(module, "sample.duplicate");
        duplicate.ContractType.ShouldBe(typeof(DuplicateFirstQuery));
        module.Operations.ShouldNotContain(operation => operation.ContractType == typeof(DuplicateSecondQuery));
        module.Operations.ShouldNotContain(operation => operation.ContractType == typeof(MissingProjectionQuery));
        module.Operations.ShouldNotContain(operation => operation.ContractType == typeof(WhitespaceProjectionActorQuery));
        string[] codes = catalog.Diagnostics.Select(diagnostic => diagnostic.Category).ToArray();
        codes.ShouldContain("missing_routing_values");
        codes.ShouldContain("ambiguous_aggregate_id");
        codes.ShouldContain("invalid_property_reference");
        codes.ShouldContain("invalid_identifier_type");
        codes.ShouldContain("conflicting_property_roles");
        codes.ShouldContain("tenant_is_aggregate_id");
        codes.ShouldContain("invalid_example");
        codes.ShouldContain("invalid_routing_value");
        codes.ShouldContain("invalid_operation_name");
        codes.ShouldContain("conflicting_operation_kinds");
        catalog.Diagnostics.Count(diagnostic => diagnostic.Category == "duplicate_operation_name").ShouldBe(1);
        catalog.Diagnostics.ShouldContain(diagnostic => diagnostic.Category == "duplicate_operation_name"
            && diagnostic.TypeName == typeof(DuplicateSecondQuery).FullName && diagnostic.Severity == "error");
        catalog.Diagnostics.ShouldContain(diagnostic => diagnostic.Category == "missing_routing_values"
            && diagnostic.TypeName == typeof(MissingProjectionQuery).FullName);
        catalog.Diagnostics.ShouldContain(diagnostic => diagnostic.Category == "invalid_routing_value"
            && diagnostic.TypeName == typeof(WhitespaceProjectionActorQuery).FullName);
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
            typeof(Manifest.Unmarked.Contracts.Placeholder).Assembly];
        string first = JsonSerializer.Serialize(CatalogBuilder.Build(assemblies), McpCliJson.Result);
        string second = JsonSerializer.Serialize(CatalogBuilder.Build(assemblies.Reverse().ToArray()), McpCliJson.Result);
        second.ShouldBe(first);
    }

    private static ModuleDescriptor Sample() => CatalogBuilder.Build([typeof(CreateItemCommand).Assembly]).Modules.Single();

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
