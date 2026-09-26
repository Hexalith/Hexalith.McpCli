using System.Reflection;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>A marked Contracts assembly whose types fail to load with one loader exception.</summary>
public sealed class UnloadableContractsAssembly : Assembly
{
    /// <summary>The message carried by the loader exception.</summary>
    public const string LoaderMessage = "Could not load dependency Missing.Dependency.";

    private const string Name = "Unloadable.Contracts";

    private readonly HexalithModuleAttribute _marker = new("unloadable", "Unloadable module.", IdentifierKind.String);

    /// <inheritdoc/>
    public override string FullName => Name;

    /// <inheritdoc/>
    public override Module ManifestModule => typeof(UnloadableContractsAssembly).Module;

    /// <inheritdoc/>
    public override AssemblyName GetName(bool copiedName) => new(Name);

    /// <inheritdoc/>
    public override object[] GetCustomAttributes(bool inherit) => new Attribute[] { _marker };

    /// <inheritdoc/>
    public override object[] GetCustomAttributes(Type attributeType, bool inherit)
        => attributeType.IsInstanceOfType(_marker) ? new Attribute[] { _marker } : Array.Empty<Attribute>();

    /// <inheritdoc/>
    public override Type[] GetTypes()
        => throw new ReflectionTypeLoadException([null], [new TypeLoadException(LoaderMessage)]);

    /// <inheritdoc/>
    public override bool Equals(object? o) => ReferenceEquals(this, o);

    /// <inheritdoc/>
    public override int GetHashCode() => System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(this);
}
