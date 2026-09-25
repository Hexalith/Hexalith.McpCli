using System.Text.Json;
using Shouldly;
using System.Text.Json.Nodes;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Core.Schema;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Sample.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Verifies canonical schema derivation and shared validation.</summary>
public sealed class SchemaTests
{
    /// <summary>Tests mixed members, nested closure, descriptions, and get-only exclusion.</summary>
    [Fact]
    public void MixedMembersFollowEffectiveJsonMetadata()
    {
        JsonSerializerOptions options = TestOptions();
        DerivedSchema derived = SchemaDeriver.Derive(typeof(MixedCommand), options, IdentifierKind.String, true);
        JsonObject root = (JsonObject)derived.Node;
        JsonObject properties = (JsonObject)root["properties"]!;

        root["type"]!.GetValue<string>().ShouldBe("object");
        root["additionalProperties"]!.GetValue<bool>().ShouldBeFalse();
        properties.ContainsKey("Name").ShouldBeTrue();
        properties.ContainsKey("Derived").ShouldBeFalse();
        properties["Name"]!["description"]!.GetValue<string>().ShouldBe("The constructor-bound name.");
        properties["Nested"]!["properties"]!["Count"]!["description"]!.GetValue<string>().ShouldBe("The count inside a nested value.");
        properties["Nested"]!["additionalProperties"]!.GetValue<bool>().ShouldBeFalse();
        properties["Items"]!["items"]!["additionalProperties"]!.GetValue<bool>().ShouldBeFalse();
        properties["Optional"]!["type"]!.ToJsonString().ShouldContain("null");
        root["required"]!.ToJsonString().ShouldContain("Required");
        root["required"]!.ToJsonString().ShouldContain("Name");
        PayloadValidator.Validate(derived, "{\"Name\":\"x\",\"Nested\":{\"Count\":1},\"Items\":[],\"Required\":\"r\",\"Mode\":1,\"tenant/~\":\"tenant\"}", true).IsValid.ShouldBeTrue();
    }

    /// <summary>Tests an explicit getter-only constructor binding and an ignored computed getter.</summary>
    [Fact]
    public void ConstructorBoundGetterRemainsInput()
    {
        DerivedSchema schema = SchemaDeriver.Derive(typeof(CtorBoundCommand), TestOptions(), IdentifierKind.String, true);
        JsonObject properties = (JsonObject)schema.Node["properties"]!;
        properties.ContainsKey("Value").ShouldBeTrue();
        properties.ContainsKey("Length").ShouldBeFalse();
        properties["Value"]!["description"]!.GetValue<string>().ShouldBe("The constructor-bound input.");
        PayloadValidator.Validate(schema, "{\"Value\":\"okay\"}", true).IsValid.ShouldBeTrue();
    }

    /// <summary>Tests provider caching and canonical non-converter settings.</summary>
    [Fact]
    public void ProviderIsReadOnceAndOnlyConvertersAreCopied()
    {
        JsonSerializerOptions first = TestOptions();
        JsonSerializerOptions second = TestOptions();
        ReferenceEquals(first, second).ShouldBeTrue();
        FixtureSerializerOptions.ReadCount.ShouldBe(1);
        first.IsReadOnly.ShouldBeTrue();
        first.PropertyNamingPolicy.ShouldBeNull();
        first.PropertyNameCaseInsensitive.ShouldBeFalse();
        first.DefaultIgnoreCondition.ShouldBe(System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull);
        first.UnmappedMemberHandling.ShouldBe(System.Text.Json.Serialization.JsonUnmappedMemberHandling.Disallow);
        first.Converters[0].ShouldBeOfType<SampleItemIdConverter>();
        first.Converters[1].ShouldBeOfType<NumericIdentifierConverter>();
        first.Converters[2].ShouldBeOfType<System.Text.Json.Serialization.JsonNumberEnumConverter<StatusValue>>();
        first.TypeInfoResolver.ShouldNotBeSameAs(FixtureSerializerOptions.Resolver);
        JsonSerializer.Serialize(new { Value = (string?)null }, first).ShouldBe("{}");
        McpCliJson.Result.PropertyNamingPolicy.ShouldBe(JsonNamingPolicy.CamelCase);
        McpCliJson.Result.WriteIndented.ShouldBeTrue();
        JsonSerializer.Serialize(StatusValue.Complete, McpCliJson.Result).ShouldBe("\"complete\"");
        Should.Throw<JsonException>(() => JsonSerializer.Deserialize<MixedCommand>("{\"unknown\":1}", first));
    }

