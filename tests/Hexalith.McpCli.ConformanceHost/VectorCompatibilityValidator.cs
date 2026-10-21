using System.Reflection;
using System.Text.Json;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Microsoft.Extensions.Logging.Abstractions;

namespace Hexalith.McpCli.Hosting;

/// <summary>Preflights every vector call through Core validation without submitting any request.</summary>
internal static class VectorCompatibilityValidator
{
    /// <summary>Returns located validation findings and the fully validated request for every step.</summary>
    internal static async Task<int> ValidateAsync(IReadOnlyList<Assembly> assemblies, string[] paths)
    {
        var provider = new CatalogProvider(() => assemblies, NullLogger<CatalogProvider>.Instance);
        var findings = new List<string>();
        var requests = new List<object>();
        foreach (string path in paths)
        {
            try
            {
                // Vector framing can be deeper than the embedded payload; Core reparses each payload at its own limit.
                using JsonDocument vector = JsonDocument.Parse(File.ReadAllText(path), new JsonDocumentOptions
                {
                    MaxDepth = 256,
                    AllowDuplicateProperties = false,
                });
                foreach ((JsonElement step, string pointer) in Steps(vector.RootElement))
                {
                    JsonElement envelope = step.GetProperty("envelope");
                    string operation = step.GetProperty("operation").GetString()!;
                    string payload = step.GetProperty("payload").GetRawText();
                    Dictionary<string, string>? extensions = envelope.TryGetProperty("extensions", out JsonElement values)
                        ? values.Deserialize<Dictionary<string, string>>() : null;
                    OperationCall call = step.GetProperty("kind").GetString() == "command"
                        ? new SendCommandArguments(operation, payload, AggregateId: Text(envelope, "aggregateId"),
                            CorrelationId: Text(envelope, "correlationId"), IdempotencyKey: Text(envelope, "idempotencyKey"), Extensions: extensions)
                        : new RunQueryArguments(operation, payload, AggregateId: Text(envelope, "aggregateId"),
                            EntityId: Text(envelope, "entityId"), PageSize: Number(envelope, "pageSize"),
                            Offset: Number(envelope, "offset"), Cursor: Text(envelope, "cursor"));
                    IEventStoreGatewayClient gateway = DispatchProxy.Create<IEventStoreGatewayClient, VectorGatewayCapture>();
                    var executor = new OperationExecutor(provider, new ExecutionAvailability(false, true), gateway, strict: true);
                    var context = new EnvelopeContext(Text(envelope, "tenant"), Text(envelope, "actor"), false,
                        new HashSet<string>(extensions?.Keys ?? Enumerable.Empty<string>(), StringComparer.OrdinalIgnoreCase));
                    OperationOutcome outcome = await executor.ExecuteAsync(call, context).ConfigureAwait(false);
                    if (((VectorGatewayCapture)gateway).Request is { } request)
                    {
                        requests.Add(new { source = path, pointer, body = request });
                    }
                    else
                    {
                        string error = JsonSerializer.Serialize(outcome.Error, McpCliJson.Result);
                        findings.Add($"{path}:{pointer}: Core compatibility failed: {error}");
                    }
                }
            }
            catch (Exception exception) when (exception is JsonException or IOException or InvalidOperationException or FormatException or OverflowException or ArgumentException)
            {
                findings.Add($"{path}:/: Core compatibility failed: {exception.Message}");
            }
        }

        Console.Out.WriteLine(JsonSerializer.Serialize(new { findings, requests }, McpCliJson.Result));
        return findings.Count == 0 ? 0 : 1;
    }

    private static string? Text(JsonElement envelope, string name)
        => envelope.TryGetProperty(name, out JsonElement value) ? value.GetString() : null;

    private static int? Number(JsonElement envelope, string name)
        => envelope.TryGetProperty(name, out JsonElement value) ? value.GetInt32() : null;

    private static IEnumerable<(JsonElement Step, string Pointer)> Steps(JsonElement vector)
    {
        int index = 0;
        foreach (JsonElement step in vector.GetProperty("prerequisites").EnumerateArray())
        {
            yield return (step, $"/prerequisites/{index++}");
        }

        yield return (vector.GetProperty("invocation"), "/invocation");
        index = 0;
        foreach (JsonElement step in vector.GetProperty("postconditions").EnumerateArray())
        {
            yield return (step, $"/postconditions/{index++}");
        }
    }
}
