namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Distinguishes a gateway write from a read.</summary>
public enum OperationKind
{
    /// <summary>A gateway command.</summary>
    Command,

    /// <summary>A gateway query.</summary>
    Query,
}