    /// <summary>Tests declaration-only identifier patterns for both Module kinds.</summary>
    [Theory]
    [InlineData(IdentifierKind.Ulid, true)]
    [InlineData(IdentifierKind.String, false)]
    public void IdentifiersFollowDeclaredKind(IdentifierKind kind, bool expectPattern)
    {
        DerivedSchema derived = SchemaDeriver.Derive(typeof(IdentifierCommand), TestOptions(), kind, true,
            new Dictionary<PropertyRole, string?> { [PropertyRole.AggregateId] = nameof(IdentifierCommand.ItemKey) });
        JsonObject properties = (JsonObject)derived.Node["properties"]!;
        (properties["ItemKey"]!["pattern"] is not null).ShouldBe(expectPattern);
        properties["Tracking"]!["pattern"]!.GetValue<string>().ShouldBe(SchemaDeriver.UlidPattern);
        properties["ExternalId"]!["type"]!.ToJsonString().ShouldContain("integer");
        properties["ExternalId"]!["pattern"].ShouldBeNull();
        Should.Throw<ArgumentException>(() => SchemaDeriver.Derive(typeof(InvalidIdentifierCommand), TestOptions(), kind, true));
    }

    /// <summary>Rejects opaque converters that emit numbers for declared identifiers.</summary>
    [Theory]
    [InlineData(IdentifierKind.Ulid)]
    [InlineData(IdentifierKind.String)]
    public void NumericConverterCannotBecomeStringIdentifier(IdentifierKind kind)
    {
        JsonSerializerOptions options = TestOptions();
        JsonSerializer.Serialize(new NumericIdentifier(1), options).ShouldBe("1");
        Should.Throw<ArgumentException>(() => SchemaDeriver.Derive(typeof(ConvertedNumericIdentifierCommand), options, kind, true));
        options.GetTypeInfo(typeof(PropertyConvertedNumericIdentifierCommand)).Properties.Single().CustomConverter.ShouldNotBeNull();
        Should.Throw<ArgumentException>(() => SchemaDeriver.Derive(typeof(PropertyConvertedNumericIdentifierCommand), options, kind, true));
        Should.Throw<ArgumentException>(() => SchemaDeriver.Derive(typeof(ConvertedNumericAggregateCommand), options, kind, true,
            new Dictionary<PropertyRole, string?> { [PropertyRole.AggregateId] = nameof(ConvertedNumericAggregateCommand.Source) }));
    }

    /// <summary>Rejects a newline after a ULID even though a dollar-anchored pattern alone accepts it.</summary>
    [Fact]
    public void UlidRequiresExactlyTwentySixCharacters()
    {
        DerivedSchema schema = SchemaDeriver.Derive(typeof(IdentifierCommand), TestOptions(), IdentifierKind.Ulid, true);
        JsonNode item = schema.Node["properties"]!["ItemKey"]!;
        item["minLength"]!.GetValue<int>().ShouldBe(26);
        item["maxLength"]!.GetValue<int>().ShouldBe(26);
        PayloadValidator.Validate(schema, "{\"ItemKey\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\\n\"}", true)
            .Violations.Select(violation => violation.Path).ShouldContain("/ItemKey");
    }

    /// <summary>Rejects unknown Module identifier kinds before exporting a schema.</summary>
    [Fact]
    public void UnknownIdentifierKindIsRejected()
    {
        Should.Throw<ArgumentOutOfRangeException>(() => SchemaDeriver.Derive(
            typeof(IdentifierCommand), TestOptions(), (IdentifierKind)99, true));
    }

