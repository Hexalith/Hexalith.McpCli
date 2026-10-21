using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Hosting;

/// <summary>Captures a validated request in memory; never opens a network connection.</summary>
internal class VectorGatewayCapture : DispatchProxy
{
    /// <summary>Gets the complete request formed by the shared executor.</summary>
    internal JsonElement? Request { get; private set; }

    /// <inheritdoc />
    protected override object? Invoke(MethodInfo? targetMethod, object?[]? args)
    {
        if (targetMethod?.Name is not ("SubmitCommandAsync" or "SubmitQueryAsync") || args?[0] is not { } request)
        {
            throw new InvalidOperationException("Unexpected conformance gateway call.");
        }

        Request = JsonSerializer.SerializeToElement(request, request.GetType(), new JsonSerializerOptions(JsonSerializerDefaults.Web)
        {
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        });
        throw new InvalidOperationException("Captured offline conformance request.");
    }
}
