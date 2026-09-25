namespace Hexalith.McpCli.Core.Schema;

/// <summary>Names a declared top-level operation property role.</summary>
public enum PropertyRole
{
    /// <summary>The aggregate identifier source.</summary>
    AggregateId,

    /// <summary>The envelope tenant.</summary>
    Tenant,

    /// <summary>The resolved correlation identifier.</summary>
    Correlation,

    /// <summary>The caller-supplied idempotency key.</summary>
    IdempotencyKey,

    /// <summary>The operator actor.</summary>
    Actor,
}
