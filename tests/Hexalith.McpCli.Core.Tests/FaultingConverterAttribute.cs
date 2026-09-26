using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Raises a non-coded exception while the Catalog resolves an operation contract.</summary>
[AttributeUsage(AttributeTargets.Property)]
public sealed class FaultingConverterAttribute : JsonConverterAttribute
{
    /// <summary>The message carried by the non-coded exception.</summary>
    public const string FaultMessage = "Simulated non-coded converter failure.";

    /// <inheritdoc/>
    public override JsonConverter? CreateConverter(Type typeToConvert) => throw new ArgumentException(FaultMessage);
}
