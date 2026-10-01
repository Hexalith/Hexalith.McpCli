using System.Reflection;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Isolates the tenant validation probe from the test assembly's cached serializer options.</summary>
public sealed class QueryValidationContractsAssembly : Assembly
{
    private const string Name = "QueryValidation.Contracts";
    private readonly HexalithModuleAttribute _marker = new("query-validation", "Query validation probes.", IdentifierKind.Ulid);

    /// <inheritdoc/>
    public override string FullName => Name;

    /// <inheritdoc/>
    public override Module ManifestModule => typeof(TenantSchemaProbeQuery).Module;

    /// <inheritdoc/>
    public override AssemblyName GetName(bool copiedName) => new(Name);

    /// <inheritdoc/>
    public override object[] GetCustomAttributes(bool inherit) => new Attribute[] { _marker };

    /// <inheritdoc/>
    public override object[] GetCustomAttributes(Type attributeType, bool inherit)
        => attributeType.IsInstanceOfType(_marker) ? new Attribute[] { _marker } : Array.Empty<Attribute>();

    /// <inheritdoc/>
    public override Type[] GetTypes() => [typeof(TenantSchemaProbeQuery)];

    /// <inheritdoc/>
    public override bool Equals(object? o) => ReferenceEquals(this, o);

    /// <inheritdoc/>
    public override int GetHashCode() => System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(this);
}
