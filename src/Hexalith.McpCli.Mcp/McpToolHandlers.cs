using System.ComponentModel;
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

    internal static CallToolResult ListOperations(
        [Description("Canonical module name from list_modules.")] string module,
        IServiceProvider services,
        [Description("Filter by operation kind. Omit to list both read and write operations.")] string? kind = null)
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

    internal static CallToolResult DescribeOperation(
        [Description("Canonical module.operation name from list_operations.")] string operation, IServiceProvider services)
        => Guard(() =>
        {
        if (string.IsNullOrWhiteSpace(operation))
        {
            return Convert(null, new OperationError("invalid_arguments", Argument: "operation", Message: "operation is required"));
        }

        CatalogLookupResult<OperationDescriptionDocument> result = services.GetRequiredService<ICatalog>().Describe(operation);
        return Convert(result.Document, result.Error);
        });

    internal static async Task<CallToolResult> SendCommand(
        [Description("Canonical write operation name from list_operations.")] string operation,
        [Description("JSON text matching the payload schema returned by describe_operation.")] string payload,
        IServiceProvider services, CancellationToken cancellationToken,
        [Description("Per-call tenant. Use the exact declared scope or the session's tenant policy.")] string? tenant = null,
        [Description("Aggregate identifier matching the payload. Use canonical uppercase text for ULID-kind modules.")] string? aggregateId = null,
        [Description("Caller-provided canonical uppercase ULID for command correlation.")] string? correlationId = null,
        [Description("Caller-provided canonical uppercase ULID for command idempotency.")] string? idempotencyKey = null,
        [Description("String-valued command extensions permitted by the selected profile.")] IReadOnlyDictionary<string, string>? extensions = null)
        => await GuardAsync(async () =>
        {
        OperationOutcome result = await services.GetRequiredService<IOperationExecutor>()
            .ExecuteAsync(new SendCommandArguments(operation, payload, tenant, aggregateId, correlationId,
                idempotencyKey, extensions), services.GetRequiredService<EnvelopeContext>(), cancellationToken)
            .ConfigureAwait(false);
        return Convert(result.Document, result.Error);
        }, cancellationToken).ConfigureAwait(false);

    internal static async Task<CallToolResult> RunQuery(
        [Description("Canonical read operation name from list_operations.")] string operation,
        [Description("JSON text matching the payload schema returned by describe_operation.")] string payload,
        IServiceProvider services, CancellationToken cancellationToken,
        [Description("Per-call tenant. Use the exact declared scope or the session's tenant policy.")] string? tenant = null,
        [Description("Query aggregate identifier. Use canonical uppercase text for ULID-kind modules.")] string? aggregateId = null,
        [Description("Entity identifier when the query supports entity selection.")] string? entityId = null,
        [Description("Requested page size from 1 to 200.")] int? pageSize = null,
        [Description("Nonnegative row offset. Omit when supplying a nonblank cursor.")] int? offset = null,
        [Description("Opaque paging cursor returned in paging.nextCursor.")] string? cursor = null)
        => await GuardAsync(async () =>
        {
        OperationOutcome result = await services.GetRequiredService<IOperationExecutor>()
            .ExecuteAsync(new RunQueryArguments(operation, payload, tenant, aggregateId, entityId,
                pageSize, offset, cursor), services.GetRequiredService<EnvelopeContext>(), cancellationToken)
            .ConfigureAwait(false);
        return Convert(result.Document, result.Error);
        }, cancellationToken).ConfigureAwait(false);

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

    private static async Task<CallToolResult> GuardAsync(Func<Task<CallToolResult>> action, CancellationToken cancellationToken)
    {
        try
        {
            return await action().ConfigureAwait(false);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            throw;
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