    /// <summary>Tests exact role mapping, pointer escaping, and ordinary similar names.</summary>
    [Fact]
    public void MappedEnvelopeRolesAreOptionalReadOnlyAndEscaped()
    {
        DerivedSchema derived = SchemaDeriver.Derive(typeof(MixedCommand), TestOptions(), IdentifierKind.String, true,
            new Dictionary<PropertyRole, string?>
            {
                [PropertyRole.Tenant] = nameof(MixedCommand.Tenant),
                [PropertyRole.Correlation] = nameof(MixedCommand.Correlation),
                [PropertyRole.IdempotencyKey] = nameof(MixedCommand.IdempotencyKey),
                [PropertyRole.Actor] = nameof(MixedCommand.Actor),
            });
        PropertyBinding binding = derived.Bindings[PropertyRole.Tenant];
        binding.SerializedName.ShouldBe("tenant/~");
        binding.Pointer.ShouldBe("/tenant~1~0");
        JsonObject properties = (JsonObject)derived.Node["properties"]!;
        properties["tenant/~"]!["readOnly"]!.GetValue<bool>().ShouldBeTrue();
        properties["TenantId"]!["readOnly"].ShouldBeNull();
        foreach (string name in new[] { "Correlation", "IdempotencyKey", "Actor" })
        {
            properties[name]!["readOnly"]!.GetValue<bool>().ShouldBeTrue();
        }
        derived.Node["required"]!.ToJsonString().ShouldNotContain("tenant/~");
        PayloadValidator.Validate(derived, "{\"Name\":\"x\",\"Nested\":{\"Count\":1},\"Items\":[],\"Required\":\"r\",\"tenant/~\":4}", true).Violations.Select(violation => violation.Path).ShouldContain("/tenant~1~0");
        Should.Throw<ArgumentException>(() => SchemaDeriver.Derive(typeof(MixedCommand), TestOptions(), IdentifierKind.String, true,
            new Dictionary<PropertyRole, string?> { [PropertyRole.Tenant] = nameof(MixedCommand.Derived) }));
        Should.Throw<ArgumentException>(() => SchemaDeriver.Derive(typeof(MixedCommand), TestOptions(), IdentifierKind.String, true,
            new Dictionary<PropertyRole, string?> { [PropertyRole.Tenant] = "tenant/~" }));
        Should.Throw<ArgumentException>(() => SchemaDeriver.Derive(typeof(MixedCommand), TestOptions(), IdentifierKind.String, true,
            new Dictionary<PropertyRole, string?>
            {
                [PropertyRole.Tenant] = nameof(MixedCommand.Tenant),
                [PropertyRole.AggregateId] = nameof(MixedCommand.Tenant),
            }));
    }

    /// <summary>Tests aggregate mapping independent of attributes and rejects numeric sources.</summary>
    [Theory]
    [InlineData(IdentifierKind.Ulid, true)]
    [InlineData(IdentifierKind.String, false)]
    public void AggregateMappingAloneControlsIdentifierKind(IdentifierKind kind, bool expectPattern)
    {
        DerivedSchema schema = SchemaDeriver.Derive(typeof(AggregateOnlyCommand), TestOptions(), kind, true,
            new Dictionary<PropertyRole, string?> { [PropertyRole.AggregateId] = nameof(AggregateOnlyCommand.Source) });
        JsonObject properties = (JsonObject)schema.Node["properties"]!;
        (properties["Source"]!["pattern"] is not null).ShouldBe(expectPattern);
        properties["OtherId"]!["type"]!.ToJsonString().ShouldContain("integer");
        Should.Throw<ArgumentException>(() => SchemaDeriver.Derive(typeof(AggregateOnlyCommand), TestOptions(), kind, true,
            new Dictionary<PropertyRole, string?> { [PropertyRole.AggregateId] = nameof(AggregateOnlyCommand.OtherId) }));
    }

