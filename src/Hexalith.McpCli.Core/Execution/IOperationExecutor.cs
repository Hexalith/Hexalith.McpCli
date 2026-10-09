namespace Hexalith.McpCli.Core.Execution;

/// <summary>Executes declared operations through the EventStore gateway.</summary>
public interface IOperationExecutor
{
    /// <summary>Runs one already-bound call against the shared Catalog and gateway.</summary>
    /// <param name="call">The requested command or query.</param>
    /// <param name="context">Trusted session envelope values.</param>
    /// <param name="cancellationToken">The request cancellation token.</param>
    /// <param name="beforeSubmit">Optional check immediately before the gateway request.</param>
    Task<OperationOutcome> ExecuteAsync(OperationCall call, EnvelopeContext context, CancellationToken cancellationToken = default,
        Func<CancellationToken, Task>? beforeSubmit = null);
}
