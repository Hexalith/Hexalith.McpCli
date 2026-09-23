using System.Reflection;
using System.Text.Json;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Sample.Contracts;
using Shouldly;

namespace Hexalith.McpCli.Abstractions.Tests;

/// <summary>
/// Verifies the synthetic module's public decoration contract.
/// </summary>
public sealed class SampleContractsTests
{
    /// <summary>Verifies the fixture declares exactly one module of the required kind.</summary>
    [Fact]
    public void SampleDeclaresOneUlidModule()
    {
        HexalithModuleAttribute module = typeof(CreateItemCommand).Assembly
            .GetCustomAttributes<HexalithModuleAttribute>().Single();

        module.Name.ShouldBe("sample");
        module.IdentifierKind.ShouldBe(IdentifierKind.Ulid);
        module.WireTypeConvention.ShouldBe(WireTypeConvention.KebabCase);
        module.SerializerOptionsProvider.ShouldBe(typeof(SampleSerializerOptions));
    }

    /// <summary>Verifies the fixture provides both command routing forms and one query.</summary>
    [Fact]
    public void SampleDeclaresBothCommandRoutingFormsAndAQuery()
    {
        typeof(ICommandContract).IsAssignableFrom(typeof(CreateItemCommand)).ShouldBeTrue();
        typeof(CreateItemCommand).GetCustomAttribute<HexalithCommandAttribute>()!.Domain.ShouldBeNull();
        typeof(RenameItemCommand).GetCustomAttribute<HexalithCommandAttribute>()!.Domain.ShouldBe("sample");
        typeof(RenameItemCommand).GetCustomAttribute<HexalithCommandAttribute>()!.AggregateIdProperty.ShouldBe(nameof(RenameItemCommand.ItemId));
        typeof(GetItemQuery).GetCustomAttribute<HexalithQueryAttribute>()!.ProjectionType.ShouldBe("sample-items");
        typeof(RenameItemCommand).GetProperty(nameof(RenameItemCommand.ItemId))!
            .IsDefined(typeof(HexalithIdentifierAttribute)).ShouldBeTrue();
    }

    /// <summary>Verifies the declared provider actually serializes the value-object identifier as a string.</summary>
    [Fact]
    public void SampleIdentifierUsesModuleConverter()
    {
        var identifier = new SampleItemId("01ARZ3NDEKTSV4RRFFQ69G5FAV");

        string json = JsonSerializer.Serialize(identifier, SampleSerializerOptions.Options);

        json.ShouldBe("\"01ARZ3NDEKTSV4RRFFQ69G5FAV\"");
        JsonSerializer.Deserialize<SampleItemId>(json, SampleSerializerOptions.Options).ShouldBe(identifier);
    }

    /// <summary>Rejects the default value-object identifier instead of emitting JSON null.</summary>
    [Fact]
    public void SampleIdentifierRejectsDefaultValue()
    {
        Should.Throw<JsonException>(() => JsonSerializer.Serialize(default(SampleItemId), SampleSerializerOptions.Options));
        Should.Throw<JsonException>(() => JsonSerializer.Deserialize<SampleItemId>("null", SampleSerializerOptions.Options));
    }
}
