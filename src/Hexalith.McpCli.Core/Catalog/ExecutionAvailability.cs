namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Reports whether an operation can be submitted in this session.</summary>
/// <param name="ReadOnly">Whether writes are disabled.</param>
/// <param name="HasGatewayUrl">Whether the gateway URL is configured.</param>
public sealed record ExecutionAvailability(bool ReadOnly, bool HasGatewayUrl)
{
    /// <summary>Gets the reason submission is unavailable, if any.</summary>
    public string? ReasonFor(OperationKind kind)
        => kind == OperationKind.Command && ReadOnly ? "read_only" : !HasGatewayUrl ? "configuration_invalid" : null;
}
