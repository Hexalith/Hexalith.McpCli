using System.Text.Json;
using Hexalith.McpCli.Core.Serialization;

namespace Hexalith.McpCli.Mcp;

/// <summary>Adapts Core's canonical result document contract to MCP tool advertisements.</summary>
internal static class McpOutputSchema
{
    /// <summary>Builds the success/error union advertised by a generic tool.</summary>
    internal static JsonElement Create(Type successType) => ResultDocumentSchema.Create(successType);
}