    /// <summary>Allows a setter-only envelope role while aggregate sources still require a getter.</summary>
    [Fact]
    public void SetterOnlyEnvelopeRoleIsBindable()
    {
        DerivedSchema schema = SchemaDeriver.Derive(typeof(SetterOnlyEnvelopeCommand), TestOptions(), IdentifierKind.String, true,
            new Dictionary<PropertyRole, string?> { [PropertyRole.Tenant] = nameof(SetterOnlyEnvelopeCommand.Tenant) });
        schema.Bindings[PropertyRole.Tenant].Pointer.ShouldBe("/tenant~1~0");
        schema.Node["properties"]!["tenant/~"]!["readOnly"]!.GetValue<bool>().ShouldBeTrue();
        schema.Node["properties"]!["tenant/~"]!["description"]!.GetValue<string>().ShouldBe("The tenant supplied by the envelope.");
        Should.Throw<ArgumentException>(() => SchemaDeriver.Derive(typeof(SetterOnlyEnvelopeCommand), TestOptions(), IdentifierKind.String, true,
            new Dictionary<PropertyRole, string?> { [PropertyRole.AggregateId] = nameof(SetterOnlyEnvelopeCommand.Tenant) }));
    }

    /// <summary>Rejects an explicit blank role but permits an absent optional role.</summary>
    [Fact]
    public void BlankRoleNameIsInvalid()
    {
        Should.Throw<ArgumentException>(() => SchemaDeriver.Derive(typeof(MixedCommand), TestOptions(), IdentifierKind.String, true,
            new Dictionary<PropertyRole, string?> { [PropertyRole.Tenant] = "  " }));
        DerivedSchema schema = SchemaDeriver.Derive(typeof(MixedCommand), TestOptions(), IdentifierKind.String, true,
            new Dictionary<PropertyRole, string?> { [PropertyRole.Tenant] = null });
        schema.Bindings.ShouldBeEmpty();
    }

    /// <summary>Rejects unsupported converter-backed fields even when an envelope role names them.</summary>
    [Fact]
    public void OrdinaryOpaqueMemberIsRejected()
    {
        Should.Throw<NotSupportedException>(() => SchemaDeriver.Derive(typeof(OrdinaryOpaqueCommand), TestOptions(), IdentifierKind.String, true))
            .Message.ShouldContain("Opaque serialized member");
        Should.Throw<NotSupportedException>(() => SchemaDeriver.Derive(typeof(OrdinaryOpaqueCommand), TestOptions(), IdentifierKind.String, true,
            new Dictionary<PropertyRole, string?> { [PropertyRole.Tenant] = nameof(OrdinaryOpaqueCommand.Value) }))
            .Message.ShouldContain("Opaque serialized member");
    }

    /// <summary>Rejects an unconstrained schema for a converter-backed Query root.</summary>
    [Fact]
    public void OpaqueQueryRootIsRejected()
    {
        JsonSerializer.Serialize(new OpaqueQueryPayload("value"), TestOptions()).ShouldBe("\"value\"");
        Should.Throw<NotSupportedException>(() => SchemaDeriver.Derive(typeof(OpaqueQueryPayload), TestOptions(), IdentifierKind.String, false))
            .Message.ShouldContain("Opaque payload root");
    }

    /// <summary>Rejects extension-data contracts at the root and inside nested values.</summary>
    [Fact]
    public void ExtensionDataIsRejectedAtEveryDepth()
    {
        Should.Throw<NotSupportedException>(() => SchemaDeriver.Derive(typeof(ExtensionDataCommand), TestOptions(), IdentifierKind.String, true))
            .Message.ShouldContain("extension data");
        Should.Throw<NotSupportedException>(() => SchemaDeriver.Derive(typeof(ExtensionContainerCommand), TestOptions(), IdentifierKind.String, true))
            .Message.ShouldContain("extension data");
    }

    /// <summary>Rejects polymorphic contracts at the root and inside nested values.</summary>
    [Fact]
    public void PolymorphismIsRejectedAtEveryDepth()
    {
        Should.Throw<NotSupportedException>(() => SchemaDeriver.Derive(typeof(PolymorphicBase), TestOptions(), IdentifierKind.String, true))
            .Message.ShouldContain("Polymorphic");
        Should.Throw<NotSupportedException>(() => SchemaDeriver.Derive(typeof(PolymorphicContainerCommand), TestOptions(), IdentifierKind.String, true))
            .Message.ShouldContain("Polymorphic");
    }

