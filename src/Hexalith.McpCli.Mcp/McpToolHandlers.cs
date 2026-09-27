using System.Text.Json;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Microsoft.Extensions.DependencyInjection;
using ModelContextProtocol.Protocol;

namespace Hexalith.McpCli.Mcp;

/// <summary>Translates the five generic MCP tools into Catalog and executor calls.</summary>
internal static class McpToolHandlers
{
    internal static CallToolResult ListModules(IServiceProvider services)
        => Guard(() =>
        {
        CatalogLookupResult<ModulesDocument> result = services.GetRequiredService<ICatalog>().ListModules();
        return Convert(result.Document, result.Error);
        });

    internal static CallToolResult ListOperations(string module, IServiceProvider services, string? kind = null)
        => Guard(() =>
        {
        if (string.IsNullOrWhiteSpace(module))
        {
            return Convert(null, new OperationError("invalid_arguments", Argument: "module", Message: "module is required"));
        }

        if (kind is not null && kind is not ("read" or "write"))
        {
            return Convert(null, new OperationError("invalid_arguments", Argument: "kind", Message: "kind must be read or write"));
        }

        CatalogLookupResult<OperationsDocument> result = services.GetRequiredService<ICatalog>().ListOperations(module, kind);
        return Convert(result.Document, result.Error);
        });

    internal static CallToolResult DescribeOperation(string operation, IServiceProvider services)
        => Guard(() =>
        {
        if (string.IsNullOrWhiteSpace(operation))
        {
            return Convert(null, new OperationError("invalid_arguments", Argument: "operation", Message: "operation is required"));
        }

        CatalogLookupResult<OperationDescriptionDocument> result = services.GetRequiredService<ICatalog>().Describe(operation);
        return Convert(result.Document, result.Error);
        });

    internal static async Task<CallToolResult> SendCommand(string operation, string payload,
        IServiceProvider services, CancellationToken cancellationToken, string? tenant = null,
        string? aggregateId = null, string? correlationId = null, string? idempotencyKey = null,
        IReadOnlyDictionary<string, string>? extensions = null)
        => await GuardAsync(async () =>
        {
        OperationOutcome result = await services.GetRequiredService<IOperationExecutor>()
            .ExecuteAsync(new SendCommandArguments(operation, payload, tenant, aggregateId, correlationId,
                idempotencyKey, extensions), services.GetRequiredService<EnvelopeContext>(), cancellationToken)
            .ConfigureAwait(false);
        return Convert(result.Document, result.Error);
        }).ConfigureAwait(false);

    internal static async Task<CallToolResult> RunQuery(string operation, string payload,
        IServiceProvider services, CancellationToken cancellationToken, string? tenant = null,
        string? aggregateId = null, string? entityId = null, int? pageSize = null, int? offset = null,
        string? cursor = null)
        => await GuardAsync(async () =>
        {
        OperationOutcome result = await services.GetRequiredService<IOperationExecutor>()
            .ExecuteAsync(new RunQueryArguments(operation, payload, tenant, aggregateId, entityId,
                pageSize, offset, cursor), services.GetRequiredService<EnvelopeContext>(), cancellationToken)
            .ConfigureAwait(false);
        return Convert(result.Document, result.Error);
        }).ConfigureAwait(false);

    private static CallToolResult Guard(Func<CallToolResult> action)
    {
        try
        {
            return action();
        }
        catch (Exception)
        {
            return Convert(null, new OperationError("internal_error", Message: "MCP tool invocation failed."));
        }
    }

    private static async Task<CallToolResult> GuardAsync(Func<Task<CallToolResult>> action)
    {
        try
        {
            return await action().ConfigureAwait(false);
        }
        catch (Exception)
        {
            return Convert(null, new OperationError("internal_error", Message: "MCP tool invocation failed."));
        }
    }

    private static CallToolResult Convert(object? document, OperationError? error)
    {
        object body = error is null ? document! : new { error };
        string json = JsonSerializer.Serialize(body, McpCliJson.Result);
        return new CallToolResult
        {
            Content = [new TextContentBlock { Text = json }],
            StructuredContent = JsonSerializer.SerializeToElement(body, McpCliJson.Result),
            IsError = error is not null,
        };
    }
}
