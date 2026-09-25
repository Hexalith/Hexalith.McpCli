using System.ComponentModel;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Describes a positional member with a parameter-targeted attribute.</summary>
/// <param name="Title">The positional title.</param>
public sealed record PositionalDescriptionCommand([Description("The positional title.")] string Title);