    /// <summary>Verifies canonical enum deserialization accepts only named values.</summary>
    [Fact]
    public void CanonicalEnumConverterRejectsIntegerInput()
    {
        DerivedSchema schema = SchemaDeriver.Derive(typeof(EnumOnlyCommand), McpCliJson.Payload, IdentifierKind.String, true);
        PayloadValidator.Validate(schema, "{\"Mode\":1}", true).Violations.Select(violation => violation.Path).ShouldContain("/Mode");
        Should.Throw<JsonException>(() => JsonSerializer.Deserialize<EnumOnlyCommand>("{\"Mode\":1}", McpCliJson.Payload));
        JsonSerializer.Deserialize<EnumOnlyCommand>("{\"Mode\":\"Complete\"}", McpCliJson.Payload)!.Mode.ShouldBe(StatusValue.Complete);
    }

    /// <summary>Tests invalid provider declarations and schema snapshot isolation.</summary>
    [Fact]
    public void InvalidProviderCannotYieldOptionsAndSchemaSnapshotStaysConsistent()
    {
        Should.Throw<ArgumentException>(() => McpCliJson.ForModule(typeof(string).Assembly,
            new HexalithModuleAttribute("invalid", "Invalid provider.", IdentifierKind.String)
            {
                SerializerOptionsProvider = typeof(FixtureSerializerOptions),
            }));
        DerivedSchema schema = SchemaDeriver.Derive(typeof(AggregateOnlyCommand), TestOptions(), IdentifierKind.String, true);
        ((JsonObject)schema.Node)["additionalProperties"] = true;
        PayloadValidator.Validate(schema, "{\"Source\":\"x\",\"Unknown\":1}", true).IsValid.ShouldBeFalse();
        schema.Node["additionalProperties"]!.GetValue<bool>().ShouldBeFalse();
    }

    /// <summary>Tests that one stored schema validates examples and payloads with all locations.</summary>
    [Fact]
    public void SharedSchemaReportsAllViolationsAndMalformedRoot()
    {
        DerivedSchema schema = SchemaDeriver.Derive(typeof(RenameItemCommand),
            McpCliJson.ForModule(typeof(RenameItemCommand).Assembly,
                typeof(RenameItemCommand).Assembly.GetCustomAttributes(typeof(HexalithModuleAttribute), false).Cast<HexalithModuleAttribute>().Single()),
            IdentifierKind.Ulid, true);
        string good = "{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\",\"Title\":\"New\"}";
        PayloadValidator.Validate(schema, good, true).IsValid.ShouldBeTrue();
        string bad = "{\"ItemId\":\"bad\",\"Title\":4,\"Extra\":1}";
        PayloadValidationResult example = PayloadValidator.Validate(schema, bad, true);
        PayloadValidationResult payload = PayloadValidator.Validate(schema, JsonDocument.Parse(bad).RootElement, true);
        example.IsValid.ShouldBeFalse();
        example.Violations.Select(violation => violation.Path).ShouldBe(payload.Violations.Select(violation => violation.Path));
        example.Violations.Select(violation => violation.Path).ShouldContain("/ItemId");
        example.Violations.Select(violation => violation.Path).ShouldContain("/Title");
        PayloadValidator.Validate(schema, "{", true).Violations.Single().Path.ShouldBe("/");
        PayloadValidator.Validate(schema, "null", true).Violations.Single().Path.ShouldBe("/");
        PayloadValidator.Validate(schema, "{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\"}", true)
            .Violations.ShouldContain(violation => violation.Path == "/" && violation.Message.Contains("Title", StringComparison.Ordinal));
        PayloadValidator.Validate(schema, default(JsonElement), false).Violations.Single().Path.ShouldBe("/");
    }

    private static JsonSerializerOptions TestOptions() => McpCliJson.ForModule(
        typeof(SchemaTests).Assembly,
        new HexalithModuleAttribute("test", "Test module.", IdentifierKind.Ulid)
        {
            SerializerOptionsProvider = typeof(FixtureSerializerOptions),
        });
}
