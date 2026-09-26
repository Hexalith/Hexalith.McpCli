using System.Reflection;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>A marked Contracts assembly exposing only <see cref="FaultingQuery"/>, isolated from the test assembly's option cache.</summary>
public sealed class FaultingContractsAssembly : Assembly
{
    private const string Name = "Faulting.Contracts";

    private readonly HexalithModuleAttribute _marker = new("faulting", "Faulting module.", IdentifierKind.String);

    /// <inheritdoc/>
    public override string FullName => Name;

    /// <inheritdoc/>
    public override Module ManifestModule => typeof(FaultingQuery).Module;

    /// <inheritdoc/>
    public override AssemblyName GetName(bool copiedName) => new(Name);

    /// <inheritdoc/>
    public override object[] GetCustomAttributes(bool inherit) => new Attribute[] { _marker };

    /// <inheritdoc/>
    public override object[] GetCustomAttributes(Type attributeType, bool inherit)
        => attributeType.IsInstanceOfType(_marker) ? new Attribute[] { _marker } : Array.Empty<Attribute>();

    /// <inheritdoc/>
    public override Type[] GetTypes() => [typeof(FaultingQuery)];

    /// <inheritdoc/>
    public override bool Equals(object? o) => ReferenceEquals(this, o);

    /// <inheritdoc/>
    public override int GetHashCode() => System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(this);
}
