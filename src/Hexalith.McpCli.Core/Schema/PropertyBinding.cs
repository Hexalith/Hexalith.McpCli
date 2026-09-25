using System.Reflection;
using System.Text.Json.Serialization.Metadata;

namespace Hexalith.McpCli.Core.Schema;

/// <summary>Preserves a declared property role and its effective serialized location.</summary>
/// <param name="Role">The declared role.</param>
/// <param name="ClrProperty">The exact CLR property.</param>
/// <param name="SerializedName">The name in module payload JSON.</param>
/// <param name="Pointer">The escaped RFC 6901 pointer.</param>
/// <param name="Metadata">The effective serialization metadata.</param>
public sealed record PropertyBinding(
    PropertyRole Role,
    PropertyInfo ClrProperty,
    string SerializedName,
    string Pointer,
    JsonPropertyInfo Metadata);
