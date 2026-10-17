using System.Reflection;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Supplies existing decorated fixture types to the real builder under an arbitrary module marker.</summary>
/// <param name="name">The canonical test module name.</param>
/// <param name="types">The real decorated contract types, including duplicate declarations when requested.</param>
internal sealed class InventoryCoverageContractsAssembly(string name, params Type[] types) : Assembly
{
    private readonly HexalithModuleAttribute _marker = new(name, "Inventory coverage fixture module.", IdentifierKind.String)
    {
        WireTypeConvention = WireTypeConvention.KebabCase,
    };

    /// <inheritdoc />
    public override string FullName => "InventoryCoverage.Contracts";

    /// <inheritdoc />
    public override Module ManifestModule => typeof(InventoryCoverageContractsAssembly).Module;

    /// <inheritdoc />
    public override AssemblyName GetName(bool copiedName) => new(FullName);

    /// <inheritdoc />
    public override object[] GetCustomAttributes(bool inherit) => new Attribute[] { _marker };

    /// <inheritdoc />
    public override object[] GetCustomAttributes(Type attributeType, bool inherit)
        => attributeType.IsInstanceOfType(_marker) ? new Attribute[] { _marker } : Array.Empty<Attribute>();

    /// <inheritdoc />
    public override Type[] GetTypes() => types;

    /// <inheritdoc />
    public override bool Equals(object? obj) => ReferenceEquals(this, obj);

    /// <inheritdoc />
    public override int GetHashCode() => System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(this);
}
